"""
Login dialog for KShot desktop application.
"""

import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QWidget, QSizePolicy,
)
from PyQt5.QtCore import Qt, QSize, QThread, pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap, QFont


_STYLE = """
QDialog, QWidget      { background:#000a1d; color:#ffffff; }
QLabel                { color:#c8c8e8; font-size:15px; background:transparent; }
QLineEdit             { background:#252540; color:#f0f0ff; border:1px solid #5050a0;
                        border-radius:6px; padding:8px 12px; font-size:15px; }
QLineEdit:focus       { border:1px solid #8080ff; }
QPushButton           { background:#2d2d50; color:#e0e0f8; border:1px solid #5050a0;
                        border-radius:6px; padding:8px 20px; font-size:15px;
                        font-weight:bold; min-height:36px; }
QPushButton:hover     { background:#3a3a6a; border-color:#9090d0; }
QPushButton:pressed   { background:#22225a; }
QPushButton#primary   { background:#3a3adc; border-color:#6060ff; color:white; }
QPushButton#primary:hover     { background:#5050ff; }
QPushButton#primary:disabled  { background:#1a1a40; color:#666680; border-color:#333360; }
QLabel#error          { color:#ff6b6b; font-size:14px;
                        background:rgba(239,68,68,0.10);
                        border:1px solid rgba(239,68,68,0.28);
                        border-radius:6px; padding:8px 12px; }
QLabel#hint           { color:#6666a0; font-size:14px; }
#titlebar             { background:#1a1a2e; border-bottom:1px solid #333; }
"""


class _LoginWorker(QThread):
    """Runs the blocking API call in a background thread."""
    done = pyqtSignal(bool, str)

    def __init__(self, auth_manager, username: str, password: str):
        super().__init__()
        self._auth = auth_manager
        self._username = username
        self._password = password

    def run(self):
        ok, msg = self._auth.login_with_credentials(self._username, self._password)
        self.done.emit(ok, msg)


