"""
Shape model for database operations.

Handles CRUD operations for vector shapes on floor plans.
"""

from typing import Optional, List, Dict, Any
import json

from app.models.database import get_database


class Shape:
    """
    Shape model representing a vector graphics element.

    Attributes:
        id: Database ID
        floor_plan_id: Associated floor plan ID
        layer_id: Associated layer ID
        shape_type: Type of shape (rectangle, line, polygon, etc.)
        geometry: JSON string with geometry data
        style: JSON string with style data
        label: Optional text label
        created_at: Creation timestamp
    """

    def __init__(
        self,
        id: Optional[int] = None,
        floor_plan_id: Optional[int] = None,
        layer_id: Optional[int] = None,
        shape_type: str = "rectangle",
        geometry: str = "{}",
        style: str = "{}",
        label: str = "",
        created_at: Optional[str] = None
    ):
        """Initialize shape."""
        self.id = id
        self.floor_plan_id = floor_plan_id
        self.layer_id = layer_id
        self.shape_type = shape_type
        self.geometry = geometry
        self.style = style
        self.label = label
        self.created_at = created_at

    def save(self) -> int:
        """
        Save shape to database (insert or update).

        Returns:
            Shape ID
        """
        db = get_database()

        if self.id is None:
            # Insert new shape
            with db.transaction():
                cursor = db.execute("""
                    INSERT INTO shapes (
                        floor_plan_id, layer_id, shape_type,
                        geometry, style, label
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    self.floor_plan_id,
                    self.layer_id,
                    self.shape_type,
                    self.geometry,
                    self.style,
                    self.label
                ))
                self.id = cursor.lastrowid
        else:
            # Update existing shape
            with db.transaction():
                db.execute("""
                    UPDATE shapes SET
                        floor_plan_id = ?,
                        layer_id = ?,
                        shape_type = ?,
                        geometry = ?,
                        style = ?,
                        label = ?
                    WHERE id = ?
                """, (
                    self.floor_plan_id,
                    self.layer_id,
                    self.shape_type,
                    self.geometry,
                    self.style,
                    self.label,
                    self.id
                ))

        return self.id

    @classmethod
    def load(cls, shape_id: int) -> Optional["Shape"]:
        """
        Load shape from database.

        Args:
            shape_id: Shape ID

        Returns:
            Shape instance or None if not found
        """
        db = get_database()
        row = db.fetchone("SELECT * FROM shapes WHERE id = ?", (shape_id,))

        if row:
            return cls.from_row(row)
        return None

    @classmethod
    def load_by_floor_plan(cls, floor_plan_id: int) -> List["Shape"]:
        """
        Load all shapes for a floor plan.

        Args:
            floor_plan_id: Floor plan ID

        Returns:
            List of Shape instances
        """
        db = get_database()
        rows = db.fetchall("""
            SELECT * FROM shapes
            WHERE floor_plan_id = ?
            ORDER BY created_at
        """, (floor_plan_id,))

        return [cls.from_row(row) for row in rows]

    @classmethod
    def load_by_layer(cls, layer_id: int) -> List["Shape"]:
        """
        Load all shapes in a layer.

        Args:
            layer_id: Layer ID

        Returns:
            List of Shape instances
        """
        db = get_database()
        rows = db.fetchall("""
            SELECT * FROM shapes
            WHERE layer_id = ?
            ORDER BY created_at
        """, (layer_id,))

        return [cls.from_row(row) for row in rows]

    @classmethod
    def from_row(cls, row) -> "Shape":
        """
        Create Shape instance from database row.

        Args:
            row: Database row

        Returns:
            Shape instance
        """
        return cls(
            id=row["id"],
            floor_plan_id=row["floor_plan_id"],
            layer_id=row["layer_id"],
            shape_type=row["shape_type"],
            geometry=row["geometry"],
            style=row["style"],
            label=row["label"],
            created_at=row["created_at"]
        )

    def delete(self):
        """Delete shape from database."""
        if self.id:
            db = get_database()
            with db.transaction():
                db.execute("DELETE FROM shapes WHERE id = ?", (self.id,))
            self.id = None

    def get_geometry_dict(self) -> Dict[str, Any]:
        """
        Parse geometry JSON string to dictionary.

        Returns:
            Geometry dictionary
        """
        try:
            return json.loads(self.geometry)
        except json.JSONDecodeError:
            return {}

    def set_geometry_dict(self, geometry_dict: Dict[str, Any]):
        """
        Set geometry from dictionary.

        Args:
            geometry_dict: Geometry data
        """
        self.geometry = json.dumps(geometry_dict)

    def get_style_dict(self) -> Dict[str, Any]:
        """
        Parse style JSON string to dictionary.

        Returns:
            Style dictionary
        """
        try:
            return json.loads(self.style)
        except json.JSONDecodeError:
            return {}

    def set_style_dict(self, style_dict: Dict[str, Any]):
        """
        Set style from dictionary.

        Args:
            style_dict: Style data
        """
        self.style = json.dumps(style_dict)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert shape to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "id": self.id,
            "floor_plan_id": self.floor_plan_id,
            "layer_id": self.layer_id,
            "shape_type": self.shape_type,
            "geometry": self.get_geometry_dict(),
            "style": self.get_style_dict(),
            "label": self.label,
            "created_at": self.created_at
        }
