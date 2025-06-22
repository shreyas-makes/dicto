#!/usr/bin/env python3
"""
Test Configuration - Comprehensive tests for Dicto configuration system
Tests the ConfigManager and PreferencesGUI functionality.
"""

import unittest
import tempfile
import json
import os
import shutil
import logging
from pathlib import Path
from typing import Dict, Any

# Import the modules to test
try:
    from config_manager import (
        ConfigManager, AudioSettings, TranscriptionSettings, 
        UISettings, AdvancedSettings, UserProfile, HotkeyBinding
    )
except ImportError as e:
    print(f"Error importing config_manager: {e}")
    exit(1)


class TestConfigManager(unittest.TestCase):
    """Test cases for ConfigManager class."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.config_manager = ConfigManager(self.test_dir)
        
        # Set up logging
        logging.basicConfig(level=logging.DEBUG)
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir)
    
    def test_initialization(self):
        """Test ConfigManager initialization."""
        self.assertIsInstance(self.config_manager, ConfigManager)
        self.assertTrue(self.config_manager.config_dir.exists())
        self.assertIsInstance(self.config_manager.config, dict)
        self.assertIsInstance(self.config_manager.profiles, dict)
        self.assertIsInstance(self.config_manager.hotkeys, dict)
    
    def test_default_config_creation(self):
        """Test default configuration creation."""
        config = self.config_manager.config
        
        # Check required fields
        self.assertIn('version', config)
        self.assertIn('audio_settings', config)
        self.assertIn('transcription_settings', config)
        self.assertIn('ui_settings', config)
        self.assertIn('advanced_settings', config)
        
        # Check default values
        self.assertEqual(config['version'], '1.0')
        self.assertEqual(config['current_profile'], 'default')
    
    def test_default_profile_creation(self):
        """Test default profile creation."""
        profiles = self.config_manager.get_user_profiles()
        
        self.assertIn('default', profiles)
        default_profile = profiles['default']
        
        self.assertEqual(default_profile.name, 'default')
        self.assertTrue(default_profile.is_default)
        self.assertIsInstance(default_profile.audio_settings, AudioSettings)
        self.assertIsInstance(default_profile.transcription_settings, TranscriptionSettings)
        self.assertIsInstance(default_profile.ui_settings, UISettings)
    
    def test_config_save_load(self):
        """Test configuration saving and loading."""
        # Modify a setting
        new_gain = 2.5
        self.config_manager.config['audio_settings']['gain_adjustment'] = new_gain
        
        # Save configuration
        self.assertTrue(self.config_manager.save_config())
        
        # Create new instance to test loading
        new_config_manager = ConfigManager(self.test_dir)
        loaded_gain = new_config_manager.config['audio_settings']['gain_adjustment']
        
        self.assertEqual(loaded_gain, new_gain)
    
    def test_profile_management(self):
        """Test profile creation, deletion, and switching."""
        # Test profile creation
        self.assertTrue(self.config_manager.create_profile("test_profile", "Test profile"))
        profiles = self.config_manager.get_user_profiles()
        self.assertIn("test_profile", profiles)
        
        # Test profile switching
        self.assertTrue(self.config_manager.switch_profile("test_profile"))
        self.assertEqual(self.config_manager.current_profile, "test_profile")
        
        # Test profile copying
        self.assertTrue(self.config_manager.create_profile("copied_profile", "Copied profile", copy_from="test_profile"))
        
        # Test profile deletion
        self.assertTrue(self.config_manager.delete_profile("test_profile"))
        profiles = self.config_manager.get_user_profiles()
        self.assertNotIn("test_profile", profiles)
        
        # Test cannot delete default profile
        self.assertFalse(self.config_manager.delete_profile("default"))
    
    def test_hotkey_management(self):
        """Test hotkey configuration and validation."""
        # Test hotkey update
        action = "test_action"
        keys = "ctrl+t"
        
        self.assertTrue(self.config_manager.update_hotkey(action, keys))
        
        # Test hotkey validation
        conflicts = self.config_manager.validate_hotkeys()
        self.assertIsInstance(conflicts, dict)
        self.assertIn('error', conflicts)
        self.assertIn('warning', conflicts)
        
        # Test duplicate hotkey detection
        self.config_manager.update_hotkey("action1", "ctrl+d")
        self.config_manager.update_hotkey("action2", "ctrl+d")
        
        conflicts = self.config_manager.validate_hotkeys()
        self.assertGreater(len(conflicts['error']), 0)
    
    def test_key_validation(self):
        """Test key combination validation."""
        # Valid key combinations
        valid_keys = ["ctrl+c", "cmd+shift+v", "alt+f4", "f1"]
        for keys in valid_keys:
            self.assertTrue(self.config_manager._validate_key_combination(keys))
        
        # Invalid key combinations
        invalid_keys = ["", "ctrl+", "+v", "invalid+key", "ctrl+invalid"]
        for keys in invalid_keys:
            self.assertFalse(self.config_manager._validate_key_combination(keys))
    
    def test_settings_export_import(self):
        """Test settings export and import functionality."""
        # Modify some settings
        self.config_manager.create_profile("export_test", "Export test profile")
        self.config_manager.update_hotkey("test_export", "ctrl+e")
        
        # Export settings
        export_file = Path(self.test_dir) / "export_test.json"
        self.assertTrue(self.config_manager.export_settings(str(export_file)))
        self.assertTrue(export_file.exists())
        
        # Verify export content
        with open(export_file, 'r') as f:
            exported_data = json.load(f)
        
        self.assertIn('config', exported_data)
        self.assertIn('profiles', exported_data)
        self.assertIn('hotkeys', exported_data)
        self.assertIn('export_test', exported_data['profiles'])
        
        # Create new instance and import
        new_config_manager = ConfigManager(tempfile.mkdtemp())
        self.assertTrue(new_config_manager.import_settings(str(export_file)))
        
        # Verify import
        imported_profiles = new_config_manager.get_user_profiles()
        self.assertIn('export_test', imported_profiles)


def main():
    """Run all configuration tests."""
    print("=== Dicto Configuration System Tests ===\n")
    
    # Set up test logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add ConfigManager tests
    test_suite.addTest(unittest.makeSuite(TestConfigManager))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Summary
    print(f"\n=== Test Summary ===")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed!")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main()) 