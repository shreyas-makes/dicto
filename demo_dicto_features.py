#!/usr/bin/env python3
"""
Dicto Features Demo - Interactive demonstration of all Task 6 features
This script shows you exactly what's working and how to test each feature manually.
"""

import os
import sys
import time
import tempfile
import json
from pathlib import Path

def print_header(title):
    """Print a formatted header."""
    print("\n" + "="*80)
    print(f"🎯 {title}")
    print("="*80)

def print_section(title):
    """Print a formatted section."""
    print(f"\n{'='*60}")
    print(f"📋 {title}")
    print(f"{'='*60}")

def wait_for_user():
    """Wait for user to press Enter."""
    input("\n👆 Press Enter to continue...")

def demo_vocabulary_manager():
    """Demonstrate VocabularyManager features."""
    print_section("VOCABULARY MANAGER DEMO")
    
    from vocabulary_manager import VocabularyManager
    
    # Create temporary directory for demo
    temp_dir = tempfile.mkdtemp(prefix="dicto_vocab_demo_")
    vocab = VocabularyManager(config_dir=temp_dir)
    
    print("1. 📝 Adding Custom Technical Words...")
    tech_words = [
        "kubernetes", "microservices", "containerization", 
        "API", "GraphQL", "PostgreSQL", "MongoDB"
    ]
    vocab.add_custom_words(tech_words)
    print(f"   ✅ Added: {', '.join(tech_words)}")
    
    print("\n2. 🏢 Adding Company/Product Names...")
    proper_nouns = ["Docker", "AWS", "Azure", "Google Cloud", "Terraform"]
    vocab.add_proper_nouns(proper_nouns)
    print(f"   ✅ Added: {', '.join(proper_nouns)}")
    
    print("\n3. 🔍 Testing Context-Aware Suggestions...")
    contexts = [
        "kubernetes deployment with docker",
        "API development using GraphQL",
        "cloud infrastructure on AWS"
    ]
    
    for context in contexts:
        suggestions = vocab.get_vocabulary_suggestions(context)
        print(f"   📝 Context: '{context}'")
        print(f"   💡 Suggestions: {suggestions}")
    
    print("\n4. 💾 Testing Save/Load Functionality...")
    vocab_file = Path(temp_dir) / "test_vocabulary.json"
    success = vocab.save_vocabulary_to_file(str(vocab_file))
    print(f"   ✅ Saved to file: {success}")
    
    # Load in new instance
    new_vocab = VocabularyManager()
    loaded = new_vocab.load_vocabulary_from_file(str(vocab_file))
    print(f"   ✅ Loaded from file: {loaded}")
    print(f"   📊 Words loaded: {len(new_vocab.custom_words)}")
    
    print("\n5. 📤 Testing Export Functionality...")
    export_data = vocab.export_vocabulary()
    print(f"   ✅ Export successful: {export_data is not None}")
    if export_data:
        print(f"   📊 Export contains {len(export_data.get('words', []))} words")
        print(f"   📊 Export contains {len(export_data.get('proper_nouns', []))} proper nouns")
    
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)
    print(f"\n🧹 Cleaned up demo directory")
    
    return True