class LoginDialog(QDialog):
    """
    Modal login dialog.
    On successful login it stores the session via AuthManager and accepts.
    On cancel / close it rejects (caller should quit the app).
    """

    def __init__(self, auth_manager, parent=None):
        super().__init__(parent)
        self._auth = auth_manager
        self._worker = None
        self._drag_pos = None
        self._init_ui()

    # ── Frameless drag support ────────────────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self._titlebar.underMouse():
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self._drag_pos is not None:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    # ── UI ────────────────────────────────────────────────────────────────────

    def _init_ui(self):
        self.setWindowTitle("KShot — Login")
        self.setModal(True)
        self.setFixedWidth(700)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setStyleSheet(_STYLE)

        _logo = os.path.join(os.path.dirname(__file__), "Logo", "logo.png")
        if os.path.exists(_logo):
            self.setWindowIcon(QIcon(_logo))

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Title bar ─────────────────────────────────────────────────────
        self._titlebar = QWidget()
        self._titlebar.setObjectName("titlebar")
        self._titlebar.setFixedHeight(40)
        tb_lay = QHBoxLayout(self._titlebar)
        tb_lay.setContentsMargins(12, 0, 8, 0)
        tb_lay.setSpacing(8)

        if os.path.exists(_logo):
            ico = QLabel()
            ico.setPixmap(QPixmap(_logo).scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            ico.setStyleSheet("background:transparent;")
            tb_lay.addWidget(ico)

        title_lbl = QLabel("KShot")
        title_lbl.setStyleSheet(
            "background:transparent; color:#e0e0e0; font-size:13px; font-weight:600;"
        )
        tb_lay.addWidget(title_lbl)
        tb_lay.addStretch()

        _TB_DIR = os.path.join(os.path.dirname(__file__), "Logo", "titlebar")

        def _tb_btn(icon_name, slot):
            btn = QPushButton("×")
            btn.setFixedSize(28, 28)
            btn.setCursor(Qt.ArrowCursor)
            btn.setStyleSheet(
                "QPushButton { background:transparent; border:none; border-radius:4px;"
                "color:#aaa; font-size:18px; font-weight:400; padding:0; margin:0; }"
                "QPushButton:hover { background:#c0392b; color:#fff; }"
            )
            btn.clicked.connect(slot)
            return btn

        tb_lay.addWidget(_tb_btn("close", self.reject))
        root.addWidget(self._titlebar)

        # ── Body ──────────────────────────────────────────────────────────
        body = QWidget()
        body.setStyleSheet("background:#1e1e2e;")
        body_lay = QVBoxLayout(body)
        body_lay.setContentsMargins(28, 24, 28, 28)
        body_lay.setSpacing(14)

        # Logo + header
        logo_row = QHBoxLayout()
        logo_row.setAlignment(Qt.AlignCenter)
        if os.path.exists(_logo):
            logo_lbl = QLabel()
            logo_lbl.setPixmap(
                QPixmap(_logo).scaled(52, 52, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
            logo_lbl.setAlignment(Qt.AlignCenter)
            logo_lbl.setStyleSheet("background:transparent;")
            logo_row.addWidget(logo_lbl)
        body_lay.addLayout(logo_row)

        headline = QLabel("Login ke KShot")
        headline.setAlignment(Qt.AlignCenter)
        headline.setStyleSheet(
            "color:#ffffff; font-size:20px; font-weight:700; background:transparent;"
        )
        body_lay.addWidget(headline)

        sub = QLabel("Masukkan username dan password yang diberikan oleh admin.")
        sub.setAlignment(Qt.AlignCenter)
        sub.setWordWrap(True)
        sub.setObjectName("hint")
        sub.setStyleSheet("color:#6666a0; font-size:12px; background:transparent;")
        body_lay.addWidget(sub)

        body_lay.addSpacing(4)

        # Error label (hidden initially)
        self._error_lbl = QLabel("")
        self._error_lbl.setObjectName("error")
        self._error_lbl.setWordWrap(True)
        self._error_lbl.setAlignment(Qt.AlignCenter)
        self._error_lbl.hide()
        body_lay.addWidget(self._error_lbl)

        # Username field
        user_lbl = QLabel("Username")
        user_lbl.setStyleSheet("font-weight:600; color:#a0a0cc; font-size:13px; background:transparent;")
        body_lay.addWidget(user_lbl)
        self._username_input = QLineEdit()
        self._username_input.setPlaceholderText("contoh: john_doe")
        self._username_input.returnPressed.connect(self._on_login)
        body_lay.addWidget(self._username_input)

        # Password field
        pass_lbl = QLabel("Password")
        pass_lbl.setStyleSheet("font-weight:600; color:#a0a0cc; font-size:13px; background:transparent;")
        body_lay.addWidget(pass_lbl)
        self._password_input = QLineEdit()
        self._password_input.setEchoMode(QLineEdit.Password)
        self._password_input.setPlaceholderText("••••••••")
        self._password_input.returnPressed.connect(self._on_login)
        body_lay.addWidget(self._password_input)

        body_lay.addSpacing(4)

        # Buttons
        self._login_btn = QPushButton("Login")
        self._login_btn.setObjectName("primary")
        self._login_btn.setFixedHeight(42)
        self._login_btn.clicked.connect(self._on_login)
        body_lay.addWidget(self._login_btn)

        root.addWidget(body)

    # ── Login logic ───────────────────────────────────────────────────────────

    def _set_loading(self, loading: bool):
        self._login_btn.setEnabled(not loading)
        self._username_input.setEnabled(not loading)
        self._password_input.setEnabled(not loading)
        self._login_btn.setText("Memproses…" if loading else "Login")

    def _show_error(self, msg: str):
        self._error_lbl.setText(msg)
        self._error_lbl.show()
        self.adjustSize()

    def _hide_error(self):
        self._error_lbl.hide()
        self._error_lbl.setText("")

    def _on_login(self):
        username = self._username_input.text().strip()
        password = self._password_input.text()

        if not username:
            self._show_error("Username tidak boleh kosong.")
            self._username_input.setFocus()
            return
        if not password:
            self._show_error("Password tidak boleh kosong.")
            self._password_input.setFocus()
            return

        self._hide_error()
        self._set_loading(True)

        self._worker = _LoginWorker(self._auth, username, password)
        self._worker.done.connect(self._on_login_done)
        self._worker.start()

    def _on_login_done(self, success: bool, message: str):
        self._set_loading(False)
        if success:
            self.accept()
        else:
            self._show_error(message)
            self._password_input.clear()
            self._password_input.setFocus()
