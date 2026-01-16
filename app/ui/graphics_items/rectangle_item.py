"""
Rectangle shape graphics item for floor plans.

Used for drawing walls, rooms, furniture, and rectangular zones.
"""

from typing import Dict, Any
from PySide6.QtCore import QRectF, QPointF
from PySide6.QtGui import QPainter

from app.ui.graphics_items.base_shape import BaseShapeItem
from app.constants import SHAPE_RECTANGLE


class RectangleItem(BaseShapeItem):
    """
    Rectangle shape that can be drawn and manipulated on the canvas.

    Used for representing rooms, walls, furniture, and rectangular zones.
    """

    def __init__(self, rect: QRectF = None, parent=None):
        """
        Initialize rectangle item.

        Args:
            rect: Rectangle dimensions (x, y, width, height)
            parent: Parent graphics item
        """
        super().__init__(parent)

        if rect is None:
            self._rect = QRectF(0, 0, 10, 10)  # Default size
        else:
            self._rect = rect

    @property
    def rect(self) -> QRectF:
        """Get rectangle geometry."""
        return self._rect

    @rect.setter
    def rect(self, rect: QRectF):
        """Set rectangle geometry."""
        self.prepareGeometryChange()
        self._rect = rect
        self.update()

    def set_dimensions(self, x: float, y: float, width: float, height: float):
        """
        Set rectangle dimensions.

        Args:
            x: Top-left X coordinate
            y: Top-left Y coordinate
            width: Rectangle width
            height: Rectangle height
        """
        self.rect = QRectF(x, y, width, height)

    def shape_type(self) -> str:
        """Get shape type identifier."""
        return SHAPE_RECTANGLE

    def geometry_to_dict(self) -> Dict[str, Any]:
        """
        Serialize geometry data.

        Returns:
            Dictionary with rectangle dimensions
        """
        return {
            "x": self._rect.x(),
            "y": self._rect.y(),
            "width": self._rect.width(),
            "height": self._rect.height()
        }

    def geometry_from_dict(self, data: Dict[str, Any]):
        """
        Deserialize geometry data.

        Args:
            data: Dictionary with rectangle dimensions
        """
        self._rect = QRectF(
            data.get("x", 0),
            data.get("y", 0),
            data.get("width", 10),
            data.get("height", 10)
        )

    def boundingRect(self) -> QRectF:
        """
        Get bounding rectangle with padding for stroke.

        Returns:
            Bounding rectangle
        """
        # Add padding for stroke width
        padding = self.stroke_width + 2
        return self._rect.adjusted(-padding, -padding, padding, padding)

    def paint(self, painter: QPainter, option, widget):
        """
        Paint the rectangle.

        Args:
            painter: QPainter instance
            option: Style options
            widget: Widget being painted on
        """
        painter.setPen(self.get_pen())
        painter.setBrush(self.get_brush())
        painter.drawRect(self._rect)

        # Draw label if exists
        if self._label:
            painter.setPen(self.get_pen())
            painter.drawText(
                self._rect,
                int(painter.pen().color().darker().rgba()),
                self._label
            )
