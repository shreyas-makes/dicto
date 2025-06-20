#!/usr/bin/env python3
"""
Dicto Main - Enhanced system-wide voice transcription app for macOS
Provides global hotkey (Cmd+V) for voice recording with enhanced audio processing,
device selection, real-time monitoring, and automatic clipboard integration.

New Features in Task 5:
- Multiple audio input device support
- Real-time audio level monitoring  
- Voice activity

Requirements:
- Global Cmd+V hotkey for record/stop toggle
- Automatic clipboard integration
- macOS native notifications
- Background operation
- Enhanced error handling with user feedback

Dependencies:
- pynput: Global hotkey support
- AppKit (PyObjC): Clipboard management
- plyer: Cross-platform notifications
- dicto_core: TranscriptionEngine
- audio_recorder: AudioRecorder
"""

import os
import sys
import time
import logging
import threading
import signal
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any

# Third-party imports
try:
    from pynput import keyboard
    from pynput.keyboard import Key, KeyCode
except ImportError:
    print("Error: pynput not installed. Install with: pip install pynput")
    sys.exit(1)

try:
    from plyer import notification
except ImportError:
    print("Error: plyer not installed. Install with: pip install plyer")
    sys.exit(1)

try:
    from AppKit import NSPasteboard, NSStringPboardType
except ImportError:
    print("Error: PyObjC not installed. Install with: pip install pyobjc-framework-Cocoa")
    sys.exit(1)

# Local imports
try:
    from dicto_core import TranscriptionEngine
except ImportError:
    print("Error: dicto_core.py not found. Ensure it's in the same directory.")
    sys.exit(1)


