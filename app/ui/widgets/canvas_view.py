"""
Canvas View widget - provides pan and zoom functionality for the canvas.

Implements QGraphicsView with mouse-based navigation and zoom controls.
"""

from typing import Optional
from PySide6.QtWidgets import QGraphicsView
from PySide6.QtCore import Qt, QPointF, Signal, QEvent
from PySide6.QtGui import QPainter, QWheelEvent, QMouseEvent, QCursor, QDragEnterEvent, QDragMoveEvent, QDropEvent

from app.constants import MIN_ZOOM, MAX_ZOOM, DEFAULT_ZOOM


class CanvasView(QGraphicsView):
    """
    Custom QGraphicsView for the floor plan canvas.

    Provides pan and zoom functionality:
    - Pan: Middle mouse button drag or Spacebar + Left mouse drag
    - Zoom: Ctrl + Mouse wheel
    - Smooth rendering with antialiasing

    Signals:
        zoom_changed: Emitted when zoom level changes (zoom_factor)
        mouse_position_changed: Emitted when mouse moves (scene_pos)
        inventory_item_dropped: Emitted when inventory item dropped (item_id, scene_pos)
    """

    zoom_changed = Signal(float)
    mouse_position_changed = Signal(QPointF)
    inventory_item_dropped = Signal(int, QPointF)

    def __init__(self, parent=None):
        """
        Initialize canvas view.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        # View configuration
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)
        self.setDragMode(QGraphicsView.NoDrag)

        # Zoom state
        self._zoom_factor = DEFAULT_ZOOM
        self._zoom_step = 1.15  # 15% zoom increment

        # Pan state
        self._panning = False
        self._pan_start_pos = QPointF()
        self._space_pressed = False

        # Enable mouse tracking for position updates
        self.setMouseTracking(True)

        # Enable drag and drop for inventory items
        self.setAcceptDrops(True)

    @property
    def zoom_factor(self) -> float:
        """Get current zoom factor."""
        return self._zoom_factor

    def zoom_in(self):
        """Zoom in by one step."""
        new_zoom = min(self._zoom_factor * self._zoom_step, MAX_ZOOM)
        self.set_zoom(new_zoom)

    def zoom_out(self):
        """Zoom out by one step."""
        new_zoom = max(self._zoom_factor / self._zoom_step, MIN_ZOOM)
        self.set_zoom(new_zoom)

    def zoom_fit(self):
        """Fit the entire scene in the view."""
        if self.scene():
            self.fitInView(self.scene().sceneRect(), Qt.KeepAspectRatio)
            # Calculate zoom factor based on transform
            self._zoom_factor = self.transform().m11()
            self.zoom_changed.emit(self._zoom_factor)

    def set_zoom(self, zoom_factor: float):
        """
        Set zoom to a specific factor.

        Args:
            zoom_factor: Zoom factor (1.0 = 100%)
        """
        # Clamp zoom factor
        zoom_factor = max(MIN_ZOOM, min(zoom_factor, MAX_ZOOM))

        if zoom_factor == self._zoom_factor:
            return

        # Calculate scale factor needed
        scale = zoom_factor / self._zoom_factor

        # Apply transform
        self.scale(scale, scale)

        # Update zoom factor
        self._zoom_factor = zoom_factor
        self.zoom_changed.emit(self._zoom_factor)

    def reset_zoom(self):
        """Reset zoom to 100%."""
        self.set_zoom(DEFAULT_ZOOM)

    def wheelEvent(self, event: QWheelEvent):
        """
        Handle mouse wheel events for zooming.

        Args:
            event: Wheel event
        """
        # Only zoom with Ctrl key
        if event.modifiers() & Qt.ControlModifier:
            # Get wheel delta (positive = zoom in, negative = zoom out)
            delta = event.angleDelta().y()

            if delta > 0:
                self.zoom_in()
            else:
                self.zoom_out()

            event.accept()
        else:
            # Default scroll behavior
            super().wheelEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        """
        Handle mouse press events.

        Args:
            event: Mouse event
        """
        # Middle mouse button or Space + Left button for panning
        if event.button() == Qt.MiddleButton or (
            event.button() == Qt.LeftButton and self._space_pressed
        ):
            self._panning = True
            self._pan_start_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
        else:
            # Pass to scene for item interaction
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        """
        Handle mouse move events.

        Args:
            event: Mouse event
        """
        # Update cursor position in scene coordinates
        scene_pos = self.mapToScene(event.pos())
        self.mouse_position_changed.emit(scene_pos)

        if self._panning:
            # Calculate pan delta
            delta = event.pos() - self._pan_start_pos
            self._pan_start_pos = event.pos()

            # Update scrollbars
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta.x()
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta.y()
            )
            event.accept()
        else:
            # Update cursor if space is pressed
            if self._space_pressed:
                self.setCursor(Qt.OpenHandCursor)

            # Pass to scene
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """
        Handle mouse release events.

        Args:
            event: Mouse event
        """
        if event.button() == Qt.MiddleButton or (
            event.button() == Qt.LeftButton and self._panning
        ):
            self._panning = False
            self.setCursor(Qt.ArrowCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        """
        Handle key press events.

        Args:
            event: Key event
        """
        if event.key() == Qt.Key_Space and not self._space_pressed:
            self._space_pressed = True
            if not self._panning:
                self.setCursor(Qt.OpenHandCursor)
            event.accept()
        else:
            super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        """
        Handle key release events.

        Args:
            event: Key event
        """
        if event.key() == Qt.Key_Space:
            self._space_pressed = False
            if not self._panning:
                self.setCursor(Qt.ArrowCursor)
            event.accept()
        else:
            super().keyReleaseEvent(event)

    def enterEvent(self, event: QEvent):
        """
        Handle mouse entering the view.

        Args:
            event: Enter event
        """
        # Set focus to receive keyboard events
        self.setFocus()
        super().enterEvent(event)

    def leaveEvent(self, event: QEvent):
        """
        Handle mouse leaving the view.

        Args:
            event: Leave event
        """
        # Reset panning state
        self._panning = False
        self._space_pressed = False
        self.setCursor(Qt.ArrowCursor)
        super().leaveEvent(event)

    def get_visible_rect(self):
        """
        Get the visible rectangle in scene coordinates.

        Returns:
            QRectF of visible area
        """
        return self.mapToScene(self.viewport().rect()).boundingRect()

    def center_on_point(self, point: QPointF):
        """
        Center the view on a specific point.

        Args:
            point: Point in scene coordinates
        """
        self.centerOn(point)

    def ensure_visible_point(self, point: QPointF, margin: int = 50):
        """
        Ensure a point is visible in the view with margin.

        Args:
            point: Point in scene coordinates
            margin: Margin in pixels
        """
        self.ensureVisible(point.x(), point.y(), margin, margin)

    def dragEnterEvent(self, event: QDragEnterEvent):
        """
        Handle drag enter events for inventory items.

        Args:
            event: Drag enter event
        """
        # Accept inventory item drags
        if event.mimeData().hasFormat("application/x-inventory-item-id"):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent):
        """
        Handle drag move events for inventory items.

        Args:
            event: Drag move event
        """
        # Accept inventory item drags
        if event.mimeData().hasFormat("application/x-inventory-item-id"):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        """
        Handle drop events for inventory items.

        Args:
            event: Drop event
        """
        # Extract item ID from mime data
        if event.mimeData().hasFormat("application/x-inventory-item-id"):
            item_id_bytes = event.mimeData().data("application/x-inventory-item-id")
            item_id = int(item_id_bytes.data().decode())

            # Convert drop position to scene coordinates
            scene_pos = self.mapToScene(event.pos())

            # Emit signal for MainWindow to handle
            self.inventory_item_dropped.emit(item_id, scene_pos)

            event.acceptProposedAction()
        else:
            event.ignore()
