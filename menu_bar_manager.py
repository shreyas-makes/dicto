#!/usr/bin/env python3
"""
Menu Bar Manager - Advanced UI elements for Dicto macOS app

Provides comprehensive menu bar integration with status indicators,
quick controls, and user interaction handling.

Features:
- Animated status indicators (idle, recording, processing)
- Context menu with quick access controls
- Keyboard shortcut customization and conflict detection
- Settings panel integration
- Real-time status updates

Dependencies:
- rumps: macOS menu bar integration
- AppKit: System integration
- threading: Background status updates
"""

import os
import sys
import time
import logging
import threading
from pathlib import Path
from typing import Optional, Dict, Any, Callable, List
from enum import Enum
from dataclasses import dataclass

try:
    import rumps
except ImportError:
    print("Error: rumps not installed. Install with: pip install rumps")
    sys.exit(1)

try:
    from AppKit import NSApplication, NSSystemDefined, NSKeyDown
except ImportError:
    print("Error: PyObjC not installed. Install with: pip install pyobjc-framework-Cocoa")
    sys.exit(1)


class AppStatus(Enum):
    """Application status states with visual indicators."""
    IDLE = ("Dicto: Idle", "⚪", "Ready to record")
    RECORDING = ("Dicto: Recording", "🔴", "Recording in progress...")
    PROCESSING = ("Dicto: Processing", "⚙️", "Processing transcription...")
    ERROR = ("Dicto: Error", "❌", "Error occurred")
    PAUSED = ("Dicto: Paused", "⏸️", "Recording paused")


@dataclass
class MenuAction:
    """Menu action configuration."""
    title: str
    callback: Callable
    enabled: bool = True
    separator_after: bool = False
    shortcut: Optional[str] = None