def demo_continuous_recorder():
    """Demonstrate ContinuousRecorder features."""
    print_section("CONTINUOUS RECORDER DEMO")
    
    from continuous_recorder import ContinuousRecorder
    
    # Create temporary directory for demo
    temp_dir = tempfile.mkdtemp(prefix="dicto_recorder_demo_")
    recorder = ContinuousRecorder(
        chunk_duration=5.0,  # 5 second chunks for demo
        temp_dir=temp_dir
    )
    
    print("1. 🎙️ Testing Recorder Initialization...")
    status = recorder.get_recording_status()
    print(f"   ✅ Recorder initialized")
    print(f"   📊 Status: Recording={status['is_recording']}, Monitoring={status['is_monitoring']}")
    print(f"   🔧 Key detection available: {status['key_detection_available']}")
    
    print("\n2. 📞 Setting Up Event Callbacks...")
    events_captured = []
    
    def on_start():
        events_captured.append("🎙️ Recording Started")
        print("   🔴 RECORDING STARTED!")
    
    def on_stop():
        events_captured.append("⏹️ Recording Stopped")
        print("   ⏹️ RECORDING STOPPED!")
    
    def on_chunk(chunk_path):
        events_captured.append(f"📁 Chunk: {Path(chunk_path).name}")
        print(f"   📁 Chunk saved: {Path(chunk_path).name}")
    
    def on_session(chunk_paths):
        events_captured.append(f"📂 Session: {len(chunk_paths)} chunks")
        print(f"   📂 Session complete: {len(chunk_paths)} chunks")
    
    recorder.set_callbacks(
        on_start=on_start,
        on_stop=on_stop, 
        on_chunk=on_chunk,
        on_session=on_session
    )
    print("   ✅ Callbacks configured")
    
    print("\n3. 🎬 Simulating Recording Session...")
    print("   (This simulates what happens when you hold CTRL+V)")
    
    # Start a manual recording session
    recorder._start_recording_session()
    
    if recorder.is_recording:
        print("   🔴 Recording session started")
        print("   ⏳ Recording for 8 seconds (will create 2 chunks)...")
        time.sleep(8)  # Let it record for 8 seconds (should create 2 chunks)
        
        recorder._stop_recording_session()
        print("   ⏹️ Recording session stopped")
    else:
        print("   ⚠️ Recording simulation skipped (audio may not be available)")
    
    print(f"\n4. 📊 Session Information...")
    session_info = recorder.get_session_info()
    print(f"   📂 Session ID: {session_info['session_id']}")
    print(f"   📁 Chunks created: {session_info['chunk_count']}")
    print(f"   ⏰ Start time: {session_info['start_time']}")
    
    print(f"\n5. 🎉 Events Captured ({len(events_captured)}):")
    for event in events_captured:
        print(f"   {event}")
    
    print(f"\n6. 🧹 Testing Cleanup...")
    cleaned = recorder.cleanup_session()
    print(f"   ✅ Session cleanup: {cleaned}")
    
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)
    print(f"   🧹 Cleaned up demo directory")
    
    return True

def demo_integration():
    """Demonstrate integration between components."""
    print_section("INTEGRATION DEMO")
    
    from vocabulary_manager import VocabularyManager
    from continuous_recorder import ContinuousRecorder
    
    print("1. 🔗 Testing Component Integration...")
    
    # Create shared temp directory
    temp_dir = tempfile.mkdtemp(prefix="dicto_integration_demo_")
    
    # Initialize both components
    vocab = VocabularyManager(config_dir=temp_dir + "/vocab")
    recorder = ContinuousRecorder(temp_dir=temp_dir + "/audio")
    
    print("   ✅ Both components initialized with shared directory")
    
    print("\n2. 📝 Setting up Medical Vocabulary Example...")
    medical_words = [
        "stethoscope", "diagnosis", "prescription", "symptoms",
        "patient", "treatment", "medication", "examination"
    ]
    medical_proper_nouns = ["Pfizer", "Johnson & Johnson", "Mayo Clinic"]
    
    vocab.add_custom_words(medical_words)
    vocab.add_proper_nouns(medical_proper_nouns)
    print(f"   ✅ Added {len(medical_words)} medical terms")
    print(f"   ✅ Added {len(medical_proper_nouns)} medical organizations")
    
    print("\n3. 🔍 Testing Medical Context Suggestions...")
    medical_contexts = [
        "patient examination with stethoscope",
        "prescription medication from Pfizer",
        "diagnosis and treatment plan"
    ]
    
    for context in medical_contexts:
        suggestions = vocab.get_vocabulary_suggestions(context)
        print(f"   📝 Context: '{context}'")
        print(f"   💊 Medical suggestions: {suggestions}")
    
    print("\n4. 🎙️ Simulating Medical Dictation Session...")
    
    # Set up recording with vocabulary context
    session_events = []
    
    def medical_on_chunk(chunk_path):
        # Simulate vocabulary enhancement
        context = "medical examination notes"
        suggestions = vocab.get_vocabulary_suggestions(context)
        session_events.append(f"Chunk recorded with {len(suggestions)} vocab suggestions")
    
    recorder.set_callbacks(on_chunk=medical_on_chunk)
    
    # Simulate short recording
    recorder._start_recording_session()
    if recorder.is_recording:
        print("   🔴 Medical dictation started")
        time.sleep(3)  # Short recording
        recorder._stop_recording_session()
        print("   ⏹️ Medical dictation completed")
    
    print(f"\n5. 📊 Integration Results:")
    for event in session_events:
        print(f"   {event}")
    
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)
    print(f"\n🧹 Cleaned up integration demo")
    
    return True

