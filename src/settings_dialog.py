"""
Settings dialog for kshot — Flameshot-style UI
Tabs: General | Filename Editor | Shortcuts
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QCheckBox, QGroupBox, QFormLayout, QFileDialog, QTabWidget, QWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QScrollArea, QFrame, QComboBox, QSpinBox, QGridLayout, QSizePolicy,
    QMessageBox, QSlider, QColorDialog
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QPoint
from PyQt5.QtGui import QKeySequence, QFont, QColor, QIcon, QPixmap
from datetime import datetime
import os, json


# ─────────────────────────────────────────────────────────────────────────────
# Shortcut-capture push button
# ─────────────────────────────────────────────────────────────────────────────

class ShortcutCapture(QPushButton):
    shortcut_changed = pyqtSignal(str)
    conflict_detected = pyqtSignal(str, str)   # (attempted, conflicting_label)

    _IDLE = ("background:#2d2d2d;color:#f0f0f0;border:1px solid #555;"
             "border-radius:4px;padding:4px 12px;font-family:monospace;font-size:14px;")
    _REC  = ("background:#1a3a5c;color:#7ec8e3;border:2px solid #7ec8e3;"
             "border-radius:4px;padding:4px 12px;font-family:monospace;font-size:14px;")
    _ERR  = ("background:#3a1a1a;color:#ff6b6b;border:2px solid #ff4444;"
             "border-radius:4px;padding:4px 12px;font-family:monospace;font-size:14px;")

    def __init__(self, shortcut="", parent=None):
        super().__init__(parent)
        self._shortcut  = shortcut
        self._recording = False
        self._conflict_checker = None   # callable(new_shortcut, self) -> conflicting label or None
        self._refresh()
        self.setStyleSheet(self._IDLE)
        self.setFocusPolicy(Qt.StrongFocus)
        self.clicked.connect(self._start)

    def set_conflict_checker(self, fn):
        """fn(new_shortcut_str, this_widget) -> label_str of conflicting widget, or None"""
        self._conflict_checker = fn

    @staticmethod
    def _format_shortcut(s):
        """Format 'ctrl+shift+s' → 'Ctrl + Shift + S'"""
        if not s:
            return "—"
        return " + ".join(part.capitalize() for part in s.split("+"))

    def _refresh(self):
        self.setText(self._format_shortcut(self._shortcut))

    def _start(self):
        self._recording = True
        self.setText("Tekan kombinasi…")
        self.setStyleSheet(self._REC)
        self.grabKeyboard()

    def _stop(self):
        self._recording = False
        self.releaseKeyboard()
        self.setStyleSheet(self._IDLE)
        self._refresh()

    def _flash_error(self, msg):
        """Briefly show error style then revert."""
        from PyQt5.QtCore import QTimer
        self.setText(msg)
        self.setStyleSheet(self._ERR)
        QTimer.singleShot(1800, self._stop)

    def keyPressEvent(self, event):
        if not self._recording:
            return super().keyPressEvent(event)
        key = event.key()
        if key == Qt.Key_Escape:
            self._stop(); return
        if key in (Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt, Qt.Key_Meta, Qt.Key_unknown):
            return
        parts = []
        m = event.modifiers()
        if m & Qt.ControlModifier: parts.append("ctrl")
        if m & Qt.ShiftModifier:   parts.append("shift")
        if m & Qt.AltModifier:     parts.append("alt")
        name = QKeySequence(key).toString().lower()
        if name: parts.append(name)
        s = "+".join(parts)
        if not s:
            self._stop(); return

        # Conflict check
        if self._conflict_checker:
            conflict_label = self._conflict_checker(s, self)
            if conflict_label:
                self.releaseKeyboard()
                self._recording = False
                self._flash_error(f"✗ sudah dipakai: {conflict_label}")
                self.conflict_detected.emit(s, conflict_label)
                return

        self._shortcut = s
        self.shortcut_changed.emit(s)
        self._stop()

    def focusOutEvent(self, event):
        if self._recording: self._stop()
        super().focusOutEvent(event)

    def value(self):  return self._shortcut
    def setValue(self, s): self._shortcut = s; self._refresh()


# ─────────────────────────────────────────────────────────────────────────────
# Main dialog
# ─────────────────────────────────────────────────────────────────────────────

_DARK = """
QDialog, QWidget       { background:#000a1d; color:#ffffff; }
QTabWidget::pane       { border:1px solid #3a3a5c; background:#0b1d3a; }
QTabBar::tab           { background:#0b1d3a; color:#9999bb;
                         padding:0px; min-width:64px; max-width:64px; min-height:38px;
                         border:1px solid #3a3a5c; border-bottom:none;
                         border-radius:4px 4px 0 0; font-size:15px; }
QTabBar::tab:selected  { background:#1a1a2e; color:#ffffff; font-weight:bold; }
QTabBar::tab:hover     { color:#ddddff; }
QGroupBox              { color:#c0c0e0; border:1px solid #4a4a7a; border-radius:6px;
                         margin-top:12px; padding-top:12px; font-weight:bold; font-size:15px; }
QGroupBox::title       { subcontrol-origin:margin; left:12px; padding:0 6px;
                         color:#bcbec2; }
QCheckBox              { color:#e0e0f8; spacing:8px; font-size:15px; }
QCheckBox::indicator   { width:17px; height:17px; border:2px solid #6060a0;
                         border-radius:3px; background:#252540; }
QCheckBox::indicator:checked   { background:#0e4689; border-color:#8080ff;
                                  image: none; }
QCheckBox::indicator:unchecked { background:#252540; }
QLineEdit              { background:#252540; color:#f0f0ff; border:1px solid #5050a0;
                         border-radius:4px; padding:5px 8px; font-size:15px; }
QLineEdit:focus        { border:1px solid #8080ff; }
QLineEdit[readOnly="true"] { background:#1e1e35; color:#8888aa; }
QComboBox              { background:#252540; color:#f0f0ff; border:1px solid #5050a0;
                         border-radius:4px; padding:5px 8px; font-size:15px; }
QComboBox QAbstractItemView { background:#252540; color:#f0f0ff; border:1px solid #5050a0; }
QSpinBox               { background:#252540; color:#f0f0ff; border:1px solid #5050a0;
                         border-radius:4px; padding:4px 6px; font-size:15px; }
QPushButton            { background:#2d2d50; color:#e0e0f8; border:1px solid #5050a0;
                         border-radius:4px; padding:6px 16px; font-size:15px; }
QPushButton:hover      { background:#3a3a6a; border-color:#9090d0; }
#titlebar QPushButton  { background:transparent; color:#cccccc; border:none;
                         border-radius:4px; padding:0px; font-size:15px; }
#titlebar QPushButton:hover        { background:#3a3a4a; color:#ffffff; }
#titlebar QPushButton#close_btn:hover { background:#c0392b; color:#ffffff; }
QPushButton#primary    { background:#3a3adc; border-color:#6060ff; color:white;
                         font-weight:bold; }
QPushButton#primary:hover { background:#5050ff; }
QPushButton#token_btn  { background:#2a2a48; color:#c0c0f0; border:1px solid #4a4a80;
                         border-radius:4px; padding:7px 4px; font-size:15px; }
QPushButton#token_btn:hover { background:#3a3a60; border-color:#8080c0; }
QLabel                 { color:#c8c8e8; font-size:15px; }
QHeaderView::section   { background:#252540; color:#a0a0cc; border:none;
                         border-bottom:1px solid #3a3a5c; padding:7px; font-size:15px; }
QScrollArea            { border:none; background:transparent; }
QScrollBar:vertical    { background:#1a1a2e; width:10px; }
QScrollBar::handle:vertical { background:#4040a0; border-radius:5px; min-height:20px; }
"""


class SettingsDialog(QDialog):
    DEFAULT_TEMPLATE = "kshot_%Y-%m-%d_%H-%M-%S"

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self._orig_template = config.get('filename_template', self.DEFAULT_TEMPLATE)
        self._drag_pos = None
        self._init_ui()
        self._load_settings()

    # ── Drag support for frameless window ────────────────────────────────────

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

    def _toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    # ── UI skeleton ──────────────────────────────────────────────────────────

    def _init_ui(self):
        self.setWindowTitle("KSHOT — Configuration")
        self.setModal(True)
        self.setMinimumSize(580, 520)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        _logo = os.path.join(os.path.dirname(__file__), 'Logo', 'logo.png')
        if os.path.exists(_logo):
            self.setWindowIcon(QIcon(_logo))
        self.setStyleSheet(_DARK)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Custom title bar ─────────────────────────────────────────────────
        self._titlebar = QWidget()
        self._titlebar.setObjectName("titlebar")
        self._titlebar.setFixedHeight(40)
        self._titlebar.setStyleSheet(
            "#titlebar { background:#1a1a2e; border-bottom: 1px solid #333; }"
        )
        tb_lay = QHBoxLayout(self._titlebar)
        tb_lay.setContentsMargins(10, 0, 8, 0)
        tb_lay.setSpacing(8)

        _logo_path = os.path.join(os.path.dirname(__file__), 'Logo', 'logo.png')
        if os.path.exists(_logo_path):
            ico_lbl = QLabel()
            ico_lbl.setPixmap(QPixmap(_logo_path).scaled(22, 22, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            ico_lbl.setStyleSheet("background: transparent;")
            tb_lay.addWidget(ico_lbl)

        title_lbl = QLabel("Settings")
        title_lbl.setStyleSheet(
            "background: transparent; color: #e0e0e0; font-size: 13px; font-weight: 600;"
        )
        tb_lay.addWidget(title_lbl)
        tb_lay.addStretch()

        _TB_ICON_DIR = os.path.join(os.path.dirname(__file__), 'Logo', 'titlebar')

        _ICONS = {"minimize": "─", "maximize": "□", "close": "×"}
        _SS_BASE = (
            "QPushButton { background:transparent; border:none; border-radius:4px;"
            "color:#aaa; font-size:16px; font-weight:400; padding:0; margin:0; }"
            "QPushButton:hover { background:#3a3a4a; color:#fff; }"
        )

        def _tb_btn(icon_name, obj_name, slot):
            btn = QPushButton(_ICONS.get(icon_name, ""))
            btn.setObjectName(obj_name)
            btn.setFixedSize(28, 28)
            btn.setCursor(Qt.ArrowCursor)
            btn.setStyleSheet(_SS_BASE)
            btn.clicked.connect(slot)
            return btn

        min_btn = _tb_btn("minimize", "min_btn",   self.showMinimized)
        max_btn = _tb_btn("maximize", "max_btn",   self._toggle_maximize)
        cls_btn = _tb_btn("close",    "close_btn", self.reject)
        cls_btn.setStyleSheet(
            _SS_BASE +
            "QPushButton#close_btn:hover { background:#c0392b; color:#fff; }"
        )
        tb_lay.addWidget(min_btn)
        tb_lay.addWidget(max_btn)
        tb_lay.addWidget(cls_btn)

        root.addWidget(self._titlebar)

        # ── Content area ─────────────────────────────────────────────────────
        content = QWidget()
        content.setStyleSheet("background:#1e1e2e;")
        content_lay = QVBoxLayout(content)
        content_lay.setContentsMargins(10, 10, 10, 10)
        content_lay.setSpacing(8)
        root.addWidget(content)

        self.tabs = QTabWidget()
        self.tabs.setIconSize(QSize(20, 20))
        self.tabs.tabBar().setExpanding(True)

        # Tab icon helper — loads SVG from src/Logo/tabs/<name>.svg if exists,
        # falls back to emoji text. Drop any SVG into that folder and it will be used.
        import os as _os
        _ICON_DIR = _os.path.join(_os.path.dirname(__file__), 'Logo', 'tabs')

        def _tab_icon(name, fallback_text):
            path = _os.path.join(_ICON_DIR, f'{name}.svg')
            if _os.path.exists(path):
                icon = QIcon(path)
                return icon, ""     # icon only, no text
            return QIcon(), fallback_text  # no icon, use emoji text

        def _add_tab(widget, name, fallback):
            path = _os.path.join(_ICON_DIR, f'{name}.svg')
            if _os.path.exists(path):
                from PyQt5.QtWidgets import QTabBar
                idx = self.tabs.count()
                self.tabs.addTab(widget, "")
                # Use setTabButton with a centered QLabel for true icon centering
                lbl = QLabel()
                lbl.setPixmap(QIcon(path).pixmap(20, 20))
                lbl.setAlignment(Qt.AlignCenter)
                lbl.setFixedSize(64, 38)
                lbl.setStyleSheet("background: transparent; margin: 0px;")
                self.tabs.tabBar().setTabButton(idx, QTabBar.LeftSide, lbl)
            else:
                self.tabs.addTab(widget, fallback)

        _add_tab(self._tab_general(),   'general',   '⚙')
        _add_tab(self._tab_interface(), 'interface', '🎨')
        _add_tab(self._tab_filename(),  'filename',  '✎')
        _add_tab(self._tab_shortcuts(), 'shortcuts', '⌨')
        _add_tab(self._tab_history(),   'history',   '🕒')
        content_lay.addWidget(self.tabs)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel = QPushButton("Cancel"); cancel.clicked.connect(self.reject)
        save   = QPushButton("Save");   save.setObjectName("primary")
        save.clicked.connect(self._save)
        btn_row.addWidget(cancel)
        btn_row.addWidget(save)
        content_lay.addLayout(btn_row)

    # ── General tab ──────────────────────────────────────────────────────────

    # ── History tab ──────────────────────────────────────────────────────

    def _tab_history(self):
        from PyQt5.QtCore import QSize
        from .history_manager import HistoryManager
        self._history_mgr = HistoryManager()

        outer = QWidget()
        lay = QVBoxLayout(outer)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(8)

        # Header row
        hdr = QHBoxLayout()
        title = QLabel("Screenshot History (last 30)")
        title.setStyleSheet("font-size:15px; font-weight:bold; color:#e0e0f8;")
        hdr.addWidget(title)
        hdr.addStretch()
        refresh_btn = QPushButton("⟳  Refresh")
        refresh_btn.setFixedHeight(32)
        refresh_btn.setMinimumWidth(110)
        refresh_btn.clicked.connect(self._history_refresh)
        hdr.addWidget(refresh_btn)

        clear_btn = QPushButton("🗑  Clear All")
        clear_btn.setFixedHeight(32)
        clear_btn.setMinimumWidth(120)
        clear_btn.clicked.connect(self._history_clear_all)
        hdr.addWidget(clear_btn)
        lay.addLayout(hdr)

        # Scroll area containing the grid
        self._history_scroll = QScrollArea()
        self._history_scroll.setWidgetResizable(True)
        self._history_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._history_scroll.setStyleSheet("QScrollArea { border: none; }")
        lay.addWidget(self._history_scroll)

        self._history_refresh()
        return outer

    def _history_refresh(self):
        from .history_manager import HistoryManager
        entries = self._history_mgr.load()

        container = QWidget()
        grid = QGridLayout(container)
        grid.setSpacing(10)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        COLS = 2
        for idx, entry in enumerate(entries):
            row, col = divmod(idx, COLS)
            card = self._history_card(entry)
            grid.addWidget(card, row, col, Qt.AlignTop)

        if not entries:
            # Replace grid container with a centered-label widget
            empty_container = QWidget()
            empty_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            vl = QVBoxLayout(empty_container)
            vl.addStretch()
            empty = QLabel("No history yet.\nScreenshots will appear here after capture.")
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet("color:#666; font-size:15px;")
            vl.addWidget(empty)
            vl.addStretch()
            self._history_scroll.setWidget(empty_container)
            return

        self._history_scroll.setWidget(container)

    def _history_card(self, entry):
        """
        Compact card: thumbnail fills top, thin bottom strip with timestamp + 3 icon buttons.
        Buttons are always visible — no hover magic needed.
        """
        from .history_manager import HistoryManager

        THUMB_H  = 140
        STRIP_H  = 30

        url = entry.get("url", "")
        ts  = entry.get("timestamp", "")[:16].replace("T", " ")

        # ── Outer card ────────────────────────────────────────────────────
        card = QFrame()
        card.setFixedHeight(THUMB_H + STRIP_H)
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        card.setStyleSheet(
            "QFrame { background:#12192e; border:1px solid #2a2a50; border-radius:8px; }"
        )
        vlay = QVBoxLayout(card)
        vlay.setContentsMargins(0, 0, 0, 0)
        vlay.setSpacing(0)

        # ── Thumbnail ─────────────────────────────────────────────────────
        thumb_lbl = QLabel()
        thumb_lbl.setFixedHeight(THUMB_H)
        thumb_lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        thumb_lbl.setAlignment(Qt.AlignCenter)
        thumb_lbl.setStyleSheet(
            "border:none; background:#0a0a1a;"
            "border-top-left-radius:8px; border-top-right-radius:8px;"
        )
        if entry.get("thumbnail"):
            px = HistoryManager.b64_to_pixmap(entry["thumbnail"])
            if px and not px.isNull():
                thumb_lbl.setPixmap(
                    px.scaled(400, THUMB_H, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )
            else:
                thumb_lbl.setText("No preview")
        else:
            thumb_lbl.setText("No preview")
        vlay.addWidget(thumb_lbl)

        # ── Bottom strip ─────────────────────────────────────────────────
        strip = QWidget()
        strip.setFixedHeight(STRIP_H)
        strip.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        strip.setStyleSheet(
            "QWidget { background:#1a2240; border:none;"
            "border-bottom-left-radius:8px; border-bottom-right-radius:8px; }"
        )
        slay = QHBoxLayout(strip)
        slay.setContentsMargins(8, 0, 6, 0)
        slay.setSpacing(4)

        ts_lbl = QLabel(ts)
        ts_lbl.setStyleSheet("color:#888; font-size:13px; border:none; background:transparent;")
        slay.addWidget(ts_lbl)
        slay.addStretch()

        _btn_ss = (
            "QPushButton { background:transparent; border:none;"
            "border-radius:4px; font-size:13px; padding:2px 4px; color:#ccc; }"
            "QPushButton:hover { background:#ffffff22; }"
        )

        # Preview button
        prev_btn = QPushButton("🔍")
        prev_btn.setFixedSize(26, 26)
        prev_btn.setToolTip("Preview")
        prev_btn.setStyleSheet(_btn_ss)
        prev_btn.clicked.connect(lambda _, e=entry: self._history_preview(e))
        slay.addWidget(prev_btn)

        # Copy URL + Open in Browser (only if URL exists)
        if url:
            copy_btn = QPushButton("🔗")
            copy_btn.setFixedSize(26, 26)
            copy_btn.setToolTip("Copy URL")
            copy_btn.setStyleSheet(_btn_ss)
            copy_btn.clicked.connect(lambda _, u=url: self._history_copy_url(u))
            slay.addWidget(copy_btn)

            open_btn = QPushButton("🌐")
            open_btn.setFixedSize(26, 26)
            open_btn.setToolTip("Open in Browser")
            open_btn.setStyleSheet(_btn_ss)
            open_btn.clicked.connect(lambda _, u=url: self._history_open_browser(u))
            slay.addWidget(open_btn)

        # Delete button
        del_btn = QPushButton("🗑")
        del_btn.setFixedSize(26, 26)
        del_btn.setToolTip("Delete")
        del_btn.setStyleSheet(
            "QPushButton { background:transparent; border:none;"
            "border-radius:4px; font-size:13px; padding:2px 4px; color:#ff6b6b; }"
            "QPushButton:hover { background:#ff000033; }"
        )
        del_btn.clicked.connect(lambda _, eid=entry["id"]: self._history_delete(eid))
        slay.addWidget(del_btn)

        vlay.addWidget(strip)
        return card

    def _history_preview(self, entry):
        from .history_manager import HistoryManager
        from PyQt5.QtWidgets import QApplication as _QApp

        # Load full-resolution image from disk (falls back to thumbnail)
        px = HistoryManager.load_full_pixmap(entry)
        if not px or px.isNull():
            return

        dlg = QDialog(self)
        dlg.setWindowTitle("Preview — KShot")
        dlg.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        dlg.setStyleSheet(
            "QDialog { background:#0d1117; border:1px solid #30363d; border-radius:10px; }"
            "QLabel  { color:#e6edf3; }"
            "QPushButton { border-radius:6px; padding:6px 18px; font-size:14px; }"
        )

        vlay = QVBoxLayout(dlg)
        vlay.setContentsMargins(16, 16, 16, 14)
        vlay.setSpacing(10)

        # Scale to fit screen (max 1200×800), no upscaling if image is smaller
        screen = _QApp.primaryScreen().availableGeometry()
        max_w  = min(screen.width()  - 80, 1200)
        max_h  = min(screen.height() - 160, 800)
        if px.width() <= max_w and px.height() <= max_h:
            big = px   # already fits, show at native resolution
        else:
            big = px.scaled(max_w, max_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        img_lbl = QLabel()
        img_lbl.setPixmap(big)
        img_lbl.setAlignment(Qt.AlignCenter)
        img_lbl.setStyleSheet(
            "border:1px solid #30363d; border-radius:6px; background:#010409; padding:4px;"
        )
        vlay.addWidget(img_lbl)

        # Metadata row
        url  = entry.get("url", "")
        ts   = entry.get("timestamp", "")[:16].replace("T", " ")
        etype = entry.get("type", "").upper()
        meta = QLabel(f"{ts}  •  {etype}" + (f"  •  {url}" if url else ""))
        meta.setAlignment(Qt.AlignCenter)
        meta.setStyleSheet("font-size:13px; color:#8b949e;")
        meta.setWordWrap(True)
        vlay.addWidget(meta)

        # Action buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        if url:
            copy_btn = QPushButton("Copy URL")
            copy_btn.setStyleSheet(
                "QPushButton { background:#21262d; color:#58a6ff; border:1px solid #30363d; }"
                "QPushButton:hover { background:#30363d; }"
            )
            copy_btn.clicked.connect(lambda: self._history_copy_url(url))
            btn_row.addWidget(copy_btn)

            open_btn = QPushButton("Open in Browser")
            open_btn.setStyleSheet(
                "QPushButton { background:#21262d; color:#79c0ff; border:1px solid #30363d; }"
                "QPushButton:hover { background:#30363d; }"
            )
            open_btn.clicked.connect(lambda: self._history_open_browser(url))
            btn_row.addWidget(open_btn)

        close_btn = QPushButton("Close")
        close_btn.setStyleSheet(
            "QPushButton { background:#238636; color:#fff; border:1px solid #2ea043; }"
            "QPushButton:hover { background:#2ea043; }"
        )
        close_btn.clicked.connect(dlg.accept)
        btn_row.addWidget(close_btn)
        btn_row.addStretch()
        vlay.addLayout(btn_row)

        dlg.exec_()

    def _history_copy_url(self, url, btn=None):
        from PyQt5.QtWidgets import QApplication
        QApplication.clipboard().setText(url)
        # Tray notification
        try:
            mw = QApplication.instance().property("main_window")
            if mw and hasattr(mw, 'tray_icon'):
                from PyQt5.QtWidgets import QSystemTrayIcon
                mw.tray_icon.showMessage(
                    "KShot — URL Copied",
                    url[:80] + ("…" if len(url) > 80 else ""),
                    QSystemTrayIcon.Information, 3000
                )
        except Exception:
            pass

    def _history_open_browser(self, url):
        import webbrowser
        try:
            webbrowser.open(url)
        except Exception as e:
            print(f"[HISTORY] open browser error: {e}")

    def _history_delete(self, entry_id):
        self._history_mgr.delete(entry_id)
        self._history_refresh()

    def _history_clear_all(self):
        mb = QMessageBox(self)
        mb.setWindowTitle("Clear History")
        mb.setText("Hapus semua history?")
        mb.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        mb.setIcon(QMessageBox.Question)
        # Fix vertical alignment of text label next to icon
        mb.setStyleSheet(
            mb.styleSheet() +
            "QLabel { qproperty-alignment: AlignVCenter; min-height: 32px; }"
        )
        r = mb.exec_()
        if r == QMessageBox.Yes:
            self._history_mgr.clear()
            self._history_refresh()

    # ── General tab ──────────────────────────────────────────────────────

    def _tab_general(self):
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        inner  = QWidget()
        lay    = QVBoxLayout(inner)
        lay.setContentsMargins(8, 8, 8, 8); lay.setSpacing(14)

        # Save path
        grp_save = QGroupBox("Save Path")
        fl = QFormLayout(grp_save); fl.setSpacing(8)

        path_row = QHBoxLayout()
        self.save_path_input = QLineEdit()
        self.save_path_input.setPlaceholderText("Default: Pictures/kshot")
        change_btn = QPushButton("Change")
        change_btn.setFixedHeight(34)
        change_btn.setMinimumWidth(110)
        change_btn.clicked.connect(self._browse_path)
        path_row.addWidget(self.save_path_input)
        path_row.addWidget(change_btn)
        fl.addRow(path_row)

        self.fixed_path_check = QCheckBox("Use fixed path for screenshots to save")
        fl.addRow(self.fixed_path_check)

        ext_row = QHBoxLayout()
        ext_lbl = QLabel("Preferred save file extension:")
        self.ext_combo = QComboBox()
        self.ext_combo.addItems(["png", "jpg"])
        self.ext_combo.setFixedWidth(80)
        ext_row.addWidget(ext_lbl); ext_row.addWidget(self.ext_combo); ext_row.addStretch()
        fl.addRow(ext_row)

        lay.addWidget(grp_save)

        # Image quality
        grp_img = QGroupBox("Image")
        fl2 = QFormLayout(grp_img); fl2.setSpacing(8)

        q_row = QHBoxLayout()
        self.jpeg_spin = QSpinBox()
        self.jpeg_spin.setRange(1, 100); self.jpeg_spin.setValue(90)
        self.jpeg_spin.setFixedWidth(70)
        q_row.addWidget(self.jpeg_spin)
        q_row.addWidget(QLabel("JPEG Quality (1–100)"))
        q_row.addStretch()
        fl2.addRow(q_row)

        lay.addWidget(grp_img)

        # Notifications & clipboard
        grp_notif = QGroupBox("Notifications & Clipboard")
        vl = QVBoxLayout(grp_notif)
        self.auto_copy_check = QCheckBox("Copy URL to clipboard after upload")
        self.show_notif_check = QCheckBox("Show notification after upload")
        vl.addWidget(self.auto_copy_check)
        vl.addWidget(self.show_notif_check)
        lay.addWidget(grp_notif)

        # Config file
        # grp_cfg = QGroupBox("Configuration File")
        # h = QHBoxLayout(grp_cfg)
        # exp_btn = QPushButton("Export"); exp_btn.clicked.connect(self._export_config)
        # imp_btn = QPushButton("Import"); imp_btn.clicked.connect(self._import_config)
        # rst_btn = QPushButton("Reset");  rst_btn.clicked.connect(self._reset_config)
        # h.addWidget(exp_btn); h.addWidget(imp_btn); h.addWidget(rst_btn); h.addStretch()
        # lay.addWidget(grp_cfg)

        lay.addStretch()
        scroll.setWidget(inner)
        return scroll

    # ── Interface tab ────────────────────────────────────────────────────────

    def _tab_interface(self):
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        inner  = QWidget()
        lay    = QVBoxLayout(inner)
        lay.setContentsMargins(8, 8, 8, 8); lay.setSpacing(14)

        # ── Color presets ──
        grp_cp = QGroupBox("Colorpicker — Preset Warna Annotasi")
        vcp    = QVBoxLayout(grp_cp); vcp.setSpacing(8)

        hint_cp = QLabel("Klik warna untuk memilih, klik 2× untuk mengedit. "
                         "Warna ini muncul sebagai pilihan di toolbar screenshot.")
        hint_cp.setWordWrap(True)
        hint_cp.setStyleSheet("color:#9999bb; font-size:14px;")
        vcp.addWidget(hint_cp)

        # Color circles grid
        self._color_presets = list(self.config.get('color_presets', [
            '#f5cb11','#ff4444','#ff8800','#44cc44',
            '#4488ff','#cc44ff',
        ]))
        self._selected_color_idx = 0
        self._color_btns = []

        self._colors_grid = QWidget()
        self._colors_layout = QGridLayout(self._colors_grid)
        self._colors_layout.setSpacing(6)
        self._rebuild_color_grid()
        vcp.addWidget(self._colors_grid)

        # Edit / Add row
        edit_row = QHBoxLayout()
        self._color_hex_edit = QLineEdit()
        self._color_hex_edit.setPlaceholderText("#rrggbb")
        self._color_hex_edit.setFixedWidth(100)

        pick_btn = QPushButton("Pick")
        pick_btn.setFixedHeight(34)
        pick_btn.setMinimumWidth(90)
        pick_btn.clicked.connect(self._pick_color_for_edit)

        update_btn = QPushButton("Update")
        update_btn.setFixedHeight(34)
        update_btn.setMinimumWidth(100)
        update_btn.clicked.connect(self._update_color)

        delete_btn = QPushButton("Delete")
        delete_btn.setFixedHeight(34)
        delete_btn.setMinimumWidth(90)
        delete_btn.clicked.connect(self._delete_color)

        add_btn = QPushButton("+ Add")
        add_btn.setFixedHeight(34)
        add_btn.setMinimumWidth(90)
        add_btn.clicked.connect(self._add_color)

        edit_row.addWidget(QLabel("Hex:"))
        edit_row.addWidget(self._color_hex_edit)
        edit_row.addWidget(pick_btn)
        edit_row.addWidget(update_btn)
        edit_row.addWidget(delete_btn)
        edit_row.addStretch()
        edit_row.addWidget(add_btn)
        vcp.addLayout(edit_row)

        lay.addWidget(grp_cp)

        # ── Selection color + Toolbar colors — 2 kolom ──────────────────
        color_grid = QHBoxLayout()
        color_grid.setSpacing(10)

        # Kolom kiri: Warna Garis Seleksi
        grp_sel = QGroupBox("Warna Garis Seleksi")
        grp_sel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        vsel = QVBoxLayout(grp_sel); vsel.setSpacing(6)
        sel_hint = QLabel("Border kotak seleksi\ndan handle pojok")
        sel_hint.setAlignment(Qt.AlignCenter)
        sel_hint.setStyleSheet("color:#9999bb; font-size:14px;")
        sel_hint.setWordWrap(True)
        self._sel_color = self.config.get('selection_color', '#f5cb11')
        self._sel_color_btn = QPushButton()
        self._sel_color_btn.setFixedSize(36, 36)
        self._sel_color_btn.setStyleSheet(
            f"background:{self._sel_color}; border:1px solid #555; border-radius:4px;")
        self._sel_color_btn.clicked.connect(self._pick_selection_color)
        self._sel_color_lbl = QLabel(self._sel_color)
        self._sel_color_lbl.setAlignment(Qt.AlignCenter)
        self._sel_color_lbl.setStyleSheet("color:#c0c0f0; font-family:monospace;")
        vsel.addWidget(sel_hint)
        vsel.addWidget(self._sel_color_btn, 0, Qt.AlignCenter)
        vsel.addWidget(self._sel_color_lbl, 0, Qt.AlignCenter)
        vsel.addStretch()

        # Kolom kanan: Warna Tombol Toolbar
        grp_tb_clr = QGroupBox("Warna Tombol Toolbar")
        grp_tb_clr.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        vtbc = QVBoxLayout(grp_tb_clr); vtbc.setSpacing(6)
        tbc_hint = QLabel("Background dan warna\nicon pada toolbar.")
        tbc_hint.setWordWrap(True)
        tbc_hint.setAlignment(Qt.AlignCenter)
        tbc_hint.setStyleSheet("color:#9999bb; font-size:14px;")
        vtbc.addWidget(tbc_hint)

        self._tb_bg_color   = self.config.get('toolbar_bg_color',   '#000a52')
        self._tb_icon_color = self.config.get('toolbar_icon_color',  '#f5cb11')

        tbc_row = QHBoxLayout(); tbc_row.setSpacing(16)
        bg_col = QVBoxLayout()
        bg_lbl = QLabel("Background")
        bg_lbl.setAlignment(Qt.AlignCenter)
        bg_lbl.setStyleSheet("color:#c0c0f0;font-size:14px;")
        self._tb_bg_btn = QPushButton()
        self._tb_bg_btn.setFixedSize(36, 36)
        self._tb_bg_btn.setStyleSheet(
            f"background:{self._tb_bg_color}; border:1px solid #555; border-radius:4px;")
        self._tb_bg_btn.clicked.connect(self._pick_toolbar_bg)
        bg_col.addWidget(bg_lbl, 0, Qt.AlignCenter)
        bg_col.addWidget(self._tb_bg_btn, 0, Qt.AlignCenter)

        ic_col = QVBoxLayout()
        ic_lbl = QLabel("Icon / Teks")
        ic_lbl.setAlignment(Qt.AlignCenter)
        ic_lbl.setStyleSheet("color:#c0c0f0;font-size:14px;")
        self._tb_icon_btn = QPushButton()
        self._tb_icon_btn.setFixedSize(36, 36)
        self._tb_icon_btn.setStyleSheet(
            f"background:{self._tb_icon_color}; border:1px solid #555; border-radius:4px;")
        self._tb_icon_btn.clicked.connect(self._pick_toolbar_icon)
        ic_col.addWidget(ic_lbl, 0, Qt.AlignCenter)
        ic_col.addWidget(self._tb_icon_btn, 0, Qt.AlignCenter)

        tbc_row.addStretch()
        tbc_row.addLayout(bg_col)
        tbc_row.addLayout(ic_col)
        tbc_row.addStretch()
        vtbc.addLayout(tbc_row)

        self._tb_preview = QLabel("Aa  ↗  ✏")
        self._tb_preview.setAlignment(Qt.AlignCenter)
        self._update_toolbar_preview()
        vtbc.addWidget(self._tb_preview)

        color_grid.addWidget(grp_sel)
        color_grid.addWidget(grp_tb_clr)
        lay.addLayout(color_grid)

        # ── Overlay opacity ──
        grp_op = QGroupBox("Opacity Area di Luar Seleksi")
        vop = QVBoxLayout(grp_op); vop.setSpacing(6)

        op_row = QHBoxLayout()
        self._opacity_lbl = QLabel("0%")
        self._opacity_lbl.setFixedWidth(38)
        self._opacity_slider = QSlider(Qt.Horizontal)
        self._opacity_slider.setRange(0, 255)
        self._opacity_slider.setValue(self.config.get('overlay_opacity', 100))
        self._opacity_slider.valueChanged.connect(
            lambda v: self._opacity_lbl.setText(f"{int(v/255*100)}%"))
        self._opacity_lbl.setText(f"{int(self._opacity_slider.value()/255*100)}%")
        self._opacity_slider.setStyleSheet(
            "QSlider::groove:horizontal{background:#252540;height:6px;border-radius:3px;}"
            "QSlider::handle:horizontal{background:#6060ff;width:14px;height:14px;"
            "margin:-4px 0;border-radius:7px;}"
            "QSlider::sub-page:horizontal{background:#4040d0;border-radius:3px;}"
        )
        op_row.addWidget(QLabel("0%"))
        op_row.addWidget(self._opacity_slider)
        op_row.addWidget(QLabel("100%"))
        op_row.addWidget(self._opacity_lbl)
        vop.addLayout(op_row)
        lay.addWidget(grp_op)

        # ── Toolbar buttons ──
        grp_tb = QGroupBox("Tombol Toolbar — Centang untuk tampilkan")
        vtb = QVBoxLayout(grp_tb); vtb.setSpacing(6)

        hint_tb = QLabel("Pilih tombol mana yang tampil di toolbar screenshot.")
        hint_tb.setWordWrap(True)
        hint_tb.setStyleSheet("color:#9999bb; font-size:14px;")
        vtb.addWidget(hint_tb)

        self._ALL_BUTTONS = [
            # (identifier, label, row, col)
            ('pen',           'Pencil',        0, 0),
            ('line',          'Line',          0, 1),
            ('arrow',         'Arrow',         0, 2),
            ('rectangle',     'Rectangle',     0, 3),
            ('circle',        'Circle',        1, 0),
            ('filled_rect',   'Filled Box',    1, 1),
            ('highlighter',   'Highlighter',   1, 2),
            ('text',          'Text',          1, 3),
            ('number',        'Number',        2, 0),
            ('blur',          'Blur',          2, 1),
            ('invert',        'Invert',        2, 2),
            ('color_picker',  'Color Picker',  2, 3),
            ('pin',           'Pin',           3, 0),
            ('save_local',    'Save Local',    3, 1),
            ('save_upload',   'Save & Upload', 3, 2),
            ('copy_clipboard','Copy',          3, 3),
            ('undo',          'Undo',          4, 0),
            ('redo',          'Redo',          4, 1),
        ]
        hidden_now = set(self.config.get('hidden_buttons', []))
        tb_grid = QGridLayout(); tb_grid.setSpacing(4)
        self._tb_checks = {}
        from PyQt5.QtWidgets import QCheckBox
        for btn_id, label, row, col in self._ALL_BUTTONS:
            cb = QCheckBox(label)
            cb.setChecked(btn_id not in hidden_now)
            cb.setStyleSheet("color:#d0d0f0; font-size:14px;")
            tb_grid.addWidget(cb, row, col)
            self._tb_checks[btn_id] = cb
        vtb.addLayout(tb_grid)
        lay.addWidget(grp_tb)

        lay.addStretch()
        scroll.setWidget(inner)
        return scroll

    # Color preset helpers
    def _rebuild_color_grid(self):
        # Clear existing
        while self._colors_layout.count():
            item = self._colors_layout.takeAt(0)
            if item.widget():
                item.widget().hide()
                item.widget().deleteLater()
        self._color_btns.clear()

        cols = 8
        for i, hex_c in enumerate(self._color_presets):
            btn = QPushButton()
            btn.setFixedSize(32, 32)
            btn.setToolTip(hex_c)
            border = "2px solid #ffffff" if i == self._selected_color_idx else "2px solid transparent"
            # Use QPushButton{} selector so child stylesheet wins over _DARK's QPushButton rule
            btn.setStyleSheet(
                f"QPushButton {{ background:{hex_c}; border:{border}; "
                f"border-radius:16px; padding:0px; outline:none; }}"
                f"QPushButton:hover {{ border:2px solid #aaaaff; }}")
            btn.clicked.connect(lambda _, idx=i: self._select_color(idx))
            self._colors_layout.addWidget(btn, i // cols, i % cols)
            self._color_btns.append(btn)

        if self._color_presets and hasattr(self, '_color_hex_edit'):
            self._color_hex_edit.setText(
                self._color_presets[min(self._selected_color_idx,
                                        len(self._color_presets)-1)])

    def _select_color(self, idx):
        self._selected_color_idx = idx
        self._rebuild_color_grid()

    def _pick_color_for_edit(self):
        cur = self._color_hex_edit.text() or '#ffffff'
        c = QColorDialog.getColor(QColor(cur), self, "Pilih Warna")
        if c.isValid():
            self._color_hex_edit.setText(c.name())

    def _update_color(self):
        if not self._color_presets: return
        idx = min(self._selected_color_idx, len(self._color_presets)-1)
        self._color_presets[idx] = self._color_hex_edit.text()
        self._rebuild_color_grid()

    def _delete_color(self):
        if not self._color_presets: return
        idx = min(self._selected_color_idx, len(self._color_presets)-1)
        self._color_presets.pop(idx)
        self._selected_color_idx = max(0, idx-1)
        self._rebuild_color_grid()

    def _add_color(self):
        c = QColorDialog.getColor(QColor('#ff0000'), self, "Tambah Warna")
        if c.isValid():
            self._color_presets.append(c.name())
            self._selected_color_idx = len(self._color_presets)-1
            self._rebuild_color_grid()

    def _pick_toolbar_bg(self):
        c = QColorDialog.getColor(QColor(self._tb_bg_color), self, "Pilih Warna Background Toolbar")
        if c.isValid():
            self._tb_bg_color = c.name()
            self._tb_bg_btn.setStyleSheet(
                f"background:{self._tb_bg_color}; border:1px solid #555; border-radius:4px;")
            self._update_toolbar_preview()

    def _pick_toolbar_icon(self):
        c = QColorDialog.getColor(QColor(self._tb_icon_color), self, "Pilih Warna Icon Toolbar")
        if c.isValid():
            self._tb_icon_color = c.name()
            self._tb_icon_btn.setStyleSheet(
                f"background:{self._tb_icon_color}; border:1px solid #555; border-radius:4px;")
            self._update_toolbar_preview()

    def _update_toolbar_preview(self):
        self._tb_preview.setStyleSheet(
            f"background:{self._tb_bg_color}; color:{self._tb_icon_color};"
            "border-radius:8px; padding:6px 14px; font-size:16px; font-weight:bold;")

    def _pick_selection_color(self):
        c = QColorDialog.getColor(QColor(self._sel_color), self, "Pilih Warna Garis Seleksi")
        if c.isValid():
            self._sel_color = c.name()
            self._sel_color_btn.setStyleSheet(
                f"background:{self._sel_color}; border:1px solid #555; border-radius:4px;")
            self._sel_color_lbl.setText(self._sel_color)

    # ── Filename Editor tab ───────────────────────────────────────────────────

    def _tab_filename(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(10, 10, 10, 10); lay.setSpacing(10)

        lbl = QLabel("Edit the name of your captures:")
        lbl.setStyleSheet("color:#ccc; font-size:14px;")
        lay.addWidget(lbl)

        # Token buttons grid (2 columns)
        tokens = [
            ("Full Date (%Y-%m-%d)",   "%Y-%m-%d"),
            ("Year (2000+)",           "%Y"),
            ("Year (00-99)",           "%y"),
            ("Month (01-12)",          "%m"),
            ("Day (01-31)",            "%d"),
            ("Hour (00-23)",           "%H"),
            ("Hour (01-12)",           "%I"),
            ("Minute (00-59)",         "%M"),
            ("Second (00-59)",         "%S"),
            ("Day of Year (001-366)",  "%j"),
            ("Week Day (1-7)",         "%u"),
            ("Week (00-53)",           "%W"),
        ]
        grid = QGridLayout(); grid.setSpacing(6)
        for i, (label, token) in enumerate(tokens):
            btn = QPushButton(label)
            btn.setObjectName("token_btn")
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.setFixedHeight(34)
            btn.clicked.connect(lambda _, t=token: self._insert_token(t))
            grid.addWidget(btn, i // 2, i % 2)
        lay.addLayout(grid)

        # Edit field
        edit_lbl = QLabel("Edit:"); edit_lbl.setStyleSheet("color:#ccc;")
        lay.addWidget(edit_lbl)
        self.fname_edit = QLineEdit()
        self.fname_edit.textChanged.connect(self._update_preview)
        lay.addWidget(self.fname_edit)

        # Preview field
        prev_lbl = QLabel("Preview:"); prev_lbl.setStyleSheet("color:#ccc;")
        lay.addWidget(prev_lbl)
        self.fname_preview = QLineEdit()
        self.fname_preview.setReadOnly(True)
        lay.addWidget(self.fname_preview)

        # Buttons
        btn_row = QHBoxLayout()
        save_fn  = QPushButton("Save");    save_fn.clicked.connect(self._save_filename)
        rest_fn  = QPushButton("Restore"); rest_fn.clicked.connect(self._restore_filename)
        clear_fn = QPushButton("Clear");   clear_fn.clicked.connect(lambda: self.fname_edit.clear())
        btn_row.addWidget(save_fn); btn_row.addWidget(rest_fn); btn_row.addWidget(clear_fn)
        btn_row.addStretch()
        lay.addLayout(btn_row)

        lay.addStretch()
        return w

    # ── Shortcuts tab ─────────────────────────────────────────────────────────

    def _tab_shortcuts(self):
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        inner  = QWidget()
        lay    = QVBoxLayout(inner)
        lay.setContentsMargins(8, 8, 8, 8); lay.setSpacing(12)

        hint = QLabel("Klik tombol di kolom <b>Key</b> lalu tekan kombinasi keyboard. "
                      "<b>Esc</b> = batal. Ikon abu-abu = tidak dapat diubah.")
        hint.setWordWrap(True)
        hint.setStyleSheet("color:#9999bb; font-size:14px;")
        lay.addWidget(hint)

        # ── Configurable global hotkeys ──
        self._shortcut_defs = [
            ("Open Settings",       "hotkey_settings",    "ctrl+shift+s"),
            ("Capture fullscreen",  "hotkey_fullscreen",  "ctrl+shift+f"),
        ]
        self._shortcut_widgets = {}

        grp_global = QGroupBox("Global Hotkeys")
        gl = QVBoxLayout(grp_global); gl.setSpacing(8)

        # Area screenshot is fixed to Print Screen
        row_area = QHBoxLayout()
        lbl_area = QLabel("Capture area screenshot"); lbl_area.setMinimumWidth(250)
        key_area = QLabel("Print Screen")
        key_area.setStyleSheet(
            "color:#a0a0cc; background:#252540; border:1px solid #3a3a60;"
            "border-radius:4px; padding:3px 10px; font-family:monospace; font-size:14px;")
        key_area.setAlignment(Qt.AlignCenter)
        key_area.setFixedWidth(180)
        key_area.setToolTip("Shortcut ini tetap, tidak dapat diubah")
        row_area.addWidget(lbl_area); row_area.addStretch(); row_area.addWidget(key_area)
        gl.addLayout(row_area)

        for display, cfg_key, default in self._shortcut_defs:
            row = QHBoxLayout()
            lbl = QLabel(display); lbl.setMinimumWidth(250)
            cap = ShortcutCapture(self.config.get(cfg_key, default))
            cap.setMinimumWidth(180)
            self._shortcut_widgets[cfg_key] = cap
            row.addWidget(lbl); row.addStretch(); row.addWidget(cap)
            gl.addLayout(row)
        lay.addWidget(grp_global)

        # Helper: build a configurable shortcut row
        def _cfg_row(parent_lay, label_text, cfg_key, default):
            row = QHBoxLayout()
            lbl = QLabel(label_text); lbl.setMinimumWidth(220)
            cap = ShortcutCapture(self.config.get(cfg_key, default))
            cap.setMinimumWidth(160)
            self._shortcut_widgets[cfg_key] = cap
            row.addWidget(lbl); row.addStretch(); row.addWidget(cap)
            parent_lay.addLayout(row)

        # Helper: build a fixed (non-editable) row
        def _fixed_row(parent_lay, label_text, key_text):
            row = QHBoxLayout()
            d = QLabel(label_text); d.setMinimumWidth(220)
            k = QLabel(key_text)
            k.setStyleSheet(
                "color:#606080; background:#1a1a2e; border:1px solid #2a2a50;"
                "border-radius:4px; padding:3px 10px; font-family:monospace; font-size:14px;")
            k.setAlignment(Qt.AlignCenter)
            k.setFixedWidth(160)
            row.addWidget(d); row.addStretch(); row.addWidget(k)
            parent_lay.addLayout(row)

        # ── Capture & Selection ──
        grp_cap = QGroupBox("Capture & Selection")
        gc = QVBoxLayout(grp_cap); gc.setSpacing(6)
        _cfg_row(gc, "Accept / Save & Upload",  "shortcut_save",   "return")
        _cfg_row(gc, "Cancel capture",          "shortcut_cancel", "escape")
        _cfg_row(gc, "Copy to Clipboard",       "shortcut_copy",   "ctrl+c")
        _fixed_row(gc, "Save to Local",                   "💾 (toolbar)")
        _fixed_row(gc, "Pin to screen",                   "📌 (toolbar)")
        _fixed_row(gc, "Move selection ±1px",             "Shift + Arrow")
        _fixed_row(gc, "Resize selection",                "Mouse drag")
        lay.addWidget(grp_cap)

        # ── Annotation Tools ──
        grp_tools = QGroupBox("Annotation Tools")
        gt = QVBoxLayout(grp_tools); gt.setSpacing(6)
        _cfg_row(gt, "Pencil",       "shortcut_pen",         "p")
        _cfg_row(gt, "Line",         "shortcut_line",        "l")
        _cfg_row(gt, "Arrow",        "shortcut_arrow",       "a")
        _cfg_row(gt, "Rectangle",    "shortcut_rect",        "r")
        _cfg_row(gt, "Circle",       "shortcut_circle",      "c")
        _cfg_row(gt, "Highlighter",  "shortcut_highlighter", "m")
        _cfg_row(gt, "Text",         "shortcut_text",        "t")
        _cfg_row(gt, "Number",       "shortcut_number",      "n")
        _cfg_row(gt, "Blur",         "shortcut_blur",        "b")
        _cfg_row(gt, "Invert",       "shortcut_invert",      "i")
        lay.addWidget(grp_tools)

        # ── Editing ──
        grp_edit = QGroupBox("Editing")
        ge = QVBoxLayout(grp_edit); ge.setSpacing(6)
        _cfg_row(ge, "Undo",  "shortcut_undo", "ctrl+z")
        _cfg_row(ge, "Redo",  "shortcut_redo", "ctrl+y")
        _fixed_row(ge, "Increase tool size", "+ (toolbar)")
        _fixed_row(ge, "Decrease tool size", "− (toolbar)")
        lay.addWidget(grp_edit)

        # Wire up conflict checker on all shortcut widgets
        # Build label map: cfg_key -> display label
        _labels = {
            'hotkey_settings':   'Open Settings',
            'hotkey_fullscreen': 'Capture fullscreen',
            'shortcut_save':        'Accept / Save & Upload',
            'shortcut_cancel':      'Cancel capture',
            'shortcut_copy':        'Copy to Clipboard',
            'shortcut_undo':        'Undo',
            'shortcut_redo':        'Redo',
            'shortcut_pen':         'Pencil',
            'shortcut_line':        'Line',
            'shortcut_arrow':       'Arrow',
            'shortcut_rect':        'Rectangle',
            'shortcut_circle':      'Circle',
            'shortcut_highlighter': 'Highlighter',
            'shortcut_text':        'Text',
            'shortcut_number':      'Number',
            'shortcut_blur':        'Blur',
            'shortcut_invert':      'Invert',
        }

        def _check_conflict(new_sc, this_widget):
            for cfg_key, widget in self._shortcut_widgets.items():
                if widget is this_widget:
                    continue
                if widget.value().lower() == new_sc.lower():
                    return _labels.get(cfg_key, cfg_key)
            return None

        for widget in self._shortcut_widgets.values():
            widget.set_conflict_checker(_check_conflict)

        lay.addStretch()
        scroll.setWidget(inner)
        return scroll

    # ── Load / Save ───────────────────────────────────────────────────────────

    def _load_settings(self):
        self.save_path_input.setText(self.config.get('local_save_path', ''))
        self.fixed_path_check.setChecked(self.config.get('use_fixed_path', False))
        ext = self.config.get('preferred_extension', 'png')
        idx = self.ext_combo.findText(ext)
        if idx >= 0: self.ext_combo.setCurrentIndex(idx)
        self.jpeg_spin.setValue(self.config.get('jpeg_quality', 90))
        self.auto_copy_check.setChecked(self.config.get('auto_copy_url', True))
        self.show_notif_check.setChecked(self.config.get('show_notification', True))
        tmpl = self.config.get('filename_template', self.DEFAULT_TEMPLATE)
        self.fname_edit.setText(tmpl)
        self._update_preview()
        # Interface
        self._color_presets = list(self.config.get('color_presets', self._color_presets))
        self._rebuild_color_grid()
        self._opacity_slider.setValue(self.config.get('overlay_opacity', 100))
        self._sel_color = self.config.get('selection_color', '#f5cb11')
        self._sel_color_btn.setStyleSheet(
            f"background:{self._sel_color}; border:1px solid #555; border-radius:4px;")
        self._sel_color_lbl.setText(self._sel_color)
        self._tb_bg_color   = self.config.get('toolbar_bg_color',   '#000a52')
        self._tb_icon_color = self.config.get('toolbar_icon_color',  '#f5cb11')
        self._tb_bg_btn.setStyleSheet(
            f"background:{self._tb_bg_color}; border:1px solid #555; border-radius:4px;")
        self._tb_icon_btn.setStyleSheet(
            f"background:{self._tb_icon_color}; border:1px solid #555; border-radius:4px;")
        self._update_toolbar_preview()
        hidden_now = set(self.config.get('hidden_buttons', []))
        for btn_id, cb in self._tb_checks.items():
            cb.setChecked(btn_id not in hidden_now)
        # Reload shortcut widgets
        _SC_DEFAULTS = {
            'shortcut_save': 'return', 'shortcut_cancel': 'escape',
            'shortcut_copy': 'ctrl+c', 'shortcut_undo': 'ctrl+z',
            'shortcut_redo': 'ctrl+y', 'shortcut_pen': 'p',
            'shortcut_line': 'l', 'shortcut_arrow': 'a',
            'shortcut_rect': 'r', 'shortcut_circle': 'c',
            'shortcut_highlighter': 'm', 'shortcut_text': 't',
            'shortcut_number': 'n', 'shortcut_blur': 'b',
            'shortcut_invert': 'i',
        }
        for cfg_key, default in _SC_DEFAULTS.items():
            if cfg_key in self._shortcut_widgets:
                self._shortcut_widgets[cfg_key]._shortcut = self.config.get(cfg_key, default)
                self._shortcut_widgets[cfg_key]._refresh()

    def _save(self):
        self.config.set('local_save_path',     self.save_path_input.text())
        self.config.set('use_fixed_path',      self.fixed_path_check.isChecked())
        self.config.set('preferred_extension', self.ext_combo.currentText())
        self.config.set('jpeg_quality',        self.jpeg_spin.value())
        self.config.set('auto_copy_url',       self.auto_copy_check.isChecked())
        self.config.set('show_notification',   self.show_notif_check.isChecked())
        self.config.set('filename_template',   self.fname_edit.text() or self.DEFAULT_TEMPLATE)
        # Interface
        self.config.set('color_presets',   self._color_presets)
        self.config.set('overlay_opacity', self._opacity_slider.value())
        self.config.set('selection_color',    self._sel_color)
        self.config.set('toolbar_bg_color',   self._tb_bg_color)
        self.config.set('toolbar_icon_color',  self._tb_icon_color)
        hidden = [bid for bid, cb in self._tb_checks.items() if not cb.isChecked()]
        self.config.set('hidden_buttons', hidden)
        for cfg_key, widget in self._shortcut_widgets.items():
            v = widget.value()
            if v: self.config.set(cfg_key, v)
        self.accept()

    # ── Filename helpers ──────────────────────────────────────────────────────

    def _insert_token(self, token):
        cur = self.fname_edit.cursorPosition()
        txt = self.fname_edit.text()
        self.fname_edit.setText(txt[:cur] + token + txt[cur:])
        self.fname_edit.setCursorPosition(cur + len(token))
        self.fname_edit.setFocus()

    def _update_preview(self):
        tmpl = self.fname_edit.text()
        try:
            preview = datetime.now().strftime(tmpl)
        except Exception:
            preview = tmpl
        ext = self.ext_combo.currentText() if hasattr(self, 'ext_combo') else 'png'
        self.fname_preview.setText(f"{preview}.{ext}")

    def _save_filename(self):
        self.config.set('filename_template', self.fname_edit.text() or self.DEFAULT_TEMPLATE)

    def _restore_filename(self):
        self.fname_edit.setText(self._orig_template)

    # ── General helpers ───────────────────────────────────────────────────────

    def _browse_path(self):
        path = QFileDialog.getExistingDirectory(self, "Pilih Folder Simpan")
        if path: self.save_path_input.setText(path)

    def _export_config(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Config", "kshot_config.json", "JSON (*.json)")
        if path:
            try:
                with open(path, 'w') as f:
                    json.dump(self.config.config, f, indent=4)
                QMessageBox.information(self, "kshot", f"Config exported to:\n{path}")
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))

    def _import_config(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Import Config", "", "JSON (*.json)")
        if path:
            try:
                with open(path) as f:
                    data = json.load(f)
                for k, v in data.items():
                    self.config.set(k, v)
                self._load_settings()
                QMessageBox.information(self, "kshot", "Config imported.")
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))

    def _reset_config(self):
        mb = QMessageBox(self)
        mb.setWindowTitle("Reset Config")
        mb.setText("Reset semua settings ke default?")
        mb.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        mb.setIcon(QMessageBox.Question)
        mb.setStyleSheet(
            mb.styleSheet() +
            "QLabel { qproperty-alignment: AlignVCenter; min-height: 32px; }"
        )
        r = mb.exec_()
        if r == QMessageBox.Yes:
            defaults = self.config.default_config()
            for k, v in defaults.items():
                self.config.set(k, v)
            self._load_settings()
