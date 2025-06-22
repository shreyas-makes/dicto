#!/usr/bin/env python3
"""
Dicto Support Tools
Customer support and diagnostics system
"""

import os
import sys
import json
import platform
import subprocess
import tempfile
import zipfile
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging
import psutil
import pkg_resources
from dataclasses import dataclass, asdict

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class SystemInfo:
    """System information structure"""
    os_version: str
    python_version: str
    cpu_model: str
    memory_total: int
    memory_available: int
    disk_space: int
    audio_devices: List[str]
    permissions: Dict[str, bool]

@dataclass
class AppDiagnostics:
    """Application diagnostics structure"""
    version: str
    install_path: str
    config_valid: bool
    dependencies_ok: bool
    whisper_model_available: bool
    hotkey_functional: bool
    audio_recording_ok: bool
    errors: List[str]

class SupportTools:
    """Comprehensive support and diagnostics tools"""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.logs_dir = self.project_root / "logs"
        self.logs_dir.mkdir(exist_ok=True)
        self.support_dir = self.project_root / "support"
        self.support_dir.mkdir(exist_ok=True)
    
    def collect_system_info(self) -> SystemInfo:
        """Collect comprehensive system information"""
        logger.info("Collecting system information...")
        
        try:
            # Get audio devices
            audio_devices = self.get_audio_devices()
            
            # Check permissions
            permissions = self.check_permissions()
            
            return SystemInfo(
                os_version=f"{platform.system()} {platform.release()} ({platform.version()})",
                python_version=platform.python_version(),
                cpu_model=platform.processor() or self.get_cpu_model(),
                memory_total=psutil.virtual_memory().total,
                memory_available=psutil.virtual_memory().available,
                disk_space=psutil.disk_usage('/').free,
                audio_devices=audio_devices,
                permissions=permissions
            )
        except Exception as e:
            logger.error(f"Failed to collect system info: {e}")
            return SystemInfo(
                os_version="Unknown",
                python_version="Unknown",
                cpu_model="Unknown",
                memory_total=0,
                memory_available=0,
                disk_space=0,
                audio_devices=[],
                permissions={}
            )
    
    def get_cpu_model(self) -> str:
        """Get CPU model information"""
        try:
            if platform.system() == "Darwin":
                result = subprocess.run(
                    ["sysctl", "-n", "machdep.cpu.brand_string"],
                    capture_output=True, text=True
                )
                return result.stdout.strip() if result.returncode == 0 else "Unknown"
            return "Unknown"
        except:
            return "Unknown"
    
    def get_audio_devices(self) -> List[str]:
        """Get list of available audio input devices"""
        devices = []
        try:
            # Try using SoX to list devices
            result = subprocess.run(
                ["sox", "--help-format"], 
                capture_output=True, text=True
            )
            if result.returncode == 0:
                devices.append("SoX audio support available")
            
            # Try using system_profiler on macOS
            if platform.system() == "Darwin":
                result = subprocess.run(
                    ["system_profiler", "SPAudioDataType", "-json"],
                    capture_output=True, text=True
                )
                if result.returncode == 0:
                    try:
                        audio_data = json.loads(result.stdout)
                        for item in audio_data.get("SPAudioDataType", []):
                            if "name" in item:
                                devices.append(item["name"])
                    except:
                        pass
        except:
            pass
        
        return devices if devices else ["No audio devices detected"]
    
    def check_permissions(self) -> Dict[str, bool]:
        """Check macOS permissions status"""
        permissions = {}
        
        if platform.system() == "Darwin":
            try:
                # Check microphone permission
                result = subprocess.run([
                    "osascript", "-e",
                    'tell application "System Events" to get microphone authorization status'
                ], capture_output=True, text=True)
                permissions["microphone"] = "authorized" in result.stdout.lower()
                
                # Check accessibility permission
                result = subprocess.run([
                    "osascript", "-e",
                    'tell application "System Events" to get UI elements enabled'
                ], capture_output=True, text=True)
                permissions["accessibility"] = "true" in result.stdout.lower()
                
            except:
                permissions["microphone"] = False
                permissions["accessibility"] = False
        
        return permissions
    
    def run_app_diagnostics(self) -> AppDiagnostics:
        """Run comprehensive application diagnostics"""
        logger.info("Running application diagnostics...")
        
        errors = []
        
        try:
            # Get version
            version = self.get_app_version()
            
            # Check install path
            install_path = str(self.project_root)
            
            # Validate configuration
            config_valid = self.validate_configuration()
            if not config_valid:
                errors.append("Configuration validation failed")
            
            # Check dependencies
            dependencies_ok = self.check_dependencies()
            if not dependencies_ok:
                errors.append("Missing or incompatible dependencies")
            
            # Check Whisper model
            whisper_model_available = self.check_whisper_model()
            if not whisper_model_available:
                errors.append("Whisper model not found or corrupted")
            
            # Test hotkey functionality
            hotkey_functional = self.test_hotkey_system()
            if not hotkey_functional:
                errors.append("Hotkey system not functional")
            
            # Test audio recording
            audio_recording_ok = self.test_audio_recording()
            if not audio_recording_ok:
                errors.append("Audio recording system failed")
            
            return AppDiagnostics(
                version=version,
                install_path=install_path,
                config_valid=config_valid,
                dependencies_ok=dependencies_ok,
                whisper_model_available=whisper_model_available,
                hotkey_functional=hotkey_functional,
                audio_recording_ok=audio_recording_ok,
                errors=errors
            )
            
        except Exception as e:
            logger.error(f"Diagnostics failed: {e}")
            return AppDiagnostics(
                version="Unknown",
                install_path="Unknown",
                config_valid=False,
                dependencies_ok=False,
                whisper_model_available=False,
                hotkey_functional=False,
                audio_recording_ok=False,
                errors=[f"Diagnostics error: {e}"]
            )
    
    def get_app_version(self) -> str:
        """Get application version"""
        try:
            with open("version.txt", 'r') as f:
                return f.read().strip()
        except:
            return "Unknown"
    
    def validate_configuration(self) -> bool:
        """Validate application configuration"""
        try:
            # Check for config file
            config_path = Path("config.json")
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    # Basic validation
                    return isinstance(config, dict)
            return True  # Default config is ok
        except:
            return False
    
    def check_dependencies(self) -> bool:
        """Check if all required dependencies are available"""
        try:
            with open("requirements.txt", 'r') as f:
                requirements = f.read().strip().split('\n')
            
            for requirement in requirements:
                if requirement.strip() and not requirement.startswith('#'):
                    try:
                        pkg_resources.require(requirement.strip())
                    except:
                        return False
            return True
        except:
            return False
    
    def check_whisper_model(self) -> bool:
        """Check if Whisper model is available"""
        model_paths = [
            "whisper.cpp/models/ggml-base.en.bin",
            "whisper.cpp/models/ggml-base.bin",
            "models/ggml-base.en.bin"
        ]
        
        for model_path in model_paths:
            if Path(model_path).exists():
                return True
        return False
    
    def test_hotkey_system(self) -> bool:
        """Test hotkey system functionality"""
        try:
            # Try importing pynput
            import pynput
            return True
        except ImportError:
            return False
        except Exception:
            return False
    
    def test_audio_recording(self) -> bool:
        """Test basic audio recording functionality"""
        try:
            # Check if SoX is available
            result = subprocess.run(
                ["sox", "--version"], 
                capture_output=True, text=True
            )
            return result.returncode == 0
        except:
            return False
    
    def generate_diagnostic_report(self) -> Path:
        """Generate comprehensive diagnostic report"""
        logger.info("Generating diagnostic report...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.support_dir / f"diagnostic_report_{timestamp}.json"
        
        # Collect all diagnostic information
        system_info = self.collect_system_info()
        app_diagnostics = self.run_app_diagnostics()
        logs = self.collect_recent_logs()
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "report_version": "1.0",
            "system_info": asdict(system_info),
            "app_diagnostics": asdict(app_diagnostics),
            "recent_logs": logs,
            "environment": {
                "PATH": os.environ.get("PATH", ""),
                "PYTHONPATH": os.environ.get("PYTHONPATH", ""),
                "HOME": os.environ.get("HOME", ""),
                "USER": os.environ.get("USER", "")
            }
        }
        
        # Save report
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Diagnostic report saved: {report_path}")
        return report_path
    
    def collect_recent_logs(self) -> Dict[str, List[str]]:
        """Collect recent log entries"""
        logs = {}
        
        log_files = [
            "logs/dicto.log",
            "logs/error.log", 
            "logs/performance.log",
            "logs/diagnostic_report.txt"
        ]
        
        for log_file in log_files:
            log_path = Path(log_file)
            if log_path.exists():
                try:
                    with open(log_path, 'r') as f:
                        lines = f.readlines()
                        # Get last 50 lines
                        recent_lines = lines[-50:] if len(lines) > 50 else lines
                        logs[log_file] = [line.strip() for line in recent_lines]
                except:
                    logs[log_file] = ["Error reading log file"]
        
        return logs
    
    def create_support_package(self) -> Path:
        """Create comprehensive support package"""
        logger.info("Creating support package...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        package_path = self.support_dir / f"dicto_support_package_{timestamp}.zip"
        
        with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add diagnostic report
            report_path = self.generate_diagnostic_report()
            zipf.write(report_path, report_path.name)
            
            # Add configuration files
            config_files = [
                "config.json",
                "version.txt",
                "requirements.txt"
            ]
            
            for config_file in config_files:
                config_path = Path(config_file)
                if config_path.exists():
                    zipf.write(config_path, config_file)
            
            # Add recent logs
            for log_file in self.logs_dir.glob("*.log"):
                zipf.write(log_file, f"logs/{log_file.name}")
            
            # Add system information
            system_info_path = self.support_dir / "system_info.txt"
            with open(system_info_path, 'w') as f:
                f.write(self.generate_system_info_text())
            zipf.write(system_info_path, "system_info.txt")
            
            # Clean up temporary files
            system_info_path.unlink()
        
        logger.info(f"Support package created: {package_path}")
        return package_path
    
    def generate_system_info_text(self) -> str:
        """Generate human-readable system information"""
        system_info = self.collect_system_info()
        
        return f"""Dicto Support Information
========================

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

System Information:
- OS: {system_info.os_version}
- Python: {system_info.python_version}
- CPU: {system_info.cpu_model}
- Memory: {system_info.memory_total // (1024**3)} GB total, {system_info.memory_available // (1024**3)} GB available
- Disk Space: {system_info.disk_space // (1024**3)} GB free

Audio Devices:
{chr(10).join(f'- {device}' for device in system_info.audio_devices)}

Permissions:
{chr(10).join(f'- {perm}: {"✓" if status else "✗"}' for perm, status in system_info.permissions.items())}

Application Diagnostics:
- Version: {self.get_app_version()}
- Install Path: {self.project_root}
- Dependencies: {"✓" if self.check_dependencies() else "✗"}
- Whisper Model: {"✓" if self.check_whisper_model() else "✗"}
- Audio Recording: {"✓" if self.test_audio_recording() else "✗"}
"""
    
    def run_health_check(self) -> bool:
        """Run quick health check"""
        logger.info("Running health check...")
        
        checks = [
            ("Configuration", self.validate_configuration()),
            ("Dependencies", self.check_dependencies()),
            ("Whisper Model", self.check_whisper_model()),
            ("Audio System", self.test_audio_recording()),
            ("Hotkey System", self.test_hotkey_system())
        ]
        
        all_passed = True
        print("\nDicto Health Check Results:")
        print("=" * 30)
        
        for check_name, result in checks:
            status = "✓ PASS" if result else "✗ FAIL"
            print(f"{check_name:<20} {status}")
            if not result:
                all_passed = False
        
        print("=" * 30)
        overall_status = "✓ HEALTHY" if all_passed else "⚠ ISSUES DETECTED"
        print(f"Overall Status: {overall_status}")
        
        return all_passed
    
    def fix_common_issues(self):
        """Attempt to fix common issues automatically"""
        logger.info("Attempting to fix common issues...")
        
        fixes_applied = []
        
        # Fix 1: Install missing dependencies
        if not self.check_dependencies():
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                             check=True)
                fixes_applied.append("Reinstalled Python dependencies")
            except:
                logger.error("Failed to install dependencies")
        
        # Fix 2: Download missing Whisper model
        if not self.check_whisper_model():
            try:
                model_script = Path("whisper.cpp/models/download-ggml-model.sh")
                if model_script.exists():
                    subprocess.run(["bash", str(model_script), "base.en"], check=True)
                    fixes_applied.append("Downloaded missing Whisper model")
            except:
                logger.error("Failed to download Whisper model")
        
        # Fix 3: Reset configuration to defaults
        if not self.validate_configuration():
            try:
                default_config = {
                    "hotkey": "cmd+v",
                    "model": "base.en",
                    "audio_device": "default"
                }
                with open("config.json", 'w') as f:
                    json.dump(default_config, f, indent=2)
                fixes_applied.append("Reset configuration to defaults")
            except:
                logger.error("Failed to reset configuration")
        
        if fixes_applied:
            print("\nAutomated fixes applied:")
            for fix in fixes_applied:
                print(f"- {fix}")
        else:
            print("\nNo automated fixes available.")
    
    def start_remote_support_session(self):
        """Start remote support session (placeholder)"""
        logger.info("Starting remote support session...")
        
        # Generate session ID
        session_id = f"dicto_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create support package
        package_path = self.create_support_package()
        
        print(f"\nRemote Support Session Started")
        print(f"Session ID: {session_id}")
        print(f"Support Package: {package_path}")
        print("\nPlease provide this information to support:")
        print(f"- Session ID: {session_id}")
        print(f"- Package Location: {package_path}")
        
        return session_id, package_path

