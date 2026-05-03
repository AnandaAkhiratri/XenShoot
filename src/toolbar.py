"""
Toolbar – 3-zone responsive layout with wrapping.

  top   : all action buttons (above selection, wraps to fit selection width)
  right : utility/nav buttons (vertical column, right of selection)
  bot   : drawing tool buttons (below selection, wraps to fit selection width)
"""

from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
                             QLabel, QLayout, QSizePolicy, QColorDialog,
                             QGridLayout, QApplication)
from PyQt5.QtCore import Qt, QSize, QRect, QPoint, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QPen, QFont, QPainterPath, QIcon, QPixmap, QBrush
from .annotation_tools import ToolType


# ──────────────────────────────────────────────────────────────────────────────
# FlowLayout – standard wrapping layout for PyQt5
# ──────────────────────────────────────────────────────────────────────────────

class FlowLayout(QLayout):
    """Horizontal flow layout — wraps to next row, each row center-aligned."""

    def __init__(self, parent=None, h_spacing=4, v_spacing=4):
        super().__init__(parent)
        self._items = []
        self._h = h_spacing
        self._v = v_spacing

    def __del__(self):
        while self.count():
            self.takeAt(0)

    def addItem(self, item):       self._items.append(item)
    def count(self):               return len(self._items)
    def itemAt(self, i):           return self._items[i] if 0 <= i < len(self._items) else None
    def takeAt(self, i):           return self._items.pop(i) if 0 <= i < len(self._items) else None
    def expandingDirections(self): return Qt.Orientations(Qt.Orientation(0))
    def hasHeightForWidth(self):   return True

    def heightForWidth(self, width):
        return self._calc_height(width)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._place(rect)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        """Return single-item minimum so Qt doesn't enforce a fully-wrapped height."""
        visible = self._visible_items()
        if not visible:
            return QSize(0, 0)
        m = self.contentsMargins()
        w = max(i.sizeHint().width() for i in visible) + m.left() + m.right()
        h = max(i.sizeHint().height() for i in visible) + m.top() + m.bottom()
        return QSize(w, h)

    def _visible_items(self):
        """Return only items whose widget is visible."""
        result = []
        for item in self._items:
            w = item.widget()
            if w is None or w.isVisible():
                result.append(item)
        return result

    def _group_rows(self, eff_w):
        """Return list of rows; each row is list of (item, sizeHint). Skips hidden items."""
        rows, row, row_w = [], [], 0
        for item in self._visible_items():
            sh = item.sizeHint()
            gap = self._h if row else 0
            if row_w + gap + sh.width() > eff_w and row:
                rows.append(row)
                row, row_w = [(item, sh)], sh.width()
            else:
                row.append((item, sh))
                row_w += gap + sh.width()
        if row:
            rows.append(row)
        return rows

    def _calc_height(self, width):
        m = self.contentsMargins()
        eff_w = width - m.left() - m.right()
        rows = self._group_rows(eff_w)
        if not rows:
            return m.top() + m.bottom()
        h = m.top() + m.bottom()
        for i, row in enumerate(rows):
            h += max(sh.height() for _, sh in row)
            if i < len(rows) - 1:
                h += self._v
        return h

    def _place(self, rect):
        m = self.contentsMargins()
        eff = rect.adjusted(m.left(), m.top(), -m.right(), -m.bottom())
        rows = self._group_rows(eff.width())
        y = eff.y()
        for row in rows:
            row_w = sum(sh.width() for _, sh in row) + self._h * max(0, len(row) - 1)
            row_h = max(sh.height() for _, sh in row)
            # Center this row within the available width
            x = eff.x() + max(0, (eff.width() - row_w) // 2)
            for item, sh in row:
                item.setGeometry(QRect(QPoint(x, y), sh))
                x += sh.width() + self._h
            y += row_h + self._v


class VFlowLayout(QLayout):
    """Vertical flow layout — wraps to next column when height exceeded."""

    def __init__(self, parent=None, h_spacing=4, v_spacing=4):
        super().__init__(parent)
        self._items = []
        self._h = h_spacing
        self._v = v_spacing

    def __del__(self):
        while self.count():
            self.takeAt(0)

    def addItem(self, item):       self._items.append(item)
    def count(self):               return len(self._items)
    def itemAt(self, i):           return self._items[i] if 0 <= i < len(self._items) else None
    def takeAt(self, i):           return self._items.pop(i) if 0 <= i < len(self._items) else None
    def expandingDirections(self): return Qt.Orientations(Qt.Orientation(0))
    def hasHeightForWidth(self):   return False

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._place(rect)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        """Return single-item minimum so Qt doesn't enforce a fully-wrapped width."""
        if not self._items:
            return QSize(0, 0)
        m = self.contentsMargins()
        w = max(i.sizeHint().width() for i in self._items) + m.left() + m.right()
        h = max(i.sizeHint().height() for i in self._items) + m.top() + m.bottom()
        return QSize(w, h)

    def width_for_height(self, max_h):
        m = self.contentsMargins()
        eff_h = max_h - m.top() - m.bottom()
        cols = self._group_cols(eff_h)
        if not cols:
            return m.left() + m.right()
        w = m.left() + m.right()
        for i, col in enumerate(cols):
            w += max(sh.width() for _, sh in col)
            if i < len(cols) - 1:
                w += self._h
        return w

    def _group_cols(self, eff_h):
        cols, col, col_h = [], [], 0
        for item in self._items:
            sh = item.sizeHint()
            gap = self._v if col else 0
            if col_h + gap + sh.height() > eff_h and col:
                cols.append(col)
                col, col_h = [(item, sh)], sh.height()
            else:
                col.append((item, sh))
                col_h += gap + sh.height()
        if col:
            cols.append(col)
        return cols

    def _place(self, rect):
        m = self.contentsMargins()
        eff = rect.adjusted(m.left(), m.top(), -m.right(), -m.bottom())
        cols = self._group_cols(eff.height())
        x = eff.x()
        for col in cols:
            col_w = max(sh.width() for _, sh in col)
            col_h = sum(sh.height() for _, sh in col) + self._v * max(0, len(col) - 1)
            # Center column vertically
            y = eff.y() + max(0, (eff.height() - col_h) // 2)
            for item, sh in col:
                item.setGeometry(QRect(QPoint(x, y), sh))
                y += sh.height() + self._v
            x += col_w + self._h


# ──────────────────────────────────────────────────────────────────────────────
# Styles
# ──────────────────────────────────────────────────────────────────────────────

def _make_btn_style(bg_hex='#000a52', icon_hex='#f5cb11'):
    """Generate toolbar button stylesheet from configurable colors."""
    c = QColor(bg_hex)
    # Derive hover (slightly lighter) and pressed (darker) from bg
    hover = QColor(min(c.red()+15, 255), min(c.green()+15, 255), min(c.blue()+30, 255))
    checked = QColor(max(c.red()-5, 0), max(c.green()-5, 0), max(c.blue()-15, 0))
    pressed = QColor(max(c.red()-8, 0), max(c.green()-8, 0), max(c.blue()-35, 0))
    return f"""
    QWidget {{ background-color: transparent; }}
    QPushButton {{
        background-color: {bg_hex};
        color: {icon_hex};
        border: none; border-radius: 18px;
        min-width: 36px; min-height: 36px;
        max-width: 36px; max-height: 36px;
        font-size: 17px; font-weight: normal;
        font-family: "Segoe UI Symbol", "Segoe UI", "Arial Unicode MS", sans-serif;
        padding: 0px;
    }}
    QPushButton:hover   {{ background-color: {hover.name()}; }}
    QPushButton:checked {{ background-color: {checked.name()};
                           border: 2px solid {icon_hex}; }}
    QPushButton:pressed {{ background-color: {pressed.name()}; }}
"""

def _make_label_style(bg_hex='#000a52', icon_hex='#f5cb11'):
    return f"""
    QLabel {{
        color: {icon_hex};
        background-color: {bg_hex};
        border-radius: 14px;
        font-size: 13px; font-weight: bold;
        min-height: 36px; max-height: 36px;
        min-width: 28px; max-width: 28px;
        padding: 0px;
    }}
"""

_BTN_STYLE   = _make_btn_style()
_LABEL_STYLE = _make_label_style()


# ──────────────────────────────────────────────────────────────────────────────
# _Bar widget
# ──────────────────────────────────────────────────────────────────────────────

class _Bar(QWidget):
    """Floating button cluster.
    flow=True  → FlowLayout (horizontal wrap, center-aligned rows)
    vflow=True → VFlowLayout (vertical wrap to next column)
    vertical=True → QVBoxLayout
    """

    def __init__(self, parent, vertical=False, flow=False, vflow=False, style=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setStyleSheet(style if style else _BTN_STYLE)
        if flow:
            layout = FlowLayout(h_spacing=4, v_spacing=4)
            layout.setContentsMargins(4, 4, 4, 4)
        elif vflow:
            layout = VFlowLayout(h_spacing=4, v_spacing=4)
            layout.setContentsMargins(4, 4, 4, 4)
        elif vertical:
            layout = QVBoxLayout()
            layout.setSpacing(4)
            layout.setContentsMargins(4, 4, 4, 4)
        else:
            layout = QHBoxLayout()
            layout.setSpacing(4)
            layout.setContentsMargins(4, 4, 4, 4)
        self.setLayout(layout)

    def add_button(self, icon=None, text=None, tooltip="",
                   checkable=False, callback=None):
        btn = QPushButton()
        if icon:
            btn.setIcon(icon)
            btn.setIconSize(QSize(28, 28))
        if text:
            btn.setText(text)
        btn.setToolTip(tooltip)
        btn.setCheckable(checkable)
        if callback:
            btn.clicked.connect(callback)
        self.layout().addWidget(btn)
        return btn

    def add_label(self, text, label_style=None):
        lbl = QLabel(text)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet(label_style if label_style else _LABEL_STYLE)
        self.layout().addWidget(lbl)
        return lbl

    def set_max_w(self, max_w):
        """Resize this bar to at most max_w wide, letting FlowLayout wrap."""
        lo = self.layout()
        if isinstance(lo, FlowLayout):
            h = lo.heightForWidth(max_w)
            self.setMinimumSize(0, 0)   # allow Qt to resize below sizeHint
            self.resize(max_w, h)
            lo.setGeometry(QRect(0, 0, max_w, h))
        else:
            self.adjustSize()

    def set_max_h(self, max_h):
        """Resize this bar to at most max_h tall, letting VFlowLayout wrap to columns."""
        lo = self.layout()
        if isinstance(lo, VFlowLayout):
            w = lo.width_for_height(max_h)
            self.setMinimumSize(0, 0)   # allow Qt to resize below sizeHint
            self.resize(w, max_h)
            lo.setGeometry(QRect(0, 0, w, max_h))
        else:
            self.adjustSize()


# ──────────────────────────────────────────────────────────────────────────────
# Color palette popup
# ──────────────────────────────────────────────────────────────────────────────

class _ColorPopup(QWidget):
    color_picked = pyqtSignal(str)

    def __init__(self, presets, parent=None):
        super().__init__(parent, Qt.Popup | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._presets = presets
        self._build()

    def _build(self):
        self.setStyleSheet("""
            QWidget#popup_bg {
                background:#1a1a2e; border:1px solid #4040a0; border-radius:6px;
            }
            QPushButton.swatch {
                border:1px solid #555; border-radius:4px;
            }
            QPushButton.swatch:hover { border:2px solid #ffffff; }
            QPushButton#custom_btn {
                background:#2a2a48; color:#c0c0f0;
                border:1px solid #4a4a80; border-radius:4px;
                padding:4px; font-size:12px;
            }
            QPushButton#custom_btn:hover { background:#3a3a60; }
        """)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        bg = QWidget(self)
        bg.setObjectName("popup_bg")
        main_lay = QVBoxLayout(bg)
        main_lay.setContentsMargins(8, 8, 8, 8)
        main_lay.setSpacing(6)

        grid = QGridLayout()
        grid.setSpacing(5)
        cols = 4
        for i, hex_c in enumerate(self._presets):
            btn = QPushButton()
            btn.setFixedSize(28, 28)
            btn.setProperty("class", "swatch")
            btn.setStyleSheet(
                f"background:{hex_c}; border:1px solid #555; border-radius:4px;")
            btn.setToolTip(hex_c)
            btn.clicked.connect(lambda _, hc=hex_c: self._emit(hc))
            grid.addWidget(btn, i // cols, i % cols)
        main_lay.addLayout(grid)

        custom_btn = QPushButton("＋ Custom")
        custom_btn.setObjectName("custom_btn")
        custom_btn.clicked.connect(self._pick_custom)
        main_lay.addWidget(custom_btn)

        outer.addWidget(bg)
        self.adjustSize()

    def _emit(self, hex_color):
        self.color_picked.emit(hex_color)
        self.close()

    def _pick_custom(self):
        from PyQt5.QtCore import QTimer
        self.hide()
        # Delay to let popup fully dismiss before opening dialog (avoid z-order issue)
        QTimer.singleShot(50, self._open_color_dialog)

    def _open_color_dialog(self):
        # Use a top-level dialog so it appears above the overlay
        dlg = QColorDialog(QColor("#f5cb11"))
        dlg.setWindowTitle("Pilih Warna")
        dlg.setWindowFlags(dlg.windowFlags() | Qt.WindowStaysOnTopHint)
        if dlg.exec_():
            c = dlg.selectedColor()
            if c.isValid():
                self.color_picked.emit(c.name())


# ──────────────────────────────────────────────────────────────────────────────
# Toolbar coordinator
# ──────────────────────────────────────────────────────────────────────────────

class Toolbar:
    """
    3-zone responsive toolbar:
      top   – above selection (flow/wrap, constrained to selection width)
      right – right of selection (vertical)
      bot   – below selection (flow/wrap, constrained to selection width)
    """

    def __init__(self, parent, annotation_manager):
        self.annotation_manager = annotation_manager
        self.parent_overlay = parent
        self.tools = {}
        self.move_btn = None
        self.thickness_label = None
        self.bars = {}
        self.action_btns = {}   # name -> QPushButton for non-tool buttons
        self._build()
        self._apply_hidden_buttons()

    # ── build ──────────────────────────────────────────────────────────────

    def _build(self):
        p = self.parent_overlay

        # Build stylesheet from config
        cfg = getattr(p, 'config', None)
        bg_hex   = cfg.get('toolbar_bg_color',   '#000a52') if cfg else '#000a52'
        icon_hex = cfg.get('toolbar_icon_color',  '#f5cb11') if cfg else '#f5cb11'
        self._btn_style    = _make_btn_style(bg_hex, icon_hex)
        self._label_style  = _make_label_style(bg_hex, icon_hex)
        self._icon_color   = QColor(icon_hex)
        self._bg_color_q   = QColor(bg_hex)

        # ── TOP (flow) ─────────────────────────────────────────────────────
        top = _Bar(p, flow=True, style=self._btn_style)
        top.add_button(icon=self._ico_minus(), tooltip="Decrease thickness",
                       callback=self.decrease_thickness)
        self.thickness_label = top.add_label("3", label_style=self._label_style)
        top.add_button(icon=self._ico_plus(), tooltip="Increase thickness",
                       callback=self.increase_thickness)
        self.action_btns['pin'] = top.add_button(
            text="📌", tooltip="Pin to Screen", callback=self.pin_to_screen)
        self.action_btns['save_upload'] = top.add_button(
            icon=self._ico_open_app(), tooltip="Save & Upload (Enter)", callback=self.save)
        self.action_btns['exit'] = top.add_button(
            icon=self._ico_exit(), tooltip="Exit (Esc)", callback=self.cancel)
        self.action_btns['save_local'] = top.add_button(
            icon=self._ico_save(), tooltip="Save to Local", callback=self.save_local_only)
        self.action_btns['copy_clipboard'] = top.add_button(
            icon=self._ico_copy(), tooltip="Copy to Clipboard", callback=self.copy_to_clipboard)
        self.bars['top'] = top

        # ── RIGHT (vertical) ───────────────────────────────────────────────
        right = _Bar(p, vflow=True, style=self._btn_style)
        self.action_btns['undo'] = right.add_button(
            icon=self._ico_undo(), tooltip="Undo (Ctrl+Z)", callback=self.undo)
        self.action_btns['redo'] = right.add_button(
            icon=self._ico_redo(), tooltip="Redo (Ctrl+Y)", callback=self.redo)
        self.move_btn = right.add_button(icon=self._ico_move(),
                                         tooltip="Move selection area",
                                         callback=self.toggle_move_mode)
        for ttype, icon, tip, name in [
            (ToolType.NUMBER, self._ico_number(), "Number (N)", 'number'),
            (ToolType.BLUR,   self._ico_blur(),   "Blur (B)",   'blur'),
            (ToolType.INVERT, self._ico_invert(), "Invert (I)", 'invert'),
        ]:
            btn = right.add_button(icon=icon, tooltip=tip, checkable=True,
                                   callback=lambda c, t=ttype: self.select_tool(t))
            self.tools[ttype] = btn
            self.action_btns[name] = btn
        self.bars['right'] = right

        # ── BOT (flow) ─────────────────────────────────────────────────────
        bot = _Bar(p, flow=True, style=self._btn_style)
        for ttype, icon, tip, name in [
            (ToolType.PEN,              self._ico_pen(),         "Pencil (P)",  'pen'),
            (ToolType.LINE,             self._ico_line(),        "Line (L)",    'line'),
            (ToolType.ARROW,            self._ico_arrow(),       "Arrow (A)",   'arrow'),
            (ToolType.RECTANGLE,        self._ico_rect(),        "Rectangle (R)",'rectangle'),
            (ToolType.CIRCLE,           self._ico_circle(),      "Circle (C)",  'circle'),
            (ToolType.RECTANGLE_FILLED, self._ico_filled_rect(), "Filled box",  'filled_rect'),
            (ToolType.HIGHLIGHTER,      self._ico_highlighter(), "Highlighter (M)", 'highlighter'),
            (ToolType.TEXT,             self._ico_text(),        "Text (T)",    'text'),
        ]:
            btn = bot.add_button(icon=icon, tooltip=tip, checkable=True,
                                 callback=lambda c, t=ttype: self.select_tool(t))
            self.tools[ttype] = btn
            self.action_btns[name] = btn
        # Color picker button
        self.color_btn = QPushButton()
        self.color_btn.setToolTip("Pick annotation color")
        self.color_btn.setFixedSize(36, 36)
        self._update_color_btn()
        self.color_btn.clicked.connect(self._show_color_popup)
        bot.layout().addWidget(self.color_btn)
        self.action_btns['color_picker'] = self.color_btn
        self.bars['bot'] = bot

        self.select_tool(ToolType.PEN)

    def _apply_hidden_buttons(self):
        """Hide buttons listed in config hidden_buttons."""
        hidden = set()
        if hasattr(self.parent_overlay, 'config'):
            hidden = set(self.parent_overlay.config.get('hidden_buttons', []))
        for name, btn in self.action_btns.items():
            btn.setVisible(name not in hidden)

    # ── visibility ─────────────────────────────────────────────────────────

    def show(self):
        for b in self.bars.values(): b.show()

    def hide(self):
        for b in self.bars.values(): b.hide()

    def close(self):
        for b in self.bars.values(): b.close()

    def adjustSize(self):
        for b in self.bars.values(): b.adjustSize()

    def updateGeometry(self): pass
    def width(self):  return self.bars['bot'].width()
    def height(self): return self.bars['bot'].height()
    def move(self, x, y): pass

    # ── handlers ───────────────────────────────────────────────────────────

    def select_tool(self, tool_type):
        # Commit any pending text before switching tools
        if hasattr(self.parent_overlay, '_commit_pending_text'):
            self.parent_overlay._commit_pending_text()
        for btn in self.tools.values(): btn.setChecked(False)
        if tool_type in self.tools: self.tools[tool_type].setChecked(True)
        self.annotation_manager.set_tool(tool_type)
        # Update label to show relevant size for the selected tool
        from .annotation_tools import ToolType
        if tool_type == ToolType.TEXT:
            self.thickness_label.setText(str(self.annotation_manager.text_font_size))
        else:
            self.thickness_label.setText(str(self.annotation_manager.current_thickness))

    def _is_text_tool(self):
        from .annotation_tools import ToolType
        return self.annotation_manager.current_tool == ToolType.TEXT

    def decrease_thickness(self):
        if self._is_text_tool():
            v = max(8, self.annotation_manager.text_font_size - 4)
            self.annotation_manager.text_font_size = v
            self.thickness_label.setText(str(v))
            # Update live preview font size if text input is active
            if hasattr(self.parent_overlay, 'text_active') and self.parent_overlay.text_active:
                self.parent_overlay.update()
        else:
            v = max(1, self.annotation_manager.current_thickness - 1)
            self.annotation_manager.set_thickness(v)
            self.thickness_label.setText(str(v))

    def increase_thickness(self):
        if self._is_text_tool():
            v = min(120, self.annotation_manager.text_font_size + 4)
            self.annotation_manager.text_font_size = v
            self.thickness_label.setText(str(v))
            # Update live preview font size if text input is active
            if hasattr(self.parent_overlay, 'text_active') and self.parent_overlay.text_active:
                self.parent_overlay.update()
        else:
            v = min(30, self.annotation_manager.current_thickness + 1)
            self.annotation_manager.set_thickness(v)
            self.thickness_label.setText(str(v))

    def change_thickness(self, value): self.annotation_manager.set_thickness(value)

    def _update_color_btn(self):
        """Refresh the color button to reflect current annotation color."""
        c = self.annotation_manager.current_color
        px = QPixmap(26, 26); px.fill(c)
        self.color_btn.setIcon(QIcon(px))
        self.color_btn.setIconSize(QSize(26, 26))
        self.color_btn.setStyleSheet(
            f"background:{c.name()}; border:2px solid #fff;"
            "border-radius:5px; padding:0px;")

    def _show_color_popup(self):
        """Show a floating color palette popup."""
        presets = []
        if hasattr(self.parent_overlay, 'config'):
            presets = self.parent_overlay.config.get('color_presets', [])
        if not presets:
            presets = ['#f5cb11','#ff4444','#ff8800','#44cc44',
                       '#4488ff','#cc44ff','#ffffff','#000000']

        # Keep reference so Python GC doesn't destroy it before user clicks
        self._color_popup = _ColorPopup(presets, self.parent_overlay)
        self._color_popup.color_picked.connect(self._apply_color)

        btn_global = self.color_btn.mapToGlobal(self.color_btn.rect().bottomLeft())
        self._color_popup.move(btn_global)
        self._color_popup.show()
        self._color_popup.raise_()

    def _apply_color(self, hex_color):
        self.annotation_manager.set_color(QColor(hex_color))
        self._update_color_btn()

    def undo(self):
        self.annotation_manager.undo()
        self.parent_overlay.update()

    def redo(self):
        self.annotation_manager.redo()
        self.parent_overlay.update()

    def copy_to_clipboard(self):
        if hasattr(self.parent_overlay, 'copy_to_clipboard'):
            self.parent_overlay.copy_to_clipboard()

    def pin_to_screen(self):
        if hasattr(self.parent_overlay, 'pin_to_screen'):
            self.parent_overlay.pin_to_screen()

    def toggle_move_mode(self):
        if hasattr(self.parent_overlay, 'toggle_move_mode'):
            self.parent_overlay.toggle_move_mode()

    def open_with_app(self):
        if hasattr(self.parent_overlay, 'open_with_app'):
            self.parent_overlay.open_with_app()

    def save(self):
        print("[TOOLBAR] save clicked")
        self.parent_overlay.finish_capture()
    def save_local_only(self):
        print("[TOOLBAR] save_local_only clicked")
        self.parent_overlay.save_to_local_only()
    def cancel(self):          self.parent_overlay.cancel_capture()

    # ── icons ──────────────────────────────────────────────────────────────

    def _ico_pen(self):
        from PyQt5.QtCore import QPointF
        from PyQt5.QtGui import QPolygonF
        px = QPixmap(32, 32); px.fill(Qt.transparent)
        p = QPainter(px); p.setRenderHint(QPainter.Antialiasing)
        p.translate(5, 5); p.setPen(Qt.NoPen); p.setBrush(self._icon_color)
        p.drawPolygon(QPolygonF([QPointF(3,18),QPointF(15,6),QPointF(18,9),
                                  QPointF(6,21),QPointF(3,21)]))
        p.drawPolygon(QPolygonF([QPointF(16,5),QPointF(18,3),
                                  QPointF(21,6),QPointF(19,8)]))
        p.end(); return QIcon(px)

    def _ico_line(self):
        px = QPixmap(24,24); px.fill(Qt.transparent)
        p = QPainter(px); p.setRenderHint(QPainter.Antialiasing)
        p.setPen(QPen(self._icon_color,2)); p.drawLine(4,20,20,4)
        p.end(); return QIcon(px)

    def _ico_arrow(self):
        px = QPixmap(24,24); px.fill(Qt.transparent)
        p = QPainter(px); p.setRenderHint(QPainter.Antialiasing)
        p.setPen(QPen(self._icon_color,2))
        p.drawLine(4,20,20,4); p.drawLine(20,4,14,6); p.drawLine(20,4,18,10)
        p.end(); return QIcon(px)

    def _ico_rect(self):
        px = QPixmap(24,24); px.fill(Qt.transparent)
        p = QPainter(px); p.setRenderHint(QPainter.Antialiasing)
        p.setPen(QPen(self._icon_color,2)); p.setBrush(Qt.NoBrush)
        p.drawRect(5,5,14,14); p.end(); return QIcon(px)

    def _ico_filled_rect(self):
        px = QPixmap(24,24); px.fill(Qt.transparent)
        p = QPainter(px); p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(self._icon_color); p.setPen(QPen(self._icon_color,2))
        p.drawRect(5,5,14,14); p.end(); return QIcon(px)

    def _ico_circle(self):
        px = QPixmap(24,24); px.fill(Qt.transparent)
        p = QPainter(px); p.setRenderHint(QPainter.Antialiasing)
        p.setPen(QPen(self._icon_color,2)); p.drawEllipse(4,4,16,16)
        p.end(); return QIcon(px)

    def _ico_highlighter(self):
        px = QPixmap(24,24); px.fill(Qt.transparent)
        p = QPainter(px); p.setRenderHint(QPainter.Antialiasing)
        pen = QPen(self._icon_color,5); pen.setCapStyle(Qt.RoundCap)
        p.setPen(pen); p.drawLine(4,12,20,12); p.end(); return QIcon(px)

    def _ico_text(self):
        px = QPixmap(24,24); px.fill(Qt.transparent)
        p = QPainter(px); p.setRenderHint(QPainter.Antialiasing)
        p.setFont(QFont("Arial",16,QFont.Bold)); p.setPen(self._icon_color)
        p.drawText(px.rect(), Qt.AlignCenter, "T"); p.end(); return QIcon(px)

    def _ico_number(self):
        px = QPixmap(32,32); px.fill(Qt.transparent)
        p = QPainter(px); p.setRenderHint(QPainter.Antialiasing); p.translate(4,4)
        p.setPen(QPen(self._icon_color,2.5,Qt.SolidLine,Qt.RoundCap,Qt.RoundJoin))
        p.setBrush(Qt.NoBrush); p.drawEllipse(3,3,18,18)
        p.drawLine(12,17,12,7); p.drawLine(12,7,10,9); p.end(); return QIcon(px)

    def _ico_blur(self):
        px = QPixmap(24,24); px.fill(Qt.transparent)
        p = QPainter(px); p.setPen(Qt.NoPen); p.setBrush(self._icon_color)
        for i in range(3):
            for j in range(3): p.drawRect(5+i*5,5+j*5,3,3)
        p.end(); return QIcon(px)

    def _ico_invert(self):
        px = QPixmap(32,32); px.fill(Qt.transparent)
        p = QPainter(px); p.setRenderHint(QPainter.Antialiasing)
        p.translate(2,2); p.scale(1.17,1.17); yellow = self._icon_color
        path = QPainterPath()
        path.moveTo(12,2); path.quadTo(4,8,4,13.75); path.quadTo(4,22,12,22)
        path.quadTo(20,22,20,13.75); path.quadTo(20,8,12,2); path.closeSubpath()
        p.setPen(QPen(yellow,1.5,Qt.SolidLine,Qt.RoundCap,Qt.RoundJoin))
        p.setBrush(Qt.NoBrush); p.drawPath(path)
        half = QPainterPath()
        half.moveTo(12,4.26); half.quadTo(6,8,6,13.75); half.quadTo(6,20,12,20)
        half.lineTo(12,4.26); half.closeSubpath()
        p.setPen(Qt.NoPen); p.setBrush(QBrush(yellow)); p.drawPath(half)
        p.end(); return QIcon(px)

    def _ico_undo(self):
        px = QPixmap(32,32); px.fill(Qt.transparent)
        p = QPainter(px); p.setRenderHint(QPainter.Antialiasing)
        p.translate(32,0); p.scale(-1,1); p.translate(4,4)
        p.setPen(QPen(self._icon_color,2,Qt.SolidLine,Qt.RoundCap,Qt.RoundJoin))
        p.setBrush(Qt.NoBrush)
        path = QPainterPath()
        path.moveTo(20,7); path.lineTo(10,7); path.cubicTo(6,7,4,9,4,13)
        path.cubicTo(4,17,6,19,10,19); path.lineTo(20,19)
        p.drawPath(path); p.drawLine(20,7,16,3); p.drawLine(20,7,16,11)
        p.end(); return QIcon(px)

    def _ico_redo(self):
        px = QPixmap(32,32); px.fill(Qt.transparent)
        p = QPainter(px); p.setRenderHint(QPainter.Antialiasing); p.translate(4,4)
        p.setPen(QPen(self._icon_color,2,Qt.SolidLine,Qt.RoundCap,Qt.RoundJoin))
        p.setBrush(Qt.NoBrush)
        path = QPainterPath()
        path.moveTo(20,7); path.lineTo(10,7); path.cubicTo(6,7,4,9,4,13)
        path.cubicTo(4,17,6,19,10,19); path.lineTo(20,19)
        p.drawPath(path); p.drawLine(20,7,16,3); p.drawLine(20,7,16,11)
        p.end(); return QIcon(px)

    def _ico_move(self):
        px = QPixmap(32,32); px.fill(Qt.transparent)
        p = QPainter(px); p.setRenderHint(QPainter.Antialiasing)
        p.setPen(QPen(self._icon_color,2,Qt.SolidLine,Qt.RoundCap,Qt.RoundJoin))
        c,al,ah = 16,8,3
        for dx,dy in [(0,-1),(0,1),(-1,0),(1,0)]:
            ex,ey = c+dx*al,c+dy*al; p.drawLine(c,c,ex,ey)
            if dx==0: p.drawLine(ex,ey,ex-ah,ey-dy*ah); p.drawLine(ex,ey,ex+ah,ey-dy*ah)
            else:     p.drawLine(ex,ey,ex-dx*ah,ey-ah); p.drawLine(ex,ey,ex-dx*ah,ey+ah)
        p.end(); return QIcon(px)

    def _ico_save(self):
        from PyQt5.QtCore import QRectF
        px = QPixmap(32,32); px.fill(Qt.transparent)
        p = QPainter(px); p.setRenderHint(QPainter.Antialiasing)
        p.translate(2,2); p.scale(1.17,1.17)
        p.setPen(Qt.NoPen); p.setBrush(QBrush(self._icon_color))
        path = QPainterPath()
        path.moveTo(17,3); path.lineTo(5,3); path.cubicTo(3.89,3,3,3.9,3,5)
        path.lineTo(3,19); path.cubicTo(3,20.1,3.89,21,5,21); path.lineTo(19,21)
        path.cubicTo(20.1,21,21,20.1,21,19); path.lineTo(21,7); path.lineTo(17,3)
        path.closeSubpath(); path.addEllipse(QRectF(9,13,6,6))
        path.moveTo(15,9); path.lineTo(5,9); path.lineTo(5,5); path.lineTo(15,5)
        path.lineTo(15,9); path.closeSubpath(); p.drawPath(path); p.end(); return QIcon(px)

    def _ico_copy(self):
        from PyQt5.QtCore import QRectF
        px = QPixmap(32,32); px.fill(Qt.transparent)
        p = QPainter(px); p.setRenderHint(QPainter.Antialiasing)
        y = self._icon_color
        p.setPen(QPen(y,2)); p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(QRectF(10,10,14,16),1,1)
        p.setBrush(QBrush(y)); p.setPen(QPen(y,2))
        p.drawRoundedRect(QRectF(8,6,14,16),1,1)
        p.setPen(QPen(self._bg_color_q,1.5))
        p.drawLine(10,10,20,10); p.drawLine(10,13,20,13); p.drawLine(10,16,17,16)
        p.end(); return QIcon(px)

    def _ico_exit(self):
        from PyQt5.QtCore import QPointF
        px = QPixmap(32,32); px.fill(Qt.transparent)
        p = QPainter(px); p.setRenderHint(QPainter.Antialiasing)
        p.setPen(QPen(self._icon_color,3,Qt.SolidLine,Qt.RoundCap,Qt.RoundJoin))
        p.drawLine(QPointF(8,8),QPointF(24,24)); p.drawLine(QPointF(24,8),QPointF(8,24))
        p.end(); return QIcon(px)

    def _ico_open_app(self):
        from PyQt5.QtCore import QRectF, QPointF
        px = QPixmap(32,32); px.fill(Qt.transparent)
        p = QPainter(px); p.setRenderHint(QPainter.Antialiasing)
        p.translate(2,2); p.scale(1.17,1.17)
        y = self._icon_color
        p.setPen(QPen(y,1.5,Qt.SolidLine,Qt.RoundCap,Qt.RoundJoin)); p.setBrush(Qt.NoBrush)
        from PyQt5.QtCore import QRectF
        p.drawRoundedRect(QRectF(3,3.5,18,13),2,2)
        p.drawLine(QPointF(12,16.5),QPointF(12,20.5))
        p.drawLine(QPointF(8,20.5),QPointF(16,20.5))
        p.drawLine(QPointF(8,10),QPointF(16,10))
        p.drawLine(QPointF(13,7),QPointF(16,10))
        p.drawLine(QPointF(13,13),QPointF(16,10))
        p.end(); return QIcon(px)

    def _ico_minus(self):
        px = QPixmap(32,32); px.fill(Qt.transparent)
        p = QPainter(px); p.setRenderHint(QPainter.Antialiasing)
        p.setPen(QPen(self._icon_color,3,Qt.SolidLine,Qt.RoundCap))
        p.drawLine(8,16,24,16); p.end(); return QIcon(px)

    def _ico_plus(self):
        px = QPixmap(32,32); px.fill(Qt.transparent)
        p = QPainter(px); p.setRenderHint(QPainter.Antialiasing)
        p.setPen(QPen(self._icon_color,3,Qt.SolidLine,Qt.RoundCap))
        p.drawLine(8,16,24,16); p.drawLine(16,8,16,24); p.end(); return QIcon(px)
