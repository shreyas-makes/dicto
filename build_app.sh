#!/bin/bash
###############################################################################
# Dicto macOS App Builder
# This script automates the process of building Dicto.app
###############################################################################

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Dicto macOS App Builder               ║${NC}"
echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo ""

# Function to print status messages
print_status() {
    echo -e "${BLUE}▶${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    print_error "This script must be run on macOS"
    exit 1
fi

print_success "Running on macOS"

# Check for Python 3
print_status "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed"
    echo "Install Python 3 from https://www.python.org/downloads/"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
print_success "Python ${PYTHON_VERSION} found"

# Check for virtual environment
print_status "Checking virtual environment..."
if [ ! -d "venv" ]; then
    print_warning "Virtual environment not found, creating one..."
    python3 -m venv venv
    print_success "Virtual environment created"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate
print_success "Virtual environment activated"

# Install/update py2app
print_status "Installing py2app..."
pip install --upgrade pip setuptools wheel py2app > /dev/null 2>&1
print_success "py2app installed"

# Install dependencies
print_status "Installing dependencies..."
pip install -r requirements.txt > /dev/null 2>&1
print_success "Dependencies installed"

# Check for whisper.cpp binary
print_status "Checking for Whisper binary..."
if [ ! -f "whisper.cpp/build/bin/whisper-cli" ]; then
    print_error "Whisper binary not found at whisper.cpp/build/bin/whisper-cli"
    echo ""
    echo "Please build whisper.cpp first:"
    echo "  cd whisper.cpp"
    echo "  cmake -B build -DWHISPER_METAL=ON"
    echo "  cmake --build build --config Release"
    exit 1
fi
print_success "Whisper binary found"

# Check for Whisper model
print_status "Checking for Whisper model..."
if [ ! -f "whisper.cpp/models/ggml-base.en.bin" ]; then
    print_error "Whisper model not found at whisper.cpp/models/ggml-base.en.bin"
    echo ""
    echo "Please download the model:"
    echo "  cd whisper.cpp"
    echo "  bash ./models/download-ggml-model.sh base.en"
    exit 1
fi
print_success "Whisper model found"

# Clean previous builds
print_status "Cleaning previous builds..."
rm -rf build dist
print_success "Clean complete"

# Build the app
print_status "Building Dicto.app..."
python setup.py py2app

if [ $? -eq 0 ]; then
    print_success "Build complete!"
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  Build Successful!                     ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
    echo ""
    echo "Your app is ready at: ${BLUE}dist/Dicto.app${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Test the app: open dist/Dicto.app"
    echo "  2. Move to Applications: cp -r dist/Dicto.app /Applications/"
    echo "  3. Grant permissions in System Preferences:"
    echo "     • Security & Privacy → Microphone → Add Dicto"
    echo "     • Security & Privacy → Accessibility → Add Dicto"
    echo ""

    # Optional: Open the dist folder
    read -p "Open dist folder in Finder? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        open dist
    fi
else
    print_error "Build failed!"
    echo "Check the error messages above for details."
    exit 1
fi
