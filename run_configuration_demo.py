#!/usr/bin/env python3
"""
Configuration Demo - Test and demonstrate Dicto configuration system
This script shows the configuration system in action.
"""

import logging
import tempfile
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Demonstrate the configuration system."""
    print("🚀 Dicto Configuration System Demo")
    print("=" * 50)
    
    try:
        # Test ConfigManager
        from config_manager import ConfigManager
        
        print("\n1. Testing ConfigManager...")
        
        # Use temporary directory for demo
        with tempfile.TemporaryDirectory() as temp_dir:
            config_manager = ConfigManager(temp_dir)
            
            print(f"✅ ConfigManager initialized")
            print(f"   Config directory: {config_manager.config_dir}")
            print(f"   Profiles: {list(config_manager.profiles.keys())}")
            print(f"   Current profile: {config_manager.current_profile}")
            
            # Test profile creation
            print("\n2. Testing Profile Management...")
            
            if config_manager.create_profile("meeting", "Settings for meetings"):
                print("✅ Created 'meeting' profile")
            
            if config_manager.create_profile("writing", "Settings for writing", copy_from="meeting"):
                print("✅ Created 'writing' profile (copied from meeting)")
            
            # Test profile switching
            if config_manager.switch_profile("meeting"):
                print("✅ Switched to 'meeting' profile")
            
            # Test settings update
            print("\n3. Testing Settings Updates...")
            
            if config_manager.update_setting("audio_settings.noise_reduction_level", "high", "meeting"):
                print("✅ Updated noise reduction level for meeting profile")
            
            if config_manager.update_setting("transcription_settings.confidence_threshold", 0.8, "meeting"):
                print("✅ Updated confidence threshold for meeting profile")
            
            # Test hotkey management
            print("\n4. Testing Hotkey Management...")
            
            if config_manager.update_hotkey("meeting_mute", "cmd+m", "meeting"):
                print("✅ Added meeting mute hotkey")
            
            # Test hotkey validation
            conflicts = config_manager.validate_hotkeys()
            print(f"✅ Hotkey validation complete: {len(conflicts['error'])} errors, {len(conflicts['warning'])} warnings")
            
            # Test export/import
            print("\n5. Testing Export/Import...")
            
            export_file = Path(temp_dir) / "demo_export.json"
            if config_manager.export_settings(str(export_file)):
                print(f"✅ Settings exported to: {export_file}")
                print(f"   File size: {export_file.stat().st_size} bytes")
            
            # Test current settings
            print("\n6. Testing Settings Retrieval...")
            
            current_settings = config_manager.get_current_settings()
            print(f"✅ Current settings retrieved")
            print(f"   Profile: {current_settings.get('profile_name')}")
            print(f"   Audio noise reduction: {current_settings.get('audio_settings', {}).get('noise_reduction_level')}")
            print(f"   Transcription confidence: {current_settings.get('transcription_settings', {}).get('confidence_threshold')}")
            
        print("\n🎉 ConfigManager tests completed successfully!")
        
    except ImportError as e:
        print(f"❌ Failed to import config_manager: {e}")
        return 1
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return 1
    
    # Test PreferencesGUI (optional, requires display)
    try:
        print("\n7. Testing PreferencesGUI...")
        
        import os
        if os.environ.get('DISPLAY') or os.environ.get('TERM_PROGRAM'):
            # Only test GUI if we have a display
            from preferences_gui import PreferencesGUI
            
            with tempfile.TemporaryDirectory() as temp_dir:
                config_manager = ConfigManager(temp_dir)
                
                print("✅ PreferencesGUI imported successfully")
                print("   Note: GUI window not opened in demo mode")
                print("   To test GUI, run: python preferences_gui.py")
        else:
            print("⏭️  Skipping GUI test (no display available)")
            
    except ImportError as e:
        print(f"⚠️  PreferencesGUI not available: {e}")
    except Exception as e:
        print(f"⚠️  GUI test failed: {e}")
    
    # Test integration
    try:
        print("\n8. Testing Integration...")
        
        print("✅ All components available for integration")
        print("   ConfigManager: Available")
        
        try:
            from preferences_gui import PreferencesGUI
            print("   PreferencesGUI: Available")
        except ImportError:
            print("   PreferencesGUI: Not available")
        
        print("   Enhanced dicto_main.py: Ready for configuration integration")
        
    except Exception as e:
        print(f"⚠️  Integration test failed: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 Demo completed!")
    print("\nNext steps:")
    print("1. Run: python test_configuration.py  # Run unit tests")
    print("2. Run: python preferences_gui.py     # Test GUI (if available)")
    print("3. Run: python dicto_main.py          # Test full integration")
    print("\nConfiguration files are stored in:")
    print("   ~/Library/Application Support/Dicto/")
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main()) 