"""
Inventory Item model for database operations.

Handles CRUD operations for inventory items with full-text search support.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import json

from app.models.database import get_database


class InventoryItem:
    """
    Inventory item model representing a physical item in storage.

    Attributes:
        id: Database ID
        sku: Stock keeping unit (unique identifier)
        name: Item name
        description: Detailed description
        category_id: Associated category ID
        quantity: Current stock quantity
        min_stock_level: Minimum stock level for alerts
        unit_price: Price per unit
        image_url: URL or path to item image
        image_data: Binary image data (thumbnail)
        tags: JSON string with tags
        custom_fields: JSON string with custom metadata
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    def __init__(
        self,
        id: Optional[int] = None,
        sku: Optional[str] = None,
        name: str = "",
        description: str = "",
        category_id: Optional[int] = None,
        quantity: int = 0,
        min_stock_level: int = 0,
        unit_price: Optional[float] = None,
        image_url: Optional[str] = None,
        image_data: Optional[bytes] = None,
        tags: str = "[]",
        custom_fields: str = "{}",
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        """Initialize inventory item."""
        self.id = id
        self.sku = sku
        self.name = name
        self.description = description
        self.category_id = category_id
        self.quantity = quantity
        self.min_stock_level = min_stock_level
        self.unit_price = unit_price
        self.image_url = image_url
        self.image_data = image_data
        self.tags = tags
        self.custom_fields = custom_fields
        self.created_at = created_at
        self.updated_at = updated_at

    def save(self) -> int:
        """
        Save inventory item to database (insert or update).

        Returns:
            Item ID
        """
        db = get_database()

        if self.id is None:
            # Insert new item
            with db.transaction():
                cursor = db.execute("""
                    INSERT INTO inventory_items (
                        sku, name, description, category_id,
                        quantity, min_stock_level, unit_price,
                        image_url, image_data, tags, custom_fields
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.sku,
                    self.name,
                    self.description,
                    self.category_id,
                    self.quantity,
                    self.min_stock_level,
                    self.unit_price,
                    self.image_url,
                    self.image_data,
                    self.tags,
                    self.custom_fields
                ))
                self.id = cursor.lastrowid
        else:
            # Update existing item
            with db.transaction():
                db.execute("""
                    UPDATE inventory_items SET
                        sku = ?,
                        name = ?,
                        description = ?,
                        category_id = ?,
                        quantity = ?,
                        min_stock_level = ?,
                        unit_price = ?,
                        image_url = ?,
                        image_data = ?,
                        tags = ?,
                        custom_fields = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    self.sku,
                    self.name,
                    self.description,
                    self.category_id,
                    self.quantity,
                    self.min_stock_level,
                    self.unit_price,
                    self.image_url,
                    self.image_data,
                    self.tags,
                    self.custom_fields,
                    self.id
                ))

        return self.id

    @classmethod
    def load(cls, item_id: int) -> Optional["InventoryItem"]:
        """
        Load inventory item from database.

        Args:
            item_id: Item ID

        Returns:
            InventoryItem instance or None if not found
        """
        db = get_database()
        row = db.fetchone("SELECT * FROM inventory_items WHERE id = ?", (item_id,))

        if row:
            return cls.from_row(row)
        return None

    @classmethod
    def load_all(cls, limit: Optional[int] = None, offset: int = 0) -> List["InventoryItem"]:
        """
        Load all inventory items from database.

        Args:
            limit: Maximum number of items to return
            offset: Number of items to skip

        Returns:
            List of InventoryItem instances
        """
        db = get_database()

        query = "SELECT * FROM inventory_items ORDER BY updated_at DESC"
        if limit:
            query += f" LIMIT {limit} OFFSET {offset}"

        rows = db.fetchall(query)
        return [cls.from_row(row) for row in rows]

    @classmethod
    def search(cls, query: str, limit: int = 100) -> List["InventoryItem"]:
        """
        Search inventory items using full-text search.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of matching InventoryItem instances
        """
        if not query.strip():
            return cls.load_all(limit=limit)

        db = get_database()

        # Use FTS5 for fast full-text search
        rows = db.fetchall("""
            SELECT inventory_items.*
            FROM inventory_items
            JOIN inventory_fts ON inventory_items.id = inventory_fts.rowid
            WHERE inventory_fts MATCH ?
            ORDER BY rank
            LIMIT ?
        """, (query, limit))

        return [cls.from_row(row) for row in rows]

    @classmethod
    def load_by_category(cls, category_id: int) -> List["InventoryItem"]:
        """
        Load all items in a category.

        Args:
            category_id: Category ID

        Returns:
            List of InventoryItem instances
        """
        db = get_database()
        rows = db.fetchall("""
            SELECT * FROM inventory_items
            WHERE category_id = ?
            ORDER BY name
        """, (category_id,))

        return [cls.from_row(row) for row in rows]

    @classmethod
    def from_row(cls, row) -> "InventoryItem":
        """
        Create InventoryItem instance from database row.

        Args:
            row: Database row

        Returns:
            InventoryItem instance
        """
        return cls(
            id=row["id"],
            sku=row["sku"],
            name=row["name"],
            description=row["description"],
            category_id=row["category_id"],
            quantity=row["quantity"],
            min_stock_level=row["min_stock_level"],
            unit_price=row["unit_price"],
            image_url=row["image_url"],
            image_data=row["image_data"],
            tags=row["tags"],
            custom_fields=row["custom_fields"],
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )

    def delete(self):
        """Delete inventory item from database."""
        if self.id:
            db = get_database()
            with db.transaction():
                db.execute("DELETE FROM inventory_items WHERE id = ?", (self.id,))
            self.id = None

    def get_tags_list(self) -> List[str]:
        """
        Parse tags JSON string to list.

        Returns:
            List of tags
        """
        try:
            return json.loads(self.tags)
        except json.JSONDecodeError:
            return []

    def set_tags_list(self, tags: List[str]):
        """
        Set tags from list.

        Args:
            tags: List of tag strings
        """
        self.tags = json.dumps(tags)

    def get_custom_fields_dict(self) -> Dict[str, Any]:
        """
        Parse custom fields JSON string to dictionary.

        Returns:
            Custom fields dictionary
        """
        try:
            return json.loads(self.custom_fields)
        except json.JSONDecodeError:
            return {}

    def set_custom_fields_dict(self, fields: Dict[str, Any]):
        """
        Set custom fields from dictionary.

        Args:
            fields: Custom fields data
        """
        self.custom_fields = json.dumps(fields)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert inventory item to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "id": self.id,
            "sku": self.sku,
            "name": self.name,
            "description": self.description,
            "category_id": self.category_id,
            "quantity": self.quantity,
            "min_stock_level": self.min_stock_level,
            "unit_price": self.unit_price,
            "image_url": self.image_url,
            "tags": self.get_tags_list(),
            "custom_fields": self.get_custom_fields_dict(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    @property
    def stock_status(self) -> str:
        """
        Get stock status string.

        Returns:
            "out_of_stock", "low_stock", or "in_stock"
        """
        if self.quantity == 0:
            return "out_of_stock"
        elif self.quantity < self.min_stock_level:
            return "low_stock"
        else:
            return "in_stock"
