#!/usr/bin/env python3
"""
setup.py for packaging Dicto as a macOS application
Build command: python setup.py py2app
"""

from setuptools import setup
import os

APP = ['dicto_main.py']
APP_NAME = 'Dicto'
VERSION = '1.0.1'

# Data files to include in the app bundle
DATA_FILES = [
    ('whisper.cpp/build/bin', ['whisper.cpp/build/bin/whisper-cli']),
    ('whisper.cpp/models', ['whisper.cpp/models/ggml-base.en.bin']),
]

# App icon (if you have one, otherwise remove this line)
# ICON_FILE = 'resources/dicto.icns'

OPTIONS = {
    'argv_emulation': False,  # Disable argv emulation for menu bar apps
    'iconfile': None,  # Add icon file path here if available
    'plist': {
        'CFBundleName': APP_NAME,
        'CFBundleDisplayName': APP_NAME,
        'CFBundleGetInfoString': 'AI-powered voice transcription for macOS',
        'CFBundleIdentifier': 'com.dicto.app',
        'CFBundleVersion': VERSION,
        'CFBundleShortVersionString': VERSION,
        'NSHumanReadableCopyright': 'Copyright © 2025. All rights reserved.',
        'LSUIElement': True,  # Run as menu bar app (no Dock icon)
        'NSMicrophoneUsageDescription': 'Dicto needs microphone access to record audio for transcription.',
        'NSAppleEventsUsageDescription': 'Dicto needs to send keystrokes to insert transcribed text.',
    },
    'packages': [
        'rumps',
        'pynput',
        'plyer',
        'AppKit',
        'Foundation',
        'Quartz',
        'pyobjc',
        'queue',
        'threading',
        'tempfile',
        'logging',
        'pathlib',
        'subprocess',
        'json',
        'time',
        'os',
        'sys',
        'hashlib',
        'signal',
    ],
    'includes': [
        'dicto_core',
        'vocabulary_manager',
        'continuous_recorder',
        'auto_text_inserter',
        'menu_bar_manager',
        'session_manager',
        'error_handler',
        'config_manager',
        'performance_monitor',
        'audio_recorder',
        'audio_processor',
    ],
    'excludes': [
        'matplotlib',
        'numpy',
        'scipy',
        'tkinter',  # We use native macOS dialogs where possible
    ],
    'resources': [],
    'optimize': 2,  # Optimize Python bytecode
}

setup(
    name=APP_NAME,
    version=VERSION,
    description='AI-powered voice transcription for macOS',
    author='Dicto Team',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
    install_requires=[
        'rumps>=0.3.0',
        'pynput>=1.7.6',
        'plyer>=2.1.0',
        'pyobjc-framework-Cocoa>=9.0',
        'pyobjc-framework-Quartz>=9.0',
        'pyaudio>=0.2.11',
        'pydub>=0.25.1',
        'rich>=13.0.0',
        'sounddevice>=0.4.6',
    ],
)
