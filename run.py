"""
Run XenShoot with error catching
"""

import sys
import traceback

# Fix encoding for Windows console (not available when compiled without console)
if sys.stdout is not None:
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Windows: override taskbar icon (must be called before QApplication)
try:
    import ctypes
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("KShot")
except Exception:
    pass

try:
    from PyQt5.QtWidgets import QApplication, QMessageBox
    from src.main_window import MainWindow
    from src.hotkey_manager import HotkeyManager
    
    print("Starting KShot...")
    print("Press Ctrl+Shift+A for area screenshot")
    print("Press Ctrl+Shift+F for fullscreen screenshot")
    print("Check system tray for icon")
    print("-" * 50)
    
    app = QApplication(sys.argv)
    app.setApplicationName("KShot")
    app.setOrganizationName("KShot")

    # Set app-wide icon (shows in taskbar for all windows)
    import os as _os_icon
    from PyQt5.QtGui import QIcon as _QIcon
    _icon_path = _os_icon.path.join(_os_icon.path.dirname(__file__), 'src', 'Logo', 'logo.png')
    if _os_icon.path.exists(_icon_path):
        app.setWindowIcon(_QIcon(_icon_path))

    # Load Poppins font and set as app-wide default
    from PyQt5.QtGui import QFontDatabase, QFont
    import os as _os
    _font_dir = _os.path.join(_os.path.dirname(__file__), 'src', 'fonts')
    for _fname in ('Poppins-Regular.ttf', 'Poppins-Bold.ttf', 'Poppins-Medium.ttf'):
        _fpath = _os.path.join(_font_dir, _fname)
        if _os.path.exists(_fpath):
            QFontDatabase.addApplicationFont(_fpath)
    _poppins = QFont("Poppins", 10)
    if _poppins.family() == "Poppins":
        app.setFont(_poppins)

    # CRITICAL: Prevent app from quitting when screenshot overlay closes
    app.setQuitOnLastWindowClosed(False)
    
    # Create main window (system tray)
    print("Creating main window...")
    main_window = MainWindow()
    app.setProperty("main_window", main_window)   # accessible from overlay
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
    main_window.hotkey_manager = hotkey_manager   # allow settings to reload hotkeys
    print("Hotkey manager started!")
    
    print("\nXenShoot is running!")
    print("Look for the blue circle icon in system tray (bottom-right)")
    print("\nTo test:")
    print("1. Press Ctrl+Shift+A (or Ctrl+Shift+F)")
    print("2. Or right-click tray icon -> Capture Screenshot")
    print("-" * 50)
    
    sys.exit(app.exec_())
    
except Exception as e:
    try:
        import traceback as _tb
        _tb.print_exc()
    except Exception:
        pass
    # Show error in GUI since there's no console in compiled mode
    try:
        from PyQt5.QtWidgets import QApplication, QMessageBox
        _app = QApplication.instance() or QApplication([])
        QMessageBox.critical(None, "KShot Error", f"{type(e).__name__}: {e}")
    except Exception:
        pass
