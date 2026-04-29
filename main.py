"""
XenShoot - Screenshot tool with annotation and auto-upload
Similar to Flameshot but with automatic URL generation
"""

import sys
from PyQt5.QtWidgets import QApplication
from src.main_window import MainWindow
from src.screenshot_overlay import ScreenshotOverlay
from src.hotkey_manager import HotkeyManager

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("XenShoot")
    app.setOrganizationName("XenShoot")
    
    # CRITICAL: Prevent app from quitting when screenshot overlay closes
    # Since main window is hidden, Qt would quit when overlay closes
    app.setQuitOnLastWindowClosed(False)
    
    # Create main window (system tray)
    main_window = MainWindow()
    
    # Setup hotkey manager
    hotkey_manager = HotkeyManager(main_window)
    hotkey_manager.start()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
