"""
Main application window for Inventory Mapper.

Provides the primary UI with menu bar, toolbars, canvas, and dock panels.
"""

from PySide6.QtWidgets import (
    QMainWindow,
    QDockWidget,
    QToolBar,
    QStatusBar,
    QLabel,
    QMessageBox,
    QFileDialog,
    QInputDialog,
    QButtonGroup,
)
from PySide6.QtCore import Qt, QTimer, QPointF
from PySide6.QtGui import QAction, QKeySequence, QIcon, QMouseEvent

from app.ui.widgets.canvas_scene import CanvasScene
from app.ui.widgets.canvas_view import CanvasView
from app.ui.widgets.layer_panel import LayerPanel
from app.controllers.drawing_controller import DrawingController, DrawingTool
from app.models.floor_plan import FloorPlan
from app.config import get_config
from app.constants import (
    APP_NAME,
    APP_VERSION,
    DEFAULT_CANVAS_WIDTH,
    DEFAULT_CANVAS_HEIGHT,
    DEFAULT_WINDOW_WIDTH,
    DEFAULT_WINDOW_HEIGHT,
    MIN_WINDOW_WIDTH,
    MIN_WINDOW_HEIGHT,
    SHORTCUT_NEW,
    SHORTCUT_OPEN,
    SHORTCUT_SAVE,
    SHORTCUT_EXPORT,
    SHORTCUT_UNDO,
    SHORTCUT_REDO,
    SHORTCUT_DELETE,
    SHORTCUT_ZOOM_IN,
    SHORTCUT_ZOOM_OUT,
    SHORTCUT_ZOOM_FIT,
    SHORTCUT_FIND,
)


