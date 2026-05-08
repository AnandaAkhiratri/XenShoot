"""
First-run setup wizard for KShot.
Shown when no valid session exists (fresh install or after logout).

Steps:
  1. Welcome
  2. Username + Password login
  3. Done / success
"""

import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QWidget, QStackedWidget, QSizePolicy,
)
from PyQt5.QtCore import Qt, QSize, QThread, pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap


# ── Shared dark stylesheet (matches settings dialog) ──────────────────────────

_STYLE = """
QDialog, QWidget       { background:#000a1d; color:#ffffff; }
QLabel                 { color:#c8c8e8; font-size:15px; background:transparent; }
QLineEdit              { background:#252540; color:#f0f0ff; border:1px solid #5050a0;
                         border-radius:6px; padding:8px 12px; font-size:15px; }
QLineEdit:focus        { border:1px solid #8080ff; background:#2a2a50; }
QPushButton            { background:#2d2d50; color:#e0e0f8; border:1px solid #5050a0;
                         border-radius:6px; padding:8px 20px; font-size:15px;
                         font-weight:bold; min-height:36px; }
QPushButton:hover      { background:#3a3a6a; border-color:#9090d0; }
QPushButton:pressed    { background:#22225a; }
QPushButton#primary    { background:#3a3adc; border-color:#6060ff; color:white; }
QPushButton#primary:hover    { background:#5050ff; }
QPushButton#primary:disabled { background:#1a1a40; color:#555570; border-color:#2a2a50; }
QPushButton#ghost      { background:transparent; border:1px solid #3a3a60; color:#7070a0; }
QPushButton#ghost:hover{ background:#1a1a30; color:#a0a0d0; }
QGroupBox              { color:#c0c0e0; border:1px solid #4a4a7a; border-radius:6px;
                         margin-top:12px; padding-top:12px; font-weight:bold; font-size:15px; }
#titlebar              { background:#1a1a2e; border-bottom:0px solid #2a2a4a; }
"""

_LOGO_PATH = os.path.join(os.path.dirname(__file__), "Logo", "logo.png")


# ── Background login worker ───────────────────────────────────────────────────

class _LoginWorker(QThread):
    done = pyqtSignal(bool, str)

    def __init__(self, auth_manager, username: str, password: str):
        super().__init__()
        self._auth     = auth_manager
        self._username = username
        self._password = password

    def run(self):
        ok, msg = self._auth.login_with_credentials(self._username, self._password)
        self.done.emit(ok, msg)


# ── Individual step pages ─────────────────────────────────────────────────────

def _field_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet("color:#a0a0cc; font-size:14px; font-weight:600;")
    return lbl


