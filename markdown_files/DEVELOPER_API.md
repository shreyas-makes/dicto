# 👨‍💻 Dicto Developer API

**API Reference for integrating with Dicto**

---

## Python API

### Basic Usage

```python
from dicto_core import TranscriptionEngine

# Initialize
engine = TranscriptionEngine()

# Transcribe file
result = engine.transcribe_file("audio.wav")
print(result)

# Real-time transcription
engine.start_recording()
# ... speak ...
result = engine.stop_recording()
print(result)
```

### Core Classes

#### TranscriptionEngine
```python
class TranscriptionEngine:
    def transcribe_file(self, file_path: str) -> str
    def start_recording(self) -> bool
    def stop_recording(self) -> str
```

#### AudioRecorder
```python
class AudioRecorder:
    def start_recording(self, device_id: int = None) -> bool
    def stop_recording(self) -> str  # Returns file path
    def is_recording(self) -> bool
```

#### VocabularyManager
```python
class VocabularyManager:
    def add_words(self, words: List[str]) -> None
    def remove_words(self, words: List[str]) -> None
    def get_vocabulary(self) -> List[str]
```

---

## Configuration API

### Config Management

```python
from config_manager import ConfigManager

config = ConfigManager()

# Get settings
model = config.get("transcription.model")
hotkey = config.get("hotkeys.record_toggle")

# Update settings
config.set("transcription.model", "base.en")
config.save()
```

---

## Plugin Development

### Creating a Plugin

```python
class MyPlugin:
    def on_transcription_complete(self, text: str) -> str:
        # Post-process transcription
        return text.upper()
    
    def on_recording_start(self):
        print("Recording started")
```

### Plugin Registration

```python
from dicto_main import DictoApp

app = DictoApp()
app.register_plugin(MyPlugin())
```

---

## Integration Examples

### Simple CLI Tool

```python
#!/usr/bin/env python3
import sys
from dicto_core import TranscriptionEngine

def main():
    if len(sys.argv) != 2:
        print("Usage: transcribe.py <audio_file>")
        return
    
    engine = TranscriptionEngine()
    result = engine.transcribe_file(sys.argv[1])
    print(result)

if __name__ == "__main__":
    main()
```

### GUI Integration

```python
import tkinter as tk
from dicto_core import TranscriptionEngine

class TranscriptionGUI:
    def __init__(self):
        self.engine = TranscriptionEngine()
        self.root = tk.Tk()
        
        # Record button
        tk.Button(self.root, text="Record", 
                 command=self.toggle_recording).pack()
        
        # Text display
        self.text = tk.Text(self.root)
        self.text.pack()
    
    def toggle_recording(self):
        if not self.engine.is_recording():
            self.engine.start_recording()
        else:
            result = self.engine.stop_recording()
            self.text.insert(tk.END, result + "\n")

gui = TranscriptionGUI()
gui.root.mainloop()
```

---

## Error Handling

### Common Exceptions

```python
from dicto_core import TranscriptionEngine, TranscriptionError

try:
    engine = TranscriptionEngine()
    result = engine.transcribe_file("audio.wav")
except TranscriptionError as e:
    print(f"Transcription failed: {e}")
except FileNotFoundError:
    print("Audio file not found")
```

---

## Support

- **Issues**: GitHub repository issues
- **Email**: dev@dicto.app
- **Documentation**: Full docs at dicto.app/api

---

© 2024 Dicto Development Team 