class MainWindow(QMainWindow):
    """
    Main application window.

    Provides:
    - Menu bar (File, Edit, View, Tools, Help)
    - Toolbar for drawing tools
    - Central canvas (QGraphicsView)
    - Dock panels (inventory, layers, properties)
    - Status bar (zoom level, cursor position, sync status)
    """

    def __init__(self):
        """Initialize main window."""
        super().__init__()

        # Configuration
        self.config = get_config()

        # Controllers
        self.drawing_controller = None
        self.current_floor_plan = None

        # Setup UI components
        self.setup_window()
        self.setup_canvas()
        self.setup_controllers()
        self.setup_menus()
        self.setup_toolbars()
        self.setup_dock_panels()
        self.setup_statusbar()
        self.setup_connections()

        # Restore window state
        self.restore_state()

    def setup_window(self):
        """Configure main window properties."""
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setMinimumSize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
        self.resize(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)

    def setup_canvas(self):
        """Create and configure the drawing canvas."""
        # Create scene
        self.scene = CanvasScene(
            width=DEFAULT_CANVAS_WIDTH,
            height=DEFAULT_CANVAS_HEIGHT,
            unit=self.config.default_unit
        )

        # Create view
        self.view = CanvasView()
        self.view.setScene(self.scene)

        # Set as central widget
        self.setCentralWidget(self.view)

        # Configure grid
        self.scene.set_grid_visible(self.config.grid_visible)
        self.scene.set_grid_size(self.config.grid_size)
        self.scene.set_snap_enabled(self.config.snap_to_grid)

        # Install event filter for mouse events
        self.view.viewport().installEventFilter(self)

    def setup_controllers(self):
        """Initialize controllers."""
        self.drawing_controller = DrawingController(self.scene)

    def setup_menus(self):
        """Create menu bar and menus."""
        menubar = self.menuBar()

        # File Menu
        file_menu = menubar.addMenu("&File")

        self.action_new = QAction("&New Floor Plan", self)
        self.action_new.setShortcut(QKeySequence(SHORTCUT_NEW))
        self.action_new.setStatusTip("Create a new floor plan")
        file_menu.addAction(self.action_new)

        self.action_open = QAction("&Open Floor Plan...", self)
        self.action_open.setShortcut(QKeySequence(SHORTCUT_OPEN))
        self.action_open.setStatusTip("Open an existing floor plan")
        file_menu.addAction(self.action_open)

        file_menu.addSeparator()

        self.action_save = QAction("&Save", self)
        self.action_save.setShortcut(QKeySequence(SHORTCUT_SAVE))
        self.action_save.setStatusTip("Save current floor plan")
        file_menu.addAction(self.action_save)

        self.action_export = QAction("&Export...", self)
        self.action_export.setShortcut(QKeySequence(SHORTCUT_EXPORT))
        self.action_export.setStatusTip("Export floor plan to file")
        file_menu.addAction(self.action_export)

        file_menu.addSeparator()

        self.action_exit = QAction("E&xit", self)
        self.action_exit.setShortcut(QKeySequence.Quit)
        self.action_exit.setStatusTip("Exit application")
        file_menu.addAction(self.action_exit)

        # Edit Menu
        edit_menu = menubar.addMenu("&Edit")

        self.action_undo = QAction("&Undo", self)
        self.action_undo.setShortcut(QKeySequence(SHORTCUT_UNDO))
        self.action_undo.setEnabled(False)
        edit_menu.addAction(self.action_undo)

        self.action_redo = QAction("&Redo", self)
        self.action_redo.setShortcut(QKeySequence(SHORTCUT_REDO))
        self.action_redo.setEnabled(False)
        edit_menu.addAction(self.action_redo)

        edit_menu.addSeparator()

        self.action_delete = QAction("&Delete", self)
        self.action_delete.setShortcut(QKeySequence(SHORTCUT_DELETE))
        self.action_delete.setStatusTip("Delete selected items")
        edit_menu.addAction(self.action_delete)

        edit_menu.addSeparator()

        self.action_find = QAction("&Find Inventory...", self)
        self.action_find.setShortcut(QKeySequence(SHORTCUT_FIND))
        self.action_find.setStatusTip("Search for inventory items")
        edit_menu.addAction(self.action_find)

        # View Menu
        view_menu = menubar.addMenu("&View")

        self.action_zoom_in = QAction("Zoom &In", self)
        self.action_zoom_in.setShortcut(QKeySequence(SHORTCUT_ZOOM_IN))
        view_menu.addAction(self.action_zoom_in)

        self.action_zoom_out = QAction("Zoom &Out", self)
        self.action_zoom_out.setShortcut(QKeySequence(SHORTCUT_ZOOM_OUT))
        view_menu.addAction(self.action_zoom_out)

        self.action_zoom_fit = QAction("Zoom to &Fit", self)
        self.action_zoom_fit.setShortcut(QKeySequence(SHORTCUT_ZOOM_FIT))
        view_menu.addAction(self.action_zoom_fit)

        view_menu.addSeparator()

        self.action_show_grid = QAction("Show &Grid", self)
        self.action_show_grid.setCheckable(True)
        self.action_show_grid.setChecked(self.config.grid_visible)
        view_menu.addAction(self.action_show_grid)

        self.action_snap_to_grid = QAction("&Snap to Grid", self)
        self.action_snap_to_grid.setCheckable(True)
        self.action_snap_to_grid.setChecked(self.config.snap_to_grid)
        view_menu.addAction(self.action_snap_to_grid)

        # Tools Menu
        tools_menu = menubar.addMenu("&Tools")

        self.action_sync = QAction("&Sync with Google Sheets", self)
        self.action_sync.setStatusTip("Synchronize inventory with Google Sheets")
        tools_menu.addAction(self.action_sync)

        self.action_import_csv = QAction("&Import Inventory CSV...", self)
        self.action_import_csv.setStatusTip("Import inventory items from CSV file")
        tools_menu.addAction(self.action_import_csv)

        tools_menu.addSeparator()

        self.action_settings = QAction("&Settings...", self)
        self.action_settings.setStatusTip("Open application settings")
        tools_menu.addAction(self.action_settings)

        # Help Menu
        help_menu = menubar.addMenu("&Help")

        self.action_about = QAction("&About", self)
        self.action_about.setStatusTip("About Inventory Mapper")
        help_menu.addAction(self.action_about)

    def setup_toolbars(self):
        """Create toolbars."""
        # Main toolbar
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(Qt.TopToolBarArea, toolbar)

        # Add actions to toolbar
        toolbar.addAction(self.action_new)
        toolbar.addAction(self.action_open)
        toolbar.addAction(self.action_save)
        toolbar.addSeparator()
        toolbar.addAction(self.action_zoom_in)
        toolbar.addAction(self.action_zoom_out)
        toolbar.addAction(self.action_zoom_fit)

        # Drawing tools toolbar
        drawing_toolbar = QToolBar("Drawing Tools")
        drawing_toolbar.setMovable(False)
        self.addToolBar(Qt.LeftToolBarArea, drawing_toolbar)

        # Create button group for exclusive tool selection
        self.tool_button_group = QButtonGroup(self)
        self.tool_button_group.setExclusive(True)

        # Select tool
        self.action_tool_select = QAction("Select", self)
        self.action_tool_select.setCheckable(True)
        self.action_tool_select.setChecked(True)
        self.action_tool_select.setStatusTip("Select and move items")
        drawing_toolbar.addAction(self.action_tool_select)

        # Rectangle tool
        self.action_tool_rectangle = QAction("Rectangle", self)
        self.action_tool_rectangle.setCheckable(True)
        self.action_tool_rectangle.setStatusTip("Draw rectangles")
        drawing_toolbar.addAction(self.action_tool_rectangle)

        # Line tool
        self.action_tool_line = QAction("Line", self)
        self.action_tool_line.setCheckable(True)
        self.action_tool_line.setStatusTip("Draw lines")
        drawing_toolbar.addAction(self.action_tool_line)

        # Polygon tool
        self.action_tool_polygon = QAction("Polygon", self)
        self.action_tool_polygon.setCheckable(True)
        self.action_tool_polygon.setStatusTip("Draw polygons (click to add points, double-click to finish)")
        drawing_toolbar.addAction(self.action_tool_polygon)

    def setup_dock_panels(self):
        """Create dock panels."""
        # Layer panel (Phase 2)
        self.layer_panel = LayerPanel()
        layer_dock = QDockWidget("Layers", self)
        layer_dock.setWidget(self.layer_panel)
        self.addDockWidget(Qt.RightDockWidgetArea, layer_dock)

        # Inventory panel (Phase 3)
        # Property panel (Phase 2 - future enhancement)

    def setup_statusbar(self):
        """Create status bar."""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)

        # Zoom level label
        self.zoom_label = QLabel("Zoom: 100%")
        self.statusbar.addPermanentWidget(self.zoom_label)

        # Cursor position label
        self.position_label = QLabel("Position: (0.0, 0.0)")
        self.statusbar.addPermanentWidget(self.position_label)

        # Sync status label
        self.sync_label = QLabel("Sync: Not connected")
        self.statusbar.addPermanentWidget(self.sync_label)

    def setup_connections(self):
        """Connect signals and slots."""
        # File menu
        self.action_new.triggered.connect(self.new_floor_plan)
        self.action_open.triggered.connect(self.open_floor_plan)
        self.action_save.triggered.connect(self.save_floor_plan)
        self.action_exit.triggered.connect(self.close)
        self.action_about.triggered.connect(self.show_about)

        # Edit menu
        self.action_delete.triggered.connect(self.delete_selected)

        # View menu
        self.action_zoom_in.triggered.connect(self.view.zoom_in)
        self.action_zoom_out.triggered.connect(self.view.zoom_out)
        self.action_zoom_fit.triggered.connect(self.view.zoom_fit)
        self.action_show_grid.toggled.connect(self.toggle_grid)
        self.action_snap_to_grid.toggled.connect(self.toggle_snap)

        # Drawing tools
        self.action_tool_select.triggered.connect(lambda: self.set_drawing_tool(DrawingTool.SELECT))
        self.action_tool_rectangle.triggered.connect(lambda: self.set_drawing_tool(DrawingTool.RECTANGLE))
        self.action_tool_line.triggered.connect(lambda: self.set_drawing_tool(DrawingTool.LINE))
        self.action_tool_polygon.triggered.connect(lambda: self.set_drawing_tool(DrawingTool.POLYGON))

        # Layer panel signals
        self.layer_panel.layer_selected.connect(self.on_layer_selected)
        self.layer_panel.layer_visibility_changed.connect(self.on_layer_visibility_changed)
        self.layer_panel.layer_created.connect(self.on_layer_created)
        self.layer_panel.layer_deleted.connect(self.on_layer_deleted)

        # Canvas signals
        self.view.zoom_changed.connect(self.update_zoom_label)
        self.view.mouse_position_changed.connect(self.update_position_label)

    def toggle_grid(self, checked: bool):
        """
        Toggle grid visibility.

        Args:
            checked: True to show grid, False to hide
        """
        self.scene.set_grid_visible(checked)
        self.config.grid_visible = checked

    def toggle_snap(self, checked: bool):
        """
        Toggle snap to grid.

        Args:
            checked: True to enable snapping, False to disable
        """
        self.scene.set_snap_enabled(checked)
        self.config.snap_to_grid = checked

    def delete_selected(self):
        """Delete selected items from canvas."""
        self.scene.delete_selected_items()

    def update_zoom_label(self, zoom_factor: float):
        """
        Update zoom level in status bar.

        Args:
            zoom_factor: Current zoom factor
        """
        zoom_percent = int(zoom_factor * 100)
        self.zoom_label.setText(f"Zoom: {zoom_percent}%")

    def update_position_label(self, pos):
        """
        Update cursor position in status bar.

        Args:
            pos: Current cursor position in scene coordinates
        """
        self.position_label.setText(
            f"Position: ({pos.x():.1f}, {pos.y():.1f}) {self.scene.unit}"
        )

    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            f"About {APP_NAME}",
            f"<h3>{APP_NAME} v{APP_VERSION}</h3>"
            f"<p>A desktop application for creating interactive floor plans "
            f"with spatial inventory tracking.</p>"
            f"<p><b>Features:</b></p>"
            f"<ul>"
            f"<li>Vector graphics drawing tools</li>"
            f"<li>Inventory management with search</li>"
            f"<li>Google Sheets synchronization</li>"
            f"<li>Export to multiple formats</li>"
            f"</ul>"
        )

    # Floor Plan Operations

    def new_floor_plan(self):
        """Create a new floor plan."""
        # Prompt for floor plan name
        name, ok = QInputDialog.getText(
            self,
            "New Floor Plan",
            "Enter floor plan name:",
            text="Untitled Floor Plan"
        )

        if ok and name:
            # Create floor plan
            floor_plan = FloorPlan(name=name)
            floor_plan.save()

            # Set as current
            self.current_floor_plan = floor_plan
            self.drawing_controller.set_floor_plan(floor_plan)

            # Update layer panel
            self.layer_panel.set_floor_plan(floor_plan)

            # Clear canvas
            self.scene.clear()

            # Update title
            self.setWindowTitle(f"{APP_NAME} - {name}")

            self.statusBar().showMessage(f"Created new floor plan: {name}", 3000)

    def open_floor_plan(self):
        """Open an existing floor plan."""
        # Get all floor plans
        floor_plans = FloorPlan.load_all()

        if not floor_plans:
            QMessageBox.information(self, "No Floor Plans", "No floor plans found. Create a new one first.")
            return

        # Create selection dialog
        names = [f"{fp.name} (ID: {fp.id})" for fp in floor_plans]
        name, ok = QInputDialog.getItem(
            self,
            "Open Floor Plan",
            "Select floor plan:",
            names,
            0,
            False
        )

        if ok and name:
            # Extract ID from name
            fp_id = int(name.split("ID: ")[1].rstrip(")"))

            # Load floor plan
            floor_plan = FloorPlan.load(fp_id)
            if floor_plan:
                self.current_floor_plan = floor_plan
                self.drawing_controller.set_floor_plan(floor_plan)
                self.drawing_controller.load_floor_plan_shapes(floor_plan)

                # Update layer panel
                self.layer_panel.set_floor_plan(floor_plan)

                # Update title
                self.setWindowTitle(f"{APP_NAME} - {floor_plan.name}")

                self.statusBar().showMessage(f"Opened floor plan: {floor_plan.name}", 3000)

    def save_floor_plan(self):
        """Save current floor plan."""
        if not self.current_floor_plan:
            QMessageBox.warning(self, "No Floor Plan", "Please create or open a floor plan first.")
            return

        # Save floor plan metadata
        self.current_floor_plan.save()

        # Save all shapes
        self.drawing_controller.save_all_shapes()

        self.statusBar().showMessage("Floor plan saved successfully", 3000)

    # Drawing Tool Operations

    def set_drawing_tool(self, tool: DrawingTool):
        """
        Set active drawing tool.

        Args:
            tool: Drawing tool to activate
        """
        self.drawing_controller.set_tool(tool)

        # Update UI
        self.action_tool_select.setChecked(tool == DrawingTool.SELECT)
        self.action_tool_rectangle.setChecked(tool == DrawingTool.RECTANGLE)
        self.action_tool_line.setChecked(tool == DrawingTool.LINE)
        self.action_tool_polygon.setChecked(tool == DrawingTool.POLYGON)

    # Layer Operations

    def on_layer_selected(self, layer_id: int):
        """Handle layer selection."""
        self.drawing_controller.set_current_layer(layer_id)

    def on_layer_visibility_changed(self, layer_id: int, visible: bool):
        """Handle layer visibility change."""
        self.scene.set_layer_visibility(layer_id, visible)

    def on_layer_created(self, layer_id: int):
        """Handle new layer creation."""
        self.drawing_controller.set_current_layer(layer_id)

    def on_layer_deleted(self, layer_id: int):
        """Handle layer deletion."""
        self.scene.remove_layer_items(layer_id)

    # Event Handling

    def eventFilter(self, obj, event):
        """
        Event filter for canvas mouse events.

        Args:
            obj: Object that received event
            event: Event

        Returns:
            True if event was handled, False otherwise
        """
        if obj == self.view.viewport():
            if event.type() == event.Type.MouseButtonPress:
                if event.button() == Qt.LeftButton:
                    # Convert to scene coordinates
                    scene_pos = self.view.mapToScene(event.pos())
                    self.drawing_controller.start_shape(scene_pos)
                    return False  # Let view handle it too

            elif event.type() == event.Type.MouseMove:
                if self.drawing_controller.drawing_in_progress:
                    scene_pos = self.view.mapToScene(event.pos())
                    self.drawing_controller.update_shape(scene_pos)
                    return False

            elif event.type() == event.Type.MouseButtonRelease:
                if event.button() == Qt.LeftButton:
                    self.drawing_controller.finish_shape()
                    return False

            elif event.type() == event.Type.MouseButtonDblClick:
                if event.button() == Qt.LeftButton:
                    self.drawing_controller.finish_polygon()
                    return False

        return super().eventFilter(obj, event)

    def restore_state(self):
        """Restore window state from settings."""
        geometry = self.config.window_geometry
        if geometry:
            self.restoreGeometry(geometry)

        state = self.config.window_state
        if state:
            self.restoreState(state)

    def save_state(self):
        """Save window state to settings."""
        self.config.window_geometry = self.saveGeometry()
        self.config.window_state = self.saveState()
        self.config.sync()

    def closeEvent(self, event):
        """
        Handle window close event.

        Args:
            event: Close event
        """
        # Save window state
        self.save_state()

        # Accept close event
        event.accept()
