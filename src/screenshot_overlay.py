"""
Screenshot overlay with annotation tools
"""

from PyQt5.QtWidgets import QWidget, QApplication, QLabel
from PyQt5.QtCore import Qt, QRect, QPoint, pyqtSignal
from PyQt5.QtGui import QPainter, QPixmap, QColor, QPen, QCursor, QScreen, QBrush, QKeyEvent
from .annotation_tools import AnnotationManager
from .toolbar import Toolbar
from .uploader import ImageUploader


# ── Shortcut matching helper ──────────────────────────────────────────────────

_KEY_NAME_MAP = {
    'return': Qt.Key_Return, 'enter': Qt.Key_Return,
    'escape': Qt.Key_Escape,
    'backspace': Qt.Key_Backspace,
    'delete': Qt.Key_Delete,
    'tab': Qt.Key_Tab,
    'space': Qt.Key_Space,
    'f1':  Qt.Key_F1,  'f2':  Qt.Key_F2,  'f3':  Qt.Key_F3,
    'f4':  Qt.Key_F4,  'f5':  Qt.Key_F5,  'f6':  Qt.Key_F6,
    'f7':  Qt.Key_F7,  'f8':  Qt.Key_F8,  'f9':  Qt.Key_F9,
    'f10': Qt.Key_F10, 'f11': Qt.Key_F11, 'f12': Qt.Key_F12,
}

def _key_match(event, shortcut_str):
    """Return True if QKeyEvent matches shortcut string (e.g. 'ctrl+z', 'p', 'return')."""
    if not shortcut_str:
        return False
    parts = shortcut_str.lower().strip().split('+')
    expected_mods = Qt.NoModifier
    key_part = None
    for p in parts:
        p = p.strip()
        if   p == 'ctrl':  expected_mods |= Qt.ControlModifier
        elif p == 'shift': expected_mods |= Qt.ShiftModifier
        elif p == 'alt':   expected_mods |= Qt.AltModifier
        else:              key_part = p
    if key_part is None:
        return False
    if key_part in _KEY_NAME_MAP:
        expected_key = _KEY_NAME_MAP[key_part]
    elif len(key_part) == 1:
        expected_key = ord(key_part.upper())
    else:
        return False
    return event.key() == expected_key and event.modifiers() == expected_mods


# ─────────────────────────────────────────────────────────────────────────────

class PinnedImageWindow(QLabel):
    """Draggable pinned image window that closes on ESC"""
    
    def __init__(self, pixmap, geometry):
        super().__init__()
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setPixmap(pixmap)
        self.setGeometry(geometry)
        
        # For dragging
        self.dragging = False
        self.drag_position = QPoint()
        
        # Set cursor to indicate draggable
        self.setCursor(Qt.OpenHandCursor)
    
    def mousePressEvent(self, event):
        """Start dragging"""
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
    
    def mouseMoveEvent(self, event):
        """Handle dragging"""
        if self.dragging:
            self.move(event.globalPos() - self.drag_position)
            event.accept()
    
    def mouseReleaseEvent(self, event):
        """Stop dragging"""
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.setCursor(Qt.OpenHandCursor)
            event.accept()
    
    def keyPressEvent(self, event):
        """Handle ESC key to close window"""
        if event.key() == Qt.Key_Escape:
            print("[PINNED] ESC pressed, closing pinned window")
            self.close()
            event.accept()
        else:
            super().keyPressEvent(event)

