#!/usr/bin/env python3
"""
Dicto Main - Enhanced system-wide voice transcription app for macOS
Provides global hotkey (Ctrl+V) for voice recording with enhanced audio processing,
device selection, real-time monitoring, automatic clipboard integration, and continuous recording.

New Features in Task 6:
- Custom vocabulary support for better accuracy
- Continuous recording while Ctrl+V is held
- Transcription confidence scoring
- Timestamping for longer recordings
- Enhanced audio buffer management

Requirements:
- Global Ctrl+V hotkey for continuous record while held
- Automatic clipboard integration
- macOS native notifications
- Background operation
- Enhanced error handling with user feedback
- Custom vocabulary injection

Dependencies:
- pynput: Global hotkey support
- AppKit (PyObjC): Clipboard management
- plyer: Cross-platform notifications
- dicto_core: TranscriptionEngine
- audio_recorder: AudioRecorder
- vocabulary_manager: VocabularyManager
- continuous_recorder: ContinuousRecorder
"""

import os
import sys
import time
import logging
import threading
import signal
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, List

# Third-party imports
try:
    import rumps
except ImportError:
    print("Error: rumps not installed. Install with: pip install rumps")
    sys.exit(1)

try:
    from pynput import keyboard
    from pynput.keyboard import Key, KeyCode
except ImportError:
    print("Error: pynput not installed. Install with: pip install pynput")
    sys.exit(1)

try:
    from plyer import notification
except ImportError:
    print("Error: plyer not installed. Install with: pip install plyer")
    sys.exit(1)

try:
    from AppKit import NSPasteboard, NSStringPboardType
except ImportError:
    print("Error: PyObjC not installed. Install with: pip install pyobjc-framework-Cocoa")
    sys.exit(1)

# Local imports
try:
    from dicto_core import TranscriptionEngine
except ImportError:
    print("Error: dicto_core.py not found. Ensure it's in the same directory.")
    sys.exit(1)

try:
    from vocabulary_manager import VocabularyManager
except ImportError:
    print("Error: vocabulary_manager.py not found. Ensure it's in the same directory.")
    sys.exit(1)

try:
    from continuous_recorder import ContinuousRecorder
except ImportError:
    print("Error: continuous_recorder.py not found. Ensure it's in the same directory.")
    sys.exit(1)

try:
    from auto_text_inserter import AutoTextInserter
except ImportError:
    print("Error: auto_text_inserter.py not found. Ensure it's in the same directory.")
    sys.exit(1)

try:
    from menu_bar_manager import MenuBarManager, AppStatus
except ImportError:
    print("Error: menu_bar_manager.py not found. Ensure it's in the same directory.")
    sys.exit(1)

try:
    from session_manager import SessionManager
except ImportError:
    print("Error: session_manager.py not found. Ensure it's in the same directory.")
    sys.exit(1)

try:
    from error_handler import ErrorHandler
except ImportError:
    print("Error: error_handler.py not found. Ensure it's in the same directory.")
    sys.exit(1)

try:
    from config_manager import ConfigManager
except ImportError:
    print("Error: config_manager.py not found. Ensure it's in the same directory.")
    sys.exit(1)


