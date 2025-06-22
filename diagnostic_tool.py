import platform
import shutil
import sys
from pathlib import Path

class DiagnosticTool:
    """
    Provides tools for system health checks and troubleshooting for Dicto.
    """

    def __init__(self, whisper_model_path: str = "./whisper.cpp/models/ggml-base.en.bin"):
        self.whisper_model_path = Path(whisper_model_path)

    def check_system_health(self) -> dict:
        """
        Performs a series of checks for common issues.
        """
        health_report = {
            "macOS Version": self.check_macos_version(),
            "Disk Space": self.check_disk_space(),
            "Whisper Model": self.check_whisper_model(),
            "Accessibility Permissions": self.check_accessibility_permissions(),
        }
        return health_report

    def check_macos_version(self) -> str:
        """Checks if the macOS version is compatible."""
        try:
            version = platform.mac_ver()[0]
            if list(map(int, version.split('.'))) < [10, 15]:
                return f"Warning: macOS version {version} is older than 10.15 (Catalina). Some features may not work."
            return f"OK ({version})"
        except Exception as e:
            return f"Error checking macOS version: {e}"

    def check_disk_space(self) -> str:
        """Checks for sufficient free disk space."""
        try:
            total, used, free = shutil.disk_usage("/")
            free_gb = free / (1024 ** 3)
            if free_gb < 2:
                return f"Warning: Low disk space ({free_gb:.2f} GB free)."
            return f"OK ({free_gb:.2f} GB free)"
        except Exception as e:
            return f"Error checking disk space: {e}"

    def check_whisper_model(self) -> str:
        """Checks if the Whisper model file exists."""
        if self.whisper_model_path.is_file():
            return f"OK (Found at {self.whisper_model_path})"
        return f"Error: Model file not found at {self.whisper_model_path}"

    def check_accessibility_permissions(self) -> str:
        """
        Checks for macOS accessibility permissions.
        This is a placeholder as a definitive check is complex from a script.
        """
        # This is a best-effort check. A true test is to try an accessibility-requiring action.
        return "Needs manual verification. Go to System Settings > Privacy & Security > Accessibility."

def main():
    """Run the diagnostic tool and print a report."""
    print("Running Dicto Diagnostic Tool...")
    tool = DiagnosticTool()
    report = tool.check_system_health()

    print("\n--- Dicto System Health Report ---")
    for check, status in report.items():
        print(f"- {check}: {status}")
    print("---------------------------------\n")
    
    # Provide a summary
    if any("Error" in status for status in report.values()):
        print("🔴 Found one or more errors. Please address them.")
    elif any("Warning" in status for status in report.values()):
        print("🟡 Found one or more warnings. Review them for optimal performance.")
    else:
        print("✅ System health looks good.")


if __name__ == "__main__":
    main() 