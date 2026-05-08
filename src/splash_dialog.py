"""
Splash / credential-check dialog for KShot.
Shown immediately on launch while auth is verified in background.
"""

import os
import math
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QWidget, QApplication
from PyQt5.QtCore    import Qt, QTimer, QThread, pyqtSignal, QRectF, QPointF
from PyQt5.QtGui     import QIcon, QPixmap, QPainter, QColor, QPen, QFont

_LOGO_PATH = os.path.join(os.path.dirname(__file__), "Logo", "logo.png")

_DARK = """
QDialog, QWidget { background:#000a1d; color:#ffffff; }
QLabel           { color:#c8c8e8; background:transparent; }
#titlebar        { background:#1a1a2e; border-bottom:1px solid #2a2a4a; }
"""

DIALOG_W = 700
DIALOG_H = 300


# ── Spinning arc widget ───────────────────────────────────────────────────────

class _Spinner(QWidget):
    def __init__(self, size=48, parent=None):
        super().__init__(parent)
        self._size  = size
        self._angle = 0
        self.setFixedSize(size, size)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(30)

    def _tick(self):
        self._angle = (self._angle + 8) % 360
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        s = self._size
        pen = QPen(QColor("#3a3adc"), 4, Qt.SolidLine, Qt.RoundCap)
        p.setPen(pen)
        rect = QRectF(6, 6, s - 12, s - 12)
        p.drawArc(rect, self._angle * 16, 270 * 16)

        # Faint track
        pen2 = QPen(QColor("#1a1a3a"), 4)
        p.setPen(pen2)
        p.drawEllipse(rect)
        p.end()

    def stop(self):
        self._timer.stop()


# ── Background worker ─────────────────────────────────────────────────────────

class _AuthCheckWorker(QThread):
    """
    Runs credential check in background:
      1. consume_pending_credentials (from installer)
      2. verify_session (existing session)
    Emits done(ok: bool, error_msg: str)
    """
    done = pyqtSignal(bool, str)

    def __init__(self, auth_manager):
        super().__init__()
        self._auth = auth_manager

    def run(self):
        # 1. Pending credentials from installer take top priority.
        #    If the installer just wrote credentials, use them regardless of any
        #    existing dev/test session — this ensures fresh install always re-logins.
        if self._auth._PENDING_FILE.exists():
            ok, msg = self._auth.consume_pending_credentials()
            if ok:
                self.done.emit(True, "")
                return
            # Pending login failed → fall through to wizard (don't trust old session)
            self.done.emit(False, msg)
            return

        # 2. No pending file → check existing session (normal app restart)
        if self._auth.is_logged_in():
            valid = self._auth.verify_session()
            if valid:
                self.done.emit(True, "")
                return
            # Session invalid → need re-login

        # 3. No valid session → show wizard
        self.done.emit(False, "")


# ── Splash dialog ─────────────────────────────────────────────────────────────

class SplashDialog(QDialog):
    """
    Shows "Memeriksa Kredensial…" while checking auth.
    Emits auth_result(ok, error_msg) when done, then closes itself.
    """
    auth_result = pyqtSignal(bool, str)

    def __init__(self, auth_manager, parent=None):
        super().__init__(parent)
        self._auth   = auth_manager
        self._worker = None
        self._drag_pos = None
        self._init_ui()
        self._center()

    # ── Drag support ─────────────────────────────────────────────────────────

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton and self._titlebar.underMouse():
            self._drag_pos = e.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if e.buttons() == Qt.LeftButton and self._drag_pos is not None:
            self.move(e.globalPos() - self._drag_pos)

    def mouseReleaseEvent(self, e):
        self._drag_pos = None

    # ── UI ────────────────────────────────────────────────────────────────────

    def _init_ui(self):
        self.setWindowTitle("KShot")
        self.setModal(True)
        self.setFixedSize(DIALOG_W, DIALOG_H)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setStyleSheet(_DARK)
        if os.path.exists(_LOGO_PATH):
            self.setWindowIcon(QIcon(_LOGO_PATH))

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Title bar ────────────────────────────────────────────────────
        self._titlebar = QWidget()
        self._titlebar.setObjectName("titlebar")
        self._titlebar.setFixedHeight(42)
        tb = QHBoxLayout(self._titlebar)
        tb.setContentsMargins(14, 0, 14, 0)
        tb.setSpacing(8)

        if os.path.exists(_LOGO_PATH):
            ico = QLabel()
            ico.setPixmap(QPixmap(_LOGO_PATH).scaled(22, 22, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            ico.setStyleSheet("background:transparent;")
            tb.addWidget(ico)

        title_lbl = QLabel("KShot")
        title_lbl.setStyleSheet(
            "background:transparent; color:#e0e0e0; font-size:13px; font-weight:600;"
        )
        tb.addWidget(title_lbl)
        tb.addStretch()
        root.addWidget(self._titlebar)

        # ── Body ─────────────────────────────────────────────────────────
        body = QWidget()
        body.setStyleSheet("background:#0d1a33;")
        body_lay = QVBoxLayout(body)
        body_lay.setContentsMargins(40, 0, 40, 0)
        body_lay.setSpacing(20)
        body_lay.addStretch()

        # Logo
        if os.path.exists(_LOGO_PATH):
            logo_row = QHBoxLayout()
            logo_row.setAlignment(Qt.AlignCenter)
            logo_lbl = QLabel()
            logo_lbl.setPixmap(
                QPixmap(_LOGO_PATH).scaled(56, 56, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
            logo_lbl.setAlignment(Qt.AlignCenter)
            logo_row.addWidget(logo_lbl)
            body_lay.addLayout(logo_row)

        # Spinner (atas) + teks (bawah) — semua center
        self._spinner = _Spinner(size=44)
        body_lay.addWidget(self._spinner, 0, Qt.AlignCenter)

        body_lay.addSpacing(12)

        self._status_lbl = QLabel("Memeriksa Kredensial…")
        self._status_lbl.setAlignment(Qt.AlignCenter)
        self._status_lbl.setStyleSheet(
            "color:#c8c8e8; font-size:16px; font-weight:600;"
        )
        body_lay.addWidget(self._status_lbl)

        self._sub_lbl = QLabel("Mohon tunggu sebentar")
        self._sub_lbl.setAlignment(Qt.AlignCenter)
        self._sub_lbl.setStyleSheet("color:#444466; font-size:13px;")
        body_lay.addWidget(self._sub_lbl)

        body_lay.addStretch()
        root.addWidget(body)

    def _center(self):
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(
            screen.center().x() - self.width()  // 2,
            screen.center().y() - self.height() // 2,
        )

    # ── Auth check ────────────────────────────────────────────────────────────

    def start_check(self):
        """Start the background credential check."""
        self._worker = _AuthCheckWorker(self._auth)
        self._worker.done.connect(self._on_done)
        self._worker.start()

    def _on_done(self, ok: bool, error_msg: str):
        self._spinner.stop()
        if ok:
            self._status_lbl.setText("✓  Kredensial valid")
            self._status_lbl.setStyleSheet("color:#22c55e; font-size:16px; font-weight:600;")
            self._sub_lbl.setText(f"Halo, {self._auth.name or self._auth.username}!")
            QTimer.singleShot(800, lambda: (self.auth_result.emit(True, ""), self.accept()))
        else:
            self.auth_result.emit(False, error_msg)
            self.accept()