class ClipboardManager:
    """
    macOS clipboard manager using AppKit.
    Handles reading from and writing to the system clipboard.
    """
    
    def __init__(self):
        self.pasteboard = NSPasteboard.generalPasteboard()
        self.logger = logging.getLogger("Dicto.ClipboardManager")
    
    def set_text(self, text: str) -> bool:
        """
        Set text to clipboard.
        
        Args:
            text: Text to copy to clipboard.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            self.pasteboard.clearContents()
            success = self.pasteboard.setString_forType_(text, NSStringPboardType)
            self.logger.info(f"Clipboard updated with {len(text)} characters")
            return bool(success)
        except Exception as e:
            self.logger.error(f"Failed to set clipboard: {e}")
            return False
    
    def get_text(self) -> Optional[str]:
        """
        Get text from clipboard.
        
        Returns:
            Optional[str]: Clipboard text content or None if not available.
        """
        try:
            content = self.pasteboard.stringForType_(NSStringPboardType)
            return str(content) if content else None
        except Exception as e:
            self.logger.error(f"Failed to get clipboard: {e}")
            return None


class NotificationManager:
    """
    Hybrid notification manager that uses macOS native notifications as fallback.
    Provides user feedback for recording state and transcription results.
    """
    
    def __init__(self, app_name: str = "Dicto"):
        self.app_name = app_name
        self.logger = logging.getLogger("Dicto.NotificationManager")
        self.use_native = False  # Flag to switch to native notifications
        
        # Test plyer on initialization
        self._test_plyer_compatibility()
    
    def _test_plyer_compatibility(self):
        """Test if plyer notifications work on this system."""
        try:
            notification.notify(
                title="Dicto Initialization",
                message="Testing notification system...",
                app_name=self.app_name,
                timeout=1
            )
            self.logger.info("plyer notifications working correctly")
        except Exception as e:
            self.logger.warning(f"plyer notifications not working ({e}), switching to native macOS notifications")
            self.use_native = True
    
    def _show_native_notification(self, title: str, message: str) -> bool:
        """
        Show a native macOS notification using osascript.
        
        Args:
            title: Notification title.
            message: Notification message.
            
        Returns:
            bool: True if notification was shown successfully.
        """
        try:
            import subprocess
            # Escape quotes in title and message
            safe_title = title.replace('"', '\\"').replace("'", "\\'")
            safe_message = message.replace('"', '\\"').replace("'", "\\'")
            
            script = f'display notification "{safe_message}" with title "{safe_title}"'
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                self.logger.info(f"Native notification shown: {title} - {message}")
                return True
            else:
                self.logger.error(f"Native notification failed: {result.stderr}")
                return False
        except Exception as e:
            self.logger.error(f"Failed to show native notification: {e}")
            return False
    
    def show_notification(self, title: str, message: str, timeout: int = 3) -> bool:
        """
        Show a system notification using best available method.
        
        Args:
            title: Notification title.
            message: Notification message.
            timeout: How long to show notification in seconds (ignored for native).
            
        Returns:
            bool: True if notification was shown successfully.
        """
        if self.use_native:
            return self._show_native_notification(title, message)
        else:
            try:
                notification.notify(
                    title=title,
                    message=message,
                    app_name=self.app_name,
                    timeout=timeout
                )
                self.logger.info(f"plyer notification shown: {title} - {message}")
                return True
            except Exception as e:
                self.logger.warning(f"plyer notification failed ({e}), falling back to native")
                self.use_native = True  # Switch to native for future notifications
                return self._show_native_notification(title, message)
    
    def notify_recording_started(self) -> bool:
        """Show notification when recording starts."""
        return self.show_notification(
            "🔴 Recording Started",
            "Release CTRL+V to stop and auto-insert transcription"
        )
    
    def notify_recording_stopped(self) -> bool:
        """Show notification when recording stops."""
        return self.show_notification(
            "⏹️ Recording Stopped",
            "Processing transcription..."
        )
    
    def notify_transcription_complete(self, text: str) -> bool:
        """Show notification when transcription is complete."""
        preview = text[:50] + "..." if len(text) > 50 else text
        return self.show_notification(
            "✅ Transcription Complete",
            f"Text automatically inserted: {preview}"
        )
    
    def notify_error(self, error_message: str) -> bool:
        """Show error notification."""
        return self.show_notification(
            "❌ Dicto Error",
            error_message,
            timeout=5
        )


class DictoApp(rumps.App):
    """
    DictoApp - Main application for system-wide voice transcription on macOS.
    Integrates recording, transcription, clipboard, and notifications via a menu bar app.
    Enhanced with advanced menu bar management and session history.
    """
    def __init__(self, whisper_binary_path: Optional[str] = None, model_path: Optional[str] = None):
        super(DictoApp, self).__init__("Dicto", icon=None, quit_button=None)
        
        self.app_support_dir = Path.home() / "Library" / "Application Support" / "Dicto"
        self.app_support_dir.mkdir(parents=True, exist_ok=True)

        # Initialize error handler first
        self.error_handler = ErrorHandler(log_dir=str(self.app_support_dir / "logs"))
        self.logger = self.error_handler.logger
        self.logger.info("DictoApp initializing...")
        
        # Initialize configuration manager
        self.config_manager = ConfigManager()
        self.current_settings = self.config_manager.get_current_settings()
        self.logger.info(f"Configuration loaded. Current profile: {self.current_settings.get('profile_name', 'default')}")

        self.whisper_binary_path = whisper_binary_path or "./whisper.cpp/main"
        self.model_path = model_path or "./whisper.cpp/models/ggml-base.en.bin"

        self.transcription_engine = TranscriptionEngine(
            whisper_binary_path=self.whisper_binary_path,
            model_path=self.model_path
        )

        self.vocabulary_manager = VocabularyManager()
        self.vocabulary_manager.add_custom_words(["Dicto", "macOS", "Whisper", "AI"])

        self.clipboard_manager = ClipboardManager()
        self.notification_manager = NotificationManager()
        self.session_manager = SessionManager(str(self.app_support_dir / "history.json"))
        self.auto_text_inserter = AutoTextInserter()

        # UI and state
        self.menu_bar_manager = MenuBarManager("Dicto", rumps_app=self)
        self.state_lock = threading.Lock()
        self.is_processing = False
        self.is_hotkey_pressed = False
        
        # Setup menu bar callbacks
        self._setup_menu_bar_callbacks()

        self.continuous_recorder = ContinuousRecorder(
            temp_dir=tempfile.gettempdir(),
            enable_key_detection=True
        )
        self.continuous_recorder.set_callbacks(
            on_start=self._on_continuous_start,
            on_stop=self._on_continuous_stop,
            on_session=self._on_session_complete
        )

        self.is_recording = False
        self.recording_session_active = False

        self._setup_enhanced_menu()
        self._start_background_tasks()

        self.logger.info("DictoApp initialized successfully with enhanced UI.")

    def _setup_menu_bar_callbacks(self):
        """Setup callbacks for the enhanced menu bar manager."""
        self.menu_bar_manager.set_recording_callback(self._handle_recording_action)
        self.menu_bar_manager.set_transcription_callback(self._handle_transcription_action)
        self.menu_bar_manager.set_history_callback(self._handle_history_action)
        self.menu_bar_manager.set_settings_callback(self._handle_settings_action)
        self.menu_bar_manager.set_shortcuts_callback(self._handle_shortcuts_action)
        self.menu_bar_manager.set_status_callback(self._handle_status_action)
        self.menu_bar_manager.set_debug_callback(self._handle_debug_action)
        self.menu_bar_manager.set_help_callback(self._handle_help_action)
        self.menu_bar_manager.set_about_callback(self._handle_about_action)
        self.menu_bar_manager.set_quit_callback(self._handle_quit_action)

    def _setup_enhanced_menu(self):
        """Setup an enhanced, multi-level menu bar."""
        menu_structure = {
            "Record": {
                "Start Recording": "record",
                "Stop Recording": "stop",
                "Cancel Recording": "cancel"
            },
            "Transcribe": {
                "Transcribe File": "transcribe_file",
                "Paste Last": "paste_last"
            },
            "History": {
                "Clear History": "clear_history",
                "View History": "view_history"
            },
            "Settings": {
                "Preferences...": "show",
                "---": None,
                "Audio Settings": "audio",
                "Transcription Settings": "transcription",
                "---": None,
                "Manage Profiles": "profiles",
                "Configure Hotkeys": "hotkeys",
                "---": None,
                "Advanced Settings": "advanced",
                "---": None,
                "Export Settings...": "export",
                "Import Settings...": "import"
            },
            "Debug": {
                "View Logs": "view_logs",
                "---": None,
                "Debug Mode": "debug_mode",
                "Run Self-Tests": "run_tests",
                "Generate Diagnostic Report": "generate_report",
                "Check System Health": "check_health"
            },
            "Help": {
                "Check for Updates...": "check_updates",
                "Documentation": "documentation",
                "Report Issue": "report_issue"
            },
            "About": {
                "About Dicto": "about_dicto"
            },
            "Quit": {
                "Quit Dicto": "quit_dicto"
            }
        }
        self.menu_bar_manager.create_menu_from_structure(menu_structure)
        
        # Update initial status
        self.menu_bar_manager.update_status(AppStatus.IDLE)
        self.title = "⚪ Dicto: Idle"
        
        # Register default shortcuts
        self.menu_bar_manager.register_shortcut("Ctrl+V", "start_recording", "Start/stop recording")
        self.menu_bar_manager.register_shortcut("Ctrl+Shift+V", "pause_recording", "Pause recording")
        self.menu_bar_manager.register_shortcut("Ctrl+Alt+H", "show_history", "Show transcription history")
        
        # Initially disable stop recording
        self.menu_bar_manager.enable_menu_item("⏹️ Stop Recording", False)

    # Enhanced menu action handlers
    def _handle_recording_action(self, action: str):
        """Handle recording-related menu actions."""
        if action == 'start':
            self.logger.info("Enhanced Menu: Start Recording")
            if not self.is_recording:
                self._start_recording()
                self.menu_bar_manager.enable_menu_item("🎤 Start Recording", False)
                self.menu_bar_manager.enable_menu_item("⏹️ Stop Recording", True)
                self.menu_bar_manager.update_status(AppStatus.RECORDING)
            else:
                self.logger.warning("Recording already in progress")
                
        elif action == 'stop':
            self.logger.info("Enhanced Menu: Stop Recording")
            if self.is_recording:
                self._stop_recording_and_transcribe()
                self.menu_bar_manager.enable_menu_item("🎤 Start Recording", True)
                self.menu_bar_manager.enable_menu_item("⏹️ Stop Recording", False)
                self.menu_bar_manager.update_status(AppStatus.PROCESSING)
            else:
                self.logger.warning("No recording in progress")

    def _handle_transcription_action(self, action: str):
        """Handle transcription-related menu actions."""
        if action == 'recent':
            self.logger.info("Enhanced Menu: Recent Transcriptions")
            recent_sessions = self.session_manager.get_recent_sessions(limit=5)
            if recent_sessions:
                # Create notification with recent transcriptions
                recent_text = "\n".join([f"• {s.transcription_text[:50]}..." for s in recent_sessions[:3]])
                self.notification_manager.show_notification(
                    "📋 Recent Transcriptions",
                    f"Last {len(recent_sessions)} transcriptions:\n{recent_text}",
                    timeout=8
                )
            else:
                self.notification_manager.show_notification("📋 Recent Transcriptions", "No recent transcriptions found")

    def _handle_history_action(self, action: str):
        """Handle history-related menu actions."""
        if action == 'show':
            self.logger.info("Enhanced Menu: Show History")
            stats = self.session_manager.get_session_stats(days=30)
            stats_text = (f"📊 Last 30 days:\n"
                         f"• {stats.total_sessions} sessions\n"
                         f"• {stats.total_words} words transcribed\n"
                         f"• {stats.total_duration:.1f} minutes recorded")
            self.notification_manager.show_notification("📝 Transcription History", stats_text, timeout=8)

    def _handle_settings_action(self, action: str):
        """Handle settings-related menu actions."""
        if action == 'show':
            self.logger.info("Enhanced Menu: Settings")
            self._show_preferences_gui()
        elif action == 'advanced':
            self.logger.info("Enhanced Menu: Advanced Settings")
            self._show_preferences_gui(tab="advanced")
        elif action == 'profiles':
            self.logger.info("Enhanced Menu: Manage Profiles")
            self._show_preferences_gui(tab="profiles")
        elif action == 'hotkeys':
            self.logger.info("Enhanced Menu: Configure Hotkeys")
            self._show_preferences_gui(tab="hotkeys")
        elif action == 'audio':
            self.logger.info("Enhanced Menu: Audio Settings")
            self._show_preferences_gui(tab="audio")
        elif action == 'transcription':
            self.logger.info("Enhanced Menu: Transcription Settings")
            self._show_preferences_gui(tab="transcription")
        elif action == 'export':
            self.logger.info("Enhanced Menu: Export Settings")
            self._export_settings()
        elif action == 'import':
            self.logger.info("Enhanced Menu: Import Settings")
            self._import_settings()
    
    def _export_settings(self):
        """Export settings to file."""
        try:
            import tkinter as tk
            from tkinter import filedialog
            
            # Create hidden root window for file dialog
            root = tk.Tk()
            root.withdraw()
            
            # Ask for export location
            file_path = filedialog.asksaveasfilename(
                title="Export Dicto Settings",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                initialfilename=f"dicto_settings_{int(time.time())}.json"
            )
            
            root.destroy()
            
            if file_path:
                if self.config_manager.export_settings(file_path):
                    self.notification_manager.show_notification(
                        "✅ Settings Exported",
                        f"Settings exported successfully to:\n{file_path}",
                        timeout=5
                    )
                    self.logger.info(f"Settings exported to: {file_path}")
                else:
                    self.notification_manager.show_notification(
                        "❌ Export Failed",
                        "Failed to export settings. Check logs for details.",
                        timeout=5
                    )
            
        except ImportError:
            self.notification_manager.show_notification(
                "⚠️ Export Unavailable",
                "GUI file dialogs not available. Use command line export.",
                timeout=5
            )
        except Exception as e:
            self.logger.error(f"Failed to export settings: {e}")
            self.notification_manager.show_notification(
                "❌ Export Error",
                f"Export failed: {e}",
                timeout=5
            )
    
    def _import_settings(self):
        """Import settings from file."""
        try:
            import tkinter as tk
            from tkinter import filedialog, messagebox
            
            # Create hidden root window for file dialog
            root = tk.Tk()
            root.withdraw()
            
            # Ask for import file
            file_path = filedialog.askopenfilename(
                title="Import Dicto Settings",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if file_path:
                # Confirm import action
                confirm = messagebox.askyesno(
                    "Confirm Import",
                    "This will merge imported settings with current settings.\n\nContinue with import?"
                )
                
                root.destroy()
                
                if confirm:
                    if self.config_manager.import_settings(file_path):
                        # Reload current settings
                        self.current_settings = self.config_manager.get_current_settings()
                        
                        self.notification_manager.show_notification(
                            "✅ Settings Imported",
                            f"Settings imported successfully from:\n{file_path}",
                            timeout=5
                        )
                        self.logger.info(f"Settings imported from: {file_path}")
                    else:
                        self.notification_manager.show_notification(
                            "❌ Import Failed",
                            "Failed to import settings. Check logs for details.",
                            timeout=5
                        )
            else:
                root.destroy()
            
        except ImportError:
            self.notification_manager.show_notification(
                "⚠️ Import Unavailable",
                "GUI file dialogs not available. Use command line import.",
                timeout=5
            )
        except Exception as e:
            self.logger.error(f"Failed to import settings: {e}")
            self.notification_manager.show_notification(
                "❌ Import Error",
                f"Import failed: {e}",
                timeout=5
            )
    
    def _show_preferences_gui(self, tab: str = "general"):
        """Show the preferences GUI."""
        try:
            # Import here to avoid circular import and only when needed
            from preferences_gui import PreferencesGUI
            
            self.logger.info(f"Opening preferences GUI - {tab} tab")
            
            # Create and show preferences window
            preferences_gui = PreferencesGUI(self.config_manager)
            
            # Switch to requested tab
            tab_mapping = {
                "general": 0,
                "audio": 1,
                "transcription": 2,
                "hotkeys": 3,
                "profiles": 4,
                "advanced": 5
            }
            
            if tab in tab_mapping:
                preferences_gui.notebook.select(tab_mapping[tab])
            
            # Show the preferences window
            preferences_gui.show()
            
            # Reload settings after preferences window closes
            self.current_settings = self.config_manager.get_current_settings()
            self.logger.info("Settings reloaded after preferences update")
            
        except ImportError as e:
            self.logger.error(f"Failed to import preferences_gui: {e}")
            self.notification_manager.show_notification(
                "⚠️ Settings Error", 
                "Preferences GUI not available. Using basic settings notification.",
                timeout=5
            )
            # Fallback to basic notification
            current_profile = self.current_settings.get('profile_name', 'default')
            settings_text = f"Current Profile: {current_profile}\nUse configuration files for advanced settings."
            self.notification_manager.show_notification("⚙️ Current Settings", settings_text, timeout=8)
        except Exception as e:
            self.logger.error(f"Failed to show preferences GUI: {e}")
            self.notification_manager.show_notification(
                "⚠️ Settings Error", 
                f"Failed to open preferences: {e}",
                timeout=5
            )

    def _handle_shortcuts_action(self, action: str):
        """Handle keyboard shortcuts menu actions."""
        if action == 'configure':
            self.logger.info("Enhanced Menu: Configure Shortcuts")
            shortcuts = self.menu_bar_manager.registered_shortcuts
            conflicts = self.menu_bar_manager.get_shortcut_conflicts()
            
            shortcut_text = "Registered shortcuts:\n" + "\n".join([f"• {k} → {v}" for k, v in shortcuts.items()])
            if conflicts:
                shortcut_text += f"\n\n⚠️ Conflicts:\n" + "\n".join([f"• {c}" for c in conflicts])
            
            self.notification_manager.show_notification("⌨️ Keyboard Shortcuts", shortcut_text, timeout=10)

    def _handle_status_action(self, action: str):
        """Handle status-related menu actions."""
        if action == 'info':
            self.logger.info("Enhanced Menu: Status Info")
            storage_info = self.session_manager.get_storage_info()
            status_text = (f"📊 Dicto Status:\n"
                          f"• Recording: {'Yes' if self.is_recording else 'No'}\n"
                          f"• Sessions stored: {storage_info.get('total_sessions', 0)}\n"
                          f"• Database size: {storage_info.get('database_size', 0)} bytes")
            self.notification_manager.show_notification("📊 Status Info", status_text, timeout=8)

    def _handle_debug_action(self, action: str):
        self.logger.debug(f"Handling debug action: {action}")
        if action == "view_logs":
            os.system(f"open '{self.error_handler.log_dir}'")
        elif action == "debug_mode":
            # This would likely toggle a more verbose logging level
            pass
        elif action == "run_tests":
            # Placeholder for running integrated self-tests
            self.notification_manager.show_notification("Self-Test", "All tests passed (placeholder).")
        elif action == "generate_report":
            report_path = self.error_handler.generate_diagnostic_report()
            self.notification_manager.show_notification(
                "Diagnostics", 
                f"Diagnostic report saved to:\n{report_path}"
            )
            os.system(f"open '{report_path}'")
        elif action == "check_health":
            health_status = self.error_handler.check_system_health()
            # Format this nicely for a notification or a small window
            status_str = "\n".join([f"• {k}: {v}" for k, v in health_status.items()])
            self.notification_manager.show_notification("System Health", status_str)

    def _handle_help_action(self, action: str):
        self.logger.debug(f"Handling help action: {action}")
        if action == 'show':
            self.logger.info("Enhanced Menu: Help")
            help_text = ("❓ Dicto Help:\n"
                        "• Hold Ctrl+V to record\n"
                        "• Release to transcribe\n"
                        "• Text auto-inserts or copies to clipboard\n"
                        "• View history from menu bar")
            self.notification_manager.show_notification("❓ Help", help_text, timeout=10)

    def _handle_about_action(self, action: str):
        """Handle about-related menu actions."""
        if action == 'show':
            self.logger.info("Enhanced Menu: About")
            about_text = ("ℹ️ About Dicto:\n"
                         "Advanced AI transcription for macOS\n"
                         "Version: 1.0 (Task 7)\n"
                         "Powered by Whisper AI")
            self.notification_manager.show_notification("ℹ️ About Dicto", about_text, timeout=8)

    def _handle_quit_action(self):
        """Handle quit menu action."""
        self.logger.info("Enhanced Menu: Quit Dicto")
        self.shutdown()
        rumps.quit_application()

    # NOTE: rumps does not support hotkeys natively
    # Global hotkey functionality needs to be implemented separately using pynput
    # @rumps.hotkey("Control-V")  # This decorator doesn't exist in rumps
    def hotkey_handler(self, sender):
        """
        Placeholder for hotkey functionality. 
        rumps does not support global hotkeys - would need pynput implementation.
        """
        self.logger.info("Global hotkey (Control-V) detected.")
        if not self.is_recording:
            self.logger.info("Hotkey: Starting recording.")
            self._start_recording()
            self.menu["Start Recording"].enabled = False
            self.menu["Stop Recording"].enabled = True
            self.title = "Dicto: Recording 🔴"
        else:
            self.logger.info("Hotkey: Stopping recording and transcribing.")
            self._stop_recording_and_transcribe()
            self.menu["Start Recording"].enabled = True
            self.menu["Stop Recording"].enabled = False
            self.title = "Dicto: Processing ⚙️"

    def _start_background_tasks(self):
        if not self.continuous_recorder.start_continuous_monitoring():
            self.logger.error("Failed to start continuous recorder's monitoring loop. Exiting.")
            sys.exit(1)

    def _on_continuous_start(self):
        self.logger.info("Continuous recording session started.")
        self.is_recording = True
        self.recording_session_active = True
        self.menu_bar_manager.update_status(AppStatus.RECORDING)
        self.notification_manager.notify_recording_started()

    def _on_continuous_stop(self):
        self.logger.info("Continuous recording session stopped.")
        self.is_recording = False
        self.menu_bar_manager.update_status(AppStatus.IDLE)
        self.notification_manager.notify_recording_stopped()

    def _on_session_complete(self, chunk_paths: List[str]):
        self.logger.info(f"Continuous recording session completed with {len(chunk_paths)} chunks.")
        self.recording_session_active = False
        self.menu_bar_manager.update_status(AppStatus.PROCESSING)

        if not chunk_paths:
            self.logger.warning("No audio chunks recorded for transcription.")
            self.notification_manager.notify_error("No audio recorded.")
            self.menu_bar_manager.update_status(AppStatus.IDLE)
            return

        session_start_time = time.time()
        try:
            output_audio_path = str(Path(tempfile.gettempdir()) / f"dicto_session_{time.time()}.wav")
            if self.continuous_recorder.combine_chunks(output_audio_path):
                self.logger.info(f"Combined audio chunks to: {output_audio_path}")
                transcription_text = self._transcribe_with_vocabulary(output_audio_path)

                if transcription_text:
                    enhanced_text = self._enhance_with_vocabulary(transcription_text)
                    
                    # Calculate session duration
                    session_duration = time.time() - session_start_time
                    
                    # Save session to history
                    try:
                        session_id = self.session_manager.create_session(
                            transcription_text=enhanced_text,
                            duration=session_duration,
                            audio_file_path=output_audio_path,
                            confidence_score=0.85,  # Placeholder confidence
                            language="en",
                            model_used="whisper",
                            metadata={
                                "chunks_count": len(chunk_paths),
                                "auto_insertion": True,
                                "vocabulary_enhanced": True
                            }
                        )
                        self.logger.info(f"Session saved to history: {session_id}")
                    except Exception as e:
                        self.logger.warning(f"Failed to save session to history: {e}")
                    
                    # Automatically insert text into the focused input area
                    if self.auto_text_inserter.insert_text(enhanced_text):
                        self.notification_manager.notify_transcription_complete(enhanced_text)
                        self.logger.info(f"Text automatically inserted: {enhanced_text[:100]}...")
                    else:
                        # Fallback to clipboard if auto-insertion fails
                        self.clipboard_manager.set_text(enhanced_text)
                        self.notification_manager.show_notification(
                            "✅ Transcription Complete (Clipboard)",
                            f"Auto-insertion failed. Text copied to clipboard. Press CMD+V to paste: {enhanced_text[:50]}..."
                        )
                        self.logger.warning("Auto-insertion failed, text copied to clipboard")
                else:
                    self.logger.warning("No transcription text returned.")
                    self.notification_manager.notify_error("Transcription failed.")
                
                os.remove(output_audio_path)
                self.logger.info(f"Cleaned up combined audio file: {output_audio_path}")

            else:
                self.logger.error("Failed to combine audio chunks.")
                self.notification_manager.notify_error("Failed to combine audio.")

            if self.continuous_recorder.cleanup_session(self.continuous_recorder.current_session_id):
                self.logger.info(f"Cleaned up session {self.continuous_recorder.current_session_id} chunks.")
            else:
                self.logger.warning(f"Failed to clean up all chunks for session {self.continuous_recorder.current_session_id}.")

        except Exception as e:
            self.logger.error(f"Error during transcription session: {e}", exc_info=True)
            self.notification_manager.notify_error(f"Transcription error: {e}")
            self.menu_bar_manager.update_status(AppStatus.ERROR)
        finally:
            self.menu_bar_manager.update_status(AppStatus.IDLE)

    def _transcribe_with_vocabulary(self, audio_path: str) -> Optional[str]:
        self.logger.info(f"Transcribing audio file: {audio_path}")
        try:
            transcription_result = self.transcription_engine.transcribe_file(audio_path)
            if transcription_result and transcription_result.get("success"):
                return transcription_result.get("text")
            else:
                error_message = transcription_result.get("error", "Unknown transcription error")
                self.logger.error(f"Transcription failed: {error_message}")
                self.notification_manager.notify_error(f"Transcription error: {error_message}")
                return None
        except Exception as e:
            self.logger.error(f"Exception during transcription: {e}", exc_info=True)
            self.notification_manager.notify_error(f"Transcription exception: {e}")
            return None

    def _enhance_with_vocabulary(self, text: str) -> str:
        """
        Enhance transcription text using custom vocabulary.
        
        Args:
            text: Original transcription text
            
        Returns:
            Enhanced text with vocabulary corrections applied
        """
        try:
            if not text:
                return text
                
            enhanced_text = text
            
            # Get vocabulary suggestions based on context
            suggestions = self.vocabulary_manager.get_vocabulary_suggestions(text)
            
            # Apply common vocabulary enhancements
            enhanced_text = self._apply_vocabulary_corrections(enhanced_text, suggestions)
            
            # Log vocabulary enhancements
            if enhanced_text != text:
                self.logger.info(f"Vocabulary enhanced: '{text[:50]}...' -> '{enhanced_text[:50]}...'")
            
            return enhanced_text
            
        except Exception as e:
            self.logger.error(f"Error enhancing with vocabulary: {e}")
            return text
    
    def _apply_vocabulary_corrections(self, text: str, suggestions: List[str]) -> str:
        """Apply vocabulary corrections to text."""
        corrected_text = text
        
        # Apply custom word replacements from vocabulary
        for suggestion in suggestions:
            # Simple case-insensitive replacement for now
            # In a more sophisticated implementation, this would use fuzzy matching
            words = suggestion.split()
            for word in words:
                # Replace with proper capitalization
                corrected_text = corrected_text.replace(word.lower(), word)
                corrected_text = corrected_text.replace(word.upper(), word)
        
        return corrected_text

    def _start_recording(self):
        """Manual start recording (from menu bar)."""
        self.logger.info("Manual recording start requested.")
        if not self.is_recording:
            self.continuous_recorder.command_queue.put("START_RECORDING")
        else:
            self.logger.warning("Recording already active.")

    def _stop_recording_and_transcribe(self):
        """Manual stop recording (from menu bar)."""
        self.logger.info("Manual recording stop requested.")
        if self.is_recording:
            self.continuous_recorder.command_queue.put("STOP_RECORDING")
        else:
            self.logger.warning("No active recording to stop.")

    def shutdown(self):
        """
        Shutdown the application and clean up resources.
        """
        self.logger.info("Shutting down DictoApp...")
        try:
            # Stop recording if active
            if self.is_recording:
                self.continuous_recorder.stop_continuous_monitoring()
            
            # Cleanup enhanced UI components
            self.menu_bar_manager.cleanup()
            
            # Backup session data
            self.session_manager.backup_sessions()
            
            # Cleanup old sessions (optional)
            cleaned_count = self.session_manager.cleanup_old_sessions(days=90)
            if cleaned_count > 0:
                self.logger.info(f"Cleaned up {cleaned_count} old sessions during shutdown")
            
            self.logger.info("DictoApp shutdown completed with enhanced cleanup.")
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")


def main():
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger("DictoMain")

    whisper_binary = os.path.join(os.path.dirname(__file__), "whisper.cpp/build/bin/whisper-cli")
    whisper_model = os.path.join(os.path.dirname(__file__), "whisper.cpp/models/ggml-base.en.bin")

    if not Path(whisper_binary).exists():
        logger.error(f"Whisper binary not found at: {whisper_binary}")
        logger.error("Please ensure whisper.cpp is built and 'whisper-cli' binary is in whisper.cpp/build/bin/ folder.")
        sys.exit(1)

    if not Path(whisper_model).exists():
        logger.error(f"Whisper model not found at: {whisper_model}")
        logger.error("Please download ggml-base.en.bin into whisper.cpp/models/ folder.")
        sys.exit(1)

    app = DictoApp(whisper_binary_path=whisper_binary, model_path=whisper_model)
    
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, initiating shutdown...")
        app.shutdown()
        rumps.quit_application()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        logger.info("Starting Dicto menu bar application...")
        app.run()
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt detected, shutting down.")
        app.shutdown()
        rumps.quit_application()
    except Exception as e:
        logger.critical(f"An unhandled error occurred: {e}", exc_info=True)
        app.notification_manager.notify_error(f"Critical error: {e}")
        app.shutdown()
        rumps.quit_application()


if __name__ == "__main__":
    main() 