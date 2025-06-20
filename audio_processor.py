#!/usr/bin/env python3
"""
Audio Processor - Enhanced audio processing capabilities for Dicto
Provides device enumeration, audio level monitoring, voice activity detection,
noise reduction, and real-time audio processing features.
"""

import os
import sys
import subprocess
import tempfile
import time
import logging
import threading
import shutil
import platform
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import queue
import json
import signal


class AudioDevice:
    """Represents an audio input device."""
    
    def __init__(self, device_id: str, name: str, description: str = "", is_default: bool = False):
        self.device_id = device_id
        self.name = name
        self.description = description
        self.is_default = is_default
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "device_id": self.device_id,
            "name": self.name,
            "description": self.description,
            "is_default": self.is_default
        }
    
    def __str__(self) -> str:
        return f"{self.name} ({self.device_id})" + (" [Default]" if self.is_default else "")


class AudioLevelMonitor:
    """Real-time audio level monitoring using SoX."""
    
    def __init__(self, sox_path: str):
        self.sox_path = sox_path
        self.is_monitoring = False
        self.monitor_process = None
        self.level_queue = queue.Queue(maxsize=100)
        self.monitor_thread = None
        self.logger = logging.getLogger(__name__ + ".AudioLevelMonitor")
    
    def start_monitoring(self, device_id: Optional[str] = None) -> bool:
        """Start real-time audio level monitoring."""
        if self.is_monitoring:
            return True
        
        try:
            # Build SoX command for level monitoring
            input_source = device_id if device_id else "-d"
            cmd = [
                self.sox_path,
                input_source,
                "-t", "null", "-",
                "trim", "0", "0.1",  # Sample 0.1 seconds
                "stats"
            ]
            
            self.is_monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_levels, args=(cmd,))
            self.monitor_thread.start()
            
            self.logger.info("Audio level monitoring started")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start audio level monitoring: {e}")
            self.is_monitoring = False
            return False
    
    def _monitor_levels(self, cmd: List[str]):
        """Monitor audio levels in a separate thread."""
        while self.is_monitoring:
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=1
                )
                
                # Parse RMS level from SoX stats output
                rms_level = self._parse_rms_level(result.stderr)
                if rms_level is not None:
                    try:
                        self.level_queue.put_nowait(rms_level)
                    except queue.Full:
                        # Remove old value and add new one
                        try:
                            self.level_queue.get_nowait()
                            self.level_queue.put_nowait(rms_level)
                        except queue.Empty:
                            pass
                
                time.sleep(0.05)  # 20 FPS monitoring
                
            except subprocess.TimeoutExpired:
                continue
            except Exception as e:
                if self.is_monitoring:
                    self.logger.warning(f"Audio level monitoring error: {e}")
                break
    
    def _parse_rms_level(self, stats_output: str) -> Optional[float]:
        """Parse RMS level from SoX stats output."""
        try:
            for line in stats_output.split('\n'):
                if 'RMS amplitude:' in line:
                    rms_str = line.split(':')[1].strip()
                    return float(rms_str)
        except Exception:
            pass
        return None
    
    def get_current_level(self) -> Optional[float]:
        """Get the current audio level."""
        try:
            return self.level_queue.get_nowait()
        except queue.Empty:
            return None
    
    def stop_monitoring(self):
        """Stop audio level monitoring."""
        self.is_monitoring = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=2)


