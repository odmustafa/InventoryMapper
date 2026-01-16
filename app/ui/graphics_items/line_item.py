"""
Line shape graphics item for floor plans.

Used for drawing walls, boundaries, and connections.
"""

from typing import Dict, Any
from PySide6.QtCore import QRectF, QPointF, QLineF
from PySide6.QtGui import QPainter
import math

from app.ui.graphics_items.base_shape import BaseShapeItem
from app.constants import SHAPE_LINE


class LineItem(BaseShapeItem):
    """
    Line shape that can be drawn and manipulated on the canvas.

    Used for representing walls, boundaries, and linear connections.
    """

    def __init__(self, line: QLineF = None, parent=None):
        """
        Initialize line item.

        Args:
            line: Line geometry (start point, end point)
            parent: Parent graphics item
        """
        super().__init__(parent)

        if line is None:
            self._line = QLineF(0, 0, 10, 10)  # Default line
        else:
            self._line = line

    @property
    def line(self) -> QLineF:
        """Get line geometry."""
        return self._line

    @line.setter
    def line(self, line: QLineF):
        """Set line geometry."""
        self.prepareGeometryChange()
        self._line = line
        self.update()

    def set_points(self, p1: QPointF, p2: QPointF):
        """
        Set line endpoints.

        Args:
            p1: Start point
            p2: End point
        """
        self.line = QLineF(p1, p2)

    def shape_type(self) -> str:
        """Get shape type identifier."""
        return SHAPE_LINE

    def geometry_to_dict(self) -> Dict[str, Any]:
        """
        Serialize geometry data.

        Returns:
            Dictionary with line endpoints
        """
        return {
            "x1": self._line.x1(),
            "y1": self._line.y1(),
            "x2": self._line.x2(),
            "y2": self._line.y2()
        }

    def geometry_from_dict(self, data: Dict[str, Any]):
        """
        Deserialize geometry data.

        Args:
            data: Dictionary with line endpoints
        """
        self._line = QLineF(
            data.get("x1", 0),
            data.get("y1", 0),
            data.get("x2", 10),
            data.get("y2", 10)
        )

    def boundingRect(self) -> QRectF:
        """
        Get bounding rectangle with padding for stroke.

        Returns:
            Bounding rectangle
        """
        # Calculate bounding box of line
        padding = self.stroke_width + 2

        x1, y1 = self._line.x1(), self._line.y1()
        x2, y2 = self._line.x2(), self._line.y2()

        left = min(x1, x2) - padding
        top = min(y1, y2) - padding
        right = max(x1, x2) + padding
        bottom = max(y1, y2) + padding

        return QRectF(left, top, right - left, bottom - top)

    def paint(self, painter: QPainter, option, widget):
        """
        Paint the line.

        Args:
            painter: QPainter instance
            option: Style options
            widget: Widget being painted on
        """
        painter.setPen(self.get_pen())
        painter.drawLine(self._line)

        # Draw label at midpoint if exists
        if self._label:
            midpoint = QPointF(
                (self._line.x1() + self._line.x2()) / 2,
                (self._line.y1() + self._line.y2()) / 2
            )
            painter.setPen(self.get_pen())
            painter.drawText(midpoint, self._label)
