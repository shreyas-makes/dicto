#!/usr/bin/env python3
"""
Audio Recorder - SoX-based audio recording for Dicto
This module provides an AudioRecorder class that uses SoX for recording audio
in the optimal format for Whisper transcription (16kHz mono WAV).
"""

import os
import sys
import subprocess
import tempfile
import time
import logging
import signal
import shutil
import platform
from pathlib import Path
from typing import Optional, Dict, Any
import threading


class AudioRecorder:
    """
    SoX-based audio recorder optimized for Whisper transcription.
    
    Records audio at 16kHz mono WAV format which is optimal for Whisper.
    Provides non-blocking recording with proper cleanup and error handling.
    """
    
    def __init__(self, temp_dir: Optional[str] = None):
        """
        Initialize the AudioRecorder.
        
        Args:
            temp_dir: Directory for temporary audio files. If None, uses system temp.
        
        Raises:
            RuntimeError: If SoX is not available or setup fails.
        """
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
        # Set up temp directory
        self.temp_dir = Path(temp_dir) if temp_dir else Path(tempfile.gettempdir()) / "dicto_audio"
        self.temp_dir.mkdir(exist_ok=True)
        
        # Recording state
        self.is_recording = False
        self.recording_process = None
        self.current_file = None
        self.recording_thread = None
        
        # Platform detection
        self.is_macos = platform.system() == "Darwin"
        
        # Validate SoX installation
        self.check_dependencies()
        
        self.logger.info("AudioRecorder initialized successfully")
    
    def check_dependencies(self) -> bool:
        """
        Check if SoX is installed and available.
        
        Returns:
            bool: True if SoX is available, False otherwise.
        
        Raises:
            RuntimeError: If SoX is not available.
        """
        self.logger.info("Checking SoX installation...")
        
        # Check if SoX is in PATH
        sox_path = shutil.which("sox")
        if not sox_path:
            # Try common installation paths on macOS
            common_paths = [
                "/usr/local/bin/sox",
                "/opt/homebrew/bin/sox",
                "/usr/bin/sox"
            ]
            
            for path in common_paths:
                if os.path.exists(path) and os.access(path, os.X_OK):
                    sox_path = path
                    break
            
            if not sox_path:
                error_msg = (
                    "SoX not found. Please install SoX using:\n"
                    "  brew install sox\n"
                    "or download from: http://sox.sourceforge.net/"
                )
                self.logger.error(error_msg)
                raise RuntimeError(error_msg)
        
        # Test SoX with version command
        try:
            result = subprocess.run([sox_path, "--version"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                version_info = result.stdout.strip()
                self.logger.info(f"✅ SoX found: {version_info}")
                self.sox_path = sox_path
                return True
            else:
                raise RuntimeError(f"SoX test failed: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            raise RuntimeError("SoX version check timed out")
        except Exception as e:
            raise RuntimeError(f"Failed to test SoX: {e}")
    
    def test_microphone_access(self) -> bool:
        """
        Test if microphone access is available by attempting a short recording.
        
        Returns:
            bool: True if microphone access works, False otherwise.
        """
        self.logger.info("Testing microphone access...")
        
        # Generate test filename
        test_file = self.temp_dir / "mic_test.wav"
        
        try:
            # Try a very short recording (0.1 seconds)
            cmd = [
                self.sox_path,
                "-d",  # Use default input device
                "-r", "16000",  # 16kHz sample rate
                "-c", "1",      # Mono
                "-b", "16",     # 16-bit depth
                str(test_file),
                "trim", "0", "0.1"  # Record for 0.1 seconds
            ]
            
            # Start the process with a timeout
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for completion with timeout
            try:
                stdout, stderr = process.communicate(timeout=5)
                
                if process.returncode == 0:
                    # Check if file was created and has some content
                    if test_file.exists() and test_file.stat().st_size > 0:
                        self.logger.info("✅ Microphone access test successful")
                        test_file.unlink()  # Clean up test file
                        return True
                    else:
                        self.logger.warning("Microphone test: No audio data recorded")
                        return False
                else:
                    # Check for common permission errors
                    error_output = stderr.lower()
                    if any(keyword in error_output for keyword in ['permission', 'denied', 'access', 'authorization']):
                        self.logger.error("❌ Microphone permission denied")
                        if self.is_macos:
                            self.logger.error("On macOS, you need to grant microphone permission to your terminal/application.")
                            self.logger.error("Go to System Preferences > Security & Privacy > Privacy > Microphone")
                    else:
                        self.logger.error(f"Microphone test failed: {stderr}")
                    return False
                    
            except subprocess.TimeoutExpired:
                # Process hung - likely permission issue
                process.kill()
                process.wait()
                self.logger.error("❌ Microphone test timed out - likely permission issue")
                if self.is_macos:
                    self.logger.error("On macOS, grant microphone permission to your terminal/application")
                    self.logger.error("Go to System Preferences > Security & Privacy > Privacy > Microphone")
                return False
                
        except Exception as e:
            self.logger.error(f"Microphone test error: {e}")
            return False
        finally:
            # Clean up test file if it exists
            if test_file.exists():
                try:
                    test_file.unlink()
                except:
                    pass
    
    def start_recording(self, duration: Optional[float] = None) -> str:
        """
        Start audio recording using SoX.
        
        Args:
            duration: Maximum recording duration in seconds. If None, records until stopped.
        
        Returns:
            str: Path to the temporary audio file being recorded.
        
        Raises:
            RuntimeError: If recording is already in progress or SoX fails to start.
        """
        if self.is_recording:
            raise RuntimeError("Recording already in progress")
        
        # Test microphone access first
        if not self.test_microphone_access():
            error_msg = "Microphone access test failed. Cannot start recording."
            if self.is_macos:
                error_msg += " Please grant microphone permission to your terminal/application in System Preferences > Security & Privacy > Privacy > Microphone"
            raise RuntimeError(error_msg)
        
        # Generate unique filename
        timestamp = int(time.time() * 1000)  # milliseconds for uniqueness
        self.current_file = self.temp_dir / f"recording_{timestamp}.wav"
        
        # Build SoX command for recording
        # Record at 16kHz mono WAV (optimal for Whisper)
        cmd = [
            self.sox_path,
            "-d",  # Use default input device
            "-r", "16000",  # 16kHz sample rate
            "-c", "1",      # Mono
            "-b", "16",     # 16-bit depth
            str(self.current_file)
        ]
        
        # Add duration if specified
        if duration:
            cmd.extend(["trim", "0", str(duration)])
        
        self.logger.info(f"Starting SoX recording: {' '.join(cmd)}")
        
        try:
            # Start SoX recording process
            self.recording_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Quick check that process started successfully
            time.sleep(0.1)  # Give it a moment to start
            if self.recording_process.poll() is not None:
                # Process already exited - likely an error
                stdout, stderr = self.recording_process.communicate()
                error_msg = f"SoX recording failed to start: {stderr}"
                self.logger.error(error_msg)
                raise RuntimeError(error_msg)
            
            self.is_recording = True
            
            # Start monitoring thread
            self.recording_thread = threading.Thread(target=self._monitor_recording)
            self.recording_thread.start()
            
            self.logger.info(f"🔴 Recording started to: {self.current_file}")
            return str(self.current_file)
            
        except Exception as e:
            self.is_recording = False
            self.recording_process = None
            error_msg = f"Failed to start SoX recording: {e}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def _monitor_recording(self):
        """Monitor the recording process in a separate thread."""
        if self.recording_process:
            try:
                # Wait for process to complete with timeout for safety
                try:
                    stdout, stderr = self.recording_process.communicate(timeout=3600)  # 1 hour max
                except subprocess.TimeoutExpired:
                    # Recording ran too long, terminate it
                    self.logger.warning("Recording timed out after 1 hour, terminating")
                    self.recording_process.kill()
                    stdout, stderr = self.recording_process.communicate()
                
                # Check result
                if self.recording_process.returncode == 0:
                    self.logger.info("🎵 Recording completed successfully")
                elif self.is_recording:
                    self.logger.error(f"SoX recording error: {stderr}")
                
            except Exception as e:
                self.logger.error(f"Recording monitor error: {e}")
            finally:
                # Don't automatically set is_recording = False here
                # Let stop_recording() handle the state properly
                pass
    
    def stop_recording(self) -> Optional[str]:
        """
        Stop the current recording.
        
        Returns:
            Optional[str]: Path to the recorded audio file, or None if no recording was active.
        
        Raises:
            RuntimeError: If there's an error stopping the recording.
        """
        if not self.is_recording:
            # Check if we have a current file from a completed recording
            if self.current_file and self.current_file.exists():
                file_size = self.current_file.stat().st_size
                if file_size > 1000:  # At least 1KB of audio data
                    self.logger.info(f"⏹️ Found completed recording: {self.current_file} ({file_size} bytes)")
                    return str(self.current_file)
            
            self.logger.warning("No recording in progress")
            return None
        
        self.logger.info("Stopping recording...")
        
        try:
            if self.recording_process:
                if self.recording_process.poll() is None:
                    # Process is still running, stop it gracefully
                    self.recording_process.send_signal(signal.SIGINT)
                    
                    # Wait for process to terminate (with timeout)
                    try:
                        self.recording_process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        # Force terminate if it doesn't stop gracefully
                        self.recording_process.terminate()
                        try:
                            self.recording_process.wait(timeout=2)
                        except subprocess.TimeoutExpired:
                            self.recording_process.kill()
                else:
                    # Process already finished
                    self.logger.info("Recording process already completed")
            
            self.is_recording = False
            
            # Wait for monitoring thread to finish
            if self.recording_thread and self.recording_thread.is_alive():
                self.recording_thread.join(timeout=3)
            
            # Check if file was created and has content
            if self.current_file and self.current_file.exists():
                file_size = self.current_file.stat().st_size
                if file_size > 1000:  # At least 1KB of audio data
                    self.logger.info(f"⏹️ Recording stopped. File: {self.current_file} ({file_size} bytes)")
                    return str(self.current_file)
                else:
                    self.logger.warning(f"Recording file too small: {file_size} bytes")
                    self._cleanup_file(self.current_file)
                    return None
            else:
                self.logger.warning("No recording file found")
                return None
                
        except Exception as e:
            error_msg = f"Error stopping recording: {e}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
        finally:
            self.recording_process = None
            self.recording_thread = None
    
    def is_recording_active(self) -> bool:
        """
        Check if recording is currently active.
        
        Returns:
            bool: True if recording is active, False otherwise.
        """
        return self.is_recording
    
    def get_recording_duration(self) -> float:
        """
        Get the duration of the current recording in seconds.
        
        Returns:
            float: Duration in seconds, or 0 if no recording is active.
        """
        if not self.is_recording or not self.current_file:
            return 0.0
        
        try:
            if self.current_file.exists():
                # Use SoX to get duration
                cmd = [self.sox_path, str(self.current_file), "-n", "stat"]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                
                # Parse duration from stderr (SoX outputs stats to stderr)
                for line in result.stderr.split('\n'):
                    if 'Length (seconds):' in line:
                        duration_str = line.split(':')[1].strip()
                        return float(duration_str)
        except Exception as e:
            self.logger.warning(f"Failed to get recording duration: {e}")
        
        return 0.0
    
    def cleanup_file(self, file_path: str) -> bool:
        """
        Clean up a temporary audio file.
        
        Args:
            file_path: Path to the file to clean up.
        
        Returns:
            bool: True if cleanup was successful, False otherwise.
        """
        return self._cleanup_file(Path(file_path))
    
    def _cleanup_file(self, file_path: Path) -> bool:
        """
        Internal method to clean up a file.
        
        Args:
            file_path: Path object of the file to clean up.
        
        Returns:
            bool: True if cleanup was successful, False otherwise.
        """
        try:
            if file_path.exists():
                file_path.unlink()
                self.logger.info(f"🗑️ Cleaned up: {file_path}")
                return True
        except Exception as e:
            self.logger.warning(f"Failed to clean up {file_path}: {e}")
        return False
    
    def cleanup_old_files(self, max_age_hours: float = 24) -> int:
        """
        Clean up old temporary audio files.
        
        Args:
            max_age_hours: Maximum age in hours for files to keep.
        
        Returns:
            int: Number of files cleaned up.
        """
        cleaned_count = 0
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        try:
            for file_path in self.temp_dir.glob("recording_*.wav"):
                file_age = current_time - file_path.stat().st_mtime
                if file_age > max_age_seconds:
                    if self._cleanup_file(file_path):
                        cleaned_count += 1
        except Exception as e:
            self.logger.warning(f"Error during cleanup: {e}")
        
        if cleaned_count > 0:
            self.logger.info(f"🗑️ Cleaned up {cleaned_count} old audio files")
        
        return cleaned_count
    
    def get_supported_formats(self) -> Dict[str, Any]:
        """
        Get information about supported audio formats.
        
        Returns:
            Dict containing format information.
        """
        return {
            "sample_rate": 16000,
            "channels": 1,
            "bit_depth": 16,
            "format": "WAV",
            "description": "16kHz mono WAV (optimized for Whisper)"
        }
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        if self.is_recording:
            try:
                self.stop_recording()
            except Exception:
                pass 