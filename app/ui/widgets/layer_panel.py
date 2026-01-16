"""
Layer Panel widget for managing drawing layers.

Provides UI for creating, deleting, renaming, showing/hiding, and reordering layers.
"""

from typing import Optional, List, Dict, Any
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QListWidgetItem, QInputDialog, QMessageBox
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QIcon, QColor

from app.models.database import get_database
from app.models.floor_plan import FloorPlan


class LayerPanel(QWidget):
    """
    Panel for managing layers on the floor plan.

    Signals:
        layer_selected: Emitted when a layer is selected (layer_id)
        layer_visibility_changed: Emitted when layer visibility changes (layer_id, visible)
        layer_created: Emitted when a new layer is created (layer_id)
        layer_deleted: Emitted when a layer is deleted (layer_id)
        layer_renamed: Emitted when a layer is renamed (layer_id, new_name)
    """

    layer_selected = Signal(int)
    layer_visibility_changed = Signal(int, bool)
    layer_created = Signal(int)
    layer_deleted = Signal(int)
    layer_renamed = Signal(int, str)

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize layer panel.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        self.current_floor_plan: Optional[FloorPlan] = None
        self.layers: List[Dict[str, Any]] = []

        self.setup_ui()

    def setup_ui(self):
        """Create UI components."""
        layout = QVBoxLayout(self)

        # Layer list
        self.layer_list = QListWidget()
        self.layer_list.itemSelectionChanged.connect(self._on_selection_changed)
        self.layer_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.layer_list)

        # Buttons
        button_layout = QHBoxLayout()

        self.btn_add = QPushButton("Add")
        self.btn_add.clicked.connect(self.add_layer)
        button_layout.addWidget(self.btn_add)

        self.btn_delete = QPushButton("Delete")
        self.btn_delete.clicked.connect(self.delete_layer)
        button_layout.addWidget(self.btn_delete)

        self.btn_rename = QPushButton("Rename")
        self.btn_rename.clicked.connect(self.rename_layer)
        button_layout.addWidget(self.btn_rename)

        layout.addLayout(button_layout)

        # Visibility buttons
        visibility_layout = QHBoxLayout()

        self.btn_show = QPushButton("Show")
        self.btn_show.clicked.connect(lambda: self.toggle_visibility(True))
        visibility_layout.addWidget(self.btn_show)

        self.btn_hide = QPushButton("Hide")
        self.btn_hide.clicked.connect(lambda: self.toggle_visibility(False))
        visibility_layout.addWidget(self.btn_hide)

        layout.addLayout(visibility_layout)

    def set_floor_plan(self, floor_plan: FloorPlan):
        """
        Set current floor plan and load its layers.

        Args:
            floor_plan: Floor plan to display layers for
        """
        self.current_floor_plan = floor_plan
        self.refresh_layers()

    def refresh_layers(self):
        """Reload layers from database and update UI."""
        if not self.current_floor_plan:
            self.layer_list.clear()
            self.layers = []
            return

        # Load layers from database
        self.layers = self.current_floor_plan.get_layers()

        # Update list widget
        self.layer_list.clear()

        for layer in self.layers:
            item = QListWidgetItem(layer["name"])
            item.setData(Qt.UserRole, layer["id"])

            # Set icon/color based on visibility
            if layer["visible"]:
                item.setForeground(QColor("#000000"))
            else:
                item.setForeground(QColor("#999999"))

            # Set checkbox for visibility
            item.setCheckState(Qt.Checked if layer["visible"] else Qt.Unchecked)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)

            self.layer_list.addItem(item)

        # Select first layer by default
        if self.layer_list.count() > 0:
            self.layer_list.setCurrentRow(0)

    def add_layer(self):
        """Create a new layer."""
        if not self.current_floor_plan:
            QMessageBox.warning(self, "No Floor Plan", "Please create or open a floor plan first.")
            return

        # Prompt for layer name
        name, ok = QInputDialog.getText(
            self,
            "New Layer",
            "Enter layer name:",
            text=f"Layer {len(self.layers) + 1}"
        )

        if ok and name:
            # Create layer in database
            layer_id = self.current_floor_plan.create_layer(name)

            # Refresh UI
            self.refresh_layers()

            # Emit signal
            self.layer_created.emit(layer_id)

            # Select new layer
            for i in range(self.layer_list.count()):
                item = self.layer_list.item(i)
                if item.data(Qt.UserRole) == layer_id:
                    self.layer_list.setCurrentRow(i)
                    break

    def delete_layer(self):
        """Delete selected layer."""
        current_item = self.layer_list.currentItem()
        if not current_item:
            return

        layer_id = current_item.data(Qt.UserRole)
        layer_name = current_item.text()

        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Delete Layer",
            f"Are you sure you want to delete layer '{layer_name}'?\n\nAll shapes on this layer will be affected.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # Delete from database
            if self.current_floor_plan:
                self.current_floor_plan.delete_layer(layer_id)

            # Emit signal
            self.layer_deleted.emit(layer_id)

            # Refresh UI
            self.refresh_layers()

    def rename_layer(self):
        """Rename selected layer."""
        current_item = self.layer_list.currentItem()
        if not current_item:
            return

        layer_id = current_item.data(Qt.UserRole)
        old_name = current_item.text()

        # Prompt for new name
        new_name, ok = QInputDialog.getText(
            self,
            "Rename Layer",
            "Enter new layer name:",
            text=old_name
        )

        if ok and new_name and new_name != old_name:
            # Update in database
            db = get_database()
            with db.transaction():
                db.execute(
                    "UPDATE layers SET name = ? WHERE id = ?",
                    (new_name, layer_id)
                )

            # Update UI
            current_item.setText(new_name)

            # Emit signal
            self.layer_renamed.emit(layer_id, new_name)

    def toggle_visibility(self, visible: bool):
        """
        Toggle visibility of selected layer.

        Args:
            visible: True to show, False to hide
        """
        current_item = self.layer_list.currentItem()
        if not current_item:
            return

        layer_id = current_item.data(Qt.UserRole)

        # Update in database
        db = get_database()
        with db.transaction():
            db.execute(
                "UPDATE layers SET visible = ? WHERE id = ?",
                (1 if visible else 0, layer_id)
            )

        # Update UI
        current_item.setCheckState(Qt.Checked if visible else Qt.Unchecked)
        if visible:
            current_item.setForeground(QColor("#000000"))
        else:
            current_item.setForeground(QColor("#999999"))

        # Emit signal
        self.layer_visibility_changed.emit(layer_id, visible)

    def get_selected_layer_id(self) -> Optional[int]:
        """
        Get currently selected layer ID.

        Returns:
            Layer ID or None if no selection
        """
        current_item = self.layer_list.currentItem()
        if current_item:
            return current_item.data(Qt.UserRole)
        return None

    def _on_selection_changed(self):
        """Handle layer selection change."""
        layer_id = self.get_selected_layer_id()
        if layer_id is not None:
            self.layer_selected.emit(layer_id)

    def _on_item_double_clicked(self, item: QListWidgetItem):
        """
        Handle double-click on layer item (toggle visibility).

        Args:
            item: List item that was double-clicked
        """
        layer_id = item.data(Qt.UserRole)

        # Get current visibility
        for layer in self.layers:
            if layer["id"] == layer_id:
                current_visibility = layer["visible"]
                self.toggle_visibility(not current_visibility)
                break
