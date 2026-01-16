"""
Drawing Controller - manages drawing tools and operations.

Coordinates between UI, graphics items, and database for drawing floor plans.
"""

from typing import Optional, List
from enum import Enum

from PySide6.QtCore import QObject, Signal, QPointF, QRectF
from PySide6.QtGui import QColor

from app.ui.graphics_items.rectangle_item import RectangleItem
from app.ui.graphics_items.line_item import LineItem
from app.ui.graphics_items.polygon_item import PolygonItem
from app.ui.widgets.canvas_scene import CanvasScene
from app.models.floor_plan import FloorPlan
from app.models.shape import Shape
from app.constants import SHAPE_RECTANGLE, SHAPE_LINE, SHAPE_POLYGON


class DrawingTool(Enum):
    """Enum for drawing tool types."""
    SELECT = "select"
    RECTANGLE = "rectangle"
    LINE = "line"
    POLYGON = "polygon"


class DrawingController(QObject):
    """
    Controller for drawing operations on the canvas.

    Manages:
    - Current drawing tool
    - Creating and manipulating shapes
    - Saving shapes to database
    - Loading shapes from database
    """

    tool_changed = Signal(DrawingTool)
    shape_created = Signal(object)  # BaseShapeItem
    shape_modified = Signal(object)  # BaseShapeItem

    def __init__(self, scene: Optional[CanvasScene] = None):
        """
        Initialize drawing controller.

        Args:
            scene: Canvas scene to draw on
        """
        super().__init__()

        self.scene = scene
        self.current_tool = DrawingTool.SELECT
        self.current_floor_plan: Optional[FloorPlan] = None
        self.current_layer_id: Optional[int] = None

        # Drawing state
        self.drawing_in_progress = False
        self.temp_shape = None  # Temporary shape being drawn
        self.polygon_points: List[QPointF] = []

        # Style settings
        self.stroke_color = QColor("#000000")
        self.fill_color = QColor("#CCCCCC")
        self.stroke_width = 2.0

    def set_scene(self, scene: CanvasScene):
        """
        Set the canvas scene.

        Args:
            scene: Canvas scene
        """
        self.scene = scene

    def set_tool(self, tool: DrawingTool):
        """
        Set active drawing tool.

        Args:
            tool: Drawing tool to activate
        """
        # Cancel any drawing in progress
        self.cancel_drawing()

        self.current_tool = tool
        self.tool_changed.emit(tool)

    def set_floor_plan(self, floor_plan: FloorPlan):
        """
        Set current floor plan.

        Args:
            floor_plan: Floor plan to work with
        """
        self.current_floor_plan = floor_plan

    def set_current_layer(self, layer_id: Optional[int]):
        """
        Set current layer for new shapes.

        Args:
            layer_id: Layer ID
        """
        self.current_layer_id = layer_id

    def start_shape(self, start_point: QPointF):
        """
        Start drawing a new shape.

        Args:
            start_point: Starting point in scene coordinates
        """
        if not self.scene or self.current_tool == DrawingTool.SELECT:
            return

        # Snap to grid if enabled
        start_point = self.scene.snap_to_grid(start_point)

        if self.current_tool == DrawingTool.RECTANGLE:
            # Create temporary rectangle
            rect = QRectF(start_point, start_point)
            self.temp_shape = RectangleItem(rect)
            self._apply_current_style(self.temp_shape)
            self.scene.addItem(self.temp_shape)
            self.drawing_in_progress = True

        elif self.current_tool == DrawingTool.LINE:
            # Create temporary line
            from PySide6.QtCore import QLineF
            line = QLineF(start_point, start_point)
            self.temp_shape = LineItem(line)
            self._apply_current_style(self.temp_shape)
            self.scene.addItem(self.temp_shape)
            self.drawing_in_progress = True

        elif self.current_tool == DrawingTool.POLYGON:
            if not self.drawing_in_progress:
                # Start new polygon
                self.polygon_points = [start_point]
                self.drawing_in_progress = True
            else:
                # Add point to existing polygon
                self.polygon_points.append(start_point)
                if self.temp_shape:
                    self.scene.removeItem(self.temp_shape)

                # Create/update temporary polygon
                if len(self.polygon_points) >= 2:
                    # Show preview with at least 2 points
                    preview_points = self.polygon_points.copy()
                    if len(preview_points) == 2:
                        # Add a third point to make it valid
                        preview_points.append(start_point)

                    self.temp_shape = PolygonItem(preview_points)
                    self._apply_current_style(self.temp_shape)
                    self.scene.addItem(self.temp_shape)

    def update_shape(self, current_point: QPointF):
        """
        Update shape being drawn.

        Args:
            current_point: Current mouse position in scene coordinates
        """
        if not self.drawing_in_progress or not self.temp_shape:
            return

        # Snap to grid if enabled
        if self.scene:
            current_point = self.scene.snap_to_grid(current_point)

        if self.current_tool == DrawingTool.RECTANGLE:
            # Update rectangle
            rect = QRectF(
                self.temp_shape.rect.topLeft(),
                current_point
            ).normalized()
            self.temp_shape.rect = rect

        elif self.current_tool == DrawingTool.LINE:
            # Update line
            from PySide6.QtCore import QLineF
            line = QLineF(self.temp_shape.line.p1(), current_point)
            self.temp_shape.line = line

    def finish_shape(self):
        """Finish drawing current shape and save it."""
        if not self.drawing_in_progress or not self.temp_shape:
            return

        if self.current_tool in [DrawingTool.RECTANGLE, DrawingTool.LINE]:
            # Finalize rectangle or line
            self.temp_shape.layer_id = self.current_layer_id
            self._save_shape_to_database(self.temp_shape)
            self.shape_created.emit(self.temp_shape)

            self.temp_shape = None
            self.drawing_in_progress = False

    def finish_polygon(self):
        """Finish drawing polygon (called on double-click or right-click)."""
        if self.current_tool != DrawingTool.POLYGON or not self.drawing_in_progress:
            return

        if len(self.polygon_points) >= 3:
            # Create final polygon
            if self.temp_shape:
                self.scene.removeItem(self.temp_shape)

            final_polygon = PolygonItem(self.polygon_points)
            self._apply_current_style(final_polygon)
            final_polygon.layer_id = self.current_layer_id
            self.scene.addItem(final_polygon)

            self._save_shape_to_database(final_polygon)
            self.shape_created.emit(final_polygon)

        self.polygon_points = []
        self.temp_shape = None
        self.drawing_in_progress = False

    def cancel_drawing(self):
        """Cancel current drawing operation."""
        if self.temp_shape and self.scene:
            self.scene.removeItem(self.temp_shape)

        self.temp_shape = None
        self.polygon_points = []
        self.drawing_in_progress = False

    def _apply_current_style(self, shape):
        """
        Apply current style settings to a shape.

        Args:
            shape: Shape item to style
        """
        shape.stroke_color = self.stroke_color
        shape.fill_color = self.fill_color
        shape.stroke_width = self.stroke_width

    def _save_shape_to_database(self, shape_item):
        """
        Save a graphics item to database.

        Args:
            shape_item: Graphics item to save
        """
        if not self.current_floor_plan:
            return

        # Convert graphics item to Shape model
        shape_data = shape_item.to_dict()

        shape = Shape(
            floor_plan_id=self.current_floor_plan.id,
            layer_id=self.current_layer_id,
            shape_type=shape_item.shape_type(),
            geometry=str(shape_data.get("geometry", {})),
            style=str(shape_data.get("style", {})),
            label=shape_item.label
        )

        shape_id = shape.save()
        shape_item.shape_id = shape_id

    def load_floor_plan_shapes(self, floor_plan: FloorPlan):
        """
        Load all shapes for a floor plan onto the canvas.

        Args:
            floor_plan: Floor plan to load
        """
        if not self.scene:
            return

        self.current_floor_plan = floor_plan

        # Clear existing shapes
        self.scene.clear()

        # Load shapes from database
        shapes = Shape.load_by_floor_plan(floor_plan.id)

        for shape_model in shapes:
            # Create graphics item from database model
            graphics_item = self._create_graphics_item_from_model(shape_model)
            if graphics_item:
                self.scene.add_item_to_layer(graphics_item, shape_model.layer_id)

    def _create_graphics_item_from_model(self, shape_model: Shape):
        """
        Create a graphics item from a database Shape model.

        Args:
            shape_model: Shape model from database

        Returns:
            Graphics item instance
        """
        shape_data = shape_model.to_dict()

        if shape_model.shape_type == SHAPE_RECTANGLE:
            item = RectangleItem()
        elif shape_model.shape_type == SHAPE_LINE:
            item = LineItem()
        elif shape_model.shape_type == SHAPE_POLYGON:
            item = PolygonItem()
        else:
            return None

        # Load data into graphics item
        item.from_dict(shape_data)
        item.shape_id = shape_model.id

        return item

    def save_all_shapes(self):
        """Save all shapes on canvas to database."""
        if not self.scene or not self.current_floor_plan:
            return

        for item in self.scene.items():
            if isinstance(item, (RectangleItem, LineItem, PolygonItem)):
                if item.shape_id is None:
                    # New shape, save to database
                    self._save_shape_to_database(item)
                else:
                    # Update existing shape
                    self._update_shape_in_database(item)

    def _update_shape_in_database(self, shape_item):
        """
        Update existing shape in database.

        Args:
            shape_item: Graphics item to update
        """
        if not shape_item.shape_id:
            return

        shape = Shape.load(shape_item.shape_id)
        if not shape:
            return

        # Update shape data
        shape_data = shape_item.to_dict()
        shape.geometry = str(shape_data.get("geometry", {}))
        shape.style = str(shape_data.get("style", {}))
        shape.label = shape_item.label
        shape.layer_id = shape_item.layer_id

        shape.save()
