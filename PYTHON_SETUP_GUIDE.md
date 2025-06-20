# Python Virtual Environment Setup Guide for Dicto

## Why Use Virtual Environments?

✅ **Dependency Isolation**: Prevents conflicts between different projects  
✅ **Reproducible Environment**: Same setup across all machines  
✅ **Clean System Python**: Keeps your system Python installation clean  
✅ **Version Control**: Manage specific package versions per project  
✅ **Easy Sharing**: Others can replicate your exact environment  

## Quick Setup (Recommended)

```bash
# 1. Set up virtual environment (one-time setup)
./setup_venv.sh

# 2. Activate environment (each time you work on the project)
source venv/bin/activate

# 3. Run Dicto
python dicto_simple.py

# 4. Deactivate when done
deactivate
```

## Manual Setup (Alternative)

If you prefer to set up manually:

```bash
# Create virtual environment
python3 -m venv venv

# Activate (macOS/Linux)
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

## Project Dependencies

The project uses these Python packages:
- `pyaudio==0.2.11` - Audio recording and playback
- `pynput==1.7.6` - Global hotkey detection
- `pydub==0.25.1` - Audio processing
- `plyer==2.1.0` - Cross-platform notifications
- `AppKit==0.2.8` - macOS clipboard integration

## Troubleshooting

### Permission Issues
The error "This process is not trusted!" means you need to grant accessibility permissions:

1. **System Preferences** → **Security & Privacy** → **Privacy** → **Accessibility**
2. Click the **lock** to make changes
3. Add your **Terminal** app (or whatever terminal you're using)
4. Restart the application

### Audio Issues
If you get audio recording errors:
```bash
# Install SoX for audio recording (if not already installed)
brew install sox
```

### Python Version
Ensure you're using Python 3.7+:
```bash
python3 --version
```

## Best Practices

### Daily Workflow
```bash
# When starting work
cd /path/to/dicto
source venv/bin/activate

# Your work here...
python dicto_simple.py

# When finishing
deactivate
```

### Environment Management
- **Never** install project dependencies globally with `pip install`
- **Always** activate the virtual environment before working
- **Keep** `requirements.txt` updated when adding new dependencies
- **Don't** commit the `venv/` folder to git (it's in `.gitignore`)

### Adding New Dependencies
```bash
# Activate environment first
source venv/bin/activate

# Install new package
pip install package_name

# Update requirements.txt
pip freeze > requirements.txt
```

## IDE Setup

### VS Code
Add to your VS Code settings for this project:
```json
{
    "python.interpreter": "./venv/bin/python"
}
```

### PyCharm
- File → Settings → Project → Python Interpreter
- Add → Existing Environment → `./venv/bin/python`

## Convenience Scripts

- `./setup_venv.sh` - One-time setup of virtual environment
- `./activate_dicto.sh` - Quick activation helper (though `source venv/bin/activate` is standard)

## Common Commands

```bash
# Check if virtual env is active (should show path to venv)
which python

# List installed packages
pip list

# Check package info
pip show package_name

# Update a package
pip install --upgrade package_name

# Uninstall a package
pip uninstall package_name
```

---

💡 **Remember**: Virtual environments are a Python best practice, not just for this project but for **all** Python development! 