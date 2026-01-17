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
from typing import Optional
from PySide6.QtCore import Qt, QTimer, QPointF
from PySide6.QtGui import QAction, QKeySequence, QIcon, QMouseEvent

from app.ui.widgets.canvas_scene import CanvasScene
from app.ui.widgets.canvas_view import CanvasView
from app.ui.widgets.layer_panel import LayerPanel
from app.ui.widgets.inventory_panel import InventoryPanel
from app.ui.graphics_items.inventory_marker import InventoryMarker
from app.ui.dialogs.item_editor import ItemEditorDialog
from app.ui.dialogs.google_sheets_dialog import GoogleSheetsDialog
from app.ui.dialogs.conflict_resolution_dialog import ConflictResolutionDialog
from app.controllers.drawing_controller import DrawingController, DrawingTool
from app.controllers.inventory_controller import InventoryController
from app.controllers.sync_controller import SyncController, SyncConflict
from app.models.floor_plan import FloorPlan
from app.models.inventory_item import InventoryItem
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
        self.inventory_controller = InventoryController()
        self.sync_controller = SyncController()
        self.current_floor_plan = None

        # Auto-sync timer
        self.auto_sync_timer = QTimer(self)
        self.auto_sync_timer.timeout.connect(self.auto_sync)
        self.auto_sync_enabled = False
        self.auto_sync_interval = 5 * 60 * 1000  # 5 minutes in milliseconds

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

        # Google Sheets sync submenu
        self.action_setup_sync = QAction("Setup &Google Sheets...", self)
        self.action_setup_sync.setStatusTip("Configure Google Sheets synchronization")
        tools_menu.addAction(self.action_setup_sync)

        self.action_sync_now = QAction("Sync &Now", self)
        self.action_sync_now.setStatusTip("Synchronize inventory with Google Sheets")
        self.action_sync_now.setEnabled(False)
        tools_menu.addAction(self.action_sync_now)

        self.action_auto_sync = QAction("&Auto-Sync", self)
        self.action_auto_sync.setCheckable(True)
        self.action_auto_sync.setChecked(False)
        self.action_auto_sync.setStatusTip("Automatically sync every 5 minutes")
        self.action_auto_sync.setEnabled(False)
        tools_menu.addAction(self.action_auto_sync)

        tools_menu.addSeparator()

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
        self.inventory_panel = InventoryPanel()
        inventory_dock = QDockWidget("Inventory", self)
        inventory_dock.setWidget(self.inventory_panel)
        self.addDockWidget(Qt.RightDockWidgetArea, inventory_dock)

        # Tabify the dock widgets
        self.tabifyDockWidget(layer_dock, inventory_dock)

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

        # Inventory panel signals
        self.inventory_panel.btn_add.clicked.connect(self.add_inventory_item)
        self.inventory_panel.btn_edit.clicked.connect(self.edit_inventory_item)
        self.inventory_panel.btn_delete.clicked.connect(self.delete_inventory_item)
        self.inventory_panel.item_double_clicked.connect(self.edit_inventory_item)
        self.inventory_panel.item_selected.connect(self.on_inventory_item_selected)

        # Tools menu - CSV import and sync
        self.action_import_csv.triggered.connect(self.import_inventory_csv)
        self.action_setup_sync.triggered.connect(self.setup_google_sheets)
        self.action_sync_now.triggered.connect(self.sync_now)
        self.action_auto_sync.toggled.connect(self.toggle_auto_sync)

        # Sync controller signals
        self.sync_controller.status_changed.connect(self.update_sync_status)
        self.sync_controller.sync_conflict.connect(self.handle_sync_conflict)
        self.sync_controller.sync_completed.connect(self.on_sync_completed)

        # Canvas signals
        self.view.zoom_changed.connect(self.update_zoom_label)
        self.view.mouse_position_changed.connect(self.update_position_label)
        self.view.inventory_item_dropped.connect(self.on_inventory_item_dropped)

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

                # Load inventory markers
                self._load_inventory_markers(floor_plan)

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

    # Inventory Operations

    def add_inventory_item(self):
        """Show dialog to add new inventory item."""
        dialog = ItemEditorDialog(parent=self)
        if dialog.exec():
            data = dialog.get_item_data()
            self.inventory_controller.create_item(**data)

    def edit_inventory_item(self, item_id: Optional[int] = None):
        """Show dialog to edit inventory item."""
        if item_id is None:
            item_id = self.inventory_panel.get_selected_item_id()

        if not item_id:
            return

        item = self.inventory_controller.get_item(item_id)
        if item:
            dialog = ItemEditorDialog(item=item, parent=self)
            if dialog.exec():
                data = dialog.get_item_data()
                self.inventory_controller.update_item(item_id, **data)

    def delete_inventory_item(self):
        """Delete selected inventory item."""
        item_id = self.inventory_panel.get_selected_item_id()
        if not item_id:
            return

        reply = QMessageBox.question(
            self, "Delete Item",
            "Are you sure you want to delete this item?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.inventory_controller.delete_item(item_id)

    def import_inventory_csv(self):
        """Import inventory from CSV file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Inventory CSV", "", "CSV Files (*.csv)"
        )

        if file_path:
            count, errors = self.inventory_controller.import_from_csv(file_path)

            if errors:
                error_msg = "\n".join(errors[:10])  # Show first 10 errors
                if len(errors) > 10:
                    error_msg += f"\n... and {len(errors) - 10} more errors"
                QMessageBox.warning(self, "Import Errors", f"Imported {count} items with errors:\n\n{error_msg}")
            else:
                QMessageBox.information(self, "Import Complete", f"Successfully imported {count} items.")

    # Google Sheets Sync Operations

    def setup_google_sheets(self):
        """Show Google Sheets setup dialog."""
        dialog = GoogleSheetsDialog(self.sync_controller, self)
        if dialog.exec():
            # Enable sync actions
            self.action_sync_now.setEnabled(True)
            self.action_auto_sync.setEnabled(True)
            self.statusBar().showMessage("Google Sheets configured successfully", 3000)

    def sync_now(self):
        """Trigger manual synchronization."""
        if not self.sync_controller.is_configured():
            QMessageBox.warning(
                self,
                "Sync Not Configured",
                "Please configure Google Sheets sync first (Tools → Setup Google Sheets)."
            )
            return

        # Perform sync
        self.statusBar().showMessage("Synchronizing...", 0)
        self.sync_controller.sync()

    def toggle_auto_sync(self, enabled: bool):
        """
        Toggle auto-sync on/off.

        Args:
            enabled: True to enable auto-sync, False to disable
        """
        self.auto_sync_enabled = enabled

        if enabled:
            self.auto_sync_timer.start(self.auto_sync_interval)
            self.statusBar().showMessage("Auto-sync enabled (every 5 minutes)", 3000)
        else:
            self.auto_sync_timer.stop()
            self.statusBar().showMessage("Auto-sync disabled", 3000)

    def auto_sync(self):
        """Perform automatic synchronization."""
        if self.sync_controller.is_configured() and self.auto_sync_enabled:
            self.sync_controller.sync()

    def update_sync_status(self, message: str):
        """
        Update sync status label.

        Args:
            message: Status message
        """
        self.sync_label.setText(f"Sync: {message}")

    def handle_sync_conflict(self, conflict: SyncConflict):
        """
        Handle sync conflict.

        Args:
            conflict: Sync conflict object
        """
        # Collect all pending conflicts
        conflicts = self.sync_controller.get_pending_conflicts()

        if conflicts:
            # Show conflict resolution dialog
            dialog = ConflictResolutionDialog(conflicts, self)
            if dialog.exec():
                # Apply resolutions
                resolutions = dialog.get_resolutions()
                for i, conflict in enumerate(conflicts):
                    use_local = resolutions.get(i, True)
                    self.sync_controller.resolve_conflict(conflict, use_local)

                # Retry sync
                self.sync_controller.sync(resolve_conflicts=True)

    def on_sync_completed(self, success: bool, message: str):
        """
        Handle sync completion.

        Args:
            success: True if sync successful
            message: Result message
        """
        if success:
            self.statusBar().showMessage(message, 3000)
            # Refresh inventory display
            self.inventory_panel.refresh_items()
        else:
            QMessageBox.warning(self, "Sync Failed", message)

    def on_inventory_item_dropped(self, item_id: int, scene_pos: QPointF):
        """
        Handle inventory item dropped on canvas.

        Args:
            item_id: ID of the inventory item
            scene_pos: Drop position in scene coordinates
        """
        # Check if a floor plan is loaded
        if not self.current_floor_plan:
            QMessageBox.warning(
                self,
                "No Floor Plan",
                "Please create or open a floor plan before placing inventory items."
            )
            return

        # Load inventory item
        item = InventoryItem.load(item_id)
        if not item:
            QMessageBox.warning(self, "Error", f"Could not load inventory item {item_id}")
            return

        # Snap to grid if enabled
        if self.scene.snap_enabled:
            scene_pos = self.scene.snap_to_grid(scene_pos)

        # Create inventory marker
        marker = InventoryMarker(item)
        marker.setPos(scene_pos)

        # Add to scene (no specific layer for now)
        self.scene.addItem(marker)

        # Save placement to database
        self._save_inventory_placement(marker)

        # Show status message
        self.statusBar().showMessage(f"Placed '{item.name}' on floor plan", 3000)

    def _save_inventory_placement(self, marker: InventoryMarker):
        """
        Save inventory placement to database.

        Args:
            marker: Inventory marker to save
        """
        from app.models.database import Database

        db = Database()
        with db.transaction():
            cursor = db.execute(
                """
                INSERT INTO inventory_placements
                (floor_plan_id, inventory_item_id, x_position, y_position, rotation)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    self.current_floor_plan.id,
                    marker.item.id,
                    marker.pos().x(),
                    marker.pos().y(),
                    marker.rotation()
                )
            )
            # Store placement ID in marker for future updates
            marker.placement_id = cursor.lastrowid

    def _load_inventory_markers(self, floor_plan: FloorPlan):
        """
        Load inventory markers for a floor plan.

        Args:
            floor_plan: Floor plan to load markers for
        """
        from app.models.database import Database

        db = Database()
        rows = db.execute(
            """
            SELECT id, inventory_item_id, x_position, y_position, rotation
            FROM inventory_placements
            WHERE floor_plan_id = ?
            """,
            (floor_plan.id,)
        ).fetchall()

        for row in rows:
            placement_id, item_id, x, y, rotation = row

            # Load inventory item
            item = InventoryItem.load(item_id)
            if not item:
                continue  # Skip if item was deleted

            # Create marker
            marker = InventoryMarker(item)
            marker.setPos(QPointF(x, y))
            marker.setRotation(rotation)
            marker.placement_id = placement_id

            # Add to scene
            self.scene.addItem(marker)

    def on_inventory_item_selected(self, item_id: int):
        """
        Handle inventory item selection - highlight and center on canvas.

        Args:
            item_id: ID of selected inventory item
        """
        # Clear all highlights first
        for item in self.scene.items():
            if isinstance(item, InventoryMarker):
                item.set_highlighted(False)

        # Find and highlight matching markers
        found_marker = None
        for item in self.scene.items():
            if isinstance(item, InventoryMarker):
                if item.get_item_id() == item_id:
                    item.set_highlighted(True)
                    if not found_marker:
                        found_marker = item

        # Center view on first found marker
        if found_marker:
            self.view.centerOn(found_marker.pos())
            self.statusBar().showMessage(f"Located '{found_marker.item.name}' on floor plan", 3000)

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
