# Dicto - System-wide Voice Transcription

## Overview
Dicto provides seamless voice-to-text transcription anywhere on macOS using a global hotkey (Cmd+V).

## Features
- **Global Hotkey**: Press Cmd+V anywhere to start/stop recording
- **Automatic Clipboard**: Transcriptions are automatically copied to clipboard
- **Native Notifications**: macOS notifications for status updates
- **Background Operation**: Runs silently in the background
- **Enhanced Error Handling**: User-friendly error messages and recovery

## Installation

### 1. Install Dependencies
```bash
# Install Python dependencies
python setup_dependencies.py

# Or manually:
pip install pynput plyer pyobjc-framework-Cocoa
```

### 2. Grant Microphone Permission
1. Go to **System Preferences > Security & Privacy > Privacy > Microphone**
2. Add your terminal application (Terminal.app, iTerm2, etc.)
3. Ensure the checkbox is checked

### 3. Ensure whisper.cpp is built
```bash
# Should already be built from previous tasks
ls whisper.cpp/build/bin/whisper-cli
ls whisper.cpp/models/ggml-base.en.bin
```

## Usage

### Start the Application
```bash
python dicto_main.py
```

### Basic Workflow
1. **Start Recording**: Press `Cmd+V` anywhere on macOS
   - You'll see a notification: "🔴 Recording Started"
2. **Speak**: Talk into your microphone
3. **Stop & Transcribe**: Press `Cmd+V` again
   - You'll see: "⏹️ Recording Stopped - Processing transcription..."
   - Then: "✅ Transcription Complete - Copied to clipboard"
4. **Paste**: Press `Cmd+V` anywhere to paste the transcribed text

### Command Line Options
```bash
# Basic usage
python dicto_main.py

# Custom whisper binary
python dicto_main.py --whisper-binary /path/to/whisper-cli

# Custom model
python dicto_main.py --model /path/to/model.bin

# Verbose logging
python dicto_main.py --verbose
```

## Background Operation
- Dicto runs in the background and listens for the global hotkey
- You can use any application while Dicto is running
- The transcribed text is immediately available in your clipboard
- Use in any text editor, email, chat application, etc.

## Troubleshooting

### Microphone Permission Issues
- **Error**: "Microphone access denied"
- **Solution**: Grant microphone permission in System Preferences
- **Path**: System Preferences > Security & Privacy > Privacy > Microphone

### Global Hotkey Not Working
- **Error**: Hotkey doesn't trigger recording
- **Solution**: Grant accessibility permission to your terminal 