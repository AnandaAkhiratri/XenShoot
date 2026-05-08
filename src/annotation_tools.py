"""
Annotation tools for drawing on screenshots
"""

from PyQt5.QtCore import QPoint, QRect, Qt
from PyQt5.QtGui import QPen, QColor, QPainter, QFont, QBrush, QPixmap, QImage
from enum import Enum
import math

class ToolType(Enum):
    SELECT = "select"
    RECTANGLE = "rectangle"
    RECTANGLE_FILLED = "rectangle_filled"
    CIRCLE = "circle"
    ARROW = "arrow"
    LINE = "line"
    PEN = "pen"
    TEXT = "text"
    NUMBER = "number"
    HIGHLIGHTER = "highlighter"
    BLUR = "blur"
    INVERT = "invert"  # Invert colors like Flameshot

class Annotation:
    def __init__(self, tool_type, color, thickness):
        self.tool_type = tool_type
        self.color = color
        self.thickness = thickness
        self.points = []
        self.text = ""
        self.rect = QRect()
        
    def add_point(self, point):
        self.points.append(point)
        
    def draw(self, painter, offset=QPoint(0, 0)):
        """Draw this annotation"""
        pass

class RectangleAnnotation(Annotation):
    def draw(self, painter, offset=QPoint(0, 0)):
        if len(self.points) >= 2:
            # Enable antialiasing for smooth rectangles
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
            
            # Use relative coordinates directly
            rect = QRect(self.points[0], self.points[-1]).normalized()
            
            # Safety check - prevent huge rectangles
            if rect.width() > 2000 or rect.height() > 2000:
                return
            
            painter.setPen(QPen(self.color, self.thickness, Qt.SolidLine, Qt.SquareCap, Qt.MiterJoin))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(rect)
            
            # Reset antialiasing
            painter.setRenderHint(QPainter.Antialiasing, False)

class FilledRectangleAnnotation(Annotation):
    """Filled rectangle annotation - solid filled rectangle"""
    def draw(self, painter, offset=QPoint(0, 0)):
        if len(self.points) >= 2:
            # Enable antialiasing for smooth rectangles
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
            
            print(f"[DEBUG FILLED_RECT] Drawing: points[0]=({self.points[0].x()}, {self.points[0].y()}), points[-1]=({self.points[-1].x()}, {self.points[-1].y()})")
            
            # Use relative coordinates directly
            rect = QRect(self.points[0], self.points[-1]).normalized()
            
            print(f"[DEBUG FILLED_RECT] Rect size: {rect.width()} x {rect.height()}")
            
            # Safety check - prevent accidentally drawing huge rectangles
            if rect.width() > 2000 or rect.height() > 2000:
                print(f"[DEBUG FILLED_RECT] BLOCKED! Rect too large!")
                return  # Don't draw if too large (likely a bug)
            
            # Make filled rectangle SOLID (100% opaque)
            color = QColor(self.color)
            color.setAlpha(255)  # 100% SOLID - not transparent
            
            painter.setPen(QPen(self.color, self.thickness, Qt.SolidLine, Qt.SquareCap, Qt.MiterJoin))
            painter.setBrush(QBrush(color))  # Fill with SOLID color
            painter.drawRect(rect)
            
            # Reset antialiasing
            painter.setRenderHint(QPainter.Antialiasing, False)

class CircleAnnotation(Annotation):
    def draw(self, painter, offset=QPoint(0, 0)):
        if len(self.points) >= 2:
            # Enable antialiasing for smooth circles
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
            
            # Use relative coordinates directly
            rect = QRect(self.points[0], self.points[-1]).normalized()
            
            # Safety check - prevent huge circles
            if rect.width() > 2000 or rect.height() > 2000:
                return
            
            painter.setPen(QPen(self.color, self.thickness, Qt.SolidLine, Qt.SquareCap, Qt.MiterJoin))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(rect)
            
            # Reset antialiasing
            painter.setRenderHint(QPainter.Antialiasing, False)

class LineAnnotation(Annotation):
    def draw(self, painter, offset=QPoint(0, 0)):
        if len(self.points) >= 2:
            # Enable antialiasing for smooth lines
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
            
            painter.setPen(QPen(self.color, self.thickness, Qt.SolidLine, Qt.SquareCap, Qt.MiterJoin))
            # Use relative coordinates directly
            painter.drawLine(self.points[0], self.points[-1])
            
            # Reset antialiasing
            painter.setRenderHint(QPainter.Antialiasing, False)

