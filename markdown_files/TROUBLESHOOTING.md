# 🔧 Dicto Troubleshooting Guide

**Complete problem-solving guide for common issues**

Version 1.0 | Updated: December 2024

---

## Table of Contents

1. [Quick Diagnostics](#quick-diagnostics)
2. [Installation Issues](#installation-issues)
3. [Permission Problems](#permission-problems)
4. [Audio & Recording Issues](#audio--recording-issues)
5. [Transcription Problems](#transcription-problems)
6. [Performance Issues](#performance-issues)
7. [Hotkey Problems](#hotkey-problems)
8. [Error Messages](#error-messages)
9. [Advanced Troubleshooting](#advanced-troubleshooting)

---

## Quick Diagnostics

Run this first for any issue:

```bash
python support_tools.py --health-check
```

---

## Common Issues & Solutions

### 🚫 Hotkeys Not Working

**Problem**: Cmd+V doesn't start recording

**Solution**:
1. Check Accessibility permission:
   - System Preferences → Security & Privacy → Privacy → Accessibility
   - Add Dicto.app and check the box
2. Restart Dicto after granting permission

### 🎤 No Audio Detected

**Problem**: Recording doesn't capture sound

**Solution**:
1. Check microphone permission:
   - System Preferences → Security & Privacy → Privacy → Microphone
   - Add Dicto to allowed apps
2. Verify microphone works in other apps
3. Select correct device in Dicto Preferences → Audio

### 📱 App Won't Launch

**Problem**: Dicto crashes or won't start

**Solution**:
1. Check macOS version (10.15+ required)
2. Reset app cache:
   ```bash
   rm -rf ~/Library/Caches/com.dicto.transcription
   ```
3. Reinstall from DMG

### 🐌 Slow Transcription

**Problem**: Long processing delays

**Solution**:
1. Use smaller model: Preferences → Transcription → Model → "tiny.en"
2. Close other resource-intensive apps
3. Check available disk space (need 1GB+ free)

### ❌ Poor Accuracy

**Problem**: Wrong words, missing text

**Solution**:
1. Speak clearly at moderate pace
2. Reduce background noise
3. Try larger model: "base.en" or "small.en"
4. Add custom vocabulary for specialized terms

---

## Installation Issues

### Issue: "App won't launch"

**Symptoms**: Dicto.app doesn't start, crashes immediately, or shows error dialog

**Solutions**:

1. **Check System Requirements**:
   - macOS 10.15+ required
   - Check: Apple Menu → About This Mac

2. **Verify Installation**:
   ```bash
   # Check if app is properly installed
   ls -la /Applications/Dicto.app
   
   # Check app signature
   codesign -dv /Applications/Dicto.app
   ```

3. **Reset Launch Services**:
   ```bash
   /System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -kill -r -domain local -domain system -domain user
   ```

4. **Clear App Cache**:
   ```bash
   rm -rf ~/Library/Caches/com.dicto.transcription
   rm -rf ~/Library/Application\ Support/Dicto/cache
   ```

5. **Reinstall from Scratch**:
   ```bash
   # Remove existing installation
   rm -rf /Applications/Dicto.app
   rm -rf ~/Library/Application\ Support/Dicto
   rm -rf ~/Library/Caches/com.dicto.transcription
   
   # Reinstall from DMG or PKG
   ```

### Issue: "Installation blocked by Gatekeeper"

**Symptoms**: "Cannot be opened because it is from an unidentified developer"

**Solutions**:

1. **Allow in Security Preferences**:
   - System Preferences → Security & Privacy → General
   - Click "Open Anyway" next to Dicto message

2. **Override Gatekeeper** (if needed):
   ```bash
   sudo spctl --master-disable
   # Install Dicto, then re-enable:
   sudo spctl --master-enable
   ```

3. **Alternative Installation**:
   - Right-click Dicto.app → "Open"
   - Click "Open" in dialog

### Issue: "Damaged app" error

**Symptoms**: "Dicto.app is damaged and can't be opened"

**Solutions**:

1. **Clear Quarantine Attribute**:
   ```bash
   sudo xattr -rd com.apple.quarantine /Applications/Dicto.app
   ```

2. **Re-download Application**:
   - Download fresh copy from official source
   - Verify download integrity

3. **Check Disk Space**:
   ```bash
   df -h
   # Ensure sufficient space (minimum 2GB free)
   ```

---

## Permission Problems

### Issue: "Microphone permission denied"

**Symptoms**: No audio recording, "Access denied" errors

**Solutions**:

1. **Grant Microphone Access**:
   - System Preferences → Security & Privacy → Privacy → Microphone
   - Unlock with password if needed
   - Add Dicto to the list or check existing box

2. **Reset Microphone Permissions**:
   ```bash
   # Reset all microphone permissions
   tccutil reset Microphone
   # Restart Dicto to re-prompt
   ```

3. **Check for Multiple Dicto Entries**:
   - Look for duplicate entries in Privacy settings
   - Remove old entries, keep only current one

4. **Verify Permission Status**:
   ```bash
   python -c "
   import subprocess
   result = subprocess.run(['osascript', '-e', 'tell application \"System Events\" to get microphone authorization status'], capture_output=True, text=True)
   print('Status:', result.stdout.strip())
   "
   ```

### Issue: "Accessibility permission required"

**Symptoms**: Global hotkeys don't work, "Permission required" notifications

**Solutions**:

1. **Grant Accessibility Access**:
   - System Preferences → Security & Privacy → Privacy → Accessibility
   - Unlock and add Dicto.app
   - Ensure checkbox is checked

2. **Remove and Re-add**:
   - Remove Dicto from Accessibility list
   - Restart Dicto
   - Re-add when prompted

3. **Terminal Method**:
   ```bash
   # Check current accessibility status
   osascript -e 'tell application "System Events" to get UI elements enabled'
   ```

### Issue: "Full Disk Access needed"

**Symptoms**: Cannot access certain folders, save issues

**Solutions**:

1. **Grant Full Disk Access** (if needed):
   - System Preferences → Security & Privacy → Privacy → Full Disk Access
   - Add Dicto.app

2. **Alternative Storage Location**:
   - Use ~/Documents/Dicto instead of system folders
   - Configure in Preferences → Advanced → Storage

---

## Audio & Recording Issues

### Issue: "No audio detected"

**Symptoms**: Recording doesn't capture sound, silent transcriptions

**Solutions**:

1. **Check Microphone Hardware**:
   ```bash
   # Test microphone in other apps
   # Open QuickTime Player → New Audio Recording
   ```

2. **Verify Input Device**:
   - Dicto Preferences → Audio → Input Device
   - Try different microphone if available
   - Check device isn't muted or volume too low

3. **Test Audio Levels**:
   ```bash
   python -c "
   import audio_processor
   ap = audio_processor.AudioProcessor()
   print('Testing audio levels...')
   ap.test_audio_levels(duration=5)
   "
   ```

4. **Reset Audio System**:
   ```bash
   # Reset Core Audio
   sudo killall coreaudiod
   # Wait 10 seconds, then test again
   ```

### Issue: "Poor audio quality"

**Symptoms**: Muffled recording, background noise, distortion

**Solutions**:

1. **Optimize Microphone Settings**:
   - Position 6-12 inches from mouth
   - Reduce background noise
   - Use external microphone if possible

2. **Adjust Audio Settings**:
   - Preferences → Audio → Enhancement Level
   - Enable noise reduction
   - Try different sample rates

3. **Check System Audio Settings**:
   - System Preferences → Sound → Input
   - Adjust input volume (middle range)
   - Enable "Use ambient noise reduction"

### Issue: "Audio device not found"

**Symptoms**: Selected microphone not available, device errors

**Solutions**:

1. **Refresh Device List**:
   - Unplug and reconnect USB microphone
   - Restart Dicto
   - Check Preferences → Audio → Input Device

2. **List Available Devices**:
   ```bash
   python -c "
   import audio_processor
   ap = audio_processor.AudioProcessor()
   devices = ap.list_audio_devices()
   for i, device in enumerate(devices):
       print(f'{i}: {device}')
   "
   ```

3. **Reset to Default**:
   - Preferences → Audio → Input Device → "System Default"
   - Test recording functionality

---

## Transcription Problems

### Issue: "Inaccurate transcriptions"

**Symptoms**: Wrong words, poor grammar, missing text

**Solutions**:

1. **Improve Speaking Technique**:
   - Speak clearly and at moderate pace
   - Use complete sentences
   - Pause between thoughts

2. **Optimize Environment**:
   - Reduce background noise
   - Use quiet room
   - Avoid echo (add soft furnishings)

3. **Adjust Model Settings**:
   - Try larger model: Preferences → Transcription → Model
   - Increase confidence threshold
   - Add custom vocabulary for specialized terms

4. **Check Audio Quality**:
   - Ensure good microphone positioning
   - Test with different microphone if available
   - Enable audio enhancements

### Issue: "Slow transcription processing"

**Symptoms**: Long delays, "Processing..." persists

**Solutions**:

1. **Use Smaller Model**:
   - Switch to `tiny.en` or `base.en`
   - Preferences → Transcription → Model

2. **Optimize Performance**:
   - Close other resource-intensive apps
   - Enable Performance Mode in Advanced settings
   - Restart Dicto to clear memory

3. **Check System Resources**:
   ```bash
   # Check memory usage
   top -l 1 | grep "PhysMem"
   
   # Check available disk space
   df -h
   ```

4. **Hardware-Specific Optimization**:
   - **Apple Silicon**: Enable Metal acceleration
   - **Intel Macs**: Reduce model size, disable GPU acceleration

### Issue: "Model file not found"

**Symptoms**: "Model not available" errors, transcription fails

**Solutions**:

1. **Download Missing Model**:
   ```bash
   cd whisper.cpp
   bash ./models/download-ggml-model.sh base.en
   ```

2. **Verify Model Integrity**:
   ```bash
   ls -la whisper.cpp/models/ggml-*.bin
   # Files should be non-zero size
   ```

3. **Reset Model Path**:
   - Preferences → Advanced → Model Management
   - Click "Reset to Default"
   - Re-download if needed

---

## Performance Issues

### Issue: "High CPU usage"

**Symptoms**: Fan noise, system slowdown, battery drain

**Solutions**:

1. **Optimize CPU Settings**:
   - Preferences → Advanced → Performance
   - Set CPU limit to 50-70%
   - Use smaller AI model

2. **Enable Battery Mode**:
   - Preferences → Advanced → Battery Optimization
   - Reduces CPU usage when on battery

3. **Monitor Resource Usage**:
   ```bash
   # Check Dicto CPU usage
   top -pid $(pgrep -f dicto)
   ```

### Issue: "High memory usage"

**Symptoms**: System becomes sluggish, swap usage increases

**Solutions**:

1. **Reduce Memory Footprint**:
   - Use `tiny.en` model instead of larger ones
   - Disable model caching
   - Reduce buffer size

2. **Clear Cache**:
   ```bash
   rm -rf ~/Library/Application\ Support/Dicto/cache
   rm -rf ~/Library/Caches/com.dicto.transcription
   ```

3. **Memory Settings**:
   - Preferences → Advanced → Performance
   - Set memory limit appropriately
   - Enable aggressive cleanup

### Issue: "App becomes unresponsive"

**Symptoms**: UI freezes, no response to clicks

**Solutions**:

1. **Force Restart**:
   ```bash
   # Kill all Dicto processes
   pkill -f dicto
   # Wait 10 seconds, then restart
   ```

2. **Check for Deadlocks**:
   ```bash
   # Generate diagnostic report
   python support_tools.py --diagnostics
   # Check logs for deadlock patterns
   ```

3. **Safe Mode Start**:
   ```bash
   # Start with minimal configuration
   python dicto_main.py --safe-mode
   ```

---

## Hotkey Problems

### Issue: "Hotkeys not working"

**Symptoms**: Cmd+V doesn't trigger recording, no response

**Solutions**:

1. **Check Accessibility Permission** (most common):
   - System Preferences → Security & Privacy → Privacy → Accessibility
   - Ensure Dicto is listed and checked
   - Restart Dicto after granting permission

2. **Test Hotkey Detection**:
   ```bash
   python -c "
   import pynput
   print('Testing hotkey system...')
   # Should import without errors
   "
   ```

3. **Alternative Hotkey**:
   - Preferences → Hotkeys
   - Try different key combination
   - Avoid conflicts with system shortcuts

4. **Restart Input Monitoring**:
   ```bash
   # Kill input monitoring service
   sudo pkill -f InputMethodKit
   # System will restart it automatically
   ```

### Issue: "Hotkey conflicts"

**Symptoms**: Other apps also respond to Cmd+V, unexpected behavior

**Solutions**:

1. **Check for Conflicts**:
   - Preferences → Hotkeys → "Detect Conflicts"
   - Review conflicting applications

2. **Change Hotkey**:
   - Use alternative like Cmd+Shift+V
   - Or Cmd+Option+V
   - Test new combination

3. **Application-Specific Settings**:
   - Configure per-app hotkeys if available
   - Disable conflicting app shortcuts

---

## Error Messages

### "Transport endpoint is not connected"

**Cause**: Audio system disconnection

**Solution**:
```bash
# Reset audio system
sudo killall coreaudiod
# Restart Dicto
```

### "Model loading failed"

**Cause**: Corrupted or missing model file

**Solution**:
```bash
# Re-download model
cd whisper.cpp
rm models/ggml-base.en.bin
bash ./models/download-ggml-model.sh base.en
```

### "Permission denied: microphone"

**Cause**: Missing microphone permission

**Solution**:
1. System Preferences → Security & Privacy → Privacy → Microphone
2. Add Dicto to allowed applications

### "Accessibility API error"

**Cause**: Missing accessibility permission

**Solution**:
1. System Preferences → Security & Privacy → Privacy → Accessibility
2. Add Dicto.app and check the box

### "Out of memory"

**Cause**: Insufficient RAM for selected model

**Solution**:
1. Switch to smaller model (tiny.en or base.en)
2. Close other applications
3. Restart system if needed

### "Audio device busy"

**Cause**: Another app is using the microphone

**Solution**:
1. Close other apps using microphone
2. Check for background recording apps
3. Select different input device

---

## Advanced Troubleshooting

### Reset Configuration
```bash
rm ~/Library/Application\ Support/Dicto/config.json
# Restart Dicto to create defaults
```

### View Logs
```bash
tail -f ~/Library/Application\ Support/Dicto/logs/dicto.log
```

### Complete Reinstall
```bash
rm -rf /Applications/Dicto.app
rm -rf ~/Library/Application\ Support/Dicto
# Reinstall from DMG
```

### Debug Mode

Enable detailed logging:

```bash
# Start with debug logging
python dicto_main.py --debug --log-level DEBUG

# Or set environment variable
export DICTO_LOG_LEVEL=DEBUG
python dicto_main.py
```

### Log Analysis

Check log files for detailed error information:

```bash
# View recent logs
tail -f ~/Library/Application\ Support/Dicto/logs/dicto.log

# Search for errors
grep -i error ~/Library/Application\ Support/Dicto/logs/*.log

# View performance logs
cat ~/Library/Application\ Support/Dicto/logs/performance.log
```

### Configuration Reset

Reset to factory defaults:

```bash
# Backup current config
cp ~/Library/Application\ Support/Dicto/config.json ~/Desktop/dicto-config-backup.json

# Reset configuration
rm ~/Library/Application\ Support/Dicto/config.json
rm -rf ~/Library/Application\ Support/Dicto/cache

# Restart Dicto (will create default config)
```

### Safe Mode

Start Dicto with minimal configuration:

```bash
python dicto_main.py --safe-mode --no-hotkeys --basic-audio
```

### System Integration Check

Verify system integration:

```bash
# Check Launch Agent
launchctl list | grep dicto

# Check system permissions
sqlite3 ~/Library/Application\ Support/com.apple.TCC/TCC.db "SELECT service, client, auth_value FROM access WHERE client LIKE '%dicto%';"

# Check audio system
system_profiler SPAudioDataType
```

### Network Diagnostics

For update and telemetry issues:

```bash
# Test connectivity
curl -I https://api.dicto.app/health

# Check DNS resolution
nslookup api.dicto.app

# Test certificate
openssl s_client -connect api.dicto.app:443 -servername api.dicto.app
```

### Performance Profiling

For performance issues:

```bash
# Run performance benchmark
python benchmark_suite.py --full --output performance-report.json

# Memory profiling
python -m memory_profiler dicto_main.py

# CPU profiling  
python -m cProfile -o profile.stats dicto_main.py
```

---

## Still Need Help?

1. Run diagnostic report: `python support_tools.py --support-package`
2. Contact: support@dicto.app
3. Include: System info, error messages, diagnostic report

---

© 2024 Dicto Development Team. All rights reserved. 