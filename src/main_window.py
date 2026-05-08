"""
Main window and system tray for KShot
"""

from PyQt5.QtWidgets import (
    QMainWindow, QSystemTrayIcon, QMenu, QAction,
    QApplication, QMessageBox,
)
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt5.QtCore import Qt
from .screenshot_overlay import ScreenshotOverlay
from .config_manager import ConfigManager
from .auth_manager import AuthManager


class MainWindow(QMainWindow):
    def __init__(self, config=None):
        super().__init__()
        self.config = config if config is not None else ConfigManager()
        self.auth   = AuthManager(self.config)
        self.screenshot_overlay = None
        self.hotkey_manager     = None   # set by run.py

        # ── Auth gate ─────────────────────────────────────────────────────
        if not self._ensure_authenticated():
            raise SystemExit(0)

        self.init_ui()
        self.init_tray()

    # ── Auth helpers ──────────────────────────────────────────────────────────

    def _ensure_authenticated(self) -> bool:
        """
        Make sure a valid session exists.
        Priority:
          1. Existing valid session (verified against server)
          2. Pending credentials written by the installer (auto-login)
          3. Setup wizard shown to the user
        Returns True when authenticated, False if the user cancels.
        """
        # 1. Check existing session
        if self.auth.is_logged_in():
            if self.auth.verify_session():
                print(f"[AUTH] Logged in as {self.auth.name} ({self.auth.username})")
                return True
            else:
                print("[AUTH] Stored session is invalid — re-authenticating.")
                self.auth.logout()

        # 2. Try auto-login from installer pending credentials
        ok, msg = self.auth.consume_pending_credentials()
        if ok:
            return True
        if msg:
            # Credentials were present but wrong — show wizard with error pre-filled
            return self._show_login_dialog(prefill_error=msg)

        # 3. No credentials anywhere — show setup wizard
        return self._show_login_dialog()

    def _show_login_dialog(self, prefill_error: str = "") -> bool:
        """Show the setup wizard. Returns True on successful login."""
        from .setup_wizard import SetupWizard
        dlg = SetupWizard(self.auth, self.config, prefill_error=prefill_error)

        screen = QApplication.primaryScreen().availableGeometry()
        dlg.adjustSize()
        dlg.move(
            screen.center().x() - dlg.width() // 2,
            screen.center().y() - dlg.height() // 2,
        )

        result = dlg.exec_()
        if result == SetupWizard.Accepted:
            print(f"[AUTH] Login successful — {self.auth.name} ({self.auth.username})")
            return True

        return False

    def _do_logout(self):
        """Log out and show the login dialog again."""
        self.auth.logout()
        print("[AUTH] User logged out.")
        if not self._show_login_dialog():
            # User closed the login dialog after logging out → quit
            self.quit_app()
        else:
            # Refresh tray tooltip with new name
            self.tray_icon.setToolTip(f"KShot — {self.auth.name}")
            self._update_tray_user_label()

    def _update_tray_user_label(self):
        """Update the 'Logged in as …' label in the tray menu."""
        if hasattr(self, '_tray_user_action'):
            self._tray_user_action.setText(f"👤  {self.auth.name}  (@{self.auth.username})")

    # ── UI & tray ─────────────────────────────────────────────────────────────

    def init_ui(self):
        self.setWindowTitle("KShot")
        self.setGeometry(100, 100, 400, 300)
        self.hide()

    def init_tray(self):
        import os
        icon_path = os.path.join(os.path.dirname(__file__), "Logo", "logo.png")

        if os.path.exists(icon_path):
            original_pixmap = QPixmap(icon_path)
            icon_size  = 128
            icon_pixmap = original_pixmap.scaled(
                icon_size, icon_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            if icon_pixmap.hasAlphaChannel():
                final_pixmap = QPixmap(icon_size, icon_size)
                final_pixmap.fill(Qt.transparent)
                painter = QPainter(final_pixmap)
                painter.setRenderHint(QPainter.Antialiasing)
                painter.setRenderHint(QPainter.SmoothPixmapTransform)
                painter.drawPixmap(0, 0, icon_pixmap)
                painter.end()
                icon_pixmap = final_pixmap
        else:
            icon_pixmap = QPixmap(128, 128)
            icon_pixmap.fill(Qt.transparent)
            painter = QPainter(icon_pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setBrush(QColor(245, 203, 17))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(8, 8, 112, 112)
            painter.end()

        self.tray_icon = QSystemTrayIcon(QIcon(icon_pixmap), self)

        # Build tray menu
        tray_menu = QMenu()

        # User info label (non-clickable)
        self._tray_user_action = QAction(
            f"👤  {self.auth.name}  (@{self.auth.username})", self
        )
        self._tray_user_action.setEnabled(False)
        tray_menu.addAction(self._tray_user_action)
        tray_menu.addSeparator()

        capture_action = QAction("Area Capture", self)
        capture_action.triggered.connect(self.start_capture)

        fullscreen_action = QAction("Fullscreen Capture", self)
        fullscreen_action.triggered.connect(self.capture_fullscreen)

        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.show_settings)

        logout_action = QAction("Logout", self)
        logout_action.triggered.connect(self._do_logout)

        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.quit_app)

        tray_menu.addAction(capture_action)
        tray_menu.addAction(fullscreen_action)
        tray_menu.addSeparator()
        tray_menu.addAction(settings_action)
        tray_menu.addAction(logout_action)
        tray_menu.addSeparator()
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.setToolTip(f"KShot — {self.auth.name}")
        self.tray_icon.show()

        self.show_startup_notification()

    # ── Notifications ─────────────────────────────────────────────────────────

    def show_startup_notification(self):
        try:
            self.tray_icon.showMessage(
                "KShot",
                f"Halo, {self.auth.name}! Tekan Print Screen untuk screenshot.",
                QSystemTrayIcon.Information,
                3000,
            )
        except Exception as e:
            print(f"[NOTIF] startup: {e}")

    def show_tray_message(self, title, message, duration=3000):
        try:
            self.tray_icon.show()
            self.tray_icon.showMessage(title, message, QSystemTrayIcon.Information, duration)
            print(f"[NOTIF] {title}: {message}")
        except Exception as e:
            print(f"[NOTIF] error: {e}")

    def show_upload_notification(self, url, copied=True):
        try:
            msg = "URL copied to clipboard!" if copied else f"Uploaded: {url}"
            self.tray_icon.showMessage("KShot — Uploaded!", msg, QSystemTrayIcon.Information, 4000)
        except Exception as e:
            print(f"[NOTIF] upload: {e}")

    # ── Settings / capture helpers ────────────────────────────────────────────

    def _hide_settings_for_capture(self):
        dlg = getattr(self, '_settings_dialog', None)
        if dlg and dlg.isVisible():
            dlg.hide()
            return True
        return False

    def _restore_settings_after_capture(self):
        dlg = getattr(self, '_settings_dialog', None)
        if dlg:
            dlg.show()
            dlg.activateWindow()
            dlg.raise_()

    def _make_uploader(self):
        """Create an ImageUploader with auth session injected."""
        from .uploader import ImageUploader
        return ImageUploader(self.config, auth_manager=self.auth)

    def start_capture(self):
        try:
            if self.screenshot_overlay is None or not self.screenshot_overlay.isVisible():
                self._hide_settings_for_capture()
                from PyQt5.QtCore import QTimer
                QTimer.singleShot(150, self._do_start_capture)
        except Exception as e:
            print(f"Error starting capture: {e}")
            import traceback; traceback.print_exc()

    def _do_start_capture(self):
        try:
            self.screenshot_overlay = ScreenshotOverlay(self.config, uploader=self._make_uploader())
            self.screenshot_overlay.main_window = self
            self.screenshot_overlay.destroyed.connect(self._restore_settings_after_capture)
            self.screenshot_overlay.show()
        except Exception as e:
            print(f"Error in _do_start_capture: {e}")
            import traceback; traceback.print_exc()

    def capture_fullscreen(self):
        try:
            if self.screenshot_overlay is None or not self.screenshot_overlay.isVisible():
                self._hide_settings_for_capture()
                from PyQt5.QtCore import QTimer
                QTimer.singleShot(150, self._do_capture_fullscreen)
        except Exception as e:
            print(f"Error capturing fullscreen: {e}")
            import traceback; traceback.print_exc()

    def _do_capture_fullscreen(self):
        try:
            self.screenshot_overlay = ScreenshotOverlay(
                self.config, fullscreen=True, uploader=self._make_uploader()
            )
            self.screenshot_overlay.main_window = self
            self.screenshot_overlay.destroyed.connect(self._restore_settings_after_capture)
            self.screenshot_overlay.show()
        except Exception as e:
            print(f"Error in _do_capture_fullscreen: {e}")
            import traceback; traceback.print_exc()

    def show_settings(self):
        dlg = getattr(self, '_settings_dialog', None)
        if dlg and dlg.isVisible():
            dlg.activateWindow()
            dlg.raise_()
            return

        from .settings_dialog import SettingsDialog
        dialog = SettingsDialog(self.config, None)
        self._settings_dialog = dialog

        screen = QApplication.primaryScreen().availableGeometry()
        dialog.adjustSize()
        dialog.move(
            screen.center().x() - dialog.width() // 2,
            screen.center().y() - dialog.height() // 2,
        )

        def _on_finished(result):
            self._settings_dialog = None
            if result and self.hotkey_manager:
                self.hotkey_manager.update_hotkeys(
                    self.config.get('hotkey_area',       'ctrl+shift+a'),
                    self.config.get('hotkey_fullscreen', 'ctrl+shift+f'),
                    self.config.get('hotkey_settings',   'ctrl+shift+s'),
                )

        dialog.finished.connect(_on_finished)
        dialog.show()

    def quit_app(self):
        self.tray_icon.hide()
        QApplication.quit()