class ArrowAnnotation(Annotation):
    def draw(self, painter, offset=QPoint(0, 0)):
        if len(self.points) >= 2:
            from PyQt5.QtCore import QPointF
            from PyQt5.QtGui import QPolygonF

            painter.setRenderHint(QPainter.Antialiasing, True)

            start = self.points[0]
            end   = self.points[-1]

            angle = math.atan2(end.y() - start.y(), end.x() - start.x())

            # Arrow head size scales with thickness
            head_len  = max(14, self.thickness * 3)
            head_half = math.pi / 6   # 30°

            tip   = QPointF(end)
            p1    = QPointF(tip.x() - head_len * math.cos(angle - head_half),
                            tip.y() - head_len * math.sin(angle - head_half))
            p2    = QPointF(tip.x() - head_len * math.cos(angle + head_half),
                            tip.y() - head_len * math.sin(angle + head_half))

            # Line ends at base of arrowhead (not tip) to avoid protrusion
            base  = QPointF((p1.x() + p2.x()) / 2, (p1.y() + p2.y()) / 2)

            # Draw shaft — FlatCap gives clean flat tail end
            painter.setPen(QPen(self.color, self.thickness, Qt.SolidLine,
                                Qt.FlatCap, Qt.RoundJoin))
            painter.setBrush(Qt.NoBrush)
            painter.drawLine(QPointF(start), base)

            # Draw filled arrowhead — no pen stroke to avoid extra edges
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(self.color))
            painter.drawPolygon(QPolygonF([tip, p1, p2]))

            painter.setRenderHint(QPainter.Antialiasing, False)

class PenAnnotation(Annotation):
    def draw(self, painter, offset=QPoint(0, 0)):
        if len(self.points) >= 2:
            # Enable antialiasing for smooth pen strokes
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
            
            painter.setPen(QPen(self.color, self.thickness, Qt.SolidLine, Qt.SquareCap, Qt.MiterJoin))
            for i in range(len(self.points) - 1):
                painter.drawLine(self.points[i], self.points[i + 1])
            
            # Reset antialiasing
            painter.setRenderHint(QPainter.Antialiasing, False)

class HighlighterAnnotation(Annotation):
    def draw(self, painter, offset=QPoint(0, 0)):
        if len(self.points) >= 2:
            # Enable antialiasing for smooth highlighter
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
            
            color = QColor(self.color)
            color.setAlpha(80)
            painter.setPen(QPen(color, self.thickness * 3, Qt.SolidLine, Qt.SquareCap, Qt.MiterJoin))
            for i in range(len(self.points) - 1):
                painter.drawLine(self.points[i], self.points[i + 1])
            
            # Reset antialiasing
            painter.setRenderHint(QPainter.Antialiasing, False)

class TextAnnotation(Annotation):
    def __init__(self, tool_type, color, thickness, font_size=32):
        super().__init__(tool_type, color, thickness)
        self.text = ""
        self.position = QPoint()
        self.font_size = font_size

    def draw(self, painter, offset=QPoint(0, 0)):
        if self.text and not self.position.isNull():
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setRenderHint(QPainter.TextAntialiasing, True)
            painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

            font = QFont("Arial", self.font_size, QFont.Normal)
            painter.setFont(font)
            from PyQt5.QtGui import QFontMetrics
            fm = QFontMetrics(font)
            # Draw at same baseline as live preview (position.y + ascent)
            painter.setPen(QPen(self.color))
            painter.drawText(self.position.x(), self.position.y() + fm.ascent(), self.text)

            painter.setRenderHint(QPainter.Antialiasing, False)
            painter.setRenderHint(QPainter.TextAntialiasing, False)

