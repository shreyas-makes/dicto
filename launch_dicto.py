#!/usr/bin/env python3
"""
Dicto Launcher - Simple launcher with better error handling
"""

import sys
import os
from pathlib import Path

def check_permissions():
    """Check if we have the necessary permissions."""
    print("🔍 Checking permissions...")
    
    # Test microphone access
    try:
        import pyaudio
        audio = pyaudio.PyAudio()
        audio.terminate()
        print("✅ Microphone access: OK")
    except Exception as e:
        print(f"❌ Microphone access: FAILED - {e}")
        print("💡 Go to System Preferences → Privacy & Security → Microphone")
        print("💡 Add Terminal or Python to the allowed apps")
        return False
    
    return True

def check_dependencies():
    """Check if all dependencies are installed."""
    print("🔍 Checking dependencies...")
    
    missing = []
    try:
        import pyaudio
        print("✅ pyaudio: OK")
    except ImportError:
        missing.append("pyaudio")
    
    try:
        from pynput import keyboard
        print("✅ pynput: OK")
    except ImportError:
        missing.append("pynput")
    
    try:
        from plyer import notification
        print("✅ plyer: OK")
    except ImportError:
        missing.append("plyer")
    
    try:
        import AppKit
        print("✅ AppKit: OK")
    except ImportError:
        missing.append("AppKit")
    
    if missing:
        print(f"❌ Missing dependencies: {', '.join(missing)}")
        print("💡 Run: pip3 install " + " ".join(missing))
        return False
    
    return True

def check_whisper():
    """Check if whisper.cpp is properly set up."""
    print("🔍 Checking Whisper setup...")
    
    whisper_cli = Path("whisper.cpp/build/bin/whisper-cli")
    model_file = Path("whisper.cpp/models/ggml-base.en.bin")
    
    if not whisper_cli.exists():
        print(f"❌ Whisper CLI not found at {whisper_cli}")
        print("💡 Make sure you're in the project directory and whisper.cpp is built")
        return False
    else:
        print("✅ Whisper CLI: OK")
    
    if not model_file.exists():
        print(f"❌ Whisper model not found at {model_file}")
        print("💡 Download model with: cd whisper.cpp && bash ./models/download-ggml-model.sh base.en")
        return False
    else:
        print("✅ Whisper model: OK")
    
    return True

def main():
    """Main launcher function."""
    print("🚀 Dicto AI Transcription Launcher")
    print("=" * 40)
    
    # Check all requirements
    if not check_dependencies():
        sys.exit(1)
    
    if not check_whisper():
        sys.exit(1)
    
    if not check_permissions():
        print("\n⚠️  Microphone access denied. Please grant permissions and try again.")
        sys.exit(1)
    
    print("\n✅ All checks passed! Starting Dicto...")
    print("=" * 40)
    
    # Import and run the main app
    try:
        from dicto_app import DictoApp
        app = DictoApp()
        app.run()
    except Exception as e:
        print(f"❌ Error starting app: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 