"""
Polygon shape graphics item for floor plans.

Used for drawing irregular rooms, zones, and custom shapes.
"""

from typing import Dict, Any, List
from PySide6.QtCore import QRectF, QPointF
from PySide6.QtGui import QPainter, QPolygonF

from app.ui.graphics_items.base_shape import BaseShapeItem
from app.constants import SHAPE_POLYGON


class PolygonItem(BaseShapeItem):
    """
    Polygon shape that can be drawn and manipulated on the canvas.

    Used for representing irregular rooms, zones, and custom multi-point shapes.
    """

    def __init__(self, points: List[QPointF] = None, parent=None):
        """
        Initialize polygon item.

        Args:
            points: List of polygon vertices
            parent: Parent graphics item
        """
        super().__init__(parent)

        if points is None or len(points) < 3:
            # Default triangle
            self._polygon = QPolygonF([
                QPointF(0, 0),
                QPointF(10, 0),
                QPointF(5, 10)
            ])
        else:
            self._polygon = QPolygonF(points)

    @property
    def polygon(self) -> QPolygonF:
        """Get polygon geometry."""
        return self._polygon

    @polygon.setter
    def polygon(self, polygon: QPolygonF):
        """Set polygon geometry."""
        self.prepareGeometryChange()
        self._polygon = polygon
        self.update()

    def set_points(self, points: List[QPointF]):
        """
        Set polygon vertices.

        Args:
            points: List of polygon vertices (minimum 3)
        """
        if len(points) >= 3:
            self.polygon = QPolygonF(points)

    def add_point(self, point: QPointF):
        """
        Add a vertex to the polygon.

        Args:
            point: Vertex to add
        """
        self.prepareGeometryChange()
        self._polygon.append(point)
        self.update()

    def remove_last_point(self):
        """Remove the last vertex from the polygon."""
        if len(self._polygon) > 3:
            self.prepareGeometryChange()
            self._polygon.removeLast()
            self.update()

    def shape_type(self) -> str:
        """Get shape type identifier."""
        return SHAPE_POLYGON

    def geometry_to_dict(self) -> Dict[str, Any]:
        """
        Serialize geometry data.

        Returns:
            Dictionary with polygon vertices
        """
        points = []
        for i in range(len(self._polygon)):
            point = self._polygon[i]
            points.append({"x": point.x(), "y": point.y()})

        return {"points": points}

    def geometry_from_dict(self, data: Dict[str, Any]):
        """
        Deserialize geometry data.

        Args:
            data: Dictionary with polygon vertices
        """
        points = []
        for point_data in data.get("points", []):
            points.append(QPointF(point_data["x"], point_data["y"]))

        if len(points) >= 3:
            self._polygon = QPolygonF(points)
        else:
            # Default triangle if invalid data
            self._polygon = QPolygonF([
                QPointF(0, 0),
                QPointF(10, 0),
                QPointF(5, 10)
            ])

    def boundingRect(self) -> QRectF:
        """
        Get bounding rectangle with padding for stroke.

        Returns:
            Bounding rectangle
        """
        # Get bounding rect from polygon
        rect = self._polygon.boundingRect()

        # Add padding for stroke width
        padding = self.stroke_width + 2
        return rect.adjusted(-padding, -padding, padding, padding)

    def paint(self, painter: QPainter, option, widget):
        """
        Paint the polygon.

        Args:
            painter: QPainter instance
            option: Style options
            widget: Widget being painted on
        """
        painter.setPen(self.get_pen())
        painter.setBrush(self.get_brush())
        painter.drawPolygon(self._polygon)

        # Draw label at centroid if exists
        if self._label:
            # Calculate centroid
            centroid_x = sum(self._polygon[i].x() for i in range(len(self._polygon))) / len(self._polygon)
            centroid_y = sum(self._polygon[i].y() for i in range(len(self._polygon))) / len(self._polygon)

            painter.setPen(self.get_pen())
            painter.drawText(QPointF(centroid_x, centroid_y), self._label)