class ClipboardManager:
    """
    macOS clipboard manager using AppKit.
    Handles reading from and writing to the system clipboard.
    """
    
    def __init__(self):
        self.pasteboard = NSPasteboard.generalPasteboard()
        self.logger = logging.getLogger(__name__ + ".ClipboardManager")
    
    def set_text(self, text: str) -> bool:
        """
        Set text to clipboard.
        
        Args:
            text: Text to copy to clipboard.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            self.pasteboard.clearContents()
            success = self.pasteboard.setString_forType_(text, NSStringPboardType)
            self.logger.info(f"Clipboard updated with {len(text)} characters")
            return bool(success)
        except Exception as e:
            self.logger.error(f"Failed to set clipboard: {e}")
            return False
    
    def get_text(self) -> Optional[str]:
        """
        Get text from clipboard.
        
        Returns:
            Optional[str]: Clipboard text content or None if not available.
        """
        try:
            content = self.pasteboard.stringForType_(NSStringPboardType)
            return str(content) if content else None
        except Exception as e:
            self.logger.error(f"Failed to get clipboard: {e}")
            return None


class NotificationManager:
    """
    Notification manager using plyer for cross-platform notifications.
    Provides user feedback for recording state and transcription results.
    """
    
    def __init__(self, app_name: str = "Dicto"):
        self.app_name = app_name
        self.logger = logging.getLogger(__name__ + ".NotificationManager")
    
    def show_notification(self, title: str, message: str, timeout: int = 3) -> bool:
        """
        Show a system notification.
        
        Args:
            title: Notification title.
            message: Notification message.
            timeout: How long to show notification in seconds.
            
        Returns:
            bool: True if notification was shown successfully.
        """
        try:
            notification.notify(
                title=title,
                message=message,
                app_name=self.app_name,
                timeout=timeout
            )
            self.logger.info(f"Notification shown: {title} - {message}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to show notification: {e}")
            return False
    
    def notify_recording_started(self) -> bool:
        """Show notification when recording starts."""
        return self.show_notification(
            "🔴 Recording Started",
            "Press Cmd+V again to stop and transcribe"
        )
    
    def notify_recording_stopped(self) -> bool:
        """Show notification when recording stops."""
        return self.show_notification(
            "⏹️ Recording Stopped",
            "Processing transcription..."
        )
    
    def notify_transcription_complete(self, text: str) -> bool:
        """Show notification when transcription is complete."""
        preview = text[:50] + "..." if len(text) > 50 else text
        return self.show_notification(
            "✅ Transcription Complete",
            f"Copied to clipboard: {preview}"
        )
    
    def notify_error(self, error_message: str) -> bool:
        """Show error notification."""
        return self.show_notification(
            "❌ Dicto Error",
            error_message,
            timeout=5
        )


class GlobalHotkeyManager:
    """
    Global hotkey manager using pynput.
    Handles Cmd+V hotkey detection and callback execution.
    """
    
    def __init__(self, callback_func):
        self.callback_func = callback_func
        self.listener = None
        self.logger = logging.getLogger(__name__ + ".GlobalHotkeyManager")
        
        # Track key state for Cmd+V combination
        self.cmd_pressed = False
        self.keys_pressed = set()
    
    def start_listening(self) -> bool:
        """
        Start listening for global hotkeys.
        
        Returns:
            bool: True if listening started successfully.
        """
        try:
            self.listener = keyboard.Listener(
                on_press=self._on_key_press,
                on_release=self._on_key_release
            )
            self.listener.start()
            self.logger.info("Global hotkey listener started (Cmd+V)")
            return True
        except Exception as e:
            self.logger.error(f"Failed to start hotkey listener: {e}")
            return False
    
    def stop_listening(self):
        """Stop listening for global hotkeys."""
        if self.listener:
            self.listener.stop()
            self.listener = None
            self.logger.info("Global hotkey listener stopped")
    
    def _on_key_press(self, key):
        """Handle key press events."""
        try:
            # Track Cmd key
            if key == Key.cmd or key == Key.cmd_r:
                self.cmd_pressed = True
            
            # Track other keys
            self.keys_pressed.add(key)
            
            # Check for Cmd+V combination
            if self.cmd_pressed and (key == KeyCode.from_char('v') or key == KeyCode.from_char('V')):
                self.logger.info("Cmd+V detected")
                # Call the callback function
                threading.Thread(target=self.callback_func, daemon=True).start()
                
        except AttributeError:
            # Handle special keys that don't have a char representation
            pass
        except Exception as e:
            self.logger.error(f"Error in key press handler: {e}")
    
    def _on_key_release(self, key):
        """Handle key release events."""
        try:
            # Track Cmd key release
            if key == Key.cmd or key == Key.cmd_r:
                self.cmd_pressed = False
            
            # Remove from pressed keys
            self.keys_pressed.discard(key)
            
        except Exception as e:
            self.logger.error(f"Error in key release handler: {e}")


class DictoApp:
    """
    Main Dicto application class.
    Coordinates all components: hotkeys, recording, transcription, clipboard, and notifications.
    """
    
    def __init__(self, whisper_binary_path: Optional[str] = None, model_path: Optional[str] = None):
        """
        Initialize the Dicto application.
        
        Args:
            whisper_binary_path: Path to whisper-cli binary.
            model_path: Path to whisper model file.
        """
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(Path.home() / "dicto.log")
            ]
        )
        self.logger = logging.getLogger(__name__ + ".DictoApp")
        
        # Application state
        self.is_running = False
        self.is_recording = False
        self.recording_start_time = None
        
        # Initialize components
        self.logger.info("Initializing Dicto application...")
        
        try:
            # Initialize transcription engine
            self.transcription_engine = TranscriptionEngine(
                whisper_binary_path=whisper_binary_path,
                model_path=model_path,
                enable_recording=True
            )
            self.logger.info("✅ Transcription engine initialized")
            
            # Initialize clipboard manager
            self.clipboard = ClipboardManager()
            self.logger.info("✅ Clipboard manager initialized")
            
            # Initialize notification manager
            self.notifications = NotificationManager()
            self.logger.info("✅ Notification manager initialized")
            
            # Initialize global hotkey manager
            self.hotkey_manager = GlobalHotkeyManager(self._handle_hotkey)
            self.logger.info("✅ Hotkey manager initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Dicto: {e}")
            self.notifications.notify_error(f"Initialization failed: {e}")
            raise
    
    def _handle_hotkey(self):
        """
        Handle Cmd+V hotkey press.
        Toggle between recording start/stop and process transcription.
        """
        try:
            if not self.is_recording:
                # Start recording
                self._start_recording()
            else:
                # Stop recording and transcribe
                self._stop_recording_and_transcribe()
                
        except Exception as e:
            self.logger.error(f"Error handling hotkey: {e}")
            self.notifications.notify_error(f"Hotkey error: {e}")
    
    def _start_recording(self):
        """Start audio recording."""
        try:
            self.logger.info("Starting recording...")
            
            # Start recording
            success = self.transcription_engine.start_recording()
            if not success:
                raise RuntimeError("Failed to start recording")
            
            self.is_recording = True
            self.recording_start_time = time.time()
            
            # Show notification
            self.notifications.notify_recording_started()
            self.logger.info("🔴 Recording started")
            
        except Exception as e:
            self.logger.error(f"Failed to start recording: {e}")
            self.notifications.notify_error(f"Recording failed: {e}")
            self.is_recording = False
    
    def _stop_recording_and_transcribe(self):
        """Stop recording and process transcription."""
        try:
            if not self.is_recording:
                return
            
            self.logger.info("Stopping recording and starting transcription...")
            
            # Stop recording
            audio_file = self.transcription_engine.stop_recording()
            self.is_recording = False
            
            # Show notification
            self.notifications.notify_recording_stopped()
            
            if not audio_file:
                raise RuntimeError("No audio file was recorded")
            
            recording_duration = time.time() - self.recording_start_time if self.recording_start_time else 0
            self.logger.info(f"⏹️ Recording stopped ({recording_duration:.1f}s)")
            
            # Transcribe audio
            self.logger.info("Starting transcription...")
            result = self.transcription_engine.transcribe_file(audio_file)
            
            if result["success"]:
                text = result["text"].strip()
                if text:
                    # Copy to clipboard
                    if self.clipboard.set_text(text):
                        # Show success notification
                        self.notifications.notify_transcription_complete(text)
                        self.logger.info(f"✅ Transcription complete: {text[:100]}...")
                    else:
                        raise RuntimeError("Failed to copy to clipboard")
                else:
                    self.notifications.notify_error("No speech detected")
            else:
                raise RuntimeError(f"Transcription failed: {result['error']}")
            
            # Clean up audio file
            if self.transcription_engine.audio_recorder:
                self.transcription_engine.audio_recorder.cleanup_file(audio_file)
                
        except Exception as e:
            self.logger.error(f"Failed to process recording: {e}")
            self.notifications.notify_error(f"Processing failed: {e}")
            self.is_recording = False
    
    def run(self):
        """
        Start the Dicto application.
        Runs in background listening for global hotkeys.
        """
        try:
            self.logger.info("Starting Dicto application...")
            
            # Test microphone access
            if hasattr(self.transcription_engine.audio_recorder, 'test_microphone_access'):
                if not self.transcription_engine.audio_recorder.test_microphone_access():
                    error_msg = "Microphone access denied. Please grant microphone permission."
                    self.logger.error(error_msg)
                    self.notifications.notify_error(error_msg)
                    return False
            
            # Start global hotkey listener
            if not self.hotkey_manager.start_listening():
                raise RuntimeError("Failed to start global hotkey listener")
            
            self.is_running = True
            
            # Show startup notification
            self.notifications.show_notification(
                "🎙️ Dicto Started",
                "Press Cmd+V anywhere to start voice transcription"
            )
            
            self.logger.info("🎙️ Dicto is running. Press Cmd+V to start transcription.")
            self.logger.info("Press Ctrl+C to exit.")
            
            # Main application loop
            try:
                while self.is_running:
                    time.sleep(0.1)
            except KeyboardInterrupt:
                self.logger.info("Received interrupt signal")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start Dicto: {e}")
            self.notifications.notify_error(f"Startup failed: {e}")
            return False
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Shutdown the application gracefully."""
        try:
            self.logger.info("Shutting down Dicto...")
            self.is_running = False
            
            # Stop any active recording
            if self.is_recording:
                self.transcription_engine.stop_recording()
                self.is_recording = False
            
            # Stop hotkey listener
            if self.hotkey_manager:
                self.hotkey_manager.stop_listening()
            
            # Cleanup transcription engine
            if self.transcription_engine:
                self.transcription_engine.cleanup()
            
            self.logger.info("✅ Dicto shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")


def main():
    """Main entry point for the Dicto application."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Dicto - System-wide voice transcription")
    parser.add_argument("--whisper-binary", type=str, help="Path to whisper-cli binary")
    parser.add_argument("--model", type=str, help="Path to whisper model file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create and run the application
    try:
        app = DictoApp(
            whisper_binary_path=args.whisper_binary,
            model_path=args.model
        )
        
        # Set up signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            print("\nReceived signal, shutting down...")
            app.shutdown()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Run the application
        success = app.run()
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 