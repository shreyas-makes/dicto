#!/bin/bash

echo "🚀 Setting up Dicto AI Transcription App..."

# Check if we're on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ This app is designed for macOS only"
    exit 1
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt

# Make the Python script executable
chmod +x dicto_app.py

# Check if whisper.cpp is built
if [ ! -f "whisper.cpp/build/bin/whisper-cli" ]; then
    echo "❌ Whisper.cpp not found. Please run this from the project directory."
    exit 1
fi

if [ ! -f "whisper.cpp/models/ggml-base.en.bin" ]; then
    echo "❌ Whisper model not found. Please run this from the project directory."
    exit 1
fi

echo "✅ Setup complete!"
echo ""
echo "🎤 To start Dicto:"
echo "   python3 dicto_app.py"
echo ""
echo "📌 Usage:"
echo "   • Press Cmd+V to start/stop recording"
echo "   • Transcription will be copied to clipboard automatically"
echo "   • Press Cmd+Q to quit"
echo ""
echo "⚠️  Important: You may need to grant microphone permissions in System Preferences > Security & Privacy > Privacy > Microphone"
echo "⚠️  You may also need to grant accessibility permissions for global hotkeys to work" 