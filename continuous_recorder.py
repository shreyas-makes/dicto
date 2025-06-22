#!/usr/bin/env python3
"""
Continuous Recorder - Extended recording sessions for Dicto
This module provides continuous recording capabilities that activate while CTRL+V is held,
with enhanced audio buffer management for extended sessions and auto-save functionality.
"""

import os
import sys
import time
import logging
import threading
import tempfile
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable
from datetime import datetime, timedelta
import signal
import queue

# Initialize pynput availability
PYNPUT_AVAILABLE = False

try:
    from pynput import keyboard
    from pynput.keyboard import Key, KeyCode
    PYNPUT_AVAILABLE = True
except ImportError:
    print("Error: pynput not installed. Install with: pip install pynput")
    print("Continuous recording functionality will not work without pynput")
    keyboard = None
    Key = None
    KeyCode = None

# Import local modules
try:
    from audio_recorder import AudioRecorder
except ImportError:
    print("Error: audio_recorder.py not found. Ensure it's in the same directory.")
    sys.exit(1)


class ContinuousRecorder:
    """
    Handles continuous recording while CTRL+V is pressed.
    
    Provides extended recording sessions with intelligent buffer management,
    auto-save functionality, and support for very long recordings.
    """
    
    def __init__(self, 
                 chunk_duration: float = 30.0,  # 30 second chunks
                 max_session_duration: float = 3600.0,  # 1 hour max
                 auto_save_interval: float = 300.0,  # 5 minute auto-save
                 temp_dir: Optional[str] = None,
                 enable_key_detection: bool = True):
        """
        Initialize the ContinuousRecorder.
        
        Args:
            chunk_duration: Duration of each recording chunk in seconds.
            max_session_duration: Maximum recording session duration in seconds.
            auto_save_interval: Interval for auto-saving chunks in seconds.
            temp_dir: Directory for temporary audio files.
            enable_key_detection: If True, the recorder will manage key detection.
                                  Set to False if an external system (e.g., rumps)
                                  is handling hotkeys.
        """
        self.logger = logging.getLogger(__name__)
        
        self.enable_key_detection = enable_key_detection

        # Check pynput availability
        if not PYNPUT_AVAILABLE and self.enable_key_detection:
            self.logger.error("pynput not available - key detection disabled")
            self.key_detection_available = False
        else:
            self.key_detection_available = self.enable_key_detection
            if self.key_detection_available:
                self.logger.info("Using pynput for key detection")
        
        # Recording parameters
        self.chunk_duration = chunk_duration
        self.max_session_duration = max_session_duration
        self.auto_save_interval = auto_save_interval
        
        # Set up temp directory
        if temp_dir:
            self.temp_dir = Path(temp_dir)
        else:
            self.temp_dir = Path(tempfile.gettempdir()) / "dicto_continuous"
        self.temp_dir.mkdir(exist_ok=True)
        
        # Recording state
        self.is_recording = False
        self.recording_start_time = None
        self.current_session_id = None
        self.audio_chunks: List[Path] = []
        self.recording_thread = None
        self.monitoring_thread = None
        
        # Keyboard monitoring
        self.ctrl_pressed = False
        self.v_pressed = False
        self.key_listener = None
        self.continuous_mode = False
        
        # Audio recorder instance
        self.audio_recorder = AudioRecorder(temp_dir=str(self.temp_dir))
        
        # Thread-safe communication
        self.command_queue = queue.Queue()
        self.status_queue = queue.Queue()
        
        # Callbacks
        self.on_recording_start: Optional[Callable] = None
        self.on_recording_stop: Optional[Callable] = None
        self.on_chunk_complete: Optional[Callable[[str], None]] = None
        self.on_session_complete: Optional[Callable[[List[str]], None]] = None
        
        self.logger.info("ContinuousRecorder initialized")
    
    def set_callbacks(self,
                     on_start: Optional[Callable] = None,
                     on_stop: Optional[Callable] = None,
                     on_chunk: Optional[Callable[[str], None]] = None,
                     on_session: Optional[Callable[[List[str]], None]] = None):
        """
        Set callback functions for recording events.
        
        Args:
            on_start: Called when recording starts.
            on_stop: Called when recording stops.
            on_chunk: Called when a chunk is completed (receives file path).
            on_session: Called when session is complete (receives list of chunk paths).
        """
        self.on_recording_start = on_start
        self.on_recording_stop = on_stop
        self.on_chunk_complete = on_chunk
        self.on_session_complete = on_session
    
    def start_continuous_monitoring(self) -> bool:
        """
        Start monitoring for CTRL+V key combination.
        
        Returns:
            bool: True if monitoring started successfully.
        """
        try:
            if not self.enable_key_detection:
                self.logger.info("Continuous key monitoring explicitly disabled for ContinuousRecorder.")
                self._start_monitoring_loop_thread()
                return True

            if not self.key_detection_available:
                self.logger.error("Cannot start monitoring - pynput not available")
                return False
            
            # Use pynput for key detection
            if self.key_listener and self.key_listener.running:
                self.logger.warning("Key monitoring already active")
                return True
            
            self.key_listener = keyboard.Listener(
                on_press=self._on_key_press,
                on_release=self._on_key_release
            )
            self.key_listener.start()
            self.logger.info("pynput keyboard listener started successfully")
            
            # Start background monitoring thread
            self.monitoring_thread = threading.Thread(
                target=self._monitoring_loop,
                daemon=True
            )
            self.monitoring_thread.start()
            
            self.logger.info("Continuous monitoring started - Hold CTRL+V to record")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start continuous monitoring: {e}")
            return False
    
    def stop_continuous_monitoring(self):
        """Stop continuous monitoring."""
        try:
            if hasattr(self, 'key_listener') and self.key_listener:
                self.key_listener.stop()
                self.key_listener = None
            
            # Stop any active recording
            if self.is_recording:
                self._stop_recording_session()
            
            # Signal monitoring thread to stop
            self.command_queue.put("STOP")
            
            self.logger.info("Continuous monitoring stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping continuous monitoring: {e}")

    def _on_key_press(self, key):
        """Handle key press events."""
        try:
            self.logger.debug(f"Key pressed: {key}")
            
            if key == Key.ctrl_l or key == Key.ctrl_r:
                self.ctrl_pressed = True
                self.logger.debug("CTRL key pressed")
            elif hasattr(key, 'char') and key.char and key.char.lower() == 'v':
                self.v_pressed = True
                self.logger.debug("V key pressed")
            
            # Check if CTRL+V combination is active
            if self.ctrl_pressed and self.v_pressed and not self.continuous_mode:
                self.logger.info("CTRL+V combination detected - starting continuous recording")
                self.continuous_mode = True
                self.command_queue.put("START_RECORDING")
                
        except Exception as e:
            self.logger.error(f"Error in key press handler: {e}")
    
    def _on_key_release(self, key):
        """Handle key release events."""
        try:
            self.logger.debug(f"Key released: {key}")
            if key == Key.ctrl_l or key == Key.ctrl_r:
                self.ctrl_pressed = False
                self.logger.debug("CTRL key released")
            elif hasattr(key, 'char') and key.char and key.char.lower() == 'v':
                self.v_pressed = False
                self.logger.debug("V key released")
            
            # Check if CTRL+V combination is released
            if not self.ctrl_pressed or not self.v_pressed:
                if self.continuous_mode:
                    self.logger.info("CTRL+V combination released - stopping continuous recording")
                    self.continuous_mode = False
                    self.command_queue.put("STOP_RECORDING")
                    
        except Exception as e:
            self.logger.error(f"Error in key release handler: {e}")
            
    def _monitoring_loop(self):
        """
        Main monitoring loop that listens for commands and manages recording state.
        """
        self.logger.info("Monitoring loop started")
        
        try:
            while True:
                try:
                    command = self.command_queue.get(timeout=1.0)
                    
                    if command == "STOP":
                        self.logger.info("Received STOP command")
                        break
                    elif command == "START_RECORDING":
                        if not self.is_recording:
                            self.logger.info("Starting recording session")
                            self._start_recording_session()
                    elif command == "STOP_RECORDING":
                        if self.is_recording:
                            self.logger.info("Stopping recording session")
                            self._stop_recording_session()
                    
                except queue.Empty:
                    # Check if we need to auto-save or handle timeouts
                    if self.is_recording and self.recording_start_time:
                        elapsed = time.time() - self.recording_start_time
                        if elapsed > self.max_session_duration:
                            self.logger.warning("Maximum session duration reached - stopping recording")
                            self._stop_recording_session()
                    continue
                    
        except Exception as e:
            self.logger.error(f"Error in monitoring loop: {e}")
        finally:
            self.logger.info("Monitoring loop ended")
    
    def _start_recording_session(self):
        """Start a new recording session."""
        try:
            if self.is_recording:
                self.logger.warning("Recording already in progress")
                return
            
            # Generate session ID
            self.current_session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            session_dir = self.temp_dir / f"session_{self.current_session_id}"
            session_dir.mkdir(exist_ok=True)
            
            # Reset state
            self.audio_chunks = []
            self.recording_start_time = time.time()
            self.is_recording = True
            
            # Start recording thread
            self.recording_thread = threading.Thread(
                target=self._recording_loop,
                args=(session_dir,),
                daemon=True
            )
            self.recording_thread.start()
            
            # Trigger callback
            if self.on_recording_start:
                self.on_recording_start()
            
            self.logger.info(f"Recording session started: {self.current_session_id}")
            
        except Exception as e:
            self.logger.error(f"Error starting recording session: {e}")
            self.is_recording = False
    
    def _stop_recording_session(self):
        """Stop the current recording session."""
        try:
            if not self.is_recording:
                self.logger.warning("No recording in progress")
                return
            
            self.is_recording = False
            
            # Wait for recording thread to finish
            if self.recording_thread and self.recording_thread.is_alive():
                self.recording_thread.join(timeout=5.0)
            
            # Stop audio recorder if active
            if hasattr(self.audio_recorder, 'stop_recording'):
                try:
                    self.audio_recorder.stop_recording()
                except:
                    pass  # Ignore errors if already stopped
            
            # Trigger callbacks
            if self.on_recording_stop:
                self.on_recording_stop()
            
            if self.on_session_complete and self.audio_chunks:
                chunk_paths = [str(chunk) for chunk in self.audio_chunks]
                self.on_session_complete(chunk_paths)
            
            self.logger.info(f"Recording session stopped: {self.current_session_id}")
            
        except Exception as e:
            self.logger.error(f"Error stopping recording session: {e}")
    
    def _recording_loop(self, session_dir: Path):
        """
        Main recording loop that handles chunked recording.
        
        Args:
            session_dir: Directory to store recording chunks.
        """
        chunk_count = 0
        
        try:
            while self.is_recording:
                chunk_count += 1
                chunk_filename = f"chunk_{chunk_count:03d}.wav"
                chunk_path = session_dir / chunk_filename
                
                self.logger.info(f"Recording chunk {chunk_count}: {chunk_filename}")
                
                try:
                    # Start recording this chunk
                    self.audio_recorder.start_recording()
                    
                    # Record for chunk duration or until stopped
                    start_time = time.time()
                    while (time.time() - start_time) < self.chunk_duration and self.is_recording:
                        time.sleep(0.1)
                    
                    # Stop recording and get the file
                    recorded_file = self.audio_recorder.stop_recording()
                    
                    if recorded_file and Path(recorded_file).exists():
                        # Move to session directory
                        Path(recorded_file).rename(chunk_path)
                        self.audio_chunks.append(chunk_path)
                        
                        # Trigger chunk callback
                        if self.on_chunk_complete:
                            self.on_chunk_complete(str(chunk_path))
                        
                        self.logger.info(f"Chunk {chunk_count} completed: {chunk_path}")
                    else:
                        self.logger.warning(f"Failed to record chunk {chunk_count}")
                        
                except Exception as e:
                    self.logger.error(f"Error recording chunk {chunk_count}: {e}")
                    
                # Auto-save check
                if chunk_count % 10 == 0:  # Every 10 chunks
                    self._auto_save_session()
                    
        except Exception as e:
            self.logger.error(f"Error in recording loop: {e}")
        finally:
            self.logger.info(f"Recording loop ended. Total chunks: {chunk_count}")
    
    def _auto_save_session(self):
        """Auto-save the current session."""
        try:
            if not self.current_session_id or not self.audio_chunks:
                return
            
            self.logger.info(f"Auto-saving session {self.current_session_id}")
            # Implementation for auto-save can be added here
            
        except Exception as e:
            self.logger.error(f"Error in auto-save: {e}")
    
    def get_session_info(self) -> Dict[str, Any]:
        """
        Get information about the current session.
        
        Returns:
            Dict containing session information.
        """
        return {
            "session_id": self.current_session_id,
            "is_recording": self.is_recording,
            "start_time": self.recording_start_time,
            "chunk_count": len(self.audio_chunks),
            "chunks": [str(chunk) for chunk in self.audio_chunks]
        }
    
    def combine_chunks(self, output_path: str) -> bool:
        """
        Combine all chunks into a single audio file.
        
        Args:
            output_path: Path for the combined audio file.
            
        Returns:
            bool: True if successful.
        """
        try:
            if not self.audio_chunks:
                self.logger.warning("No chunks to combine")
                return False
            
            # Use SoX to combine chunks
            sox_cmd = ["sox"] + [str(chunk) for chunk in self.audio_chunks] + [output_path]
            
            result = subprocess.run(sox_cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logger.info(f"Successfully combined {len(self.audio_chunks)} chunks into {output_path}")
                return True
            else:
                self.logger.error(f"Failed to combine chunks: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error combining chunks: {e}")
            return False
    
    def cleanup_session(self, session_id: Optional[str] = None) -> bool:
        """
        Clean up session files.
        
        Args:
            session_id: Session ID to clean up. If None, cleans current session.
            
        Returns:
            bool: True if successful.
        """
        try:
            target_session = session_id or self.current_session_id
            if not target_session:
                return False
            
            session_dir = self.temp_dir / f"session_{target_session}"
            if session_dir.exists():
                import shutil
                shutil.rmtree(session_dir)
                self.logger.info(f"Cleaned up session: {target_session}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error cleaning up session: {e}")
            return False
    
    def get_recording_status(self) -> Dict[str, Any]:
        """
        Get current recording status.
        
        Returns:
            Dict containing status information.
        """
        return {
            "is_recording": self.is_recording,
            "continuous_mode": self.continuous_mode,
            "ctrl_pressed": self.ctrl_pressed,
            "v_pressed": self.v_pressed,
            "key_detection_available": self.key_detection_available,
            "session_info": self.get_session_info() if self.is_recording else None
        }
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        try:
            self.stop_continuous_monitoring()
        except:
            pass
    
    def _start_monitoring_loop_thread(self):
        """Start background monitoring thread without key detection."""
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True
        )
        self.monitoring_thread.start()
        self.logger.info("Background monitoring thread started (no key detection)") 