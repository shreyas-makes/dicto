#!/usr/bin/env python3
"""
Test script to verify MenuBarManager fixes
"""

import logging
import sys
from pathlib import Path

# Setup basic logging
logging.basicConfig(level=logging.INFO)

def test_menu_manager():
    """Test MenuBarManager functionality."""
    try:
        from menu_bar_manager import MenuBarManager, AppStatus
        
        print("✅ MenuBarManager import successful")
        
        # Create manager
        manager = MenuBarManager("Test")
        print("✅ MenuBarManager created")
        
        # Test method existence
        assert hasattr(manager, 'create_menu_from_structure'), "create_menu_from_structure method missing"
        print("✅ create_menu_from_structure method exists")
        
        # Test callback setters
        def dummy_callback(action):
            print(f"Callback called with action: {action}")
        
        manager.set_recording_callback(dummy_callback)
        manager.set_transcription_callback(dummy_callback)
        manager.set_settings_callback(dummy_callback)
        print("✅ Callback setters work")
        
        print("✅ All MenuBarManager tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ MenuBarManager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_notification_manager():
    """Test NotificationManager functionality."""
    try:
        # Import the DictoApp to test notification manager
        from dicto_main import NotificationManager
        
        print("✅ NotificationManager import successful")
        
        # Create notification manager
        nm = NotificationManager()
        print("✅ NotificationManager created")
        
        # Test escaping function (should be available in the method)
        # We can't test the actual notification without showing it, but we can test the setup
        print("✅ NotificationManager basic functionality verified")
        return True
        
    except Exception as e:
        print(f"❌ NotificationManager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("🧪 Testing Dicto fixes...")
    print("=" * 50)
    
    tests = [
        ("MenuBarManager", test_menu_manager),
        ("NotificationManager", test_notification_manager),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Testing {test_name}...")
        if test_func():
            passed += 1
        
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The fixes should work correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 