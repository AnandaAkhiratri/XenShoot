"""
Settings dialog for XenShoot — Flameshot-style UI
Tabs: General | Filename Editor | Shortcuts
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QCheckBox, QGroupBox, QFormLayout, QFileDialog, QTabWidget, QWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QScrollArea, QFrame, QComboBox, QSpinBox, QGridLayout, QSizePolicy,
    QMessageBox, QSlider, QColorDialog
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
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
             "border-radius:4px;padding:4px 12px;font-family:monospace;font-size:13px;")
    _REC  = ("background:#1a3a5c;color:#7ec8e3;border:2px solid #7ec8e3;"
             "border-radius:4px;padding:4px 12px;font-family:monospace;font-size:13px;")
    _ERR  = ("background:#3a1a1a;color:#ff6b6b;border:2px solid #ff4444;"
             "border-radius:4px;padding:4px 12px;font-family:monospace;font-size:13px;")

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

    def _refresh(self):
        self.setText(self._shortcut or "—")

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
QDialog, QWidget       { background:#1a1a2e; color:#e8e8f0; }
QTabWidget::pane       { border:1px solid #3a3a5c; background:#1a1a2e; }
QTabBar::tab           { background:#252540; color:#9999bb; padding:9px 18px;
                         border:1px solid #3a3a5c; border-bottom:none;
                         border-radius:4px 4px 0 0; font-size:13px; }
QTabBar::tab:selected  { background:#1a1a2e; color:#ffffff; font-weight:bold; }
QTabBar::tab:hover     { color:#ddddff; }
QGroupBox              { color:#c0c0e0; border:1px solid #4a4a7a; border-radius:6px;
                         margin-top:12px; padding-top:12px; font-weight:bold; font-size:12px; }
QGroupBox::title       { subcontrol-origin:margin; left:12px; padding:0 6px;
                         color:#a0a0ff; }
QCheckBox              { color:#e0e0f8; spacing:8px; font-size:13px; }
QCheckBox::indicator   { width:17px; height:17px; border:2px solid #6060a0;
                         border-radius:3px; background:#252540; }
QCheckBox::indicator:checked   { background:#5050d0; border-color:#8080ff;
                                  image: none; }
QCheckBox::indicator:unchecked { background:#252540; }
QLineEdit              { background:#252540; color:#f0f0ff; border:1px solid #5050a0;
                         border-radius:4px; padding:5px 8px; font-size:13px; }
QLineEdit:focus        { border:1px solid #8080ff; }
QLineEdit[readOnly="true"] { background:#1e1e35; color:#8888aa; }
QComboBox              { background:#252540; color:#f0f0ff; border:1px solid #5050a0;
                         border-radius:4px; padding:5px 8px; font-size:13px; }
QComboBox QAbstractItemView { background:#252540; color:#f0f0ff; border:1px solid #5050a0; }
QSpinBox               { background:#252540; color:#f0f0ff; border:1px solid #5050a0;
                         border-radius:4px; padding:4px 6px; font-size:13px; }
QPushButton            { background:#2d2d50; color:#e0e0f8; border:1px solid #5050a0;
                         border-radius:4px; padding:6px 16px; font-size:13px; }
QPushButton:hover      { background:#3a3a6a; border-color:#9090d0; }
QPushButton#primary    { background:#3a3adc; border-color:#6060ff; color:white;
                         font-weight:bold; }
QPushButton#primary:hover { background:#5050ff; }
QPushButton#token_btn  { background:#2a2a48; color:#c0c0f0; border:1px solid #4a4a80;
                         border-radius:4px; padding:7px 4px; font-size:12px; }
QPushButton#token_btn:hover { background:#3a3a60; border-color:#8080c0; }
QLabel                 { color:#c8c8e8; font-size:13px; }
QHeaderView::section   { background:#252540; color:#a0a0cc; border:none;
                         border-bottom:1px solid #3a3a5c; padding:7px; font-size:13px; }
QScrollArea            { border:none; background:transparent; }
QScrollBar:vertical    { background:#1a1a2e; width:10px; }
QScrollBar::handle:vertical { background:#4040a0; border-radius:5px; min-height:20px; }
"""