class VoiceActivityDetector:
    """Voice activity detection for auto-start/stop recording."""
    
    def __init__(self, sox_path: str):
        self.sox_path = sox_path
        self.logger = logging.getLogger(__name__ + ".VoiceActivityDetector")
        
        # VAD parameters
        self.silence_threshold = 0.01  # RMS threshold for silence
        self.speech_threshold = 0.05   # RMS threshold for speech
        self.min_speech_duration = 0.5  # Minimum speech duration in seconds
        self.max_silence_duration = 1.5  # Maximum silence duration before stopping
        
        # State tracking
        self.is_speech_detected = False
        self.speech_start_time = None
        self.silence_start_time = None
    
    def analyze_audio_segment(self, audio_file: str) -> Dict[str, Any]:
        """Analyze an audio segment for voice activity."""
        try:
            # Get audio statistics using SoX
            cmd = [self.sox_path, audio_file, "-n", "stats"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            # Parse statistics
            stats = self._parse_audio_stats(result.stderr)
            
            # Determine if speech is present
            rms_level = stats.get('rms_amplitude', 0.0)
            max_level = stats.get('max_amplitude', 0.0)
            
            has_speech = (
                rms_level > self.speech_threshold or 
                max_level > self.silence_threshold * 3
            )
            
            return {
                'has_speech': has_speech,
                'rms_level': rms_level,
                'max_level': max_level,
                'duration': stats.get('length', 0.0),
                'stats': stats
            }
            
        except Exception as e:
            self.logger.error(f"Voice activity analysis failed: {e}")
            return {'has_speech': False, 'error': str(e)}
    
    def _parse_audio_stats(self, stats_output: str) -> Dict[str, float]:
        """Parse audio statistics from SoX output."""
        stats = {}
        try:
            for line in stats_output.split('\n'):
                if 'Length (seconds):' in line:
                    stats['length'] = float(line.split(':')[1].strip())
                elif 'RMS amplitude:' in line:
                    stats['rms_amplitude'] = float(line.split(':')[1].strip())
                elif 'Maximum amplitude:' in line:
                    stats['max_amplitude'] = float(line.split(':')[1].strip())
                elif 'Mean amplitude:' in line:
                    stats['mean_amplitude'] = float(line.split(':')[1].strip())
        except Exception as e:
            self.logger.warning(f"Failed to parse some audio stats: {e}")
        
        return stats
    
    def should_start_recording(self, current_level: float) -> bool:
        """Determine if recording should start based on current audio level."""
        return current_level > self.speech_threshold
    
    def should_stop_recording(self, current_level: float, recording_duration: float) -> bool:
        """Determine if recording should stop based on silence detection."""
        current_time = time.time()
        
        if current_level > self.silence_threshold:
            # Speech detected, reset silence timer
            self.silence_start_time = None
            if not self.is_speech_detected:
                self.is_speech_detected = True
                self.speech_start_time = current_time
        else:
            # Silence detected
            if self.silence_start_time is None:
                self.silence_start_time = current_time
            
            # Check if we've had enough silence to stop
            silence_duration = current_time - self.silence_start_time
            
            # Only stop if we've had some speech and then enough silence
            if (self.is_speech_detected and 
                recording_duration > self.min_speech_duration and
                silence_duration > self.max_silence_duration):
                return True
        
        return False


class AudioProcessor:
    """
    Enhanced audio processor with device selection, monitoring, and processing capabilities.
    Built on top of the existing AudioRecorder functionality.
    """
    
    def __init__(self, temp_dir: Optional[str] = None):
        """Initialize the AudioProcessor."""
        self.logger = logging.getLogger(__name__)
        
        # Set up temp directory
        self.temp_dir = Path(temp_dir) if temp_dir else Path(tempfile.gettempdir()) / "dicto_audio"
        self.temp_dir.mkdir(exist_ok=True)
        
        # Platform detection
        self.is_macos = platform.system() == "Darwin"
        
        # Initialize SoX
        self.sox_path = self._find_sox()
        
        # Audio processing components
        self.level_monitor = AudioLevelMonitor(self.sox_path)
        self.vad = VoiceActivityDetector(self.sox_path)
        
        # Current settings
        self.current_device = None
        self.noise_reduction_enabled = True
        self.auto_gain_enabled = True
        
        self.logger.info("AudioProcessor initialized successfully")
    
    def _find_sox(self) -> str:
        """Find SoX executable."""
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
                raise RuntimeError("SoX not found. Install with: brew install sox")
        
        return sox_path
    
    def list_audio_devices(self) -> List[AudioDevice]:
        """
        List available audio input devices.
        
        Returns:
            List of AudioDevice objects representing available input devices.
        """
        devices = []
        
        try:
            if self.is_macos:
                # Use system_profiler to get audio devices on macOS
                cmd = ["system_profiler", "SPAudioDataType", "-json"]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    devices = self._parse_macos_devices(result.stdout)
                else:
                    self.logger.warning("Failed to get device list from system_profiler")
            
            # Add default device
            if not any(d.is_default for d in devices):
                devices.insert(0, AudioDevice(
                    device_id="default",
                    name="Default Audio Input",
                    description="System default audio input device",
                    is_default=True
                ))
            
            self.logger.info(f"Found {len(devices)} audio input devices")
            return devices
            
        except Exception as e:
            self.logger.error(f"Failed to list audio devices: {e}")
            # Return at least the default device
            return [AudioDevice(
                device_id="default",
                name="Default Audio Input",
                description="System default audio input device",
                is_default=True
            )]
    
    def _parse_macos_devices(self, json_output: str) -> List[AudioDevice]:
        """Parse macOS system_profiler output for audio devices."""
        devices = []
        try:
            data = json.loads(json_output)
            audio_data = data.get('SPAudioDataType', [])
            
            for item in audio_data:
                # Look for input devices
                if 'coreaudio_input_source' in item:
                    sources = item['coreaudio_input_source']
                    if isinstance(sources, list):
                        for source in sources:
                            device = AudioDevice(
                                device_id=source.get('coreaudio_device_id', 'unknown'),
                                name=source.get('_name', 'Unknown Device'),
                                description=f"{item.get('_name', 'Unknown')} - {source.get('_name', '')}"
                            )
                            devices.append(device)
                    elif isinstance(sources, dict):
                        device = AudioDevice(
                            device_id=sources.get('coreaudio_device_id', 'unknown'),
                            name=sources.get('_name', 'Unknown Device'),
                            description=f"{item.get('_name', 'Unknown')} - {sources.get('_name', '')}"
                        )
                        devices.append(device)
        
        except Exception as e:
            self.logger.warning(f"Failed to parse macOS device data: {e}")
        
        return devices
    
    def set_input_device(self, device_id: str) -> bool:
        """
        Set the audio input device.
        
        Args:
            device_id: ID of the device to use for input.
            
        Returns:
            bool: True if device was set successfully, False otherwise.
        """
        try:
            # Validate device exists
            devices = self.list_audio_devices()
            device_exists = any(d.device_id == device_id for d in devices)
            
            if not device_exists and device_id != "default":
                self.logger.error(f"Device not found: {device_id}")
                return False
            
            self.current_device = device_id
            self.logger.info(f"Audio input device set to: {device_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set input device: {e}")
            return False
    
    def get_audio_level(self) -> Optional[float]:
        """
        Get the current real-time audio level.
        
        Returns:
            Optional[float]: Current audio level (RMS amplitude) or None if not available.
        """
        if not self.level_monitor.is_monitoring:
            self.level_monitor.start_monitoring(self.current_device)
        
        return self.level_monitor.get_current_level()
    
    def start_level_monitoring(self) -> bool:
        """Start real-time audio level monitoring."""
        return self.level_monitor.start_monitoring(self.current_device)
    
    def stop_level_monitoring(self):
        """Stop real-time audio level monitoring."""
        self.level_monitor.stop_monitoring()
    
    def apply_noise_reduction(self, input_file: str, output_file: str, level: str = "medium") -> bool:
        """
        Apply noise reduction to an audio file using SoX.
        
        Args:
            input_file: Path to input audio file.
            output_file: Path to output audio file.
            level: Noise reduction level ("light", "medium", "heavy").
            
        Returns:
            bool: True if noise reduction was applied successfully.
        """
        try:
            # Noise reduction parameters based on level
            nr_params = {
                "light": ["noisered", "0.15"],
                "medium": ["noisered", "0.25"],
                "heavy": ["noisered", "0.35"]
            }
            
            if level not in nr_params:
                level = "medium"
            
            # Build SoX command with noise reduction
            cmd = [
                self.sox_path,
                input_file,
                output_file,
                "highpass", "200",  # Remove low-frequency noise
                "lowpass", "8000",  # Remove high-frequency noise
                "compand", "0.02,0.20", "5:-60,-40,-10", "-5", "-90", "0.1",  # Dynamic range compression
                *nr_params[level]
            ]
            
            # Apply auto-gain if enabled
            if self.auto_gain_enabled:
                cmd.extend(["gain", "-n"])  # Normalize gain
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                self.logger.info(f"Noise reduction applied: {level} level")
                return True
            else:
                self.logger.error(f"Noise reduction failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error applying noise reduction: {e}")
            return False
    
    def voice_activity_detection(self, audio_file: str) -> Dict[str, Any]:
        """
        Perform voice activity detection on an audio file.
        
        Args:
            audio_file: Path to audio file to analyze.
            
        Returns:
            Dict containing VAD results and statistics.
        """
        return self.vad.analyze_audio_segment(audio_file)
    
    def optimize_for_transcription(self, input_file: str, output_file: str) -> bool:
        """
        Optimize audio file for transcription (Whisper-ready format).
        
        Args:
            input_file: Path to input audio file.
            output_file: Path to output audio file.
            
        Returns:
            bool: True if optimization was successful.
        """
        try:
            # Convert to 16kHz mono WAV with noise reduction and normalization
            cmd = [
                self.sox_path,
                input_file,
                "-r", "16000",  # 16kHz sample rate
                "-c", "1",      # Mono
                "-b", "16",     # 16-bit
                output_file,
                "highpass", "80",   # Remove very low frequencies
                "lowpass", "8000",  # Remove frequencies above speech range
                "compand", "0.1,0.3", "-60,-60,-30,-15,-20,-10,-5,-5,0,-3", "6",  # Gentle compression
                "gain", "-n"    # Normalize
            ]
            
            # Add noise reduction if enabled
            if self.noise_reduction_enabled:
                cmd.extend(["noisered", "0.2"])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                self.logger.info("Audio optimized for transcription")
                return True
            else:
                self.logger.error(f"Audio optimization failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error optimizing audio: {e}")
            return False
    
    def get_audio_info(self, audio_file: str) -> Dict[str, Any]:
        """
        Get detailed information about an audio file.
        
        Args:
            audio_file: Path to audio file.
            
        Returns:
            Dict containing audio file information.
        """
        try:
            cmd = [self.sox_path, "--info", audio_file]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                info = self._parse_audio_info(result.stdout)
                
                # Add file size
                file_path = Path(audio_file)
                if file_path.exists():
                    info['file_size'] = file_path.stat().st_size
                
                return info
            else:
                self.logger.error(f"Failed to get audio info: {result.stderr}")
                return {}
                
        except Exception as e:
            self.logger.error(f"Error getting audio info: {e}")
            return {}
    
    def _parse_audio_info(self, info_output: str) -> Dict[str, Any]:
        """Parse SoX audio info output."""
        info = {}
        try:
            for line in info_output.split('\n'):
                line = line.strip()
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower().replace(' ', '_')
                    value = value.strip()
                    
                    # Convert numeric values
                    if key in ['sample_rate', 'channels', 'precision']:
                        try:
                            info[key] = int(value.split()[0])
                        except:
                            info[key] = value
                    elif key == 'duration':
                        try:
                            # Parse duration in format "00:00:05.23"
                            parts = value.split(':')
                            if len(parts) == 3:
                                hours, minutes, seconds = parts
                                total_seconds = float(hours) * 3600 + float(minutes) * 60 + float(seconds)
                                info[key] = total_seconds
                            else:
                                info[key] = value
                        except:
                            info[key] = value
                    else:
                        info[key] = value
        except Exception as e:
            self.logger.warning(f"Failed to parse some audio info: {e}")
        
        return info
    
    def cleanup(self):
        """Clean up resources."""
        self.stop_level_monitoring()
        self.logger.info("AudioProcessor cleanup completed")


if __name__ == "__main__":
    # Basic testing
    logging.basicConfig(level=logging.INFO)
    
    try:
        processor = AudioProcessor()
        
        print("Testing AudioProcessor...")
        
        # List devices
        devices = processor.list_audio_devices()
        print(f"\nFound {len(devices)} audio devices:")
        for device in devices:
            print(f"  {device}")
        
        # Test audio level monitoring
        print("\nStarting audio level monitoring for 5 seconds...")
        processor.start_level_monitoring()
        
        for i in range(50):  # 5 seconds at 10 FPS
            level = processor.get_audio_level()
            if level is not None:
                print(f"Audio level: {level:.4f}", end='\r')
            time.sleep(0.1)
        
        processor.stop_level_monitoring()
        print("\nAudio level monitoring test completed")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'processor' in locals():
            processor.cleanup() 