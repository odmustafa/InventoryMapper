"""
Canvas Scene widget - manages the drawing canvas using QGraphicsScene.

Handles all graphics items, layers, grid rendering, and selection management.
"""

from typing import List, Optional, Dict
from PySide6.QtWidgets import QGraphicsScene, QGraphicsItem
from PySide6.QtCore import Qt, QPointF, QRectF, Signal, QObject
from PySide6.QtGui import QPen, QBrush, QPainter, QColor

from app.constants import (
    COLOR_GRID,
    COLOR_BACKGROUND,
    DEFAULT_CANVAS_WIDTH,
    DEFAULT_CANVAS_HEIGHT,
    DEFAULT_GRID_SIZE,
)


class CanvasScene(QGraphicsScene):
    """
    Custom QGraphicsScene for the floor plan canvas.

    Manages graphics items, handles layer visibility, renders grid,
    and provides snapping functionality.

    Signals:
        item_added: Emitted when an item is added to the scene
        item_moved: Emitted when an item is moved (item, old_pos, new_pos)
        selection_changed_signal: Emitted when selection changes
    """

    item_added = Signal(QGraphicsItem)
    item_moved = Signal(QGraphicsItem, QPointF, QPointF)
    selection_changed_signal = Signal(list)
    inventory_marker_double_clicked = Signal(int)  # item_id

    def __init__(
        self,
        width: float = DEFAULT_CANVAS_WIDTH,
        height: float = DEFAULT_CANVAS_HEIGHT,
        unit: str = "feet",
        parent: Optional[QObject] = None
    ):
        """
        Initialize canvas scene.

        Args:
            width: Scene width in real-world units
            height: Scene height in real-world units
            unit: Measurement unit ('feet', 'meters', etc.)
            parent: Parent QObject
        """
        super().__init__(parent)

        # Set scene dimensions
        self.setSceneRect(0, 0, width, height)

        # Configuration
        self.unit = unit
        self.grid_size = DEFAULT_GRID_SIZE
        self.grid_visible = True
        self.snap_enabled = True

        # Layer management
        self.current_layer_id: Optional[int] = None
        self.layer_visibility: Dict[int, bool] = {}

        # Background
        self.setBackgroundBrush(QBrush(COLOR_BACKGROUND))

        # Connect selection changed signal
        self.selectionChanged.connect(self._on_selection_changed)

    def drawBackground(self, painter: QPainter, rect: QRectF):
        """
        Draw the background with optional grid.

        Args:
            painter: QPainter instance
            rect: Rectangle to draw
        """
        # Call parent to draw background color
        super().drawBackground(painter, rect)

        if not self.grid_visible:
            return

        # Draw grid
        painter.save()

        # Set grid pen
        pen = QPen(COLOR_GRID)
        pen.setWidth(1)
        pen.setCosmetic(True)  # Width stays constant regardless of zoom
        painter.setPen(pen)

        # Calculate grid bounds
        left = int(rect.left() - (rect.left() % self.grid_size))
        top = int(rect.top() - (rect.top() % self.grid_size))
        right = int(rect.right())
        bottom = int(rect.bottom())

        # Draw vertical lines
        x = left
        while x <= right:
            painter.drawLine(int(x), int(rect.top()), int(x), int(rect.bottom()))
            x += self.grid_size

        # Draw horizontal lines
        y = top
        while y <= bottom:
            painter.drawLine(int(rect.left()), int(y), int(rect.right()), int(y))
            y += self.grid_size

        painter.restore()

    def snap_to_grid(self, point: QPointF) -> QPointF:
        """
        Snap a point to the grid.

        Args:
            point: Point to snap

        Returns:
            Snapped point if snap_enabled, otherwise original point
        """
        if not self.snap_enabled or self.grid_size == 0:
            return point

        snapped_x = round(point.x() / self.grid_size) * self.grid_size
        snapped_y = round(point.y() / self.grid_size) * self.grid_size
        return QPointF(snapped_x, snapped_y)

    def set_grid_visible(self, visible: bool):
        """
        Set grid visibility.

        Args:
            visible: True to show grid, False to hide
        """
        self.grid_visible = visible
        self.invalidate(self.sceneRect(), QGraphicsScene.BackgroundLayer)

    def set_grid_size(self, size: float):
        """
        Set grid size.

        Args:
            size: Grid size in scene units
        """
        self.grid_size = size
        if self.grid_visible:
            self.invalidate(self.sceneRect(), QGraphicsScene.BackgroundLayer)

    def set_snap_enabled(self, enabled: bool):
        """
        Enable or disable snapping to grid.

        Args:
            enabled: True to enable snapping, False to disable
        """
        self.snap_enabled = enabled

    def add_item_to_layer(self, item: QGraphicsItem, layer_id: Optional[int] = None):
        """
        Add an item to the scene and associate it with a layer.

        Args:
            item: Graphics item to add
            layer_id: Layer ID to add item to (None for default)
        """
        self.addItem(item)

        # Store layer ID in item data
        if layer_id is not None:
            item.setData(0, layer_id)  # Store layer ID at key 0

        # Apply layer visibility
        if layer_id in self.layer_visibility:
            item.setVisible(self.layer_visibility[layer_id])

        self.item_added.emit(item)

    def set_layer_visibility(self, layer_id: int, visible: bool):
        """
        Set visibility for all items in a layer.

        Args:
            layer_id: Layer ID
            visible: True to show, False to hide
        """
        self.layer_visibility[layer_id] = visible

        # Update all items in this layer
        for item in self.items():
            if item.data(0) == layer_id:
                item.setVisible(visible)

    def get_items_in_layer(self, layer_id: int) -> List[QGraphicsItem]:
        """
        Get all items in a specific layer.

        Args:
            layer_id: Layer ID

        Returns:
            List of graphics items in the layer
        """
        return [item for item in self.items() if item.data(0) == layer_id]

    def remove_layer_items(self, layer_id: int):
        """
        Remove all items from a layer.

        Args:
            layer_id: Layer ID
        """
        items = self.get_items_in_layer(layer_id)
        for item in items:
            self.removeItem(item)

    def set_current_layer(self, layer_id: Optional[int]):
        """
        Set the current active layer for new items.

        Args:
            layer_id: Layer ID or None
        """
        self.current_layer_id = layer_id

    def _on_selection_changed(self):
        """Handle selection changed event."""
        selected = self.selectedItems()
        self.selection_changed_signal.emit(selected)

    def get_selected_items(self) -> List[QGraphicsItem]:
        """
        Get currently selected items.

        Returns:
            List of selected graphics items
        """
        return self.selectedItems()

    def clear_selection(self):
        """Clear all selected items."""
        self.clearSelection()

    def select_items(self, items: List[QGraphicsItem]):
        """
        Select specific items.

        Args:
            items: List of items to select
        """
        self.clearSelection()
        for item in items:
            item.setSelected(True)

    def delete_selected_items(self):
        """Delete all currently selected items."""
        selected = self.selectedItems()
        for item in selected:
            self.removeItem(item)

    def get_bounds(self) -> QRectF:
        """
        Get bounding rectangle of all items.

        Returns:
            Bounding rectangle
        """
        return self.itemsBoundingRect()

    def set_dimensions(self, width: float, height: float):
        """
        Set scene dimensions.

        Args:
            width: Scene width in units
            height: Scene height in units
        """
        self.setSceneRect(0, 0, width, height)

    def batch_add_items(self, items: List[QGraphicsItem], layer_id: Optional[int] = None):
        """
        Add multiple items efficiently with signals blocked.

        Args:
            items: List of graphics items to add
            layer_id: Layer ID for all items
        """
        # Block signals during bulk operation for performance
        self.blockSignals(True)
        try:
            for item in items:
                self.add_item_to_layer(item, layer_id)
        finally:
            self.blockSignals(False)

        # Emit one update signal
        self.update()
