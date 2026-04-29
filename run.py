"""
Run XenShoot with error catching
"""

import sys
import traceback

# Fix encoding for Windows console
sys.stdout.reconfigure(encoding='utf-8')

try:
    from PyQt5.QtWidgets import QApplication, QMessageBox
    from src.main_window import MainWindow
    from src.hotkey_manager import HotkeyManager
    
    print("Starting XenShoot...")
    print("Press Ctrl+Shift+A for area screenshot")
    print("Press Ctrl+Shift+F for fullscreen screenshot")
    print("Check system tray for icon")
    print("-" * 50)
    
    app = QApplication(sys.argv)
    app.setApplicationName("XenShoot")
    app.setOrganizationName("XenShoot")
    
    # CRITICAL: Prevent app from quitting when screenshot overlay closes
    app.setQuitOnLastWindowClosed(False)
    
    # Create main window (system tray)
    print("Creating main window...")
    main_window = MainWindow()
    print("Main window created!")
    
    # Setup hotkey manager
    print("Setting up hotkey manager...")
    hotkey_manager = HotkeyManager(main_window)
    
    # Connect error signal
    def show_hotkey_error(error_msg):
        print(f"[ERROR] Hotkey manager: {error_msg}")
        # Show warning but don't block app
        QMessageBox.warning(None, "Hotkey Warning", 
            f"{error_msg}\n\nYou can still use:\n"
            "- Right-click tray icon\n"
            "- System tray menu")
    
    hotkey_manager.error_signal.connect(show_hotkey_error)
    hotkey_manager.start()
    print("Hotkey manager started!")
    
    print("\nXenShoot is running!")
    print("Look for the blue circle icon in system tray (bottom-right)")
    print("\nTo test:")
    print("1. Press Ctrl+Shift+A (or Ctrl+Shift+F)")
    print("2. Or right-click tray icon -> Capture Screenshot")
    print("-" * 50)
    
    sys.exit(app.exec_())
    
except Exception as e:
    print(f"\nERROR: {e}")
    print("\nFull traceback:")
    traceback.print_exc()
    input("\nPress Enter to exit...")
