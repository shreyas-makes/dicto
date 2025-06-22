#!/usr/bin/env python3
"""
Specific Feature Tests - Show exactly what each feature does
This script demonstrates specific functionality with clear examples.
"""

import time
import tempfile
from pathlib import Path

def test_vocabulary_features():
    """Test vocabulary features with clear examples."""
    print("🎯 VOCABULARY MANAGER - SPECIFIC FEATURES")
    print("=" * 50)
    
    from vocabulary_manager import VocabularyManager
    
    # Create vocab manager
    temp_dir = tempfile.mkdtemp(prefix="vocab_test_")
    vocab = VocabularyManager(config_dir=temp_dir)
    
    print("\n1. 📝 Adding Technical Terms:")
    tech_terms = ["kubernetes", "microservices", "API", "containerization"]
    added = vocab.add_custom_words(tech_terms)
    print(f"   Added {added} technical terms: {', '.join(tech_terms)}")
    
    print("\n2. 🏢 Adding Company Names:")
    companies = ["Docker", "AWS", "Microsoft", "Google"]
    added = vocab.add_proper_nouns(companies)
    print(f"   Added {added} company names: {', '.join(companies)}")
    
    print("\n3. 🔍 Context-Aware Suggestions:")
    test_contexts = [
        "kubernetes deployment",
        "AWS cloud services", 
        "Docker container setup"
    ]
    
    for context in test_contexts:
        suggestions = vocab.get_vocabulary_suggestions(context)
        print(f"   Context: '{context}' → Suggestions: {suggestions}")
    
    print("\n4. 💾 Saving/Loading Vocabulary:")
    vocab_file = Path(temp_dir) / "my_vocabulary.json"
    saved = vocab.save_vocabulary_to_file(str(vocab_file))
    print(f"   Saved vocabulary: {saved}")
    
    # Load in new instance
    new_vocab = VocabularyManager()
    loaded = new_vocab.load_vocabulary_from_file(str(vocab_file))
    print(f"   Loaded in new instance: {loaded}")
    print(f"   Words loaded: {len(new_vocab.custom_words)}")
    
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)
    
    return True

def test_recording_features():
    """Test continuous recording features."""
    print("\n🎯 CONTINUOUS RECORDER - SPECIFIC FEATURES")
    print("=" * 50)
    
    from continuous_recorder import ContinuousRecorder
    
    # Create recorder
    temp_dir = tempfile.mkdtemp(prefix="recorder_test_")
    recorder = ContinuousRecorder(
        chunk_duration=3.0,  # 3 second chunks for demo
        temp_dir=temp_dir
    )
    
    print("\n1. 🎙️ Recorder Status:")
    status = recorder.get_recording_status()
    print(f"   Recording: {status['is_recording']}")
    print(f"   Monitoring: {status['is_monitoring']}")
    print(f"   Key detection: {status['key_detection_available']}")
    
    print("\n2. 📞 Event Callbacks:")
    events = []
    
    def on_start():
        events.append("🔴 Recording Started")
        print("   🔴 Recording Started!")
    
    def on_chunk(chunk_path):
        events.append(f"📁 Chunk: {Path(chunk_path).name}")
        print(f"   📁 Chunk saved: {Path(chunk_path).name}")
    
    def on_stop():
        events.append("⏹️ Recording Stopped")
        print("   ⏹️ Recording Stopped!")
    
    recorder.set_callbacks(on_start=on_start, on_chunk=on_chunk, on_stop=on_stop)
    
    print("\n3. 🎬 Simulating Recording Session:")
    print("   (This is what happens when you hold CTRL+V)")
    
    # Start recording
    recorder._start_recording_session()
    
    if recorder.is_recording:
        print("   ⏳ Recording for 7 seconds...")
        time.sleep(7)  # Record for 7 seconds (should create 2-3 chunks)
        
        recorder._stop_recording_session()
    
    print(f"\n4. 📊 Session Results:")
    session_info = recorder.get_session_info()
    print(f"   Session ID: {session_info['session_id']}")
    print(f"   Chunks created: {session_info['chunk_count']}")
    print(f"   Events captured: {len(events)}")
    
    for event in events:
        print(f"   - {event}")
    
    # Cleanup
    recorder.cleanup_session()
    import shutil
    shutil.rmtree(temp_dir)
    
    return True

