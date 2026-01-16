"""
Inventory Mapper - Main application entry point.

A desktop application for creating interactive floor plans with spatial
inventory tracking, Google Sheets integration, and reseller marketplace features.
"""

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from app.ui.main_window import MainWindow
from app.models.database import get_database
from app.constants import APP_NAME, APP_ORGANIZATION


def main():
    """Main application entry point."""
    # Enable high DPI support
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(APP_ORGANIZATION)

    # Set application style (optional - can be customized)
    app.setStyle("Fusion")

    # Initialize database
    try:
        db = get_database()
        print(f"Database initialized at: {db.db_path}")
    except Exception as e:
        print(f"Error initializing database: {e}")
        return 1

    # Create and show main window
    window = MainWindow()
    window.show()

    # Start event loop
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
