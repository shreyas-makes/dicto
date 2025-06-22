#!/bin/bash

# Dicto activation script with proper virtual environment handling
# This script ensures the virtual environment is properly activated before running Dicto

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"
PYTHON_BIN="$VENV_DIR/bin/python"

echo "🎙️  Starting Dicto with proper environment..."

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo "❌ Virtual environment not found at $VENV_DIR"
    echo "Run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Check if Python binary exists in venv
if [ ! -f "$PYTHON_BIN" ]; then
    echo "❌ Python binary not found in virtual environment"
    exit 1
fi

# Verify pynput is available
echo "🔍 Checking dependencies..."
if ! "$PYTHON_BIN" -c "import pynput; print('✅ pynput available')" 2>/dev/null; then
    echo "❌ pynput not available in virtual environment"
    echo "Installing pynput..."
    "$VENV_DIR/bin/pip" install pynput plyer pyobjc-framework-Cocoa
fi

# Set environment variables to ensure proper Python path
export VIRTUAL_ENV="$VENV_DIR"
export PATH="$VENV_DIR/bin:$PATH"
unset PYTHON_HOME

echo "✅ Environment configured"
echo "✅ Using Python: $PYTHON_BIN"

# Run Dicto with the virtual environment Python
exec "$PYTHON_BIN" dicto_main.py "$@"

mkdir -p markdown_files 