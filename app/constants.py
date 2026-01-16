"""
Application constants for Inventory Mapper.

Defines colors, sizes, and other constant values used throughout the application.
"""

from PySide6.QtGui import QColor
from PySide6.QtCore import QSize

# Application Metadata
APP_NAME = "Inventory Mapper"
APP_VERSION = "1.0.0"
APP_ORGANIZATION = "InventoryMapper"

# Window Sizes
DEFAULT_WINDOW_WIDTH = 1400
DEFAULT_WINDOW_HEIGHT = 900
MIN_WINDOW_WIDTH = 1000
MIN_WINDOW_HEIGHT = 600

# Canvas Settings
DEFAULT_CANVAS_WIDTH = 100.0  # feet
DEFAULT_CANVAS_HEIGHT = 80.0  # feet
DEFAULT_GRID_SIZE = 1.0  # 1 foot/meter
MIN_ZOOM = 0.1
MAX_ZOOM = 10.0
DEFAULT_ZOOM = 1.0

# Stock Level Colors (RGB)
COLOR_OUT_OF_STOCK = QColor(255, 0, 0)  # Red
COLOR_LOW_STOCK = QColor(255, 165, 0)    # Orange
COLOR_IN_STOCK = QColor(0, 200, 0)       # Green
COLOR_UNKNOWN = QColor(128, 128, 128)    # Gray

# Shape Colors
COLOR_DEFAULT_STROKE = QColor(0, 0, 0)       # Black
COLOR_DEFAULT_FILL = QColor(200, 200, 200)   # Light Gray
COLOR_SELECTED = QColor(0, 120, 215)         # Blue
COLOR_GRID = QColor(220, 220, 220)           # Very Light Gray
COLOR_BACKGROUND = QColor(255, 255, 255)     # White

# Layer Colors
COLOR_LAYER_VISIBLE = QColor(0, 200, 0)      # Green
COLOR_LAYER_HIDDEN = QColor(200, 200, 200)   # Gray
COLOR_LAYER_LOCKED = QColor(255, 165, 0)     # Orange

# Drawing Tool Defaults
DEFAULT_STROKE_WIDTH = 2.0
DEFAULT_SELECTION_WIDTH = 3.0
HANDLE_SIZE = 8  # pixels

# Marker Settings
MARKER_SIZE = 20  # pixels
MARKER_ICON_SIZE = QSize(16, 16)
MARKER_PULSE_DURATION = 1000  # milliseconds

# Panel Sizes
INVENTORY_PANEL_WIDTH = 300
LAYER_PANEL_WIDTH = 250
PROPERTY_PANEL_WIDTH = 250
TOOLBAR_ICON_SIZE = QSize(24, 24)

# Sync Settings
DEFAULT_SYNC_INTERVAL = 300  # seconds (5 minutes)
SYNC_STATUS_SYNCED = "synced"
SYNC_STATUS_LOCAL_MODIFIED = "local_modified"
SYNC_STATUS_REMOTE_MODIFIED = "remote_modified"
SYNC_STATUS_CONFLICT = "conflict"

# Measurement Units
UNIT_FEET = "feet"
UNIT_METERS = "meters"
UNIT_INCHES = "inches"
UNIT_CENTIMETERS = "centimeters"

SUPPORTED_UNITS = [UNIT_FEET, UNIT_METERS, UNIT_INCHES, UNIT_CENTIMETERS]

# File Formats
EXPORT_FORMAT_JSON = "json"
EXPORT_FORMAT_XML = "xml"
EXPORT_FORMAT_CSV = "csv"
EXPORT_FORMAT_PNG = "png"
EXPORT_FORMAT_PDF = "pdf"

# Shape Types
SHAPE_RECTANGLE = "rectangle"
SHAPE_LINE = "line"
SHAPE_POLYGON = "polygon"
SHAPE_DIMENSION = "dimension"
SHAPE_IMAGE = "image"

# Database Constants
MAX_SKU_LENGTH = 100
MAX_NAME_LENGTH = 255
MAX_DESCRIPTION_LENGTH = 2000

# UI Settings
SEARCH_DEBOUNCE_MS = 300  # milliseconds
DOUBLE_CLICK_TIMEOUT_MS = 500  # milliseconds
TOOLTIP_DELAY_MS = 500  # milliseconds

# Keyboard Shortcuts
SHORTCUT_NEW = "Ctrl+N"
SHORTCUT_OPEN = "Ctrl+O"
SHORTCUT_SAVE = "Ctrl+S"
SHORTCUT_EXPORT = "Ctrl+E"
SHORTCUT_UNDO = "Ctrl+Z"
SHORTCUT_REDO = "Ctrl+Shift+Z"
SHORTCUT_DELETE = "Delete"
SHORTCUT_SELECT_ALL = "Ctrl+A"
SHORTCUT_ZOOM_IN = "Ctrl+="
SHORTCUT_ZOOM_OUT = "Ctrl+-"
SHORTCUT_ZOOM_FIT = "Ctrl+0"
SHORTCUT_FIND = "Ctrl+F"

# Google Sheets Settings
GOOGLE_SHEETS_SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file'
]

# Image Settings
MAX_IMAGE_WIDTH = 4000  # pixels
MAX_IMAGE_HEIGHT = 4000  # pixels
THUMBNAIL_SIZE = QSize(64, 64)
SUPPORTED_IMAGE_FORMATS = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff']

# Performance Settings
CACHE_MODE_ENABLED = True
MAX_UNDO_STACK_SIZE = 50
