#!/usr/bin/env python3
"""
Configuration Manager - Comprehensive configuration system for Dicto
Provides advanced configuration management with GUI preferences, hotkey customization,
user profiles, and import/export functionality.
"""

import os
import json
import logging
import shutil
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Union
from dataclasses import dataclass, asdict
from enum import Enum

try:
    import jsonschema
    from jsonschema import validate, ValidationError
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False
    print("Warning: jsonschema not available. Schema validation disabled.")


class HotkeyConflictLevel(Enum):
    """Conflict severity levels for hotkey validation."""
    NONE = "none"
    WARNING = "warning"  # Different apps, might conflict
    ERROR = "error"      # Same app, will definitely conflict


@dataclass
class HotkeyBinding:
    """Represents a hotkey binding configuration."""
    action: str
    keys: str  # e.g., "cmd+shift+v"
    description: str
    enabled: bool = True
    global_scope: bool = True


@dataclass
class AudioSettings:
    """Audio processing configuration."""
    input_device: Optional[str] = None
    noise_reduction_level: str = "medium"  # low, medium, high
    gain_adjustment: float = 1.0
    sample_rate: int = 16000
    auto_gain_control: bool = True
    voice_activity_detection: bool = True
    silence_threshold: float = 0.01
    speech_threshold: float = 0.05


@dataclass
class TranscriptionSettings:
    """Transcription processing configuration."""
    model_name: str = "base.en"
    confidence_threshold: float = 0.6
    language: str = "en"
    auto_language_detection: bool = False
    custom_vocabulary_enabled: bool = True
    timestamping_enabled: bool = True
    speaker_diarization: bool = False


@dataclass
class UISettings:
    """User interface configuration."""
    menu_bar_behavior: str = "always_visible"  # always_visible, auto_hide, minimal
    notification_style: str = "native"  # native, minimal, disabled
    show_transcription_preview: bool = True
    auto_copy_to_clipboard: bool = True
    show_confidence_scores: bool = False
    dark_mode: Optional[bool] = None  # None = system default


@dataclass
class AdvancedSettings:
    """Advanced system configuration."""
    temp_file_location: str = ""  # Empty means system default
    cleanup_policy: str = "auto"  # auto, manual, never
    max_session_duration: int = 3600  # seconds
    auto_save_interval: int = 30  # seconds
    log_level: str = "INFO"
    enable_crash_recovery: bool = True
    diagnostic_mode: bool = False


@dataclass
class UserProfile:
    """User profile configuration for different scenarios."""
    name: str
    description: str
    audio_settings: AudioSettings
    transcription_settings: TranscriptionSettings
    ui_settings: UISettings
    hotkeys: Dict[str, HotkeyBinding]
    created_at: float
    last_used: float
    is_default: bool = False


