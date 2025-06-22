#!/usr/bin/env python3
"""
Auto Text Inserter - Automatically insert text into focused input areas
This module provides functionality to automatically type/paste text into 
the currently focused text field or input area on macOS.
"""

import os
import sys
import time
import logging
import subprocess
from typing import Optional, Dict, Any

try:
    from AppKit import NSPasteboard, NSStringPboardType, NSWorkspace
    from Quartz import (
        CGEventCreateKeyboardEvent, CGEventPost, kCGHIDEventTap,
        kCGEventKeyDown, kCGEventKeyUp, CGEventCreateFromGestureCall,
        CGEventSetFlags, kCGEventFlagMaskCommand
    )
    MACOS_APIS_AVAILABLE = True
except ImportError:
    print("Warning: macOS APIs not available. Install with: pip install pyobjc-framework-Cocoa pyobjc-framework-Quartz")
    MACOS_APIS_AVAILABLE = False

try:
    from pynput.keyboard import Key, Controller as KeyboardController
    from pynput.mouse import Controller as MouseController
    PYNPUT_AVAILABLE = True
except ImportError:
    print("Warning: pynput not available. Install with: pip install pynput")
    PYNPUT_AVAILABLE = False


class AutoTextInserter:
    """
    Automatically inserts text into the currently focused text input area.
    
    Uses multiple methods for maximum compatibility:
    1. Clipboard + CMD+V simulation (most reliable)
    2. Direct typing simulation
    3. AppleScript integration
    """
    
    def __init__(self):
        """Initialize the AutoTextInserter."""
        self.logger = logging.getLogger(__name__)
        
        # Check available methods
        self.clipboard_available = MACOS_APIS_AVAILABLE
        self.typing_available = PYNPUT_AVAILABLE
        self.applescript_available = self._check_applescript()
        
        # Initialize controllers
        if self.typing_available:
            self.keyboard = KeyboardController()
            self.mouse = MouseController()
        
        # Store original clipboard content
        self.original_clipboard = None
        
        self.logger.info(f"AutoTextInserter initialized - Clipboard: {self.clipboard_available}, "
                        f"Typing: {self.typing_available}, AppleScript: {self.applescript_available}")
    
    def _check_applescript(self) -> bool:
        """Check if AppleScript is available."""
        try:
            result = subprocess.run(['osascript', '-e', 'return 1'], 
                                  capture_output=True, timeout=2)
            return result.returncode == 0
        except Exception:
            return False
    
    def insert_text(self, text: str, method: str = "auto") -> bool:
        """
        Insert text into the currently focused text input area.
        
        Args:
            text: Text to insert
            method: Method to use ("auto", "clipboard", "typing", "applescript")
            
        Returns:
            bool: True if text was inserted successfully
        """
        if not text:
            self.logger.warning("No text provided for insertion")
            return False
        
        self.logger.info(f"Inserting text using method: {method}")
        
        # Try methods in order of reliability
        if method == "auto":
            return (self._insert_via_clipboard(text) or 
                   self._insert_via_typing(text) or
                   self._insert_via_applescript(text))
        elif method == "clipboard":
            return self._insert_via_clipboard(text)
        elif method == "typing":
            return self._insert_via_typing(text)
        elif method == "applescript":
            return self._insert_via_applescript(text)
        else:
            self.logger.error(f"Unknown insertion method: {method}")
            return False
    
    def _insert_via_clipboard(self, text: str) -> bool:
        """Insert text by copying to clipboard and simulating CMD+V."""
        if not self.clipboard_available:
            return False
        
        try:
            # Store original clipboard content
            self._backup_clipboard()
            
            # Set text to clipboard
            pasteboard = NSPasteboard.generalPasteboard()
            pasteboard.clearContents()
            success = pasteboard.setString_forType_(text, NSStringPboardType)
            
            if not success:
                self.logger.error("Failed to set clipboard content")
                return False
            
            # Small delay to ensure clipboard is set
            time.sleep(0.05)
            
            # Simulate CMD+V
            if self._simulate_paste_shortcut():
                self.logger.info("Text inserted via clipboard method")
                
                # Restore original clipboard after a short delay
                time.sleep(0.1)
                self._restore_clipboard()
                return True
            else:
                self._restore_clipboard()
                return False
                
        except Exception as e:
            self.logger.error(f"Error in clipboard insertion: {e}")
            self._restore_clipboard()
            return False
    
    def _simulate_paste_shortcut(self) -> bool:
        """Simulate CMD+V key combination."""
        try:
            if self.typing_available:
                # Use pynput to simulate CMD+V
                with self.keyboard.pressed(Key.cmd):
                    self.keyboard.press('v')
                    self.keyboard.release('v')
                return True
            else:
                # Fallback to subprocess
                return self._simulate_paste_via_subprocess()
                
        except Exception as e:
            self.logger.error(f"Error simulating paste shortcut: {e}")
            return False
    
    def _simulate_paste_via_subprocess(self) -> bool:
        """Simulate CMD+V using AppleScript as fallback."""
        try:
            script = '''
            tell application "System Events"
                keystroke "v" using command down
            end tell
            '''
            result = subprocess.run(['osascript', '-e', script], 
                                  capture_output=True, timeout=2)
            return result.returncode == 0
        except Exception as e:
            self.logger.error(f"Error in subprocess paste simulation: {e}")
            return False
    
    def _insert_via_typing(self, text: str) -> bool:
        """Insert text by simulating direct typing."""
        if not self.typing_available:
            return False
        
        try:
            # Type the text character by character
            self.keyboard.type(text)
            self.logger.info("Text inserted via typing method")
            return True
            
        except Exception as e:
            self.logger.error(f"Error in typing insertion: {e}")
            return False
    
    def _insert_via_applescript(self, text: str) -> bool:
        """Insert text using AppleScript."""
        if not self.applescript_available:
            return False
        
        try:
            # Escape quotes and backslashes in the text
            escaped_text = text.replace('\\', '\\\\').replace('"', '\\"')
            
            script = f'''
            tell application "System Events"
                keystroke "{escaped_text}"
            end tell
            '''
            
            result = subprocess.run(['osascript', '-e', script], 
                                  capture_output=True, timeout=5)
            
            if result.returncode == 0:
                self.logger.info("Text inserted via AppleScript method")
                return True
            else:
                self.logger.error(f"AppleScript failed: {result.stderr.decode()}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error in AppleScript insertion: {e}")
            return False
    
    def _backup_clipboard(self):
        """Backup current clipboard content."""
        try:
            if self.clipboard_available:
                pasteboard = NSPasteboard.generalPasteboard()
                self.original_clipboard = pasteboard.stringForType_(NSStringPboardType)
        except Exception as e:
            self.logger.warning(f"Failed to backup clipboard: {e}")
            self.original_clipboard = None
    
    def _restore_clipboard(self):
        """Restore original clipboard content."""
        try:
            if self.clipboard_available and self.original_clipboard:
                pasteboard = NSPasteboard.generalPasteboard()
                pasteboard.clearContents()
                pasteboard.setString_forType_(self.original_clipboard, NSStringPboardType)
                self.logger.debug("Original clipboard content restored")
        except Exception as e:
            self.logger.warning(f"Failed to restore clipboard: {e}")
    
    def get_focused_app_info(self) -> Dict[str, Any]:
        """Get information about the currently focused application."""
        try:
            if self.applescript_available:
                script = '''
                tell application "System Events"
                    set frontApp to name of first application process whose frontmost is true
                    return frontApp
                end tell
                '''
                result = subprocess.run(['osascript', '-e', script], 
                                      capture_output=True, text=True, timeout=2)
                
                if result.returncode == 0:
                    app_name = result.stdout.strip()
                    return {
                        "app_name": app_name,
                        "method": "applescript"
                    }
            
            # Fallback to NSWorkspace
            if self.clipboard_available:
                workspace = NSWorkspace.sharedWorkspace()
                active_app = workspace.activeApplication()
                if active_app:
                    return {
                        "app_name": active_app.get('NSApplicationName', 'Unknown'),
                        "bundle_id": active_app.get('NSApplicationBundleIdentifier', ''),
                        "method": "nsworkspace"
                    }
            
            return {"app_name": "Unknown", "method": "none"}
            
        except Exception as e:
            self.logger.error(f"Error getting focused app info: {e}")
            return {"app_name": "Unknown", "method": "error"}
    
    def test_insertion(self, test_text: str = "Test text insertion") -> bool:
        """Test text insertion functionality."""
        self.logger.info("Testing text insertion...")
        
        app_info = self.get_focused_app_info()
        self.logger.info(f"Focused app: {app_info}")
        
        print(f"\n📝 Testing text insertion in: {app_info.get('app_name', 'Unknown')}")
        print("Place your cursor in a text field and press Enter to test...")
        input()
        
        success = self.insert_text(test_text)
        
        if success:
            print(f"✅ Successfully inserted: '{test_text}'")
        else:
            print(f"❌ Failed to insert text")
        
        return success