class ScreenshotOverlay(QWidget):
    def __init__(self, config, fullscreen=False):
        super().__init__()
        self.config = config
        self.fullscreen_mode = fullscreen
        self.init_ui()
        self.init_variables()
        
        if fullscreen:
            self.finalize_fullscreen()
        
    def init_ui(self):
        # Fullscreen overlay
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint | 
            Qt.FramelessWindowHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)  # receive mouseMoveEvent even without button press
        self.showFullScreen()
        self.setCursor(Qt.CrossCursor)
        
        # Take screenshot of all screens
        self.screen_pixmap = self.capture_screen()
        
    def init_variables(self):
        self.selection_rect = QRect()
        self.is_selecting = False
        self.start_point = QPoint()
        self.end_point = QPoint()
        self.is_editing = False
        self.is_moving_selection = False
        self.move_start_pos = QPoint()
        self.resize_handle = None  # active corner being dragged: 'tl','tr','bl','br'

        self.annotation_manager = AnnotationManager()
        self.toolbar = None
        self.size_indicator = None
        # Text input state (no QLineEdit — handled directly in overlay to avoid focus issues)
        self.text_input = None          # kept for legacy checks; always None now
        self.text_active = False        # whether inline text entry is active
        self.text_buffer = ""           # characters typed so far
        self.text_cursor = 0            # cursor position inside text_buffer
        self.text_pos = QPoint()        # screen position where text is drawn
        self.text_color = QColor(255, 255, 255)
        self.uploader = ImageUploader(self.config)
        
    def _get_handle_at(self, pos):
        """Return handle id ('tl','tr','bl','br') if pos is within hit-area of a corner handle, else None."""
        if self.selection_rect.isNull():
            return None
        hit = 12  # hit-area radius in px
        corners = {
            'tl': QPoint(self.selection_rect.left(),  self.selection_rect.top()),
            'tr': QPoint(self.selection_rect.right(), self.selection_rect.top()),
            'bl': QPoint(self.selection_rect.left(),  self.selection_rect.bottom()),
            'br': QPoint(self.selection_rect.right(), self.selection_rect.bottom()),
        }
        for handle_id, corner in corners.items():
            if abs(pos.x() - corner.x()) <= hit and abs(pos.y() - corner.y()) <= hit:
                return handle_id
        return None

    def _resize_cursor_for(self, handle_id):
        """Return the appropriate resize cursor for a corner handle."""
        if handle_id in ('tl', 'br'):
            return Qt.SizeFDiagCursor   # ↖↘
        return Qt.SizeBDiagCursor       # ↗↙

    def capture_screen(self):
        """Capture screen - primary screen only for simplicity"""
        # Get primary screen
        screen = QApplication.primaryScreen()
        if not screen:
            return QPixmap()
        
        # Capture the primary screen
        screenshot = screen.grabWindow(0)
        return screenshot
        
    def finalize_fullscreen(self):
        """For fullscreen mode, immediately finalize the entire screen"""
        self.selection_rect = QRect(0, 0, self.screen_pixmap.width(), self.screen_pixmap.height())
        self.start_editing()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        
        # Draw the screenshot
        painter.drawPixmap(0, 0, self.screen_pixmap)
        
        # Draw dark overlay (opacity from config)
        opacity = self.config.get('overlay_opacity', 100)
        painter.fillRect(self.rect(), QColor(0, 0, 0, opacity))
        
        if not self.selection_rect.isNull():
            # Clear selected area
            painter.setCompositionMode(QPainter.CompositionMode_Clear)
            painter.fillRect(self.selection_rect, Qt.transparent)
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            
            # Draw selected area
            selected_pixmap = self.screen_pixmap.copy(self.selection_rect)
            painter.drawPixmap(self.selection_rect, selected_pixmap)
            
            # Draw annotations (with clipping to selection area)
            if self.is_editing:
                # Set clipping region to prevent annotations from going outside selection
                painter.setClipRect(self.selection_rect)
                
                # Translate painter to selection area origin (coordinates are now relative)
                painter.save()
                painter.translate(self.selection_rect.topLeft())
                self.annotation_manager.draw(painter, QPoint(0, 0))
                painter.restore()
                
                painter.setClipping(False)
                
                # Draw live text input preview
                if self.text_active:
                    from PyQt5.QtGui import QFont, QFontMetrics
                    font_size = self.annotation_manager.text_font_size
                    font = QFont("Arial", font_size)
                    painter.setFont(font)
                    fm = QFontMetrics(font)
                    before_cursor = self.text_buffer[:self.text_cursor]
                    caret_x = self.text_pos.x() + fm.horizontalAdvance(before_cursor)
                    baseline_y = self.text_pos.y() + fm.ascent()
                    # Draw text
                    painter.setPen(self.text_color)
                    painter.drawText(self.text_pos.x(), baseline_y, self.text_buffer)
                    # Draw caret line
                    painter.setPen(QPen(self.text_color, 2))
                    painter.drawLine(caret_x, self.text_pos.y(), caret_x, self.text_pos.y() + fm.height())
            
            # Draw selection border (color from config)
            sel_color = QColor(self.config.get('selection_color', '#f5cb11'))
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            painter.setPen(QPen(sel_color, 3))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(self.selection_rect)

            # Draw corner handles
            painter.save()
            handle_size = 10
            handles_positions = [
                (self.selection_rect.x() - handle_size // 2,
                 self.selection_rect.y() - handle_size // 2),
                (self.selection_rect.x() + self.selection_rect.width() - handle_size // 2,
                 self.selection_rect.y() - handle_size // 2),
                (self.selection_rect.x() - handle_size // 2,
                 self.selection_rect.y() + self.selection_rect.height() - handle_size // 2),
                (self.selection_rect.x() + self.selection_rect.width() - handle_size // 2,
                 self.selection_rect.y() + self.selection_rect.height() - handle_size // 2),
            ]
            for x, y in handles_positions:
                painter.fillRect(x, y, handle_size, handle_size, sel_color)
            painter.restore()
            
            # Draw size info with background (Flameshot style)
            if self.is_selecting:
                info_text = f"{self.selection_rect.width()} x {self.selection_rect.height()}"
                
                # Calculate text size
                font_metrics = painter.fontMetrics()
                text_width = font_metrics.horizontalAdvance(info_text)
                text_height = font_metrics.height()
                padding = 8
                
                # Position: top-left of selection
                text_x = self.selection_rect.x()
                text_y = self.selection_rect.y() - text_height - padding - 5
                
                # If too close to top, show below selection
                if text_y < 5:
                    text_y = self.selection_rect.y() + self.selection_rect.height() + padding + 5
                
                # Draw background
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(QColor(245, 203, 17, 200)))  # Yellow/Gold background
                painter.drawRect(
                    text_x - padding // 2,
                    text_y - padding // 2,
                    text_width + padding,
                    text_height + padding
                )
                
                # Draw text
                painter.setPen(QColor(255, 255, 255))
                painter.drawText(text_x + padding // 2, text_y + text_height - padding // 2, info_text)
                
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # If text input is active and user clicks elsewhere, commit the text
            if self.text_active:
                self._commit_pending_text()

            if not self.is_editing:
                # Start selection
                self.is_selecting = True
                self.start_point = event.pos()
                self.end_point = event.pos()
            elif self.is_editing:
                # Check corner handles first (resize takes priority)
                handle = self._get_handle_at(event.pos())
                if handle:
                    self.resize_handle = handle
                    self.setCursor(self._resize_cursor_for(handle))
                elif self.is_moving_selection:
                    self.move_start_pos = event.pos()
                else:
                    # Annotation tools
                    from .annotation_tools import ToolType
                    if self.annotation_manager.current_tool == ToolType.TEXT:
                        self.show_text_input_dialog(event.pos())
                    else:
                        self.annotation_manager.mouse_press(event.pos(), self.selection_rect.topLeft())
                    self.update()
        elif event.button() == Qt.RightButton:
            if self.is_editing:
                self.cancel_capture()
                
    def mouseMoveEvent(self, event):
        if self.is_selecting:
            self.end_point = event.pos()
            self.selection_rect = QRect(self.start_point, self.end_point).normalized()
            self.update()
        elif self.resize_handle and self.is_editing:
            # Resize selection by dragging a corner handle
            pos = event.pos()
            r = QRect(self.selection_rect)
            min_size = 20

            if 't' in self.resize_handle:
                r.setTop(min(pos.y(), r.bottom() - min_size))
            if 'b' in self.resize_handle:
                r.setBottom(max(pos.y(), r.top() + min_size))
            if 'l' in self.resize_handle:
                r.setLeft(min(pos.x(), r.right() - min_size))
            if 'r' in self.resize_handle:
                r.setRight(max(pos.x(), r.left() + min_size))

            self.selection_rect = r
            if self.toolbar:
                self.position_toolbar()
            self.update_size_indicator()
            self.update()
        elif self.is_moving_selection and self.is_editing:
            # Move the selection rect
            delta = event.pos() - self.move_start_pos
            self.selection_rect.translate(delta)
            self.move_start_pos = event.pos()
            if self.toolbar:
                self.position_toolbar()
            self.update()
        elif self.is_editing:
            # Update cursor when hovering over corner handles
            if not self.annotation_manager.is_drawing:
                handle = self._get_handle_at(event.pos())
                if handle:
                    self.setCursor(self._resize_cursor_for(handle))
                elif self.is_moving_selection:
                    self.setCursor(Qt.SizeAllCursor)
                else:
                    self.setCursor(Qt.ArrowCursor)
            self.annotation_manager.mouse_move(event.pos(), self.selection_rect.topLeft())
            self.update()
            
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.is_selecting:
                self.is_selecting = False
                if self.selection_rect.width() > 10 and self.selection_rect.height() > 10:
                    self.start_editing()
            elif self.resize_handle:
                # Finish resizing
                self.resize_handle = None
                self.setCursor(Qt.ArrowCursor)
                self.position_toolbar()
                self.update_size_indicator()
                self.update()
            elif self.is_editing:
                # Check if we just finished a blur or invert annotation
                from .annotation_tools import BlurAnnotation, InvertAnnotation, ToolType
                
                if self.annotation_manager.current_annotation and len(self.annotation_manager.current_annotation.points) >= 2:
                    # For invert, we need to capture the CURRENT rendered state (with all previous annotations)
                    # For blur, we use the original screenshot
                    if isinstance(self.annotation_manager.current_annotation, InvertAnnotation):
                        # Create pixmap with all existing annotations rendered
                        temp_pixmap = QPixmap(self.selection_rect.size())
                        temp_pixmap.fill(Qt.white)
                        temp_painter = QPainter(temp_pixmap)
                        
                        # Draw original screenshot
                        temp_painter.drawPixmap(0, 0, self.screen_pixmap.copy(self.selection_rect))
                        
                        # Draw all PREVIOUS annotations (not the current one)
                        temp_painter.save()
                        for annotation in self.annotation_manager.annotations:
                            annotation.draw(temp_painter, QPoint(0, 0))
                        temp_painter.restore()
                        temp_painter.end()
                        
                        # Now invert from this rendered result
                        self.annotation_manager.apply_invert_to_annotation(
                            self.annotation_manager.current_annotation,
                            temp_pixmap
                        )
                    elif isinstance(self.annotation_manager.current_annotation, BlurAnnotation):
                        # Blur uses original screenshot
                        selected_pixmap = self.screen_pixmap.copy(self.selection_rect)
                        self.annotation_manager.apply_blur_to_annotation(
                            self.annotation_manager.current_annotation,
                            selected_pixmap
                        )
                
                self.annotation_manager.mouse_release(event.pos(), self.selection_rect.topLeft())
                self.update()
                
    def keyPressEvent(self, event):
        # When text input is active, all keys are handled here (no QLineEdit)
        if self.text_active:
            print(f"[TEXT] keyPressEvent: key={event.key()}, text='{event.text()}', buffer='{self.text_buffer}'")
            key = event.key()
            if key == Qt.Key_Escape:
                self.text_active = False
                self.text_buffer = ""
                self.annotation_manager.current_annotation = None
                self.annotation_manager.is_drawing = False
                self.update()
            elif key in (Qt.Key_Return, Qt.Key_Enter):
                self.finish_text_input()
            elif key == Qt.Key_Backspace:
                if self.text_cursor > 0:
                    self.text_buffer = self.text_buffer[:self.text_cursor - 1] + self.text_buffer[self.text_cursor:]
                    self.text_cursor -= 1
                    self.update()
            elif key == Qt.Key_Delete:
                if self.text_cursor < len(self.text_buffer):
                    self.text_buffer = self.text_buffer[:self.text_cursor] + self.text_buffer[self.text_cursor + 1:]
                    self.update()
            elif key == Qt.Key_Left:
                self.text_cursor = max(0, self.text_cursor - 1)
                self.update()
            elif key == Qt.Key_Right:
                self.text_cursor = min(len(self.text_buffer), self.text_cursor + 1)
                self.update()
            elif key == Qt.Key_Home:
                self.text_cursor = 0
                self.update()
            elif key == Qt.Key_End:
                self.text_cursor = len(self.text_buffer)
                self.update()
            elif event.text() and not (event.modifiers() & Qt.ControlModifier):
                self.text_buffer = self.text_buffer[:self.text_cursor] + event.text() + self.text_buffer[self.text_cursor:]
                self.text_cursor += len(event.text())
                self.update()
            return

        # Normal key handling (text input not active)
        cfg = self.config
        if _key_match(event, cfg.get('shortcut_cancel', 'escape')):
            self.cancel_capture()
        elif _key_match(event, cfg.get('shortcut_save', 'return')):
            if self.is_editing:
                self.finish_capture()
        elif _key_match(event, cfg.get('shortcut_undo', 'ctrl+z')):
            if self.is_editing:
                self.annotation_manager.undo()
                self.update()
        elif _key_match(event, cfg.get('shortcut_redo', 'ctrl+y')):
            if self.is_editing:
                self.annotation_manager.redo()
                self.update()
        elif _key_match(event, cfg.get('shortcut_copy', 'ctrl+c')):
            if self.is_editing:
                self.copy_to_clipboard()
        elif self.is_editing:
            from .annotation_tools import ToolType
            _tool_map = [
                ('shortcut_pen',         'p',  ToolType.PEN),
                ('shortcut_line',        'l',  ToolType.LINE),
                ('shortcut_arrow',       'a',  ToolType.ARROW),
                ('shortcut_rect',        'r',  ToolType.RECTANGLE),
                ('shortcut_circle',      'c',  ToolType.CIRCLE),
                ('shortcut_highlighter', 'm',  ToolType.HIGHLIGHTER),
                ('shortcut_text',        't',  ToolType.TEXT),
                ('shortcut_number',      'n',  ToolType.NUMBER),
                ('shortcut_blur',        'b',  ToolType.BLUR),
                ('shortcut_invert',      'i',  ToolType.INVERT),
            ]
            matched_tool = False
            for cfg_key, default, tool_type in _tool_map:
                if _key_match(event, cfg.get(cfg_key, default)):
                    if self.toolbar:
                        self.toolbar.select_tool(tool_type)
                    matched_tool = True
                    break
            # Selection nudge with Shift+Arrow (fixed, not configurable)
            if not matched_tool and event.modifiers() == Qt.ShiftModifier:
                nudge = {
                    Qt.Key_Left:  QPoint(-1, 0),
                    Qt.Key_Right: QPoint(1, 0),
                    Qt.Key_Up:    QPoint(0, -1),
                    Qt.Key_Down:  QPoint(0, 1),
                }
                if event.key() in nudge:
                    self.selection_rect = self.selection_rect.translated(nudge[event.key()])
                    if self.toolbar:
                        self.position_toolbar()
                    self.update_size_indicator()
                    self.update()
                
    def start_editing(self):
        """Start annotation mode"""
        self.is_editing = True
        self.setCursor(Qt.ArrowCursor)
        
        if self.toolbar is None:
            self.toolbar = Toolbar(self, self.annotation_manager)
        
        # Show first so style sheets are applied and sizeHint() is accurate
        self.toolbar.show()
        # Then position using correct button sizes
        self.position_toolbar()
        
        self.create_size_indicator()
        self.update_size_indicator()
        
        self.update()
        
    def create_size_indicator(self):
        """Create size indicator label (Flameshot-style)"""
        from PyQt5.QtWidgets import QLabel
        
        if self.size_indicator is None:
            self.size_indicator = QLabel(self)
            self.size_indicator.setStyleSheet("""
                QLabel {
                    background-color: rgba(0, 10, 82, 230);
                    color: rgb(245, 203, 17);
                    padding: 4px 10px;
                    border-radius: 3px;
                    font-size: 12px;
                    font-weight: bold;
                    border: 1px solid rgb(245, 203, 17);
                }
            """)
            self.size_indicator.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
            
    def update_size_indicator(self):
        """Update size indicator with current selection dimensions"""
        if self.size_indicator and not self.selection_rect.isNull():
            size_text = f"{self.selection_rect.width()} × {self.selection_rect.height()} px"
            self.size_indicator.setText(size_text)
            self.size_indicator.adjustSize()

            if self.toolbar:
                top_bar = self.toolbar.bars['top']
                indicator_x = top_bar.x() + top_bar.width() // 2 - self.size_indicator.width() // 2
                indicator_y = top_bar.y() - self.size_indicator.height() - 4
                if indicator_y < 5:
                    indicator_y = top_bar.y() + top_bar.height() + 4
                indicator_x = max(5, min(indicator_x, self.width() - self.size_indicator.width() - 5))
                self.size_indicator.move(indicator_x, indicator_y)
                self.size_indicator.show()
                self.size_indicator.repaint()
                
    def position_toolbar(self):
        """Position 3 responsive toolbar zones around the selection."""
        if self.toolbar is None:
            return

        r   = self.selection_rect
        sw  = self.width()
        sh  = self.height()
        gap = 8

        bars  = self.toolbar.bars
        top   = bars['top']
        right = bars['right']
        bot   = bars['bot']

        # ── TOP bar: above selection, centered to selection ────────────────
        max_w = max(r.width(), 44)
        top.set_max_w(max_w)
        # Center the bar over the selection horizontally
        tx = r.left() + (r.width() - top.width()) // 2
        tx = max(5, min(tx, sw - top.width() - 5))
        ty = r.top() - top.height() - gap
        if ty < 5:
            ty = r.bottom() + gap   # no room above → go below
        top.move(tx, ty)
        top.repaint()

        # ── RIGHT bar: right of selection, height-constrained to selection ─
        max_h = max(r.height(), 44)
        right.set_max_h(max_h)
        rx = r.right() + gap
        if rx + right.width() > sw - 5:
            rx = r.left() - right.width() - gap  # no room right → go left
        rx = max(5, rx)
        # Center the bar vertically beside the selection
        ry = r.top() + (r.height() - right.height()) // 2
        ry = max(5, min(ry, sh - right.height() - 5))
        right.move(rx, ry)
        right.repaint()

        # ── BOT bar: below selection, centered to selection ────────────────
        bot.set_max_w(max_w)
        bx = r.left() + (r.width() - bot.width()) // 2
        bx = max(5, min(bx, sw - bot.width() - 5))
        by = r.bottom() + gap
        if by + bot.height() > sh - 5:
            by = r.top() - bot.height() - gap  # no room below → go above
            if by < 5:
                by = r.bottom() - bot.height() - gap
        bot.move(bx, by)
        bot.repaint()
        
    def finish_capture(self):
        """Finish capture and upload"""
        print("[SAVE] finish_capture called")
        self._commit_pending_text()
        try:
            # Create final image
            final_pixmap = QPixmap(self.selection_rect.size())
            final_pixmap.fill(Qt.white)
            
            painter = QPainter(final_pixmap)
            # Draw screenshot
            painter.drawPixmap(0, 0, self.screen_pixmap.copy(self.selection_rect))
            # Draw annotations
            self.annotation_manager.draw(painter, QPoint(0, 0))
            painter.end()
            
            # Convert to bytes using QBuffer
            from PyQt5.QtCore import QBuffer, QIODevice
            buffer = QBuffer()
            buffer.open(QIODevice.WriteOnly)
            final_pixmap.save(buffer, "PNG")
            image_data = buffer.data().data()
            
            # Save local copy if enabled
            if self.config.get('save_local_copy', False):
                try:
                    self.save_local(final_pixmap)
                except Exception as e:
                    print(f"Warning: Failed to save local copy: {e}")
            
            # Upload and get URL
            self.hide()
            if self.toolbar:
                self.toolbar.hide()
            
            try:
                url = self.uploader.upload(image_data)
            except Exception as e:
                print(f"Upload error: {e}")
                url = None
            
            if url:
                # Copy to clipboard if enabled
                if self.config.get('auto_copy_url', True):
                    try:
                        clipboard = QApplication.clipboard()
                        clipboard.setText(url)
                    except Exception as e:
                        print(f"Clipboard error: {e}")
                
                # Show notification if enabled
                if self.config.get('show_notification', True):
                    try:
                        from PyQt5.QtWidgets import QMessageBox
                        msg = QMessageBox()
                        msg.setIcon(QMessageBox.Information)
                        msg.setWindowTitle("XenShoot")
                        
                        if self.config.get('auto_copy_url', True):
                            msg.setText(f"Screenshot uploaded!\nURL copied to clipboard:\n{url}")
                        else:
                            msg.setText(f"Screenshot uploaded!\nURL: {url}")
                            
                        msg.setStandardButtons(QMessageBox.Ok)
                        msg.exec_()
                    except Exception as e:
                        print(f"Notification error: {e}")
            else:
                # Show error if upload failed
                from PyQt5.QtWidgets import QMessageBox
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setWindowTitle("XenShoot")
                msg.setText("Upload failed!\n\nScreenshot saved locally (if enabled).\nCheck console for error details.")
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec_()
            
        except Exception as e:
            print(f"Critical error in finish_capture: {e}")
            import traceback
            traceback.print_exc()
            
            # Show error dialog
            try:
                from PyQt5.QtWidgets import QMessageBox
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Critical)
                msg.setWindowTitle("XenShoot - Error")
                msg.setText(f"An error occurred:\n{str(e)}\n\nCheck console for details.")
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec_()
            except:
                pass
        finally:
            # Always close the overlay and size indicator
            if self.size_indicator:
                self.size_indicator.hide()
            self.close()
        
    def save_local(self, pixmap):
        """Save screenshot pixmap to local folder using config template, return filepath"""
        import os
        from datetime import datetime
        from pathlib import Path

        save_path = self.config.get('local_save_path', '') or str(Path.home() / "Pictures" / "XenShoot")
        os.makedirs(save_path, exist_ok=True)

        template = self.config.get('filename_template', 'xenshoot_%Y-%m-%d_%H-%M-%S')
        ext      = self.config.get('preferred_extension', 'png').lower().lstrip('.')
        try:
            name = datetime.now().strftime(template)
        except Exception:
            name = f"xenshoot_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        filepath = os.path.join(save_path, f"{name}.{ext}")
        fmt = "JPEG" if ext in ('jpg', 'jpeg') else "PNG"
        quality = self.config.get('jpeg_quality', 90) if fmt == "JPEG" else -1
        pixmap.save(filepath, fmt, quality)
        return filepath

    def save_to_local_only(self):
        """Save screenshot with annotations — user picks save location via dialog"""
        self._commit_pending_text()
        try:
            final_pixmap = QPixmap(self.selection_rect.size())
            final_pixmap.fill(Qt.white)
            painter = QPainter(final_pixmap)
            painter.drawPixmap(0, 0, self.screen_pixmap.copy(self.selection_rect))
            self.annotation_manager.draw(painter, QPoint(0, 0))
            painter.end()

            # Hide overlay before showing dialog
            self.hide()
            if self.toolbar:
                self.toolbar.hide()
            if self.size_indicator:
                self.size_indicator.hide()

            from PyQt5.QtWidgets import QFileDialog
            from datetime import datetime
            from pathlib import Path

            default_dir = self.config.get('local_save_path', '') or str(Path.home() / "Pictures" / "XenShoot")
            ext      = self.config.get('preferred_extension', 'png').lower().lstrip('.')
            template = self.config.get('filename_template', 'xenshoot_%Y-%m-%d_%H-%M-%S')
            try:
                base_name = datetime.now().strftime(template)
            except Exception:
                base_name = f"xenshoot_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            default_path = str(Path(default_dir) / f"{base_name}.{ext}")

            # Build filter with preferred extension first
            if ext in ('jpg', 'jpeg'):
                filt = "JPEG Image (*.jpg *.jpeg);;PNG Image (*.png);;All Files (*)"
            else:
                filt = "PNG Image (*.png);;JPEG Image (*.jpg *.jpeg);;All Files (*)"

            filepath, _ = QFileDialog.getSaveFileName(
                None, "Simpan Screenshot", default_path, filt
            )

            if filepath:
                if not any(filepath.lower().endswith(e) for e in ('.png', '.jpg', '.jpeg')):
                    filepath += f'.{ext}'
                fmt     = "JPEG" if filepath.lower().endswith(('.jpg', '.jpeg')) else "PNG"
                quality = self.config.get('jpeg_quality', 90) if fmt == "JPEG" else -1
                final_pixmap.save(filepath, fmt, quality)
        except Exception as e:
            print(f"Error saving local: {e}")
            import traceback; traceback.print_exc()
        finally:
            self.close()
        
    def copy_to_clipboard(self):
        """Copy screenshot with annotations to clipboard"""
        self._commit_pending_text()
        from PyQt5.QtWidgets import QApplication
        
        try:
            # Create final image with annotations
            final_pixmap = QPixmap(self.selection_rect.size())
            final_pixmap.fill(Qt.white)
            
            painter = QPainter(final_pixmap)
            # Draw screenshot
            painter.drawPixmap(0, 0, self.screen_pixmap.copy(self.selection_rect))
            # Annotation points are stored relative to selection origin (0,0 of final_pixmap)
            self.annotation_manager.draw(painter, QPoint(0, 0))
            painter.end()
            
            # Copy to clipboard
            clipboard = QApplication.clipboard()
            clipboard.setPixmap(final_pixmap)
            
            print("[SCREENSHOT] Copied to clipboard!")
            
            # Close overlay after copy
            self.cancel_capture()
            
        except Exception as e:
            print(f"[ERROR] Failed to copy to clipboard: {e}")
            import traceback
            traceback.print_exc()
    
    def pin_to_screen(self):
        """Pin screenshot to screen (keep it visible)"""
        self._commit_pending_text()
        try:
            # Create final image with annotations
            final_pixmap = QPixmap(self.selection_rect.size())
            final_pixmap.fill(Qt.white)
            
            painter = QPainter(final_pixmap)
            painter.drawPixmap(0, 0, self.screen_pixmap.copy(self.selection_rect))
            self.annotation_manager.draw(painter, QPoint(0, 0))
            painter.end()
            
            # Create draggable pinned window
            pinned = PinnedImageWindow(final_pixmap, self.selection_rect)
            
            # Store reference to prevent garbage collection
            if not hasattr(self, 'pinned_windows'):
                self.pinned_windows = []
            self.pinned_windows.append(pinned)
            
            pinned.show()
            
            print("[SCREENSHOT] Pinned to screen! Drag to move, ESC to close.")
            
            # Close overlay after pinning
            self.cancel_capture()
            
        except Exception as e:
            print(f"[ERROR] Failed to pin to screen: {e}")
            import traceback
            traceback.print_exc()
    
    def toggle_move_mode(self):
        """Toggle move selection mode on/off"""
        self.is_moving_selection = not self.is_moving_selection
        
        if self.is_moving_selection:
            self.setCursor(Qt.SizeAllCursor)  # Four-way arrow cursor
            print("[SCREENSHOT] Move mode enabled - drag to move selection")
        else:
            self.setCursor(Qt.CrossCursor)  # Back to crosshair
            print("[SCREENSHOT] Move mode disabled")
        
        # Update toolbar button visual state if needed
        if self.toolbar and hasattr(self.toolbar, 'move_btn'):
            self.toolbar.move_btn.setStyleSheet(
                self.toolbar.move_btn.styleSheet() + 
                (" border: 2px solid rgb(245, 203, 17);" if self.is_moving_selection else "")
            )
    
    def open_with_app(self):
        """Save screenshot and open with selected application"""
        self._commit_pending_text()
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QListWidget, QPushButton, QMessageBox, QListWidgetItem, QLabel
        import os
        import subprocess
        
        try:
            # Create final image with annotations
            final_pixmap = QPixmap(self.selection_rect.size())
            final_pixmap.fill(Qt.white)
            
            painter = QPainter(final_pixmap)
            painter.drawPixmap(0, 0, self.screen_pixmap.copy(self.selection_rect))
            self.annotation_manager.draw(painter, QPoint(0, 0))
            painter.end()
            
            # Save to temp file
            import tempfile
            from datetime import datetime
            
            temp_dir = tempfile.gettempdir()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_path = os.path.join(temp_dir, f"xenshoot_{timestamp}.png")
            
            if not final_pixmap.save(temp_path, "PNG"):
                QMessageBox.warning(None, "Error", "Failed to save screenshot")
                return
            
            print(f"[SCREENSHOT] Saved temp file: {temp_path}")
            
            # List of common image editing apps with their typical paths
            common_apps = [
                ("Paint", "mspaint.exe"),
                ("Paint 3D", "C:\\Program Files\\WindowsApps\\Microsoft.MSPaint_*\\PaintStudio.View.exe"),
                ("Photoshop", "C:\\Program Files\\Adobe\\Adobe Photoshop*\\Photoshop.exe"),
                ("GIMP", "C:\\Program Files\\GIMP*\\bin\\gimp-*.exe"),
                ("Paint.NET", "C:\\Program Files\\paint.net\\paintdotnet.exe"),
                ("Inkscape", "C:\\Program Files\\Inkscape\\bin\\inkscape.exe"),
                ("IrfanView", "C:\\Program Files\\IrfanView\\i_view64.exe"),
                ("XnView", "C:\\Program Files\\XnView\\xnview.exe"),
            ]
            
            # Find available apps
            available_apps = []
            
            # Check mspaint (always available on Windows)
            available_apps.append(("Paint", "mspaint.exe"))
            
            # Check other apps
            import glob
            for app_name, app_pattern in common_apps[1:]:
                if "*" in app_pattern:
                    # Use glob to find matching paths
                    matches = glob.glob(app_pattern)
                    if matches:
                        available_apps.append((app_name, matches[0]))
                else:
                    # Direct path check
                    if os.path.exists(app_pattern):
                        available_apps.append((app_name, app_pattern))
            
            if not available_apps:
                QMessageBox.warning(None, "No Apps Found", "No image editing apps found")
                return
            
            # Create modern styled dialog
            dialog = QDialog()
            dialog.setWindowTitle("Open with Application")
            dialog.setMinimumWidth(400)
            dialog.setMinimumHeight(300)
            dialog.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Dialog | Qt.WindowCloseButtonHint)
            
            # Apply modern styling
            dialog.setStyleSheet("""
                QDialog {
                    background-color: #2b2b2b;
                }
                QLabel {
                    color: #f5cb11;
                    font-size: 14px;
                    font-weight: bold;
                    padding: 10px;
                }
                QListWidget {
                    background-color: #1e1e1e;
                    border: 2px solid #f5cb11;
                    border-radius: 5px;
                    color: white;
                    font-size: 13px;
                    padding: 5px;
                }
                QListWidget::item {
                    padding: 10px;
                    border-radius: 3px;
                }
                QListWidget::item:selected {
                    background-color: #000a52;
                    color: #f5cb11;
                }
                QListWidget::item:hover {
                    background-color: #3a3a3a;
                }
                QPushButton {
                    background-color: #000a52;
                    color: #f5cb11;
                    border: 2px solid #f5cb11;
                    border-radius: 5px;
                    padding: 10px 20px;
                    font-size: 13px;
                    font-weight: bold;
                    min-width: 100px;
                }
                QPushButton:hover {
                    background-color: #000f64;
                }
                QPushButton:pressed {
                    background-color: #00053c;
                }
            """)
            
            layout = QVBoxLayout()
            layout.setSpacing(10)
            layout.setContentsMargins(15, 15, 15, 15)
            
            # Title label
            title_label = QLabel("Choose an application to open your capture:")
            layout.addWidget(title_label)
            
            # List widget
            list_widget = QListWidget()
            for app_name, app_path in available_apps:
                item = QListWidgetItem(f"  {app_name}")
                item.setData(Qt.UserRole, app_path)
                list_widget.addItem(item)
            
            list_widget.setCurrentRow(0)
            layout.addWidget(list_widget)
            
            # Buttons layout
            from PyQt5.QtWidgets import QHBoxLayout
            button_layout = QHBoxLayout()
            button_layout.addStretch()
            
            # Cancel button
            cancel_btn = QPushButton("Cancel")
            cancel_btn.clicked.connect(dialog.reject)
            button_layout.addWidget(cancel_btn)
            
            # OK button
            ok_btn = QPushButton("Open")
            ok_btn.clicked.connect(dialog.accept)
            ok_btn.setDefault(True)
            button_layout.addWidget(ok_btn)
            
            layout.addLayout(button_layout)
            
            dialog.setLayout(layout)
            
            # Show dialog
            if dialog.exec_() == QDialog.Accepted:
                selected_item = list_widget.currentItem()
                if selected_item:
                    app_path = selected_item.data(Qt.UserRole)
                    print(f"[SCREENSHOT] Opening with: {app_path}")
                    
                    # Open file with selected app
                    if app_path == "mspaint.exe":
                        subprocess.Popen([app_path, temp_path])
                    else:
                        subprocess.Popen([app_path, temp_path])
                    
                    # Close overlay
                    self.cancel_capture()
            
        except Exception as e:
            print(f"[ERROR] Failed to open with app: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.warning(None, "Error", f"Failed to open with app: {str(e)}")
    
    def cancel_capture(self):
        """Cancel capture"""
        # Cleanup any active text input
        self.text_active = False
        self.text_buffer = ""
        
        # Cleanup toolbar
        if self.toolbar:
            self.toolbar.close()
            self.toolbar = None
        
        # Cleanup size indicator
        if self.size_indicator:
            self.size_indicator.close()
            self.size_indicator = None
        
        # Close overlay window
        self.close()
    
    def show_text_input_dialog(self, pos):
        """Start inline text input at click position (no QLineEdit — uses overlay key events)"""
        from .annotation_tools import ToolType
        
        # Commit any existing text first
        if self.text_active:
            self._commit_pending_text()
        
        # Create text annotation placeholder
        offset = self.selection_rect.topLeft()
        self.annotation_manager.mouse_press(pos, offset)
        
        if not self.annotation_manager.current_annotation:
            return
        
        text_annotation = self.annotation_manager.current_annotation
        relative_pos = text_annotation.position
        screen_pos = relative_pos + self.selection_rect.topLeft()
        
        # Set up buffer-based text input
        self.text_active = True
        self.text_buffer = ""
        self.text_cursor = 0
        self.text_pos = QPoint(screen_pos.x(), screen_pos.y())
        self.text_color = self.annotation_manager.current_color
        print(f"[TEXT] text input started at screen_pos=({screen_pos.x()},{screen_pos.y()})")
        # Ensure overlay keeps keyboard focus (not toolbar or other window)
        self.activateWindow()
        self.setFocus()
        self.update()
    
    def finish_text_input(self):
        """Commit buffered text as a text annotation"""
        print(f"[TEXT] finish_text_input: text_active={self.text_active}, current_annotation={self.annotation_manager.current_annotation}, buffer='{self.text_buffer}'")
        if not self.text_active or not self.annotation_manager.current_annotation:
            return
        
        text = self.text_buffer.strip()
        self.text_active = False
        self.text_buffer = ""
        self.text_cursor = 0
        
        if text:
            self.annotation_manager.add_text_annotation(text)
            print(f"[TEXT] annotation added, total={len(self.annotation_manager.annotations)}")
        else:
            print(f"[TEXT] empty buffer — cancelled")
            self.annotation_manager.current_annotation = None
            self.annotation_manager.is_drawing = False
        
        self.update()

    def _commit_pending_text(self):
        """Finalize any active text input before exporting or switching tools."""
        if self.text_active:
            self.finish_text_input()