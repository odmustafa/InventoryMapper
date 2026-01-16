"""
Application configuration management using QSettings.

Handles persistent storage of user preferences and application settings.
"""

from typing import Any, Optional
from PySide6.QtCore import QSettings
from app.constants import (
    APP_NAME,
    APP_ORGANIZATION,
    DEFAULT_GRID_SIZE,
    DEFAULT_SYNC_INTERVAL,
    UNIT_FEET,
)


class Config:
    """
    Application configuration manager.

    Uses QSettings for cross-platform persistent storage of user preferences.
    """

    def __init__(self):
        """Initialize configuration with QSettings."""
        self.settings = QSettings(APP_ORGANIZATION, APP_NAME)

    # Window Settings
    @property
    def window_geometry(self) -> Optional[bytes]:
        """Get saved window geometry."""
        return self.settings.value("window/geometry")

    @window_geometry.setter
    def window_geometry(self, geometry: bytes):
        """Save window geometry."""
        self.settings.setValue("window/geometry", geometry)

    @property
    def window_state(self) -> Optional[bytes]:
        """Get saved window state (toolbars, docks, etc)."""
        return self.settings.value("window/state")

    @window_state.setter
    def window_state(self, state: bytes):
        """Save window state."""
        self.settings.setValue("window/state", state)

    # Canvas Settings
    @property
    def default_unit(self) -> str:
        """Get default measurement unit."""
        return self.settings.value("canvas/default_unit", UNIT_FEET)

    @default_unit.setter
    def default_unit(self, unit: str):
        """Set default measurement unit."""
        self.settings.setValue("canvas/default_unit", unit)

    @property
    def grid_size(self) -> float:
        """Get grid size."""
        return float(self.settings.value("canvas/grid_size", DEFAULT_GRID_SIZE))

    @grid_size.setter
    def grid_size(self, size: float):
        """Set grid size."""
        self.settings.setValue("canvas/grid_size", size)

    @property
    def grid_visible(self) -> bool:
        """Check if grid is visible by default."""
        return self.settings.value("canvas/grid_visible", True, type=bool)

    @grid_visible.setter
    def grid_visible(self, visible: bool):
        """Set grid visibility default."""
        self.settings.setValue("canvas/grid_visible", visible)

    @property
    def snap_to_grid(self) -> bool:
        """Check if snap to grid is enabled."""
        return self.settings.value("canvas/snap_to_grid", True, type=bool)

    @snap_to_grid.setter
    def snap_to_grid(self, enabled: bool):
        """Set snap to grid enabled state."""
        self.settings.setValue("canvas/snap_to_grid", enabled)

    # Google Sheets Settings
    @property
    def google_credentials_path(self) -> Optional[str]:
        """Get path to Google OAuth credentials file."""
        return self.settings.value("sync/google_credentials_path")

    @google_credentials_path.setter
    def google_credentials_path(self, path: str):
        """Set path to Google OAuth credentials file."""
        self.settings.setValue("sync/google_credentials_path", path)

    @property
    def sync_interval(self) -> int:
        """Get sync interval in seconds."""
        return int(self.settings.value("sync/interval", DEFAULT_SYNC_INTERVAL))

    @sync_interval.setter
    def sync_interval(self, interval: int):
        """Set sync interval in seconds."""
        self.settings.setValue("sync/interval", interval)

    @property
    def auto_sync_enabled(self) -> bool:
        """Check if auto-sync is enabled."""
        return self.settings.value("sync/auto_enabled", False, type=bool)

    @auto_sync_enabled.setter
    def auto_sync_enabled(self, enabled: bool):
        """Set auto-sync enabled state."""
        self.settings.setValue("sync/auto_enabled", enabled)

    # Recent Files
    @property
    def recent_floor_plans(self) -> list:
        """Get list of recent floor plan IDs."""
        return self.settings.value("recent/floor_plans", [], type=list)

    def add_recent_floor_plan(self, floor_plan_id: int, max_recent: int = 10):
        """
        Add floor plan to recent list.

        Args:
            floor_plan_id: ID of floor plan
            max_recent: Maximum number of recent items to keep
        """
        recent = self.recent_floor_plans
        # Remove if already in list
        if floor_plan_id in recent:
            recent.remove(floor_plan_id)
        # Add to front
        recent.insert(0, floor_plan_id)
        # Trim to max size
        recent = recent[:max_recent]
        self.settings.setValue("recent/floor_plans", recent)

    # Drawing Tool Settings
    @property
    def last_stroke_color(self) -> str:
        """Get last used stroke color (hex)."""
        return self.settings.value("drawing/stroke_color", "#000000")

    @last_stroke_color.setter
    def last_stroke_color(self, color: str):
        """Set last used stroke color."""
        self.settings.setValue("drawing/stroke_color", color)

    @property
    def last_fill_color(self) -> str:
        """Get last used fill color (hex)."""
        return self.settings.value("drawing/fill_color", "#CCCCCC")

    @last_fill_color.setter
    def last_fill_color(self, color: str):
        """Set last used fill color."""
        self.settings.setValue("drawing/fill_color", color)

    @property
    def last_stroke_width(self) -> float:
        """Get last used stroke width."""
        return float(self.settings.value("drawing/stroke_width", 2.0))

    @last_stroke_width.setter
    def last_stroke_width(self, width: float):
        """Set last used stroke width."""
        self.settings.setValue("drawing/stroke_width", width)

    # Inventory Panel Settings
    @property
    def inventory_sort_column(self) -> str:
        """Get inventory table sort column."""
        return self.settings.value("inventory/sort_column", "name")

    @inventory_sort_column.setter
    def inventory_sort_column(self, column: str):
        """Set inventory table sort column."""
        self.settings.setValue("inventory/sort_column", column)

    @property
    def inventory_sort_ascending(self) -> bool:
        """Check if inventory sort is ascending."""
        return self.settings.value("inventory/sort_ascending", True, type=bool)

    @inventory_sort_ascending.setter
    def inventory_sort_ascending(self, ascending: bool):
        """Set inventory sort order."""
        self.settings.setValue("inventory/sort_ascending", ascending)

    # General Methods
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get arbitrary setting value.

        Args:
            key: Setting key
            default: Default value if not found

        Returns:
            Setting value or default
        """
        return self.settings.value(key, default)

    def set(self, key: str, value: Any):
        """
        Set arbitrary setting value.

        Args:
            key: Setting key
            value: Value to set
        """
        self.settings.setValue(key, value)

    def clear(self):
        """Clear all settings."""
        self.settings.clear()

    def sync(self):
        """Force synchronize settings to storage."""
        self.settings.sync()


# Singleton instance
_config_instance: Optional[Config] = None


def get_config() -> Config:
    """
    Get singleton configuration instance.

    Returns:
        Config instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance
