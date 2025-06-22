# Dicto CTRL+V Usage Guide

## 🎯 Overview

Dicto provides **system-wide voice transcription** triggered by the **CTRL+V** key combination. Press and hold CTRL+V anywhere on your Mac to start recording, then release to stop and get instant transcription **automatically inserted** into the text field where you pressed CTRL+V.

## 🚀 Quick Start

1. **Setup**: Run `./setup_dicto_complete.sh` to install all dependencies
2. **Launch**: Run `./launch_dicto_easy.sh` or `./activate_dicto.sh`
3. **Grant Permissions**: Add Terminal to Accessibility permissions in System Preferences
4. **Use**: Press and hold CTRL+V anywhere to record voice → Release to get text automatically inserted

## 🔥 Key Features

### ✨ System-Wide Recording
- **Works anywhere**: Any text field, any app, any input area
- **Global hotkey**: CTRL+V works even when Dicto is in the background
- **Instant activation**: No need to switch to Dicto app

### 🎙️ Continuous Recording
- **Hold to record**: Press and hold CTRL+V to start continuous recording
- **Release to stop**: Let go of CTRL+V to stop and process transcription
- **Chunked recording**: Long sessions are automatically split into manageable chunks
- **Auto-save**: Sessions are automatically saved during long recordings

### 📋 Automatic Text Insertion
- **Instant insertion**: Transcription is automatically typed into the text field where you pressed CTRL+V
- **No manual pasting**: Text appears automatically in the correct location
- **Seamless workflow**: No need to press CMD+V or manage clipboard

### 🧠 Enhanced Accuracy
- **Custom vocabulary**: Add domain-specific terms for better accuracy
- **Proper noun support**: Better recognition of names and technical terms
- **Context-aware**: Vocabulary suggestions based on recording context

## 🔧 Setup Instructions

### 1. Initial Setup

```bash
# Clone or download Dicto project
cd /path/to/dicto

# Run complete setup (installs everything)
./setup_dicto_complete.sh

# Alternative: Manual setup
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Grant Accessibility Permissions

**CRITICAL**: Dicto needs accessibility permissions to detect global CTRL+V hotkeys.

1. Open **System Preferences** → **Privacy & Security** → **Accessibility**
2. Click the **lock icon** and enter your password
3. Click **+** and add your **Terminal app** (or iTerm, etc.)
4. **Enable** the checkbox for your terminal
5. Restart Terminal and relaunch Dicto

### 3. Launch Dicto

```bash
# Easy launch (recommended)
./launch_dicto_easy.sh

# Alternative methods
./activate_dicto.sh
# or
source venv/bin/activate && python3 dicto_main.py
```

## 💡 Usage Examples

### Basic Recording
```
1. Open any text editor (TextEdit, Notes, web browser, etc.)
2. Click in a text field where you want the text to appear
3. Press and HOLD CTRL+V
4. Speak: "Hello, this is a test of voice transcription"
5. Release CTRL+V
6. The transcribed text automatically appears in the text field!
```

### Email Composition
```
1. Open Mail app or Gmail in browser
2. Click in email body where you want the text
3. Press and HOLD CTRL+V
4. Speak your email content
5. Release CTRL+V
6. The transcribed email automatically appears in the email body!
```

### Coding Comments
```
1. Open your IDE (VS Code, Xcode, etc.)
2. Place cursor where you want a comment
3. Type: "// " (comment prefix)
4. Press and HOLD CTRL+V
5. Speak: "This function calculates the user's total score"
6. Release CTRL+V and the comment automatically appears!
```

### Long-Form Content
```
1. Open your document editor and place cursor where you want the text
2. Press and HOLD CTRL+V for extended recording
3. Speak naturally - pauses are okay
4. For very long content (>30 seconds), Dicto will auto-chunk
5. Release CTRL+V when finished
6. The entire transcription automatically appears in your document!
```

## ⚙️ Configuration

### Custom Vocabulary

Add domain-specific terms for better accuracy:

```python
# Create vocabulary file: ~/.dicto/vocabulary/custom_vocabulary.json
{
    "words": ["API", "database", "authentication", "middleware"],
    "proper_nouns": ["PostgreSQL", "React", "JavaScript", "GitHub"],
    "domains": {
        "programming": ["function", "variable", "class", "method"],
        "medical": ["patient", "diagnosis", "treatment", "medication"]
    }
}
```

### Recording Settings

Modify settings in `dicto_main.py`:

```python
# Chunk duration for long recordings (seconds)
chunk_duration = 30.0