class MenuBarManager:
    """
    MenuBarManager - Advanced menu bar integration for Dicto.
    
    Provides status indicators, quick controls, and user interaction handling
    with animated status updates and keyboard shortcut management.
    """
    
    def __init__(self, app_name: str = "Dicto", rumps_app: Optional[rumps.App] = None):
        """
        Initialize MenuBarManager.
        
        Args:
            app_name: Application name for menu bar display.
            rumps_app: Optional existing rumps.App instance to use.
        """
        self.app_name = app_name
        self.logger = logging.getLogger(__name__ + ".MenuBarManager")
        
        # Status management
        self.current_status = AppStatus.IDLE
        self.status_animation_thread = None
        self.animation_running = False
        
        # Menu state
        self.menu_items: Dict[str, rumps.MenuItem] = {}
        self.status_callbacks: Dict[AppStatus, Optional[Callable]] = {}
        
        # Shortcut management
        self.registered_shortcuts: Dict[str, str] = {}
        self.shortcut_conflicts: List[str] = []
        
        # Quick settings
        self.settings_panel_visible = False
        
        # Callback handlers (initialized to None)
        self.recording_callback: Optional[Callable] = None
        self.transcription_callback: Optional[Callable] = None
        self.history_callback: Optional[Callable] = None
        self.settings_callback: Optional[Callable] = None
        self.shortcuts_callback: Optional[Callable] = None
        self.status_callback: Optional[Callable] = None
        self.debug_callback: Optional[Callable] = None
        self.help_callback: Optional[Callable] = None
        self.about_callback: Optional[Callable] = None
        self.quit_callback: Optional[Callable] = None
        
        # Initialize rumps app (create new or use existing)
        if rumps_app:
            self.app = rumps_app
            self.logger.info("Using existing rumps app")
        else:
            self._create_app()
        
        self.logger.info("MenuBarManager initialized")
    
    def _create_app(self):
        """Create the rumps app for menu bar integration."""
        try:
            # Create rumps app
            self.app = rumps.App(
                name=self.app_name,
                icon=None,
                quit_button=None  # Custom quit handling
            )
            
            # Set initial status
            self.update_status(AppStatus.IDLE)
            
            self.logger.info("Rumps app created successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to create rumps app: {e}")
            raise
    
    def create_status_icon(self, initial_status: AppStatus = AppStatus.IDLE) -> rumps.App:
        """
        Create and configure the menu bar status icon.
        
        Args:
            initial_status: Initial application status.
            
        Returns:
            rumps.App: Configured menu bar application.
        """
        try:
            # Create rumps app with initial status
            app = rumps.App(
                name=initial_status.value[0],
                icon=None,  # We'll use emoji in title
                quit_button=None  # Custom quit handling
            )
            
            self.app = app
            self.update_status(initial_status)
            
            self.logger.info(f"Status icon created with status: {initial_status.name}")
            return app
            
        except Exception as e:
            self.logger.error(f"Failed to create status icon: {e}")
            raise
    
    def update_status(self, status: AppStatus, message: Optional[str] = None):
        """
        Update menu bar status with animation support.
        
        Args:
            status: New application status.
            message: Optional custom status message.
        """
        try:
            self.current_status = status
            
            # Update title with emoji indicator
            title = f"{status.value[1]} {status.value[0]}"
            if hasattr(self, 'app'):
                self.app.title = title
            
            # Start animation for recording/processing states
            if status in [AppStatus.RECORDING, AppStatus.PROCESSING]:
                self._start_status_animation(status)
            else:
                self._stop_status_animation()
            
            # Trigger status callback if registered
            callback = self.status_callbacks.get(status)
            if callback:
                try:
                    callback(status, message)
                except Exception as e:
                    self.logger.error(f"Status callback error: {e}")
            
            self.logger.info(f"Status updated to: {status.name}")
            
        except Exception as e:
            self.logger.error(f"Failed to update status: {e}")
    
    def _start_status_animation(self, status: AppStatus):
        """Start animated status indicator."""
        if self.animation_running:
            self._stop_status_animation()
        
        self.animation_running = True
        self.status_animation_thread = threading.Thread(
            target=self._animate_status,
            args=(status,),
            daemon=True
        )
        self.status_animation_thread.start()
    
    def _stop_status_animation(self):
        """Stop animated status indicator."""
        self.animation_running = False
        if self.status_animation_thread and self.status_animation_thread.is_alive():
            self.status_animation_thread.join(timeout=1.0)
    
    def _animate_status(self, status: AppStatus):
        """Animate status indicator with pulsing effect."""
        animation_frames = {
            AppStatus.RECORDING: ["🔴", "🟥", "🔴", "⭕"],
            AppStatus.PROCESSING: ["⚙️", "🔄", "⚡", "💫"]
        }
        
        frames = animation_frames.get(status, ["⚪"])
        frame_index = 0
        
        while self.animation_running and hasattr(self, 'app'):
            try:
                current_frame = frames[frame_index % len(frames)]
                title = f"{current_frame} {status.value[0]}"
                self.app.title = title
                
                frame_index += 1
                time.sleep(0.5)  # Animation speed
                
            except Exception as e:
                self.logger.error(f"Animation error: {e}")
                break
    
    def create_context_menu(self) -> List[rumps.MenuItem]:
        """
        Create comprehensive context menu with quick controls.
        
        Returns:
            List[rumps.MenuItem]: Menu items for context menu.
        """
        menu_actions = [
            MenuAction("🎤 Start Recording", self._handle_start_recording, True),
            MenuAction("⏹️ Stop Recording", self._handle_stop_recording, False),
            MenuAction("", None, separator_after=True),  # Separator
            
            MenuAction("📋 Recent Transcriptions", self._handle_recent_transcriptions),
            MenuAction("📝 Transcription History", self._handle_history),
            MenuAction("", None, separator_after=True),  # Separator
            
            MenuAction("⚙️ Settings", self._handle_settings),
            MenuAction("🔧 Advanced Settings", self._handle_advanced_settings),
            MenuAction("⌨️ Keyboard Shortcuts", self._handle_shortcuts),
            MenuAction("", None, separator_after=True),  # Separator
            
            MenuAction("📊 Status", self._handle_status_info),
            MenuAction("🔍 Debug Info", self._handle_debug_info),
            MenuAction("", None, separator_after=True),  # Separator
            
            MenuAction("❓ Help", self._handle_help),
            MenuAction("ℹ️ About Dicto", self._handle_about),
            MenuAction("🚪 Quit Dicto", self._handle_quit)
        ]
        
        menu_items = []
        for action in menu_actions:
            if action.title == "":  # Separator
                menu_items.append(None)
            else:
                item = rumps.MenuItem(
                    title=action.title,
                    callback=action.callback
                )
                item.enabled = action.enabled
                menu_items.append(item)
                self.menu_items[action.title] = item
        
        self.logger.info(f"Context menu created with {len([i for i in menu_items if i])} items")
        return menu_items
    
    def handle_menu_actions(self, action_name: str, *args, **kwargs):
        """
        Handle menu action by name with error handling.
        
        Args:
            action_name: Name of the action to execute.
            *args, **kwargs: Arguments to pass to action handler.
        """
        try:
            handler_map = {
                "start_recording": self._handle_start_recording,
                "stop_recording": self._handle_stop_recording,
                "recent_transcriptions": self._handle_recent_transcriptions,
                "history": self._handle_history,
                "settings": self._handle_settings,
                "shortcuts": self._handle_shortcuts,
                "status": self._handle_status_info,
                "quit": self._handle_quit
            }
            
            handler = handler_map.get(action_name)
            if handler:
                handler(*args, **kwargs)
            else:
                self.logger.warning(f"Unknown menu action: {action_name}")
                
        except Exception as e:
            self.logger.error(f"Menu action error for {action_name}: {e}")
    
    def register_status_callback(self, status: AppStatus, callback: Callable):
        """Register callback for status changes."""
        self.status_callbacks[status] = callback
        self.logger.info(f"Registered callback for status: {status.name}")
    
    def register_shortcut(self, shortcut: str, action: str, description: str = "") -> bool:
        """
        Register keyboard shortcut with conflict detection.
        
        Args:
            shortcut: Keyboard shortcut (e.g., "Ctrl+V").
            action: Action name to associate with shortcut.
            description: Human-readable description.
            
        Returns:
            bool: True if registered successfully, False if conflict detected.
        """
        try:
            # Check for conflicts with existing shortcuts
            if shortcut in self.registered_shortcuts:
                existing_action = self.registered_shortcuts[shortcut]
                self.logger.warning(f"Shortcut conflict: {shortcut} already assigned to {existing_action}")
                self.shortcut_conflicts.append(f"{shortcut}: {action} vs {existing_action}")
                return False
            
            # Register shortcut
            self.registered_shortcuts[shortcut] = action
            self.logger.info(f"Registered shortcut: {shortcut} -> {action}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to register shortcut {shortcut}: {e}")
            return False
    
    def get_shortcut_conflicts(self) -> List[str]:
        """Get list of detected shortcut conflicts."""
        return self.shortcut_conflicts.copy()
    
    def resolve_shortcut_conflict(self, shortcut: str, preferred_action: str) -> bool:
        """
        Resolve shortcut conflict by assigning to preferred action.
        
        Args:
            shortcut: Conflicting shortcut.
            preferred_action: Action to assign shortcut to.
            
        Returns:
            bool: True if resolved successfully.
        """
        try:
            if shortcut in self.registered_shortcuts:
                old_action = self.registered_shortcuts[shortcut]
                self.registered_shortcuts[shortcut] = preferred_action
                
                # Remove from conflicts list
                conflict_entries = [c for c in self.shortcut_conflicts if shortcut in c]
                for entry in conflict_entries:
                    self.shortcut_conflicts.remove(entry)
                
                self.logger.info(f"Resolved shortcut conflict: {shortcut} reassigned from {old_action} to {preferred_action}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to resolve shortcut conflict for {shortcut}: {e}")
            return False
    
    def enable_menu_item(self, title: str, enabled: bool = True):
        """Enable or disable menu item by title."""
        if title in self.menu_items:
            self.menu_items[title].enabled = enabled
            self.logger.debug(f"Menu item '{title}' {'enabled' if enabled else 'disabled'}")
    
    def update_menu_item_title(self, old_title: str, new_title: str):
        """Update menu item title."""
        if old_title in self.menu_items:
            item = self.menu_items[old_title]
            item.title = new_title
            self.menu_items[new_title] = self.menu_items.pop(old_title)
            self.logger.debug(f"Menu item title updated: '{old_title}' -> '{new_title}'")
    
    # Menu action handlers
    def _handle_start_recording(self, sender=None):
        """Handle start recording menu action."""
        self.logger.info("Menu action: Start Recording")
        if hasattr(self, 'recording_callback'):
            self.recording_callback('start')
    
    def _handle_stop_recording(self, sender=None):
        """Handle stop recording menu action."""
        self.logger.info("Menu action: Stop Recording")
        if hasattr(self, 'recording_callback'):
            self.recording_callback('stop')
    
    def _handle_recent_transcriptions(self, sender=None):
        """Handle recent transcriptions menu action."""
        self.logger.info("Menu action: Recent Transcriptions")
        if hasattr(self, 'transcription_callback'):
            self.transcription_callback('recent')
    
    def _handle_history(self, sender=None):
        """Handle transcription history menu action."""
        self.logger.info("Menu action: Transcription History")
        if hasattr(self, 'history_callback'):
            self.history_callback('show')
    
    def _handle_settings(self, sender=None):
        """Handle settings menu action."""
        self.logger.info("Menu action: Settings")
        if hasattr(self, 'settings_callback'):
            self.settings_callback('show')
    
    def _handle_advanced_settings(self, sender=None):
        """Handle advanced settings menu action."""
        self.logger.info("Menu action: Advanced Settings")
        if hasattr(self, 'settings_callback'):
            self.settings_callback('advanced')
    
    def _handle_shortcuts(self, sender=None):
        """Handle keyboard shortcuts menu action."""
        self.logger.info("Menu action: Keyboard Shortcuts")
        if hasattr(self, 'shortcuts_callback'):
            self.shortcuts_callback('configure')
    
    def _handle_status_info(self, sender=None):
        """Handle status info menu action."""
        self.logger.info("Menu action: Status Info")
        if hasattr(self, 'status_callback'):
            self.status_callback('info')
    
    def _handle_debug_info(self, sender=None):
        """Handle debug info menu action."""
        self.logger.info("Menu action: Debug Info")
        if hasattr(self, 'debug_callback'):
            self.debug_callback('show')
    
    def _handle_help(self, sender=None):
        """Handle help menu action."""
        self.logger.info("Menu action: Help")
        if hasattr(self, 'help_callback'):
            self.help_callback('show')
    
    def _handle_about(self, sender=None):
        """Handle about menu action."""
        self.logger.info("Menu action: About")
        if hasattr(self, 'about_callback'):
            self.about_callback('show')
    
    def _handle_quit(self, sender=None):
        """Handle quit menu action."""
        self.logger.info("Menu action: Quit")
        if hasattr(self, 'quit_callback'):
            self.quit_callback()
    
    def set_recording_callback(self, callback: Callable):
        """Set callback for recording actions."""
        self.recording_callback = callback
    
    def set_transcription_callback(self, callback: Callable):
        """Set callback for transcription actions."""
        self.transcription_callback = callback
    
    def set_history_callback(self, callback: Callable):
        """Set callback for history actions."""
        self.history_callback = callback
    
    def set_settings_callback(self, callback: Callable):
        """Set callback for settings actions."""
        self.settings_callback = callback
    
    def set_shortcuts_callback(self, callback: Callable):
        """Set callback for shortcuts actions."""
        self.shortcuts_callback = callback
    
    def set_status_callback(self, callback: Callable):
        """Set callback for status actions."""
        self.status_callback = callback
    
    def set_debug_callback(self, callback: Callable):
        """Set callback for debug actions."""
        self.debug_callback = callback
    
    def set_help_callback(self, callback: Callable):
        """Set callback for help actions."""
        self.help_callback = callback
    
    def set_about_callback(self, callback: Callable):
        """Set callback for about actions."""
        self.about_callback = callback
    
    def set_quit_callback(self, callback: Callable):
        """Set callback for quit actions."""
        self.quit_callback = callback
    
    def cleanup(self):
        """Cleanup menu bar manager resources."""
        try:
            # Stop any running animations
            self._stop_status_animation()
            
            # Clear callbacks
            self.status_callbacks.clear()
            
            self.logger.info("MenuBarManager cleanup completed")
            
        except Exception as e:
            self.logger.error(f"MenuBarManager cleanup failed: {e}")

    def create_menu_from_structure(self, menu_structure: Dict[str, Dict[str, str]]):
        """
        Create menu items from a structured dictionary.
        
        Args:
            menu_structure: Nested dictionary defining menu structure.
                           Format: {"Section": {"Item Name": "action_id"}}
        """
        try:
            if not hasattr(self, 'app') or not self.app:
                self.logger.error("Cannot create menu: app not initialized")
                return
            
            # Clear existing menu items
            self.menu_items.clear()
            
            first_section = True
            for section_name, items in menu_structure.items():
                # Add section separator if this isn't the first section
                if not first_section:
                    self.app.menu.add(rumps.separator)
                first_section = False
                
                # Add section items
                for item_name, action_id in items.items():
                    # Handle separators
                    if item_name == "---" or action_id is None:
                        self.app.menu.add(rumps.separator)
                        continue
                    
                    # Create menu item
                    menu_item = rumps.MenuItem(item_name)
                    
                    # Set callback if action_id is provided
                    if action_id:
                        menu_item.callback = self._create_menu_callback(action_id)
                    
                    self.app.menu.add(menu_item)
                    self.menu_items[item_name] = menu_item
            
            self.logger.info(f"Created menu structure with {len(self.menu_items)} items")
            
        except Exception as e:
            self.logger.error(f"Failed to create menu from structure: {e}")
            # Log the exception details for debugging
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")

    def _create_menu_callback(self, action_id: str):
        """Create a callback function for the given action_id."""
        def callback(sender):
            try:
                # Handle callbacks based on action_id pattern
                if action_id in ['record', 'start', 'stop', 'cancel']:
                    if self.recording_callback:
                        self.recording_callback(action_id)
                elif action_id.startswith('record_'):
                    action = action_id.replace('record_', '')
                    if self.recording_callback:
                        self.recording_callback(action)
                elif action_id in ['transcribe_file', 'paste_last']:
                    if self.transcription_callback:
                        self.transcription_callback(action_id)
                elif action_id.startswith('transcribe_'):
                    action = action_id.replace('transcribe_', '')
                    if self.transcription_callback:
                        self.transcription_callback(action)
                elif action_id in ['clear_history', 'view_history']:
                    if self.history_callback:
                        self.history_callback(action_id)
                elif action_id.startswith('history_'):
                    action = action_id.replace('history_', '')
                    if self.history_callback:
                        self.history_callback(action)
                elif action_id in ['show', 'audio', 'transcription', 'profiles', 'hotkeys', 'advanced', 'export', 'import']:
                    if self.settings_callback:
                        self.settings_callback(action_id)
                elif action_id.startswith('settings_'):
                    action = action_id.replace('settings_', '')
                    if self.settings_callback:
                        self.settings_callback(action)
                elif action_id in ['view_logs', 'debug_mode', 'run_tests', 'generate_report', 'check_health']:
                    if self.debug_callback:
                        self.debug_callback(action_id)
                elif action_id.startswith('debug_'):
                    action = action_id.replace('debug_', '')
                    if self.debug_callback:
                        self.debug_callback(action)
                elif action_id in ['check_updates', 'documentation', 'report_issue']:
                    if self.help_callback:
                        self.help_callback(action_id)
                elif action_id.startswith('help_'):
                    action = action_id.replace('help_', '')
                    if self.help_callback:
                        self.help_callback(action)
                elif action_id in ['about_dicto']:
                    if self.about_callback:
                        self.about_callback(action_id)
                elif action_id.startswith('about_'):
                    action = action_id.replace('about_', '')
                    if self.about_callback:
                        self.about_callback(action)
                elif action_id == 'quit_dicto':
                    if self.quit_callback:
                        self.quit_callback()
                elif action_id.startswith('shortcuts_'):
                    action = action_id.replace('shortcuts_', '')
                    if self.shortcuts_callback:
                        self.shortcuts_callback(action)
                elif action_id.startswith('status_'):
                    action = action_id.replace('status_', '')
                    if self.status_callback:
                        self.status_callback(action)
                else:
                    # Generic callback
                    self.logger.info(f"Generic menu action: {action_id}")
            except Exception as e:
                self.logger.error(f"Menu callback error for {action_id}: {e}")
                # Log the exception details for debugging
                import traceback
                self.logger.error(f"Traceback: {traceback.format_exc()}")
        
        return callback
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        try:
            self.cleanup()
        except:
            pass

    def run(self):
        """Run the menu bar application."""
        try:
            if hasattr(self, 'app') and self.app:
                self.logger.info("Starting MenuBar application...")
                self.app.run()
            else:
                self.logger.error("Cannot run: app not initialized")
        except Exception as e:
            self.logger.error(f"Failed to run MenuBar app: {e}")
            raise
    
    def quit(self):
        """Quit the menu bar application."""
        try:
            if hasattr(self, 'app') and self.app:
                self.app.quit()
                self.logger.info("MenuBar application quit")
        except Exception as e:
            self.logger.error(f"Error quitting MenuBar app: {e}")

    def set_rumps_app(self, rumps_app: rumps.App):
        """Set an existing rumps app to work with."""
        self.app = rumps_app
        self.logger.info("Rumps app set successfully") 