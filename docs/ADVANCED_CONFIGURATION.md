# ⚙️ Dicto Advanced Configuration Manual

**Power User Guide for Optimal Performance and Customization**

Version 1.0 | Updated: December 2024

---

## Table of Contents

1. [Configuration Architecture](#configuration-architecture)
2. [Performance Tuning](#performance-tuning)
3. [Audio Pipeline Optimization](#audio-pipeline-optimization)
4. [Model Management](#model-management)
5. [Hotkey System](#hotkey-system)
6. [Security & Privacy](#security--privacy)
7. [Developer API](#developer-api)
8. [Command Line Interface](#command-line-interface)

---

## Configuration Architecture

### Configuration Hierarchy

Dicto uses a layered configuration system:

```
1. System Defaults (built-in)
2. Global Config (~/.dicto/config.json)
3. User Config (~/Library/Application Support/Dicto/config.json)
4. Runtime Overrides (command line arguments)
```

### Configuration File Structure

```json
{
  "version": "1.0",
  "app": {
    "auto_start": false,
    "check_updates": true,
    "telemetry_enabled": false,
    "log_level": "INFO"
  },
  "audio": {
    "input_device": "default",
    "sample_rate": 16000,
    "channels": 1,
    "chunk_size": 1024,
    "buffer_duration": 0.5,
    "noise_reduction": {
      "enabled": true,
      "level": 0.5,
      "gate_threshold": -30
    },
    "voice_activation": {
      "enabled": true,
      "threshold": -40,
      "pre_record": 0.5,
      "post_record": 1.0
    }
  },
  "transcription": {
    "model": "base.en",
    "model_path": "auto",
    "language": "en",
    "confidence_threshold": 0.6,
    "max_segment_length": 30,
    "beam_size": 5,
    "best_of": 1,
    "temperature": 0.0,
    "compression_ratio_threshold": 2.4,
    "logprob_threshold": -1.0,
    "no_speech_threshold": 0.6
  },
  "hotkeys": {
    "record_toggle": ["cmd", "v"],
    "paste_last": ["cmd", "shift", "v"],
    "show_history": ["cmd", "option", "v"],
    "preferences": ["cmd", ","],
    "emergency_stop": ["cmd", "shift", "escape"]
  },
  "interface": {
    "menu_bar_icon": true,
    "notifications": true,
    "notification_duration": 3,
    "status_animations": true,
    "click_through": false
  },
  "performance": {
    "max_memory_mb": 2048,
    "cpu_limit_percent": 80,
    "gpu_acceleration": true,
    "background_priority": "normal",
    "cache_models": true,
    "preload_model": false
  },
  "privacy": {
    "store_recordings": false,
    "store_transcriptions": true,
    "max_history_days": 30,
    "encrypt_history": true,
    "auto_cleanup": true
  }
}
```

### Environment Variables

Override configuration via environment variables:

```bash
export DICTO_LOG_LEVEL=DEBUG
export DICTO_MODEL_PATH=/custom/path/to/models
export DICTO_CONFIG_PATH=/custom/config.json
export DICTO_CACHE_DIR=/custom/cache
export DICTO_DISABLE_GPU=1
export DICTO_MAX_MEMORY=1024
```

---

## Performance Tuning

### Hardware-Specific Optimization

#### Apple Silicon (M1/M2/M3)
```json
{
  "performance": {
    "gpu_acceleration": true,
    "metal_backend": true,
    "neural_engine": true,
    "unified_memory_optimization": true,
    "background_priority": "high"
  },
  "transcription": {
    "model": "base.en",
    "beam_size": 5,
    "best_of": 1
  }
}
```

#### Intel Macs
```json
{
  "performance": {
    "gpu_acceleration": false,
    "cpu_threads": "auto",
    "avx_optimization": true,
    "background_priority": "normal"
  },
  "transcription": {
    "model": "tiny.en",
    "beam_size": 1,
    "best_of": 1
  }
}
```

### Memory Optimization

#### Low Memory Systems (8GB or less)
```json
{
  "performance": {
    "max_memory_mb": 1024,
    "cache_models": false,
    "preload_model": false,
    "aggressive_cleanup": true
  },
  "transcription": {
    "model": "tiny.en",
    "max_segment_length": 15
  },
  "audio": {
    "buffer_duration": 0.25,
    "chunk_size": 512
  }
}
```

#### High Memory Systems (16GB+)
```json
{
  "performance": {
    "max_memory_mb": 4096,
    "cache_models": true,
    "preload_model": true,
    "model_cache_size": 3
  },
  "transcription": {
    "model": "medium.en",
    "beam_size": 5,
    "best_of": 3
  }
}
```

### CPU Optimization

```json
{
  "performance": {
    "cpu_threads": 4,
    "cpu_limit_percent": 80,
    "process_priority": "normal",
    "affinity_mask": "auto",
    "simd_optimization": true
  }
}
```

### Battery Optimization

```json
{
  "performance": {
    "battery_mode": {
      "enabled": true,
      "model": "tiny.en",
      "reduce_accuracy": true,
      "sleep_when_idle": true,
      "background_priority": "low"
    }
  }
}
```

---

## Audio Pipeline Optimization

### Device Configuration

List available audio devices:
```bash
python -c "import audio_processor; ap = audio_processor.AudioProcessor(); print(ap.list_audio_devices())"
```

Configure specific device:
```json
{
  "audio": {
    "input_device": "USB Audio Device",
    "input_device_id": 2,
    "exclusive_mode": false,
    "low_latency": true
  }
}
```

### Sample Rate Optimization

| Sample Rate | Use Case | Quality | Performance |
|-------------|----------|---------|-------------|
| 8000 Hz | Voice calls | Low | Fastest |
| 16000 Hz | Speech transcription | Good | Fast ⭐ |
| 22050 Hz | Podcasts | Better | Moderate |
| 44100 Hz | Music/high quality | Best | Slow |

### Audio Enhancement Pipeline

```json
{
  "audio": {
    "enhancement_pipeline": [
      {
        "type": "noise_gate",
        "threshold": -40,
        "attack": 0.01,
        "release": 0.1
      },
      {
        "type": "noise_reduction",
        "algorithm": "spectral_subtraction",
        "strength": 0.5
      },
      {
        "type": "compressor",
        "ratio": 3.0,
        "threshold": -20,
        "attack": 0.003,
        "release": 0.1
      },
      {
        "type": "equalizer",
        "high_pass": 80,
        "low_pass": 8000,
        "vocal_boost": 3
      }
    ]
  }
}
```

### Voice Activity Detection

```json
{
  "audio": {
    "vad": {
      "enabled": true,
      "algorithm": "energy_based",
      "threshold": -35,
      "min_speech_duration": 0.25,
      "min_silence_duration": 0.5,
      "pre_speech_buffer": 0.25,
      "post_speech_buffer": 0.5
    }
  }
}
```

---

## Model Management

### Available Models

| Model | Size | Speed | Accuracy | Memory | Use Case |
|-------|------|-------|----------|---------|----------|
| tiny.en | 39MB | Fastest | Basic | 1GB | Quick notes |
| base.en | 147MB | Fast | Good | 1GB | General use ⭐ |
| small.en | 244MB | Medium | Better | 2GB | Professional |
| medium.en | 769MB | Slow | High | 5GB | High accuracy |
| large-v3 | 1550MB | Slowest | Best | 10GB | Maximum quality |

### Custom Model Configuration

```json
{
  "models": {
    "custom_base": {
      "path": "/path/to/custom-model.bin",
      "type": "whisper",
      "language": "en",
      "vocab_size": 51864,
      "context_length": 448
    }
  }
}
```

### Model Download & Management

```bash
# Download specific model
python -m dicto.models download base.en

# List available models
python -m dicto.models list

# Verify model integrity
python -m dicto.models verify base.en

# Remove unused models
python -m dicto.models cleanup
```

### Fine-tuning Configuration

```json
{
  "transcription": {
    "fine_tuning": {
      "vocabulary_boost": {
        "enabled": true,
        "boost_factor": 1.5,
        "custom_words": ["kubernetes", "postgresql", "api"]
      },
      "context_priming": {
        "enabled": true,
        "context_window": 30,
        "domain_adaptation": "technology"
      }
    }
  }
}
```

---

## Hotkey System

### Advanced Hotkey Configuration

```json
{
  "hotkeys": {
    "global_hotkeys": {
      "record_toggle": {
        "keys": ["cmd", "v"],
        "mode": "toggle",
        "repeat_delay": 0.5,
        "conflict_resolution": "prefer_dicto"
      },
      "continuous_record": {
        "keys": ["cmd", "shift", "v"],
        "mode": "hold",
        "max_duration": 300
      }
    },
    "contextual_hotkeys": {
      "text_editors": {
        "enabled": true,
        "apps": ["com.microsoft.VSCode", "com.apple.TextEdit"],
        "hotkeys": {
          "voice_comment": ["cmd", "option", "c"]
        }
      }
    }
  }
}
```

### Conflict Detection

```json
{
  "hotkeys": {
    "conflict_detection": {
      "enabled": true,
      "scan_interval": 30,
      "resolution_strategy": "ask_user",
      "excluded_apps": ["com.apple.Terminal"]
    }
  }
}
```

### Application-Specific Hotkeys

```json
{
  "hotkeys": {
    "app_specific": {
      "com.microsoft.VSCode": {
        "voice_docstring": ["cmd", "option", "d"],
        "voice_comment": ["cmd", "option", "c"]
      },
      "com.apple.mail": {
        "voice_reply": ["cmd", "option", "r"]
      }
    }
  }
}
```

---

## Security & Privacy

### Data Encryption

```json
{
  "security": {
    "encryption": {
      "algorithm": "AES-256-GCM",
      "key_derivation": "PBKDF2",
      "iterations": 100000,
      "salt_size": 16
    },
    "storage": {
      "encrypt_transcriptions": true,
      "encrypt_audio_cache": false,
      "secure_delete": true
    }
  }
}
```

### Access Control

```json
{
  "security": {
    "access_control": {
      "require_authentication": false,
      "allowed_apps": ["*"],
      "blocked_apps": ["com.example.untrusted"],
      "api_key_required": false
    }
  }
}
```

### Audit Logging

```json
{
  "security": {
    "audit": {
      "enabled": true,
      "log_level": "INFO",
      "log_file": "~/Library/Logs/Dicto/audit.log",
      "rotate_size": "10MB",
      "retention_days": 30,
      "events": ["transcription", "config_change", "model_load"]
    }
  }
}
```

---

## Developer API

### Python API

```python
from dicto import DictoAPI

# Initialize API
api = DictoAPI(config_path="/path/to/config.json")

# Transcribe audio file
result = api.transcribe_file("audio.wav")
print(result.text)

# Real-time transcription
def on_transcription(text):
    print(f"Transcribed: {text}")

api.start_real_time_transcription(callback=on_transcription)

# Custom vocabulary
api.add_vocabulary(["kubernetes", "postgresql", "fastapi"])

# Get transcription history
history = api.get_history(limit=10)
```

### REST API

Enable REST API in configuration:
```json
{
  "api": {
    "rest": {
      "enabled": true,
      "host": "127.0.0.1",
      "port": 8080,
      "auth_required": false,
      "cors_enabled": true
    }
  }
}
```

API Endpoints:
```bash
# Transcribe audio file
curl -X POST \
  -F "audio=@audio.wav" \
  http://localhost:8080/api/v1/transcribe

# Get transcription status
curl http://localhost:8080/api/v1/status

# Add vocabulary
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"words": ["kubernetes", "docker"]}' \
  http://localhost:8080/api/v1/vocabulary

# Get history
curl http://localhost:8080/api/v1/history?limit=10
```

### WebSocket API

```javascript
const ws = new WebSocket('ws://localhost:8080/api/v1/stream');

ws.onopen = function() {
    console.log('Connected to Dicto WebSocket');
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    if (data.type === 'transcription') {
        console.log('Transcription:', data.text);
    }
};

// Send audio data
const audioBlob = new Blob([audioData], {type: 'audio/wav'});
ws.send(audioBlob);
```

---

## Command Line Interface

### Basic Usage

```bash
# Start Dicto
dicto start

# Stop Dicto
dicto stop

# Get status
dicto status

# Run diagnostics
dicto diagnose

# Show configuration
dicto config show
```

### Advanced Commands

```bash
# Transcribe file with custom model
dicto transcribe --model large-v3 --input audio.wav --output transcript.txt

# Performance benchmark
dicto benchmark --model base.en --duration 60

# Model management
dicto model download base.en
dicto model list
dicto model verify base.en

# Configuration management
dicto config set transcription.model small.en
dicto config get audio.sample_rate
dicto config reset

# Export settings
dicto export --output dicto-config.json --include-history

# Import settings
dicto import --input dicto-config.json --overwrite
```

### Scripting Examples

```bash
#!/bin/bash
# Batch transcription script

for audio_file in *.wav; do
    echo "Transcribing $audio_file..."
    dicto transcribe \
        --input "$audio_file" \
        --output "${audio_file%.wav}.txt" \
        --model base.en \
        --confidence 0.8
done
```

### Environment Configuration

```bash
# Development environment
export DICTO_ENV=development
export DICTO_LOG_LEVEL=DEBUG
export DICTO_CONFIG_PATH=./dev-config.json

# Production environment
export DICTO_ENV=production
export DICTO_LOG_LEVEL=INFO
export DICTO_TELEMETRY_ENABLED=false
```

---

## Troubleshooting Advanced Issues

### Performance Debugging

```bash
# Enable performance profiling
dicto start --profile --profile-output profile.json

# Memory usage analysis
dicto diagnose --memory --output memory-report.json

# CPU usage analysis
dicto diagnose --cpu --duration 60
```

### Audio Pipeline Debugging

```bash
# Test audio input
dicto audio test-input --device "USB Microphone"

# Audio latency test
dicto audio test-latency --input-device 1 --buffer-size 512

# Voice activity detection test
dicto audio test-vad --threshold -35 --duration 30
```

### Model Debugging

```bash
# Model performance test
dicto model benchmark --model base.en --test-audio test.wav

# Model accuracy test
dicto model accuracy --model base.en --reference reference.txt --audio test.wav

# Model memory usage
dicto model memory-usage --model large-v3
```

---

## Configuration Examples

### Podcast Transcription Setup
```json
{
  "audio": {
    "sample_rate": 22050,
    "noise_reduction": {"enabled": true, "level": 0.7},
    "vad": {"enabled": false}
  },
  "transcription": {
    "model": "medium.en",
    "max_segment_length": 60,
    "beam_size": 5
  }
}
```

### Meeting Transcription Setup
```json
{
  "audio": {
    "sample_rate": 16000,
    "noise_reduction": {"enabled": true, "level": 0.5},
    "vad": {"enabled": true, "threshold": -30}
  },
  "transcription": {
    "model": "base.en",
    "confidence_threshold": 0.7,
    "max_segment_length": 30
  },
  "interface": {
    "notifications": false,
    "status_animations": false
  }
}
```

### Voice Coding Setup
```json
{
  "hotkeys": {
    "voice_comment": ["cmd", "option", "c"],
    "voice_docstring": ["cmd", "option", "d"]
  },
  "transcription": {
    "model": "small.en",
    "custom_vocabulary": ["function", "variable", "array", "object"]
  }
}
```

---

*For additional advanced configuration options and technical support, contact the development team at dev@dicto.app*

---

© 2024 Dicto Development Team. All rights reserved. 