def test_auto_text_inserter():
    """Test function for the AutoTextInserter."""
    logging.basicConfig(level=logging.INFO)
    
    inserter = AutoTextInserter()
    
    print("🧪 AutoTextInserter Test")
    print("=" * 40)
    
    # Test different methods
    test_text = "Hello from Dicto! This is a test of automatic text insertion."
    
    while True:
        print("\n📝 Test Options:")
        print("1. Test clipboard insertion (CMD+V)")
        print("2. Test direct typing")
        print("3. Test AppleScript insertion")
        print("4. Test auto method (tries all)")
        print("5. Get focused app info")
        print("6. Exit")
        
        try:
            choice = input("\nEnter your choice (1-6): ").strip()
            
            if choice == "1":
                inserter.test_insertion(test_text)
            elif choice == "2":
                print("\nPlace cursor in text field and press Enter...")
                input()
                inserter._insert_via_typing(test_text)
            elif choice == "3":
                print("\nPlace cursor in text field and press Enter...")
                input()
                inserter._insert_via_applescript(test_text)
            elif choice == "4":
                inserter.test_insertion(test_text)
            elif choice == "5":
                app_info = inserter.get_focused_app_info()
                print(f"Focused app: {app_info}")
            elif choice == "6":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break


if __name__ == "__main__":
    test_auto_text_inserter() 