# 🎤 Dicto User Guide

**Professional AI Transcription for macOS**

Version 1.0 | Updated: December 2024

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Basic Usage](#basic-usage)
3. [Advanced Features](#advanced-features)
4. [Configuration](#configuration)
5. [Troubleshooting](#troubleshooting)
6. [Tips & Best Practices](#tips--best-practices)

---

## Getting Started

### System Requirements

- **Operating System**: macOS 10.15 (Catalina) or later
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 2GB free space
- **Microphone**: Built-in or external microphone
- **Permissions**: Microphone and Accessibility access

### Installation

#### Method 1: DMG Installer (Recommended)
1. Download `Dicto-1.0.dmg` from the official website
2. Double-click the DMG file to mount it
3. Drag `Dicto.app` to the Applications folder
4. Launch Dicto from Applications or Spotlight

#### Method 2: Package Installer
1. Download `Dicto-1.0.pkg`
2. Double-click to run the installer
3. Follow the installation wizard
4. Launch Dicto from Applications

### First Launch Setup

When you first launch Dicto, you'll need to grant essential permissions:

#### 1. Microphone Permission
- macOS will prompt for microphone access
- Click **"Allow"** to enable audio recording
- If you miss the prompt: System Preferences → Security & Privacy → Privacy → Microphone → Add Dicto

#### 2. Accessibility Permission
- Required for global hotkeys to work system-wide
- Go to: System Preferences → Security & Privacy → Privacy → Accessibility
- Click the lock icon and enter your password
- Click **"+"** and add Dicto.app
- Ensure the checkbox next to Dicto is checked

#### 3. Initial Configuration
- Dicto will appear in your menu bar as a microphone icon
- Click the icon to access the preferences
- Test your setup with a quick recording

---

## Basic Usage

### Quick Start: Your First Transcription

1. **Start Recording**: Press `Cmd+V` anywhere on your Mac
   - You'll see a notification: "🎤 Recording started..."
   - The menu bar icon will show a red recording indicator

2. **Speak Clearly**: Talk normally into your microphone
   - Speak at a moderate pace for best accuracy
   - Avoid background noise when possible

3. **Stop Recording**: Press `Cmd+V` again
   - You'll see: "⏹️ Recording stopped. Processing..."
   - Wait for the transcription to complete

4. **Get Your Text**: The transcription automatically copies to your clipboard
   - Paste anywhere with `Cmd+V`
   - Access recent transcriptions via the menu bar

### The Dicto Workflow

```
Press Cmd+V → Speak → Press Cmd+V → Text copied → Paste anywhere
```

This seamless workflow works in any application:
- **Writing**: Dictate directly into documents, emails, messages
- **Note-taking**: Quick voice notes that become searchable text
- **Coding**: Dictate comments and documentation
- **Research**: Transcribe interviews, meetings, or lectures

---

## Advanced Features

### Menu Bar Controls

Click the Dicto icon in your menu bar to access:

#### Quick Actions
- **🎤 Start Recording**: Begin a new transcription
- **⏹️ Stop Recording**: End current recording
- **📋 Paste Last**: Insert the most recent transcription
- **🔄 Retry Last**: Re-process the last recording

#### Transcription History
- **📝 Recent Transcriptions**: View and reuse past transcriptions
- **🔍 Search History**: Find specific transcriptions by content
- **📊 Statistics**: View usage stats and accuracy metrics
- **🗑️ Clear History**: Remove old transcriptions

#### Settings
- **⚙️ Preferences**: Open the full preferences window
- **🎵 Audio Settings**: Configure microphone and audio quality
- **⌨️ Hotkeys**: Customize keyboard shortcuts
- **🔧 Advanced**: Model selection and performance options

### Custom Hotkeys

Default hotkeys can be customized in Preferences:

- **Recording Toggle**: `Cmd+V` (customizable)
- **Paste Last**: `Cmd+Shift+V`
- **Show History**: `Cmd+Option+V`
- **Open Preferences**: `Cmd+,`

### Continuous Recording Mode

For longer transcriptions:

1. **Enable Continuous Mode**: Hold `Cmd+V` down
2. **Keep Speaking**: Dicto will record while the key is held
3. **Release to Stop**: Let go of `Cmd+V` to end recording
4. **Auto-Processing**: Transcription begins immediately

### Custom Vocabulary

Improve accuracy for specialized terms:

1. **Open Preferences** → **Vocabulary** tab
2. **Add Custom Words**: Enter technical terms, names, acronyms
3. **Import Lists**: Load vocabulary from text files
4. **Context-Aware**: Dicto learns from your usage patterns

Example custom vocabulary:
- Technical terms: "Kubernetes", "PostgreSQL", "API endpoint"
- Names: "Shreyas", "MacBook Pro", "ChatGPT"
- Acronyms: "CEO", "AI/ML", "SaaS"

### Audio Enhancement

Dicto automatically optimizes audio for better transcription:

- **Noise Reduction**: Filters background noise
- **Volume Normalization**: Adjusts audio levels
- **Voice Activity Detection**: Skips silence periods
- **Echo Cancellation**: Reduces room echo

Configure in Preferences → Audio Settings:
- **Input Device**: Select microphone
- **Quality Level**: Balance speed vs. accuracy
- **Enhancement Level**: Adjust noise reduction strength

---

## Configuration

### Preferences Window

Access via Menu Bar → ⚙️ Preferences or `Cmd+,`

#### General Tab
- **Launch at Startup**: Start Dicto automatically
- **Menu Bar Icon**: Show/hide the menu bar icon
- **Notifications**: Configure notification style
- **Language**: Select transcription language (English default)

#### Audio Tab
- **Input Device**: Choose microphone source
- **Sample Rate**: 16kHz (recommended) or 44.1kHz
- **Audio Quality**: Balance between speed and accuracy
- **Monitoring**: Enable real-time audio level display

#### Hotkeys Tab
- **Recording Shortcut**: Customize main hotkey
- **Conflict Detection**: Automatic conflict resolution
- **Global vs App-Specific**: Choose hotkey scope
- **Alternative Shortcuts**: Set backup hotkeys

#### Transcription Tab
- **AI Model**: Select Whisper model size
  - `tiny.en`: Fastest, basic accuracy (39MB)
  - `base.en`: Balanced speed/accuracy (147MB) ⭐ Recommended
  - `small.en`: Better accuracy, slower (244MB)
  - `medium.en`: High accuracy (769MB)
  - `large-v3`: Best accuracy, slowest (1.5GB)
- **Confidence Threshold**: Filter low-confidence results
- **Timestamp Insertion**: Add timestamps to long transcriptions
- **Auto-Capitalization**: Smart sentence capitalization

#### Privacy Tab
- **Local Processing**: All transcription happens on-device
- **Data Storage**: Control transcription history retention
- **Analytics**: Opt-in usage statistics (disabled by default)
- **Cleanup**: Automatic temporary file deletion

#### Advanced Tab
- **Performance Tuning**: CPU and memory usage limits
- **Debug Logging**: Enable detailed logging for support
- **Model Management**: Download/manage AI models
- **Export Settings**: Backup/restore configuration

### Configuration Files

Dicto stores settings in:
- **Main Config**: `~/Library/Application Support/Dicto/config.json`
- **User Vocabulary**: `~/Library/Application Support/Dicto/vocabulary.json`
- **Transcription History**: `~/Library/Application Support/Dicto/history.db`
- **Logs**: `~/Library/Application Support/Dicto/logs/`

### Backup & Restore

To backup your Dicto configuration:

1. **Open Preferences** → **Advanced** → **Export Settings**
2. **Save Configuration File**: Choose location for backup
3. **Include History**: Optionally backup transcription history

To restore configuration:

1. **Open Preferences** → **Advanced** → **Import Settings**
2. **Select Backup File**: Choose your configuration backup
3. **Restart Dicto**: Changes take effect after restart

---

## Troubleshooting

### Common Issues

#### "Hotkey not working"
**Solution**:
1. Check Accessibility permission: System Preferences → Security & Privacy → Privacy → Accessibility
2. Add Dicto to the list if missing
3. Restart Dicto after granting permission

#### "No audio detected"
**Solution**:
1. Check microphone permission: System Preferences → Security & Privacy → Privacy → Microphone
2. Verify microphone is connected and working in other apps
3. Try selecting a different input device in Dicto preferences

#### "Transcription is inaccurate"
**Solutions**:
1. Speak more clearly and at moderate pace
2. Reduce background noise
3. Try a larger AI model (e.g., switch from base.en to small.en)
4. Add custom vocabulary for specialized terms
5. Ensure good microphone positioning (6-12 inches from mouth)

#### "App won't start"
**Solution**:
1. Check system requirements (macOS 10.15+)
2. Restart your Mac
3. Reinstall Dicto
4. Run Dicto Support Tools for detailed diagnostics

#### "Slow transcription"
**Solutions**:
1. Use a smaller AI model (tiny.en or base.en)
2. Close other resource-intensive applications
3. Enable "Performance Mode" in Advanced preferences
4. Check available storage space (need 1GB+ free)

#### "Menu bar icon missing"
**Solution**:
1. Check "Show in menu bar" in Preferences → General
2. Look for hidden icons (click the double arrows in menu bar)
3. Restart Dicto
4. Reset preferences to defaults

### Error Messages

#### "Model file not found"
This indicates the AI model hasn't been downloaded:
1. Open Preferences → Advanced → Model Management
2. Click "Download" next to missing model
3. Wait for download to complete (may take several minutes)

#### "Microphone access denied"
System hasn't granted microphone permission:
1. Open System Preferences → Security & Privacy
2. Go to Privacy → Microphone
3. Add Dicto to the allowed apps list

#### "Recording failed"
Audio system issue:
1. Check microphone connection
2. Try a different input device
3. Restart the audio system: `sudo killall coreaudiod`
4. Restart Dicto

### Performance Optimization

#### For Older Macs
- Use `tiny.en` model for fastest performance
- Close unnecessary applications
- Reduce audio quality to 16kHz
- Disable audio enhancements

#### For Maximum Accuracy
- Use `large-v3` model (if you have 16GB+ RAM)
- Enable all audio enhancements
- Use external microphone in quiet environment
- Add custom vocabulary for your domain

#### Battery Optimization
- Use `base.en` model (best balance)
- Enable "Battery Mode" in Advanced preferences
- Reduce notification frequency
- Configure auto-sleep when not recording

### Getting Help

#### Built-in Support Tools
1. **Run Diagnostics**: Menu Bar → Help → Run Diagnostics
2. **View Logs**: Menu Bar → Help → Show Logs
3. **Health Check**: Menu Bar → Help → System Health Check

#### Support Resources
- **User Manual**: This document (available offline)
- **Video Tutorials**: dicto.app/tutorials
- **FAQ**: dicto.app/faq
- **Community Forum**: dicto.app/community
- **Email Support**: support@dicto.app

#### Reporting Issues
When contacting support, include:
1. **Diagnostic Report**: Use built-in diagnostic tool
2. **System Information**: macOS version, Mac model
3. **Steps to Reproduce**: Detailed description of the issue
4. **Screenshots**: If relevant to the problem

---

## Tips & Best Practices

### Getting the Best Transcription Accuracy

#### Speaking Technique
- **Speak naturally**: Don't slow down unnaturally
- **Enunciate clearly**: Pronounce words fully
- **Consistent pace**: Avoid rushing or speaking too slowly
- **Pause between sentences**: Brief pauses help with punctuation

#### Environment Setup
- **Quiet room**: Minimize background noise
- **Good microphone positioning**: 6-12 inches from mouth
- **Avoid echo**: Soft furnishings reduce room echo
- **Consistent distance**: Stay same distance from microphone

#### Content Optimization
- **Add custom vocabulary**: Include names, technical terms
- **Use full sentences**: Fragments are less accurate
- **Spell out abbreviations**: Say "API" as "A-P-I" initially
- **Provide context**: Lead with topic for better accuracy

### Workflow Integration

#### Writing & Editing
1. **Draft with voice**: Dictate initial thoughts quickly
2. **Edit with keyboard**: Refine and polish the text
3. **Mixed approach**: Alternate between typing and dictating
4. **Voice notes**: Capture ideas when away from keyboard

#### Meeting & Interview Transcription
1. **Test setup first**: Verify audio levels before important recordings
2. **Use external microphone**: Better quality for group settings
3. **Speaker identification**: Verbally note speaker changes
4. **Break into segments**: Stop/start for long sessions

#### Coding & Documentation
1. **Comments first**: Dictate code comments and documentation
2. **Variable names**: Spell out complex variable names
3. **Code review**: Dictate code review comments
4. **API documentation**: Voice-to-text for API descriptions

### Productivity Hacks

#### Quick Capture
- **Voice reminders**: "Remind me to call John at 3 PM"
- **Shopping lists**: Dictate items while cooking
- **Brain dumps**: Capture thoughts without breaking flow
- **Meeting notes**: Real-time transcription during calls

#### Accessibility Benefits
- **RSI relief**: Reduce repetitive strain from typing
- **Multitasking**: Dictate while doing other tasks
- **Learning support**: Great for dyslexia or writing difficulties
- **Hands-free operation**: Use when hands are occupied

#### Language Learning
- **Pronunciation practice**: See if Dicto understands your accent
- **Vocabulary building**: Practice new words
- **Fluency development**: Practice speaking naturally
- **Accent training**: Work on clear pronunciation

### Advanced Workflows

#### Content Creation
1. **Outline verbally**: Speak your article structure
2. **Record rough draft**: Get ideas down quickly
3. **Edit and refine**: Polish with traditional editing
4. **Add voice notes**: Insert ideas without breaking flow

#### Research & Interviews
1. **Live transcription**: Real-time notes during interviews
2. **Quote capture**: Accurate capture of important quotes
3. **Follow-up questions**: Note questions while listening
4. **Summary creation**: Verbally summarize key points

#### Business Communications
1. **Email drafts**: Dictate emails faster than typing
2. **Report writing**: Voice first drafts of reports
3. **Documentation**: Create procedure documents
4. **Training materials**: Develop training content efficiently

---

## Keyboard Shortcuts Reference

| Action | Default Shortcut | Customizable |
|--------|-----------------|--------------|
| Start/Stop Recording | `Cmd+V` | ✅ |
| Paste Last Transcription | `Cmd+Shift+V` | ✅ |
| Show Transcription History | `Cmd+Option+V` | ✅ |
| Open Preferences | `Cmd+,` | ✅ |
| Quick Settings Menu | `Cmd+Ctrl+V` | ✅ |
| Emergency Stop | `Cmd+Shift+Esc` | ❌ |
| Show/Hide Menu Icon | `Cmd+Shift+M` | ✅ |

---

## Privacy & Security

### Data Handling
- **Completely Offline**: All transcription happens on your device
- **No Network Required**: Works without internet connection
- **Local Storage**: Transcriptions stored only on your Mac
- **No Data Sharing**: Nothing sent to external servers
- **Automatic Cleanup**: Temporary files deleted after processing

### Permissions Explained
- **Microphone**: Required to record audio for transcription
- **Accessibility**: Needed for global hotkeys to work system-wide
- **Files & Folders**: Only for importing/exporting settings (optional)

### Security Features
- **Code Signed**: App is signed and verified by Apple
- **Notarized**: Approved by Apple's security scanning
- **Sandboxed**: Runs in secure container
- **Privacy First**: Designed with privacy as core principle

---

*This user guide is included with Dicto and available offline. For the latest version and video tutorials, visit [dicto.app/docs](https://dicto.app/docs)*

**Need Help?** Contact support@dicto.app or use the built-in diagnostic tools.

---

© 2024 Dicto Development Team. All rights reserved. 