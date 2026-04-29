"""
Settings dialog for XenShoot
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QCheckBox,
                             QGroupBox, QFormLayout, QFileDialog, QTabWidget,
                             QWidget)
from PyQt5.QtCore import Qt

class SettingsDialog(QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.init_ui()
        self.load_settings()
        
    def init_ui(self):
        self.setWindowTitle("XenShoot Settings")
        self.setModal(True)
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout()
        
        # Create tabs
        tabs = QTabWidget()
        
        # Upload settings tab - HIDDEN (pre-configured)
        # upload_tab = self.create_upload_tab()
        # tabs.addTab(upload_tab, "Storage")
        
        # General settings tab
        general_tab = self.create_general_tab()
        tabs.addTab(general_tab, "General")
        
        # Hotkeys tab
        hotkeys_tab = self.create_hotkeys_tab()
        tabs.addTab(hotkeys_tab, "Hotkeys")
        
        layout.addWidget(tabs)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_settings)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def create_upload_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # BackBlaze B2 settings
        backblaze_group = QGroupBox("BackBlaze B2 Cloud Storage")
        backblaze_layout = QFormLayout()
        
        self.backblaze_bucket_id_input = QLineEdit()
        self.backblaze_bucket_id_input.setPlaceholderText("63bf91f04bf0f57e99cb061f")
        backblaze_layout.addRow("Bucket ID:", self.backblaze_bucket_id_input)
        
        self.backblaze_endpoint_input = QLineEdit()
        self.backblaze_endpoint_input.setPlaceholderText("s3.us-east-005.backblazeb2.com")
        backblaze_layout.addRow("Endpoint:", self.backblaze_endpoint_input)
        
        self.backblaze_access_key_input = QLineEdit()
        self.backblaze_access_key_input.setPlaceholderText("0053f10b05e9b6f0000000001")
        backblaze_layout.addRow("Access Key ID:", self.backblaze_access_key_input)
        
        self.backblaze_secret_key_input = QLineEdit()
        self.backblaze_secret_key_input.setPlaceholderText("K005+CqN5dlkoFX7ibbcA0Jx2gXtm0E")
        self.backblaze_secret_key_input.setEchoMode(QLineEdit.EchoMode.Password)  # Hide text with bullets
        backblaze_layout.addRow("Secret Key:", self.backblaze_secret_key_input)
        
        self.backblaze_bucket_name_input = QLineEdit()
        self.backblaze_bucket_name_input.setPlaceholderText("XenShot")
        backblaze_layout.addRow("Bucket Name:", self.backblaze_bucket_name_input)
        
        backblaze_help = QLabel(
            '<b>BackBlaze B2 Cloud Storage</b><br><br>'
            'All credentials are pre-configured and ready to use.<br>'
            'Screenshots are automatically uploaded to BackBlaze B2.<br><br>'
            '<b>Storage Details:</b><br>'
            '• Cost: $0.005/GB per month<br>'
            '• Free: First 10GB storage<br>'
            '• Speed: Global CDN delivery<br>'
            '• Control: Your own private storage<br><br>'
            '<b>Important:</b> Bucket must be set to <b>Public</b> in BackBlaze console<br>'
            'for URLs to work properly.'
        )
        backblaze_help.setOpenExternalLinks(True)
        backblaze_help.setWordWrap(True)
        backblaze_help.setStyleSheet(
            "color: #2c3e50; font-size: 10px; padding: 10px; "
            "background-color: #ecf0f1; border-radius: 5px; "
            "border-left: 4px solid #3498db;"
        )
        backblaze_layout.addRow("", backblaze_help)
        
        backblaze_group.setLayout(backblaze_layout)
        layout.addWidget(backblaze_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_general_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Local save settings
        save_group = QGroupBox("Local Save")
        save_layout = QFormLayout()
        
        self.save_local_check = QCheckBox("Save local copy of screenshots")
        save_layout.addRow(self.save_local_check)
        
        path_layout = QHBoxLayout()
        self.save_path_input = QLineEdit()
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_save_path)
        path_layout.addWidget(self.save_path_input)
        path_layout.addWidget(browse_btn)
        save_layout.addRow("Save Path:", path_layout)
        
        save_group.setLayout(save_layout)
        layout.addWidget(save_group)
        
        # Notification settings
        notif_group = QGroupBox("Notifications")
        notif_layout = QVBoxLayout()
        
        self.auto_copy_check = QCheckBox("Automatically copy URL to clipboard")
        self.auto_copy_check.setChecked(True)
        notif_layout.addWidget(self.auto_copy_check)
        
        self.show_notif_check = QCheckBox("Show notification after upload")
        self.show_notif_check.setChecked(True)
        notif_layout.addWidget(self.show_notif_check)
        
        notif_group.setLayout(notif_layout)
        layout.addWidget(notif_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
        
    def create_hotkeys_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        hotkey_group = QGroupBox("Keyboard Shortcuts")
        hotkey_layout = QFormLayout()
        
        self.hotkey_area_input = QLineEdit()
        self.hotkey_area_input.setPlaceholderText("ctrl+shift+a")
        hotkey_layout.addRow("Area Screenshot:", self.hotkey_area_input)
        
        self.hotkey_full_input = QLineEdit()
        self.hotkey_full_input.setPlaceholderText("ctrl+shift+f")
        hotkey_layout.addRow("Fullscreen Screenshot:", self.hotkey_full_input)
        
        help_label = QLabel("Note: Hotkey changes require restart")
        help_label.setStyleSheet("color: gray; font-style: italic;")
        hotkey_layout.addRow("", help_label)
        
        hotkey_group.setLayout(hotkey_layout)
        layout.addWidget(hotkey_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
        
    def browse_save_path(self):
        path = QFileDialog.getExistingDirectory(self, "Select Save Directory")
        if path:
            self.save_path_input.setText(path)
            
    def load_settings(self):
        """Load settings from config"""
        # BackBlaze settings - SKIP (hidden tab, pre-configured)
        # self.backblaze_bucket_id_input.setText(self.config.get('backblaze_bucket_id', ''))
        # self.backblaze_endpoint_input.setText(self.config.get('backblaze_endpoint', ''))
        # self.backblaze_access_key_input.setText(self.config.get('backblaze_access_key_id', ''))
        # self.backblaze_secret_key_input.setText(self.config.get('backblaze_secret_access_key', ''))
        # self.backblaze_bucket_name_input.setText(self.config.get('backblaze_bucket_name', 'XenShot'))
        
        # General settings
        self.save_local_check.setChecked(self.config.get('save_local_copy', True))
        self.save_path_input.setText(self.config.get('local_save_path', ''))
        self.auto_copy_check.setChecked(self.config.get('auto_copy_url', True))
        self.show_notif_check.setChecked(self.config.get('show_notification', True))
        
        # Hotkeys
        self.hotkey_area_input.setText(self.config.get('hotkey_area', 'ctrl+shift+a'))
        self.hotkey_full_input.setText(self.config.get('hotkey_fullscreen', 'ctrl+shift+f'))
        
    def save_settings(self):
        """Save settings to config"""
        # Upload service is always backblaze (fixed)
        self.config.set('upload_service', 'backblaze')
        
        # BackBlaze settings - SKIP (hidden tab, pre-configured, don't overwrite)
        # self.config.set('backblaze_bucket_id', self.backblaze_bucket_id_input.text().strip())
        # self.config.set('backblaze_endpoint', self.backblaze_endpoint_input.text().strip())
        # self.config.set('backblaze_access_key_id', self.backblaze_access_key_input.text().strip())
        # self.config.set('backblaze_secret_access_key', self.backblaze_secret_key_input.text().strip())
        # self.config.set('backblaze_bucket_name', self.backblaze_bucket_name_input.text().strip())
        
        # General settings
        self.config.set('save_local_copy', self.save_local_check.isChecked())
        self.config.set('local_save_path', self.save_path_input.text())
        self.config.set('auto_copy_url', self.auto_copy_check.isChecked())
        self.config.set('show_notification', self.show_notif_check.isChecked())
        
        # Hotkeys
        self.config.set('hotkey_area', self.hotkey_area_input.text())
        self.config.set('hotkey_fullscreen', self.hotkey_full_input.text())
        
        self.accept()