def main():
    """Main support tools interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Dicto Support Tools")
    parser.add_argument("--health-check", action="store_true", 
                       help="Run health check")
    parser.add_argument("--diagnostics", action="store_true", 
                       help="Generate diagnostic report")
    parser.add_argument("--support-package", action="store_true", 
                       help="Create support package")
    parser.add_argument("--fix-issues", action="store_true", 
                       help="Attempt to fix common issues")
    parser.add_argument("--remote-support", action="store_true", 
                       help="Start remote support session")
    
    args = parser.parse_args()
    
    support = SupportTools()
    
    if args.health_check:
        support.run_health_check()
    elif args.diagnostics:
        report_path = support.generate_diagnostic_report()
        print(f"Diagnostic report generated: {report_path}")
    elif args.support_package:
        package_path = support.create_support_package()
        print(f"Support package created: {package_path}")
    elif args.fix_issues:
        support.fix_common_issues()
    elif args.remote_support:
        support.start_remote_support_session()
    else:
        # Interactive mode
        print("Dicto Support Tools")
        print("=" * 20)
        print("1. Health Check")
        print("2. Generate Diagnostics")
        print("3. Create Support Package")
        print("4. Fix Common Issues")
        print("5. Remote Support Session")
        
        choice = input("\nSelect option (1-5): ").strip()
        
        if choice == "1":
            support.run_health_check()
        elif choice == "2":
            report_path = support.generate_diagnostic_report()
            print(f"Diagnostic report generated: {report_path}")
        elif choice == "3":
            package_path = support.create_support_package()
            print(f"Support package created: {package_path}")
        elif choice == "4":
            support.fix_common_issues()
        elif choice == "5":
            support.start_remote_support_session()
        else:
            print("Invalid option")

if __name__ == "__main__":
    main() 