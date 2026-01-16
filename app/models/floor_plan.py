"""
Floor Plan model for database operations.

Handles CRUD operations for floor plans and their associated layers.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path

from app.models.database import get_database


class FloorPlan:
    """
    Floor plan model representing a drawable canvas with layers and shapes.

    Attributes:
        id: Database ID
        name: Floor plan name
        description: Optional description
        width: Canvas width in real-world units
        height: Canvas height in real-world units
        unit: Measurement unit (feet, meters, etc.)
        background_image_path: Path to background image file
        created_at: Creation timestamp
        updated_at: Last update timestamp
        google_sheet_id: Linked Google Sheet ID
        last_synced_at: Last sync timestamp
    """

    def __init__(
        self,
        id: Optional[int] = None,
        name: str = "Untitled Floor Plan",
        description: str = "",
        width: float = 100.0,
        height: float = 80.0,
        unit: str = "feet",
        background_image_path: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        google_sheet_id: Optional[str] = None,
        last_synced_at: Optional[datetime] = None
    ):
        """Initialize floor plan."""
        self.id = id
        self.name = name
        self.description = description
        self.width = width
        self.height = height
        self.unit = unit
        self.background_image_path = background_image_path
        self.created_at = created_at
        self.updated_at = updated_at
        self.google_sheet_id = google_sheet_id
        self.last_synced_at = last_synced_at

    def save(self) -> int:
        """
        Save floor plan to database (insert or update).

        Returns:
            Floor plan ID
        """
        db = get_database()

        if self.id is None:
            # Insert new floor plan
            with db.transaction():
                cursor = db.execute("""
                    INSERT INTO floor_plans (
                        name, description, width, height, unit,
                        background_image_path, google_sheet_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.name,
                    self.description,
                    self.width,
                    self.height,
                    self.unit,
                    self.background_image_path,
                    self.google_sheet_id
                ))
                self.id = cursor.lastrowid

                # Create default layer
                db.execute("""
                    INSERT INTO layers (floor_plan_id, name, z_index)
                    VALUES (?, ?, ?)
                """, (self.id, "Default Layer", 0))

        else:
            # Update existing floor plan
            with db.transaction():
                db.execute("""
                    UPDATE floor_plans SET
                        name = ?,
                        description = ?,
                        width = ?,
                        height = ?,
                        unit = ?,
                        background_image_path = ?,
                        google_sheet_id = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    self.name,
                    self.description,
                    self.width,
                    self.height,
                    self.unit,
                    self.background_image_path,
                    self.google_sheet_id,
                    self.id
                ))

        return self.id

    @classmethod
    def load(cls, floor_plan_id: int) -> Optional["FloorPlan"]:
        """
        Load floor plan from database.

        Args:
            floor_plan_id: Floor plan ID

        Returns:
            FloorPlan instance or None if not found
        """
        db = get_database()
        row = db.fetchone(
            "SELECT * FROM floor_plans WHERE id = ?",
            (floor_plan_id,)
        )

        if row:
            return cls.from_row(row)
        return None

    @classmethod
    def load_all(cls) -> List["FloorPlan"]:
        """
        Load all floor plans from database.

        Returns:
            List of FloorPlan instances
        """
        db = get_database()
        rows = db.fetchall("SELECT * FROM floor_plans ORDER BY updated_at DESC")
        return [cls.from_row(row) for row in rows]

    @classmethod
    def from_row(cls, row) -> "FloorPlan":
        """
        Create FloorPlan instance from database row.

        Args:
            row: Database row

        Returns:
            FloorPlan instance
        """
        return cls(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            width=row["width"],
            height=row["height"],
            unit=row["unit"],
            background_image_path=row["background_image_path"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            google_sheet_id=row["google_sheet_id"],
            last_synced_at=row["last_synced_at"]
        )

    def delete(self):
        """Delete floor plan from database (cascades to layers and shapes)."""
        if self.id:
            db = get_database()
            with db.transaction():
                db.execute("DELETE FROM floor_plans WHERE id = ?", (self.id,))
            self.id = None

    def get_layers(self) -> List[Dict[str, Any]]:
        """
        Get all layers for this floor plan.

        Returns:
            List of layer dictionaries
        """
        if not self.id:
            return []

        db = get_database()
        rows = db.fetchall("""
            SELECT * FROM layers
            WHERE floor_plan_id = ?
            ORDER BY z_index
        """, (self.id,))

        return [dict(row) for row in rows]

    def create_layer(self, name: str = "New Layer") -> int:
        """
        Create a new layer for this floor plan.

        Args:
            name: Layer name

        Returns:
            Layer ID
        """
        if not self.id:
            raise ValueError("Floor plan must be saved before creating layers")

        db = get_database()

        # Get max z_index
        row = db.fetchone("""
            SELECT MAX(z_index) as max_z FROM layers WHERE floor_plan_id = ?
        """, (self.id,))
        max_z = row["max_z"] if row["max_z"] is not None else -1

        with db.transaction():
            cursor = db.execute("""
                INSERT INTO layers (floor_plan_id, name, z_index)
                VALUES (?, ?, ?)
            """, (self.id, name, max_z + 1))
            return cursor.lastrowid

    def delete_layer(self, layer_id: int):
        """
        Delete a layer and its shapes.

        Args:
            layer_id: Layer ID to delete
        """
        db = get_database()
        with db.transaction():
            # Shapes will be cascade deleted due to ON DELETE SET NULL
            db.execute("DELETE FROM layers WHERE id = ?", (layer_id,))

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert floor plan to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "width": self.width,
            "height": self.height,
            "unit": self.unit,
            "background_image_path": self.background_image_path,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "google_sheet_id": self.google_sheet_id,
            "last_synced_at": self.last_synced_at.isoformat() if self.last_synced_at else None
        }
