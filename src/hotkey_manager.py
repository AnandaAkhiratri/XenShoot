"""
Global hotkey manager for KShot
"""

from pynput import keyboard
from PyQt5.QtCore import QThread, pyqtSignal
import threading
import sys

class HotkeyManager(QThread):
    capture_signal = pyqtSignal()
    capture_fullscreen_signal = pyqtSignal()
    open_settings_signal = pyqtSignal()
    error_signal = pyqtSignal(str)
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.capture_signal.connect(main_window.start_capture)
        self.capture_fullscreen_signal.connect(main_window.capture_fullscreen)
        self.open_settings_signal.connect(main_window.show_settings)
        
        # Get hotkeys from config
        config = main_window.config
        self.area_hotkey     = self.parse_hotkey(config.get('hotkey_area',       'ctrl+shift+a'))
        self.full_hotkey     = self.parse_hotkey(config.get('hotkey_fullscreen',  'ctrl+shift+f'))
        self.settings_hotkey = self.parse_hotkey(config.get('hotkey_settings',    'ctrl+shift+s'))
        
        self.current_keys = set()
        self.lock = threading.Lock()
        self.triggered_area     = False
        self.triggered_full     = False
        self.triggered_settings = False
        self.listener = None
        self.running = False
        
    def parse_hotkey(self, hotkey_str):
        """Parse hotkey string to set of keys"""
        parts = hotkey_str.lower().split('+')
        keys = set()
        
        for part in parts:
            part = part.strip()
            if part == 'ctrl':
                keys.add('ctrl')
            elif part == 'shift':
                keys.add('shift')
            elif part == 'alt':
                keys.add('alt')
            elif part == 'win' or part == 'cmd':
                keys.add('win')
            else:
                keys.add(part)
                    
        return keys
        
    def run(self):
        """Run hotkey listener"""
        try:
            self.running = True
            self.listener = keyboard.Listener(
                on_press=self.on_press,
                on_release=self.on_release,
                suppress=False  # Don't suppress keys for other apps
            )
            self.listener.start()
            
            # Keep thread alive
            while self.running:
                self.msleep(100)
                
        except Exception as e:
            error_msg = f"Failed to start keyboard listener: {e}\n\nTry running as Administrator or use tray menu."
            print(f"[HotkeyManager] ERROR: {error_msg}")
            self.error_signal.emit(error_msg)
            
    def stop(self):
        """Stop the hotkey listener"""
        self.running = False
        if self.listener:
            self.listener.stop()

    def update_hotkeys(self, area_str, full_str, settings_str=None):
        """Restart listener with new hotkey strings (called after settings save)"""
        self.area_hotkey     = self.parse_hotkey(area_str)
        self.full_hotkey     = self.parse_hotkey(full_str)
        if settings_str:
            self.settings_hotkey = self.parse_hotkey(settings_str)
        self.current_keys.clear()
        self.triggered_area     = False
        self.triggered_full     = False
        self.triggered_settings = False
        # Restart the pynput listener so it picks up nothing stale
        if self.listener:
            self.listener.stop()
        self.listener = keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release,
            suppress=False
        )
        self.listener.start()
            
    def normalize_key(self, key):
        """Normalize key to string"""
        if isinstance(key, keyboard.Key):
            if key in [keyboard.Key.ctrl_l, keyboard.Key.ctrl_r, keyboard.Key.ctrl]:
                return 'ctrl'
            elif key in [keyboard.Key.shift, keyboard.Key.shift_r, keyboard.Key.shift_l]:
                return 'shift'
            elif key in [keyboard.Key.alt_l, keyboard.Key.alt_r, keyboard.Key.alt, keyboard.Key.alt_gr]:
                return 'alt'
            elif key in [keyboard.Key.cmd, keyboard.Key.cmd_l, keyboard.Key.cmd_r]:
                return 'win'
            elif key == keyboard.Key.print_screen:
                return 'print_screen'
        elif isinstance(key, keyboard.KeyCode):
            if hasattr(key, 'char') and key.char:
                char = key.char
                # Handle control characters (Ctrl+letter produces \x01-\x1a)
                if ord(char) >= 1 and ord(char) <= 26:
                    # Convert control char back to letter (Ctrl+A = \x01 -> 'a')
                    return chr(ord(char) + 96)  # \x01 + 96 = 'a' (97)
                return char.lower()
            # Handle keys with vk code but no char (like function keys)
            elif hasattr(key, 'vk'):
                # Map common vk codes to key names
                if key.vk == 112: return 'f1'
                elif key.vk == 113: return 'f2'
                elif key.vk == 114: return 'f3'
                elif key.vk == 115: return 'f4'
                elif key.vk == 116: return 'f5'
                elif key.vk == 117: return 'f6'
                elif key.vk == 118: return 'f7'
                elif key.vk == 119: return 'f8'
                elif key.vk == 120: return 'f9'
                elif key.vk == 121: return 'f10'
                elif key.vk == 122: return 'f11'
                elif key.vk == 123: return 'f12'
        return None
            
    def on_press(self, key):
        """Handle key press"""
        try:
            with self.lock:
                normalized = self.normalize_key(key)
                if normalized:
                    self.current_keys.add(normalized)

                # Print Screen → area capture (fixed, not configurable)
                if normalized == 'print_screen' and not self.triggered_area:
                    self.triggered_area = True
                    self.capture_signal.emit()
                    return

                # Check for configurable area capture hotkey (secondary)
                if not self.triggered_area and self.area_hotkey.issubset(self.current_keys):
                    self.triggered_area = True
                    self.capture_signal.emit()

                # Check for fullscreen capture hotkey
                if not self.triggered_full and self.full_hotkey.issubset(self.current_keys):
                    self.triggered_full = True
                    self.capture_fullscreen_signal.emit()

                # Check for open settings hotkey
                if not self.triggered_settings and self.settings_hotkey.issubset(self.current_keys):
                    self.triggered_settings = True
                    self.open_settings_signal.emit()
        except Exception as e:
            print(f"[HotkeyManager] Error in on_press: {e}")
            
    def on_release(self, key):
        """Handle key release"""
        try:
            with self.lock:
                normalized = self.normalize_key(key)
                if normalized:
                    self.current_keys.discard(normalized)
                    
                # Reset all triggers on any key release
                # (covers cases where modifier release is missed due to focus change)
                self.triggered_area     = False
                self.triggered_full     = False
                self.triggered_settings = False
        except Exception as e:
            print(f"[HotkeyManager] Error in on_release: {e}")
