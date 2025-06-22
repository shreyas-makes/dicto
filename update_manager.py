#!/usr/bin/env python3
"""
Dicto Update Manager
Automatic updates and version management for Dicto transcription app.
"""

import os
import sys
import json
import shutil
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import threading
import time


@dataclass
class VersionInfo:
    """Version information structure."""
    version: str
    build_number: int
    release_date: str
    download_url: str
    checksum: str
    release_notes: str


@dataclass
class UpdateConfig:
    """Configuration for update management."""
    check_interval_hours: int = 24
    auto_download: bool = True
    auto_install: bool = False
    backup_count: int = 3
    update_server_url: str = "https://api.dicto.app/updates"
    beta_channel: bool = False


class VersionManager:
    """Manages version information and comparisons."""
    
    def __init__(self):
        self.logger = logging.getLogger("DictoUpdater.VersionManager")
        self.current_version = self._get_current_version()
    
    def _get_current_version(self) -> str:
        """Get the current installed version."""
        try:
            version_file = Path(__file__).parent / "version.txt"
            if version_file.exists():
                return version_file.read_text().strip()
            return "1.0.0"
        except Exception as e:
            self.logger.error(f"Error getting current version: {e}")
            return "1.0.0"
    
    def compare_versions(self, version1: str, version2: str) -> int:
        """Compare two version strings."""
        try:
            def normalize_version(v):
                parts = []
                for part in v.split('.'):
                    if '-' in part:
                        main_part = part.split('-')[0]
                        parts.append(int(main_part) if main_part.isdigit() else 0)
                        break
                    parts.append(int(part) if part.isdigit() else 0)
                return parts
            
            v1_parts = normalize_version(version1)
            v2_parts = normalize_version(version2)
            
            max_len = max(len(v1_parts), len(v2_parts))
            v1_parts.extend([0] * (max_len - len(v1_parts)))
            v2_parts.extend([0] * (max_len - len(v2_parts)))
            
            if v1_parts < v2_parts:
                return -1
            elif v1_parts > v2_parts:
                return 1
            else:
                return 0
        except Exception as e:
            self.logger.error(f"Error comparing versions: {e}")
            return 0
    
    def is_newer_version(self, version: str) -> bool:
        """Check if the given version is newer than current."""
        return self.compare_versions(version, self.current_version) > 0


