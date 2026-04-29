"""
Toolbar for annotation tools - Professional icons
"""

from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QPushButton, QColorDialog, 
                             QSpinBox, QLabel, QVBoxLayout, QStyle)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPainter, QColor, QPen, QFont, QPainterPath, QIcon, QPixmap, QBrush
from .annotation_tools import ToolType

class Toolbar(QWidget):
    def __init__(self, parent, annotation_manager):
        super().__init__(parent)
        self.annotation_manager = annotation_manager
        self.parent_overlay = parent
        self.init_ui()
        
    def init_ui(self):
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        
        layout = QHBoxLayout()
        layout.setSpacing(4)  # Tighter spacing like Flameshot
        layout.setContentsMargins(6, 6, 6, 6)
        
        # Clean and consistent NAVY/YELLOW theme - Navy background, Yellow icons
        self.setStyleSheet("""
            QWidget {
                background-color: transparent;
                border-radius: 3px;
            }
            QPushButton {
                background-color: rgba(0, 10, 82, 255);
                color: rgb(245, 203, 17);
                border: none;
                border-radius: 18px;
                min-width: 36px;
                min-height: 36px;
                max-width: 36px;
                max-height: 36px;
                font-size: 17px;
                font-weight: normal;
                font-family: "Segoe UI Symbol", "Segoe UI", "Arial Unicode MS", sans-serif;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: rgba(0, 20, 102, 255);
                color: rgb(245, 203, 17);
            }
            QPushButton:checked {
                background-color: rgba(0, 5, 52, 255);
                border: 2px solid rgb(245, 203, 17);
                color: rgb(245, 203, 17);
            }
            QPushButton:pressed {
                background-color: rgba(0, 2, 32, 255);
                color: rgb(245, 203, 17);
            }
            QLabel {
                color: white;
                padding: 5px;
                font-size: 10px;
            }
        """)
        
        # Tools with custom drawn icons
        self.tools = {}
        
        # Create icons programmatically - no external images needed
        # Ordered logically: drawing tools first, then shapes
        tools_config = [
            (ToolType.PEN, self.create_pen_icon(), "Pencil - Freehand drawing (P)"),
            (ToolType.LINE, self.create_line_icon(), "Line - Draw straight line (L)"),
            (ToolType.ARROW, self.create_arrow_icon(), "Arrow - Draw arrow pointer (A)"),
            (ToolType.RECTANGLE, self.create_rect_icon(), "Rectangle - Draw outline (R)"),
            (ToolType.CIRCLE, self.create_circle_icon(), "Circle - Draw circle outline (C)"),
            (ToolType.RECTANGLE_FILLED, self.create_filled_rect_icon(), "Filled Box - Highlight area (Shift+R)"),
            (ToolType.HIGHLIGHTER, self.create_highlighter_icon(), "Highlighter - Mark text (M)"),
            (ToolType.TEXT, self.create_text_icon(), "Text - Add label (T)"),
            (ToolType.NUMBER, self.create_number_icon(), "Number - Add numbered counter (N)"),
            (ToolType.BLUR, self.create_blur_icon(), "Blur - Hide sensitive info (B)"),
            (ToolType.INVERT, self.create_invert_icon(), "Invert - Reverse colors (I)"),
        ]
        
        for tool_type, icon, tooltip in tools_config:
            btn = QPushButton()
            btn.setIcon(icon)
            btn.setIconSize(QSize(28, 28))  # Larger icon size (was 20x20)
            btn.setToolTip(tooltip)
            btn.setCheckable(True)
            
            # Create wrapper function for better debugging
            def make_tool_handler(t):
                def handler(checked):
                    print(f"[BUTTON] Clicked: {t}, checked={checked}")
                    self.select_tool(t)
                return handler
            
            btn.clicked.connect(make_tool_handler(tool_type))
            self.tools[tool_type] = btn
            layout.addWidget(btn)
        
        # Color picker button
        self.color_btn = QPushButton("⬤")
        self.color_btn.setToolTip("Color Picker")
        self.color_btn.setStyleSheet("""
            QPushButton {
                background-color: rgb(0, 10, 82);
                color: rgb(245, 203, 17);
                font-size: 14px;
                border-radius: 18px;
                min-width: 36px;
                min-height: 36px;
                max-width: 36px;
                max-height: 36px;
            }
            QPushButton:hover {
                background-color: rgb(0, 20, 102);
                color: rgb(245, 203, 17);
            }
        """)
        self.color_btn.clicked.connect(self.pick_color)
        layout.addWidget(self.color_btn)
        
        # Undo button with icon
        undo_btn = QPushButton()
        undo_btn.setIcon(self.create_undo_icon())
        undo_btn.setIconSize(QSize(28, 28))  # Larger icon
        undo_btn.setToolTip("Undo (Ctrl+Z)")
        undo_btn.setCheckable(False)
        undo_btn.clicked.connect(self.undo)
        layout.addWidget(undo_btn)
        
        # Redo button with icon
        redo_btn = QPushButton()
        redo_btn.setIcon(self.create_redo_icon())
        redo_btn.setIconSize(QSize(28, 28))  # Larger icon
        redo_btn.setToolTip("Redo (Ctrl+Y)")
        redo_btn.setCheckable(False)
        redo_btn.clicked.connect(self.redo)
        layout.addWidget(redo_btn)
        
        # Move Selection button
        move_btn = QPushButton()
        move_btn.setIcon(self.create_move_icon())
        move_btn.setIconSize(QSize(28, 28))
        move_btn.setToolTip("Move selection area (Ctrl+M)")
        move_btn.setCheckable(False)
        move_btn.clicked.connect(self.toggle_move_mode)
        layout.addWidget(move_btn)
        self.move_btn = move_btn  # Store reference
        
        # Open with app button
        open_btn = QPushButton()
        open_btn.setIcon(self.create_open_app_icon())  # Use screen-share icon for "open with app"
        open_btn.setIconSize(QSize(28, 28))
        open_btn.setToolTip("Choose an app to open the capture (Ctrl+O)")
        open_btn.setCheckable(False)
        open_btn.clicked.connect(self.open_with_app)
        layout.addWidget(open_btn)
        
        # Copy button
        copy_btn = QPushButton()
        copy_btn.setIcon(self.create_copy_icon())
        copy_btn.setIconSize(QSize(28, 28))
        copy_btn.setToolTip("Copy to Clipboard")
        copy_btn.setCheckable(False)
        copy_btn.clicked.connect(self.copy_to_clipboard)
        layout.addWidget(copy_btn)
        
        # Save button (Navy theme like other buttons)
        save_btn = QPushButton()
        save_btn.setIcon(self.create_save_icon())
        save_btn.setIconSize(QSize(28, 28))
        save_btn.setToolTip("Save & Upload (Enter)")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 10, 82, 255);
                color: rgb(245, 203, 17);
                font-size: 20px;
                font-weight: bold;
                border-radius: 18px;
                min-width: 36px;
                min-height: 36px;
                max-width: 36px;
                max-height: 36px;
            }
            QPushButton:hover {
                background-color: rgba(0, 15, 100, 255);
            }
            QPushButton:pressed {
                background-color: rgba(0, 5, 60, 255);
            }
        """)
        save_btn.setCheckable(False)
        save_btn.clicked.connect(self.save)
        layout.addWidget(save_btn)
        
        # Pin button
        pin_btn = QPushButton("📌")
        pin_btn.setToolTip("Pin to Screen")
        pin_btn.setCheckable(False)
        pin_btn.clicked.connect(self.pin_to_screen)
        layout.addWidget(pin_btn)
        
        # Exit button (Red X like Flameshot)
        exit_btn = QPushButton()
        exit_btn.setIcon(self.create_exit_icon())
        exit_btn.setIconSize(QSize(28, 28))
        exit_btn.setToolTip("Exit (Esc)")
        exit_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 10, 82, 255);
                color: rgb(245, 203, 17);
                font-size: 20px;
                font-weight: bold;
                border-radius: 18px;
                min-width: 36px;
                min-height: 36px;
                max-width: 36px;
                max-height: 36px;
            }
            QPushButton:hover {
                background-color: rgba(0, 15, 100, 255);
            }
            QPushButton:pressed {
                background-color: rgba(0, 5, 60, 255);
            }
        """)
        exit_btn.setCheckable(False)
        exit_btn.clicked.connect(self.cancel)
        layout.addWidget(exit_btn)
        
        self.setLayout(layout)
        
        # Select pen tool by default (like Flameshot)
        self.select_tool(ToolType.PEN)
    
    def create_pen_icon(self):
        """Create pen/pencil icon - from latest SVG (scaled up and centered)"""
        from PyQt5.QtCore import QPointF
        from PyQt5.QtGui import QPolygonF
        
        pixmap = QPixmap(32, 32)  # Larger canvas
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Better centering - move more to center
        painter.translate(5, 5)  # Center adjustment
        painter.scale(1.0, 1.0)  # No scale, use original size for better fit
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(245, 203, 17))
        
        # Main pencil body
        body = QPolygonF([
            QPointF(3, 18),
            QPointF(15, 6),
            QPointF(18, 9),
            QPointF(6, 21),
            QPointF(3, 21),
            QPointF(3, 18)
        ])
        painter.drawPolygon(body)
        
        # Top/eraser part
        eraser = QPolygonF([
            QPointF(16, 5),
            QPointF(18, 3),
            QPointF(21, 6),
            QPointF(19, 8),
            QPointF(16, 5)
        ])
        painter.drawPolygon(eraser)
        
        painter.end()
        return QIcon(pixmap)
    
    def create_line_icon(self):
        """Create line icon"""
        pixmap = QPixmap(24, 24)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor(245, 203, 17), 2)
        painter.setPen(pen)
        painter.drawLine(4, 20, 20, 4)
        painter.end()
        return QIcon(pixmap)
    
    def create_arrow_icon(self):
        """Create arrow icon - improved with better arrowhead"""
        from PyQt5.QtCore import QPoint
        pixmap = QPixmap(24, 24)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        pen = QPen(QColor(245, 203, 17), 2)
        painter.setPen(pen)
        
        # Arrow line (from bottom-left to top-right)
        painter.drawLine(4, 20, 20, 4)
        
        # Arrowhead (better shape)
        painter.drawLine(20, 4, 14, 6)
        painter.drawLine(20, 4, 18, 10)
        
        painter.end()
        return QIcon(pixmap)
    
    def create_rect_icon(self):
        """Create rectangle outline icon - OUTLINE ONLY, no fill"""
        pixmap = QPixmap(24, 24)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw OUTLINE ONLY - no fill
        pen = QPen(QColor(245, 203, 17), 2)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)  # Explicitly no brush
        painter.drawRect(5, 5, 14, 14)
        
        painter.end()
        return QIcon(pixmap)
    
    def create_filled_rect_icon(self):
        """Create filled rectangle icon - clearly distinguished from outline"""
        pixmap = QPixmap(24, 24)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw SOLID filled rectangle with thick border
        painter.setBrush(QColor(245, 203, 17))
        painter.setPen(QPen(QColor(245, 203, 17), 2))  # Thick border
        painter.drawRect(5, 5, 14, 14)
        
        painter.end()
        return QIcon(pixmap)
    
    def create_circle_icon(self):
        """Create circle icon"""
        pixmap = QPixmap(24, 24)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor(245, 203, 17), 2)
        painter.setPen(pen)
        painter.drawEllipse(4, 4, 16, 16)
        painter.end()
        return QIcon(pixmap)
    
    def create_highlighter_icon(self):
        """Create highlighter icon"""
        pixmap = QPixmap(24, 24)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor(245, 203, 17), 5)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        painter.drawLine(4, 12, 20, 12)
        painter.end()
        return QIcon(pixmap)
    
    def create_text_icon(self):
        """Create text icon"""
        pixmap = QPixmap(24, 24)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        font = QFont("Arial", 16, QFont.Bold)
        painter.setFont(font)
        painter.setPen(QColor(245, 203, 17))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "T")
        painter.end()
        return QIcon(pixmap)
    
    def create_blur_icon(self):
        """Create blur/pixelate icon"""
        pixmap = QPixmap(24, 24)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(245, 203, 17))
        for i in range(3):
            for j in range(3):
                painter.drawRect(5 + i*5, 5 + j*5, 3, 3)
        painter.end()
        return QIcon(pixmap)
    
    def create_number_icon(self):
        """Create number counter icon - from SVG number-1-circle"""
        pixmap = QPixmap(32, 32)  # Larger to match other icons
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Center and scale to fit
        painter.translate(4, 4)
        
        # Draw circle outline (cx="12" cy="12" r="9")
        painter.setPen(QPen(QColor(245, 203, 17), 2.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(3, 3, 18, 18)  # radius 9 = diameter 18
        
        # Draw number "1" (path: M12.5,17 V7 L10.5,9)
        painter.setPen(QPen(QColor(245, 203, 17), 2.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        
        # Vertical line of "1"
        painter.drawLine(12, 17, 12, 7)
        
        # Small diagonal top of "1"
        painter.drawLine(12, 7, 10, 9)
        
        painter.end()
        return QIcon(pixmap)
    
    def create_invert_icon(self):
        """Create invert icon - droplet half-filled from SVG"""
        from PyQt5.QtCore import QRectF
        from PyQt5.QtGui import QPainterPath
        
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Scale from 24x24 to 28x28 and center
        painter.translate(2, 2)
        painter.scale(1.17, 1.17)
        
        yellow = QColor(245, 203, 17)
        
        # Parse SVG path: "M12.578 2.184a1.004 1.004 0 0 0-1.156 0C11.119 2.398 4 7.513 4 13.75 4 18.53 7.364 22 12 22s8-3.468 8-8.246c0-6.241-7.119-11.356-7.422-11.57z"
        # This is the droplet outline
        path = QPainterPath()
        path.moveTo(12.578, 2.184)
        # Simplified: draw droplet shape
        path.lineTo(12, 2)
        path.quadTo(4, 8, 4, 13.75)  # Left curve
        path.quadTo(4, 22, 12, 22)   # Bottom curve
        path.quadTo(20, 22, 20, 13.75)  # Right curve
        path.quadTo(20, 8, 12, 2)    # Top curve
        path.closeSubpath()
        
        # Draw outline
        painter.setPen(QPen(yellow, 1.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path)
        
        # Fill left half (like the SVG path: "M6 13.75c0-4.283 4.395-8.201 6-9.49V20c-3.533 0-6-2.57-6-6.25z")
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(yellow))
        
        left_half = QPainterPath()
        left_half.moveTo(12, 4.26)  # Top of droplet center
        left_half.quadTo(6, 8, 6, 13.75)  # Left side
        left_half.quadTo(6, 20, 12, 20)  # Bottom center
        left_half.lineTo(12, 4.26)  # Back to top
        left_half.closeSubpath()
        
        painter.drawPath(left_half)
        
        painter.end()
        return QIcon(pixmap)
    
    def create_undo_icon(self):
        """Create undo icon - curved arrow from reverse-right SVG (mirrored)"""
        from PyQt5.QtGui import QPainterPath
        
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Mirror horizontally for undo (pointing left)
        painter.translate(32, 0)
        painter.scale(-1, 1)
        painter.translate(4, 4)
        
        painter.setPen(QPen(QColor(245, 203, 17), 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.setBrush(Qt.NoBrush)
        
        # Draw curved arrow
        path = QPainterPath()
        path.moveTo(20, 7)
        path.lineTo(10, 7)
        path.cubicTo(6, 7, 4, 9, 4, 13)
        path.cubicTo(4, 17, 6, 19, 10, 19)
        path.lineTo(20, 19)
        painter.drawPath(path)
        
        # Arrow head
        painter.drawLine(20, 7, 16, 3)
        painter.drawLine(20, 7, 16, 11)
        
        painter.end()
        return QIcon(pixmap)
    
    def create_redo_icon(self):
        """Create redo icon - curved arrow from reverse-right SVG"""
        from PyQt5.QtGui import QPainterPath
        
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # No mirror for redo (pointing right)
        painter.translate(4, 4)
        
        painter.setPen(QPen(QColor(245, 203, 17), 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.setBrush(Qt.NoBrush)
        
        # Draw curved arrow
        path = QPainterPath()
        path.moveTo(20, 7)
        path.lineTo(10, 7)
        path.cubicTo(6, 7, 4, 9, 4, 13)
        path.cubicTo(4, 17, 6, 19, 10, 19)
        path.lineTo(20, 19)
        painter.drawPath(path)
        
        # Arrow head
        painter.drawLine(20, 7, 16, 3)
        painter.drawLine(20, 7, 16, 11)
        
        painter.end()
        return QIcon(pixmap)
    
    def create_save_icon(self):
        """Create save icon - simple floppy disk from new SVG"""
        from PyQt5.QtCore import QRectF
        from PyQt5.QtGui import QPainterPath
        
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Scale from 24x24 to ~28x28 and center
        painter.translate(2, 2)
        painter.scale(1.17, 1.17)
        
        yellow = QColor(245, 203, 17)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(yellow))
        
        # Parse path: "M17 3H5c-1.11 0-2 .9-2 2v14c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V7l-4-4z
        #             m-5 16c-1.66 0-3-1.34-3-3s1.34-3 3-3 3 1.34 3 3-1.34 3-3 3z
        #             m3-10H5V5h10v4z"
        
        path = QPainterPath()
        
        # Main body: M17,3 H5 (rounded rect from 3,3 to 21,21)
        # M17 3H5c-1.11 0-2 .9-2 2v14c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V7l-4-4
        path.moveTo(17, 3)
        path.lineTo(5, 3)
        path.cubicTo(3.89, 3, 3, 3.9, 3, 5)
        path.lineTo(3, 19)
        path.cubicTo(3, 20.1, 3.89, 21, 5, 21)
        path.lineTo(19, 21)
        path.cubicTo(20.1, 21, 21, 20.1, 21, 19)
        path.lineTo(21, 7)
        path.lineTo(17, 3)
        path.closeSubpath()
        
        # Circle in middle: m-5 16 (center at 12,19, radius 3)
        # m-5 16c-1.66 0-3-1.34-3-3s1.34-3 3-3 3 1.34 3 3-1.34 3-3 3
        path.addEllipse(QRectF(9, 13, 6, 6))
        
        # Top rectangle: m3-10H5V5h10v4 (rect from 5,5 to 15,9)
        path.moveTo(15, 9)
        path.lineTo(5, 9)
        path.lineTo(5, 5)
        path.lineTo(15, 5)
        path.lineTo(15, 9)
        path.closeSubpath()
        
        painter.drawPath(path)
        
        painter.end()
        return QIcon(pixmap)
    
    def create_exit_icon(self):
        """Create exit/close icon - simple X"""
        from PyQt5.QtCore import QPointF
        
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        yellow = QColor(245, 203, 17)
        painter.setPen(QPen(yellow, 3, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        
        # Draw X with two diagonal lines
        # Top-left to bottom-right
        painter.drawLine(QPointF(8, 8), QPointF(24, 24))
        # Top-right to bottom-left
        painter.drawLine(QPointF(24, 8), QPointF(8, 24))
        
        painter.end()
        return QIcon(pixmap)
    
    def create_copy_icon(self):
        """Create copy icon - simple two overlapping documents"""
        from PyQt5.QtCore import QRectF
        
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        yellow = QColor(245, 203, 17)
        
        # Back document (shadow/copy indicator)
        painter.setPen(QPen(yellow, 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(QRectF(10, 10, 14, 16), 1, 1)
        
        # Front document (main)
        painter.setBrush(QBrush(yellow))
        painter.setPen(QPen(yellow, 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawRoundedRect(QRectF(8, 6, 14, 16), 1, 1)
        
        # Lines on front document to indicate text
        painter.setPen(QPen(QColor(0, 10, 82), 1.5))
        painter.drawLine(10, 10, 20, 10)
        painter.drawLine(10, 13, 20, 13)
        painter.drawLine(10, 16, 17, 16)
        
        painter.end()
        return QIcon(pixmap)
    
    def create_move_icon(self):
        """Create move selection icon - four arrows pointing outward"""
        from PyQt5.QtCore import QPointF
        
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        yellow = QColor(245, 203, 17)
        painter.setPen(QPen(yellow, 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.setBrush(QBrush(yellow))
        
        center = 16
        arrow_len = 8
        arrow_head = 3
        
        # Up arrow
        painter.drawLine(center, center, center, center - arrow_len)
        painter.drawLine(center, center - arrow_len, center - arrow_head, center - arrow_len + arrow_head)
        painter.drawLine(center, center - arrow_len, center + arrow_head, center - arrow_len + arrow_head)
        
        # Down arrow
        painter.drawLine(center, center, center, center + arrow_len)
        painter.drawLine(center, center + arrow_len, center - arrow_head, center + arrow_len - arrow_head)
        painter.drawLine(center, center + arrow_len, center + arrow_head, center + arrow_len - arrow_head)
        
        # Left arrow
        painter.drawLine(center, center, center - arrow_len, center)
        painter.drawLine(center - arrow_len, center, center - arrow_len + arrow_head, center - arrow_head)
        painter.drawLine(center - arrow_len, center, center - arrow_len + arrow_head, center + arrow_head)
        
        # Right arrow
        painter.drawLine(center, center, center + arrow_len, center)
        painter.drawLine(center + arrow_len, center, center + arrow_len - arrow_head, center - arrow_head)
        painter.drawLine(center + arrow_len, center, center + arrow_len - arrow_head, center + arrow_head)
        
        painter.end()
        return QIcon(pixmap)
    
    def create_open_app_icon(self):
        """Create open with app icon - monitor with arrow from SVG"""
        from PyQt5.QtCore import QRectF, QPointF
        from PyQt5.QtGui import QPainterPath
        
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Scale from 24x24 to 28x28 and center
        painter.translate(2, 2)
        painter.scale(1.17, 1.17)
        
        yellow = QColor(245, 203, 17)
        painter.setPen(QPen(yellow, 1.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.setBrush(Qt.NoBrush)
        
        # Monitor screen (rounded rectangle)
        # d="M12 16.5C16 16.5 19.5 16.1667 20 15.8333C20.5 15.5 21 12.6667 21 10C21 7.33333 20.5 4.5 20 4.16667C19.5 3.83333 16 3.5 12 3.5C8 3.5 4.5 3.83333 4 4.16667C3.5 4.5 3 7.33333 3 10C3 12.6667 3.5 15.5 4 15.8333C4.5 16.1667 8 16.5 12 16.5Z"
        painter.drawRoundedRect(QRectF(3, 3.5, 18, 13), 2, 2)
        
        # Stand vertical line
        # M12 16.5V20.5
        painter.drawLine(QPointF(12, 16.5), QPointF(12, 20.5))
        
        # Stand base horizontal line
        # M12 20.5H16 M12 20.5H8
        painter.drawLine(QPointF(8, 20.5), QPointF(16, 20.5))
        
        # Arrow pointing right (share/pin out)
        # M13 13L16 10M16 10L13 7M16 10H8
        painter.drawLine(QPointF(8, 10), QPointF(16, 10))  # Horizontal line
        painter.drawLine(QPointF(13, 7), QPointF(16, 10))  # Arrow top
        painter.drawLine(QPointF(13, 13), QPointF(16, 10))  # Arrow bottom
        
        painter.end()
        return QIcon(pixmap)
    
    def select_tool(self, tool_type):
        """Select a tool and update UI"""
        print(f"[TOOLBAR] Selecting tool: {tool_type}")
        
        # Uncheck all tools
        for btn in self.tools.values():
            btn.setChecked(False)
        
        # Check selected tool
        if tool_type in self.tools:
            self.tools[tool_type].setChecked(True)
            print(f"[TOOLBAR] Button checked for: {tool_type}")
        else:
            print(f"[TOOLBAR ERROR] Tool type {tool_type} not found in self.tools!")
            print(f"[TOOLBAR] Available tools: {list(self.tools.keys())}")
        
        # Update annotation manager
        self.annotation_manager.set_tool(tool_type)
        print(f"[TOOLBAR] Tool selected: {tool_type}")
        
    def pick_color(self):
        """Open color picker dialog"""
        color = QColorDialog.getColor()
        if color.isValid():
            self.annotation_manager.set_color(color)
            # Update button color to show selected color
            self.color_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color.name()};
                    color: white;
                    font-size: 14px;
                    border-radius: 18px;
                    min-width: 36px;
                    min-height: 36px;
                    max-width: 36px;
                    max-height: 36px;
                }}
                QPushButton:hover {{
                    background-color: {color.lighter(110).name()};
                }}
            """)
            
    def change_thickness(self, value):
        """Change line thickness"""
        self.annotation_manager.set_thickness(value)
        
    def undo(self):
        """Undo last annotation"""
        self.annotation_manager.undo()
        self.parent_overlay.update()
        
    def redo(self):
        """Redo annotation"""
        self.annotation_manager.redo()
        self.parent_overlay.update()
    
    def copy_to_clipboard(self):
        """Copy screenshot to clipboard"""
        if self.parent_overlay and hasattr(self.parent_overlay, 'copy_to_clipboard'):
            self.parent_overlay.copy_to_clipboard()
        else:
            print("[TOOLBAR] Copy to clipboard method not found in parent")
    
    def pin_to_screen(self):
        """Pin screenshot to screen"""
        if self.parent_overlay and hasattr(self.parent_overlay, 'pin_to_screen'):
            self.parent_overlay.pin_to_screen()
        else:
            print("[TOOLBAR] Pin to screen method not found in parent")
    
    def toggle_move_mode(self):
        """Toggle move selection mode"""
        if self.parent_overlay and hasattr(self.parent_overlay, 'toggle_move_mode'):
            self.parent_overlay.toggle_move_mode()
        else:
            print("[TOOLBAR] Toggle move mode method not found in parent")
    
    def open_with_app(self):
        """Open capture with selected app"""
        if self.parent_overlay and hasattr(self.parent_overlay, 'open_with_app'):
            self.parent_overlay.open_with_app()
        else:
            print("[TOOLBAR] Open with app method not found in parent")
        
    def save(self):
        """Save and upload screenshot"""
        self.parent_overlay.finish_capture()
        
    def cancel(self):
        """Cancel screenshot"""
        self.parent_overlay.cancel_capture()