class SettingsDialog(QDialog):
    DEFAULT_TEMPLATE = "xenshoot_%Y-%m-%d_%H-%M-%S"

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self._orig_template = config.get('filename_template', self.DEFAULT_TEMPLATE)
        self._init_ui()
        self._load_settings()

    # ── UI skeleton ──────────────────────────────────────────────────────────

    def _init_ui(self):
        self.setWindowTitle("XenShoot — Configuration")
        self.setModal(True)
        self.setMinimumSize(580, 520)
        self.setStyleSheet(_DARK)

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._tab_general(),   "⚙  General")
        self.tabs.addTab(self._tab_interface(), "🎨  Interface")
        self.tabs.addTab(self._tab_filename(),  "✎  Filename Editor")
        self.tabs.addTab(self._tab_shortcuts(), "⌨  Shortcuts")
        root.addWidget(self.tabs)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel = QPushButton("Cancel"); cancel.clicked.connect(self.reject)
        save   = QPushButton("Save");   save.setObjectName("primary")
        save.clicked.connect(self._save)
        btn_row.addWidget(cancel)
        btn_row.addWidget(save)
        root.addLayout(btn_row)

    # ── General tab ──────────────────────────────────────────────────────────

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
        self.save_path_input.setPlaceholderText("Default: Pictures/XenShoot")
        change_btn = QPushButton("Change…")
        change_btn.setFixedWidth(90)
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
        grp_cfg = QGroupBox("Configuration File")
        h = QHBoxLayout(grp_cfg)
        exp_btn = QPushButton("Export"); exp_btn.clicked.connect(self._export_config)
        imp_btn = QPushButton("Import"); imp_btn.clicked.connect(self._import_config)
        rst_btn = QPushButton("Reset");  rst_btn.clicked.connect(self._reset_config)
        h.addWidget(exp_btn); h.addWidget(imp_btn); h.addWidget(rst_btn); h.addStretch()
        lay.addWidget(grp_cfg)

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
        hint_cp.setStyleSheet("color:#9999bb; font-size:11px;")
        vcp.addWidget(hint_cp)

        # Color circles grid
        self._color_presets = list(self.config.get('color_presets', [
            '#f5cb11','#ff4444','#ff8800','#44cc44',
            '#4488ff','#cc44ff','#ffffff','#000000',
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

        pick_btn = QPushButton("Pick…")
        pick_btn.setFixedWidth(70)
        pick_btn.clicked.connect(self._pick_color_for_edit)

        update_btn = QPushButton("Update")
        update_btn.setFixedWidth(80)
        update_btn.clicked.connect(self._update_color)

        delete_btn = QPushButton("Delete")
        delete_btn.setFixedWidth(80)
        delete_btn.clicked.connect(self._delete_color)

        add_btn = QPushButton("+ Add")
        add_btn.setFixedWidth(80)
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

        # ── Selection border color ──
        grp_sel = QGroupBox("Warna Garis Seleksi")
        vsel = QVBoxLayout(grp_sel); vsel.setSpacing(6)
        sel_row = QHBoxLayout()
        self._sel_color = self.config.get('selection_color', '#f5cb11')
        self._sel_color_btn = QPushButton()
        self._sel_color_btn.setFixedSize(36, 36)
        self._sel_color_btn.setStyleSheet(
            f"background:{self._sel_color}; border:1px solid #555; border-radius:4px;")
        self._sel_color_btn.clicked.connect(self._pick_selection_color)
        self._sel_color_lbl = QLabel(self._sel_color)
        self._sel_color_lbl.setStyleSheet("color:#c0c0f0; font-family:monospace;")
        sel_hint = QLabel("Warna border kotak seleksi dan handle pojok")
        sel_hint.setStyleSheet("color:#9999bb; font-size:11px;")
        sel_hint.setWordWrap(True)
        sel_row.addWidget(self._sel_color_btn)
        sel_row.addWidget(self._sel_color_lbl)
        sel_row.addStretch()
        vsel.addWidget(sel_hint)
        vsel.addLayout(sel_row)
        lay.addWidget(grp_sel)

        # ── Toolbar colors ──
        grp_tb_clr = QGroupBox("Warna Tombol Toolbar")
        vtbc = QVBoxLayout(grp_tb_clr); vtbc.setSpacing(6)
        tbc_hint = QLabel("Background dan warna icon pada tombol-tombol toolbar.")
        tbc_hint.setWordWrap(True)
        tbc_hint.setStyleSheet("color:#9999bb; font-size:11px;")
        vtbc.addWidget(tbc_hint)

        self._tb_bg_color   = self.config.get('toolbar_bg_color',   '#000a52')
        self._tb_icon_color = self.config.get('toolbar_icon_color',  '#f5cb11')

        tbc_row = QHBoxLayout(); tbc_row.setSpacing(12)
        # Background color
        bg_col = QVBoxLayout()
        bg_lbl = QLabel("Background"); bg_lbl.setStyleSheet("color:#c0c0f0;font-size:11px;")
        self._tb_bg_btn = QPushButton()
        self._tb_bg_btn.setFixedSize(36, 36)
        self._tb_bg_btn.setStyleSheet(
            f"background:{self._tb_bg_color}; border:1px solid #555; border-radius:4px;")
        self._tb_bg_btn.clicked.connect(self._pick_toolbar_bg)
        bg_col.addWidget(bg_lbl, 0, Qt.AlignCenter)
        bg_col.addWidget(self._tb_bg_btn, 0, Qt.AlignCenter)
        # Icon color
        ic_col = QVBoxLayout()
        ic_lbl = QLabel("Icon / Teks"); ic_lbl.setStyleSheet("color:#c0c0f0;font-size:11px;")
        self._tb_icon_btn = QPushButton()
        self._tb_icon_btn.setFixedSize(36, 36)
        self._tb_icon_btn.setStyleSheet(
            f"background:{self._tb_icon_color}; border:1px solid #555; border-radius:4px;")
        self._tb_icon_btn.clicked.connect(self._pick_toolbar_icon)
        ic_col.addWidget(ic_lbl, 0, Qt.AlignCenter)
        ic_col.addWidget(self._tb_icon_btn, 0, Qt.AlignCenter)

        tbc_row.addLayout(bg_col)
        tbc_row.addLayout(ic_col)
        tbc_row.addStretch()
        vtbc.addLayout(tbc_row)

        # Live preview
        self._tb_preview = QLabel("Aa  ↗  ✏")
        self._tb_preview.setAlignment(Qt.AlignCenter)
        self._update_toolbar_preview()
        vtbc.addWidget(self._tb_preview)
        lay.addWidget(grp_tb_clr)

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
        hint_tb.setStyleSheet("color:#9999bb; font-size:11px;")
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
            cb.setStyleSheet("color:#d0d0f0; font-size:12px;")
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
            if item.widget(): item.widget().deleteLater()
        self._color_btns.clear()

        cols = 8
        for i, hex_c in enumerate(self._color_presets):
            btn = QPushButton()
            btn.setFixedSize(32, 32)
            btn.setToolTip(hex_c)
            border = "3px solid #ffffff" if i == self._selected_color_idx else "1px solid #555"
            btn.setStyleSheet(
                f"background:{hex_c};border:{border};border-radius:16px;padding:0px;")
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
        lbl.setStyleSheet("color:#ccc; font-size:13px;")
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
        hint.setStyleSheet("color:#9999bb; font-size:12px;")
        lay.addWidget(hint)

        # ── Configurable global hotkeys ──
        self._shortcut_defs = [
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
            "border-radius:4px; padding:3px 10px; font-family:monospace; font-size:12px;")
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
                "border-radius:4px; padding:3px 10px; font-family:monospace; font-size:12px;")
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
            self, "Export Config", "xenshoot_config.json", "JSON (*.json)")
        if path:
            try:
                with open(path, 'w') as f:
                    json.dump(self.config.config, f, indent=4)
                QMessageBox.information(self, "XenShoot", f"Config exported to:\n{path}")
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
                QMessageBox.information(self, "XenShoot", "Config imported.")
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))

    def _reset_config(self):
        r = QMessageBox.question(self, "Reset Config",
            "Reset semua settings ke default?",
            QMessageBox.Yes | QMessageBox.No)
        if r == QMessageBox.Yes:
            defaults = self.config.default_config()
            for k, v in defaults.items():
                self.config.set(k, v)
            self._load_settings()