# Maximum session duration (seconds)  
max_session_duration = 3600.0  # 1 hour

# Auto-save interval (seconds)
auto_save_interval = 300.0  # 5 minutes
```

## 🔍 Testing

### Test CTRL+V Detection

```bash
# Activate environment
source venv/bin/activate

# Run test script
python3 test_ctrl_v.py

# Choose test option:
# 1. Test macOS Key Detector (recommended)
# 2. Test pynput Key Detector (fallback)  
# 3. Test Continuous Recorder
```

### Test Audio Recording

```bash
# Test basic audio recording
python3 test_recording.py

# Test vocabulary features  
python3 test_vocabulary.py
```

## ❗ Troubleshooting

### CTRL+V Not Detected

1. **Check accessibility permissions**: System Preferences → Privacy & Security → Accessibility
2. **Restart Terminal** after granting permissions
3. **Try fallback detection**: Test with `python3 test_ctrl_v.py`
4. **Check dependencies**: Run setup script again

### No Audio Recording

1. **Check microphone permissions**: System Preferences → Privacy & Security → Microphone
2. **Test audio device**: Run `python3 test_recording.py`
3. **Check audio dependencies**: Ensure pyaudio and sounddevice are installed

### Transcription Issues

1. **Check Whisper setup**: Ensure `whisper.cpp/main` binary exists
2. **Check model file**: Ensure `whisper.cpp/models/ggml-base.en.bin` exists
3. **Test transcription**: Run `python3 test_transcription.py`

### Permission Errors

```bash
# If you get permission errors, check:
ls -la whisper.cpp/main  # Should be executable
chmod +x whisper.cpp/main  # Make executable if needed

# Check audio device access
python3 -c "import sounddevice; print(sounddevice.query_devices())"
```

## 🎯 Performance Tips

### For Best Accuracy
- **Speak clearly** and at moderate pace
- **Reduce background noise** when possible
- **Add custom vocabulary** for specialized terms
- **Use shorter recordings** (< 30 seconds) for faster processing

### For Long Recordings
- **Keep CTRL+V held** for continuous recording
- **Speak naturally** - pauses are handled automatically
- **Trust auto-chunking** for sessions > 30 seconds
- **Wait for processing** after releasing CTRL+V

### For Technical Content
- **Add technical terms** to custom vocabulary
- **Spell out abbreviations** initially ("A P I" instead of "API")
- **Use consistent terminology** for better learning

## 🔄 Workflow Integration

### With IDEs
```bash
# VS Code integration
1. Install "Paste and Indent" extension
2. Use CTRL+V for voice → CMD+Shift+V for formatted paste

# Xcode integration  
1. Use CTRL+V for voice comments
2. Press CMD+V to paste transcribed comments
```

### With Note-Taking
```bash
# Obsidian/Notion integration
1. Use CTRL+V for voice notes
2. Combine with markdown shortcuts
3. Press CMD+V to paste formatted text
```

### With Communication
```bash
# Slack/Teams integration
1. Click in message field
2. Use CTRL+V for voice messages
3. Text automatically appears in the message field
4. Edit if needed, then send
```

## 📊 System Requirements

- **macOS**: 10.15 (Catalina) or later
- **Python**: 3.8 or higher
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 2GB free space for models and recordings
- **Microphone**: Built-in or external microphone

## 🔗 Additional Resources

- **Main Documentation**: `README.md`
- **Setup Guide**: `FINAL_SETUP.md`  
- **Development Log**: `docs/DEVELOPMENT_LOG.md`
- **Project Summary**: `docs/PROJECT_SUMMARY.md`

---

## 🎉 Happy Voice Transcribing!

With Dicto's CTRL+V functionality, you can now use your voice to input text anywhere on your Mac with **zero extra steps**. From coding comments to email composition, from note-taking to document writing - just press CTRL+V, speak, and watch the text automatically appear exactly where you need it! 