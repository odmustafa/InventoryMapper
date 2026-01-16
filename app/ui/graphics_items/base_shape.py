"""
Base class for all shape graphics items.

Provides common functionality for serialization, styling, selection, and interaction.
"""

from typing import Dict, Any, Optional
from PySide6.QtWidgets import QGraphicsItem, QGraphicsSceneMouseEvent
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QPen, QBrush, QColor, QPainter
import json

from app.constants import (
    COLOR_DEFAULT_STROKE,
    COLOR_DEFAULT_FILL,
    COLOR_SELECTED,
    DEFAULT_STROKE_WIDTH,
    DEFAULT_SELECTION_WIDTH,
)


class BaseShapeItem(QGraphicsItem):
    """
    Base class for all drawable shapes on the canvas.

    Provides:
    - Style management (stroke, fill, width)
    - Selection visualization
    - Serialization/deserialization
    - Layer assignment
    - Common properties
    """

    def __init__(self, parent: Optional[QGraphicsItem] = None):
        """
        Initialize base shape item.

        Args:
            parent: Parent graphics item
        """
        super().__init__(parent)

        # Make item selectable and movable
        self.setFlags(
            QGraphicsItem.ItemIsSelectable |
            QGraphicsItem.ItemIsMovable |
            QGraphicsItem.ItemSendsGeometryChanges
        )

        # Style properties
        self._stroke_color = QColor(COLOR_DEFAULT_STROKE)
        self._fill_color = QColor(COLOR_DEFAULT_FILL)
        self._stroke_width = DEFAULT_STROKE_WIDTH

        # Metadata
        self._label = ""
        self._layer_id: Optional[int] = None
        self._shape_id: Optional[int] = None  # Database ID

    # Style Properties

    @property
    def stroke_color(self) -> QColor:
        """Get stroke color."""
        return self._stroke_color

    @stroke_color.setter
    def stroke_color(self, color: QColor):
        """Set stroke color."""
        self._stroke_color = color
        self.update()

    @property
    def fill_color(self) -> QColor:
        """Get fill color."""
        return self._fill_color

    @fill_color.setter
    def fill_color(self, color: QColor):
        """Set fill color."""
        self._fill_color = color
        self.update()

    @property
    def stroke_width(self) -> float:
        """Get stroke width."""
        return self._stroke_width

    @stroke_width.setter
    def stroke_width(self, width: float):
        """Set stroke width."""
        self._stroke_width = width
        self.update()

    @property
    def label(self) -> str:
        """Get label text."""
        return self._label

    @label.setter
    def label(self, text: str):
        """Set label text."""
        self._label = text
        self.update()

    @property
    def layer_id(self) -> Optional[int]:
        """Get layer ID."""
        return self._layer_id

    @layer_id.setter
    def layer_id(self, layer_id: Optional[int]):
        """Set layer ID."""
        self._layer_id = layer_id
        # Also store in item data for scene queries
        self.setData(0, layer_id)

    @property
    def shape_id(self) -> Optional[int]:
        """Get database shape ID."""
        return self._shape_id

    @shape_id.setter
    def shape_id(self, shape_id: Optional[int]):
        """Set database shape ID."""
        self._shape_id = shape_id
        self.setData(1, shape_id)

    # Drawing Methods

    def get_pen(self) -> QPen:
        """
        Get pen for drawing based on selection state.

        Returns:
            QPen configured with current style
        """
        if self.isSelected():
            pen = QPen(COLOR_SELECTED)
            pen.setWidth(DEFAULT_SELECTION_WIDTH)
        else:
            pen = QPen(self._stroke_color)
            pen.setWidthF(self._stroke_width)

        pen.setCosmetic(True)  # Width stays constant regardless of zoom
        return pen

    def get_brush(self) -> QBrush:
        """
        Get brush for filling.

        Returns:
            QBrush configured with fill color
        """
        return QBrush(self._fill_color)

    # Serialization Methods

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize shape to dictionary.

        Returns:
            Dictionary with shape data
        """
        return {
            "type": self.shape_type(),
            "position": {
                "x": self.pos().x(),
                "y": self.pos().y()
            },
            "style": {
                "stroke_color": self._stroke_color.name(),
                "fill_color": self._fill_color.name(),
                "stroke_width": self._stroke_width
            },
            "label": self._label,
            "layer_id": self._layer_id,
            "shape_id": self._shape_id,
            "geometry": self.geometry_to_dict()
        }

    def from_dict(self, data: Dict[str, Any]):
        """
        Deserialize shape from dictionary.

        Args:
            data: Dictionary with shape data
        """
        # Position
        if "position" in data:
            pos = data["position"]
            self.setPos(pos["x"], pos["y"])

        # Style
        if "style" in data:
            style = data["style"]
            self._stroke_color = QColor(style.get("stroke_color", "#000000"))
            self._fill_color = QColor(style.get("fill_color", "#CCCCCC"))
            self._stroke_width = style.get("stroke_width", 2.0)

        # Metadata
        self._label = data.get("label", "")
        self._layer_id = data.get("layer_id")
        self._shape_id = data.get("shape_id")

        # Geometry (implemented by subclasses)
        if "geometry" in data:
            self.geometry_from_dict(data["geometry"])

        self.update()

    def to_json(self) -> str:
        """
        Serialize shape to JSON string.

        Returns:
            JSON string
        """
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "BaseShapeItem":
        """
        Deserialize shape from JSON string.

        Args:
            json_str: JSON string

        Returns:
            Shape instance
        """
        data = json.loads(json_str)
        shape = cls()
        shape.from_dict(data)
        return shape

    # Abstract Methods (to be implemented by subclasses)

    def shape_type(self) -> str:
        """
        Get shape type identifier.

        Returns:
            Shape type string (e.g., "rectangle", "line")
        """
        raise NotImplementedError("Subclasses must implement shape_type()")

    def geometry_to_dict(self) -> Dict[str, Any]:
        """
        Serialize geometry-specific data.

        Returns:
            Dictionary with geometry data
        """
        raise NotImplementedError("Subclasses must implement geometry_to_dict()")

    def geometry_from_dict(self, data: Dict[str, Any]):
        """
        Deserialize geometry-specific data.

        Args:
            data: Dictionary with geometry data
        """
        raise NotImplementedError("Subclasses must implement geometry_from_dict()")

    # Qt Override Methods

    def boundingRect(self) -> QRectF:
        """
        Get bounding rectangle.

        Returns:
            Bounding rectangle
        """
        raise NotImplementedError("Subclasses must implement boundingRect()")

    def paint(self, painter: QPainter, option, widget):
        """
        Paint the shape.

        Args:
            painter: QPainter instance
            option: Style options
            widget: Widget being painted on
        """
        raise NotImplementedError("Subclasses must implement paint()")

    # Interaction Methods

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value):
        """
        Handle item changes.

        Args:
            change: Type of change
            value: New value

        Returns:
            Processed value
        """
        if change == QGraphicsItem.ItemPositionHasChanged:
            # Emit signal if scene supports it
            if self.scene():
                scene = self.scene()
                if hasattr(scene, 'item_moved'):
                    scene.item_moved.emit(self, self.pos(), value)

        return super().itemChange(change, value)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        """
        Handle mouse press.

        Args:
            event: Mouse event
        """
        if event.button() == Qt.LeftButton:
            # Select on left click
            super().mousePressEvent(event)
        else:
            event.ignore()

    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent):
        """
        Handle double click.

        Args:
            event: Mouse event
        """
        if event.button() == Qt.LeftButton:
            # Future: Open properties dialog
            pass
        super().mouseDoubleClickEvent(event)
