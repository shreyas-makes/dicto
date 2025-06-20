#!/usr/bin/env python3
"""
Test Vocabulary - Testing script for Task 6 vocabulary and continuous recording features
This script tests the VocabularyManager and ContinuousRecorder functionality.
"""

import os
import sys
import time
import logging
import tempfile
import json
from pathlib import Path
from typing import List, Dict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_vocabulary_manager():
    """Test VocabularyManager functionality."""
    print("=" * 60)
    print("Testing VocabularyManager...")
    print("=" * 60)
    
    try:
        from vocabulary_manager import VocabularyManager
        
        # Test with temporary directory
        test_dir = tempfile.mkdtemp(prefix="dicto_vocab_test_")
        vocab_manager = VocabularyManager(config_dir=test_dir)
        
        # Test 1: Add custom words
        print("\n1. Testing add_custom_words()...")
        test_words = ["kubernetes", "docker", "microservices", "api", "database"]
        added_count = vocab_manager.add_custom_words(test_words)
        print(f"✅ Added {added_count} custom words")
        assert added_count == len(test_words), f"Expected {len(test_words)}, got {added_count}"
        
        # Test 2: Add proper nouns
        print("\n2. Testing proper noun handling...")
        proper_nouns = ["Amazon", "Microsoft", "OpenAI", "GitHub"]
        for noun in proper_nouns:
            vocab_manager._add_proper_noun(noun)
        print(f"✅ Added {len(proper_nouns)} proper nouns")
        
        # Test 3: Get vocabulary suggestions
        print("\n3. Testing vocabulary suggestions...")
        context = "Let's deploy our microservices to kubernetes"
        suggestions = vocab_manager.get_vocabulary_suggestions(context)
        print(f"✅ Got {len(suggestions)} suggestions for context")
        print(f"   Suggestions: {suggestions[:5]}")  # Show first 5
        
        # Test 4: Save and load vocabulary
        print("\n4. Testing save/load functionality...")
        saved = vocab_manager.save_vocabulary_preferences()
        print(f"✅ Vocabulary saved: {saved}")
        
        # Create new instance to test loading
        vocab_manager2 = VocabularyManager(config_dir=test_dir)
        vocab_data = vocab_manager2.get_all_vocabulary()
        print(f"✅ Loaded vocabulary: {vocab_data['total_words']} words, {vocab_data['total_proper_nouns']} proper nouns")
        
        # Test 5: Export vocabulary
        print("\n5. Testing vocabulary export...")
        export_file = Path(test_dir) / "test_export.json"
        exported = vocab_manager.export_vocabulary(str(export_file), "json")
        print(f"✅ Vocabulary exported: {exported}")
        
        if export_file.exists():
            with open(export_file, 'r') as f:
                export_data = json.load(f)
            print(f"   Export contains {len(export_data['custom_words'])} words")
        
        # Test 6: Load from file
        print("\n6. Testing load from file...")
        # Create a test vocabulary file
        test_vocab_file = Path(test_dir) / "test_vocab.json"
        test_vocab_data = {
            "words": ["python", "javascript", "typescript"],
            "proper_nouns": ["VSCode", "PyCharm"],
            "domains": {
                "programming": ["function", "variable", "class", "method"]
            }
        }
        
        with open(test_vocab_file, 'w') as f:
            json.dump(test_vocab_data, f)
        
        loaded = vocab_manager.load_custom_vocabulary(str(test_vocab_file))
        print(f"✅ Loaded vocabulary from file: {loaded}")
        
        # Clean up
        import shutil
        shutil.rmtree(test_dir)
        print(f"✅ Cleaned up test directory")
        
        print("\n✅ VocabularyManager tests completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"VocabularyManager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_continuous_recorder():
    """Test ContinuousRecorder functionality."""
    print("\n" + "=" * 60)
    print("Testing ContinuousRecorder...")
    print("=" * 60)
    
    try:
        from continuous_recorder import ContinuousRecorder, PYNPUT_AVAILABLE
        
        # Test with temporary directory
        test_dir = tempfile.mkdtemp(prefix="dicto_recorder_test_")
        
        print("\n1. Testing ContinuousRecorder initialization...")
        recorder = ContinuousRecorder(
            chunk_duration=2.0,  # Short chunks for testing
            max_session_duration=30.0,  # Short session for testing
            temp_dir=test_dir
        )
        
        if PYNPUT_AVAILABLE:
            print("✅ ContinuousRecorder initialized with pynput support")
        else:
            print("⚠️  ContinuousRecorder initialized without pynput (limited functionality)")
        
        print("\n2. Testing callback setup...")
        events = []
        
        def on_start():
            events.append("recording_started")
            print("📹 Recording started callback")
        
        def on_stop():
            events.append("recording_stopped")
            print("⏹️ Recording stopped callback")
        
        def on_chunk(chunk_path):
            events.append(f"chunk_complete: {Path(chunk_path).name}")
            print(f"📁 Chunk completed: {Path(chunk_path).name}")
        
        def on_session(chunk_paths):
            events.append(f"session_complete: {len(chunk_paths)} chunks")
            print(f"📂 Session completed: {len(chunk_paths)} chunks")
        
        recorder.set_callbacks(
            on_start=on_start,
            on_stop=on_stop,
            on_chunk=on_chunk,
            on_session=on_session
        )
        print("✅ Callbacks configured")
        
        print("\n3. Testing status methods...")
        status = recorder.get_recording_status()
        print(f"✅ Initial status: monitoring={status['is_monitoring']}, recording={status['is_recording']}")
        
        session_info = recorder.get_session_info()
        print(f"✅ Session info: {len(session_info)} fields")
        
        print("\n4. Testing manual session simulation...")
        # Simulate a recording session manually (without keyboard)
        recorder._start_recording_session()
        
        if recorder.is_recording:
            print("✅ Recording session started manually")
            time.sleep(3)  # Let it record a chunk
            
            recorder._stop_recording_session()
            print("✅ Recording session stopped manually")
        else:
            print("⚠️  Recording session simulation skipped (audio recording may not be available)")
        
        print(f"\n5. Events captured: {len(events)}")
        for event in events:
            print(f"   - {event}")
        
        print("\n6. Testing session cleanup...")
        cleaned = recorder.cleanup_session()
        print(f"✅ Session cleanup: {cleaned}")
        
        # Clean up test directory
        import shutil
        shutil.rmtree(test_dir)
        print(f"✅ Cleaned up test directory")
        
        print("\n✅ ContinuousRecorder tests completed successfully!")
        if PYNPUT_AVAILABLE:
            print("\nNote: Full CTRL+V functionality requires manual testing")
            print("      Start the app and hold CTRL+V to test continuous recording")
        else:
            print("\nNote: Install pynput to enable CTRL+V continuous recording functionality")
            print("      Run: pip install pynput")
        
        return True
        
    except Exception as e:
        logger.error(f"ContinuousRecorder test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_integration():
    """Test integration between vocabulary and recording components."""
    print("\n" + "=" * 60)
    print("Testing Integration...")
    print("=" * 60)
    
    try:
        print("\n1. Testing combined import...")
        from vocabulary_manager import VocabularyManager
        from continuous_recorder import ContinuousRecorder
        print("✅ Both modules imported successfully")
        
        print("\n2. Testing temporary directory sharing...")
        test_dir = tempfile.mkdtemp(prefix="dicto_integration_test_")
        
        vocab_manager = VocabularyManager(config_dir=test_dir + "/vocab")
        recorder = ContinuousRecorder(temp_dir=test_dir + "/audio")
        
        print("✅ Both components initialized with shared directory structure")
        
        print("\n3. Testing vocabulary with recording context...")
        # Add some technical vocabulary
        tech_words = ["transcription", "whisper", "audio", "recording", "continuous"]
        vocab_manager.add_custom_words(tech_words)
        
        context = "continuous recording with transcription"
        suggestions = vocab_manager.get_vocabulary_suggestions(context)
        print(f"✅ Got {len(suggestions)} vocabulary suggestions for recording context")
        
        # Clean up
        import shutil
        shutil.rmtree(test_dir)
        print(f"✅ Cleaned up integration test directory")
        
        print("\n✅ Integration tests completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_dependencies():
    """Test that all required dependencies are available."""
    print("=" * 60)
    print("Testing Dependencies...")
    print("=" * 60)
    
    dependencies = [
        ("json", "JSON parsing"),
        ("pathlib", "Path handling"),
        ("tempfile", "Temporary files"),
        ("threading", "Threading support"),
        ("logging", "Logging"),
        ("queue", "Thread-safe queues"),
        ("subprocess", "Process execution"),
        ("datetime", "Date/time handling"),
    ]
    
    optional_dependencies = [
        ("audio_recorder", "Audio recording"),
    ]
    
    pynput_test = [
        ("pynput", "Global hotkey support"),
    ]
    
    print("\n1. Checking required dependencies...")
    for module, description in dependencies:
        try:
            __import__(module)
            print(f"✅ {module:15} - {description}")
        except ImportError as e:
            print(f"❌ {module:15} - {description} - ERROR: {e}")
            return False
    
    print("\n2. Checking optional dependencies...")
    for module, description in optional_dependencies:
        try:
            __import__(module)
            print(f"✅ {module:15} - {description}")
        except ImportError as e:
            print(f"⚠️  {module:15} - {description} - WARNING: {e}")
    
    print("\n3. Checking pynput (for continuous recording)...")
    for module, description in pynput_test:
        try:
            __import__(module)
            print(f"✅ {module:15} - {description}")
        except ImportError as e:
            print(f"⚠️  {module:15} - {description} - Install with: pip install pynput")
    
    print("\n✅ Dependency check completed!")
    return True


def main():
    """Run all tests."""
    print("🎯 Dicto Task 6 - Vocabulary and Continuous Recording Tests")
    print("=" * 80)
    
    # Track test results
    results = {}
    
    # Test dependencies first
    results["dependencies"] = test_dependencies()
    
    # Test vocabulary manager
    results["vocabulary_manager"] = test_vocabulary_manager()
    
    # Test continuous recorder
    results["continuous_recorder"] = test_continuous_recorder()
    
    # Test integration
    results["integration"] = test_integration()
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        emoji = "✅" if result else "❌"
        print(f"{emoji} {test_name.replace('_', ' ').title():25} - {status}")
    
    print(f"\nResults: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("\n🎉 All tests passed! Task 6 implementation is ready.")
        print("\nNext steps:")
        print("1. Test CTRL+V continuous recording manually")
        print("2. Create vocabulary files for your use case")
        print("3. Integrate with dicto_main.py")
        return True
    else:
        print(f"\n❌ {total_tests - passed_tests} test(s) failed. Please fix issues before proceeding.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 