class BackupManager:
    """Manages configuration and application backups."""
    
    def __init__(self, backup_dir: Optional[Path] = None):
        self.backup_dir = backup_dir or (Path.home() / "Library" / "Application Support" / "Dicto" / "Backups")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger("DictoUpdater.BackupManager")
    
    def create_backup(self, version: str) -> Optional[Path]:
        """Create a backup of the current installation."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"dicto_backup_{version}_{timestamp}"
            backup_path = self.backup_dir / backup_name
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # Backup application files
            app_backup_dir = backup_path / "app"
            app_backup_dir.mkdir(exist_ok=True)
            
            dicto_dir = Path.home() / "dicto"
            if dicto_dir.exists():
                shutil.copytree(dicto_dir, app_backup_dir / "dicto", 
                              ignore=shutil.ignore_patterns('*.pyc', '__pycache__'))
            
            # Backup configuration
            config_backup_dir = backup_path / "config"
            config_backup_dir.mkdir(exist_ok=True)
            
            config_sources = [
                Path.home() / "Library" / "Application Support" / "Dicto",
                Path.home() / "Library" / "Preferences" / "com.dicto.transcription.plist"
            ]
            
            for source in config_sources:
                if source.exists():
                    if source.is_file():
                        shutil.copy2(source, config_backup_dir / source.name)
                    else:
                        shutil.copytree(source, config_backup_dir / source.name,
                                      ignore=shutil.ignore_patterns('Logs', 'Cache'))
            
            # Create backup manifest
            manifest = {
                "version": version,
                "created_at": datetime.now().isoformat(),
                "backup_type": "pre_update"
            }
            
            with open(backup_path / "manifest.json", 'w') as f:
                json.dump(manifest, f, indent=2)
            
            self.logger.info(f"Backup created: {backup_path}")
            self._cleanup_old_backups()
            
            return backup_path
            
        except Exception as e:
            self.logger.error(f"Error creating backup: {e}")
            return None
    
    def restore_backup(self, backup_path: Path) -> bool:
        """Restore from a backup."""
        try:
            if not backup_path.exists():
                self.logger.error(f"Backup path does not exist: {backup_path}")
                return False
            
            # Restore application files
            app_backup = backup_path / "app" / "dicto"
            if app_backup.exists():
                dicto_dir = Path.home() / "dicto"
                if dicto_dir.exists():
                    shutil.rmtree(dicto_dir)
                shutil.copytree(app_backup, dicto_dir)
            
            # Restore configuration
            config_backup = backup_path / "config"
            if config_backup.exists():
                for item in config_backup.iterdir():
                    if item.name == "Dicto":
                        target = Path.home() / "Library" / "Application Support" / "Dicto"
                        if target.exists():
                            shutil.rmtree(target)
                        shutil.copytree(item, target)
                    elif item.name.endswith('.plist'):
                        target = Path.home() / "Library" / "Preferences" / item.name
                        shutil.copy2(item, target)
            
            self.logger.info("Backup restored successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error restoring backup: {e}")
            return False
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """List available backups."""
        backups = []
        try:
            for backup_dir in self.backup_dir.iterdir():
                if backup_dir.is_dir():
                    manifest_file = backup_dir / "manifest.json"
                    if manifest_file.exists():
                        with open(manifest_file, 'r') as f:
                            manifest = json.load(f)
                            manifest['path'] = str(backup_dir)
                            backups.append(manifest)
            
            backups.sort(key=lambda x: x['created_at'], reverse=True)
            
        except Exception as e:
            self.logger.error(f"Error listing backups: {e}")
        
        return backups
    
    def _cleanup_old_backups(self, max_backups: int = 5):
        """Remove old backups to save space."""
        try:
            backups = self.list_backups()
            if len(backups) > max_backups:
                for backup in backups[max_backups:]:
                    backup_path = Path(backup['path'])
                    if backup_path.exists():
                        shutil.rmtree(backup_path)
                        self.logger.info(f"Removed old backup: {backup_path}")
        except Exception as e:
            self.logger.error(f"Error cleaning up old backups: {e}")


class UpdateChecker:
    """Handles checking for available updates."""
    
    def __init__(self, config: UpdateConfig):
        self.config = config
        self.logger = logging.getLogger("DictoUpdater.UpdateChecker")
        self.version_manager = VersionManager()
    
    def check_for_updates(self) -> Optional[VersionInfo]:
        """Check for available updates."""
        try:
            self.logger.info("Checking for updates...")
            
            # Mock update info for demonstration
            mock_update = VersionInfo(
                version="1.1.0",
                build_number=110,
                release_date="2024-01-15",
                download_url="https://github.com/dicto/releases/download/v1.1.0/dicto-1.1.0.zip",
                checksum="sha256:abcd1234...",
                release_notes="Bug fixes and performance improvements"
            )
            
            if self.version_manager.is_newer_version(mock_update.version):
                return mock_update
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error checking for updates: {e}")
            return None


class UpdateManager:
    """Main update manager orchestrating the update process."""
    
    def __init__(self, config: Optional[UpdateConfig] = None):
        self.config = config or UpdateConfig()
        self.logger = logging.getLogger("DictoUpdater.UpdateManager")
        
        # Initialize components
        self.version_manager = VersionManager()
        self.update_checker = UpdateChecker(self.config)
        self.backup_manager = BackupManager()
        
        # State tracking
        self._update_thread = None
        self._last_check = None
        self._available_update = None
    
    def start_background_checking(self):
        """Start background update checking."""
        if self._update_thread and self._update_thread.is_alive():
            return
        
        self._update_thread = threading.Thread(target=self._background_update_loop, daemon=True)
        self._update_thread.start()
        self.logger.info("Background update checking started")
    
    def check_for_updates_now(self) -> Optional[VersionInfo]:
        """Immediately check for updates."""
        update_info = self.update_checker.check_for_updates()
        self._last_check = datetime.now()
        self._available_update = update_info
        return update_info
    
    def get_update_status(self) -> Dict[str, Any]:
        """Get current update status."""
        return {
            "current_version": self.version_manager.current_version,
            "last_check": self._last_check.isoformat() if self._last_check else None,
            "available_update": self._available_update.__dict__ if self._available_update else None,
            "auto_update_enabled": self.config.auto_install,
            "update_channel": "beta" if self.config.beta_channel else "stable"
        }
    
    def _background_update_loop(self):
        """Background thread for periodic update checking."""
        while True:
            try:
                if (not self._last_check or 
                    datetime.now() - self._last_check > timedelta(hours=self.config.check_interval_hours)):
                    
                    update_info = self.check_for_updates_now()
                    
                    if update_info:
                        self.logger.info(f"Update available: {update_info.version}")
                
                time.sleep(3600)  # Sleep for 1 hour
                
            except Exception as e:
                self.logger.error(f"Error in background update loop: {e}")
                time.sleep(3600)


def main():
    """Main entry point for update manager."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Dicto Update Manager")
    parser.add_argument('--check', action='store_true', help='Check for updates')
    parser.add_argument('--status', action='store_true', help='Show update status')
    parser.add_argument('--background', action='store_true', help='Start background checking')
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO, 
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    update_manager = UpdateManager()
    
    if args.check:
        update_info = update_manager.check_for_updates_now()
        if update_info:
            print(f"Update available: {update_info.version}")
            print(f"Release notes: {update_info.release_notes}")
        else:
            print("No updates available")
    
    elif args.status:
        status = update_manager.get_update_status()
        print("Update Status:")
        for key, value in status.items():
            print(f"  {key}: {value}")
    
    elif args.background:
        print("Starting background update checking...")
        update_manager.start_background_checking()
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            print("Stopping background update checking...")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main() 