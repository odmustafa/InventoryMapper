"""
Inventory Controller - manages inventory operations.

Coordinates between UI, inventory models, and database for inventory management.
"""

from typing import Optional, List, Dict, Any
from PySide6.QtCore import QObject, Signal
import csv
from pathlib import Path

from app.models.inventory_item import InventoryItem
from app.models.database import get_database


class InventoryController(QObject):
    """
    Controller for inventory management operations.

    Manages:
    - CRUD operations for inventory items
    - Search and filtering
    - Category management
    - CSV import/export
    - Bulk operations

    Signals:
        item_created: Emitted when an item is created (item_id)
        item_updated: Emitted when an item is updated (item_id)
        item_deleted: Emitted when an item is deleted (item_id)
        items_changed: Emitted when inventory list changes
    """

    item_created = Signal(int)
    item_updated = Signal(int)
    item_deleted = Signal(int)
    items_changed = Signal()

    def __init__(self):
        """Initialize inventory controller."""
        super().__init__()

    # CRUD Operations

    def create_item(self, **kwargs) -> int:
        """
        Create a new inventory item.

        Args:
            **kwargs: Item attributes

        Returns:
            Item ID
        """
        item = InventoryItem(**kwargs)
        item_id = item.save()

        self.item_created.emit(item_id)
        self.items_changed.emit()

        return item_id

    def update_item(self, item_id: int, **kwargs) -> bool:
        """
        Update an existing inventory item.

        Args:
            item_id: Item ID to update
            **kwargs: Item attributes to update

        Returns:
            True if successful, False otherwise
        """
        item = InventoryItem.load(item_id)
        if not item:
            return False

        # Update attributes
        for key, value in kwargs.items():
            if hasattr(item, key):
                setattr(item, key, value)

        item.save()

        self.item_updated.emit(item_id)
        self.items_changed.emit()

        return True

    def delete_item(self, item_id: int) -> bool:
        """
        Delete an inventory item.

        Args:
            item_id: Item ID to delete

        Returns:
            True if successful, False otherwise
        """
        item = InventoryItem.load(item_id)
        if not item:
            return False

        item.delete()

        self.item_deleted.emit(item_id)
        self.items_changed.emit()

        return True

    def get_item(self, item_id: int) -> Optional[InventoryItem]:
        """
        Get an inventory item by ID.

        Args:
            item_id: Item ID

        Returns:
            InventoryItem instance or None
        """
        return InventoryItem.load(item_id)

    def get_all_items(self, limit: Optional[int] = None, offset: int = 0) -> List[InventoryItem]:
        """
        Get all inventory items.

        Args:
            limit: Maximum number of items
            offset: Number of items to skip

        Returns:
            List of InventoryItem instances
        """
        return InventoryItem.load_all(limit=limit, offset=offset)

    def search_items(self, query: str, limit: int = 100) -> List[InventoryItem]:
        """
        Search inventory items.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of matching InventoryItem instances
        """
        return InventoryItem.search(query, limit=limit)

    def get_items_by_category(self, category_id: int) -> List[InventoryItem]:
        """
        Get all items in a category.

        Args:
            category_id: Category ID

        Returns:
            List of InventoryItem instances
        """
        return InventoryItem.load_by_category(category_id)

    def get_low_stock_items(self) -> List[InventoryItem]:
        """
        Get items with quantity below minimum stock level.

        Returns:
            List of low stock InventoryItem instances
        """
        db = get_database()
        rows = db.fetchall("""
            SELECT * FROM inventory_items
            WHERE quantity < min_stock_level AND quantity > 0
            ORDER BY (min_stock_level - quantity) DESC
        """)

        return [InventoryItem.from_row(row) for row in rows]

    def get_out_of_stock_items(self) -> List[InventoryItem]:
        """
        Get items that are out of stock.

        Returns:
            List of out of stock InventoryItem instances
        """
        db = get_database()
        rows = db.fetchall("""
            SELECT * FROM inventory_items
            WHERE quantity = 0
            ORDER BY name
        """)

        return [InventoryItem.from_row(row) for row in rows]

    # Category Operations

    def create_category(self, name: str, parent_id: Optional[int] = None, color: Optional[str] = None) -> int:
        """
        Create a new category.

        Args:
            name: Category name
            parent_id: Parent category ID for nested categories
            color: Hex color for category

        Returns:
            Category ID
        """
        db = get_database()
        with db.transaction():
            cursor = db.execute("""
                INSERT INTO categories (name, parent_category_id, color)
                VALUES (?, ?, ?)
            """, (name, parent_id, color))
            return cursor.lastrowid

    def get_all_categories(self) -> List[Dict[str, Any]]:
        """
        Get all categories.

        Returns:
            List of category dictionaries
        """
        db = get_database()
        rows = db.fetchall("SELECT * FROM categories ORDER BY name")
        return [dict(row) for row in rows]

    def delete_category(self, category_id: int) -> bool:
        """
        Delete a category.

        Args:
            category_id: Category ID to delete

        Returns:
            True if successful
        """
        db = get_database()
        with db.transaction():
            db.execute("DELETE FROM categories WHERE id = ?", (category_id,))
        return True

    # CSV Import/Export

    def import_from_csv(self, csv_path: str) -> tuple[int, List[str]]:
        """
        Import inventory items from CSV file.

        Expected CSV columns: sku, name, description, quantity, min_stock_level, unit_price, tags, category

        Args:
            csv_path: Path to CSV file

        Returns:
            Tuple of (number of items imported, list of error messages)
        """
        imported_count = 0
        errors = []

        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                for row_num, row in enumerate(reader, start=2):  # Start at 2 (1 is header)
                    try:
                        # Parse tags
                        tags = []
                        if 'tags' in row and row['tags']:
                            tags = [tag.strip() for tag in row['tags'].split(',')]

                        # Handle category
                        category_id = None
                        if 'category' in row and row['category']:
                            category_id = self._get_or_create_category(row['category'])

                        # Create item
                        item = InventoryItem(
                            sku=row.get('sku'),
                            name=row.get('name', ''),
                            description=row.get('description', ''),
                            quantity=int(row.get('quantity', 0)),
                            min_stock_level=int(row.get('min_stock_level', 0)),
                            unit_price=float(row.get('unit_price')) if row.get('unit_price') else None,
                            category_id=category_id
                        )
                        item.set_tags_list(tags)
                        item.save()

                        imported_count += 1

                    except Exception as e:
                        errors.append(f"Row {row_num}: {str(e)}")

        except Exception as e:
            errors.append(f"Failed to read CSV file: {str(e)}")

        if imported_count > 0:
            self.items_changed.emit()

        return imported_count, errors

    def export_to_csv(self, csv_path: str, items: Optional[List[InventoryItem]] = None) -> bool:
        """
        Export inventory items to CSV file.

        Args:
            csv_path: Path to save CSV file
            items: List of items to export (None = all items)

        Returns:
            True if successful
        """
        if items is None:
            items = self.get_all_items()

        try:
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)

                # Write header
                writer.writerow([
                    'sku', 'name', 'description', 'category', 'quantity',
                    'min_stock_level', 'unit_price', 'tags'
                ])

                # Write items
                for item in items:
                    # Get category name
                    category_name = ''
                    if item.category_id:
                        db = get_database()
                        row = db.fetchone("SELECT name FROM categories WHERE id = ?", (item.category_id,))
                        if row:
                            category_name = row['name']

                    # Get tags as comma-separated string
                    tags_str = ', '.join(item.get_tags_list())

                    writer.writerow([
                        item.sku or '',
                        item.name,
                        item.description,
                        category_name,
                        item.quantity,
                        item.min_stock_level,
                        item.unit_price or '',
                        tags_str
                    ])

            return True

        except Exception as e:
            print(f"Failed to export CSV: {e}")
            return False

    def _get_or_create_category(self, category_name: str) -> int:
        """
        Get existing category ID or create new one.

        Args:
            category_name: Category name

        Returns:
            Category ID
        """
        db = get_database()

        # Check if category exists
        row = db.fetchone("SELECT id FROM categories WHERE name = ?", (category_name,))
        if row:
            return row['id']

        # Create new category
        return self.create_category(category_name)

    # Statistics

    def get_total_items(self) -> int:
        """Get total number of inventory items."""
        db = get_database()
        row = db.fetchone("SELECT COUNT(*) as count FROM inventory_items")
        return row['count'] if row else 0

    def get_total_quantity(self) -> int:
        """Get total quantity of all items."""
        db = get_database()
        row = db.fetchone("SELECT SUM(quantity) as total FROM inventory_items")
        return row['total'] if row and row['total'] else 0

    def get_total_value(self) -> float:
        """Get total value of all inventory."""
        db = get_database()
        row = db.fetchone("""
            SELECT SUM(quantity * unit_price) as total
            FROM inventory_items
            WHERE unit_price IS NOT NULL
        """)
        return row['total'] if row and row['total'] else 0.0
