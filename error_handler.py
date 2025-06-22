import logging
import logging.handlers
import os
import sys
import platform
import traceback
import time
import shutil
from pathlib import Path
from typing import Optional, Dict, Any

class ErrorHandler:
    """
    Centralized error handling, logging, and diagnostics for Dicto.
    """

    def __init__(self, log_dir: str = "logs", log_level=logging.INFO):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.log_file = self.log_dir / "dicto.log"
        self.log_level = log_level
        self.logger = self.setup_logging()

    def setup_logging(self) -> logging.Logger:
        """
        Set up sophisticated logging with rotating file and console output.
        """
        logger = logging.getLogger("Dicto")
        logger.setLevel(self.log_level)

        # Prevent duplicate handlers if called multiple times
        if logger.hasHandlers():
            logger.handlers.clear()

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        # Rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            self.log_file, maxBytes=5 * 1024 * 1024, backupCount=3
        )
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - [%(threadName)s] - %(message)s (%(filename)s:%(lineno)d)"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        # Set up a global exception hook
        sys.excepthook = self.handle_exception

        logger.info("Logging initialized.")
        return logger

    def handle_exception(self, exc_type, exc_value, exc_traceback):
        """
        Global exception hook to catch unhandled exceptions.
        """
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        self.logger.critical(f"Unhandled exception:\n{error_msg}")
        # Here you could add a call to a user-facing error dialog
        
    def handle_system_errors(self, error_type: str, details: Dict[str, Any]):
        """
        Handle specific macOS-related system errors.
        Placeholder for now.
        """
        self.logger.error(f"System Error: {error_type} - {details}")
        # E.g., for permission errors, guide user to System Settings.

    def recover_from_crash(self) -> Optional[Dict[str, Any]]:
        """
        Restore application state from a session file after a crash.
        Placeholder for now.
        """
        self.logger.info("Attempting to recover from previous session...")
        # This would interact with a session manager
        return None

    def generate_diagnostic_report(self) -> str:
        """
        Generate a comprehensive diagnostic report for troubleshooting.
        """
        self.logger.info("Generating diagnostic report...")
        report = []
        report.append("="*20 + " Dicto Diagnostic Report " + "="*20)
        report.append(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Python Version: {sys.version}")
        report.append(f"Platform: {platform.platform()}")
        report.append(f"macOS Version: {platform.mac_ver()[0]}")
        
        report.append("\n--- System Health ---")
        health_checks = self.check_system_health()
        for check, status in health_checks.items():
            report.append(f"{check}: {status}")

        report.append("\n--- Recent Log Entries ---")
        try:
            with open(self.log_file, "r") as f:
                lines = f.readlines()
                report.extend(lines[-50:]) # Last 50 lines
        except Exception as e:
            report.append(f"Could not read log file: {e}")
        
        report.append("="*55)
        
        report_str = "\n".join(report)
        
        report_path = self.log_dir / "diagnostic_report.txt"
        with open(report_path, "w") as f:
            f.write(report_str)
            
        self.logger.info(f"Diagnostic report saved to {report_path}")
        return str(report_path)

    def check_system_health(self) -> Dict[str, str]:
        """
        Perform proactive checks for common issues.
        """
        health = {}
        # Check accessibility permissions (very basic check)
        # A more robust check would involve trying to use an accessibility feature
        health["Accessibility ( अनुमान )"] = "Potentially OK (cannot verify programmatically)"
        
        # Check for whisper model files (placeholder paths)
        whisper_path = Path("./whisper.cpp/ggml-base.en.bin") # Example
        health["Whisper Model"] = "Found" if whisper_path.exists() else "Not Found"
        
        # Check disk space
        try:
            total, used, free = shutil.disk_usage("/")
            free_gb = free // (2**30)
            health["Free Disk Space"] = f"{free_gb} GB"
            if free_gb < 1:
                health["Disk Space Warning"] = "Low disk space!"
        except Exception as e:
            health["Disk Space"] = f"Error checking disk space: {e}"

        return health

if __name__ == '__main__':
    # Example usage
    handler = ErrorHandler()
    logging.info("This is an info message.")
    logging.warning("This is a warning.")
    
    handler.generate_diagnostic_report()

    # Test exception hook
    # raise ValueError("This is a test exception to check the hook.") 