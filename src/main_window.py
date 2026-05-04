"""
Main window and system tray for KShot
"""

from PyQt5.QtWidgets import QMainWindow, QSystemTrayIcon, QMenu, QAction, QApplication
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt5.QtCore import Qt
from .screenshot_overlay import ScreenshotOverlay
from .config_manager import ConfigManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = ConfigManager()
        self.screenshot_overlay = None
        self.hotkey_manager = None   # set by run.py after HotkeyManager is created
        self.init_ui()
        self.init_tray()
        
    def init_ui(self):
        self.setWindowTitle("KShot")
        self.setGeometry(100, 100, 400, 300)
        # Hide main window, only show tray icon
        self.hide()
        
    def init_tray(self):
        # Load icon from file
        import os
        icon_path = os.path.join(os.path.dirname(__file__), "Logo", "logo.png")
        
        if os.path.exists(icon_path):
            # Use custom icon from file
            original_pixmap = QPixmap(icon_path)
            
            # Create a larger tray icon (128x128) for better clarity
            # Windows will scale it down with better quality
            icon_size = 128
            icon_pixmap = original_pixmap.scaled(
                icon_size, icon_size, 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            
            # If image has transparency issues, add a subtle background
            if icon_pixmap.hasAlphaChannel():
                final_pixmap = QPixmap(icon_size, icon_size)
                final_pixmap.fill(Qt.transparent)
                painter = QPainter(final_pixmap)
                painter.setRenderHint(QPainter.Antialiasing)
                painter.setRenderHint(QPainter.SmoothPixmapTransform)
                
                # Draw with high quality
                painter.drawPixmap(0, 0, icon_pixmap)
                painter.end()
                icon_pixmap = final_pixmap
        else:
            # Fallback: Create a simple icon programmatically
            icon_pixmap = QPixmap(128, 128)
            icon_pixmap.fill(Qt.transparent)
            painter = QPainter(icon_pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setBrush(QColor(245, 203, 17))  # Yellow
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(8, 8, 112, 112)
            painter.end()
        
        self.tray_icon = QSystemTrayIcon(QIcon(icon_pixmap), self)
        
        # Create tray menu
        tray_menu = QMenu()
        
        capture_action = QAction("Area Capture", self)
        capture_action.triggered.connect(self.start_capture)
        
        fullscreen_action = QAction("Fullscreen Capture", self)
        fullscreen_action.triggered.connect(self.capture_fullscreen)
        
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.show_settings)
        
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.quit_app)
        
        tray_menu.addAction(capture_action)
        tray_menu.addAction(fullscreen_action)
        tray_menu.addSeparator()
        tray_menu.addAction(settings_action)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.setToolTip("KShot")
        self.tray_icon.show()
        
        # Show welcome notification when app starts
        # self.show_startup_notification()
        
    def show_startup_notification(self):
        """Show notification when app starts"""
        if self.tray_icon.supportsMessages():
            self.tray_icon.showMessage(
                "KShot",
                "Hello, I'm here! Click icon in the tray to take a screenshot or click with a right button to see more options.",
                QSystemTrayIcon.NoIcon,
                3000
            )

    def show_upload_notification(self, url, copied=True):
        """Show tray notification after upload."""
        if self.tray_icon.supportsMessages():
            msg = "URL copied to clipboard!" if copied else f"Uploaded: {url}"
            self.tray_icon.showMessage("Image Uploaded!", msg, QSystemTrayIcon.NoIcon, 4000)
        
    def start_capture(self):
        """Start area screenshot capture"""
        try:
            if self.screenshot_overlay is None or not self.screenshot_overlay.isVisible():
                self.screenshot_overlay = ScreenshotOverlay(self.config)
                self.screenshot_overlay.main_window = self
                self.screenshot_overlay.show()
        except Exception as e:
            print(f"Error starting capture: {e}")
            import traceback
            traceback.print_exc()
            
    def capture_fullscreen(self):
        """Capture fullscreen immediately"""
        try:
            if self.screenshot_overlay is None or not self.screenshot_overlay.isVisible():
                self.screenshot_overlay = ScreenshotOverlay(self.config, fullscreen=True)
                self.screenshot_overlay.main_window = self
                self.screenshot_overlay.show()
        except Exception as e:
            print(f"Error capturing fullscreen: {e}")
            import traceback
            traceback.print_exc()
            
    def show_settings(self):
        """Show settings dialog centered on screen"""
        # Prevent opening multiple instances
        if hasattr(self, '_settings_open') and self._settings_open:
            return
        self._settings_open = True
        from .settings_dialog import SettingsDialog
        dialog = SettingsDialog(self.config, None)
        # Center on primary screen
        screen = QApplication.primaryScreen().availableGeometry()
        dialog.adjustSize()
        dialog.move(
            screen.center().x() - dialog.width() // 2,
            screen.center().y() - dialog.height() // 2,
        )
        result = dialog.exec_()
        self._settings_open = False
        if result == dialog.Accepted and self.hotkey_manager:
            # Apply new hotkeys immediately without restart
            self.hotkey_manager.update_hotkeys(
                self.config.get('hotkey_area',       'ctrl+shift+a'),
                self.config.get('hotkey_fullscreen',  'ctrl+shift+f'),
                self.config.get('hotkey_settings',    'ctrl+shift+s'),
            )
        
    def quit_app(self):
        """Quit application"""
        self.tray_icon.hide()
        QApplication.quit()
