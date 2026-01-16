"""
Inventory Marker graphics item for floor plans.

Visual marker representing inventory item position on floor plan.
"""

from typing import Optional, Dict, Any
from PySide6.QtWidgets import QGraphicsItem, QGraphicsEllipseItem, QGraphicsTextItem
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QPen, QBrush, QColor, QPainter, QFont

from app.models.inventory_item import InventoryItem
from app.constants import (
    COLOR_OUT_OF_STOCK,
    COLOR_LOW_STOCK,
    COLOR_IN_STOCK,
    COLOR_SELECTED,
    MARKER_SIZE,
)


class InventoryMarker(QGraphicsItem):
    """
    Visual marker for inventory items on floor plans.

    Shows item position with color-coded status indicator.
    """

    def __init__(self, item: InventoryItem, parent: Optional[QGraphicsItem] = None):
        """
        Initialize inventory marker.

        Args:
            item: Inventory item to represent
            parent: Parent graphics item
        """
        super().__init__(parent)

        self.item = item
        self.placement_id: Optional[int] = None  # Database placement ID

        # Make item selectable and movable
        self.setFlags(
            QGraphicsItem.ItemIsSelectable |
            QGraphicsItem.ItemIsMovable |
            QGraphicsItem.ItemSendsGeometryChanges
        )

        # Set tooltip
        self.setToolTip(self._create_tooltip())

        # Animation state
        self._highlighted = False
        self._pulse_phase = 0

    def _create_tooltip(self) -> str:
        """Create tooltip text for marker."""
        tooltip = f"<b>{self.item.name}</b>"
        if self.item.sku:
            tooltip += f"<br>SKU: {self.item.sku}"
        tooltip += f"<br>Quantity: {self.item.quantity}"
        if self.item.description:
            tooltip += f"<br>{self.item.description[:100]}"
        return tooltip

    def get_marker_color(self) -> QColor:
        """
        Get marker color based on stock status.

        Returns:
            QColor for marker
        """
        if self.isSelected():
            return COLOR_SELECTED

        if self.item.quantity == 0:
            return COLOR_OUT_OF_STOCK
        elif self.item.quantity < self.item.min_stock_level:
            return COLOR_LOW_STOCK
        else:
            return COLOR_IN_STOCK

    def boundingRect(self) -> QRectF:
        """Get bounding rectangle."""
        size = MARKER_SIZE
        return QRectF(-size/2, -size/2, size, size)

    def paint(self, painter: QPainter, option, widget):
        """
        Paint the marker.

        Args:
            painter: QPainter instance
            option: Style options
            widget: Widget being painted on
        """
        # Get color
        color = self.get_marker_color()

        # Draw circle
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(color.darker(120))
        pen.setWidth(2)
        pen.setCosmetic(True)
        painter.setPen(pen)
        painter.setBrush(QBrush(color))

        size = MARKER_SIZE
        painter.drawEllipse(-size/2, -size/2, size, size)

        # Draw inner indicator
        if self._highlighted:
            # Pulsing effect for highlighted items
            pulse_color = QColor(255, 255, 0, 150)
            painter.setBrush(QBrush(pulse_color))
            painter.setPen(Qt.NoPen)
            pulse_size = size * 0.6
            painter.drawEllipse(-pulse_size/2, -pulse_size/2, pulse_size, pulse_size)

        # Draw label below marker
        if not self.isSelected():
            font = QFont()
            font.setPointSize(8)
            font.setBold(True)
            painter.setFont(font)
            painter.setPen(QPen(Qt.black))

            # Draw text with background
            text = self.item.name[:20]  # Truncate long names
            text_rect = QRectF(-30, size/2 + 2, 60, 15)

            # Semi-transparent background
            painter.setBrush(QBrush(QColor(255, 255, 255, 200)))
            painter.setPen(Qt.NoPen)
            painter.drawRect(text_rect)

            # Text
            painter.setPen(QPen(Qt.black))
            painter.drawText(text_rect, Qt.AlignCenter, text)

    def set_highlighted(self, highlighted: bool):
        """
        Set highlighted state for search results.

        Args:
            highlighted: True to highlight, False to remove
        """
        self._highlighted = highlighted
        self.update()

    def get_item_id(self) -> int:
        """Get inventory item ID."""
        return self.item.id

    def update_item(self, item: InventoryItem):
        """
        Update marker with new item data.

        Args:
            item: Updated inventory item
        """
        self.item = item
        self.setToolTip(self._create_tooltip())
        self.update()

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize marker to dictionary.

        Returns:
            Dictionary with placement data
        """
        return {
            "inventory_item_id": self.item.id,
            "x": self.pos().x(),
            "y": self.pos().y(),
            "rotation": self.rotation(),
            "placement_id": self.placement_id
        }

    def mouseDoubleClickEvent(self, event):
        """Handle double-click to show item details."""
        # Emit signal to parent scene if available
        if self.scene():
            scene = self.scene()
            if hasattr(scene, 'inventory_marker_double_clicked'):
                scene.inventory_marker_double_clicked.emit(self.item.id)

        super().mouseDoubleClickEvent(event)
