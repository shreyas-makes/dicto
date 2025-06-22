#!/usr/bin/env python3
"""
Dicto Professional Installer
Automated installation and deployment system for macOS system-wide transcription.

Features:
- Guided step-by-step installation process
- Comprehensive dependency management and conflict resolution
- System integration and permission configuration
- macOS service installation with LaunchAgent
- Post-installation verification and testing

Usage:
    python3 installer.py
    python3 installer.py --unattended  # Silent installation
    python3 installer.py --verify      # Post-installation verification only
"""

import os
import sys
import subprocess
import shutil
import json
import tempfile
import logging
import urllib.request
import hashlib
import stat
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import argparse
import time
import platform
import pkg_resources
import re


@dataclass
class InstallationConfig:
    """Configuration for Dicto installation."""
    app_name: str = "Dicto"
    app_identifier: str = "com.dicto.transcription"
    install_location: str = "/Applications/Dicto.app"
    user_data_dir: str = "~/Library/Application Support/Dicto"
    launch_agent_path: str = "~/Library/LaunchAgents/com.dicto.transcription.plist"
    whisper_model_url: str = "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin"
    whisper_model_hash: str = "60ed5bc3dd14eea856493d334349b405782ddcaf0028d4b5df4088345ffa2aca"
    python_min_version: Tuple[int, int] = (3, 8)
    macos_min_version: Tuple[int, int] = (10, 15)