class ConfigManager:
    """
    Comprehensive configuration manager for Dicto.
    
    Handles loading, saving, validation, user profiles, hotkey management,
    and import/export functionality with backup and versioning.
    """
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize ConfigManager.
        
        Args:
            config_dir: Custom configuration directory. If None, uses standard location.
        """
        self.logger = logging.getLogger(__name__ + ".ConfigManager")
        
        # Set up configuration directory
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            # Use macOS standard Application Support directory
            home_dir = Path.home()
            self.config_dir = home_dir / "Library" / "Application Support" / "Dicto"
        
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Configuration files
        self.main_config_file = self.config_dir / "config.json"
        self.profiles_file = self.config_dir / "profiles.json"
        self.hotkeys_file = self.config_dir / "hotkeys.json"
        self.backup_dir = self.config_dir / "backups"
        self.backup_dir.mkdir(exist_ok=True)
        
        # Configuration state
        self.config: Dict[str, Any] = {}
        self.profiles: Dict[str, UserProfile] = {}
        self.hotkeys: Dict[str, HotkeyBinding] = {}
        self.current_profile: Optional[str] = None
        
        # Schema validation
        self.config_schema = self._load_config_schema()
        
        # Load existing configuration
        self.load_config()
        
        self.logger.info(f"ConfigManager initialized with {len(self.profiles)} profiles")
    
    def _load_config_schema(self) -> Dict[str, Any]:
        """Load JSON schema for configuration validation."""
        return {
            "type": "object",
            "properties": {
                "version": {"type": "string"},
                "current_profile": {"type": ["string", "null"]},
                "audio_settings": {
                    "type": "object",
                    "properties": {
                        "input_device": {"type": ["string", "null"]},
                        "noise_reduction_level": {"type": "string", "enum": ["low", "medium", "high"]},
                        "gain_adjustment": {"type": "number", "minimum": 0.1, "maximum": 5.0},
                        "sample_rate": {"type": "integer", "enum": [8000, 16000, 22050, 44100, 48000]},
                        "auto_gain_control": {"type": "boolean"},
                        "voice_activity_detection": {"type": "boolean"},
                        "silence_threshold": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                        "speech_threshold": {"type": "number", "minimum": 0.0, "maximum": 1.0}
                    }
                },
                "transcription_settings": {
                    "type": "object",
                    "properties": {
                        "model_name": {"type": "string"},
                        "confidence_threshold": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                        "language": {"type": "string"},
                        "auto_language_detection": {"type": "boolean"},
                        "custom_vocabulary_enabled": {"type": "boolean"},
                        "timestamping_enabled": {"type": "boolean"},
                        "speaker_diarization": {"type": "boolean"}
                    }
                },
                "ui_settings": {
                    "type": "object",
                    "properties": {
                        "menu_bar_behavior": {"type": "string", "enum": ["always_visible", "auto_hide", "minimal"]},
                        "notification_style": {"type": "string", "enum": ["native", "minimal", "disabled"]},
                        "show_transcription_preview": {"type": "boolean"},
                        "auto_copy_to_clipboard": {"type": "boolean"},
                        "show_confidence_scores": {"type": "boolean"},
                        "dark_mode": {"type": ["boolean", "null"]}
                    }
                },
                "advanced_settings": {
                    "type": "object",
                    "properties": {
                        "temp_file_location": {"type": "string"},
                        "cleanup_policy": {"type": "string", "enum": ["auto", "manual", "never"]},
                        "max_session_duration": {"type": "integer", "minimum": 60},
                        "auto_save_interval": {"type": "integer", "minimum": 5},
                        "log_level": {"type": "string", "enum": ["DEBUG", "INFO", "WARNING", "ERROR"]},
                        "enable_crash_recovery": {"type": "boolean"},
                        "diagnostic_mode": {"type": "boolean"}
                    }
                }
            },
            "required": ["version"]
        }
    
    def load_config(self) -> bool:
        """
        Load configuration from files with schema validation.
        
        Returns:
            bool: True if loaded successfully, False otherwise.
        """
        try:
            # Load main configuration
            if self.main_config_file.exists():
                with open(self.main_config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                
                # Validate against schema if jsonschema is available
                if JSONSCHEMA_AVAILABLE:
                    try:
                        validate(instance=self.config, schema=self.config_schema)
                        self.logger.info("Configuration validation successful")
                    except ValidationError as e:
                        self.logger.warning(f"Configuration validation failed: {e.message}")
                        # Continue with potentially invalid config, but log the issue
            else:
                # Create default configuration
                self.config = self._create_default_config()
                self.save_config()
            
            # Load user profiles
            self._load_profiles()
            
            # Load hotkeys
            self._load_hotkeys()
            
            # Set current profile
            profile_name = self.config.get('current_profile')
            if profile_name and profile_name in self.profiles:
                self.current_profile = profile_name
            else:
                # Set default profile
                default_profiles = [name for name, profile in self.profiles.items() if profile.is_default]
                if default_profiles:
                    self.current_profile = default_profiles[0]
                elif self.profiles:
                    self.current_profile = list(self.profiles.keys())[0]
            
            self.logger.info(f"Configuration loaded successfully. Current profile: {self.current_profile}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            # Create minimal default configuration
            self.config = self._create_default_config()
            return False
    
    def save_config(self) -> bool:
        """
        Save configuration with backup and versioning.
        
        Returns:
            bool: True if saved successfully, False otherwise.
        """
        try:
            # Create backup before saving
            self._create_backup()
            
            # Update version and timestamp
            self.config['version'] = "1.0"
            self.config['last_modified'] = time.time()
            self.config['current_profile'] = self.current_profile
            
            # Validate before saving if jsonschema is available
            if JSONSCHEMA_AVAILABLE:
                try:
                    validate(instance=self.config, schema=self.config_schema)
                except ValidationError as e:
                    self.logger.error(f"Configuration validation failed before save: {e.message}")
                    return False
            
            # Save main configuration
            with open(self.main_config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            
            # Save profiles and hotkeys
            self._save_profiles()
            self._save_hotkeys()
            
            self.logger.info("Configuration saved successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
            return False
    
    def _create_default_config(self) -> Dict[str, Any]:
        """Create default configuration."""
        audio_settings = AudioSettings()
        transcription_settings = TranscriptionSettings()
        ui_settings = UISettings()
        advanced_settings = AdvancedSettings()
        
        return {
            "version": "1.0",
            "current_profile": "default",
            "audio_settings": asdict(audio_settings),
            "transcription_settings": asdict(transcription_settings),
            "ui_settings": asdict(ui_settings),
            "advanced_settings": asdict(advanced_settings),
            "created_at": time.time(),
            "last_modified": time.time()
        }
    
    def _load_profiles(self) -> bool:
        """Load user profiles from file."""
        try:
            if self.profiles_file.exists():
                with open(self.profiles_file, 'r', encoding='utf-8') as f:
                    profiles_data = json.load(f)
                
                for name, profile_dict in profiles_data.items():
                    # Convert dict to UserProfile
                    audio_settings = AudioSettings(**profile_dict['audio_settings'])
                    transcription_settings = TranscriptionSettings(**profile_dict['transcription_settings'])
                    ui_settings = UISettings(**profile_dict['ui_settings'])
                    
                    hotkeys = {}
                    for action, hotkey_dict in profile_dict.get('hotkeys', {}).items():
                        hotkeys[action] = HotkeyBinding(**hotkey_dict)
                    
                    profile = UserProfile(
                        name=profile_dict['name'],
                        description=profile_dict['description'],
                        audio_settings=audio_settings,
                        transcription_settings=transcription_settings,
                        ui_settings=ui_settings,
                        hotkeys=hotkeys,
                        created_at=profile_dict['created_at'],
                        last_used=profile_dict['last_used'],
                        is_default=profile_dict.get('is_default', False)
                    )
                    
                    self.profiles[name] = profile
            else:
                # Create default profile
                self._create_default_profile()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load profiles: {e}")
            self._create_default_profile()
            return False
    
    def _create_default_profile(self):
        """Create default user profile."""
        default_hotkeys = {
            "record_toggle": HotkeyBinding("record_toggle", "ctrl+v", "Toggle recording", True, True),
            "transcribe_clipboard": HotkeyBinding("transcribe_clipboard", "ctrl+shift+v", "Transcribe from clipboard", True, True),
            "open_preferences": HotkeyBinding("open_preferences", "cmd+,", "Open preferences", True, False)
        }
        
        profile = UserProfile(
            name="default",
            description="Default configuration profile",
            audio_settings=AudioSettings(),
            transcription_settings=TranscriptionSettings(),
            ui_settings=UISettings(),
            hotkeys=default_hotkeys,
            created_at=time.time(),
            last_used=time.time(),
            is_default=True
        )
        
        self.profiles["default"] = profile
    
    def _save_profiles(self) -> bool:
        """Save user profiles to file."""
        try:
            profiles_data = {}
            for name, profile in self.profiles.items():
                # Convert UserProfile to dict
                hotkeys_dict = {}
                for action, hotkey in profile.hotkeys.items():
                    hotkeys_dict[action] = asdict(hotkey)
                
                profiles_data[name] = {
                    "name": profile.name,
                    "description": profile.description,
                    "audio_settings": asdict(profile.audio_settings),
                    "transcription_settings": asdict(profile.transcription_settings),
                    "ui_settings": asdict(profile.ui_settings),
                    "hotkeys": hotkeys_dict,
                    "created_at": profile.created_at,
                    "last_used": profile.last_used,
                    "is_default": profile.is_default
                }
            
            with open(self.profiles_file, 'w', encoding='utf-8') as f:
                json.dump(profiles_data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save profiles: {e}")
            return False
    
    def _load_hotkeys(self) -> bool:
        """Load global hotkeys configuration."""
        try:
            if self.hotkeys_file.exists():
                with open(self.hotkeys_file, 'r', encoding='utf-8') as f:
                    hotkeys_data = json.load(f)
                
                for action, hotkey_dict in hotkeys_data.items():
                    self.hotkeys[action] = HotkeyBinding(**hotkey_dict)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load hotkeys: {e}")
            return False
    
    def _save_hotkeys(self) -> bool:
        """Save global hotkeys configuration."""
        try:
            hotkeys_data = {}
            for action, hotkey in self.hotkeys.items():
                hotkeys_data[action] = asdict(hotkey)
            
            with open(self.hotkeys_file, 'w', encoding='utf-8') as f:
                json.dump(hotkeys_data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save hotkeys: {e}")
            return False
    
    def _create_backup(self):
        """Create backup of current configuration."""
        try:
            timestamp = int(time.time())
            backup_name = f"config_backup_{timestamp}"
            backup_path = self.backup_dir / backup_name
            backup_path.mkdir(exist_ok=True)
            
            # Backup main config
            if self.main_config_file.exists():
                shutil.copy2(self.main_config_file, backup_path / "config.json")
            
            # Backup profiles
            if self.profiles_file.exists():
                shutil.copy2(self.profiles_file, backup_path / "profiles.json")
            
            # Backup hotkeys
            if self.hotkeys_file.exists():
                shutil.copy2(self.hotkeys_file, backup_path / "hotkeys.json")
            
            # Clean old backups (keep last 10)
            backups = sorted([d for d in self.backup_dir.iterdir() if d.is_dir()])
            if len(backups) > 10:
                for old_backup in backups[:-10]:
                    shutil.rmtree(old_backup)
            
            self.logger.info(f"Configuration backup created: {backup_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}")
    
    def get_user_profiles(self) -> Dict[str, UserProfile]:
        """
        Get all user profiles.
        
        Returns:
            Dict[str, UserProfile]: Dictionary of profile names to UserProfile objects.
        """
        return self.profiles.copy()
    
    def create_profile(self, name: str, description: str, copy_from: Optional[str] = None) -> bool:
        """
        Create a new user profile.
        
        Args:
            name: Profile name.
            description: Profile description.
            copy_from: Optional profile name to copy settings from.
            
        Returns:
            bool: True if created successfully, False otherwise.
        """
        try:
            if name in self.profiles:
                self.logger.error(f"Profile '{name}' already exists")
                return False
            
            if copy_from and copy_from in self.profiles:
                # Copy from existing profile
                source_profile = self.profiles[copy_from]
                profile = UserProfile(
                    name=name,
                    description=description,
                    audio_settings=AudioSettings(**asdict(source_profile.audio_settings)),
                    transcription_settings=TranscriptionSettings(**asdict(source_profile.transcription_settings)),
                    ui_settings=UISettings(**asdict(source_profile.ui_settings)),
                    hotkeys=source_profile.hotkeys.copy(),
                    created_at=time.time(),
                    last_used=time.time(),
                    is_default=False
                )
            else:
                # Create default profile
                profile = UserProfile(
                    name=name,
                    description=description,
                    audio_settings=AudioSettings(),
                    transcription_settings=TranscriptionSettings(),
                    ui_settings=UISettings(),
                    hotkeys={},
                    created_at=time.time(),
                    last_used=time.time(),
                    is_default=False
                )
            
            self.profiles[name] = profile
            self.save_config()
            
            self.logger.info(f"Profile '{name}' created successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create profile '{name}': {e}")
            return False
    
    def delete_profile(self, name: str) -> bool:
        """
        Delete a user profile.
        
        Args:
            name: Profile name to delete.
            
        Returns:
            bool: True if deleted successfully, False otherwise.
        """
        try:
            if name not in self.profiles:
                self.logger.error(f"Profile '{name}' does not exist")
                return False
            
            if self.profiles[name].is_default:
                self.logger.error(f"Cannot delete default profile '{name}'")
                return False
            
            # Switch to default profile if deleting current profile
            if self.current_profile == name:
                default_profiles = [n for n, p in self.profiles.items() if p.is_default and n != name]
                if default_profiles:
                    self.current_profile = default_profiles[0]
                else:
                    remaining = [n for n in self.profiles.keys() if n != name]
                    if remaining:
                        self.current_profile = remaining[0]
                    else:
                        self.current_profile = None
            
            del self.profiles[name]
            self.save_config()
            
            self.logger.info(f"Profile '{name}' deleted successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete profile '{name}': {e}")
            return False
    
    def switch_profile(self, name: str) -> bool:
        """
        Switch to a different user profile.
        
        Args:
            name: Profile name to switch to.
            
        Returns:
            bool: True if switched successfully, False otherwise.
        """
        try:
            if name not in self.profiles:
                self.logger.error(f"Profile '{name}' does not exist")
                return False
            
            # Update last used timestamp for new profile
            self.profiles[name].last_used = time.time()
            
            self.current_profile = name
            self.save_config()
            
            self.logger.info(f"Switched to profile '{name}'")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to switch to profile '{name}': {e}")
            return False
    
    def validate_hotkeys(self) -> Dict[str, List[str]]:
        """
        Validate hotkey configurations for conflicts.
        
        Returns:
            Dict[str, List[str]]: Dictionary of conflict levels to lists of conflicting hotkeys.
        """
        conflicts = {"error": [], "warning": []}
        
        try:
            # Collect all hotkeys from current profile and global hotkeys
            all_hotkeys = {}
            
            # Add global hotkeys
            for action, hotkey in self.hotkeys.items():
                if hotkey.enabled:
                    key_combo = hotkey.keys.lower()
                    if key_combo in all_hotkeys:
                        conflicts["error"].append(f"Duplicate global hotkey '{key_combo}': {all_hotkeys[key_combo]} vs {action}")
                    else:
                        all_hotkeys[key_combo] = f"global:{action}"
            
            # Add current profile hotkeys
            if self.current_profile and self.current_profile in self.profiles:
                profile = self.profiles[self.current_profile]
                for action, hotkey in profile.hotkeys.items():
                    if hotkey.enabled:
                        key_combo = hotkey.keys.lower()
                        if key_combo in all_hotkeys:
                            conflicts["error"].append(f"Duplicate hotkey '{key_combo}': {all_hotkeys[key_combo]} vs profile:{action}")
                        else:
                            all_hotkeys[key_combo] = f"profile:{action}"
            
            # Check for system hotkey conflicts (basic check)
            system_hotkeys = [
                "cmd+c", "cmd+v", "cmd+x", "cmd+z", "cmd+a", "cmd+s", "cmd+w", "cmd+q",
                "cmd+tab", "cmd+space", "cmd+shift+3", "cmd+shift+4", "cmd+shift+5"
            ]
            
            for key_combo in all_hotkeys:
                if key_combo in system_hotkeys:
                    conflicts["warning"].append(f"Hotkey '{key_combo}' conflicts with system shortcut")
            
            self.logger.info(f"Hotkey validation complete. Found {len(conflicts['error'])} errors, {len(conflicts['warning'])} warnings")
            
        except Exception as e:
            self.logger.error(f"Failed to validate hotkeys: {e}")
        
        return conflicts
    
    def update_hotkey(self, action: str, keys: str, profile_name: Optional[str] = None) -> bool:
        """
        Update a hotkey binding.
        
        Args:
            action: Action name.
            keys: Key combination string.
            profile_name: Profile name for profile-specific hotkey, None for global.
            
        Returns:
            bool: True if updated successfully, False otherwise.
        """
        try:
            # Validate key combination format
            if not self._validate_key_combination(keys):
                self.logger.error(f"Invalid key combination: {keys}")
                return False
            
            if profile_name:
                # Update profile-specific hotkey
                if profile_name not in self.profiles:
                    self.logger.error(f"Profile '{profile_name}' does not exist")
                    return False
                
                if action in self.profiles[profile_name].hotkeys:
                    self.profiles[profile_name].hotkeys[action].keys = keys
                else:
                    self.profiles[profile_name].hotkeys[action] = HotkeyBinding(
                        action=action,
                        keys=keys,
                        description=f"Custom hotkey for {action}",
                        enabled=True,
                        global_scope=True
                    )
            else:
                # Update global hotkey
                if action in self.hotkeys:
                    self.hotkeys[action].keys = keys
                else:
                    self.hotkeys[action] = HotkeyBinding(
                        action=action,
                        keys=keys,
                        description=f"Global hotkey for {action}",
                        enabled=True,
                        global_scope=True
                    )
            
            self.save_config()
            self.logger.info(f"Hotkey updated: {action} -> {keys}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update hotkey: {e}")
            return False
    
    def _validate_key_combination(self, keys: str) -> bool:
        """
        Validate key combination format.
        
        Args:
            keys: Key combination string.
            
        Returns:
            bool: True if valid, False otherwise.
        """
        try:
            # Basic validation - should contain valid modifiers and keys
            valid_modifiers = {"cmd", "ctrl", "alt", "shift", "option"}
            valid_keys = {
                "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m",
                "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z",
                "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
                "space", "enter", "tab", "esc", "delete", "backspace",
                "up", "down", "left", "right", "home", "end", "pageup", "pagedown",
                "f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11", "f12"
            }
            
            parts = keys.lower().split("+")
            if len(parts) < 1:
                return False
            
            # Last part should be a valid key
            if parts[-1] not in valid_keys:
                return False
            
            # All other parts should be valid modifiers
            for modifier in parts[:-1]:
                if modifier not in valid_modifiers:
                    return False
            
            return True
            
        except Exception:
            return False
    
    def export_settings(self, file_path: str, include_profiles: bool = True) -> bool:
        """
        Export settings to a file for portability.
        
        Args:
            file_path: Destination file path.
            include_profiles: Whether to include user profiles.
            
        Returns:
            bool: True if exported successfully, False otherwise.
        """
        try:
            export_data = {
                "version": "1.0",
                "export_timestamp": time.time(),
                "config": self.config,
                "hotkeys": {action: asdict(hotkey) for action, hotkey in self.hotkeys.items()}
            }
            
            if include_profiles:
                profiles_data = {}
                for name, profile in self.profiles.items():
                    hotkeys_dict = {action: asdict(hotkey) for action, hotkey in profile.hotkeys.items()}
                    profiles_data[name] = {
                        "name": profile.name,
                        "description": profile.description,
                        "audio_settings": asdict(profile.audio_settings),
                        "transcription_settings": asdict(profile.transcription_settings),
                        "ui_settings": asdict(profile.ui_settings),
                        "hotkeys": hotkeys_dict,
                        "created_at": profile.created_at,
                        "last_used": profile.last_used,
                        "is_default": profile.is_default
                    }
                export_data["profiles"] = profiles_data
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Settings exported to {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export settings: {e}")
            return False
    
    def import_settings(self, file_path: str, merge_profiles: bool = True) -> bool:
        """
        Import settings from a file.
        
        Args:
            file_path: Source file path.
            merge_profiles: Whether to merge profiles or replace them.
            
        Returns:
            bool: True if imported successfully, False otherwise.
        """
        try:
            if not Path(file_path).exists():
                self.logger.error(f"Import file not found: {file_path}")
                return False
            
            with open(file_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # Create backup before import
            self._create_backup()
            
            # Import main config
            if "config" in import_data:
                # Validate imported config if jsonschema is available
                if JSONSCHEMA_AVAILABLE:
                    try:
                        validate(instance=import_data["config"], schema=self.config_schema)
                        self.config.update(import_data["config"])
                    except ValidationError as e:
                        self.logger.warning(f"Imported config validation failed: {e.message}")
                        # Continue with merge but log validation issues
                else:
                    self.config.update(import_data["config"])
            
            # Import hotkeys
            if "hotkeys" in import_data:
                for action, hotkey_dict in import_data["hotkeys"].items():
                    self.hotkeys[action] = HotkeyBinding(**hotkey_dict)
            
            # Import profiles
            if "profiles" in import_data:
                for name, profile_dict in import_data["profiles"].items():
                    if not merge_profiles and name in self.profiles:
                        continue  # Skip existing profiles if not merging
                    
                    # Convert dict to UserProfile
                    audio_settings = AudioSettings(**profile_dict['audio_settings'])
                    transcription_settings = TranscriptionSettings(**profile_dict['transcription_settings'])
                    ui_settings = UISettings(**profile_dict['ui_settings'])
                    
                    hotkeys = {}
                    for action, hotkey_dict in profile_dict.get('hotkeys', {}).items():
                        hotkeys[action] = HotkeyBinding(**hotkey_dict)
                    
                    profile = UserProfile(
                        name=profile_dict['name'],
                        description=profile_dict['description'],
                        audio_settings=audio_settings,
                        transcription_settings=transcription_settings,
                        ui_settings=ui_settings,
                        hotkeys=hotkeys,
                        created_at=profile_dict['created_at'],
                        last_used=profile_dict['last_used'],
                        is_default=profile_dict.get('is_default', False)
                    )
                    
                    self.profiles[name] = profile
            
            # Save imported configuration
            self.save_config()
            
            self.logger.info(f"Settings imported from {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to import settings: {e}")
            return False
    
    def get_current_settings(self) -> Dict[str, Any]:
        """
        Get current effective settings (from current profile + global config).
        
        Returns:
            Dict[str, Any]: Current effective settings.
        """
        try:
            if self.current_profile and self.current_profile in self.profiles:
                profile = self.profiles[self.current_profile]
                return {
                    "profile_name": profile.name,
                    "audio_settings": asdict(profile.audio_settings),
                    "transcription_settings": asdict(profile.transcription_settings),
                    "ui_settings": asdict(profile.ui_settings),
                    "hotkeys": {action: asdict(hotkey) for action, hotkey in profile.hotkeys.items()},
                    "global_hotkeys": {action: asdict(hotkey) for action, hotkey in self.hotkeys.items()},
                    "advanced_settings": self.config.get("advanced_settings", asdict(AdvancedSettings()))
                }
            else:
                return {
                    "profile_name": None,
                    "audio_settings": self.config.get("audio_settings", asdict(AudioSettings())),
                    "transcription_settings": self.config.get("transcription_settings", asdict(TranscriptionSettings())),
                    "ui_settings": self.config.get("ui_settings", asdict(UISettings())),
                    "hotkeys": {},
                    "global_hotkeys": {action: asdict(hotkey) for action, hotkey in self.hotkeys.items()},
                    "advanced_settings": self.config.get("advanced_settings", asdict(AdvancedSettings()))
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get current settings: {e}")
            return {}
    
    def update_setting(self, setting_path: str, value: Any, profile_name: Optional[str] = None) -> bool:
        """
        Update a specific setting value.
        
        Args:
            setting_path: Dot-separated path to setting (e.g., "audio_settings.gain_adjustment").
            value: New value.
            profile_name: Profile name for profile-specific setting, None for global.
            
        Returns:
            bool: True if updated successfully, False otherwise.
        """
        try:
            path_parts = setting_path.split(".")
            
            if profile_name:
                # Update profile-specific setting
                if profile_name not in self.profiles:
                    self.logger.error(f"Profile '{profile_name}' does not exist")
                    return False
                
                target = self.profiles[profile_name]
                # Navigate to the correct settings object
                if path_parts[0] == "audio_settings":
                    target = target.audio_settings
                elif path_parts[0] == "transcription_settings":
                    target = target.transcription_settings
                elif path_parts[0] == "ui_settings":
                    target = target.ui_settings
                else:
                    self.logger.error(f"Invalid setting path: {setting_path}")
                    return False
                
                # Update the value
                if len(path_parts) == 2 and hasattr(target, path_parts[1]):
                    setattr(target, path_parts[1], value)
                else:
                    self.logger.error(f"Invalid setting path: {setting_path}")
                    return False
            else:
                # Update global setting
                if path_parts[0] not in self.config:
                    self.config[path_parts[0]] = {}
                
                target = self.config[path_parts[0]]
                if len(path_parts) == 2:
                    target[path_parts[1]] = value
                else:
                    self.logger.error(f"Invalid setting path: {setting_path}")
                    return False
            
            self.save_config()
            self.logger.info(f"Setting updated: {setting_path} = {value}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update setting '{setting_path}': {e}")
            return False
    
    def reset_to_defaults(self, profile_name: Optional[str] = None) -> bool:
        """
        Reset configuration to default values.
        
        Args:
            profile_name: Profile name to reset, None to reset global config.
            
        Returns:
            bool: True if reset successfully, False otherwise.
        """
        try:
            # Create backup before reset
            self._create_backup()
            
            if profile_name:
                # Reset specific profile
                if profile_name not in self.profiles:
                    self.logger.error(f"Profile '{profile_name}' does not exist")
                    return False
                
                self.profiles[profile_name].audio_settings = AudioSettings()
                self.profiles[profile_name].transcription_settings = TranscriptionSettings()
                self.profiles[profile_name].ui_settings = UISettings()
                
            else:
                # Reset global configuration
                self.config = self._create_default_config()
                self.hotkeys.clear()
            
            self.save_config()
            self.logger.info(f"Configuration reset to defaults: {'profile ' + profile_name if profile_name else 'global'}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to reset configuration: {e}")
            return False


# Example usage and testing
if __name__ == "__main__":
    import tempfile
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Test with temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        config_manager = ConfigManager(temp_dir)
        
        print("✅ ConfigManager initialized")
        
        # Test profile creation
        config_manager.create_profile("meeting", "Settings for meetings")
        config_manager.create_profile("writing", "Settings for writing", copy_from="meeting")
        
        print(f"✅ Created profiles: {list(config_manager.profiles.keys())}")
        
        # Test hotkey validation
        conflicts = config_manager.validate_hotkeys()
        print(f"✅ Hotkey validation: {len(conflicts['error'])} errors, {len(conflicts['warning'])} warnings")
        
        # Test settings export/import
        export_path = Path(temp_dir) / "test_export.json"
        config_manager.export_settings(str(export_path))
        print(f"✅ Settings exported to {export_path}")
        
        print("🎉 All configuration tests passed!") 