#!/usr/bin/env python3
"""
Dicto Simple - AI Transcription App using macOS built-in audio recording
A simple transcription app using whisper.cpp with global hotkeys, using system audio recording.
"""

import os
import sys
import subprocess
import tempfile
import time
import threading
from pathlib import Path
from typing import Optional

from pynput import keyboard
from plyer import notification
import AppKit
from AppKit import NSPasteboard, NSStringPboardType


class DictoSimple:
    def __init__(self):
        self.is_recording = False
        self.record_process = None
        self.whisper_path = Path("whisper.cpp/build/bin/whisper-cli")
        self.model_path = Path("whisper.cpp/models/ggml-base.en.bin")
        self.temp_dir = Path(tempfile.gettempdir()) / "dicto"
        self.temp_dir.mkdir(exist_ok=True)
        
        # Check if paths exist
        self.validate_setup()
        
        print("🎤 Dicto Simple AI Transcription App Started!")
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
        
        # Check if sox is available for audio recording
        try:
            subprocess.run(["which", "sox"], check=True, capture_output=True)
            print("✅ SoX found for audio recording")
        except subprocess.CalledProcessError:
            print("⚠️  SoX not found, installing via Homebrew...")
            try:
                subprocess.run(["brew", "install", "sox"], check=True)
                print("✅ SoX installed successfully")
            except subprocess.CalledProcessError:
                print("❌ Failed to install SoX. Please install manually: brew install sox")
                raise
        
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
        """Start audio recording using SoX."""
        if self.is_recording:
            return
            
        try:
            timestamp = int(time.time())
            self.audio_file = self.temp_dir / f"recording_{timestamp}.wav"
            
            # Use SoX to record audio
            cmd = [
                "sox", "-t", "coreaudio", "default",
                str(self.audio_file),
                "rate", "16000",
                "channels", "1"
            ]
            
            self.record_process = subprocess.Popen(cmd)
            self.is_recording = True
            
            print("🔴 Recording started...")
            self.show_notification("Dicto", "🔴 Recording started")
            
        except Exception as e:
            print(f"Recording error: {e}")
            self.is_recording = False
            self.show_notification("Dicto Error", f"Recording failed: {e}")
    
    def stop_recording(self):
        """Stop recording and transcribe."""
        if not self.is_recording:
            return
            
        self.is_recording = False
        
        if self.record_process:
            self.record_process.terminate()
            self.record_process.wait()
            self.record_process = None
            
        print("⏹️ Recording stopped. Transcribing...")
        self.show_notification("Dicto", "⏹️ Processing audio...")
        
        # Process the recording
        threading.Thread(target=self._process_recording).start()
    
    def _process_recording(self):
        """Process the recorded audio and transcribe it."""
        try:
            if not hasattr(self, 'audio_file') or not self.audio_file.exists():
                self.show_notification("Dicto", "No audio recorded")
                return
            
            print(f"💾 Audio saved to {self.audio_file}")
            
            # Transcribe using whisper.cpp
            transcription = self._transcribe_audio(self.audio_file)
            
            if transcription:
                # Copy to clipboard
                self.copy_to_clipboard(transcription)
                self.show_notification("Dicto", f"✅ Transcribed: {transcription[:50]}...")
                print(f"📝 Transcription: {transcription}")
            else:
                self.show_notification("Dicto", "❌ Transcription failed")
                
            # Clean up temp file
            try:
                self.audio_file.unlink()
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
        if self.is_recording and self.record_process:
            self.record_process.terminate()
            self.record_process.wait()
    
    def run(self):
        """Run the main application loop."""
        try:
            # Set up hotkeys
            with keyboard.GlobalHotKeys({
                '<cmd>+v': self.on_hotkey_triggered,
                '<cmd>+q': self.on_quit_triggered
            }) as hotkeys:
                # Keep the application running
                hotkeys.join()
                
        except KeyboardInterrupt:
            print("\n👋 Shutting down Dicto...")
        finally:
            self.cleanup()


def main():
    """Main entry point."""
    print("🚀 Starting Dicto Simple AI Transcription App...")
    
    try:
        app = DictoSimple()
        app.run()
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 