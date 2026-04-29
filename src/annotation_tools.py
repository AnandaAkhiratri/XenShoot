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
            # Use relative coordinates directly
            rect = QRect(self.points[0], self.points[-1]).normalized()
            
            # Safety check - prevent huge rectangles
            if rect.width() > 2000 or rect.height() > 2000:
                return
            
            painter.setPen(QPen(self.color, self.thickness))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(rect)

class FilledRectangleAnnotation(Annotation):
    """Filled rectangle annotation - solid filled rectangle"""
    def draw(self, painter, offset=QPoint(0, 0)):
        if len(self.points) >= 2:
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
            
            painter.setPen(QPen(self.color, self.thickness))
            painter.setBrush(QBrush(color))  # Fill with SOLID color
            painter.drawRect(rect)

class CircleAnnotation(Annotation):
    def draw(self, painter, offset=QPoint(0, 0)):
        if len(self.points) >= 2:
            # Use relative coordinates directly
            rect = QRect(self.points[0], self.points[-1]).normalized()
            
            # Safety check - prevent huge circles
            if rect.width() > 2000 or rect.height() > 2000:
                return
            
            painter.setPen(QPen(self.color, self.thickness))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(rect)

class LineAnnotation(Annotation):
    def draw(self, painter, offset=QPoint(0, 0)):
        if len(self.points) >= 2:
            painter.setPen(QPen(self.color, self.thickness))
            # Use relative coordinates directly
            painter.drawLine(self.points[0], self.points[-1])