def test_integration_scenario():
    """Test a realistic integration scenario."""
    print("\n🎯 INTEGRATION SCENARIO - MEDICAL DICTATION")
    print("=" * 50)
    
    from vocabulary_manager import VocabularyManager
    from continuous_recorder import ContinuousRecorder
    
    # Setup
    temp_dir = tempfile.mkdtemp(prefix="medical_demo_")
    vocab = VocabularyManager(config_dir=temp_dir + "/vocab")
    recorder = ContinuousRecorder(temp_dir=temp_dir + "/audio")
    
    print("\n1. 📝 Setting up Medical Vocabulary:")
    medical_terms = [
        "stethoscope", "diagnosis", "prescription", "symptoms",
        "hypertension", "diabetes", "medication", "treatment"
    ]
    medical_orgs = ["Mayo Clinic", "Johns Hopkins", "Cleveland Clinic"]
    
    vocab.add_custom_words(medical_terms)
    vocab.add_proper_nouns(medical_orgs)
    
    print(f"   Added {len(medical_terms)} medical terms")
    print(f"   Added {len(medical_orgs)} medical organizations")
    
    print("\n2. 🔍 Testing Medical Context Recognition:")
    medical_contexts = [
        "patient shows symptoms of hypertension",
        "prescription medication for diabetes",
        "diagnosis from Mayo Clinic specialist"
    ]
    
    for context in medical_contexts:
        suggestions = vocab.get_vocabulary_suggestions(context)
        print(f"   '{context}' → {suggestions}")
    
    print("\n3. 🎙️ Simulating Medical Dictation:")
    
    # Track vocabulary usage
    vocab_usage = []
    
    def medical_chunk_handler(chunk_path):
        # Simulate vocabulary enhancement on each chunk
        context = "medical examination notes"
        suggestions = vocab.get_vocabulary_suggestions(context)
        vocab_usage.append(f"Chunk with {len(suggestions)} vocabulary suggestions")
        print(f"   📁 {Path(chunk_path).name} - {len(suggestions)} vocab suggestions")
    
    recorder.set_callbacks(on_chunk=medical_chunk_handler)
    
    # Simulate dictation
    recorder._start_recording_session()
    if recorder.is_recording:
        print("   🔴 Medical dictation in progress...")
        time.sleep(4)  # Short dictation
        recorder._stop_recording_session()
        print("   ⏹️ Medical dictation complete")
    
    print(f"\n4. 📊 Medical Dictation Results:")
    for usage in vocab_usage:
        print(f"   - {usage}")
    
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)
    
    return True

def show_app_usage():
    """Show how to use the main app."""
    print("\n🎯 HOW TO USE THE MAIN DICTO APP")
    print("=" * 50)
    
    print("\n🚀 LAUNCHING THE APP:")
    print("   python dicto_main.py")
    print("   → App appears in your menu bar with 🎙️ icon")
    
    print("\n🎹 BASIC USAGE:")
    print("   1. Hold CTRL+V to start recording")
    print("   2. Speak your text")
    print("   3. Release CTRL+V to stop")
    print("   4. Text automatically appears where your cursor is")
    
    print("\n📝 VOCABULARY FEATURES:")
    print("   • Add technical terms via menu bar")
    print("   • Better transcription accuracy for domain-specific words")
    print("   • Proper noun capitalization")
    print("   • Context-aware suggestions")
    
    print("\n⏱️ CONTINUOUS RECORDING:")
    print("   • Hold CTRL+V for 30+ seconds")
    print("   • Automatic chunking every 30 seconds")
    print("   • Complete transcription when released")
    print("   • No memory issues with long recordings")
    
    print("\n📊 MENU BAR FEATURES:")
    print("   • 🔴 Recording status indicator")
    print("   • 📋 Session history")
    print("   • ⚙️ Settings and preferences")
    print("   • 📝 Vocabulary management")
    print("   • 🔧 Debug information")
    
    print("\n🎯 TESTING SCENARIOS:")
    print("   1. Basic: 'Hello, this is a test'")
    print("   2. Technical: 'Deploy kubernetes microservices'")
    print("   3. Medical: 'Patient shows symptoms of hypertension'")
    print("   4. Long form: Hold CTRL+V for 60+ seconds")

def main():
    """Run all specific feature tests."""
    print("🎯 DICTO TASK 6 - SPECIFIC FEATURE DEMONSTRATION")
    print("=" * 60)
    print("This shows exactly what each feature does with clear examples.")
    
    try:
        # Test each component
        test_vocabulary_features()
        test_recording_features()
        test_integration_scenario()
        show_app_usage()
        
        print("\n" + "=" * 60)
        print("✅ ALL FEATURES DEMONSTRATED SUCCESSFULLY!")
        print("=" * 60)
        
        print("\n🎉 READY TO USE:")
        print("   python dicto_main.py")
        print("   Then hold CTRL+V to record!")
        
    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 