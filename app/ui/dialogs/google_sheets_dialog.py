"""
Google Sheets setup dialog.

Allows users to configure Google Sheets synchronization.
"""

from typing import Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QTextEdit, QGroupBox,
    QRadioButton, QButtonGroup, QMessageBox, QProgressDialog
)
from PySide6.QtCore import Qt, QThread, Signal

from app.controllers.sync_controller import SyncController


class AuthThread(QThread):
    """Thread for handling OAuth authentication."""

    success = Signal()
    error = Signal(str)

    def __init__(self, sync_controller: SyncController):
        """Initialize auth thread."""
        super().__init__()
        self.sync_controller = sync_controller

    def run(self):
        """Run authentication."""
        try:
            if self.sync_controller.authenticate():
                self.success.emit()
            else:
                self.error.emit("Authentication failed")
        except Exception as e:
            self.error.emit(str(e))


class GoogleSheetsDialog(QDialog):
    """
    Dialog for configuring Google Sheets synchronization.

    Allows users to:
    - Authenticate with Google
    - Create new spreadsheet
    - Connect to existing spreadsheet
    """

    def __init__(self, sync_controller: SyncController, parent=None):
        """
        Initialize dialog.

        Args:
            sync_controller: Sync controller instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.sync_controller = sync_controller

        self.setWindowTitle("Google Sheets Setup")
        self.setMinimumWidth(500)

        self.setup_ui()

    def setup_ui(self):
        """Create UI components."""
        layout = QVBoxLayout(self)

        # Instructions
        instructions = QLabel(
            "<h3>Google Sheets Synchronization</h3>"
            "<p>Sync your inventory with Google Sheets for easy access and collaboration.</p>"
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        # Authentication status
        self.auth_group = QGroupBox("Authentication")
        auth_layout = QVBoxLayout()

        self.auth_status_label = QLabel("Not authenticated")
        auth_layout.addWidget(self.auth_status_label)

        self.btn_authenticate = QPushButton("Authenticate with Google")
        self.btn_authenticate.clicked.connect(self.authenticate)
        auth_layout.addWidget(self.btn_authenticate)

        auth_help = QLabel(
            "<small><i>Note: You'll need a credentials.json file from Google Cloud Console. "
            "See documentation for setup instructions.</i></small>"
        )
        auth_help.setWordWrap(True)
        auth_layout.addWidget(auth_help)

        self.auth_group.setLayout(auth_layout)
        layout.addWidget(self.auth_group)

        # Spreadsheet configuration
        self.sheet_group = QGroupBox("Spreadsheet Configuration")
        sheet_layout = QVBoxLayout()

        # Option 1: Create new
        self.radio_create = QRadioButton("Create new spreadsheet")
        self.radio_create.setChecked(True)
        self.radio_create.toggled.connect(self.on_option_changed)
        sheet_layout.addWidget(self.radio_create)

        create_layout = QHBoxLayout()
        create_layout.addSpacing(30)
        create_layout.addWidget(QLabel("Title:"))
        self.input_sheet_title = QLineEdit("Inventory Mapper")
        create_layout.addWidget(self.input_sheet_title)
        sheet_layout.addLayout(create_layout)

        sheet_layout.addSpacing(10)

        # Option 2: Use existing
        self.radio_existing = QRadioButton("Connect to existing spreadsheet")
        self.radio_existing.toggled.connect(self.on_option_changed)
        sheet_layout.addWidget(self.radio_existing)

        existing_layout = QHBoxLayout()
        existing_layout.addSpacing(30)
        existing_layout.addWidget(QLabel("Spreadsheet ID:"))
        self.input_sheet_id = QLineEdit()
        self.input_sheet_id.setPlaceholderText("e.g., 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms")
        self.input_sheet_id.setEnabled(False)
        existing_layout.addWidget(self.input_sheet_id)
        sheet_layout.addLayout(existing_layout)

        help_text = QLabel(
            "<small><i>Find the spreadsheet ID in the URL: "
            "https://docs.google.com/spreadsheets/d/<b>SPREADSHEET_ID</b>/edit</i></small>"
        )
        help_text.setWordWrap(True)
        help_text.setIndent(30)
        sheet_layout.addWidget(help_text)

        self.sheet_group.setLayout(sheet_layout)
        self.sheet_group.setEnabled(False)
        layout.addWidget(self.sheet_group)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        button_layout.addWidget(self.btn_cancel)

        self.btn_connect = QPushButton("Connect")
        self.btn_connect.clicked.connect(self.connect_sheet)
        self.btn_connect.setEnabled(False)
        button_layout.addWidget(self.btn_connect)

        layout.addLayout(button_layout)

        # Update initial state
        self.update_auth_status()

    def update_auth_status(self):
        """Update authentication status display."""
        is_authenticated = self.sync_controller.sheets_service.is_authenticated()

        if is_authenticated:
            self.auth_status_label.setText("✓ Authenticated with Google")
            self.btn_authenticate.setText("Re-authenticate")
            self.sheet_group.setEnabled(True)
            self.btn_connect.setEnabled(True)
        else:
            self.auth_status_label.setText("✗ Not authenticated")
            self.btn_authenticate.setText("Authenticate with Google")
            self.sheet_group.setEnabled(False)
            self.btn_connect.setEnabled(False)

    def on_option_changed(self):
        """Handle spreadsheet option change."""
        if self.radio_create.isChecked():
            self.input_sheet_title.setEnabled(True)
            self.input_sheet_id.setEnabled(False)
        else:
            self.input_sheet_title.setEnabled(False)
            self.input_sheet_id.setEnabled(True)

    def authenticate(self):
        """Authenticate with Google."""
        # Show progress dialog
        progress = QProgressDialog("Authenticating with Google...", None, 0, 0, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.show()

        # Create and start auth thread
        self.auth_thread = AuthThread(self.sync_controller)
        self.auth_thread.success.connect(lambda: self.on_auth_success(progress))
        self.auth_thread.error.connect(lambda e: self.on_auth_error(progress, e))
        self.auth_thread.start()

    def on_auth_success(self, progress: QProgressDialog):
        """Handle successful authentication."""
        progress.close()
        self.update_auth_status()
        QMessageBox.information(
            self,
            "Authentication Successful",
            "Successfully authenticated with Google Sheets!"
        )

    def on_auth_error(self, progress: QProgressDialog, error: str):
        """Handle authentication error."""
        progress.close()
        QMessageBox.critical(
            self,
            "Authentication Failed",
            f"Failed to authenticate with Google:\n\n{error}\n\n"
            "Please ensure:\n"
            "1. You have credentials.json file\n"
            "2. Google Sheets API is enabled\n"
            "3. You granted necessary permissions"
        )

    def connect_sheet(self):
        """Connect to or create spreadsheet."""
        if not self.sync_controller.sheets_service.is_authenticated():
            QMessageBox.warning(
                self,
                "Not Authenticated",
                "Please authenticate with Google first."
            )
            return

        try:
            if self.radio_create.isChecked():
                # Create new spreadsheet
                title = self.input_sheet_title.text().strip()
                if not title:
                    QMessageBox.warning(self, "Invalid Title", "Please enter a title.")
                    return

                progress = QProgressDialog("Creating spreadsheet...", None, 0, 0, self)
                progress.setWindowModality(Qt.WindowModal)
                progress.show()

                spreadsheet_id = self.sync_controller.create_new_sheet(title)
                progress.close()

                if spreadsheet_id:
                    QMessageBox.information(
                        self,
                        "Spreadsheet Created",
                        f"Successfully created spreadsheet!\n\n"
                        f"Spreadsheet ID: {spreadsheet_id}\n\n"
                        f"You can access it at:\n"
                        f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"
                    )
                    self.accept()
                else:
                    QMessageBox.critical(self, "Error", "Failed to create spreadsheet.")

            else:
                # Connect to existing spreadsheet
                spreadsheet_id = self.input_sheet_id.text().strip()
                if not spreadsheet_id:
                    QMessageBox.warning(
                        self,
                        "Invalid ID",
                        "Please enter a spreadsheet ID."
                    )
                    return

                # Verify spreadsheet exists
                progress = QProgressDialog("Connecting to spreadsheet...", None, 0, 0, self)
                progress.setWindowModality(Qt.WindowModal)
                progress.show()

                try:
                    self.sync_controller.sheets_service.get_spreadsheet(spreadsheet_id)
                    self.sync_controller.set_spreadsheet(spreadsheet_id)
                    progress.close()

                    QMessageBox.information(
                        self,
                        "Connected",
                        f"Successfully connected to spreadsheet!\n\n"
                        f"Spreadsheet ID: {spreadsheet_id}"
                    )
                    self.accept()

                except Exception as e:
                    progress.close()
                    QMessageBox.critical(
                        self,
                        "Connection Failed",
                        f"Failed to connect to spreadsheet:\n\n{str(e)}\n\n"
                        "Please verify:\n"
                        "1. The spreadsheet ID is correct\n"
                        "2. You have access to the spreadsheet\n"
                        "3. The spreadsheet exists"
                    )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"An error occurred:\n\n{str(e)}"
            )
