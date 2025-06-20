#!/bin/bash

# Quick activation script for Dicto
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Run ./setup_venv.sh first"
    exit 1
fi

echo "🔌 Activating Dicto environment..."
source venv/bin/activate

echo "✅ Dicto environment activated!"
echo "🎤 You can now run: python dicto_simple.py"
echo "📋 To deactivate later: deactivate" 