#!/usr/bin/env python3
"""
Test Recording - Test script for Dicto's SoX-based audio recording and transcription
This script tests the complete recording and transcription pipeline.
"""

import sys
import time
import logging
from pathlib import Path
from typing import Dict, Any

from dicto_core import TranscriptionEngine
from audio_recorder import AudioRecorder


def setup_logging():
    """Set up logging for the test."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)


def test_sox_installation(logger) -> bool:
    """Test if SoX is properly installed and available."""
    logger.info("🔧 Testing SoX installation...")
    
    try:
        recorder = AudioRecorder()
        logger.info("✅ SoX is properly installed and available")
        return True
    except Exception as e:
        logger.error(f"❌ SoX test failed: {e}")
        return False


def test_whisper_setup(logger) -> bool:
    """Test if Whisper.cpp is properly set up."""
    logger.info("🔧 Testing Whisper.cpp setup...")
    
    try:
        engine = TranscriptionEngine(enable_recording=False)
        logger.info("✅ Whisper.cpp is properly set up")
        return True
    except Exception as e:
        logger.error(f"❌ Whisper.cpp test failed: {e}")
        return False


def test_recording_only(logger, duration: float = 3.0) -> Dict[str, Any]:
    """Test audio recording without transcription."""
    logger.info(f"🎤 Testing audio recording ({duration} seconds)...")
    
    try:
        recorder = AudioRecorder()
        
        # Test microphone access first
        if not recorder.test_microphone_access():
            error_msg = "Microphone access test failed. Please check permissions."
            if recorder.is_macos:
                error_msg += " Run 'python check_mic_permission.py' for help."
            logger.error(f"❌ {error_msg}")
            return {"success": False, "error": error_msg}
        
        # Start recording
        audio_file = recorder.start_recording(duration)
        logger.info(f"🔴 Recording started, saving to: {audio_file}")
        
        # Wait for recording to complete
        time.sleep(duration + 0.5)  # Add small buffer
        
        # Stop recording
        final_file = recorder.stop_recording()
        
        if final_file and Path(final_file).exists():
            file_size = Path(final_file).stat().st_size
            logger.info(f"✅ Recording successful: {final_file} ({file_size} bytes)")
            return {"success": True, "file": final_file, "size": file_size}
        else:
            logger.error("❌ Recording failed: No file created")
            return {"success": False, "error": "No file created"}
            
    except Exception as e:
        logger.error(f"❌ Recording test failed: {e}")
        return {"success": False, "error": str(e)}


def test_transcription_only(logger, audio_file: str) -> Dict[str, Any]:
    """Test transcription of an existing audio file."""
    logger.info(f"📝 Testing transcription of: {audio_file}")
    
    try:
        engine = TranscriptionEngine(enable_recording=False)
        result = engine.transcribe_file(audio_file)
        
        if result["success"]:
            logger.info(f"✅ Transcription successful: {result['text'][:100]}...")
            return result
        else:
            logger.error(f"❌ Transcription failed: {result['error']}")
            return result
            
    except Exception as e:
        logger.error(f"❌ Transcription test failed: {e}")
        return {"success": False, "error": str(e)}


def test_record_and_transcribe(logger, duration: float = 5.0) -> Dict[str, Any]:
    """Test the complete record and transcribe workflow."""
    logger.info(f"🎤📝 Testing complete record-and-transcribe workflow ({duration} seconds)...")
    
    try:
        engine = TranscriptionEngine()
        
        # Get recording info
        recording_info = engine.get_recording_info()
        if not recording_info.get("available", False):
            error_msg = f"Recording not available: {recording_info.get('reason', 'Unknown')}"
            logger.error(f"❌ {error_msg}")
            return {"success": False, "error": error_msg}
        
        logger.info(f"📊 Recording format: {recording_info}")
        
        # Record and transcribe
        logger.info("🔴 Starting recording... Please speak into your microphone!")
        result = engine.record_and_transcribe(duration=duration)
        
        if result["success"]:
            logger.info(f"✅ Complete workflow successful!")
            logger.info(f"📊 Recording duration: {result['recording_duration']:.2f}s")
            logger.info(f"📊 Transcription duration: {result['transcription_duration']:.2f}s")
            logger.info(f"📝 Transcribed text: {result['text']}")
            return result
        else:
            logger.error(f"❌ Workflow failed: {result['error']}")
            return result
            
    except Exception as e:
        logger.error(f"❌ Complete workflow test failed: {e}")
        return {"success": False, "error": str(e)}


def interactive_recording_test(logger):
    """Interactive test allowing user to control recording."""
    logger.info("🎮 Interactive recording test")
    logger.info("Press Enter to start recording, then Enter again to stop...")
    
    try:
        engine = TranscriptionEngine()
        
        # Wait for user to start
        input("Press Enter to start recording...")
        
        # Start recording
        if not engine.start_recording():
            logger.error("❌ Failed to start recording")
            return
        
        logger.info("🔴 Recording... Press Enter to stop.")
        
        # Wait for user to stop
        input()
        
        # Stop recording and transcribe
        audio_file = engine.stop_recording()
        
        if audio_file:
            logger.info(f"⏹️ Recording stopped: {audio_file}")
            logger.info("📝 Transcribing...")
            
            result = engine.transcribe_file(audio_file)
            
            if result["success"]:
                logger.info(f"✅ Transcription: {result['text']}")
            else:
                logger.error(f"❌ Transcription failed: {result['error']}")
            
            # Clean up
            engine.audio_recorder.cleanup_file(audio_file)
        else:
            logger.error("❌ No audio file was created")
            
    except Exception as e:
        logger.error(f"❌ Interactive test failed: {e}")


def main():
    """Main test function."""
    logger = setup_logging()
    
    logger.info("=" * 60)
    logger.info("🎤 DICTO AUDIO RECORDING & TRANSCRIPTION TEST")
    logger.info("=" * 60)
    
    # Check if on macOS and provide guidance
    import platform
    if platform.system() == "Darwin":
        logger.info("🍎 Running on macOS - Microphone permission may be required")
        logger.info("💡 If recording fails, run: python check_mic_permission.py")
        logger.info("=" * 60)
    
    # Test 1: SoX Installation
    logger.info("\n1️⃣ Testing SoX installation...")
    sox_ok = test_sox_installation(logger)
    
    if not sox_ok:
        logger.error("❌ SoX is not available. Please install SoX using:")
        logger.error("   brew install sox")
        sys.exit(1)
    
    # Test 2: Whisper.cpp Setup
    logger.info("\n2️⃣ Testing Whisper.cpp setup...")
    whisper_ok = test_whisper_setup(logger)
    
    if not whisper_ok:
        logger.error("❌ Whisper.cpp is not properly set up")
        sys.exit(1)
    
    # Test 3: Recording Only
    logger.info("\n3️⃣ Testing audio recording...")
    recording_result = test_recording_only(logger, duration=3.0)
    
    if not recording_result["success"]:
        logger.error("❌ Recording test failed")
        sys.exit(1)
    
    # Test 4: Transcription Only
    logger.info("\n4️⃣ Testing transcription...")
    transcription_result = test_transcription_only(logger, recording_result["file"])
    
    # Clean up test file
    try:
        Path(recording_result["file"]).unlink()
        logger.info(f"🗑️ Cleaned up test file: {recording_result['file']}")
    except Exception:
        pass
    
    if not transcription_result["success"]:
        logger.error("❌ Transcription test failed")
        sys.exit(1)
    
    # Test 5: Complete Workflow
    logger.info("\n5️⃣ Testing complete record-and-transcribe workflow...")
    workflow_result = test_record_and_transcribe(logger, duration=5.0)
    
    if not workflow_result["success"]:
        logger.error("❌ Complete workflow test failed")
        sys.exit(1)
    
    # Test 6: Interactive Test (optional)
    logger.info("\n6️⃣ Interactive test (optional)")
    response = input("Would you like to run an interactive recording test? (y/N): ").lower().strip()
    
    if response in ['y', 'yes']:
        interactive_recording_test(logger)
    
    # Final summary
    logger.info("\n" + "=" * 60)
    logger.info("🎉 ALL TESTS PASSED!")
    logger.info("✅ SoX is properly installed")
    logger.info("✅ Whisper.cpp is properly set up")
    logger.info("✅ Audio recording works correctly")
    logger.info("✅ Audio transcription works correctly")
    logger.info("✅ Complete record-and-transcribe workflow works")
    logger.info("🎤 Your Dicto setup is ready to use!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main() 