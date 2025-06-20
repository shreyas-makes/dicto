# 🎤 Dicto - AI Transcription App

A simple, offline AI transcription app for macOS that uses OpenAI's Whisper (via whisper.cpp) with global hotkey support.

## ✨ Features

- **🔥 Completely Offline**: No internet required, everything runs locally
- **⚡ Fast & Efficient**: Uses optimized whisper.cpp with Metal acceleration
- **🎯 Global Hotkeys**: Press `Cmd+V` from anywhere to start/stop recording
- **📋 Auto-Clipboard**: Transcriptions are automatically copied to clipboard
- **🔊 Real-time Feedback**: macOS notifications keep you informed
- **🛡️ Privacy-First**: Your audio never leaves your machine

## 🚀 Quick Start

### Prerequisites

- macOS (tested on macOS 14+)
- Python 3.8+
- Xcode Command Line Tools
- Homebrew (recommended)

### Installation

1. **Clone and Setup**:
   ```bash
   git clone <your-repo>
   cd dicto
   chmod +x setup.sh
   ./setup.sh
   ```

2. **Grant Permissions** (Important!):
   - **Microphone**: Go to System Preferences → Security & Privacy → Privacy → Microphone
   - **Accessibility**: Go to System Preferences → Security & Privacy → Privacy → Accessibility
   - Add Terminal or your Python interpreter to both lists

3. **Run the App**:
   ```bash
   python3 dicto_app.py
   ```

## 🎮 Usage

1. **Start the app**: `python3 dicto_app.py`
2. **Record**: Press `Cmd+V` to start recording (you'll see a notification)
3. **Stop & Transcribe**: Press `Cmd+V` again to stop and transcribe
4. **Get Results**: Transcription is automatically copied to your clipboard
5. **Paste Anywhere**: Use `Cmd+V` in any app to paste the transcription
6. **Quit**: Press `Cmd+Q` to exit the app

## 🔧 Technical Details

### Audio Settings
- **Sample Rate**: 16kHz (optimal for Whisper)
- **Channels**: Mono
- **Format**: 16-bit PCM

### Whisper Model
- **Default**: base.en (English only, ~140MB)
- **Performance**: ~2-3x faster than base multilingual
- **Accuracy**: Good balance of speed and quality

### Performance
- **Transcription Speed**: ~0.5-2 seconds for 10-second audio clips
- **Memory Usage**: ~200MB base + audio buffer
- **CPU**: Utilizes Apple Silicon Metal acceleration

## 🛠️ Customization

### Change Hotkey

Edit `dicto_app.py` and modify the hotkey mapping:

```python
with keyboard.GlobalHotKeys({
    '<cmd>+shift+v': self.on_hotkey_triggered,  # Changed from <cmd>+v
    '<cmd>+q': self.on_quit_triggered
}):
```

### Use Different Whisper Model

Download a different model and update the path:

```bash
# Download larger model for better accuracy
cd whisper.cpp
bash ./models/download-ggml-model.sh large-v3

# Update model path in dicto_app.py
self.model_path = Path("whisper.cpp/models/ggml-large-v3.bin")
```

Available models:
- `tiny.en` (39 MB) - Fastest, lowest accuracy
- `base.en` (147 MB) - Good balance (default)
- `small.en` (244 MB) - Better accuracy
- `medium.en` (769 MB) - High accuracy
- `large-v3` (1550 MB) - Best accuracy, multilingual

### Audio Quality Settings

Modify audio settings in `dicto_app.py`:

```python
# Higher quality (more CPU intensive)
self.rate = 44100  # Instead of 16000
self.channels = 2  # Stereo instead of mono
```

## 🐛 Troubleshooting

### "No module named 'pyaudio'"
```bash
# Install PortAudio first
brew install portaudio
pip3 install pyaudio
```

### "Permission denied" for microphone
1. Go to System Preferences → Security & Privacy → Privacy → Microphone
2. Add Terminal or Python to the list
3. Restart the app

### Hotkeys not working
1. Go to System Preferences → Security & Privacy → Privacy → Accessibility
2. Add Terminal or Python to the list
3. Restart the app

### "Whisper CLI not found"
Make sure you're running from the project directory where `whisper.cpp/` exists.

### Slow transcription
- Try a smaller model (`tiny.en` or `base.en`)
- Ensure Metal acceleration is working (check console output)
- Close other resource-intensive apps

## 🔒 Privacy & Security

- **No Network Requests**: All processing happens locally
- **Temporary Files**: Audio files are automatically deleted after processing
- **No Data Collection**: We don't collect any usage data or audio
- **Open Source**: Full source code available for inspection

## 📦 Project Structure

```
dicto/
├── dicto_app.py          # Main application
├── requirements.txt      # Python dependencies
├── setup.sh             # Setup script
├── README.md            # This file
└── whisper.cpp/         # Whisper.cpp submodule
    ├── build/bin/        # Compiled binaries
    └── models/           # Whisper models
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly on macOS
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License. See the whisper.cpp repository for their licensing terms.

## 🙏 Acknowledgments

- [whisper.cpp](https://github.com/ggml-org/whisper.cpp) - Fast Whisper inference
- [OpenAI Whisper](https://github.com/openai/whisper) - Original Whisper model
- [PyAudio](https://people.csail.mit.edu/hubert/pyaudio/) - Audio recording
- [pynput](https://github.com/moses-palmer/pynput) - Global hotkeys

---

**Note**: This app is designed specifically for macOS. For other platforms, you'll need to modify the clipboard and notification code. 