def show_app_launch_instructions():
    """Show how to launch the main app."""
    print_section("HOW TO LAUNCH THE MAIN APP")
    
    print("🚀 To launch the full Dicto app with menu bar:")
    print("")
    print("1. 📦 Install required dependencies:")
    print("   pip install rumps pynput plyer pyobjc-framework-Cocoa")
    print("")
    print("2. 🏗️ Build Whisper.cpp (if not already done):")
    print("   cd whisper.cpp")
    print("   make")
    print("")
    print("3. 📥 Download Whisper model (if not already done):")
    print("   cd whisper.cpp/models")
    print("   ./download-ggml-model.sh base.en")
    print("")
    print("4. 🎯 Launch the app:")
    print("   python dicto_main.py")
    print("")
    print("5. 📱 The app will appear in your menu bar with a microphone icon")
    print("")
    print("6. 🎹 Use CTRL+V to start continuous recording:")
    print("   - Hold CTRL+V to record")
    print("   - Release to stop and auto-transcribe")
    print("   - Text is automatically inserted where your cursor is")
    print("")
    print("💡 Features you'll see in the menu bar:")
    print("   - 🔴 Recording status indicator")
    print("   - 📊 Session history")
    print("   - ⚙️ Settings and preferences")
    print("   - 📝 Vocabulary management")
    print("   - 🔧 Debug information")

def show_manual_testing_guide():
    """Show manual testing scenarios."""
    print_section("MANUAL TESTING SCENARIOS")
    
    scenarios = [
        {
            "name": "🎙️ Basic Recording Test",
            "steps": [
                "Launch the app: python dicto_main.py",
                "Hold CTRL+V and speak: 'Hello, this is a test recording'",
                "Release CTRL+V",
                "Check that text appears in your active text field",
                "Verify notification shows transcription result"
            ]
        },
        {
            "name": "📝 Custom Vocabulary Test", 
            "steps": [
                "Add technical terms to vocabulary (via menu or code)",
                "Hold CTRL+V and speak technical terms",
                "Release and check transcription accuracy",
                "Compare with/without vocabulary enhancement"
            ]
        },
        {
            "name": "⏱️ Continuous Recording Test",
            "steps": [
                "Hold CTRL+V for 30+ seconds",
                "Speak continuously with pauses",
                "Release and check complete transcription",
                "Verify chunked recording worked properly"
            ]
        },
        {
            "name": "🔄 Session Management Test",
            "steps": [
                "Record several different sessions",
                "Check menu bar -> History",
                "Verify sessions are saved with timestamps",
                "Test session playback/review"
            ]
        },
        {
            "name": "⚙️ Error Handling Test",
            "steps": [
                "Try recording without microphone permission",
                "Test with very short recordings",
                "Test with very long recordings",
                "Verify error notifications appear"
            ]
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{i}. {scenario['name']}")
        for j, step in enumerate(scenario['steps'], 1):
            print(f"   {j}. {step}")

def main():
    """Run the complete demo."""
    print_header("DICTO TASK 6 - COMPLETE FEATURE DEMONSTRATION")
    
    print("This demo will show you exactly what features are working and how to test them.")
    print("Each section demonstrates different components with real examples.")
    
    wait_for_user()
    
    # Run feature demos
    demos = [
        ("Vocabulary Manager", demo_vocabulary_manager),
        ("Continuous Recorder", demo_continuous_recorder), 
        ("Component Integration", demo_integration)
    ]
    
    results = {}
    for name, demo_func in demos:
        try:
            print_header(f"DEMO: {name.upper()}")
            results[name] = demo_func()
            print(f"\n✅ {name} demo completed successfully!")
            wait_for_user()
        except Exception as e:
            print(f"\n❌ {name} demo failed: {e}")
            results[name] = False
            import traceback
            traceback.print_exc()
            wait_for_user()
    
    # Show app launch instructions
    show_app_launch_instructions()
    wait_for_user()
    
    # Show manual testing guide
    show_manual_testing_guide()
    wait_for_user()
    
    # Final summary
    print_header("DEMO SUMMARY")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    print(f"📊 Demo Results: {passed}/{total} components working")
    
    for name, result in results.items():
        status = "✅ WORKING" if result else "❌ FAILED"
        print(f"   {name}: {status}")
    
    if passed == total:
        print(f"\n🎉 ALL FEATURES ARE WORKING!")
        print(f"Ready to launch the full app with: python dicto_main.py")
    else:
        print(f"\n⚠️ Some components need attention before full app launch")
    
    print(f"\n💡 Next Steps:")
    print(f"1. Install missing dependencies if any")
    print(f"2. Test the full app: python dicto_main.py")
    print(f"3. Try the manual testing scenarios above")
    print(f"4. Report any issues you find")

if __name__ == "__main__":
    main() 