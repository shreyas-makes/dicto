#!/usr/bin/env python3
"""
File Processor - Audio file handling and format conversion for Dicto
Supports various audio file formats and provides conversion capabilities
for optimal transcription processing.
"""

import os
import sys
import subprocess
import tempfile
import logging
import shutil
import platform
from pathlib import Path
from typing import Optional, Dict, Any, List, Union, Tuple
import mimetypes


class AudioFileProcessor:
    """
    Audio file processor for handling various audio formats and conversions.
    Supports import, conversion, and optimization of audio files for transcription.
    """
    
    # Supported input formats
    SUPPORTED_FORMATS = {
        '.mp3': 'MP3 Audio',
        '.m4a': 'MPEG-4 Audio',
        '.aac': 'Advanced Audio Coding',
        '.flac': 'Free Lossless Audio Codec',
        '.wav': 'Waveform Audio',
        '.aiff': 'Audio Interchange File Format',
        '.ogg': 'Ogg Vorbis',
        '.opus': 'Opus Audio',
        '.wma': 'Windows Media Audio',
        '.amr': 'Adaptive Multi-Rate',
        '.3gp': '3GPP Audio',
        '.mp4': 'MPEG-4 Container',
        '.mov': 'QuickTime Movie',
        '.avi': 'Audio Video Interleave',
        '.webm': 'WebM Container'
    }
    
    def __init__(self, temp_dir: Optional[str] = None):
        """
        Initialize the AudioFileProcessor.
        
        Args:
            temp_dir: Directory for temporary files. If None, uses system temp.
        """
        self.logger = logging.getLogger(__name__)
        
        # Set up temp directory
        self.temp_dir = Path(temp_dir) if temp_dir else Path(tempfile.gettempdir()) / "dicto_files"
        self.temp_dir.mkdir(exist_ok=True)
        
        # Platform detection
        self.is_macos = platform.system() == "Darwin"
        
        # Find required tools
        self.sox_path = self._find_sox()
        self.ffmpeg_path = self._find_ffmpeg()
        
        self.logger.info("AudioFileProcessor initialized successfully")
    
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
    
    def _find_ffmpeg(self) -> Optional[str]:
        """Find FFmpeg executable (optional for additional format support)."""
        ffmpeg_path = shutil.which("ffmpeg")
        if not ffmpeg_path:
            # Try common installation paths on macOS
            common_paths = [
                "/usr/local/bin/ffmpeg",
                "/opt/homebrew/bin/ffmpeg",
                "/usr/bin/ffmpeg"
            ]
            
            for path in common_paths:
                if os.path.exists(path) and os.access(path, os.X_OK):
                    ffmpeg_path = path
                    break
        
        if ffmpeg_path:
            self.logger.info("FFmpeg found - extended format support available")
        else:
            self.logger.warning("FFmpeg not found - some formats may not be supported")
        
        return ffmpeg_path
    
    def is_supported_format(self, file_path: Union[str, Path]) -> bool:
        """
        Check if the audio file format is supported.
        
        Args:
            file_path: Path to the audio file.
            
        Returns:
            bool: True if format is supported, False otherwise.
        """
        file_path = Path(file_path)
        extension = file_path.suffix.lower()
        
        # Check if extension is in our supported list
        if extension in self.SUPPORTED_FORMATS:
            return True
        
        # Check MIME type as fallback
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type and mime_type.startswith('audio/'):
            return True
        
        return False
    
    def get_file_info(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Get detailed information about an audio file.
        
        Args:
            file_path: Path to the audio file.
            
        Returns:
            Dict containing file information.
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            return {"error": "File not found"}
        
        info = {
            "file_path": str(file_path),
            "filename": file_path.name,
            "extension": file_path.suffix.lower(),
            "file_size": file_path.stat().st_size,
            "supported": self.is_supported_format(file_path)
        }
        
        # Try to get audio-specific information
        try:
            if self.ffmpeg_path:
                audio_info = self._get_ffmpeg_info(file_path)
            else:
                audio_info = self._get_sox_info(file_path)
            
            info.update(audio_info)
            
        except Exception as e:
            self.logger.warning(f"Could not get audio info for {file_path}: {e}")
            info["info_error"] = str(e)
        
        return info
    
    def _get_sox_info(self, file_path: Path) -> Dict[str, Any]:
        """Get audio info using SoX."""
        try:
            cmd = [self.sox_path, "--info", str(file_path)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                return self._parse_sox_info(result.stdout)
            else:
                return {"sox_error": result.stderr}
                
        except Exception as e:
            return 