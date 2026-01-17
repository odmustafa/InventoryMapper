"""
Conflict resolution dialog for Google Sheets sync.

Allows users to resolve conflicts when both local and remote data have changed.
"""

from typing import List
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QGroupBox, QRadioButton, QButtonGroup,
    QTextEdit, QSplitter
)
from PySide6.QtCore import Qt

from app.controllers.sync_controller import SyncConflict


class ConflictResolutionDialog(QDialog):
    """
    Dialog for resolving sync conflicts.

    Shows side-by-side comparison of local vs remote data
    and allows user to choose which version to keep.
    """

    def __init__(self, conflicts: List[SyncConflict], parent=None):
        """
        Initialize dialog.

        Args:
            conflicts: List of sync conflicts
            parent: Parent widget
        """
        super().__init__(parent)
        self.conflicts = conflicts
        self.current_index = 0
        self.resolutions = {}  # conflict_index -> use_local (bool)

        self.setWindowTitle(f"Resolve Sync Conflicts ({len(conflicts)} conflicts)")
        self.setMinimumSize(800, 600)

        self.setup_ui()
        self.show_conflict(0)

    def setup_ui(self):
        """Create UI components."""
        layout = QVBoxLayout(self)

        # Header
        header = QLabel(
            "<h3>Sync Conflicts Detected</h3>"
            "<p>The following items have been modified both locally and remotely. "
            "Please choose which version to keep for each conflict.</p>"
        )
        header.setWordWrap(True)
        layout.addWidget(header)

        # Progress indicator
        self.progress_label = QLabel()
        layout.addWidget(self.progress_label)

        # Conflict display
        splitter = QSplitter(Qt.Horizontal)

        # Local version
        local_group = QGroupBox("Local Version (Your Computer)")
        local_layout = QVBoxLayout()

        self.radio_local = QRadioButton("Use local version")
        self.radio_local.setChecked(True)
        local_layout.addWidget(self.radio_local)

        self.local_details = QTableWidget()
        self.local_details.setColumnCount(2)
        self.local_details.setHorizontalHeaderLabels(["Field", "Value"])
        self.local_details.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.local_details.setEditTriggers(QTableWidget.NoEditTriggers)
        local_layout.addWidget(self.local_details)

        local_group.setLayout(local_layout)
        splitter.addWidget(local_group)

        # Remote version
        remote_group = QGroupBox("Remote Version (Google Sheets)")
        remote_layout = QVBoxLayout()

        self.radio_remote = QRadioButton("Use remote version")
        remote_layout.addWidget(self.radio_remote)

        self.remote_details = QTableWidget()
        self.remote_details.setColumnCount(2)
        self.remote_details.setHorizontalHeaderLabels(["Field", "Value"])
        self.remote_details.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.remote_details.setEditTriggers(QTableWidget.NoEditTriggers)
        remote_layout.addWidget(self.remote_details)

        remote_group.setLayout(remote_layout)
        splitter.addWidget(remote_group)

        # Button group for radio buttons
        self.version_group = QButtonGroup(self)
        self.version_group.addButton(self.radio_local, 0)
        self.version_group.addButton(self.radio_remote, 1)

        layout.addWidget(splitter)

        # Navigation buttons
        nav_layout = QHBoxLayout()

        self.btn_prev = QPushButton("← Previous")
        self.btn_prev.clicked.connect(self.show_previous)
        nav_layout.addWidget(self.btn_prev)

        nav_layout.addStretch()

        self.btn_next = QPushButton("Next →")
        self.btn_next.clicked.connect(self.show_next)
        nav_layout.addWidget(self.btn_next)

        layout.addLayout(nav_layout)

        # Action buttons
        button_layout = QHBoxLayout()

        help_label = QLabel(
            "<small><i>Review each conflict and choose which version to keep. "
            "Click 'Apply All' when finished.</i></small>"
        )
        help_label.setWordWrap(True)
        button_layout.addWidget(help_label)

        button_layout.addStretch()

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        button_layout.addWidget(self.btn_cancel)

        self.btn_apply = QPushButton("Apply All Resolutions")
        self.btn_apply.clicked.connect(self.apply_resolutions)
        button_layout.addWidget(self.btn_apply)

        layout.addLayout(button_layout)

    def show_conflict(self, index: int):
        """
        Show conflict at given index.

        Args:
            index: Conflict index
        """
        if index < 0 or index >= len(self.conflicts):
            return

        self.current_index = index
        conflict = self.conflicts[index]

        # Update progress label
        self.progress_label.setText(
            f"Conflict {index + 1} of {len(self.conflicts)}: "
            f"<b>{conflict.local_item.name}</b> (ID: {conflict.item_id})"
        )

        # Update local details
        self._populate_table(self.local_details, conflict.local_item)

        # Update remote details
        self._populate_table(self.remote_details, conflict.remote_item)

        # Restore saved resolution or default to local
        use_local = self.resolutions.get(index, True)
        if use_local:
            self.radio_local.setChecked(True)
        else:
            self.radio_remote.setChecked(True)

        # Update navigation buttons
        self.btn_prev.setEnabled(index > 0)
        self.btn_next.setEnabled(index < len(self.conflicts) - 1)

    def _populate_table(self, table: QTableWidget, data):
        """
        Populate table with item data.

        Args:
            table: Table widget to populate
            data: Item data (InventoryItem or dict)
        """
        # Define fields to show
        if hasattr(data, '__dict__'):
            # Local item (InventoryItem object)
            fields = [
                ('SKU', data.sku or ''),
                ('Name', data.name),
                ('Description', data.description or ''),
                ('Quantity', str(data.quantity)),
                ('Min Stock Level', str(data.min_stock_level)),
                ('Unit Price', f"${data.unit_price:.2f}" if data.unit_price else '$0.00'),
                ('Tags', ', '.join(data.tags) if data.tags else ''),
                ('Stock Status', data.stock_status.replace('_', ' ').title()),
            ]
        else:
            # Remote item (dictionary)
            fields = [
                ('SKU', data.get('SKU', '')),
                ('Name', data.get('Name', '')),
                ('Description', data.get('Description', '')),
                ('Quantity', data.get('Quantity', '')),
                ('Min Stock Level', data.get('Min Stock Level', '')),
                ('Unit Price', data.get('Unit Price', '')),
                ('Tags', data.get('Tags', '')),
                ('Last Modified', data.get('Last Modified', '')),
            ]

        # Set row count
        table.setRowCount(len(fields))

        # Populate rows
        for i, (field, value) in enumerate(fields):
            field_item = QTableWidgetItem(field)
            field_item.setForeground(Qt.darkGray)
            table.setItem(i, 0, field_item)

            value_item = QTableWidgetItem(str(value))
            table.setItem(i, 1, value_item)

    def show_previous(self):
        """Show previous conflict."""
        # Save current resolution
        self.resolutions[self.current_index] = self.radio_local.isChecked()

        # Show previous
        self.show_conflict(self.current_index - 1)

    def show_next(self):
        """Show next conflict."""
        # Save current resolution
        self.resolutions[self.current_index] = self.radio_local.isChecked()

        # Show next
        self.show_conflict(self.current_index + 1)

    def apply_resolutions(self):
        """Apply all conflict resolutions."""
        # Save current resolution
        self.resolutions[self.current_index] = self.radio_local.isChecked()

        # Ensure all conflicts are resolved
        for i in range(len(self.conflicts)):
            if i not in self.resolutions:
                self.resolutions[i] = True  # Default to local

        self.accept()

    def get_resolutions(self) -> dict:
        """
        Get conflict resolutions.

        Returns:
            Dictionary mapping conflict index to use_local (bool)
        """
        return self.resolutions
