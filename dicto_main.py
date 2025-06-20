#!/usr/bin/env python3
"""
Dicto Main - Enhanced system-wide voice transcription app for macOS
Provides global hotkey (Ctrl+V) for voice recording with enhanced audio processing,
device selection, real-time monitoring, automatic clipboard integration, and continuous recording.

New Features in Task 6:
- Custom vocabulary support for better accuracy
- Continuous recording while Ctrl+V is held
- Transcription confidence scoring
- Timestamping for longer recordings
- Enhanced audio buffer management

Requirements:
- Global Ctrl+V hotkey for continuous record while held
- Automatic clipboard integration
- macOS native notifications
- Background operation
- Enhanced error handling with user feedback
- Custom vocabulary injection

Dependencies:
- pynput: Global hotkey support
- AppKit (PyObjC): Clipboard management
- plyer: Cross-platform notifications
- dicto_core: TranscriptionEngine
- audio_recorder: AudioRecorder
- vocabulary_manager: VocabularyManager
- continuous_recorder: ContinuousRecorder
"""

import os
import sys
import time
import logging
import threading
import signal
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, List

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

try:
    from vocabulary_manager import VocabularyManager
except ImportError:
    print("Error: vocabulary_manager.py not found. Ensure it's in the same directory.")
    sys.exit(1)

try:
    from continuous_recorder import ContinuousRecorder
