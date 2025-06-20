#!/usr/bin/env python3
"""
Dicto Core - Python wrapper around whisper.cpp for audio transcription
This module provides a TranscriptionEngine class that handles audio file transcription
and integrates with SoX-based audio recording.
"""

import os
import sys
import subprocess
import tempfile
import time
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from audio_recorder import AudioRecorder


class TranscriptionEngine:
    """
    A Python wrapper around whisper.cpp for audio transcription with integrated recording.
    
    This class provides an interface to transcribe audio files using whisper.cpp
    and record audio using SoX, with proper error handling and logging.
    """
    
    def __init__(self, whisper_binary_path: Optional[str] = None, model_path: Optional[str] = None, 
                 enable_recording: bool = True):
        """
        Initialize the TranscriptionEngine.
        
        Args:
            whisper_binary_path: Path to whisper-cli binary. If None, uses default location.
            model_path: Path to whisper model file. If None, uses default location.
            enable_recording: Whether to initialize audio recording capabilities.
        
        Raises:
            FileNotFoundError: If whisper binary or model is not found.
            RuntimeError: If setup validation fails.
        """
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Set default paths
        self.whisper_path = Path(whisper_binary_path) if whisper_binary_path else Path("whisper.cpp/build/bin/whisper-cli")
        self.model_path = Path(model_path) if model_path else Path("whisper.cpp/models/ggml-base.en.bin")
        
        # Create temp directory for processing
        self.temp_dir = Path(tempfile.gettempdir()) / "dicto_core"
        self.temp_dir.mkdir(exist_ok=True)
        
        # Initialize audio recorder if enabled
        self.audio_recorder = None
        if enable_recording:
            try:
                self.audio_recorder = AudioRecorder(str(self.temp_dir))
                self.logger.info("Audio recording capabilities enabled")
            except Exception as e:
                self.logger.warning(f"Audio recording disabled: {e}")
                self.audio_recorder = None
        
        # Validate setup
        self._validate_setup()
        
        self.logger.info("TranscriptionEngine initialized successfully")
        
    def _validate_setup(self):
        """
        Validate that whisper binary and model are available.
        
        Raises:
            FileNotFoundError: If required files are not found.
            RuntimeError: If whisper binary is not executable.
        """
        self.logger.info("Validating whisper.cpp setup...")
        
        # Check whisper binary
        if not self.whisper_path.exists():
            raise FileNotFoundError(f"Whisper CLI binary not found at {self.whisper_path}")
        
        if not os.access(self.whisper_path, os.X_OK):
            raise RuntimeError(f"Whisper CLI binary is not executable: {self.whisper_path}")
        
        # Check model file
        if not self.model_path.exists():
            raise FileNotFoundError(f"Whisper model not found at {self.model_path}")
        
        # Test whisper binary with help command
        try:
            result = subprocess.run([str(self.whisper_path), "--help"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                raise RuntimeError(f"Whisper binary test failed: {result.stderr}")
        except subprocess.TimeoutExpired:
            raise RuntimeError("Whisper binary test timed out")
        except Exception as e:
            raise RuntimeError(f"Failed to test whisper binary: {e}")
        
        self.logger.info("✅ Whisper.cpp setup validation successful")
        self.logger.info(f"✅ Binary: {self.whisper_path}")
        self.logger.info(f"✅ Model: {self.model_path}")
    
    def transcribe_file(self, audio_path: str, language: str = "en", no_timestamps: bool = True) -> Dict[str, Any]:
        """
        Transcribe an audio file using whisper.cpp.
        
        Args:
            audio_path: Path to the audio file to transcribe.
            language: Language code for transcription (default: "en").
            no_timestamps: Whether to exclude timestamps from output (default: True).
        
        Returns:
            Dict containing:
                - success: bool indicating if transcription was successful
                - text: str containing transcribed text (if successful)
                - error: str containing error message (if failed)
                - duration: float time taken for transcription
                - file_path: str path to the audio file processed
        
        Raises:
            FileNotFoundError: If audio file does not exist.
        """
        start_time = time.time()
        
        # Validate input file
        audio_file = Path(audio_path)
        if not audio_file.exists():
            error_msg = f"Audio file not found: {audio_path}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "text": "",
                "error": error_msg,
                "duration": 0.0,
                "file_path": str(audio_path)
            }
        
        self.logger.info(f"Starting transcription of: {audio_path}")
        
        # Create temporary output file
        timestamp = int(time.time())
        temp_output = self.temp_dir / f"transcription_{timestamp}"
        
        try:
            # Build whisper command
            cmd = [
                str(self.whisper_path),
                "-m", str(self.model_path),
                "-f", str(audio_file),
                "-l", language,
                "--output-file", str(temp_output)
            ]
            
            if no_timestamps:
                cmd.append("--no-timestamps")
            
            # Add text output format
            cmd.extend(["--output-txt"])
            
            self.logger.info(f"Running whisper command: {' '.join(cmd)}")
            
            # Execute whisper
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            duration = time.time() - start_time
            
            if result.returncode == 0:
                # Read transcription from output file
                txt_file = temp_output.with_suffix(".txt")
                
                if txt_file.exists():
                    transcription = txt_file.read_text().strip()
                    
                    # Clean up temporary file
                    try:
                        txt_file.unlink()
                    except Exception as e:
                        self.logger.warning(f"Failed to clean up temp file: {e}")
                    
                    self.logger.info(f"Transcription successful in {duration:.2f}s")
                    self.logger.info(f"Result: {transcription[:100]}...")
                    
                    return {
                        "success": True,
                        "text": transcription,
                        "error": "",
                        "duration": duration,
                        "file_path": str(audio_path)
                    }
                else:
                    error_msg = "Whisper output file not found"
                    self.logger.error(error_msg)
                    return {
                        "success": False,
                        "text": "",
                        "error": error_msg,
                        "duration": duration,
                        "file_path": str(audio_path)
                    }
            else:
                error_msg = f"Whisper process failed: {result.stderr}"
                self.logger.error(error_msg)
                self.logger.error(f"Whisper stdout: {result.stdout}")
                
                return {
                    "success": False,
                    "text": "",
                    "error": error_msg,
                    "duration": duration,
                    "file_path": str(audio_path)
                }
                
        except subprocess.TimeoutExpired:
            error_msg = "Whisper process timed out"
            self.logger.error(error_msg)
            return {
                "success": False,
                "text": "",
                "error": error_msg,
                "duration": time.time() - start_time,
                "file_path": str(audio_path)
            }
        except Exception as e:
            error_msg = f"Unexpected error during transcription: {e}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "text": "",
                "error": error_msg,
                "duration": time.time() - start_time,
                "file_path": str(audio_path)
            }
    
    def start_recording(self, duration: Optional[float] = None) -> bool:
        """
        Start audio recording using SoX.
        
        Args:
            duration: Maximum recording duration in seconds. If None, records until stopped.
        
        Returns:
            bool: True if recording started successfully, False otherwise.
        """
        if not self.audio_recorder:
            self.logger.error("Audio recording not available")
            return False
        
        try:
            self.audio_recorder.start_recording(duration)
            return True
        except Exception as e:
            self.logger.error(f"Failed to start recording: {e}")
            return False
    
    def stop_recording(self) -> Optional[str]:
        """
        Stop audio recording and return the recorded file path.
        
        Returns:
            Optional[str]: Path to the recorded audio file, or None if no recording was active.
        """
        if not self.audio_recorder:
            self.logger.error("Audio recording not available")
            return None
        
        try:
            return self.audio_recorder.stop_recording()
        except Exception as e:
            self.logger.error(f"Failed to stop recording: {e}")
            return None
    
    def is_recording(self) -> bool:
        """
        Check if recording is currently active.
        
        Returns:
            bool: True if recording is active, False otherwise.
        """
        if not self.audio_recorder:
            return False
        return self.audio_recorder.is_recording_active()
    
    def record_and_transcribe(self, duration: Optional[float] = None, 
                             language: str = "en", no_timestamps: bool = True,
                             cleanup_audio: bool = True) -> Dict[str, Any]:
        """
        Record audio and immediately transcribe it.
        
        Args:
            duration: Maximum recording duration in seconds. If None, records until stopped manually.
            language: Language code for transcription (default: "en").
            no_timestamps: Whether to exclude timestamps from output (default: True).
            cleanup_audio: Whether to delete the audio file after transcription (default: True).
        
        Returns:
            Dict containing:
                - success: bool indicating if the operation was successful
                - text: str containing transcribed text (if successful)
                - error: str containing error message (if failed)
                - audio_file: str path to the recorded audio file
                - recording_duration: float time spent recording
                - transcription_duration: float time spent transcribing
        """
        start_time = time.time()
        
        if not self.audio_recorder:
            error_msg = "Audio recording not available"
            self.logger.error(error_msg)
            return {
                "success": False,
                "text": "",
                "error": error_msg,
                "audio_file": "",
                "recording_duration": 0.0,
                "transcription_duration": 0.0
            }
        
        # Start recording
        if not self.start_recording(duration):
            error_msg = "Failed to start recording"
            return {
                "success": False,
                "text": "",
                "error": error_msg,
                "audio_file": "",
                "recording_duration": 0.0,
                "transcription_duration": 0.0
            }
        
        self.logger.info("🔴 Recording started. Press Ctrl+C or call stop_recording() to stop...")
        
        # If duration is specified, wait for that duration
        if duration:
            time.sleep(duration)
            recording_end_time = time.time()
        else:
            # Wait for manual stop (this would typically be called from UI)
            self.logger.info("Recording indefinitely until stop_recording() is called...")
            # In a real application, this would be handled by the UI
            # For now, we'll just wait a bit and stop
            time.sleep(5)  # Default 5 seconds for testing
            recording_end_time = time.time()
        
        # Stop recording
        audio_file = self.stop_recording()
        recording_duration = recording_end_time - start_time
        
        if not audio_file:
            error_msg = "No audio file was recorded"
            self.logger.error(error_msg)
            return {
                "success": False,
                "text": "",
                "error": error_msg,
                "audio_file": "",
                "recording_duration": recording_duration,
                "transcription_duration": 0.0
            }
        
        self.logger.info(f"⏹️ Recording completed: {audio_file}")
        
        # Transcribe the recorded audio
        transcription_start = time.time()
        result = self.transcribe_file(audio_file, language, no_timestamps)
        transcription_duration = time.time() - transcription_start
        
        # Clean up audio file if requested
        if cleanup_audio and self.audio_recorder:
            self.audio_recorder.cleanup_file(audio_file)
        
        # Return combined result
        return {
            "success": result["success"],
            "text": result["text"],
            "error": result["error"],
            "audio_file": audio_file,
            "recording_duration": recording_duration,
            "transcription_duration": transcription_duration
        }
    
    def get_supported_formats(self) -> list:
        """
        Get list of supported audio formats.
        
        Returns:
            List of supported file extensions.
        """
        return [".wav", ".mp3", ".m4a", ".ogg", ".flac", ".aac"]
    
    def get_recording_info(self) -> Dict[str, Any]:
        """
        Get information about recording capabilities.
        
        Returns:
            Dict containing recording format information.
        """
        if not self.audio_recorder:
            return {"available": False, "reason": "Audio recorder not initialized"}
        
        try:
            format_info = self.audio_recorder.get_supported_formats()
            format_info["available"] = True
            return format_info
        except Exception as e:
            return {"available": False, "reason": str(e)}
    
    def cleanup(self):
        """Clean up temporary files and resources."""
        try:
            # Stop any active recording
            if self.audio_recorder and self.audio_recorder.is_recording_active():
                self.audio_recorder.stop_recording()
            
            # Clean up old audio files
            if self.audio_recorder:
                self.audio_recorder.cleanup_old_files()
            
            # Remove temporary directory if empty
            if self.temp_dir.exists() and not any(self.temp_dir.iterdir()):
                self.temp_dir.rmdir()
                self.logger.info("Cleaned up temporary directory")
        except Exception as e:
            self.logger.warning(f"Failed to clean up temporary directory: {e}")


def main():
    """
    Simple command-line interface for testing the TranscriptionEngine.
    """
    if len(sys.argv) != 2:
        print("Usage: python dicto_core.py <audio_file>")
        sys.exit(1)
    
    audio_file = sys.argv[1]
    
    try:
        # Initialize engine
        engine = TranscriptionEngine()
        
        # Transcribe file
        result = engine.transcribe_file(audio_file)
        
        # Print results
        print(f"\n{'='*50}")
        print("TRANSCRIPTION RESULT")
        print(f"{'='*50}")
        print(f"File: {result['file_path']}")
        print(f"Success: {result['success']}")
        print(f"Duration: {result['duration']:.2f}s")
        
        if result['success']:
            print(f"Text: {result['text']}")
        else:
            print(f"Error: {result['error']}")
        
        # Cleanup
        engine.cleanup()
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 