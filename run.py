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

    # ── Auth flow ─────────────────────────────────────────────────────────────
    from src.config_manager import ConfigManager
    from src.auth_manager   import AuthManager
    from src.splash_dialog  import SplashDialog
    from src.setup_wizard   import SetupWizard

    config       = ConfigManager()
    auth_manager = AuthManager(config)

    # Show splash + check credentials in background
    splash = SplashDialog(auth_manager)
    splash.show()
    app.processEvents()
    splash.start_check()

    auth_ok    = [False]
    auth_error = [""]

    def _on_auth_result(ok, err):
        auth_ok[0]    = ok
        auth_error[0] = err

    splash.auth_result.connect(_on_auth_result)
    splash.exec_()   # blocks until splash closes

    # If not authenticated, show setup wizard
    if not auth_ok[0]:
        wizard = SetupWizard(auth_manager, config, prefill_error=auth_error[0])
        screen = QApplication.primaryScreen().availableGeometry()
        wizard.adjustSize()
        wizard.move(
            screen.center().x() - wizard.width()  // 2,
            screen.center().y() - wizard.height() // 2,
        )
        result = wizard.exec_()
        if result != wizard.Accepted:
            sys.exit(0)   # user closed wizard → quit

    # ── Main app ──────────────────────────────────────────────────────────────
    print("Creating main window...")
    main_window = MainWindow(config=config)
    app.setProperty("main_window", main_window)
    print("Main window created!")

    print("Setting up hotkey manager...")
    hotkey_manager = HotkeyManager(main_window)

    def show_hotkey_error(error_msg):
        print(f"[ERROR] Hotkey manager: {error_msg}")
        QMessageBox.warning(None, "Hotkey Warning",
            f"{error_msg}\n\nYou can still use:\n"
            "- Right-click tray icon\n"
            "- System tray menu")

    hotkey_manager.error_signal.connect(show_hotkey_error)
    hotkey_manager.start()
    main_window.hotkey_manager = hotkey_manager
    print("Hotkey manager started!")

    print("\nKShot is running!")
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
