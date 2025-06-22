#!/usr/bin/env python3
"""
Test CTRL+V Detection - Simple test for Dicto hotkey functionality
This script tests the CTRL+V detection system using pynput for reliable key detection.
"""

import os
import sys
import time
import logging
import signal
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_pynput_detector():
    """Test the pynput key detector."""
    print("🔍 Testing pynput Key Detector...")
    
    try:
        from pynput import keyboard
        from pynput.keyboard import Key, KeyCode
        
        # Key state tracking
        ctrl_pressed = False
        v_pressed = False
        
        def on_press(key):
            nonlocal ctrl_pressed, v_pressed
            
            try:
                if key in [Key.ctrl_l, Key.ctrl_r]:
                    ctrl_pressed = True
                elif hasattr(key, 'char') and key.char == 'v':
                    v_pressed = True
                    
                if ctrl_pressed and v_pressed:
                    print("🔥 CTRL+V PRESSED via pynput!")
                    
            except AttributeError:
                pass
        
        def on_release(key):
            nonlocal ctrl_pressed, v_pressed
            
            try:
                if key in [Key.ctrl_l, Key.ctrl_r]:
                    ctrl_pressed = False
                    if ctrl_pressed and v_pressed:  # Was active, now released
                        print("🔥 CTRL+V RELEASED via pynput!")
                elif hasattr(key, 'char') and key.char == 'v':
                    v_pressed = False
                    if ctrl_pressed and v_pressed:  # Was active, now released
                        print("🔥 CTRL+V RELEASED via pynput!")
                    
                if key == Key.esc:
                    print("🛑 Escape pressed - stopping test")
                    return False
                    
            except AttributeError:
                pass
        
        print("✅ pynput detector ready")
        print("💡 Hold CTRL+V to test detection...")
        print("💡 Press ESC to stop test")
        
        with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
            listener.join()
            
        return True
        
    except ImportError as e:
        print(f"❌ pynput not available: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing pynput: {e}")
        return False

def test_continuous_recorder():
    """Test the continuous recorder with CTRL+V."""
    print("🔍 Testing Continuous Recorder...")
    
    try:
        from continuous_recorder import ContinuousRecorder
        
        def on_start():
            print("🎙️  Recording started!")
            
        def on_stop():
            print("⏹️  Recording stopped!")
            
        def on_chunk_complete(chunk_path):
            print(f"📁 Chunk completed: {chunk_path}")
            
        def on_session_complete(chunks):
            print(f"✅ Session complete with {len(chunks)} chunks")
            for i, chunk in enumerate(chunks, 1):
                print(f"   {i}. {chunk}")
            
        # Create recorder with key detection enabled
        recorder = ContinuousRecorder(
            chunk_duration=5.0,  # Short chunks for testing
            enable_key_detection=True
        )
        
        recorder.set_callbacks(
            on_start=on_start,
            on_stop=on_stop,
            on_chunk=on_chunk_complete,
            on_session=on_session_complete
        )
        
        if recorder.start_continuous_monitoring():
            print("✅ Continuous recorder started")
            print("💡 Hold CTRL+V to start recording...")
            print("💡 Release CTRL+V to stop recording...")
            print("💡 Press Ctrl+C to stop test")
            
            try:
                while True:
                    time.sleep(0.1)
            except KeyboardInterrupt:
                print("\n🛑 Stopping continuous recorder...")
                recorder.stop_continuous_monitoring()
                return True
        else:
            print("❌ Failed to start continuous recorder")
            return False
            
    except ImportError as e:
        print(f"❌ Continuous recorder not available: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing continuous recorder: {e}")
        return False

def main():
    """Main test function."""
    print("🎯 Dicto CTRL+V Detection Test")
    print("=" * 50)
    
    # Check dependencies
    print("📦 Checking dependencies...")
    
    dependencies = [
        ("pynput", "import pynput"),
        ("AppKit", "from AppKit import NSPasteboard"),
        ("plyer", "import plyer"),
        ("rumps", "import rumps")
    ]
    
    for name, import_stmt in dependencies:
        try:
            exec(import_stmt)
            print(f"✅ {name}")
        except ImportError:
            print(f"❌ {name}")
    
    print("\n" + "=" * 50)
    
    # Interactive test selection
    while True:
        print("\n🧪 Test Options:")
        print("1. Test pynput Key Detector")
        print("2. Test Continuous Recorder")
        print("3. Exit")
        
        try:
            choice = input("\nEnter your choice (1-3): ").strip()
            
            if choice == "1":
                test_pynput_detector()
            elif choice == "2":
                test_continuous_recorder()
            elif choice == "3":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please enter 1-3.")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

def signal_handler(signum, frame):
    """Handle interrupt signals."""
    print(f"\n🛑 Received signal {signum}, exiting...")
    sys.exit(0)

if __name__ == "__main__":
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    main() 