class SystemChecker:
    """System compatibility and requirement checker."""
    
    def __init__(self, config: InstallationConfig):
        self.config = config
        self.logger = logging.getLogger("DictoInstaller.SystemChecker")
    
    def check_macos_version(self) -> Tuple[bool, str]:
        """Check if macOS version meets requirements."""
        try:
            version_str = platform.mac_ver()[0]
            if not version_str:
                return False, "Unable to determine macOS version"
            
            major, minor = map(int, version_str.split('.')[:2])
            required_major, required_minor = self.config.macos_min_version
            
            if (major, minor) >= (required_major, required_minor):
                return True, f"macOS {version_str} (compatible)"
            else:
                return False, f"macOS {version_str} found, but {required_major}.{required_minor}+ required"
                
        except Exception as e:
            return False, f"Error checking macOS version: {e}"
    
    def check_python_version(self) -> Tuple[bool, str]:
        """Check if Python version meets requirements."""
        try:
            current = sys.version_info[:2]
            required = self.config.python_min_version
            
            if current >= required:
                return True, f"Python {'.'.join(map(str, current))} (compatible)"
            else:
                return False, f"Python {'.'.join(map(str, current))} found, but {'.'.join(map(str, required))}+ required"
                
        except Exception as e:
            return False, f"Error checking Python version: {e}"
    
    def check_homebrew(self) -> Tuple[bool, str]:
        """Check if Homebrew is installed."""
        try:
            result = subprocess.run(['brew', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                version_line = result.stdout.split('\n')[0]
                return True, f"Homebrew found: {version_line}"
            else:
                return False, "Homebrew not found or not working"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False, "Homebrew not installed"
        except Exception as e:
            return False, f"Error checking Homebrew: {e}"
    
    def check_xcode_tools(self) -> Tuple[bool, str]:
        """Check if Xcode Command Line Tools are installed."""
        try:
            result = subprocess.run(['xcode-select', '--print-path'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and result.stdout.strip():
                return True, f"Xcode tools found at: {result.stdout.strip()}"
            else:
                return False, "Xcode Command Line Tools not found"
        except Exception as e:
            return False, f"Error checking Xcode tools: {e}"
    
    def check_disk_space(self, required_mb: int = 500) -> Tuple[bool, str]:
        """Check available disk space."""
        try:
            statvfs = os.statvfs('/')
            free_bytes = statvfs.f_frsize * statvfs.f_bavail
            free_mb = free_bytes / (1024 * 1024)
            
            if free_mb >= required_mb:
                return True, f"{free_mb:.1f} MB available (sufficient)"
            else:
                return False, f"Only {free_mb:.1f} MB available, {required_mb} MB required"
                
        except Exception as e:
            return False, f"Error checking disk space: {e}"
    
    def check_permissions(self) -> Tuple[bool, str]:
        """Check if we have necessary permissions."""
        issues = []
        
        # Check write access to Applications
        try:
            test_path = "/Applications/.dicto_install_test"
            Path(test_path).touch()
            Path(test_path).unlink()
        except PermissionError:
            issues.append("No write access to /Applications (may need admin privileges)")
        except Exception:
            pass
        
        # Check LaunchAgents directory
        try:
            launch_dir = Path.home() / "Library" / "LaunchAgents"
            launch_dir.mkdir(parents=True, exist_ok=True)
            test_file = launch_dir / ".dicto_test"
            test_file.touch()
            test_file.unlink()
        except Exception:
            issues.append("Cannot access LaunchAgents directory")
        
        if issues:
            return False, "; ".join(issues)
        else:
            return True, "Sufficient permissions"


class DependencyResolver:
    """Handles dependency installation and conflict resolution."""
    
    def __init__(self, config: InstallationConfig):
        self.config = config
        self.logger = logging.getLogger("DictoInstaller.DependencyResolver")
        self.pip_packages = [
            "rumps>=0.3.0",
            "pynput>=1.7.6",
            "pydub>=0.25.1",
            "plyer>=2.1.0",
            "pyobjc-framework-Cocoa>=9.0",
            "pyobjc-framework-Quartz>=9.0",
            "sounddevice>=0.4.6",
            "rich>=13.0.0",
            "pyaudio>=0.2.11"
        ]
        self.system_packages = ["sox", "ffmpeg", "cmake"]
    
    def check_pip_package(self, package_spec: str) -> Tuple[bool, str]:
        """Check if a pip package is installed and meets requirements."""
        try:
            if '>=' in package_spec:
                package_name, version_spec = package_spec.split('>=')
                required_version = version_spec.strip()
            else:
                package_name = package_spec
                required_version = None
            
            package_name = package_name.strip()
            
            try:
                installed_version = pkg_resources.get_distribution(package_name).version
                if required_version and self._compare_versions(installed_version, required_version) < 0:
                    return False, f"{package_name} {installed_version} installed, but {required_version}+ required"
                return True, f"{package_name} {installed_version} (OK)"
            except pkg_resources.DistributionNotFound:
                return False, f"{package_name} not installed"
                
        except Exception as e:
            return False, f"Error checking {package_spec}: {e}"
    
    def _compare_versions(self, version1: str, version2: str) -> int:
        """Compare two version strings. Returns -1, 0, or 1."""
        try:
            v1_parts = [int(x) for x in version1.split('.')]
            v2_parts = [int(x) for x in version2.split('.')]
            
            max_len = max(len(v1_parts), len(v2_parts))
            v1_parts.extend([0] * (max_len - len(v1_parts)))
            v2_parts.extend([0] * (max_len - len(v2_parts)))
            
            if v1_parts < v2_parts:
                return -1
            elif v1_parts > v2_parts:
                return 1
            else:
                return 0
        except Exception:
            return 0
    
    def check_system_package(self, package: str) -> Tuple[bool, str]:
        """Check if a system package is installed via Homebrew."""
        try:
            result = subprocess.run(['brew', 'list', package], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                # Get version info
                version_result = subprocess.run(['brew', 'list', '--versions', package],
                                              capture_output=True, text=True, timeout=10)
                if version_result.returncode == 0:
                    version_info = version_result.stdout.strip()
                    return True, f"{version_info} (installed)"
                return True, f"{package} (installed)"
            else:
                return False, f"{package} not installed"
        except Exception as e:
            return False, f"Error checking {package}: {e}"
    
    def install_pip_packages(self, packages: List[str]) -> bool:
        """Install Python packages via pip."""
        try:
            cmd = [sys.executable, '-m', 'pip', 'install', '--upgrade'] + packages
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                self.logger.info(f"Successfully installed pip packages: {packages}")
                return True
            else:
                self.logger.error(f"Failed to install pip packages: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error installing pip packages: {e}")
            return False
    
    def install_system_packages(self, packages: List[str]) -> bool:
        """Install system packages via Homebrew."""
        try:
            for package in packages:
                cmd = ['brew', 'install', package]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                
                if result.returncode != 0:
                    self.logger.error(f"Failed to install {package}: {result.stderr}")
                    return False
                    
                self.logger.info(f"Successfully installed {package}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error installing system packages: {e}")
            return False
    
    def resolve_conflicts(self) -> List[str]:
        """Identify and suggest resolutions for dependency conflicts."""
        conflicts = []
        
        # Check for known problematic package combinations
        try:
            import pyaudio
            import sounddevice
            self.logger.info("Both pyaudio and sounddevice are available")
        except ImportError as e:
            conflicts.append(f"Audio library conflict: {e}")
        
        # Check for PyObjC framework conflicts
        try:
            from AppKit import NSApplication
            from Quartz import CGEventTapCreate
            self.logger.info("PyObjC frameworks working correctly")
        except ImportError as e:
            conflicts.append(f"PyObjC framework issue: {e}")
        
        return conflicts


class WhisperSetup:
    """Handles Whisper.cpp compilation and model download."""
    
    def __init__(self, config: InstallationConfig, install_dir: Path):
        self.config = config
        self.install_dir = install_dir
        self.whisper_dir = install_dir / "whisper.cpp"
        self.models_dir = self.whisper_dir / "models"
        self.logger = logging.getLogger("DictoInstaller.WhisperSetup")
    
    def clone_whisper_repo(self) -> bool:
        """Clone the whisper.cpp repository."""
        try:
            if self.whisper_dir.exists():
                self.logger.info("Whisper.cpp directory already exists, updating...")
                result = subprocess.run(['git', 'pull'], 
                                      cwd=self.whisper_dir, 
                                      capture_output=True, text=True, timeout=60)
                return result.returncode == 0
            else:
                self.logger.info("Cloning whisper.cpp repository...")
                result = subprocess.run([
                    'git', 'clone', 
                    'https://github.com/ggerganov/whisper.cpp.git',
                    str(self.whisper_dir)
                ], capture_output=True, text=True, timeout=120)
                return result.returncode == 0
                
        except Exception as e:
            self.logger.error(f"Error cloning whisper.cpp: {e}")
            return False
    
    def compile_whisper(self) -> bool:
        """Compile whisper.cpp with optimizations."""
        try:
            self.logger.info("Compiling whisper.cpp...")
            
            # Create build directory
            build_dir = self.whisper_dir / "build"
            build_dir.mkdir(exist_ok=True)
            
            # Configure with CMake
            cmake_cmd = [
                'cmake', '..', 
                '-DCMAKE_BUILD_TYPE=Release',
                '-DWHISPER_BUILD_TESTS=OFF',
                '-DWHISPER_BUILD_EXAMPLES=ON'
            ]
            
            result = subprocess.run(cmake_cmd, 
                                  cwd=build_dir, 
                                  capture_output=True, text=True, timeout=120)
            
            if result.returncode != 0:
                self.logger.error(f"CMake configuration failed: {result.stderr}")
                return False
            
            # Build
            build_cmd = ['make', '-j', str(os.cpu_count() or 4)]
            result = subprocess.run(build_cmd,
                                  cwd=build_dir,
                                  capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                self.logger.info("Whisper.cpp compiled successfully")
                return True
            else:
                self.logger.error(f"Compilation failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error compiling whisper.cpp: {e}")
            return False
    
    def download_model(self) -> bool:
        """Download and verify the Whisper model."""
        try:
            self.models_dir.mkdir(parents=True, exist_ok=True)
            model_path = self.models_dir / "ggml-base.en.bin"
            
            if model_path.exists():
                # Verify existing model
                if self._verify_model_hash(model_path):
                    self.logger.info("Model already exists and is valid")
                    return True
                else:
                    self.logger.warning("Existing model is corrupted, re-downloading...")
                    model_path.unlink()
            
            self.logger.info("Downloading Whisper model...")
            
            # Download with progress
            def progress_hook(block_num, block_size, total_size):
                if total_size > 0:
                    percent = (block_num * block_size / total_size) * 100
                    if block_num % 100 == 0:  # Update every 100 blocks
                        print(f"\rDownloading model... {percent:.1f}%", end='', flush=True)
            
            urllib.request.urlretrieve(
                self.config.whisper_model_url,
                str(model_path),
                reporthook=progress_hook
            )
            print()  # New line after progress
            
            # Verify download
            if self._verify_model_hash(model_path):
                self.logger.info("Model downloaded and verified successfully")
                return True
            else:
                self.logger.error("Downloaded model failed hash verification")
                model_path.unlink()
                return False
                
        except Exception as e:
            self.logger.error(f"Error downloading model: {e}")
            return False
    
    def _verify_model_hash(self, model_path: Path) -> bool:
        """Verify model file hash."""
        try:
            sha256_hash = hashlib.sha256()
            with open(model_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            
            calculated_hash = sha256_hash.hexdigest()
            return calculated_hash == self.config.whisper_model_hash
            
        except Exception as e:
            self.logger.error(f"Error verifying model hash: {e}")
            return False


class SystemIntegrator:
    """Handles macOS system integration and service installation."""
    
    def __init__(self, config: InstallationConfig, install_dir: Path):
        self.config = config
        self.install_dir = install_dir
        self.logger = logging.getLogger("DictoInstaller.SystemIntegrator")
    
    def create_launch_agent(self) -> bool:
        """Create LaunchAgent for background operation."""
        try:
            launch_agent_path = Path(self.config.launch_agent_path).expanduser()
            launch_agent_path.parent.mkdir(parents=True, exist_ok=True)
            
            plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{self.config.app_identifier}</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>{self.install_dir}/dicto_main.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>{Path.home()}/Library/Logs/Dicto/dicto.log</string>
    <key>StandardErrorPath</key>
    <string>{Path.home()}/Library/Logs/Dicto/dicto_error.log</string>
    <key>WorkingDirectory</key>
    <string>{self.install_dir}</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin</string>
    </dict>
</dict>
</plist>"""
            
            with open(launch_agent_path, 'w') as f:
                f.write(plist_content)
            
            # Set proper permissions
            os.chmod(launch_agent_path, 0o644)
            
            self.logger.info(f"LaunchAgent created at {launch_agent_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating LaunchAgent: {e}")
            return False
    
    def register_launch_agent(self) -> bool:
        """Register the LaunchAgent with launchd."""
        try:
            launch_agent_path = Path(self.config.launch_agent_path).expanduser()
            
            # Load the LaunchAgent
            result = subprocess.run([
                'launchctl', 'load', '-w', str(launch_agent_path)
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                self.logger.info("LaunchAgent registered successfully")
                return True
            else:
                self.logger.error(f"Failed to register LaunchAgent: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error registering LaunchAgent: {e}")
            return False
    
    def create_app_bundle(self) -> bool:
        """Create macOS application bundle."""
        try:
            app_path = Path(self.config.install_location)
            contents_dir = app_path / "Contents"
            macos_dir = contents_dir / "MacOS"
            resources_dir = contents_dir / "Resources"
            
            # Create directory structure
            for dir_path in [app_path, contents_dir, macos_dir, resources_dir]:
                dir_path.mkdir(parents=True, exist_ok=True)
            
            # Create Info.plist
            info_plist = contents_dir / "Info.plist"
            plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>dicto_launcher</string>
    <key>CFBundleIdentifier</key>
    <string>{self.config.app_identifier}</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundleName</key>
    <string>{self.config.app_name}</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.0</string>
    <key>CFBundleVersion</key>
    <string>1.0.0</string>
    <key>LSMinimumSystemVersion</key>
    <string>{'.'.join(map(str, self.config.macos_min_version))}</string>
    <key>LSUIElement</key>
    <true/>
    <key>NSMicrophoneUsageDescription</key>
    <string>Dicto needs microphone access for voice transcription.</string>
    <key>NSAppleEventsUsageDescription</key>
    <string>Dicto needs Apple Events access for system integration.</string>
</dict>
</plist>"""
            
            with open(info_plist, 'w') as f:
                f.write(plist_content)
            
            # Create launcher script
            launcher_script = macos_dir / "dicto_launcher"
            script_content = f"""#!/bin/bash
cd "{self.install_dir}"
exec /usr/bin/python3 dicto_main.py
"""
            
            with open(launcher_script, 'w') as f:
                f.write(script_content)
            
            # Make launcher executable
            os.chmod(launcher_script, 0o755)
            
            # Copy application files
            for file_name in ['dicto_main.py', 'dicto_core.py', 'audio_processor.py']:
                src_file = self.install_dir / file_name
                if src_file.exists():
                    dst_file = resources_dir / file_name
                    shutil.copy2(src_file, dst_file)
            
            self.logger.info(f"App bundle created at {app_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating app bundle: {e}")
            return False
    
    def setup_permissions(self) -> Tuple[bool, List[str]]:
        """Set up required macOS permissions."""
        permission_requests = []
        
        # Check current permissions
        accessibility_status = self._check_accessibility_permission()
        microphone_status = self._check_microphone_permission()
        
        if not accessibility_status:
            permission_requests.append(
                "Accessibility: System Preferences → Security & Privacy → Privacy → Accessibility"
            )
        
        if not microphone_status:
            permission_requests.append(
                "Microphone: System Preferences → Security & Privacy → Privacy → Microphone"
            )
        
        return len(permission_requests) == 0, permission_requests
    
    def _check_accessibility_permission(self) -> bool:
        """Check if accessibility permission is granted."""
        try:
            from Quartz import AXIsProcessTrusted
            return AXIsProcessTrusted()
        except ImportError:
            return False
    
    def _check_microphone_permission(self) -> bool:
        """Check if microphone permission is granted."""
        try:
            import sounddevice
            devices = sounddevice.query_devices()
            return len(devices) > 0
        except Exception:
            return False


class PostInstallVerifier:
    """Verifies installation completeness and functionality."""
    
    def __init__(self, config: InstallationConfig, install_dir: Path):
        self.config = config
        self.install_dir = install_dir
        self.logger = logging.getLogger("DictoInstaller.PostInstallVerifier")
    
    def verify_files(self) -> Tuple[bool, List[str]]:
        """Verify all required files are present."""
        required_files = [
            "dicto_main.py",
            "dicto_core.py",
            "audio_processor.py",
            "whisper.cpp/build/bin/main",
            "whisper.cpp/models/ggml-base.en.bin"
        ]
        
        missing_files = []
        for file_path in required_files:
            full_path = self.install_dir / file_path
            if not full_path.exists():
                missing_files.append(str(file_path))
        
        return len(missing_files) == 0, missing_files
    
    def verify_dependencies(self) -> Tuple[bool, List[str]]:
        """Verify all dependencies are properly installed."""
        missing_deps = []
        
        # Check Python packages
        python_packages = [
            "rumps", "pynput", "pydub", "plyer", 
            "AppKit", "sounddevice", "pyaudio"
        ]
        
        for package in python_packages:
            try:
                __import__(package)
            except ImportError:
                missing_deps.append(f"Python package: {package}")
        
        # Check system tools
        system_tools = ["sox", "ffmpeg", "cmake"]
        for tool in system_tools:
            result = subprocess.run(['which', tool], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                missing_deps.append(f"System tool: {tool}")
        
        return len(missing_deps) == 0, missing_deps
    
    def test_functionality(self) -> Tuple[bool, List[str]]:
        """Test basic functionality."""
        test_results = []
        all_passed = True
        
        # Test 1: Import main modules
        try:
            sys.path.insert(0, str(self.install_dir))
            import dicto_core
            test_results.append("✅ Core module import: PASS")
        except Exception as e:
            test_results.append(f"❌ Core module import: FAIL ({e})")
            all_passed = False
        
        # Test 2: Audio system
        try:
            import sounddevice
            devices = sounddevice.query_devices()
            if len(devices) > 0:
                test_results.append("✅ Audio system: PASS")
            else:
                test_results.append("❌ Audio system: FAIL (no devices)")
                all_passed = False
        except Exception as e:
            test_results.append(f"❌ Audio system: FAIL ({e})")
            all_passed = False
        
        # Test 3: Whisper binary
        try:
            whisper_path = self.install_dir / "whisper.cpp/build/bin/main"
            if whisper_path.exists():
                result = subprocess.run([str(whisper_path), "--help"], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    test_results.append("✅ Whisper binary: PASS")
                else:
                    test_results.append("❌ Whisper binary: FAIL (not executable)")
                    all_passed = False
            else:
                test_results.append("❌ Whisper binary: FAIL (not found)")
                all_passed = False
        except Exception as e:
            test_results.append(f"❌ Whisper binary: FAIL ({e})")
            all_passed = False
        
        return all_passed, test_results


class DictoInstaller:
    """Main installer class orchestrating the installation process."""
    
    def __init__(self, unattended: bool = False):
        self.config = InstallationConfig()
        self.unattended = unattended
        self.install_dir = Path.home() / "dicto"
        
        # Setup logging
        self.setup_logging()
        self.logger = logging.getLogger("DictoInstaller")
        
        # Initialize components
        self.system_checker = SystemChecker(self.config)
        self.dependency_resolver = DependencyResolver(self.config)
        self.whisper_setup = WhisperSetup(self.config, self.install_dir)
        self.system_integrator = SystemIntegrator(self.config, self.install_dir)
        self.verifier = PostInstallVerifier(self.config, self.install_dir)
    
    def setup_logging(self):
        """Configure logging for the installer."""
        log_dir = Path.home() / "Library" / "Logs" / "Dicto"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / "installer.log"),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def guided_installation(self) -> bool:
        """Run the guided installation process."""
        print("🎙️  Welcome to Dicto Professional Installer")
        print("=" * 50)
        
        if not self.unattended:
            response = input("Continue with installation? (y/N): ")
            if response.lower() != 'y':
                print("Installation cancelled.")
                return False
        
        # Step 1: System Requirements Check
        print("\n📋 Step 1: Checking System Requirements")
        if not self._check_system_requirements():
            return False
        
        # Step 2: Dependency Resolution
        print("\n📦 Step 2: Resolving Dependencies")
        if not self._resolve_dependencies():
            return False
        
        # Step 3: Install Application Files
        print("\n📁 Step 3: Installing Application Files")
        if not self._install_application_files():
            return False
        
        # Step 4: Setup Whisper.cpp
        print("\n🤖 Step 4: Setting up Whisper.cpp")
        if not self._setup_whisper():
            return False
        
        # Step 5: System Integration
        print("\n🔗 Step 5: System Integration")
        if not self._integrate_with_system():
            return False
        
        # Step 6: Post-Installation Verification
        print("\n✅ Step 6: Post-Installation Verification")
        if not self.post_install_verification():
            return False
        
        print("\n🎉 Installation completed successfully!")
        print("\n📖 Next Steps:")
        print("1. Grant required permissions (if prompted)")
        print("2. Launch Dicto from Applications folder")
        print("3. Test voice transcription with Ctrl+V")
        
        return True
    
    def _check_system_requirements(self) -> bool:
        """Check all system requirements."""
        checks = [
            ("macOS Version", self.system_checker.check_macos_version),
            ("Python Version", self.system_checker.check_python_version),
            ("Homebrew", self.system_checker.check_homebrew),
            ("Xcode Tools", self.system_checker.check_xcode_tools),
            ("Disk Space", self.system_checker.check_disk_space),
            ("Permissions", self.system_checker.check_permissions)
        ]
        
        all_passed = True
        for check_name, check_func in checks:
            try:
                passed, message = check_func()
                status = "✅" if passed else "❌"
                print(f"  {status} {check_name}: {message}")
                if not passed:
                    all_passed = False
            except Exception as e:
                print(f"  ❌ {check_name}: Error - {e}")
                all_passed = False
        
        return all_passed
    
    def _resolve_dependencies(self) -> bool:
        """Resolve and install all dependencies."""
        print("  🔍 Checking Python packages...")
        
        missing_pip = []
        for package in self.dependency_resolver.pip_packages:
            passed, message = self.dependency_resolver.check_pip_package(package)
            if not passed:
                missing_pip.append(package)
                print(f"    📦 {message}")
        
        if missing_pip:
            print(f"  📥 Installing {len(missing_pip)} Python packages...")
            if not self.dependency_resolver.install_pip_packages(missing_pip):
                print("  ❌ Failed to install Python packages")
                return False
        
        print("  🔍 Checking system packages...")
        missing_system = []
        for package in self.dependency_resolver.system_packages:
            passed, message = self.dependency_resolver.check_system_package(package)
            if not passed:
                missing_system.append(package)
                print(f"    🍺 {message}")
        
        if missing_system:
            print(f"  📥 Installing {len(missing_system)} system packages...")
            if not self.dependency_resolver.install_system_packages(missing_system):
                print("  ❌ Failed to install system packages")
                return False
        
        # Check for conflicts
        conflicts = self.dependency_resolver.resolve_conflicts()
        if conflicts:
            print("  ⚠️  Dependency conflicts detected:")
            for conflict in conflicts:
                print(f"    • {conflict}")
        
        return True
    
    def _install_application_files(self) -> bool:
        """Install the main application files."""
        try:
            # Create installation directory
            self.install_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy application files from current directory
            current_dir = Path(__file__).parent
            
            files_to_copy = [
                "dicto_main.py", "dicto_core.py", "audio_processor.py",
                "audio_recorder.py", "continuous_recorder.py", 
                "vocabulary_manager.py", "auto_text_inserter.py",
                "menu_bar_manager.py", "session_manager.py",
                "error_handler.py", "config_manager.py",
                "performance_monitor.py", "requirements.txt"
            ]
            
            copied_files = 0
            for file_name in files_to_copy:
                src_file = current_dir / file_name
                if src_file.exists():
                    dst_file = self.install_dir / file_name
                    shutil.copy2(src_file, dst_file)
                    copied_files += 1
                    print(f"    📄 Copied {file_name}")
            
            print(f"  ✅ Copied {copied_files} application files")
            return True
            
        except Exception as e:
            print(f"  ❌ Failed to install application files: {e}")
            return False
    
    def _setup_whisper(self) -> bool:
        """Setup Whisper.cpp compilation and model download."""
        try:
            # Clone repository
            print("  📥 Cloning Whisper.cpp repository...")
            if not self.whisper_setup.clone_whisper_repo():
                print("  ❌ Failed to clone Whisper.cpp repository")
                return False
            
            # Compile Whisper
            print("  🔨 Compiling Whisper.cpp (this may take a few minutes)...")
            if not self.whisper_setup.compile_whisper():
                print("  ❌ Failed to compile Whisper.cpp")
                return False
            
            # Download model
            print("  📥 Downloading Whisper model...")
            if not self.whisper_setup.download_model():
                print("  ❌ Failed to download Whisper model")
                return False
            
            print("  ✅ Whisper.cpp setup completed")
            return True
            
        except Exception as e:
            print(f"  ❌ Whisper setup failed: {e}")
            return False
    
    def _integrate_with_system(self) -> bool:
        """Integrate with macOS system services."""
        try:
            # Create app bundle
            print("  📱 Creating macOS app bundle...")
            if not self.system_integrator.create_app_bundle():
                print("  ❌ Failed to create app bundle")
                return False
            
            # Create LaunchAgent
            print("  🚀 Creating LaunchAgent...")
            if not self.system_integrator.create_launch_agent():
                print("  ❌ Failed to create LaunchAgent")
                return False
            
            # Register LaunchAgent
            print("  📝 Registering LaunchAgent...")
            if not self.system_integrator.register_launch_agent():
                print("  ⚠️  LaunchAgent registration may require manual action")
            
            # Check permissions
            print("  🔐 Checking permissions...")
            permissions_ok, requests = self.system_integrator.setup_permissions()
            if not permissions_ok:
                print("  ⚠️  Additional permissions required:")
                for request in requests:
                    print(f"    • {request}")
            
            print("  ✅ System integration completed")
            return True
            
        except Exception as e:
            print(f"  ❌ System integration failed: {e}")
            return False
    
    def post_install_verification(self) -> bool:
        """Verify the installation is complete and functional."""
        print("  🔍 Verifying installation files...")
        files_ok, missing_files = self.verifier.verify_files()
        if not files_ok:
            print("  ❌ Missing files:")
            for file_path in missing_files:
                print(f"    • {file_path}")
            return False
        
        print("  🔍 Verifying dependencies...")
        deps_ok, missing_deps = self.verifier.verify_dependencies()
        if not deps_ok:
            print("  ❌ Missing dependencies:")
            for dep in missing_deps:
                print(f"    • {dep}")
            return False
        
        print("  🧪 Testing functionality...")
        func_ok, test_results = self.verifier.test_functionality()
        for result in test_results:
            print(f"    {result}")
        
        if not func_ok:
            print("  ⚠️  Some functionality tests failed")
            return False
        
        print("  ✅ Installation verification completed")
        return True


def main():
    """Main installer entry point."""
    parser = argparse.ArgumentParser(description="Dicto Professional Installer")
    parser.add_argument('--unattended', action='store_true',
                       help='Run installation without user prompts')
    parser.add_argument('--verify', action='store_true',
                       help='Run post-installation verification only')
    
    args = parser.parse_args()
    
    installer = DictoInstaller(unattended=args.unattended)
    
    if args.verify:
        print("🔍 Running post-installation verification...")
        success = installer.post_install_verification()
        sys.exit(0 if success else 1)
    else:
        success = installer.guided_installation()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 