def _hint(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setWordWrap(True)
    lbl.setStyleSheet("color:#555580; font-size:14px;")
    return lbl


class _StepWelcome(QWidget):
    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(16)
        lay.addStretch()

        if os.path.exists(_LOGO_PATH):
            logo = QLabel()
            logo.setPixmap(
                QPixmap(_LOGO_PATH).scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
            logo.setAlignment(Qt.AlignCenter)
            lay.addWidget(logo)

        title = QLabel("Selamat datang di KShot")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color:#ffffff; font-size:22px; font-weight:800;")
        lay.addWidget(title)

        sub = QLabel(
            "Login dengan akun yang diberikan admin\nuntuk mulai menggunakan KShot."
        )
        sub.setAlignment(Qt.AlignCenter)
        sub.setWordWrap(True)
        sub.setStyleSheet("color:#6666a0; font-size:14px;")
        lay.addWidget(sub)

        lay.addStretch()


class _StepLogin(QWidget):
    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)

        title = QLabel("Login ke KSHOT")
        title.setStyleSheet("color:#ffffff; font-size:18px; font-weight:700;")
        lay.addWidget(title)

        lay.addWidget(_hint(
            "Masukkan Username dan Password yang diberikan oleh admin."
        ))

        lay.addSpacing(4)

        self.error_lbl = QLabel("")
        self.error_lbl.setWordWrap(True)
        self.error_lbl.setAlignment(Qt.AlignCenter)
        self.error_lbl.setStyleSheet(
            "color:#ff6b6b; font-size:13px; background:rgba(239,68,68,.10);"
            "border:1px solid rgba(239,68,68,.28); border-radius:6px; padding:8px 12px;"
        )
        self.error_lbl.hide()
        lay.addWidget(self.error_lbl)

        lay.addWidget(_field_label("Username"))
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("contoh: user")
        lay.addWidget(self.username_input)

        lay.addWidget(_field_label("Password"))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("••••••••")
        lay.addWidget(self.password_input)

        lay.addStretch()

    def show_error(self, msg: str):
        self.error_lbl.setText(msg)
        self.error_lbl.show()

    def hide_error(self):
        self.error_lbl.hide()
        self.error_lbl.setText("")

    @property
    def username(self) -> str:
        return self.username_input.text().strip()

    @property
    def password(self) -> str:
        return self.password_input.text()


class _StepDone(QWidget):
    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(16)
        lay.addStretch()

        check = QLabel("✓")
        check.setAlignment(Qt.AlignCenter)
        check.setStyleSheet(
            "color:#22c55e; font-size:56px; font-weight:900; background:transparent;"
        )
        lay.addWidget(check)

        title = QLabel("Login berhasil!")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color:#ffffff; font-size:22px; font-weight:800;")
        lay.addWidget(title)

        self.name_lbl = QLabel("")
        self.name_lbl.setAlignment(Qt.AlignCenter)
        self.name_lbl.setStyleSheet("color:#6666a0; font-size:14px;")
        lay.addWidget(self.name_lbl)

        sub = QLabel(
            "KShot siap digunakan.\n"
            "Tekan Print Screen untuk mulai screenshot."
        )
        sub.setAlignment(Qt.AlignCenter)
        sub.setWordWrap(True)
        sub.setStyleSheet("color:#555580; font-size:13px;")
        lay.addWidget(sub)

        lay.addStretch()

    def set_user(self, name: str, username: str):
        self.name_lbl.setText(f"Login sebagai  {name}  (@{username})")


# ── Main wizard dialog ────────────────────────────────────────────────────────

class SetupWizard(QDialog):
    """
    First-run / re-login wizard.
    Accepted  → user is authenticated (auth_manager session is saved).
    Rejected  → user closed/cancelled (app should quit).
    """

    PAGE_WELCOME = 0
    PAGE_LOGIN   = 1
    PAGE_DONE    = 2

    def __init__(self, auth_manager, config, prefill_error: str = "", parent=None):
        super().__init__(parent)
        self._auth          = auth_manager
        self._config        = config
        self._prefill_error = prefill_error
        self._worker        = None
        self._drag_pos      = None
        self._init_ui()

        # If installer credentials failed, jump straight to login step with error shown
        if prefill_error:
            self._stack.setCurrentIndex(self.PAGE_LOGIN)
            self._next_btn.setText("Masuk")
            self._back_btn.show()
            self._page_login.show_error(prefill_error)
            self._update_dots()

    # ── Frameless drag ────────────────────────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self._titlebar.underMouse():
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self._drag_pos is not None:
            self.move(event.globalPos() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    # ── UI ────────────────────────────────────────────────────────────────────

    def _init_ui(self):
        self.setWindowTitle("KShot — Setup")
        self.setModal(True)
        self.setFixedWidth(700)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setStyleSheet(_STYLE)
        if os.path.exists(_LOGO_PATH):
            self.setWindowIcon(QIcon(_LOGO_PATH))

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Title bar ─────────────────────────────────────────────────────
        self._titlebar = QWidget()
        self._titlebar.setObjectName("titlebar")
        self._titlebar.setFixedHeight(40)
        tb = QHBoxLayout(self._titlebar)
        tb.setContentsMargins(12, 0, 8, 0)
        tb.setSpacing(8)

        if os.path.exists(_LOGO_PATH):
            ico = QLabel()
            ico.setPixmap(QPixmap(_LOGO_PATH).scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            tb.addWidget(ico)

        tb.addWidget(QLabel("KShot — Setup"))
        tb.addStretch()

        _TB_DIR = os.path.join(os.path.dirname(__file__), "Logo", "titlebar")
        close_btn = QPushButton("×")
        close_btn.setFixedSize(28, 28)
        close_btn.setCursor(Qt.ArrowCursor)
        close_btn.setStyleSheet(
            "QPushButton { background:transparent; border:none; border-radius:4px;"
            "color:#aaa; font-size:18px; font-weight:400; padding:0; margin:0; }"
            "QPushButton:hover { background:#c0392b; color:#fff; }"
        )
        close_btn.clicked.connect(self.reject)
        tb.addWidget(close_btn)
        root.addWidget(self._titlebar)

        # ── Progress dots ─────────────────────────────────────────────────
        self._dots = []   # kept for compatibility, no longer rendered

        # ── Stacked pages ─────────────────────────────────────────────────
        body = QWidget()
        body.setStyleSheet("background:#1e1e2e;")
        body_lay = QVBoxLayout(body)
        body_lay.setContentsMargins(32, 24, 32, 20)
        body_lay.setSpacing(0)

        self._stack = QStackedWidget()
        self._page_welcome = _StepWelcome()
        self._page_login   = _StepLogin()
        self._page_done    = _StepDone()

        self._stack.addWidget(self._page_welcome)
        self._stack.addWidget(self._page_login)
        self._stack.addWidget(self._page_done)
        body_lay.addWidget(self._stack)

        # ── Navigation buttons ─────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(0, 16, 0, 0)

        self._back_btn = QPushButton("Kembali")
        self._back_btn.setObjectName("ghost")
        self._back_btn.clicked.connect(self._go_back)
        self._back_btn.hide()

        self._next_btn = QPushButton("Mulai Setup")
        self._next_btn.setObjectName("primary")
        self._next_btn.clicked.connect(self._go_next)

        btn_row.addWidget(self._back_btn)
        btn_row.addStretch()
        btn_row.addWidget(self._next_btn)
        body_lay.addLayout(btn_row)

        root.addWidget(body)
        self._update_dots()

    # ── Navigation ────────────────────────────────────────────────────────────

    def _current_page(self) -> int:
        return self._stack.currentIndex()

    def _update_dots(self):
        page = self._current_page()
        # Dots represent pages 1, 2 (login, done)
        for i, dot in enumerate(self._dots):
            target_page = i + 1
            if target_page < page:
                dot.setStyleSheet("color:#22c55e; font-size:10px;")   # completed
            elif target_page == page:
                dot.setStyleSheet("color:#6060ff; font-size:12px;")   # active
            else:
                dot.setStyleSheet("color:#2a2a50; font-size:10px;")   # future

    def _go_next(self):
        page = self._current_page()

        if page == self.PAGE_WELCOME:
            self._stack.setCurrentIndex(self.PAGE_LOGIN)
            self._next_btn.setText("Masuk")
            self._back_btn.show()
            self._page_login.username_input.setFocus()

        elif page == self.PAGE_LOGIN:
            self._do_login()

        elif page == self.PAGE_DONE:
            self.accept()

        self._update_dots()

    def _go_back(self):
        page = self._current_page()
        if page == self.PAGE_LOGIN:
            self._stack.setCurrentIndex(self.PAGE_WELCOME)
            self._next_btn.setText("Mulai Setup")
            self._back_btn.hide()
        self._update_dots()

    # ── Login ─────────────────────────────────────────────────────────────────

    def _set_login_loading(self, loading: bool):
        self._next_btn.setEnabled(not loading)
        self._back_btn.setEnabled(not loading)
        self._page_login.username_input.setEnabled(not loading)
        self._page_login.password_input.setEnabled(not loading)
        self._next_btn.setText("Memverifikasi…" if loading else "Masuk")

    def _do_login(self):
        username = self._page_login.username
        password = self._page_login.password

        if not username:
            self._page_login.show_error("Username tidak boleh kosong.")
            self._page_login.username_input.setFocus()
            return
        if not password:
            self._page_login.show_error("Password tidak boleh kosong.")
            self._page_login.password_input.setFocus()
            return

        self._page_login.hide_error()
        self._set_login_loading(True)

        self._worker = _LoginWorker(self._auth, username, password)
        self._worker.done.connect(self._on_login_done)
        self._worker.start()

    def _on_login_done(self, success: bool, message: str):
        self._set_login_loading(False)
        if success:
            self._page_done.set_user(self._auth.name, self._auth.username)
            self._stack.setCurrentIndex(self.PAGE_DONE)
            self._next_btn.setText("Selesai")
            self._back_btn.hide()
            self._update_dots()
        else:
            self._page_login.show_error(message)
            self._page_login.password_input.clear()
            self._page_login.password_input.setFocus()

    # Enter key support
    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if self._next_btn.isEnabled():
                self._go_next()
        elif event.key() == Qt.Key_Escape:
            pass   # block accidental close on Escape during wizard
        else:
            super().keyPressEvent(event)