class NumberAnnotation(Annotation):
    """Number pin marker — circle with optional triangle pointer on drag."""
    def __init__(self, tool_type, color, thickness, number):
        super().__init__(tool_type, color, thickness)
        self.number = number
        self.position = QPoint()   # circle center (click start)
        self.pointer_end = None    # triangle tip (drag end), None = no pointer

    def draw(self, painter, offset=QPoint(0, 0)):
        if self.position.isNull():
            return
        from PyQt5.QtCore import QRectF, QPointF
        from PyQt5.QtGui import QPolygonF

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)

        circle_radius = max(10, self.thickness + 9)
        font_size = max(8, int(circle_radius * 0.7))

        cx, cy = float(self.position.x()), float(self.position.y())

        # ── Draw triangle pointer if dragged far enough ──────────────────
        if self.pointer_end and not self.pointer_end.isNull():
            dx = self.pointer_end.x() - cx
            dy = self.pointer_end.y() - cy
            dist = math.hypot(dx, dy)

            if dist > circle_radius + 4:
                import math as _m
                angle = _m.atan2(dy, dx)
                half_w = _m.pi / 5   # 36° half-width of triangle base

                # Two points on circle edge
                base1 = QPointF(cx + circle_radius * _m.cos(angle - half_w),
                                cy + circle_radius * _m.sin(angle - half_w))
                base2 = QPointF(cx + circle_radius * _m.cos(angle + half_w),
                                cy + circle_radius * _m.sin(angle + half_w))
                tip   = QPointF(float(self.pointer_end.x()), float(self.pointer_end.y()))

                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(self.color))
                painter.drawPolygon(QPolygonF([base1, base2, tip]))

        # ── Draw filled circle with white border ─────────────────────────
        border_w = max(2, circle_radius // 8)
        painter.setPen(QPen(QColor(255, 255, 255), border_w))
        painter.setBrush(QBrush(self.color))
        painter.drawEllipse(QRectF(cx - circle_radius, cy - circle_radius,
                                   circle_radius * 2, circle_radius * 2))

        # ── Draw number ───────────────────────────────────────────────────
        painter.setPen(QPen(QColor(255, 255, 255)))
        font = QFont("Arial", font_size, QFont.Bold)
        painter.setFont(font)
        painter.drawText(QRect(int(cx - circle_radius), int(cy - circle_radius),
                               circle_radius * 2, circle_radius * 2),
                         Qt.AlignCenter, str(self.number))

        painter.restore()

class BlurAnnotation(Annotation):
    """Blur/pixelate annotation for censoring sensitive information"""
    def __init__(self, tool_type, color, thickness):
        super().__init__(tool_type, color, thickness)
        self.blurred_pixmap = None  # Store the blurred result

    def _overlay_alpha(self):
        """Opacity of dark overlay: size 1→5, size 50→255 (fully black)"""
        return int(5 + (self.thickness - 1) * (250 / 49))

    def draw(self, painter, offset=QPoint(0, 0)):
        if len(self.points) >= 2:
            rect = QRect(self.points[0], self.points[-1]).normalized()
            if rect.width() > 2000 or rect.height() > 2000:
                return

            if self.blurred_pixmap and not self.blurred_pixmap.isNull():
                # Draw pixelated base
                painter.drawPixmap(rect, self.blurred_pixmap)
            else:
                # Preview: show darkening rectangle while dragging
                pass

            # Dark overlay — opacity proportional to size
            alpha = self._overlay_alpha()
            painter.save()
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(0, 0, 0, alpha))
            painter.drawRect(rect)
            painter.restore()

            # Border preview
            painter.setPen(QPen(QColor(52, 152, 219, 180), 1))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(rect)

class InvertAnnotation(Annotation):
    """Invert colors annotation - inverts RGB colors like Flameshot"""
    def __init__(self, tool_type, color, thickness):
        super().__init__(tool_type, color, thickness)
        self.inverted_pixmap = None  # Store the inverted result
    
    def draw(self, painter, offset=QPoint(0, 0)):
        if len(self.points) >= 2:
            # Use relative coordinates directly
            rect = QRect(self.points[0], self.points[-1]).normalized()
            
            # Safety check - prevent huge invert areas
            if rect.width() > 2000 or rect.height() > 2000:
                return
            
            # If we have a pre-inverted pixmap, draw it
            if self.inverted_pixmap and not self.inverted_pixmap.isNull():
                painter.drawPixmap(rect, self.inverted_pixmap)
            else:
                # Preview mode - show purple outline to indicate invert area
                painter.setPen(QPen(QColor(155, 89, 182), 2))  # Purple outline
                painter.setBrush(Qt.NoBrush)  # No fill - empty rectangle
                painter.drawRect(rect)

