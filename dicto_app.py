#!/usr/bin/env python3
"""
Dicto - AI Transcription App with Global Hotkeys
A simple transcription app using whisper.cpp that works with Cmd+V hotkey on Mac.
"""

import os
import sys
import subprocess
import tempfile
import time
import threading
from pathlib import Path
from typing import Optional

import pyaudio
import wave
from pynput import keyboard
from pynput.keyboard import Key, KeyCode
from plyer import notification
import AppKit
from AppKit import NSPasteboard, NSStringPboardType


class DictoApp:
    def __init__(self):
        self.is_recording = False
        self.audio_stream = None
        self.audio_data = []
        self.whisper_path = Path("whisper.cpp/build/bin/whisper-cli")
        self.model_path = Path("whisper.cpp/models/ggml-base.en.bin")
        self.temp_dir = Path(tempfile.gettempdir()) / "dicto"
        self.temp_dir.mkdir(exist_ok=True)
        
        # Audio settings
        self.chunk = 1024
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 16000
        
        # Initialize PyAudio
        self.audio = pyaudio.PyAudio()
        
        # Check if paths exist
        self.validate_setup()
        
        print("🎤 Dicto AI Transcription App Started!")
        print("📌 Press Cmd+V to start/stop recording")
        print("📌 Recording will automatically transcribe when stopped")
        print("📌 Transcription will be copied to clipboard")
        print("📌 Press Cmd+Q to quit")
        
    def validate_setup(self):
        """Validate that whisper.cpp is properly set up."""
        if not self.whisper_path.exists():
            raise FileNotFoundError(f"Whisper CLI not found at {self.whisper_path}")
        if not self.model_path.exists():
            raise FileNotFoundError(f"Whisper model not found at {self.model_path}")
        print("✅ Whisper.cpp setup validated")
        
    def show_notification(self, title: str, message: str):
        """Show a macOS notification."""
        try:
            notification.notify(
                title=title,
                message=message,
                app_name="Dicto",
                timeout=3
            )
        except Exception as e:
            print(f"Notification error: {e}")
            
    def copy_to_clipboard(self, text: str):
        """Copy text to macOS clipboard."""
        try:
            pasteboard = NSPasteboard.generalPasteboard()
            pasteboard.clearContents()
            pasteboard.setString_forType_(text, NSStringPboardType)
            print(f"📋 Copied to clipboard: {text[:50]}...")
        except Exception as e:
            print(f"Clipboard error: {e}")
    
    def start_recording(self):
        """Start audio recording."""
        if self.is_recording:
            return
            
        try:
            self.is_recording = True
            self.audio_data = []
            
            self.audio_stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk
            )
            
            print("🔴 Recording started...")
            self.show_notification("Dicto", "🔴 Recording started")
            
            # Record in background thread
            self.record_thread = threading.Thread(target=self._record_audio)
            self.record_thread.start()
            
        except Exception as e:
            print(f"Recording error: {e}")
            self.is_recording = False
            self.show_notification("Dicto Error", f"Recording failed: {e}")
    
    def _record_audio(self):
        """Record audio in background thread."""
        while self.is_recording:
            try:
                data = self.audio_stream.read(self.chunk, exception_on_overflow=False)
                self.audio_data.append(data)
            except Exception as e:
                print(f"Audio capture error: {e}")
                break
    
    def stop_recording(self):
        """Stop recording and transcribe."""
        if not self.is_recording:
            return
            
        self.is_recording = False
        
        if self.audio_stream:
            self.audio_stream.stop_stream()
            self.audio_stream.close()
            
        if hasattr(self, 'record_thread'):
            self.record_thread.join()
            
        print("⏹️ Recording stopped. Transcribing...")
        self.show_notification("Dicto", "⏹️ Processing audio...")
        
        # Process the recording
        threading.Thread(target=self._process_recording).start()
    
    def _process_recording(self):
        """Process the recorded audio and transcribe it."""
        try:
            if not self.audio_data:
                self.show_notification("Dicto", "No audio recorded")
                return
            
            # Save audio to temporary file
            timestamp = int(time.time())
            audio_file = self.temp_dir / f"recording_{timestamp}.wav"
            
            with wave.open(str(audio_file), 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(self.audio.get_sample_size(self.format))
                wf.setframerate(self.rate)
                wf.writeframes(b''.join(self.audio_data))
            
            print(f"💾 Audio saved to {audio_file}")
            
            # Transcribe using whisper.cpp
            transcription = self._transcribe_audio(audio_file)
            
            if transcription:
                # Copy to clipboard
                self.copy_to_clipboard(transcription)
                self.show_notification("Dicto", f"✅ Transcribed: {transcription[:50]}...")
                print(f"📝 Transcription: {transcription}")
            else:
                self.show_notification("Dicto", "❌ Transcription failed")
                
            # Clean up temp file
            try:
                audio_file.unlink()
            except Exception:
                pass
                
        except Exception as e:
            print(f"Processing error: {e}")
            self.show_notification("Dicto Error", f"Processing failed: {e}")
    
    def _transcribe_audio(self, audio_file: Path) -> Optional[str]:
        """Transcribe audio using whisper.cpp."""
        try:
            cmd = [
                str(self.whisper_path),
                "-m", str(self.model_path),
                "-f", str(audio_file),
                "--no-timestamps",
                "--output-txt",
                "--output-file", str(audio_file.with_suffix(""))
            ]
            
            print(f"🔄 Running whisper: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                # Read the output file
                txt_file = audio_file.with_suffix(".txt")
                if txt_file.exists():
                    transcription = txt_file.read_text().strip()
                    txt_file.unlink()  # Clean up
                    return transcription
                else:
                    print("Output file not found")
                    return None
            else:
                print(f"Whisper error: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            print("Whisper timeout")
            return None
        except Exception as e:
            print(f"Transcription error: {e}")
            return None
    
    def on_hotkey_triggered(self):
        """Handle hotkey press."""
        if self.is_recording:
            self.stop_recording()
        else:
            self.start_recording()
    
    def on_quit_triggered(self):
        """Handle quit hotkey."""
        print("👋 Shutting down Dicto...")
        self.cleanup()
        sys.exit(0)
    
    def cleanup(self):
        """Clean up resources."""
        if self.is_recording:
            self.stop_recording()
        if self.audio:
            self.audio.terminate()
    
    def run(self):
        """Run the main application loop."""
        try:
            # Set up hotkeys
            with keyboard.GlobalHotKeys({
                '<cmd>+v': self.on_hotkey_triggered,
                '<cmd>+q': self.on_quit_triggered
            }):
                # Keep the application running
                keyboard.Listener(on_press=lambda key: None).join()
                
        except KeyboardInterrupt:
            print("\n👋 Shutting down Dicto...")
        finally:
            self.cleanup()


def main():
    """Main entry point."""
    print("🚀 Starting Dicto AI Transcription App...")
    
    try:
        app = DictoApp()
        app.run()
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 