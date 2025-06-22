#!/usr/bin/env python3
"""
Preferences GUI - Visual configuration interface for Dicto
Provides user-friendly GUI for configuration management, profile switching,
and settings customization.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
import json

try:
    from config_manager import ConfigManager, AudioSettings, TranscriptionSettings, UISettings, AdvancedSettings
except ImportError:
    print("Error: config_manager.py not found. Ensure it's in the same directory.")
    exit(1)


class PreferencesGUI:
    """
    Visual preferences interface for Dicto configuration.
    
    Provides tabbed interface for different settings categories:
    - General settings
    - Audio configuration
    - Transcription options
    - Hotkeys management
    - User profiles
    - Advanced settings
    """
    
    def __init__(self, config_manager: ConfigManager):
        """
        Initialize preferences GUI.
        
        Args:
            config_manager: ConfigManager instance for settings management.
        """
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__ + ".PreferencesGUI")
        
        # Create main window
        self.root = tk.Tk()
        self.root.title("Dicto Preferences")
        self.root.geometry("800x600")
        
        # Configure style for better macOS appearance
        self.style = ttk.Style()
        self.style.theme_use('clam')  # More native-looking theme
        
        # Variables for form controls
        self.form_vars = {}
        self.hotkey_entries = {}
        
        # Create interface
        self._create_interface()
        
        # Load current settings
        self._load_current_settings()
        
        self.logger.info("PreferencesGUI initialized")
    
    def _create_interface(self):
        """Create the main GUI interface."""
        # Create notebook for tabbed interface
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create tabs
        self._create_general_tab()
        self._create_audio_tab()
        self._create_transcription_tab()
        self._create_hotkeys_tab()
        self._create_profiles_tab()
        self._create_advanced_tab()
        
        # Create bottom button frame
        self._create_button_frame()
    
    def _create_general_tab(self):
        """Create general settings tab."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="General")
        
        # UI Settings section
        ui_frame = ttk.LabelFrame(frame, text="User Interface", padding=10)
        ui_frame.pack(fill='x', padx=10, pady=5)
        
        # Menu bar behavior
        ttk.Label(ui_frame, text="Menu Bar Behavior:").grid(row=0, column=0, sticky='w', pady=2)
        self.form_vars['menu_bar_behavior'] = tk.StringVar()
        menu_combo = ttk.Combobox(ui_frame, textvariable=self.form_vars['menu_bar_behavior'],
                                 values=['always_visible', 'auto_hide', 'minimal'], state='readonly')
        menu_combo.grid(row=0, column=1, sticky='ew', padx=(10, 0), pady=2)
        
        # Notification style
        ttk.Label(ui_frame, text="Notification Style:").grid(row=1, column=0, sticky='w', pady=2)
        self.form_vars['notification_style'] = tk.StringVar()
        notif_combo = ttk.Combobox(ui_frame, textvariable=self.form_vars['notification_style'],
                                  values=['native', 'minimal', 'disabled'], state='readonly')
        notif_combo.grid(row=1, column=1, sticky='ew', padx=(10, 0), pady=2)
        
        # Checkboxes
        self.form_vars['show_transcription_preview'] = tk.BooleanVar()
        ttk.Checkbutton(ui_frame, text="Show transcription preview",
                       variable=self.form_vars['show_transcription_preview']).grid(row=2, column=0, columnspan=2, sticky='w', pady=2)
        
        self.form_vars['auto_copy_to_clipboard'] = tk.BooleanVar()
        ttk.Checkbutton(ui_frame, text="Auto copy to clipboard",
                       variable=self.form_vars['auto_copy_to_clipboard']).grid(row=3, column=0, columnspan=2, sticky='w', pady=2)
        
        self.form_vars['show_confidence_scores'] = tk.BooleanVar()
        ttk.Checkbutton(ui_frame, text="Show confidence scores",
                       variable=self.form_vars['show_confidence_scores']).grid(row=4, column=0, columnspan=2, sticky='w', pady=2)
        
        # Dark mode
        ttk.Label(ui_frame, text="Dark Mode:").grid(row=5, column=0, sticky='w', pady=2)
        self.form_vars['dark_mode'] = tk.StringVar()
        dark_combo = ttk.Combobox(ui_frame, textvariable=self.form_vars['dark_mode'],
                                 values=['system', 'light', 'dark'], state='readonly')
        dark_combo.grid(row=5, column=1, sticky='ew', padx=(10, 0), pady=2)
        
        ui_frame.columnconfigure(1, weight=1)
    
    def _create_audio_tab(self):
        """Create audio settings tab."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Audio")
        
        # Audio Settings section
        audio_frame = ttk.LabelFrame(frame, text="Audio Processing", padding=10)
        audio_frame.pack(fill='x', padx=10, pady=5)
        
        # Input device (placeholder - would need to get from audio processor)
        ttk.Label(audio_frame, text="Input Device:").grid(row=0, column=0, sticky='w', pady=2)
        self.form_vars['input_device'] = tk.StringVar()
        device_combo = ttk.Combobox(audio_frame, textvariable=self.form_vars['input_device'],
                                   values=['Default', 'Built-in Microphone'], state='readonly')
        device_combo.grid(row=0, column=1, sticky='ew', padx=(10, 0), pady=2)
        
        # Noise reduction
        ttk.Label(audio_frame, text="Noise Reduction:").grid(row=1, column=0, sticky='w', pady=2)
        self.form_vars['noise_reduction_level'] = tk.StringVar()
        noise_combo = ttk.Combobox(audio_frame, textvariable=self.form_vars['noise_reduction_level'],
                                  values=['low', 'medium', 'high'], state='readonly')
        noise_combo.grid(row=1, column=1, sticky='ew', padx=(10, 0), pady=2)
        
        # Gain adjustment
        ttk.Label(audio_frame, text="Gain Adjustment:").grid(row=2, column=0, sticky='w', pady=2)
        self.form_vars['gain_adjustment'] = tk.DoubleVar()
        gain_scale = ttk.Scale(audio_frame, from_=0.1, to=5.0, orient='horizontal',
                              variable=self.form_vars['gain_adjustment'])
        gain_scale.grid(row=2, column=1, sticky='ew', padx=(10, 0), pady=2)
        
        # Sample rate
        ttk.Label(audio_frame, text="Sample Rate:").grid(row=3, column=0, sticky='w', pady=2)
        self.form_vars['sample_rate'] = tk.StringVar()
        rate_combo = ttk.Combobox(audio_frame, textvariable=self.form_vars['sample_rate'],
                                 values=['8000', '16000', '22050', '44100', '48000'], state='readonly')
        rate_combo.grid(row=3, column=1, sticky='ew', padx=(10, 0), pady=2)
        
        # Checkboxes
        self.form_vars['auto_gain_control'] = tk.BooleanVar()
        ttk.Checkbutton(audio_frame, text="Auto gain control",
                       variable=self.form_vars['auto_gain_control']).grid(row=4, column=0, columnspan=2, sticky='w', pady=2)
        
        self.form_vars['voice_activity_detection'] = tk.BooleanVar()
        ttk.Checkbutton(audio_frame, text="Voice activity detection",
                       variable=self.form_vars['voice_activity_detection']).grid(row=5, column=0, columnspan=2, sticky='w', pady=2)
        
        audio_frame.columnconfigure(1, weight=1)
    
    def _create_transcription_tab(self):
        """Create transcription settings tab."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Transcription")
        
        # Transcription Settings section
        trans_frame = ttk.LabelFrame(frame, text="Transcription Options", padding=10)
        trans_frame.pack(fill='x', padx=10, pady=5)
        
        # Model selection
        ttk.Label(trans_frame, text="Model:").grid(row=0, column=0, sticky='w', pady=2)
        self.form_vars['model_name'] = tk.StringVar()
        model_combo = ttk.Combobox(trans_frame, textvariable=self.form_vars['model_name'],
                                  values=['base.en', 'small.en', 'medium.en', 'large'], state='readonly')
        model_combo.grid(row=0, column=1, sticky='ew', padx=(10, 0), pady=2)
        
        # Language
        ttk.Label(trans_frame, text="Language:").grid(row=1, column=0, sticky='w', pady=2)
        self.form_vars['language'] = tk.StringVar()
        lang_combo = ttk.Combobox(trans_frame, textvariable=self.form_vars['language'],
                                 values=['en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'ja', 'zh'], state='readonly')
        lang_combo.grid(row=1, column=1, sticky='ew', padx=(10, 0), pady=2)
        
        # Confidence threshold
        ttk.Label(trans_frame, text="Confidence Threshold:").grid(row=2, column=0, sticky='w', pady=2)
        self.form_vars['confidence_threshold'] = tk.DoubleVar()
        conf_scale = ttk.Scale(trans_frame, from_=0.0, to=1.0, orient='horizontal',
                              variable=self.form_vars['confidence_threshold'])
        conf_scale.grid(row=2, column=1, sticky='ew', padx=(10, 0), pady=2)
        
        # Checkboxes
        self.form_vars['auto_language_detection'] = tk.BooleanVar()
        ttk.Checkbutton(trans_frame, text="Auto language detection",
                       variable=self.form_vars['auto_language_detection']).grid(row=3, column=0, columnspan=2, sticky='w', pady=2)
        
        self.form_vars['custom_vocabulary_enabled'] = tk.BooleanVar()
        ttk.Checkbutton(trans_frame, text="Enable custom vocabulary",
                       variable=self.form_vars['custom_vocabulary_enabled']).grid(row=4, column=0, columnspan=2, sticky='w', pady=2)
        
        self.form_vars['timestamping_enabled'] = tk.BooleanVar()
        ttk.Checkbutton(trans_frame, text="Enable timestamping",
                       variable=self.form_vars['timestamping_enabled']).grid(row=5, column=0, columnspan=2, sticky='w', pady=2)
        
        self.form_vars['speaker_diarization'] = tk.BooleanVar()
        ttk.Checkbutton(trans_frame, text="Speaker diarization",
                       variable=self.form_vars['speaker_diarization']).grid(row=6, column=0, columnspan=2, sticky='w', pady=2)
        
        trans_frame.columnconfigure(1, weight=1)
    
    def _create_hotkeys_tab(self):
        """Create hotkeys configuration tab."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Hotkeys")
        
        # Hotkeys section
        hotkey_frame = ttk.LabelFrame(frame, text="Keyboard Shortcuts", padding=10)
        hotkey_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Create scrollable frame for hotkeys
        canvas = tk.Canvas(hotkey_frame)
        scrollbar = ttk.Scrollbar(hotkey_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Default hotkeys
        hotkey_definitions = [
            ("record_toggle", "Toggle Recording", "ctrl+v"),
            ("transcribe_clipboard", "Transcribe Clipboard", "ctrl+shift+v"),
            ("open_preferences", "Open Preferences", "cmd+,"),
            ("pause_resume", "Pause/Resume", "space"),
            ("stop_recording", "Stop Recording", "esc")
        ]
        
        for i, (action, description, default_key) in enumerate(hotkey_definitions):
            ttk.Label(scrollable_frame, text=f"{description}:").grid(row=i, column=0, sticky='w', pady=2)
            
            entry_var = tk.StringVar(value=default_key)
            self.hotkey_entries[action] = entry_var
            entry = ttk.Entry(scrollable_frame, textvariable=entry_var, width=20)
            entry.grid(row=i, column=1, padx=(10, 5), pady=2)
            
            # Detect button
            detect_btn = ttk.Button(scrollable_frame, text="Detect", width=8,
                                   command=lambda a=action: self._detect_hotkey(a))
            detect_btn.grid(row=i, column=2, padx=5, pady=2)
            
            # Clear button
            clear_btn = ttk.Button(scrollable_frame, text="Clear", width=8,
                                  command=lambda a=action: self.hotkey_entries[a].set(""))
            clear_btn.grid(row=i, column=3, padx=5, pady=2)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Validation button
        validate_frame = ttk.Frame(frame)
        validate_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(validate_frame, text="Validate Hotkeys",
                  command=self._validate_hotkeys).pack(side='left')
        
        self.hotkey_status_label = ttk.Label(validate_frame, text="")
        self.hotkey_status_label.pack(side='left', padx=(10, 0))
    
    def _create_profiles_tab(self):
        """Create user profiles management tab."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Profiles")
        
        # Profile management section
        profile_frame = ttk.LabelFrame(frame, text="User Profiles", padding=10)
        profile_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Profile selection
        selection_frame = ttk.Frame(profile_frame)
        selection_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(selection_frame, text="Current Profile:").pack(side='left')
        
        self.profile_var = tk.StringVar()
        self.profile_combo = ttk.Combobox(selection_frame, textvariable=self.profile_var,
                                         state='readonly', width=20)
        self.profile_combo.pack(side='left', padx=(10, 0))
        self.profile_combo.bind('<<ComboboxSelected>>', self._on_profile_selected)
        
        ttk.Button(selection_frame, text="Switch", command=self._switch_profile).pack(side='left', padx=(10, 0))
        
        # Profile management buttons
        button_frame = ttk.Frame(profile_frame)
        button_frame.pack(fill='x', pady=5)
        
        ttk.Button(button_frame, text="New Profile", command=self._create_new_profile).pack(side='left', padx=(0, 5))
        ttk.Button(button_frame, text="Copy Profile", command=self._copy_profile).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Delete Profile", command=self._delete_profile).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Rename Profile", command=self._rename_profile).pack(side='left', padx=5)
        
        # Profile details
        details_frame = ttk.LabelFrame(profile_frame, text="Profile Details", padding=10)
        details_frame.pack(fill='both', expand=True, pady=(10, 0))
        
        self.profile_details_text = tk.Text(details_frame, height=10, wrap='word', state='disabled')
        details_scrollbar = ttk.Scrollbar(details_frame, orient="vertical", command=self.profile_details_text.yview)
        self.profile_details_text.configure(yscrollcommand=details_scrollbar.set)
        
        self.profile_details_text.pack(side="left", fill="both", expand=True)
        details_scrollbar.pack(side="right", fill="y")
        
        # Import/Export buttons
        ie_frame = ttk.Frame(profile_frame)
        ie_frame.pack(fill='x', pady=(10, 0))
        
        ttk.Button(ie_frame, text="Export Settings", command=self._export_settings).pack(side='left', padx=(0, 5))
        ttk.Button(ie_frame, text="Import Settings", command=self._import_settings).pack(side='left', padx=5)
    
    def _create_advanced_tab(self):
        """Create advanced settings tab."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Advanced")
        
        # Advanced Settings section
        adv_frame = ttk.LabelFrame(frame, text="Advanced Options", padding=10)
        adv_frame.pack(fill='x', padx=10, pady=5)
        
        # Temp file location
        ttk.Label(adv_frame, text="Temp File Location:").grid(row=0, column=0, sticky='w', pady=2)
        self.form_vars['temp_file_location'] = tk.StringVar()
        temp_entry = ttk.Entry(adv_frame, textvariable=self.form_vars['temp_file_location'])
        temp_entry.grid(row=0, column=1, sticky='ew', padx=(10, 5), pady=2)
        ttk.Button(adv_frame, text="Browse", command=self._browse_temp_location).grid(row=0, column=2, padx=5, pady=2)
        
        # Cleanup policy
        ttk.Label(adv_frame, text="Cleanup Policy:").grid(row=1, column=0, sticky='w', pady=2)
        self.form_vars['cleanup_policy'] = tk.StringVar()
        cleanup_combo = ttk.Combobox(adv_frame, textvariable=self.form_vars['cleanup_policy'],
                                    values=['auto', 'manual', 'never'], state='readonly')
        cleanup_combo.grid(row=1, column=1, sticky='ew', padx=(10, 0), pady=2)
        
        # Log level
        ttk.Label(adv_frame, text="Log Level:").grid(row=2, column=0, sticky='w', pady=2)
        self.form_vars['log_level'] = tk.StringVar()
        log_combo = ttk.Combobox(adv_frame, textvariable=self.form_vars['log_level'],
                                values=['DEBUG', 'INFO', 'WARNING', 'ERROR'], state='readonly')
        log_combo.grid(row=2, column=1, sticky='ew', padx=(10, 0), pady=2)
        
        # Checkboxes
        self.form_vars['enable_crash_recovery'] = tk.BooleanVar()
        ttk.Checkbutton(adv_frame, text="Enable crash recovery",
                       variable=self.form_vars['enable_crash_recovery']).grid(row=3, column=0, columnspan=2, sticky='w', pady=2)
        
        self.form_vars['diagnostic_mode'] = tk.BooleanVar()
        ttk.Checkbutton(adv_frame, text="Enable diagnostic mode",
                       variable=self.form_vars['diagnostic_mode']).grid(row=4, column=0, columnspan=2, sticky='w', pady=2)
        
        # Reset buttons
        reset_frame = ttk.Frame(adv_frame)
        reset_frame.grid(row=5, column=0, columnspan=3, sticky='ew', pady=(10, 0))
        
        ttk.Button(reset_frame, text="Reset Current Profile", command=self._reset_current_profile).pack(side='left', padx=(0, 5))
        ttk.Button(reset_frame, text="Reset All Settings", command=self._reset_all_settings).pack(side='left', padx=5)
        
        adv_frame.columnconfigure(1, weight=1)
    
    def _create_button_frame(self):
        """Create bottom button frame."""
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        ttk.Button(button_frame, text="Cancel", command=self._cancel).pack(side='right', padx=(5, 0))
        ttk.Button(button_frame, text="Apply", command=self._apply_settings).pack(side='right', padx=5)
        ttk.Button(button_frame, text="OK", command=self._ok).pack(side='right')
    
    def _load_current_settings(self):
        """Load current settings into the form."""
        try:
            current_settings = self.config_manager.get_current_settings()
            
            # Load UI settings
            ui_settings = current_settings.get('ui_settings', {})
            self.form_vars['menu_bar_behavior'].set(ui_settings.get('menu_bar_behavior', 'always_visible'))
            self.form_vars['notification_style'].set(ui_settings.get('notification_style', 'native'))
            self.form_vars['show_transcription_preview'].set(ui_settings.get('show_transcription_preview', True))
            self.form_vars['auto_copy_to_clipboard'].set(ui_settings.get('auto_copy_to_clipboard', True))
            self.form_vars['show_confidence_scores'].set(ui_settings.get('show_confidence_scores', False))
            
            # Handle dark mode (None -> system)
            dark_mode = ui_settings.get('dark_mode')
            if dark_mode is None:
                self.form_vars['dark_mode'].set('system')
            else:
                self.form_vars['dark_mode'].set('dark' if dark_mode else 'light')
            
            # Load audio settings
            audio_settings = current_settings.get('audio_settings', {})
            self.form_vars['input_device'].set(audio_settings.get('input_device', 'Default') or 'Default')
            self.form_vars['noise_reduction_level'].set(audio_settings.get('noise_reduction_level', 'medium'))
            self.form_vars['gain_adjustment'].set(audio_settings.get('gain_adjustment', 1.0))
            self.form_vars['sample_rate'].set(str(audio_settings.get('sample_rate', 16000)))
            self.form_vars['auto_gain_control'].set(audio_settings.get('auto_gain_control', True))
            self.form_vars['voice_activity_detection'].set(audio_settings.get('voice_activity_detection', True))
            
            # Load transcription settings
            trans_settings = current_settings.get('transcription_settings', {})
            self.form_vars['model_name'].set(trans_settings.get('model_name', 'base.en'))
            self.form_vars['language'].set(trans_settings.get('language', 'en'))
            self.form_vars['confidence_threshold'].set(trans_settings.get('confidence_threshold', 0.6))
            self.form_vars['auto_language_detection'].set(trans_settings.get('auto_language_detection', False))
            self.form_vars['custom_vocabulary_enabled'].set(trans_settings.get('custom_vocabulary_enabled', True))
            self.form_vars['timestamping_enabled'].set(trans_settings.get('timestamping_enabled', True))
            self.form_vars['speaker_diarization'].set(trans_settings.get('speaker_diarization', False))
            
            # Load hotkeys
            hotkeys = current_settings.get('hotkeys', {})
            for action, entry_var in self.hotkey_entries.items():
                if action in hotkeys:
                    entry_var.set(hotkeys[action].get('keys', ''))
            
            # Load advanced settings
            adv_settings = current_settings.get('advanced_settings', {})
            self.form_vars['temp_file_location'].set(adv_settings.get('temp_file_location', ''))
            self.form_vars['cleanup_policy'].set(adv_settings.get('cleanup_policy', 'auto'))
            self.form_vars['log_level'].set(adv_settings.get('log_level', 'INFO'))
            self.form_vars['enable_crash_recovery'].set(adv_settings.get('enable_crash_recovery', True))
            self.form_vars['diagnostic_mode'].set(adv_settings.get('diagnostic_mode', False))
            
            # Load profiles
            self._refresh_profiles()
            
        except Exception as e:
            self.logger.error(f"Failed to load current settings: {e}")
            messagebox.showerror("Error", f"Failed to load settings: {e}")
    
    def _refresh_profiles(self):
        """Refresh the profiles dropdown."""
        try:
            profiles = self.config_manager.get_user_profiles()
            profile_names = list(profiles.keys())
            
            self.profile_combo['values'] = profile_names
            
            current_profile = self.config_manager.current_profile
            if current_profile:
                self.profile_var.set(current_profile)
                self._update_profile_details(current_profile)
            
        except Exception as e:
            self.logger.error(f"Failed to refresh profiles: {e}")
    
    def _update_profile_details(self, profile_name: str):
        """Update profile details display."""
        try:
            profiles = self.config_manager.get_user_profiles()
            if profile_name in profiles:
                profile = profiles[profile_name]
                
                details = f"Name: {profile.name}\n"
                details += f"Description: {profile.description}\n"
                details += f"Created: {profile.created_at}\n"
                details += f"Last Used: {profile.last_used}\n"
                details += f"Is Default: {profile.is_default}\n\n"
                
                details += "Audio Settings:\n"
                for key, value in profile.audio_settings.__dict__.items():
                    details += f"  {key}: {value}\n"
                
                details += "\nTranscription Settings:\n"
                for key, value in profile.transcription_settings.__dict__.items():
                    details += f"  {key}: {value}\n"
                
                details += "\nUI Settings:\n"
                for key, value in profile.ui_settings.__dict__.items():
                    details += f"  {key}: {value}\n"
                
                details += f"\nHotkeys: {len(profile.hotkeys)} configured\n"
                
                self.profile_details_text.config(state='normal')
                self.profile_details_text.delete(1.0, tk.END)
                self.profile_details_text.insert(1.0, details)
                self.profile_details_text.config(state='disabled')
            
        except Exception as e:
            self.logger.error(f"Failed to update profile details: {e}")
    
    def _apply_settings(self):
        """Apply current form settings."""
        try:
            current_profile = self.config_manager.current_profile
            if not current_profile:
                messagebox.showerror("Error", "No active profile to update")
                return
            
            # Update UI settings
            ui_dark_mode = self.form_vars['dark_mode'].get()
            dark_mode_value = None if ui_dark_mode == 'system' else (ui_dark_mode == 'dark')
            
            self.config_manager.update_setting('ui_settings.menu_bar_behavior', 
                                             self.form_vars['menu_bar_behavior'].get(), current_profile)
            self.config_manager.update_setting('ui_settings.notification_style', 
                                             self.form_vars['notification_style'].get(), current_profile)
            self.config_manager.update_setting('ui_settings.show_transcription_preview', 
                                             self.form_vars['show_transcription_preview'].get(), current_profile)
            self.config_manager.update_setting('ui_settings.auto_copy_to_clipboard', 
                                             self.form_vars['auto_copy_to_clipboard'].get(), current_profile)
            self.config_manager.update_setting('ui_settings.show_confidence_scores', 
                                             self.form_vars['show_confidence_scores'].get(), current_profile)
            self.config_manager.update_setting('ui_settings.dark_mode', dark_mode_value, current_profile)
            
            # Update audio settings
            self.config_manager.update_setting('audio_settings.noise_reduction_level', 
                                             self.form_vars['noise_reduction_level'].get(), current_profile)
            self.config_manager.update_setting('audio_settings.gain_adjustment', 
                                             self.form_vars['gain_adjustment'].get(), current_profile)
            self.config_manager.update_setting('audio_settings.sample_rate', 
                                             int(self.form_vars['sample_rate'].get()), current_profile)
            self.config_manager.update_setting('audio_settings.auto_gain_control', 
                                             self.form_vars['auto_gain_control'].get(), current_profile)
            self.config_manager.update_setting('audio_settings.voice_activity_detection', 
                                             self.form_vars['voice_activity_detection'].get(), current_profile)
            
            # Update transcription settings
            self.config_manager.update_setting('transcription_settings.model_name', 
                                             self.form_vars['model_name'].get(), current_profile)
            self.config_manager.update_setting('transcription_settings.language', 
                                             self.form_vars['language'].get(), current_profile)
            self.config_manager.update_setting('transcription_settings.confidence_threshold', 
                                             self.form_vars['confidence_threshold'].get(), current_profile)
            self.config_manager.update_setting('transcription_settings.auto_language_detection', 
                                             self.form_vars['auto_language_detection'].get(), current_profile)
            self.config_manager.update_setting('transcription_settings.custom_vocabulary_enabled', 
                                             self.form_vars['custom_vocabulary_enabled'].get(), current_profile)
            self.config_manager.update_setting('transcription_settings.timestamping_enabled', 
                                             self.form_vars['timestamping_enabled'].get(), current_profile)
            self.config_manager.update_setting('transcription_settings.speaker_diarization', 
                                             self.form_vars['speaker_diarization'].get(), current_profile)
            
            # Update hotkeys
            for action, entry_var in self.hotkey_entries.items():
                keys = entry_var.get().strip()
                if keys:
                    self.config_manager.update_hotkey(action, keys, current_profile)
            
            # Update advanced settings (global)
            self.config_manager.update_setting('advanced_settings.temp_file_location', 
                                             self.form_vars['temp_file_location'].get())
            self.config_manager.update_setting('advanced_settings.cleanup_policy', 
                                             self.form_vars['cleanup_policy'].get())
            self.config_manager.update_setting('advanced_settings.log_level', 
                                             self.form_vars['log_level'].get())
            self.config_manager.update_setting('advanced_settings.enable_crash_recovery', 
                                             self.form_vars['enable_crash_recovery'].get())
            self.config_manager.update_setting('advanced_settings.diagnostic_mode', 
                                             self.form_vars['diagnostic_mode'].get())
            
            messagebox.showinfo("Success", "Settings applied successfully!")
            
        except Exception as e:
            self.logger.error(f"Failed to apply settings: {e}")
            messagebox.showerror("Error", f"Failed to apply settings: {e}")
    
    def _ok(self):
        """Apply settings and close window."""
        self._apply_settings()
        self.root.destroy()
    
    def _cancel(self):
        """Close window without applying."""
        self.root.destroy()
    
    def _detect_hotkey(self, action: str):
        """Detect hotkey for action (placeholder)."""
        messagebox.showinfo("Hotkey Detection", f"Hotkey detection for {action} not implemented yet.\nPlease enter the key combination manually.")
    
    def _validate_hotkeys(self):
        """Validate current hotkey configuration."""
        try:
            conflicts = self.config_manager.validate_hotkeys()
            
            total_conflicts = len(conflicts['error']) + len(conflicts['warning'])
            
            if total_conflicts == 0:
                self.hotkey_status_label.config(text="✅ No conflicts", foreground='green')
                messagebox.showinfo("Validation", "No hotkey conflicts detected!")
            else:
                self.hotkey_status_label.config(text=f"⚠️ {total_conflicts} conflicts", foreground='red')
                
                message = "Hotkey Conflicts Detected:\n\n"
                if conflicts['error']:
                    message += "ERRORS:\n" + "\n".join(conflicts['error']) + "\n\n"
                if conflicts['warning']:
                    message += "WARNINGS:\n" + "\n".join(conflicts['warning'])
                
                messagebox.showwarning("Conflicts", message)
                
        except Exception as e:
            self.logger.error(f"Failed to validate hotkeys: {e}")
            messagebox.showerror("Error", f"Failed to validate hotkeys: {e}")
    
    def _on_profile_selected(self, event=None):
        """Handle profile selection change."""
        profile_name = self.profile_var.get()
        if profile_name:
            self._update_profile_details(profile_name)
    
    def _switch_profile(self):
        """Switch to selected profile."""
        try:
            profile_name = self.profile_var.get()
            if profile_name and self.config_manager.switch_profile(profile_name):
                self._load_current_settings()
                messagebox.showinfo("Success", f"Switched to profile '{profile_name}'")
            else:
                messagebox.showerror("Error", "Failed to switch profile")
                
        except Exception as e:
            self.logger.error(f"Failed to switch profile: {e}")
            messagebox.showerror("Error", f"Failed to switch profile: {e}")
    
    def _create_new_profile(self):
        """Create a new profile."""
        try:
            name = simpledialog.askstring("New Profile", "Enter profile name:")
            if name:
                description = simpledialog.askstring("New Profile", "Enter profile description:")
                if self.config_manager.create_profile(name, description or ""):
                    self._refresh_profiles()
                    messagebox.showinfo("Success", f"Profile '{name}' created successfully!")
                else:
                    messagebox.showerror("Error", "Failed to create profile")
                    
        except Exception as e:
            self.logger.error(f"Failed to create profile: {e}")
            messagebox.showerror("Error", f"Failed to create profile: {e}")
    
    def _copy_profile(self):
        """Copy current profile."""
        try:
            current_profile = self.config_manager.current_profile
            if not current_profile:
                messagebox.showerror("Error", "No active profile to copy")
                return
            
            name = simpledialog.askstring("Copy Profile", "Enter new profile name:")
            if name:
                description = simpledialog.askstring("Copy Profile", "Enter profile description:")
                if self.config_manager.create_profile(name, description or "", copy_from=current_profile):
                    self._refresh_profiles()
                    messagebox.showinfo("Success", f"Profile '{name}' created from '{current_profile}'!")
                else:
                    messagebox.showerror("Error", "Failed to copy profile")
                    
        except Exception as e:
            self.logger.error(f"Failed to copy profile: {e}")
            messagebox.showerror("Error", f"Failed to copy profile: {e}")
    
    def _delete_profile(self):
        """Delete selected profile."""
        try:
            profile_name = self.profile_var.get()
            if not profile_name:
                messagebox.showerror("Error", "No profile selected")
                return
            
            if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete profile '{profile_name}'?"):
                if self.config_manager.delete_profile(profile_name):
                    self._refresh_profiles()
                    self._load_current_settings()
                    messagebox.showinfo("Success", f"Profile '{profile_name}' deleted!")
                else:
                    messagebox.showerror("Error", "Failed to delete profile")
                    
        except Exception as e:
            self.logger.error(f"Failed to delete profile: {e}")
            messagebox.showerror("Error", f"Failed to delete profile: {e}")
    
    def _rename_profile(self):
        """Rename selected profile (placeholder)."""
        messagebox.showinfo("Not Implemented", "Profile renaming not implemented yet.")
    
    def _browse_temp_location(self):
        """Browse for temp file location."""
        try:
            directory = filedialog.askdirectory(title="Select Temp File Location")
            if directory:
                self.form_vars['temp_file_location'].set(directory)
                
        except Exception as e:
            self.logger.error(f"Failed to browse temp location: {e}")
    
    def _export_settings(self):
        """Export settings to file."""
        try:
            file_path = filedialog.asksaveasfilename(
                title="Export Settings",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if file_path:
                if self.config_manager.export_settings(file_path):
                    messagebox.showinfo("Success", f"Settings exported to {file_path}")
                else:
                    messagebox.showerror("Error", "Failed to export settings")
                    
        except Exception as e:
            self.logger.error(f"Failed to export settings: {e}")
            messagebox.showerror("Error", f"Failed to export settings: {e}")
    
    def _import_settings(self):
        """Import settings from file."""
        try:
            file_path = filedialog.askopenfilename(
                title="Import Settings",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if file_path:
                if messagebox.askyesno("Confirm Import", "This will merge imported settings with current settings. Continue?"):
                    if self.config_manager.import_settings(file_path):
                        self._refresh_profiles()
                        self._load_current_settings()
                        messagebox.showinfo("Success", "Settings imported successfully!")
                    else:
                        messagebox.showerror("Error", "Failed to import settings")
                        
        except Exception as e:
            self.logger.error(f"Failed to import settings: {e}")
            messagebox.showerror("Error", f"Failed to import settings: {e}")
    
    def _reset_current_profile(self):
        """Reset current profile to defaults."""
        try:
            current_profile = self.config_manager.current_profile
            if not current_profile:
                messagebox.showerror("Error", "No active profile to reset")
                return
            
            if messagebox.askyesno("Confirm Reset", f"Reset profile '{current_profile}' to defaults?"):
                if self.config_manager.reset_to_defaults(current_profile):
                    self._load_current_settings()
                    messagebox.showinfo("Success", f"Profile '{current_profile}' reset to defaults!")
                else:
                    messagebox.showerror("Error", "Failed to reset profile")
                    
        except Exception as e:
            self.logger.error(f"Failed to reset profile: {e}")
            messagebox.showerror("Error", f"Failed to reset profile: {e}")
    
    def _reset_all_settings(self):
        """Reset all settings to defaults."""
        try:
            if messagebox.askyesno("Confirm Reset", "Reset ALL settings to defaults? This cannot be undone!"):
                if self.config_manager.reset_to_defaults():
                    self._refresh_profiles()
                    self._load_current_settings()
                    messagebox.showinfo("Success", "All settings reset to defaults!")
                else:
                    messagebox.showerror("Error", "Failed to reset settings")
                    
        except Exception as e:
            self.logger.error(f"Failed to reset settings: {e}")
            messagebox.showerror("Error", f"Failed to reset settings: {e}")
    
    def show(self):
        """Show the preferences window."""
        self.root.mainloop()


def main():
    """Test the preferences GUI."""
    import tempfile
    
    logging.basicConfig(level=logging.INFO)
    
    # Test with temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        config_manager = ConfigManager(temp_dir)
        preferences_gui = PreferencesGUI(config_manager)
        preferences_gui.show()


if __name__ == "__main__":
    main() 