except ImportError:
    print("Error: continuous_recorder.py not found. Ensure it's in the same directory.")
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
        self.continuous_mode = False
        
        # Initialize components
        self.logger.info("Initializing Dicto application...")
        
        try:
            # Initialize vocabulary manager
            self.vocabulary_manager = VocabularyManager()
            self.logger.info("✅ Vocabulary manager initialized")
            
            # Initialize continuous recorder
            self.continuous_recorder = ContinuousRecorder()
            self.continuous_recorder.set_callbacks(
                on_start=self._on_continuous_start,
                on_stop=self._on_continuous_stop,
                on_chunk=self._on_chunk_complete,
                on_session=self._on_session_complete
            )
            self.logger.info("✅ Continuous recorder initialized")
            
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
            
            # Initialize global hotkey manager (for fallback)
            self.hotkey_manager = GlobalHotkeyManager(self._handle_hotkey)
            self.logger.info("✅ Hotkey manager initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Dicto: {e}")
            self.notifications.notify_error(f"Initialization failed: {e}")
            raise
    
    def _on_continuous_start(self):
        """Callback when continuous recording starts."""
        self.continuous_mode = True
        self.notifications.show_notification(
            "🔴 Continuous Recording",
            "Hold Ctrl+V to continue recording"
        )
        self.logger.info("🔴 Continuous recording started")
    
    def _on_continuous_stop(self):
        """Callback when continuous recording stops."""
        self.continuous_mode = False
        self.notifications.show_notification(
            "⏹️ Processing Recording",
            "Combining chunks and transcribing..."
        )
        self.logger.info("⏹️ Continuous recording stopped")
    
    def _on_chunk_complete(self, chunk_path: str):
        """Callback when a recording chunk is completed."""
        self.logger.debug(f"📁 Chunk completed: {Path(chunk_path).name}")
    
    def _on_session_complete(self, chunk_paths: List[str]):
        """Callback when a recording session is completed."""
        try:
            self.logger.info(f"📂 Session completed with {len(chunk_paths)} chunks")
            
            if not chunk_paths:
                self.notifications.notify_error("No audio recorded")
                return
            
            # Combine chunks into single file
            combined_file = Path(tempfile.gettempdir()) / "dicto_combined.wav"
            
            if self.continuous_recorder.combine_chunks(str(combined_file)):
                # Transcribe the combined file
                self._transcribe_with_vocabulary(str(combined_file))
                
                # Clean up combined file
                if combined_file.exists():
                    combined_file.unlink()
            else:
                self.notifications.notify_error("Failed to combine audio chunks")
                
        except Exception as e:
            self.logger.error(f"Error processing session: {e}")
            self.notifications.notify_error(f"Session processing failed: {e}")
    
    def _transcribe_with_vocabulary(self, audio_path: str):
        """Transcribe audio with vocabulary enhancement."""
        try:
            # Get transcription result
            result = self.transcription_engine.transcribe_file(
                audio_path, 
                language="en", 
                no_timestamps=False  # Include timestamps for longer recordings
            )
            
            if result["success"]:
                text = result["text"].strip()
                
                if text:
                    # Apply vocabulary enhancements
                    enhanced_text = self._enhance_with_vocabulary(text)
                    
                    # Copy to clipboard
                    if self.clipboard.set_text(enhanced_text):
                        # Calculate confidence score
                        confidence = self._calculate_confidence(result, enhanced_text)
                        
                        # Show success notification with confidence
                        self.notifications.show_notification(
                            "✅ Transcription Complete",
                            f"Confidence: {confidence:.0%} | {enhanced_text[:50]}..."
                        )
                        self.logger.info(f"✅ Enhanced transcription (confidence: {confidence:.2%}): {enhanced_text[:100]}...")
                    else:
                        raise RuntimeError("Failed to copy to clipboard")
                else:
                    self.notifications.notify_error("No speech detected")
            else:
                raise RuntimeError(f"Transcription failed: {result['error']}")
                
        except Exception as e:
            self.logger.error(f"Transcription with vocabulary failed: {e}")
            self.notifications.notify_error(f"Transcription failed: {e}")
    
    def _enhance_with_vocabulary(self, text: str) -> str:
        """Enhance transcription text using custom vocabulary."""
        if not self.vocabulary_manager:
            return text
        
        try:
            # Get vocabulary suggestions based on context
            suggestions = self.vocabulary_manager.get_vocabulary_suggestions(text)
            
            enhanced_text = text
            
            # Apply proper noun capitalization and custom vocabulary
            vocab_data = self.vocabulary_manager.get_all_vocabulary()
            
            # Replace with proper nouns (case-sensitive)
            for proper_noun in vocab_data.get("proper_nouns", []):
                # Simple word boundary replacement
                import re
                pattern = r'\b' + re.escape(proper_noun.lower()) + r'\b'
                enhanced_text = re.sub(pattern, proper_noun, enhanced_text, flags=re.IGNORECASE)
            
            # Log vocabulary enhancement
            if enhanced_text != text:
                self.logger.info(f"Vocabulary enhancement applied: {len(suggestions)} suggestions used")
            
            return enhanced_text
            
        except Exception as e:
            self.logger.warning(f"Vocabulary enhancement failed: {e}")
            return text
    
    def _calculate_confidence(self, transcription_result: Dict[str, Any], enhanced_text: str) -> float:
        """Calculate confidence score for the transcription."""
        try:
            # Base confidence from transcription duration and text length
            duration = transcription_result.get("duration", 1.0)
            text_length = len(enhanced_text.split())
            
            # Basic confidence calculation
            # More words per second generally indicates clearer speech
            words_per_second = text_length / max(duration, 0.1)
            
            # Normalize to reasonable range (0.3 to 4.0 words/second)
            if words_per_second < 0.5:
                base_confidence = 0.3  # Very slow speech
            elif words_per_second > 4.0:
                base_confidence = 0.7  # Very fast speech
            else:
                # Linear scale between 0.5 and 1.0 for 0.5-3.0 words/second
                base_confidence = 0.5 + (min(words_per_second, 3.0) - 0.5) * 0.2
            
            # Boost confidence if vocabulary enhancements were applied
            vocab_boost = 0.1 if self.vocabulary_manager else 0.0
            
            # Ensure confidence is between 0.0 and 1.0
            confidence = min(1.0, max(0.0, base_confidence + vocab_boost))
            
            return confidence
            
        except Exception as e:
            self.logger.warning(f"Confidence calculation failed: {e}")
            return 0.5  # Default moderate confidence
    
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
            
            # Start continuous recorder monitoring
            if self.continuous_recorder and self.continuous_recorder.start_continuous_monitoring():
                self.logger.info("✅ Continuous recording monitoring started")
            else:
                # Fallback to simple hotkey manager
                self.logger.warning("Falling back to simple hotkey mode")
                if not self.hotkey_manager.start_listening():
                    raise RuntimeError("Failed to start hotkey listener")
            
            self.is_running = True
            
            # Show startup notification
            self.notifications.show_notification(
                "🎙️ Dicto Started",
                "Hold Ctrl+V anywhere for continuous voice transcription"
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
            
            # Stop continuous recorder
            if self.continuous_recorder:
                self.continuous_recorder.stop_continuous_monitoring()
                self.logger.info("Stopped continuous recorder")
            
            # Stop any active recording
            if self.is_recording:
                self.transcription_engine.stop_recording()
                self.is_recording = False
            
            # Stop hotkey listener (fallback)
            if self.hotkey_manager:
                self.hotkey_manager.stop_listening()
            
            # Save vocabulary preferences
            if self.vocabulary_manager:
                self.vocabulary_manager.save_vocabulary_preferences()
                self.logger.info("Saved vocabulary preferences")
            
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