#!/usr/bin/env python3
"""
Dicto Uninstaller
Complete system cleanup and removal utility for Dicto transcription app.

Features:
- Complete application removal
- System service cleanup
- Configuration and data removal
- LaunchAgent unregistration
- Preference cleanup
- Backup creation before uninstall
"""

import os
import sys
import shutil
import subprocess
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import argparse
from datetime import datetime
import json
import time


class UninstallConfig:
    """Configuration for uninstallation process."""
    
    def __init__(self):
        self.app_name = "Dicto"
        self.app_identifier = "com.dicto.transcription"
        self.install_locations = [
            Path("/Applications/Dicto.app"),
            Path.home() / "dicto",
            Path.home() / "Applications" / "Dicto.app"
        ]
        self.config_locations = [
            Path.home() / "Library" / "Application Support" / "Dicto",
            Path.home() / "Library" / "Preferences" / "com.dicto.transcription.plist",
            Path.home() / "Library" / "Caches" / "Dicto",
            Path.home() / "Library" / "Logs" / "Dicto"
        ]
        self.launch_agent_path = Path.home() / "Library" / "LaunchAgents" / "com.dicto.transcription.plist"
        self.backup_before_uninstall = True


class ProcessKiller:
    """Handles stopping Dicto processes before uninstall."""
    
    def __init__(self):
        self.logger = logging.getLogger("DictoUninstaller.ProcessKiller")
    
    def stop_all_dicto_processes(self) -> bool:
        """Stop all running Dicto processes."""
        try:
            self.logger.info("Stopping Dicto processes...")
            
            # Stop LaunchAgent first
            self._stop_launch_agent()
            
            # Kill main processes
            process_patterns = [
                'dicto_main.py',
                'Dicto.app',
                'dicto',
                'dicto_launcher'
            ]
            
            for pattern in process_patterns:
                try:
                    result = subprocess.run(['pkill', '-f', pattern], 
                                          capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        self.logger.info(f"Stopped processes matching: {pattern}")
                except subprocess.TimeoutExpired:
                    self.logger.warning(f"Timeout stopping processes: {pattern}")
                except Exception as e:
                    self.logger.warning(f"Error stopping {pattern}: {e}")
            
            # Wait for graceful shutdown
            time.sleep(3)
            
            self.logger.info("All Dicto processes stopped")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping Dicto processes: {e}")
            return False
    
    def _stop_launch_agent(self):
        """Stop and unload the LaunchAgent."""
        try:
            launch_agent_path = Path.home() / "Library" / "LaunchAgents" / "com.dicto.transcription.plist"
            if launch_agent_path.exists():
                result = subprocess.run([
                    'launchctl', 'unload', str(launch_agent_path)
                ], capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    self.logger.info("LaunchAgent unloaded")
                else:
                    self.logger.warning(f"LaunchAgent unload warning: {result.stderr}")
                    
        except Exception as e:
            self.logger.warning(f"Error stopping LaunchAgent: {e}")


class SystemCleaner:
    """Handles cleaning system integrations and services."""
    
    def __init__(self, config: UninstallConfig):
        self.config = config
        self.logger = logging.getLogger("DictoUninstaller.SystemCleaner")
    
    def cleanup_launch_agents(self) -> bool:
        """Clean up LaunchAgent configuration."""
        try:
            if self.config.launch_agent_path.exists():
                self.logger.info("Removing LaunchAgent...")
                
                # First try to unload it
                try:
                    subprocess.run([
                        'launchctl', 'unload', str(self.config.launch_agent_path)
                    ], capture_output=True, timeout=10)
                except Exception:
                    pass
                
                # Remove the plist file
                self.config.launch_agent_path.unlink()
                self.logger.info("LaunchAgent removed")
                return True
            else:
                self.logger.info("No LaunchAgent found to remove")
                return True
                
        except Exception as e:
            self.logger.error(f"Error removing LaunchAgent: {e}")
            return False
    
    def cleanup_system_preferences(self) -> bool:
        """Clean up system preferences and caches."""
        try:
            self.logger.info("Cleaning system preferences...")
            
            # Clear application preferences
            pref_files = [
                Path.home() / "Library" / "Preferences" / "com.dicto.transcription.plist"
            ]
            
            for pref_file in pref_files:
                if pref_file.exists():
                    pref_file.unlink()
                    self.logger.info(f"Removed preference file: {pref_file}")
            
            # Clear preference cache
            try:
                subprocess.run([
                    'defaults', 'delete', 'com.dicto.transcription'
                ], capture_output=True, timeout=10)
            except Exception:
                pass
            
            self.logger.info("System preferences cleaned")
            return True
            
        except Exception as e:
            self.logger.error(f"Error cleaning system preferences: {e}")
            return False


class BackupCreator:
    """Creates backup before uninstallation."""
    
    def __init__(self, config: UninstallConfig):
        self.config = config
        self.logger = logging.getLogger("DictoUninstaller.BackupCreator")
        self.backup_dir = Path.home() / "Library" / "Application Support" / "Dicto" / "UninstallBackups"
    
    def create_uninstall_backup(self) -> Optional[Path]:
        """Create a backup before uninstallation."""
        try:
            if not self.config.backup_before_uninstall:
                return None
            
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"dicto_uninstall_backup_{timestamp}"
            backup_path = self.backup_dir / backup_name
            backup_path.mkdir(parents=True, exist_ok=True)
            
            self.logger.info(f"Creating uninstall backup: {backup_path}")
            
            # Backup application files
            app_backup_dir = backup_path / "applications"
            app_backup_dir.mkdir(exist_ok=True)
            
            for app_location in self.config.install_locations:
                if app_location.exists():
                    backup_target = app_backup_dir / app_location.name
                    if app_location.is_dir():
                        shutil.copytree(app_location, backup_target, 
                                      ignore=shutil.ignore_patterns('*.pyc', '__pycache__'))
                    else:
                        shutil.copy2(app_location, backup_target)
                    self.logger.info(f"Backed up: {app_location}")
            
            # Backup configuration
            config_backup_dir = backup_path / "configuration"
            config_backup_dir.mkdir(exist_ok=True)
            
            for config_location in self.config.config_locations:
                if config_location.exists():
                    backup_target = config_backup_dir / config_location.name
                    if config_location.is_dir():
                        shutil.copytree(config_location, backup_target,
                                      ignore=shutil.ignore_patterns('Cache', '*.log'))
                    else:
                        shutil.copy2(config_location, backup_target)
                    self.logger.info(f"Backed up config: {config_location}")
            
            # Create backup manifest
            manifest = {
                "backup_type": "uninstall",
                "created_at": datetime.now().isoformat(),
                "app_version": self._get_app_version(),
                "backed_up_locations": {
                    "applications": [str(loc) for loc in self.config.install_locations if loc.exists()],
                    "configuration": [str(loc) for loc in self.config.config_locations if loc.exists()]
                }
            }
            
            with open(backup_path / "manifest.json", 'w') as f:
                json.dump(manifest, f, indent=2)
            
            self.logger.info(f"Uninstall backup created: {backup_path}")
            return backup_path
            
        except Exception as e:
            self.logger.error(f"Error creating uninstall backup: {e}")
            return None
    
    def _get_app_version(self) -> str:
        """Get the current app version for backup manifest."""
        try:
            version_file = Path.home() / "dicto" / "version.txt"
            if version_file.exists():
                return version_file.read_text().strip()
            return "unknown"
        except Exception:
            return "unknown"


class FileRemover:
    """Handles removal of application files and directories."""
    
    def __init__(self, config: UninstallConfig):
        self.config = config
        self.logger = logging.getLogger("DictoUninstaller.FileRemover")
    
    def remove_application_files(self) -> bool:
        """Remove all application files and directories."""
        try:
            self.logger.info("Removing application files...")
            
            removed_count = 0
            for location in self.config.install_locations:
                if location.exists():
                    try:
                        if location.is_dir():
                            shutil.rmtree(location)
                        else:
                            location.unlink()
                        self.logger.info(f"Removed: {location}")
                        removed_count += 1
                    except Exception as e:
                        self.logger.error(f"Failed to remove {location}: {e}")
            
            self.logger.info(f"Removed {removed_count} application locations")
            return True
            
        except Exception as e:
            self.logger.error(f"Error removing application files: {e}")
            return False
    
    def remove_configuration_files(self) -> bool:
        """Remove all configuration files and directories."""
        try:
            self.logger.info("Removing configuration files...")
            
            removed_count = 0
            for location in self.config.config_locations:
                if location.exists():
                    try:
                        if location.is_dir():
                            shutil.rmtree(location)
                        else:
                            location.unlink()
                        self.logger.info(f"Removed config: {location}")
                        removed_count += 1
                    except Exception as e:
                        self.logger.error(f"Failed to remove config {location}: {e}")
            
            self.logger.info(f"Removed {removed_count} configuration locations")
            return True
            
        except Exception as e:
            self.logger.error(f"Error removing configuration files: {e}")
            return False


class DictoUninstaller:
    """Main uninstaller class orchestrating the removal process."""
    
    def __init__(self, interactive: bool = True, create_backup: bool = True):
        self.config = UninstallConfig()
        self.config.backup_before_uninstall = create_backup
        self.interactive = interactive
        
        # Setup logging
        self.setup_logging()
        self.logger = logging.getLogger("DictoUninstaller")
        
        # Initialize components
        self.process_killer = ProcessKiller()
        self.system_cleaner = SystemCleaner(self.config)
        self.backup_creator = BackupCreator(self.config)
        self.file_remover = FileRemover(self.config)
    
    def setup_logging(self):
        """Configure logging for the uninstaller."""
        log_dir = Path.home() / "Library" / "Logs" / "Dicto"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / "uninstaller.log"),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def run_uninstallation(self) -> bool:
        """Run the complete uninstallation process."""
        print("🗑️  Dicto Uninstaller")
        print("=" * 30)
        
        if self.interactive:
            print("\nThis will completely remove Dicto from your system including:")
            print("• Application files")
            print("• Configuration and preferences")
            print("• System integrations")
            print("• Cache and log files")
            
            if self.config.backup_before_uninstall:
                print("• A backup will be created before removal")
            
            response = input("\nContinue with uninstallation? (y/N): ")
            if response.lower() != 'y':
                print("Uninstallation cancelled.")
                return False
        
        success = True
        
        # Step 1: Create backup
        backup_path = None
        if self.config.backup_before_uninstall:
            print("\n📦 Step 1: Creating backup...")
            backup_path = self.backup_creator.create_uninstall_backup()
            if backup_path:
                print(f"✅ Backup created: {backup_path}")
            else:
                print("⚠️  Backup creation failed, continuing...")
        
        # Step 2: Stop processes
        print("\n🛑 Step 2: Stopping Dicto processes...")
        if self.process_killer.stop_all_dicto_processes():
            print("✅ All processes stopped")
        else:
            print("⚠️  Some processes may still be running")
            success = False
        
        # Step 3: Clean system integrations
        print("\n🧹 Step 3: Cleaning system integrations...")
        if self.system_cleaner.cleanup_launch_agents():
            print("✅ LaunchAgent removed")
        else:
            print("❌ LaunchAgent removal failed")
            success = False
        
        if self.system_cleaner.cleanup_system_preferences():
            print("✅ System preferences cleaned")
        else:
            print("❌ System preferences cleanup failed")
            success = False
        
        # Step 4: Remove files
        print("\n📁 Step 4: Removing application files...")
        if self.file_remover.remove_application_files():
            print("✅ Application files removed")
        else:
            print("❌ Application file removal failed")
            success = False
        
        print("\n⚙️  Step 5: Removing configuration files...")
        if self.file_remover.remove_configuration_files():
            print("✅ Configuration files removed")
        else:
            print("❌ Configuration file removal failed")
            success = False
        
        # Final status
        if success:
            print("\n🎉 Dicto has been successfully uninstalled!")
            if backup_path:
                print(f"📦 Backup saved at: {backup_path}")
        else:
            print("\n⚠️  Uninstallation completed with some errors.")
            print("Check the log file for details.")
        
        return success
    
    def verify_removal(self) -> Dict[str, Any]:
        """Verify that all components have been removed."""
        verification_results = {
            "applications_removed": True,
            "configurations_removed": True,
            "launch_agent_removed": True,
            "remaining_files": []
        }
        
        # Check application files
        for location in self.config.install_locations:
            if location.exists():
                verification_results["applications_removed"] = False
                verification_results["remaining_files"].append(str(location))
        
        # Check configuration files
        for location in self.config.config_locations:
            if location.exists():
                verification_results["configurations_removed"] = False
                verification_results["remaining_files"].append(str(location))
        
        # Check LaunchAgent
        if self.config.launch_agent_path.exists():
            verification_results["launch_agent_removed"] = False
            verification_results["remaining_files"].append(str(self.config.launch_agent_path))
        
        return verification_results


def main():
    """Main entry point for the uninstaller."""
    parser = argparse.ArgumentParser(description="Dicto Uninstaller")
    parser.add_argument('--no-backup', action='store_true',
                       help='Skip backup creation before uninstall')
    parser.add_argument('--non-interactive', action='store_true',
                       help='Run without user prompts')
    parser.add_argument('--verify', action='store_true',
                       help='Verify removal without uninstalling')
    
    args = parser.parse_args()
    
    create_backup = not args.no_backup
    interactive = not args.non_interactive
    
    uninstaller = DictoUninstaller(interactive=interactive, create_backup=create_backup)
    
    if args.verify:
        print("🔍 Verifying removal status...")
        results = uninstaller.verify_removal()
        
        print("\nRemoval Status:")
        print(f"Applications removed: {'✅' if results['applications_removed'] else '❌'}")
        print(f"Configurations removed: {'✅' if results['configurations_removed'] else '❌'}")
        print(f"LaunchAgent removed: {'✅' if results['launch_agent_removed'] else '❌'}")
        
        if results['remaining_files']:
            print("\nRemaining files:")
            for file_path in results['remaining_files']:
                print(f"  • {file_path}")
        else:
            print("\n✅ Complete removal verified")
        
        return
    
    success = uninstaller.run_uninstallation()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 