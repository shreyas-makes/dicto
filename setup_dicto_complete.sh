#!/bin/bash

# Dicto Complete Setup Script
# This script sets up the complete Dicto environment with all dependencies for CTRL+V functionality

set -e  # Exit on any error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"

echo "🎙️  Setting up Dicto with CTRL+V functionality..."

# Check if we're on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ This script is designed for macOS. Dicto requires macOS for optimal functionality."
    exit 1
fi

# Check Python version
echo "🔍 Checking Python version..."
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "✅ Python version: $PYTHON_VERSION"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)" 2>/dev/null; then
    echo "❌ Python 3.8 or higher is required. Current version: $PYTHON_VERSION"
    exit 1
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "📚 Installing Python dependencies..."
if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
    pip install -r "$SCRIPT_DIR/requirements.txt"
    echo "✅ Python dependencies installed"
else
    echo "❌ requirements.txt not found"
    exit 1
fi

# Check for Homebrew (needed for audio tools)
echo "🍺 Checking for Homebrew..."
if ! command -v brew &> /dev/null; then
    echo "❌ Homebrew not found. Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    echo "✅ Homebrew installed"
else
    echo "✅ Homebrew found"
fi

# Install system dependencies
echo "🔧 Installing system dependencies..."

# Install SoX for audio processing
if ! command -v sox &> /dev/null; then
    echo "📦 Installing SoX..."
    brew install sox
    echo "✅ SoX installed"
else
    echo "✅ SoX already installed"
fi

# Install FFmpeg for advanced audio processing
if ! command -v ffmpeg &> /dev/null; then
    echo "📦 Installing FFmpeg..."
    brew install ffmpeg
    echo "✅ FFmpeg installed"
else
    echo "✅ FFmpeg already installed"
fi

# Check for whisper.cpp
echo "🤖 Checking Whisper.cpp setup..."
WHISPER_BINARY="$SCRIPT_DIR/whisper.cpp/main"
WHISPER_MODEL="$SCRIPT_DIR/whisper.cpp/models/ggml-base.en.bin"

if [ ! -f "$WHISPER_BINARY" ]; then
    echo "⚠️  Whisper binary not found at: $WHISPER_BINARY"
    echo "   Please build whisper.cpp manually or run the whisper setup script"
    if [ -d "$SCRIPT_DIR/whisper.cpp" ]; then
        echo "💡 Try running: cd whisper.cpp && make && cd .."
    else
        echo "💡 Try running: git clone https://github.com/ggerganov/whisper.cpp.git"
    fi
else
    echo "✅ Whisper binary found"
fi

if [ ! -f "$WHISPER_MODEL" ]; then
    echo "⚠️  Whisper model not found at: $WHISPER_MODEL"
    echo "💡 Download with: curl -o whisper.cpp/models/ggml-base.en.bin https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin"
else
    echo "✅ Whisper model found"
fi

# Test key dependencies
echo "🧪 Testing key dependencies..."

# Test PyObjC frameworks
echo "🔍 Testing PyObjC frameworks..."
if python3 -c "from AppKit import NSPasteboard; print('✅ AppKit available')" 2>/dev/null; then
    echo "✅ AppKit framework working"
else
    echo "❌ AppKit framework not working"
fi

if python3 -c "from Quartz import CGEventTapCreate; print('✅ Quartz available')" 2>/dev/null; then
    echo "✅ Quartz framework working (enhanced CTRL+V detection)"
else
    echo "⚠️  Quartz framework not available (will fallback to pynput)"
    echo "   Installing pyobjc-framework-Quartz..."
    pip install pyobjc-framework-Quartz
fi

# Test pynput
if python3 -c "import pynput; print('✅ pynput available')" 2>/dev/null; then
    echo "✅ pynput working (fallback key detection)"
else
    echo "❌ pynput not working"
fi

# Test audio dependencies
echo "🔊 Testing audio dependencies..."
if python3 -c "import sounddevice; print('✅ sounddevice available')" 2>/dev/null; then
    echo "✅ sounddevice working"
else
    echo "❌ sounddevice not working"
fi

if python3 -c "import pyaudio; print('✅ pyaudio available')" 2>/dev/null; then
    echo "✅ pyaudio working"
else
    echo "❌ pyaudio not working"
fi

# Check for accessibility permissions
echo "🔐 Checking accessibility permissions..."
echo "⚠️  IMPORTANT: Dicto needs accessibility permissions to detect global CTRL+V hotkeys"
echo "   Go to: System Preferences → Privacy & Security → Accessibility"
echo "   Add Terminal or your terminal app to the list and enable it"
echo "   This allows Dicto to detect keyboard input globally"

# Create launch script
echo "🚀 Creating launch script..."
cat > "$SCRIPT_DIR/launch_dicto_easy.sh" << 'EOF'
#!/bin/bash
# Easy launch script for Dicto

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🎙️  Launching Dicto..."
echo "📍 Working directory: $SCRIPT_DIR"

# Activate virtual environment and run
source venv/bin/activate
python3 dicto_main.py

EOF

chmod +x "$SCRIPT_DIR/launch_dicto_easy.sh"
echo "✅ Launch script created: launch_dicto_easy.sh"

# Final verification
echo ""
echo "🎯 Setup Complete! Final verification:"
echo "✅ Virtual environment: $VENV_DIR"
echo "✅ Python dependencies installed"
echo "✅ System tools (SoX, FFmpeg) installed"

if [ -f "$WHISPER_BINARY" ] && [ -f "$WHISPER_MODEL" ]; then
    echo "✅ Whisper.cpp ready"
else
    echo "⚠️  Whisper.cpp needs setup (see messages above)"
fi

echo ""
echo "🚀 To run Dicto:"
echo "   Option 1: ./launch_dicto_easy.sh"
echo "   Option 2: ./activate_dicto.sh"
echo "   Option 3: source venv/bin/activate && python3 dicto_main.py"
echo ""
echo "🔥 CTRL+V Features:"
echo "   • Press and hold CTRL+V anywhere to start recording"
echo "   • Release CTRL+V to stop and get transcription"
echo "   • Works in any text input area system-wide"
echo "   • Transcription automatically copied to clipboard"
echo ""
echo "⚠️  Don't forget to grant accessibility permissions!"
echo "   System Preferences → Privacy & Security → Accessibility"
echo "" 