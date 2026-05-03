"""
Configuration manager for XenShoot
"""

import json
import os
from pathlib import Path

class ConfigManager:
    def __init__(self):
        self.config_dir = Path.home() / ".xenshoot"
        self.config_file = self.config_dir / "config.json"
        self.config = self.load_config()
        
    def load_config(self):
        """Load configuration from file"""
        if not self.config_dir.exists():
            self.config_dir.mkdir(parents=True)
            
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except:
                return self.default_config()
        else:
            config = self.default_config()
            self.save_config(config)
            return config
            
    def default_config(self):
        """Return default configuration"""
        return {
            'upload_service': 'backblaze',
            
            # BackBlaze B2 Storage (Primary)
            'backblaze_bucket_id': '63bf91f04bf0f57e99cb061f',
            'backblaze_endpoint': 's3.us-east-005.backblazeb2.com',
            'backblaze_access_key_id': '0053f10b05e9b6f0000000001',
            'backblaze_secret_access_key': 'K005+CqN5dlkoFX7ibbcA0Jx2gXtm0E',
            'backblaze_bucket_name': 'XenShot',
            
            # Laravel API Integration
            'laravel_api_url': 'https://xenshot.cloud',
            'laravel_user_id': 1,  # Default user ID for testing
            
            # Other services (optional)
            'imgbb_api_key': '',
            'imgbb_url_type': 'page',
            'imgur_client_id': '',
            'cloudinary_cloud_name': '',
            'cloudinary_upload_preset': 'xenshoot',
            'custom_endpoint': '',
            
            # Global hotkeys
            'hotkey_area': 'ctrl+shift+a',
            'hotkey_fullscreen': 'ctrl+shift+f',

            # In-capture shortcuts
            'shortcut_save':        'return',
            'shortcut_cancel':      'escape',
            'shortcut_copy':        'ctrl+c',
            'shortcut_undo':        'ctrl+z',
            'shortcut_redo':        'ctrl+y',
            'shortcut_pen':         'p',
            'shortcut_line':        'l',
            'shortcut_arrow':       'a',
            'shortcut_rect':        'r',
            'shortcut_circle':      'c',
            'shortcut_highlighter': 'm',
            'shortcut_text':        't',
            'shortcut_number':      'n',
            'shortcut_blur':        'b',
            'shortcut_invert':      'i',
            
            # Local settings
            'save_local_copy': True,
            'local_save_path': str(Path.home() / "Pictures" / "XenShoot"),
            'auto_copy_url': True,
            'show_notification': True,

            # Filename
            'filename_template': 'xenshoot_%Y-%m-%d_%H-%M-%S',
            'preferred_extension': 'png',
            'jpeg_quality': 90,

            # Interface
            'overlay_opacity': 100,   # 0-255, darkness of area outside selection
            'selection_color': '#f5cb11',  # selection border + handle color
            'toolbar_bg_color': '#000a52',   # toolbar button background
            'toolbar_icon_color': '#f5cb11', # toolbar icon / text color
            'color_presets': [
                '#f5cb11', '#ff4444', '#ff8800', '#44cc44',
                '#4488ff', '#cc44ff', '#ffffff', '#000000',
            ],
            'hidden_buttons': [],     # list of button names to hide
        }
        
    def save_config(self, config=None):
        """Save configuration to file"""
        if config:
            self.config = config
            
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)
            
    def get(self, key, default=None):
        """Get configuration value"""
        return self.config.get(key, default)
        
    def set(self, key, value):
        """Set configuration value"""
        self.config[key] = value
        self.save_config()
