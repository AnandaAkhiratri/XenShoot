"""
Screenshot overlay with annotation tools
"""

from PyQt5.QtWidgets import QWidget, QApplication, QLabel
from PyQt5.QtCore import Qt, QRect, QPoint, pyqtSignal
from PyQt5.QtGui import QPainter, QPixmap, QColor, QPen, QCursor, QScreen, QBrush, QKeyEvent
from .annotation_tools import AnnotationManager
from .toolbar import Toolbar
from .uploader import ImageUploader


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
            Qt.FramelessWindowHint | 
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
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
        self.is_moving_selection = False  # NEW: for move mode
        self.move_start_pos = QPoint()  # NEW: starting position for move
        
        self.annotation_manager = AnnotationManager()
        self.toolbar = None
        self.size_indicator = None  # NEW: Size indicator label
        self.text_input = None  # For inline text input
        self.uploader = ImageUploader(self.config)
        
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
        
        # Draw dark overlay
        painter.fillRect(self.rect(), QColor(0, 0, 0, 100))
        
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
            
            # Draw selection border - solid and bold
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)  # Ensure normal mode
            painter.setPen(QPen(QColor(245, 203, 17), 3))  # Thicker border (3px) - Yellow/Gold
            painter.setBrush(Qt.NoBrush)  # No fill for border
            painter.drawRect(self.selection_rect)
            
            # Draw corner handles - SOLID BLUE squares (tebal/filled)
            painter.save()  # Save painter state
            
            handle_size = 10  # Larger handles
            
            # Draw each handle as solid blue filled rectangle
            handles_positions = [
                # Top-left
                (self.selection_rect.x() - handle_size // 2, 
                 self.selection_rect.y() - handle_size // 2),
                # Top-right
                (self.selection_rect.x() + self.selection_rect.width() - handle_size // 2,
                 self.selection_rect.y() - handle_size // 2),
                # Bottom-left
                (self.selection_rect.x() - handle_size // 2,
                 self.selection_rect.y() + self.selection_rect.height() - handle_size // 2),
                # Bottom-right
                (self.selection_rect.x() + self.selection_rect.width() - handle_size // 2,
                 self.selection_rect.y() + self.selection_rect.height() - handle_size // 2),
            ]
            
            for x, y in handles_positions:
                # Fill with SOLID BLUE - no transparency!
                painter.fillRect(x, y, handle_size, handle_size, QColor(245, 203, 17))  # Yellow/Gold handles
            
            painter.restore()  # Restore painter state
            
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
            if not self.is_editing:
                # Start selection
                self.is_selecting = True
                self.start_point = event.pos()
                self.end_point = event.pos()
            elif self.is_moving_selection:
                # Start moving selection
                self.move_start_pos = event.pos()
            else:
                # Check if TEXT tool is selected - show text input
                from .annotation_tools import ToolType
                if self.annotation_manager.current_tool == ToolType.TEXT:
                    self.show_text_input_dialog(event.pos())
                else:
                    # Annotation tool interaction
                    self.annotation_manager.mouse_press(event.pos(), self.selection_rect.topLeft())
                self.update()
        elif event.button() == Qt.RightButton:
            if self.is_editing:
                # Cancel or go back to selection
                self.cancel_capture()
                
    def mouseMoveEvent(self, event):
        if self.is_selecting:
            self.end_point = event.pos()
            self.selection_rect = QRect(self.start_point, self.end_point).normalized()
            self.update()
        elif self.is_moving_selection and self.is_editing:
            # Move the selection rect
            delta = event.pos() - self.move_start_pos
            self.selection_rect.translate(delta)
            self.move_start_pos = event.pos()
            
            # Reposition toolbar and size indicator
            if self.toolbar:
                self.position_toolbar()
            
            self.update()
        elif self.is_editing:
            self.annotation_manager.mouse_move(event.pos(), self.selection_rect.topLeft())
            self.update()
            
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.is_selecting:
                self.is_selecting = False
                if self.selection_rect.width() > 10 and self.selection_rect.height() > 10:
                    self.start_editing()
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
        # Handle ESC for text input cancellation
        if event.key() == Qt.Key_Escape:
            if self.text_input and self.text_input.isVisible():
                # Cancel text input
                self.text_input.close()
                self.text_input = None
                self.annotation_manager.current_annotation = None
                self.annotation_manager.is_drawing = False
                self.update()
            else:
                self.cancel_capture()
        elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            # Don't finish capture if text input is active
            if self.text_input and self.text_input.isVisible():
                return  # Let text input handle it
            elif self.is_editing:
                self.finish_capture()
        elif event.key() == Qt.Key_Z and event.modifiers() == Qt.ControlModifier:
            if self.is_editing:
                self.annotation_manager.undo()
                self.update()
        elif event.key() == Qt.Key_Y and event.modifiers() == Qt.ControlModifier:
            if self.is_editing:
                self.annotation_manager.redo()
                self.update()
                
    def start_editing(self):
        """Start annotation mode"""
        self.is_editing = True
        self.setCursor(Qt.ArrowCursor)
        
        # Show toolbar
        if self.toolbar is None:
            self.toolbar = Toolbar(self, self.annotation_manager)
            
        # Position toolbar at bottom of selection
        self.position_toolbar()
        self.toolbar.show()
        
        # Create and show size indicator
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
            size_text = f"{self.selection_rect.width()} × {self.selection_rect.height()}"
            self.size_indicator.setText(size_text)
            self.size_indicator.adjustSize()
            
            # Position above toolbar, centered
            if self.toolbar:
                indicator_x = self.selection_rect.center().x() - self.size_indicator.width() // 2
                indicator_y = self.selection_rect.top() - self.size_indicator.height() - 8
                
                # Keep on screen
                if indicator_y < 10:
                    indicator_y = self.selection_rect.top() + 10
                    
                self.size_indicator.move(indicator_x, indicator_y)
                self.size_indicator.show()
                
    def position_toolbar(self):
        """Position toolbar centered below selection box"""
        if self.toolbar is None:
            return
        
        # Make sure toolbar geometry is updated
        self.toolbar.adjustSize()
        self.toolbar.updateGeometry()
        
        # Center horizontally relative to selection box
        toolbar_x = self.selection_rect.center().x() - self.toolbar.width() // 2
        toolbar_y = self.selection_rect.bottom() + 10  # 10px below selection
        
        # If toolbar goes off screen bottom, put it above selection
        if toolbar_y + self.toolbar.height() > self.height():
            toolbar_y = self.selection_rect.top() - self.toolbar.height() - 10
            
        self.toolbar.move(toolbar_x, toolbar_y)
        
    def finish_capture(self):
        """Finish capture and upload"""
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
        """Save screenshot to local folder"""
        import os
        from datetime import datetime
        
        save_path = self.config.get('local_save_path', '')
        if not save_path:
            from pathlib import Path
            save_path = str(Path.home() / "Pictures" / "XenShoot")
        
        # Create directory if not exists
        os.makedirs(save_path, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"xenshoot_{timestamp}.png"
        filepath = os.path.join(save_path, filename)
        
        # Save
        pixmap.save(filepath, "PNG")
        
    def copy_to_clipboard(self):
        """Copy screenshot with annotations to clipboard"""
        from PyQt5.QtWidgets import QApplication
        
        try:
            # Create final image with annotations
            final_pixmap = QPixmap(self.selection_rect.size())
            final_pixmap.fill(Qt.white)
            
            painter = QPainter(final_pixmap)
            # Draw screenshot
            painter.drawPixmap(0, 0, self.screen_pixmap.copy(self.selection_rect))
            
            # Draw annotations (translate to selection origin)
            painter.translate(-self.selection_rect.topLeft())
            self.annotation_manager.draw(painter, self.selection_rect.topLeft())
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
        try:
            # Create final image with annotations
            final_pixmap = QPixmap(self.selection_rect.size())
            final_pixmap.fill(Qt.white)
            
            painter = QPainter(final_pixmap)
            # Draw screenshot
            painter.drawPixmap(0, 0, self.screen_pixmap.copy(self.selection_rect))
            
            # Draw annotations
            painter.translate(-self.selection_rect.topLeft())
            self.annotation_manager.draw(painter, self.selection_rect.topLeft())
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
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QListWidget, QPushButton, QMessageBox, QListWidgetItem, QLabel
        import os
        import subprocess
        
        try:
            # Create final image with annotations
            final_pixmap = QPixmap(self.selection_rect.size())
            final_pixmap.fill(Qt.white)
            
            painter = QPainter(final_pixmap)
            painter.drawPixmap(0, 0, self.screen_pixmap.copy(self.selection_rect))
            painter.translate(-self.selection_rect.topLeft())
            self.annotation_manager.draw(painter, self.selection_rect.topLeft())
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
        # Cleanup text input if exists
        if self.text_input:
            self.text_input.close()
            self.text_input = None
        
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
        """Show inline text input at click position"""
        from PyQt5.QtWidgets import QLineEdit
        from .annotation_tools import ToolType
        
        # Create text annotation first
        offset = self.selection_rect.topLeft()
        self.annotation_manager.mouse_press(pos, offset)
        
        if not self.annotation_manager.current_annotation:
            return
        
        text_annotation = self.annotation_manager.current_annotation
        relative_pos = text_annotation.position
        screen_pos = relative_pos + self.selection_rect.topLeft()
        
        color = self.annotation_manager.current_color
        
        # Create inline text input
        self.text_input = QLineEdit(self)
        self.text_input.setWindowFlags(Qt.Widget)
        self.text_input.setAttribute(Qt.WA_DeleteOnClose, False)
        self.text_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: transparent;
                color: {color.name()};
                border: none;
                padding: 0px;
                font-size: 32px;
                font-weight: normal;
                font-family: Arial;
                selection-background-color: rgba(52, 152, 219, 100);
                selection-color: white;
            }}
        """)
        
        self.text_input.move(screen_pos.x(), screen_pos.y())
        self.text_input.setMinimumWidth(200)
        self.text_input.raise_()
        self.text_input.show()
        self.text_input.setFocus()
        self.text_input.activateWindow()
        
        # Connect to finish method
        self.text_input.returnPressed.connect(self.finish_text_input)
    
    def finish_text_input(self):
        """Finish text input and add to annotations"""
        if not self.text_input or not self.annotation_manager.current_annotation:
            return
        
        text = self.text_input.text().strip()
        
        # Disconnect signal first to prevent double-trigger
        try:
            self.text_input.returnPressed.disconnect(self.finish_text_input)
        except:
            pass
        
        # Close and cleanup text input
        self.text_input.close()
        self.text_input = None
        
        if text:
            # Add text to annotation
            self.annotation_manager.add_text_annotation(text)
        else:
            # Cancel if empty text
            self.annotation_manager.current_annotation = None
            self.annotation_manager.is_drawing = False
        
        self.update()