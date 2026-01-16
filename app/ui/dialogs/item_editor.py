"""
Item Editor Dialog for adding/editing inventory items.
"""

from typing import Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QTextEdit, QSpinBox, QDoubleSpinBox, QPushButton,
    QHBoxLayout, QDialogButtonBox
)

from app.models.inventory_item import InventoryItem


class ItemEditorDialog(QDialog):
    """Dialog for creating or editing inventory items."""

    def __init__(self, item: Optional[InventoryItem] = None, parent=None):
        """
        Initialize item editor dialog.

        Args:
            item: Existing item to edit (None for new item)
            parent: Parent widget
        """
        super().__init__(parent)
        self.item = item
        self.setup_ui()
        if item:
            self.load_item(item)

    def setup_ui(self):
        """Create UI components."""
        self.setWindowTitle("Edit Item" if self.item else "Add Item")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        # SKU
        self.sku_input = QLineEdit()
        form.addRow("SKU:", self.sku_input)

        # Name
        self.name_input = QLineEdit()
        form.addRow("Name *:", self.name_input)

        # Description
        self.desc_input = QTextEdit()
        self.desc_input.setMaximumHeight(100)
        form.addRow("Description:", self.desc_input)

        # Quantity
        self.quantity_input = QSpinBox()
        self.quantity_input.setMaximum(1000000)
        form.addRow("Quantity:", self.quantity_input)

        # Min Stock Level
        self.min_stock_input = QSpinBox()
        self.min_stock_input.setMaximum(1000000)
        form.addRow("Min Stock:", self.min_stock_input)

        # Unit Price
        self.price_input = QDoubleSpinBox()
        self.price_input.setMaximum(1000000)
        self.price_input.setDecimals(2)
        self.price_input.setPrefix("$ ")
        form.addRow("Price:", self.price_input)

        layout.addLayout(form)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def load_item(self, item: InventoryItem):
        """Load item data into form."""
        self.sku_input.setText(item.sku or "")
        self.name_input.setText(item.name)
        self.desc_input.setPlainText(item.description)
        self.quantity_input.setValue(item.quantity)
        self.min_stock_input.setValue(item.min_stock_level)
        if item.unit_price:
            self.price_input.setValue(item.unit_price)

    def get_item_data(self) -> dict:
        """Get item data from form."""
        return {
            "sku": self.sku_input.text() or None,
            "name": self.name_input.text(),
            "description": self.desc_input.toPlainText(),
            "quantity": self.quantity_input.value(),
            "min_stock_level": self.min_stock_input.value(),
            "unit_price": self.price_input.value() if self.price_input.value() > 0 else None
        }