class ArrowAnnotation(Annotation):
    def draw(self, painter, offset=QPoint(0, 0)):
        if len(self.points) >= 2:
            # Enable antialiasing for smooth arrows
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
            
            painter.setPen(QPen(self.color, self.thickness, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            painter.setBrush(QBrush(self.color))
            
            # Use relative coordinates directly
            start = self.points[0]
            end = self.points[-1]
            
            # Draw line
            painter.drawLine(start, end)
            
            # Draw arrow head (triangle) with float precision
            angle = math.atan2(end.y() - start.y(), end.x() - start.x())
            arrow_size = 12
            
            # Use QPointF for sub-pixel precision
            from PyQt5.QtCore import QPointF
            from PyQt5.QtGui import QPolygonF
            
            p1 = QPointF(
                end.x() - arrow_size * math.cos(angle - math.pi / 6),
                end.y() - arrow_size * math.sin(angle - math.pi / 6)
            )
            p2 = QPointF(
                end.x() - arrow_size * math.cos(angle + math.pi / 6),
                end.y() - arrow_size * math.sin(angle + math.pi / 6)
            )
            
            # Draw arrowhead as filled polygon with float precision
            polygon = QPolygonF([QPointF(end), p1, p2])
            painter.drawPolygon(polygon)
            
            # Reset antialiasing
            painter.setRenderHint(QPainter.Antialiasing, False)

class PenAnnotation(Annotation):
    def draw(self, painter, offset=QPoint(0, 0)):
        if len(self.points) >= 2:
            painter.setPen(QPen(self.color, self.thickness, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            for i in range(len(self.points) - 1):
                painter.drawLine(self.points[i], self.points[i + 1])

class HighlighterAnnotation(Annotation):
    def draw(self, painter, offset=QPoint(0, 0)):
        if len(self.points) >= 2:
            color = QColor(self.color)
            color.setAlpha(80)
            painter.setPen(QPen(color, self.thickness * 3, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            for i in range(len(self.points) - 1):
                painter.drawLine(self.points[i], self.points[i + 1])

class TextAnnotation(Annotation):
    def __init__(self, tool_type, color, thickness):
        super().__init__(tool_type, color, thickness)
        self.text = ""
        self.position = QPoint()
        
    def draw(self, painter, offset=QPoint(0, 0)):
        if self.text and not self.position.isNull():
            painter.setPen(QPen(self.color))
            font = QFont("Arial", 32, QFont.Normal)  # 32px, normal weight as user requested
            painter.setFont(font)
            # Use relative coordinates directly
            painter.drawText(self.position, self.text)

class NumberAnnotation(Annotation):
    """Number counter annotation - displays numbered circles"""
    def __init__(self, tool_type, color, thickness, number):
        super().__init__(tool_type, color, thickness)
        self.number = number
        self.position = QPoint()
        
    def draw(self, painter, offset=QPoint(0, 0)):
        if not self.position.isNull():
            # Enable antialiasing for smooth circle
            painter.save()
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
            
            # Draw circle with number inside
            circle_radius = 18
            
            # Draw filled circle with smooth edges
            painter.setPen(QPen(self.color, 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            painter.setBrush(QBrush(self.color, Qt.SolidPattern))
            
            # Use QRectF for sub-pixel precision (floating point)
            from PyQt5.QtCore import QRectF, QPointF
            circle_rect = QRectF(
                self.position.x() - circle_radius, 
                self.position.y() - circle_radius,
                circle_radius * 2.0, 
                circle_radius * 2.0
            )
            painter.drawEllipse(circle_rect)
            
            # Draw navy blue number in center with antialiasing
            painter.setPen(QPen(QColor(0, 10, 82)))
            font = QFont("Arial", 14, QFont.Bold)
            painter.setFont(font)
            
            # Calculate text rect for centering
            text = str(self.number)
            text_rect = QRect(
                self.position.x() - circle_radius,
                self.position.y() - circle_radius,
                circle_radius * 2,
                circle_radius * 2
            )
            painter.drawText(text_rect, Qt.AlignCenter, text)
            
            # Reset brush and restore painter state
            painter.setBrush(Qt.NoBrush)
            painter.restore()

class BlurAnnotation(Annotation):
    """Blur/pixelate annotation for censoring sensitive information"""
    def __init__(self, tool_type, color, thickness):
        super().__init__(tool_type, color, thickness)
        self.blurred_pixmap = None  # Store the blurred result
    
    def draw(self, painter, offset=QPoint(0, 0)):
        if len(self.points) >= 2:
            # Use relative coordinates directly
            rect = QRect(self.points[0], self.points[-1]).normalized()
            
            # Safety check - prevent huge blur areas
            if rect.width() > 2000 or rect.height() > 2000:
                return
            
            # If we have a pre-blurred pixmap, draw it
            if self.blurred_pixmap and not self.blurred_pixmap.isNull():
                painter.drawPixmap(rect, self.blurred_pixmap)
            else:
                # Preview mode - just show simple rectangle outline (like drawing a square)
                painter.setPen(QPen(QColor(52, 152, 219), 2))  # Blue outline
                painter.setBrush(Qt.NoBrush)  # No fill - empty rectangle
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
        self.current_thickness = 3
        self.undo_stack = []
        self.is_drawing = False
        self.number_counter = 1  # Counter for number annotations
        
    def set_tool(self, tool_type):
        self.current_tool = tool_type
        print(f"[ANNOTATION_MANAGER] Tool set to: {tool_type}")
        
    def set_color(self, color):
        self.current_color = color
        
    def set_thickness(self, thickness):
        self.current_thickness = thickness
        
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
            self.current_annotation = TextAnnotation(self.current_tool, self.current_color, self.current_thickness)
            self.current_annotation.position = relative_pos
            self.is_drawing = True
            return  # Don't add point, just wait for text input
        elif self.current_tool == ToolType.NUMBER:
            # Number tool - create numbered circle
            print(f"[DEBUG] Creating NUMBER annotation #{self.number_counter}")
            self.current_annotation = NumberAnnotation(self.current_tool, self.current_color, self.current_thickness, self.number_counter)
            self.current_annotation.position = relative_pos
            print(f"[DEBUG] NUMBER position set to: ({relative_pos.x()}, {relative_pos.y()})")
            self.annotations.append(self.current_annotation)
            print(f"[DEBUG] NUMBER annotation appended, total annotations: {len(self.annotations)}")
            self.number_counter += 1
            self.undo_stack.clear()
            self.current_annotation = None
            self.is_drawing = False
            return
            
        if self.current_annotation:
            # Store in relative coordinates (relative to selection area)
            self.current_annotation.add_point(relative_pos)
            print(f"[DEBUG] Added point: ({relative_pos.x()}, {relative_pos.y()})")
            
    def mouse_move(self, pos, offset):
        if self.is_drawing and self.current_annotation:
            # Convert to relative coordinates
            relative_pos = pos - offset
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
            self.annotations.append(self.current_annotation)
            self.undo_stack.clear()
            self.current_annotation = None
            self.is_drawing = False
    
    def add_text_annotation(self, text):
        """Add text to current text annotation and finalize it"""
        if self.current_annotation and isinstance(self.current_annotation, TextAnnotation):
            self.current_annotation.text = text
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
        
        # Create blur by scaling down then up with smooth transformation
        blur_strength = 20  # Reduced from 80 to 20 for more moderate blur
        
        if region.width() > blur_strength and region.height() > blur_strength:
            # Scale down (creates pixelation/blur effect)
            small = region.scaled(
                max(1, region.width() // blur_strength),
                max(1, region.height() // blur_strength),
                Qt.IgnoreAspectRatio,
                Qt.SmoothTransformation
            )
            
            # Scale back up to original size (smooths it out into blur)
            blurred = small.scaled(
                region.width(),
                region.height(),
                Qt.IgnoreAspectRatio,
                Qt.SmoothTransformation
            )
            
            blur_annotation.blurred_pixmap = blurred
        else:
            # For very small regions, just use solid color
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