class AnnotationManager:
    def __init__(self):
        self.annotations = []
        self.current_annotation = None
        self.current_tool = ToolType.SELECT
        self.current_color = QColor(245, 203, 17)  # Yellow/Gold default (#f5cb11)
        self.current_thickness = 3   # unified size 1-50 for all tools
        self.undo_stack = []
        self.is_drawing = False
        self.number_counter = 1  # Counter for number annotations
        
    def set_tool(self, tool_type):
        self.current_tool = tool_type
        print(f"[ANNOTATION_MANAGER] Tool set to: {tool_type}")
        
    def set_color(self, color):
        self.current_color = color
        
    @property
    def text_font_size(self):
        """Derive font size from current_thickness: size 1→10pt, size 50→108pt"""
        return max(8, self.current_thickness * 2 + 8)

    def set_thickness(self, thickness):
        self.current_thickness = max(1, min(50, thickness))
        
    def mouse_press(self, pos, offset):
        if self.current_tool == ToolType.SELECT:
            return
            
        self.is_drawing = True
        
        # Convert to relative coordinates (relative to selection area)
        relative_pos = pos - offset
        print(f"[DEBUG] mouse_press: pos=({pos.x()}, {pos.y()}), offset=({offset.x()}, {offset.y()}), relative=({relative_pos.x()}, {relative_pos.y()})")
        
        # Create new annotation based on tool type
        if self.current_tool == ToolType.RECTANGLE:
            self.current_annotation = RectangleAnnotation(self.current_tool, self.current_color, self.current_thickness)
        elif self.current_tool == ToolType.RECTANGLE_FILLED:
            self.current_annotation = FilledRectangleAnnotation(self.current_tool, self.current_color, self.current_thickness)
        elif self.current_tool == ToolType.CIRCLE:
            self.current_annotation = CircleAnnotation(self.current_tool, self.current_color, self.current_thickness)
        elif self.current_tool == ToolType.LINE:
            self.current_annotation = LineAnnotation(self.current_tool, self.current_color, self.current_thickness)
        elif self.current_tool == ToolType.ARROW:
            self.current_annotation = ArrowAnnotation(self.current_tool, self.current_color, self.current_thickness)
            print(f"[DEBUG] Created ARROW annotation")
        elif self.current_tool == ToolType.PEN:
            self.current_annotation = PenAnnotation(self.current_tool, self.current_color, self.current_thickness)
        elif self.current_tool == ToolType.HIGHLIGHTER:
            self.current_annotation = HighlighterAnnotation(self.current_tool, self.current_color, self.current_thickness)
        elif self.current_tool == ToolType.BLUR:
            self.current_annotation = BlurAnnotation(self.current_tool, self.current_color, self.current_thickness)
        elif self.current_tool == ToolType.INVERT:
            self.current_annotation = InvertAnnotation(self.current_tool, self.current_color, self.current_thickness)
        elif self.current_tool == ToolType.TEXT:
            self.current_annotation = TextAnnotation(self.current_tool, self.current_color, self.current_thickness, self.text_font_size)
            self.current_annotation.position = relative_pos
            self.is_drawing = True
            return  # Don't add point, just wait for text input
        elif self.current_tool == ToolType.NUMBER:
            self.current_annotation = NumberAnnotation(
                self.current_tool, self.current_color,
                self.current_thickness, self.number_counter)
            self.current_annotation.position = relative_pos
            self.is_drawing = True
            return  # Wait for release/drag
            
        if self.current_annotation:
            # Store in relative coordinates (relative to selection area)
            self.current_annotation.add_point(relative_pos)
            print(f"[DEBUG] Added point: ({relative_pos.x()}, {relative_pos.y()})")
            
    def mouse_move(self, pos, offset):
        if self.is_drawing and self.current_annotation:
            # Convert to relative coordinates
            relative_pos = pos - offset
            # Number tool: update pointer tip on drag
            if self.current_tool == ToolType.NUMBER:
                self.current_annotation.pointer_end = relative_pos
                return
            if self.current_tool in [ToolType.PEN, ToolType.HIGHLIGHTER]:
                self.current_annotation.add_point(relative_pos)
            elif len(self.current_annotation.points) > 0:
                # Update last point for shapes
                if len(self.current_annotation.points) == 1:
                    self.current_annotation.add_point(relative_pos)
                else:
                    self.current_annotation.points[-1] = relative_pos
                    
    def mouse_release(self, pos, offset):
        if self.is_drawing and self.current_annotation:
            # TEXT annotations are finalized via add_text_annotation(), not here
            if self.current_tool == ToolType.TEXT:
                return
            # NUMBER: commit and increment counter
            if self.current_tool == ToolType.NUMBER:
                self.annotations.append(self.current_annotation)
                self.undo_stack.clear()
                self.number_counter += 1
                self.current_annotation = None
                self.is_drawing = False
                return
            self.annotations.append(self.current_annotation)
            self.undo_stack.clear()
            self.current_annotation = None
            self.is_drawing = False
    
    def add_text_annotation(self, text):
        """Add text to current text annotation and finalize it"""
        if self.current_annotation and isinstance(self.current_annotation, TextAnnotation):
            self.current_annotation.text = text
            # Always use the latest font size (user may have changed it with wheel)
            self.current_annotation.font_size = self.text_font_size
            self.annotations.append(self.current_annotation)
            self.undo_stack.clear()
            self.current_annotation = None
            self.is_drawing = False
    
    def apply_blur_to_annotation(self, blur_annotation, source_pixmap):
        """Apply actual blur effect to a BlurAnnotation using the source screenshot
        
        Args:
            blur_annotation: The BlurAnnotation to apply blur to
            source_pixmap: The original screenshot QPixmap to blur from
        """
        if not isinstance(blur_annotation, BlurAnnotation) or len(blur_annotation.points) < 2:
            return
        
        rect = QRect(blur_annotation.points[0], blur_annotation.points[-1]).normalized()
        
        # Safety check
        if rect.width() <= 0 or rect.height() <= 0 or rect.width() > 2000 or rect.height() > 2000:
            return
        
        # Extract the region to blur
        region = source_pixmap.copy(rect)
        
        # Blur strength scales with thickness: size 1→4, size 50→30
        blur_strength = max(4, int(4 + blur_annotation.thickness * 0.52))

        if region.width() > blur_strength and region.height() > blur_strength:
            small = region.scaled(
                max(1, region.width() // blur_strength),
                max(1, region.height() // blur_strength),
                Qt.IgnoreAspectRatio,
                Qt.FastTransformation
            )
            blurred = small.scaled(
                region.width(),
                region.height(),
                Qt.IgnoreAspectRatio,
                Qt.SmoothTransformation
            )
            blur_annotation.blurred_pixmap = blurred
        else:
            blur_annotation.blurred_pixmap = region
    
    def apply_invert_to_annotation(self, invert_annotation, source_pixmap):
        """Apply color inversion to an InvertAnnotation using the source screenshot
        
        Args:
            invert_annotation: The InvertAnnotation to apply inversion to
            source_pixmap: The original screenshot QPixmap to invert from
        """
        if not isinstance(invert_annotation, InvertAnnotation) or len(invert_annotation.points) < 2:
            return
        
        rect = QRect(invert_annotation.points[0], invert_annotation.points[-1]).normalized()
        
        # Safety check
        if rect.width() <= 0 or rect.height() <= 0 or rect.width() > 2000 or rect.height() > 2000:
            return
        
        # Extract the region to invert
        region = source_pixmap.copy(rect)
        
        # Convert to QImage for pixel manipulation
        image = region.toImage()
        
        # Invert all pixels (RGB inversion: new_color = 255 - old_color)
        for y in range(image.height()):
            for x in range(image.width()):
                pixel = image.pixel(x, y)
                r = 255 - ((pixel >> 16) & 0xFF)
                g = 255 - ((pixel >> 8) & 0xFF)
                b = 255 - (pixel & 0xFF)
                a = (pixel >> 24) & 0xFF  # Keep alpha unchanged
                inverted_pixel = (a << 24) | (r << 16) | (g << 8) | b
                image.setPixel(x, y, inverted_pixel)
        
        # Convert back to QPixmap
        invert_annotation.inverted_pixmap = QPixmap.fromImage(image)
            
    def draw(self, painter, offset):
        """Draw all annotations"""
        for annotation in self.annotations:
            annotation.draw(painter, offset)
            
        # Draw current annotation being drawn
        if self.current_annotation:
            self.current_annotation.draw(painter, offset)
            
    def undo(self):
        if self.annotations:
            self.undo_stack.append(self.annotations.pop())
            
    def redo(self):
        if self.undo_stack:
            self.annotations.append(self.undo_stack.pop())
