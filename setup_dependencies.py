#!/usr/bin/env python3
"""
Setup script for Dicto dependencies.
Installs required Python packages for macOS system-wide transcription.
"""

import subprocess
import sys
import os


def install_package(package_name: str) -> bool:
    """Install a Python package using pip."""
    try:
        print(f"Installing {package_name}...")
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", package_name
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ {package_name} installed successfully")
            return True
        else:
            print(f"❌ Failed to install {package_name}: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error installing {package_name}: {e}")
        return False


def check_macos():
    """Check if running on macOS."""
    if os.uname().sysname != "Darwin":
        print("❌ This application is designed for macOS only")
        return False
    print("✅ Running on macOS")
    return True


def main():
    """Main setup function."""
    print("Setting up Dicto dependencies for macOS...")
    print("=" * 50)
    
    # Check macOS
    if not check_macos():
        sys.exit(1)
    
    # Required packages
    packages = [
        "pynput",  # Global hotkey support
        "plyer",   # Cross-platform notifications
        "pyobjc-framework-Cocoa",  # macOS clipboard integration
    ]
    
    # Install packages
    failed_packages = []
    for package in packages:
        if not install_package(package):
            failed_packages.append(package)
    
    # Report results
    print("\n" + "=" * 50)
    if failed_packages:
        print("❌ Setup completed with errors:")
        for package in failed_packages:
            print(f"   - {package} failed to install")
        print("\nPlease install failed packages manually:")
        print(f"   pip install {' '.join(failed_packages)}")
        sys.exit(1)
    else:
        print("✅ All dependencies installed successfully!")
        print("\nNext steps:")
        print("1. Ensure whisper.cpp is built (see setup instructions)")
        print("2. Grant microphone permission to your terminal")
        print("3. Run: python dicto_main.py")
        print("\nFor microphone permission:")
        print("System Preferences > Security & Privacy > Privacy > Microphone")


if __name__ == "__main__":
    main() 