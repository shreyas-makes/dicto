# Building Dicto as a macOS Application

This guide explains how to build Dicto as a standalone macOS `.app` bundle that can be installed and run like any other Mac application.

## Prerequisites

Before building, ensure you have:

- **macOS** (10.14 or later)
- **Python 3.8+** installed
- **Xcode Command Line Tools**: `xcode-select --install`
- **Homebrew** (recommended): `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`

## Step 1: Set Up Whisper.cpp

First, you need to build the Whisper engine and download the AI model:

```bash
# Clone whisper.cpp if not already present
git submodule update --init --recursive

# Navigate to whisper.cpp directory
cd whisper.cpp

# Build with Metal acceleration (for Apple Silicon)
cmake -B build -DWHISPER_METAL=ON
cmake --build build --config Release

# Download the English base model (~140MB)
bash ./models/download-ggml-model.sh base.en

# Return to project root
cd ..
```

**Verify the setup:**
```bash
ls whisper.cpp/build/bin/whisper-cli    # Should exist
ls whisper.cpp/models/ggml-base.en.bin  # Should exist
```

## Step 2: Build the macOS App

We've created an automated build script that handles everything:

```bash
# Make the build script executable (if not already)
chmod +x build_app.sh

# Run the build script
./build_app.sh
```

The script will:
1. ✓ Check system requirements
2. ✓ Create/activate virtual environment
3. ✓ Install Python dependencies
4. ✓ Verify Whisper setup
5. ✓ Build the `.app` bundle using py2app
6. ✓ Package everything into `dist/Dicto.app`

## Step 3: Install the App

After successful build:

```bash
# Test the app first
open dist/Dicto.app

# If it works, install to Applications folder
cp -r dist/Dicto.app /Applications/
```

## Step 4: Grant Permissions

For Dicto to work properly, you need to grant permissions:

### Microphone Access
1. Open **System Preferences** → **Security & Privacy** → **Privacy** → **Microphone**
2. Click the lock to make changes
3. Find and check **Dicto** in the list

### Accessibility Access (for global hotkeys and text insertion)
1. Open **System Preferences** → **Security & Privacy** → **Privacy** → **Accessibility**
2. Click the lock to make changes
3. Click **+** and add **Dicto** from Applications folder

## Manual Build (Alternative)

If you prefer to build manually without the script:

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
pip install py2app

# Build the app
python setup.py py2app

# The app will be in dist/Dicto.app
```

## Troubleshooting

### Build fails with "whisper-cli not found"
- Make sure you built whisper.cpp: `cd whisper.cpp && cmake -B build && cmake --build build`
- Verify the binary exists: `ls whisper.cpp/build/bin/whisper-cli`

### Build fails with "model not found"
- Download the model: `cd whisper.cpp && bash ./models/download-ggml-model.sh base.en`
- Verify it exists: `ls whisper.cpp/models/ggml-base.en.bin`

### App crashes on launch
- Check Console.app for crash logs
- Ensure all permissions are granted (Microphone + Accessibility)
- Try running from Terminal first to see error messages: `./dist/Dicto.app/Contents/MacOS/dicto_main`

### "App is damaged" error
- This happens if the app isn't signed. You can bypass with:
  ```bash
  xattr -cr /Applications/Dicto.app
  ```

### Dependencies missing in built app
- Make sure all Python modules are listed in `setup.py` under `packages` and `includes`
- Rebuild after updating setup.py

## Distribution

### For Personal Use
Just copy `Dicto.app` to any Mac's `/Applications` folder

### For Public Distribution
You'll need to:
1. **Sign the app** with an Apple Developer certificate
2. **Notarize** the app through Apple
3. Create a DMG installer for easy distribution

Example signing command:
```bash
codesign --deep --force --sign "Developer ID Application: Your Name" dist/Dicto.app
```

## App Structure

After building, your app structure looks like:

```
Dicto.app/
├── Contents/
│   ├── Info.plist              # App metadata
│   ├── MacOS/
│   │   └── dicto_main          # Main executable
│   ├── Resources/
│   │   ├── lib/                # Python libraries
│   │   ├── whisper.cpp/        # Whisper binary & models
│   │   └── *.py                # Your Python modules
│   └── Frameworks/             # Python framework
```

## Customization

### Change App Icon
1. Create an `.icns` file (macOS icon format)
2. Update `setup.py`: `'iconfile': 'path/to/icon.icns'`
3. Rebuild

### Use Different Whisper Model
Edit `setup.py` and change the model path in `DATA_FILES`:
```python
DATA_FILES = [
    ('whisper.cpp/models', ['whisper.cpp/models/ggml-large-v3.bin']),
]
```

Then update `dicto_main.py` to use the new model path.

### Customize App Name
Edit `setup.py` and change `APP_NAME` and `CFBundleName`

## File Size

The built app will be approximately:
- Base app: ~50 MB (Python runtime + dependencies)
- Whisper binary: ~5 MB
- Base model: ~140 MB
- **Total: ~200 MB**

Larger models will increase the size:
- `tiny.en`: 39 MB
- `small.en`: 244 MB
- `medium.en`: 769 MB
- `large-v3`: 1.5 GB

## Next Steps

After successful build:
1. ✓ Launch the app from Applications folder
2. ✓ Look for Dicto icon in the menu bar
3. ✓ Test with Ctrl+V hotkey to record
4. ✓ Check that transcriptions work properly

Enjoy your standalone Dicto.app! 🎤
