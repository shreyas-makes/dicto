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

try:
    from pynput import keyboard
    from pynput.keyboard import Key, KeyCode
    PYNPUT_AVAILABLE = True
except ImportError:
    print("Warning: pynput not installed. Install with: pip install pynput")
    print("Continuous recording functionality will be limited")
    keyboard = None
    Key = None
    KeyCode = None
    PYNPUT_AVAILABLE = False

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
                 temp_dir: Optional[str] = None):
        """
        Initialize the ContinuousRecorder.
        
        Args:
            chunk_duration: Duration of each recording chunk in seconds.
            max_session_duration: Maximum recording session duration in seconds.
            auto_save_interval: Interval for auto-saving chunks in seconds.
            temp_dir: Directory for temporary audio files.
        """
        self.logger = logging.getLogger(__name__)
        
        # Check if pynput is available
        if not PYNPUT_AVAILABLE:
            self.logger.warning("pynput not available - continuous recording disabled")
            self.pynput_available = False
        else:
            self.pynput_available = True
        
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
            if not self.pynput_available:
                self.logger.error("Cannot start monitoring - pynput not available")
                return False
            
            if self.key_listener and self.key_listener.running:
                self.logger.warning("Key monitoring already active")
                return True
            
            # Start keyboard listener
            self.key_listener = keyboard.Listener(
                on_press=self._on_key_press,
                on_release=self._on_key_release
            )
            self.key_listener.start()
            
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
            if self.key_listener:
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
            if key == Key.ctrl_l or key == Key.ctrl_r:
                self.ctrl_pressed = True
            elif hasattr(key, 'char') and key.char and key.char.lower() == 'v':
                self.v_pressed = True
            
            # Check if CTRL+V combination is active
            if self.ctrl_pressed and self.v_pressed and not self.continuous_mode:
                self.continuous_mode = True
                self.command_queue.put("START_RECORDING")
                
        except Exception as e:
            self.logger.error(f"Error in key press handler: {e}")
    
    def _on_key_release(self, key):
        """Handle key release events."""
        try:
            if key == Key.ctrl_l or key == Key.ctrl_r:
                self.ctrl_pressed = False
            elif hasattr(key, 'char') and key.char and key.char.lower() == 'v':
                self.v_pressed = False
            
            # Stop recording if CTRL+V is released
            if not (self.ctrl_pressed and self.v_pressed) and self.continuous_mode:
                self.continuous_mode = False
                self.command_queue.put("STOP_RECORDING")
                
        except Exception as e:
            self.logger.error(f"Error in key release handler: {e}")
    
    def _monitoring_loop(self):
        """Main monitoring loop for handling recording commands."""
        self.logger.info("Monitoring loop started")
        
        while True:
            try:
                # Check for commands with timeout
                try:
                    command = self.command_queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                
                if command == "STOP":
                    break
                elif command == "START_RECORDING":
                    self._start_recording_session()
                elif command == "STOP_RECORDING":
                    self._stop_recording_session()
                
                self.command_queue.task_done()
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
        
        self.logger.info("Monitoring loop stopped")
    
    def _start_recording_session(self):
        """Start a new continuous recording session."""
        if self.is_recording:
            self.logger.warning("Recording already in progress")
            return
        
        try:
            # Generate session ID
            self.current_session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.recording_start_time = time.time()
            self.audio_chunks = []
            self.is_recording = True
            
            # Create session directory
            session_dir = self.temp_dir / f"session_{self.current_session_id}"
            session_dir.mkdir(exist_ok=True)
            
            # Start recording thread
            self.recording_thread = threading.Thread(
                target=self._recording_loop,
                args=(session_dir,),
                daemon=True
            )
            self.recording_thread.start()
            
            # Call callback
            if self.on_recording_start:
                self.on_recording_start()
            
            self.logger.info(f"Started continuous recording session: {self.current_session_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to start recording session: {e}")
            self.is_recording = False
    
    def _stop_recording_session(self):
        """Stop the current recording session."""
        if not self.is_recording:
            return
        
        try:
            self.is_recording = False
            
            # Wait for recording thread to finish
            if self.recording_thread and self.recording_thread.is_alive():
                self.recording_thread.join(timeout=5.0)
            
            # Call callback with all chunks
            if self.on_session_complete and self.audio_chunks:
                chunk_paths = [str(chunk) for chunk in self.audio_chunks]
                self.on_session_complete(chunk_paths)
            
            # Call stop callback
            if self.on_recording_stop:
                self.on_recording_stop()
            
            duration = time.time() - self.recording_start_time if self.recording_start_time else 0
            self.logger.info(f"Stopped recording session: {self.current_session_id}, "
                           f"Duration: {duration:.1f}s, Chunks: {len(self.audio_chunks)}")
            
        except Exception as e:
            self.logger.error(f"Error stopping recording session: {e}")
    
    def _recording_loop(self, session_dir: Path):
        """Main recording loop that handles chunked recording."""
        chunk_number = 1
        last_auto_save = time.time()
        
        while self.is_recording:
            try:
                # Check if we've exceeded maximum session duration
                if (time.time() - self.recording_start_time) > self.max_session_duration:
                    self.logger.warning(f"Maximum session duration reached ({self.max_session_duration}s)")
                    break
                
                # Generate chunk filename
                chunk_filename = f"chunk_{chunk_number:03d}_{self.current_session_id}.wav"
                chunk_path = session_dir / chunk_filename
                
                # Record chunk
                self.logger.debug(f"Recording chunk {chunk_number}: {chunk_filename}")
                
                # Use audio recorder for this chunk
                try:
                    recorded_file = self.audio_recorder.start_recording(duration=self.chunk_duration)
                    
                    # Wait for chunk to complete or recording to stop
                    start_time = time.time()
                    while (time.time() - start_time) < self.chunk_duration and self.is_recording:
                        time.sleep(0.1)
                    
                    # Stop the chunk recording
                    if self.audio_recorder.is_recording_active():
                        final_file = self.audio_recorder.stop_recording()
                        
                        if final_file and Path(final_file).exists():
                            # Move to session directory with proper name
                            import shutil
                            shutil.move(final_file, chunk_path)
                            
                            self.audio_chunks.append(chunk_path)
                            
                            # Call chunk complete callback
                            if self.on_chunk_complete:
                                self.on_chunk_complete(str(chunk_path))
                            
                            self.logger.debug(f"Completed chunk {chunk_number}: {chunk_path}")
                            chunk_number += 1
                        
                except Exception as e:
                    self.logger.error(f"Error recording chunk {chunk_number}: {e}")
                    continue
                
                # Auto-save check
                current_time = time.time()
                if (current_time - last_auto_save) >= self.auto_save_interval:
                    self._auto_save_session()
                    last_auto_save = current_time
                
                # Brief pause before next chunk
                if self.is_recording:
                    time.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"Error in recording loop: {e}")
                break
        
        self.logger.info(f"Recording loop completed. Total chunks: {len(self.audio_chunks)}")
    
    def _auto_save_session(self):
        """Auto-save current session data."""
        try:
            if not self.current_session_id or not self.audio_chunks:
                return
            
            session_info = {
                "session_id": self.current_session_id,
                "start_time": self.recording_start_time,
                "chunks": [str(chunk) for chunk in self.audio_chunks],
                "auto_save_time": time.time(),
                "status": "recording" if self.is_recording else "completed"
            }
            
            session_file = self.temp_dir / f"session_{self.current_session_id}.json"
            import json
            with open(session_file, 'w') as f:
                json.dump(session_info, f, indent=2)
            
            self.logger.debug(f"Auto-saved session: {len(self.audio_chunks)} chunks")
            
        except Exception as e:
            self.logger.error(f"Auto-save failed: {e}")
    
    def get_session_info(self) -> Dict[str, Any]:
        """
        Get current session information.
        
        Returns:
            Dict containing session information.
        """
        if not self.current_session_id:
            return {}
        
        duration = time.time() - self.recording_start_time if self.recording_start_time else 0
        
        return {
            "session_id": self.current_session_id,
            "is_recording": self.is_recording,
            "duration": duration,
            "chunks_count": len(self.audio_chunks),
            "chunks": [str(chunk) for chunk in self.audio_chunks],
            "continuous_mode": self.continuous_mode,
            "ctrl_pressed": self.ctrl_pressed,
            "v_pressed": self.v_pressed
        }
    
    def combine_chunks(self, output_path: str) -> bool:
        """
        Combine all chunks from current session into a single file.
        
        Args:
            output_path: Path for the combined audio file.
            
        Returns:
            bool: True if combination was successful.
        """
        if not self.audio_chunks:
            self.logger.warning("No chunks to combine")
            return False
        
        try:
            # Use SoX to combine all chunks
            cmd = ["sox"] + [str(chunk) for chunk in self.audio_chunks] + [output_path]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                self.logger.info(f"Combined {len(self.audio_chunks)} chunks into {output_path}")
                return True
            else:
                self.logger.error(f"Failed to combine chunks: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("Chunk combination timed out")
            return False
        except Exception as e:
            self.logger.error(f"Error combining chunks: {e}")
            return False
    
    def cleanup_session(self, session_id: Optional[str] = None) -> bool:
        """
        Clean up session files.
        
        Args:
            session_id: Specific session to clean up. If None, cleans current session.
            
        Returns:
            bool: True if cleanup was successful.
        """
        try:
            if session_id:
                target_session = session_id
            else:
                target_session = self.current_session_id
            
            if not target_session:
                return False
            
            # Clean up session directory
            session_dir = self.temp_dir / f"session_{target_session}"
            if session_dir.exists():
                import shutil
                shutil.rmtree(session_dir)
                self.logger.info(f"Cleaned up session directory: {session_dir}")
            
            # Clean up session info file
            session_file = self.temp_dir / f"session_{target_session}.json"
            if session_file.exists():
                session_file.unlink()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error cleaning up session: {e}")
            return False
    
    def get_recording_status(self) -> Dict[str, Any]:
        """
        Get current recording status.
        
        Returns:
            Dict containing status information.
        """
        status = {
            "is_monitoring": self.key_listener is not None and self.key_listener.running,
            "is_recording": self.is_recording,
            "continuous_mode": self.continuous_mode,
            "ctrl_pressed": self.ctrl_pressed,
            "v_pressed": self.v_pressed,
            "current_session": self.current_session_id,
            "chunks_recorded": len(self.audio_chunks),
        }
        
        if self.recording_start_time:
            status["recording_duration"] = time.time() - self.recording_start_time
        
        return status
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        try:
            self.stop_continuous_monitoring()
        except:
            pass 