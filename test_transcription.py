#!/usr/bin/env python3
"""
Test script for Dicto TranscriptionEngine
This script tests the transcription functionality with various scenarios.
"""

import os
import sys
import tempfile
import wave
import time
from pathlib import Path

# Import our transcription engine
from dicto_core import TranscriptionEngine


def create_test_audio_file(duration: float = 2.0, filename: str = "test_audio.wav") -> str:
    """
    Create a simple test audio file with sine wave.
    
    Args:
        duration: Duration of audio in seconds
        filename: Name of the output file
    
    Returns:
        Path to the created audio file
    """
    import math
    
    # Audio parameters
    sample_rate = 16000
    frequency = 440  # A note
    amplitude = 0.3
    
    # Generate samples
    samples = []
    for i in range(int(sample_rate * duration)):
        sample = amplitude * math.sin(2 * math.pi * frequency * i / sample_rate)
        samples.append(int(sample * 32767))  # Convert to 16-bit
    
    # Create temporary file
    temp_dir = Path(tempfile.gettempdir()) / "dicto_test"
    temp_dir.mkdir(exist_ok=True)
    audio_path = temp_dir / filename
    
    # Write WAV file
    with wave.open(str(audio_path), 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 2 bytes per sample
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(b''.join(sample.to_bytes(2, 'little', signed=True) for sample in samples))
    
    print(f"✅ Created test audio file: {audio_path}")
    return str(audio_path)


def test_engine_initialization():
    """Test TranscriptionEngine initialization."""
    print("\n" + "="*60)
    print("TEST 1: Engine Initialization")
    print("="*60)
    
    try:
        engine = TranscriptionEngine()
        print("✅ TranscriptionEngine initialized successfully")
        print(f"   Whisper binary: {engine.whisper_path}")
        print(f"   Model file: {engine.model_path}")
        print(f"   Temp directory: {engine.temp_dir}")
        
        # Test supported formats
        formats = engine.get_supported_formats()
        print(f"   Supported formats: {', '.join(formats)}")
        
        engine.cleanup()
        return True
    except Exception as e:
        print(f"❌ Engine initialization failed: {e}")
        return False


def test_valid_transcription():
    """Test transcription with a valid audio file."""
    print("\n" + "="*60)
    print("TEST 2: Valid Audio Transcription")
    print("="*60)
    
    try:
        # Create test audio file
        audio_file = create_test_audio_file(duration=3.0, filename="valid_test.wav")
        
        # Initialize engine
        engine = TranscriptionEngine()
        
        # Transcribe
        print(f"📝 Transcribing: {audio_file}")
        result = engine.transcribe_file(audio_file)
        
        # Print results
        print(f"Success: {result['success']}")
        print(f"Duration: {result['duration']:.2f}s")
        
        if result['success']:
            print(f"✅ Transcription: '{result['text']}'")
        else:
            print(f"❌ Error: {result['error']}")
        
        # Cleanup
        engine.cleanup()
        Path(audio_file).unlink()  # Remove test file
        
        return result['success']
        
    except Exception as e:
        print(f"❌ Valid transcription test failed: {e}")
        return False


def test_invalid_file():
    """Test transcription with non-existent file."""
    print("\n" + "="*60)
    print("TEST 3: Invalid File Handling")
    print("="*60)
    
    try:
        engine = TranscriptionEngine()
        
        # Try to transcribe non-existent file
        fake_file = "/nonexistent/fake_audio.wav"
        print(f"📝 Attempting to transcribe non-existent file: {fake_file}")
        
        result = engine.transcribe_file(fake_file)
        
        # Should fail gracefully
        print(f"Success: {result['success']}")
        print(f"Error: {result['error']}")
        
        if not result['success'] and "not found" in result['error'].lower():
            print("✅ Error handling works correctly")
            engine.cleanup()
            return True
        else:
            print("❌ Error handling failed")
            engine.cleanup()
            return False
            
    except Exception as e:
        print(f"❌ Invalid file test failed unexpectedly: {e}")
        return False


def test_empty_file():
    """Test transcription with an empty file."""
    print("\n" + "="*60)
    print("TEST 4: Empty File Handling")
    print("="*60)
    
    try:
        # Create empty file
        temp_dir = Path(tempfile.gettempdir()) / "dicto_test"
        temp_dir.mkdir(exist_ok=True)
        empty_file = temp_dir / "empty.wav"
        empty_file.touch()  # Create empty file
        
        engine = TranscriptionEngine()
        
        print(f"📝 Transcribing empty file: {empty_file}")
        result = engine.transcribe_file(str(empty_file))
        
        print(f"Success: {result['success']}")
        print(f"Duration: {result['duration']:.2f}s")
        
        if result['success']:
            print(f"Text: '{result['text']}'")
        else:
            print(f"Error: {result['error']}")
        
        # Cleanup
        engine.cleanup()
        empty_file.unlink()
        
        # Either success with empty text or graceful failure is acceptable
        if result['success'] or result['error']:
            print("✅ Empty file handled appropriately")
            return True
        else:
            print("❌ Empty file handling unclear")
            return False
            
    except Exception as e:
        print(f"❌ Empty file test failed: {e}")
        return False


def test_initialization_errors():
    """Test initialization with invalid paths."""
    print("\n" + "="*60)
    print("TEST 5: Initialization Error Handling")
    print("="*60)
    
    try:
        # Test with invalid binary path
        print("Testing with invalid binary path...")
        try:
            engine = TranscriptionEngine(whisper_binary_path="/fake/path/whisper")
            print("❌ Should have failed with invalid binary path")
            return False
        except FileNotFoundError as e:
            print(f"✅ Correctly caught binary error: {e}")
        
        # Test with invalid model path
        print("\nTesting with invalid model path...")
        try:
            engine = TranscriptionEngine(model_path="/fake/path/model.bin")
            print("❌ Should have failed with invalid model path")
            return False
        except FileNotFoundError as e:
            print(f"✅ Correctly caught model error: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Initialization error test failed: {e}")
        return False


def main():
    """Run all tests and report results."""
    print("🎤 DICTO TRANSCRIPTION ENGINE TESTS")
    print("=" * 60)
    
    # Run all tests
    tests = [
        ("Engine Initialization", test_engine_initialization),
        ("Valid Transcription", test_valid_transcription),
        ("Invalid File Handling", test_invalid_file),
        ("Empty File Handling", test_empty_file),
        ("Initialization Errors", test_initialization_errors),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! TranscriptionEngine is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 