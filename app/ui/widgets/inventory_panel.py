"""
Inventory Panel widget for managing inventory items.

Provides UI for viewing, searching, and managing inventory.
"""

from typing import Optional, List
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QTableWidget, QTableWidgetItem, QPushButton,
    QComboBox, QLabel, QHeaderView
)
from PySide6.QtCore import Signal, Qt, QTimer

from app.controllers.inventory_controller import InventoryController
from app.models.inventory_item import InventoryItem


class InventoryPanel(QWidget):
    """
    Panel for managing inventory items.

    Signals:
        item_selected: Emitted when an item is selected (item_id)
        item_double_clicked: Emitted when item is double-clicked (item_id)
    """

    item_selected = Signal(int)
    item_double_clicked = Signal(int)

    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize inventory panel."""
        super().__init__(parent)

        self.controller = InventoryController()
        self.current_items: List[InventoryItem] = []

        # Debounce timer for search
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.perform_search)

        self.setup_ui()
        self.connect_signals()
        self.refresh_items()

    def setup_ui(self):
        """Create UI components."""
        layout = QVBoxLayout(self)

        # Search bar
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search inventory...")
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["SKU", "Name", "Quantity", "Min Stock", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        layout.addWidget(self.table)

        # Buttons
        button_layout = QHBoxLayout()
        self.btn_add = QPushButton("Add Item")
        self.btn_edit = QPushButton("Edit Item")
        self.btn_delete = QPushButton("Delete Item")
        button_layout.addWidget(self.btn_add)
        button_layout.addWidget(self.btn_edit)
        button_layout.addWidget(self.btn_delete)
        button_layout.addStretch()
        layout.addLayout(button_layout)

    def connect_signals(self):
        """Connect signals."""
        self.search_input.textChanged.connect(lambda: self.search_timer.start(300))
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        self.table.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.controller.items_changed.connect(self.refresh_items)

    def perform_search(self):
        """Perform search."""
        query = self.search_input.text().strip()
        if query:
            self.current_items = self.controller.search_items(query)
        else:
            self.current_items = self.controller.get_all_items()
        self.update_table()

    def refresh_items(self):
        """Refresh item list."""
        self.current_items = self.controller.get_all_items()
        self.update_table()

    def update_table(self):
        """Update table with current items."""
        self.table.setRowCount(len(self.current_items))

        for row, item in enumerate(self.current_items):
            self.table.setItem(row, 0, QTableWidgetItem(item.sku or ""))
            self.table.setItem(row, 1, QTableWidgetItem(item.name))
            self.table.setItem(row, 2, QTableWidgetItem(str(item.quantity)))
            self.table.setItem(row, 3, QTableWidgetItem(str(item.min_stock_level)))

            # Status with color coding
            status_item = QTableWidgetItem(item.stock_status.replace('_', ' ').title())
            if item.stock_status == "out_of_stock":
                status_item.setForeground(Qt.red)
            elif item.stock_status == "low_stock":
                status_item.setForeground(Qt.darkYellow)
            else:
                status_item.setForeground(Qt.darkGreen)
            self.table.setItem(row, 4, status_item)

            # Store item ID in row data
            self.table.item(row, 0).setData(Qt.UserRole, item.id)

    def on_selection_changed(self):
        """Handle selection change."""
        selected = self.table.currentRow()
        if selected >= 0:
            item_id = self.table.item(selected, 0).data(Qt.UserRole)
            self.item_selected.emit(item_id)

    def on_item_double_clicked(self, item):
        """Handle double click."""
        item_id = item.data(Qt.UserRole)
        if item_id:
            self.item_double_clicked.emit(item_id)

    def get_selected_item_id(self) -> Optional[int]:
        """Get currently selected item ID."""
        selected = self.table.currentRow()
        if selected >= 0:
            return self.table.item(selected, 0).data(Qt.UserRole)
        return None
