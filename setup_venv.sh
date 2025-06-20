#!/bin/bash

# Dicto Virtual Environment Setup Script
echo "🔧 Setting up Dicto Virtual Environment..."

# Check if we're in the dicto directory
if [ ! -f "dicto_simple.py" ]; then
    echo "❌ Please run this script from the dicto project directory"
    exit 1
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "✅ Virtual environment setup complete!"
echo ""
echo "🚀 To use Dicto:"
echo "   1. Activate the environment: source venv/bin/activate"
echo "   2. Run the app: python dicto_simple.py"
echo "   3. Deactivate when done: deactivate"
echo ""
echo "📝 Note: The threading error suggests accessibility permissions are needed."
echo "   Go to: System Preferences > Security & Privacy > Privacy > Accessibility"
echo "   Add Terminal (or your terminal app) to the list." 