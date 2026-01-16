"""
Database module for Inventory Mapper application.

Handles SQLite connection, schema creation, migrations, and database utilities.
"""

import sqlite3
import hashlib
import json
from pathlib import Path
from typing import Optional, Dict, List, Any, Tuple
from contextlib import contextmanager
import appdirs


class Database:
    """
    SQLite database manager for the Inventory Mapper application.

    Implements connection pooling, schema management, and provides
    context managers for transaction handling.
    """

    SCHEMA_VERSION = 1

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file. If None, uses default user data directory.
        """
        if db_path is None:
            # Use platform-specific user data directory
            app_data_dir = appdirs.user_data_dir("InventoryMapper", "InventoryMapper")
            Path(app_data_dir).mkdir(parents=True, exist_ok=True)
            db_path = Path(app_data_dir) / "inventory_mapper.db"

        self.db_path = Path(db_path)
        self.connection: Optional[sqlite3.Connection] = None
        self._connect()
        self._initialize_schema()

    def _connect(self):
        """Establish connection to SQLite database."""
        self.connection = sqlite3.connect(
            str(self.db_path),
            check_same_thread=False  # Allow multi-threaded access
        )
        self.connection.row_factory = sqlite3.Row  # Enable dict-like access to rows

        # Enable foreign key constraints
        self.connection.execute("PRAGMA foreign_keys = ON")

        # Enable WAL mode for better concurrent access
        self.connection.execute("PRAGMA journal_mode = WAL")

    @contextmanager
    def transaction(self):
        """
        Context manager for database transactions.

        Usage:
            with db.transaction():
                db.execute("INSERT INTO ...")
                db.execute("UPDATE ...")
            # Auto-commits on success, rolls back on exception
        """
        try:
            yield self.connection
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise

    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute a single SQL statement."""
        return self.connection.execute(query, params)

    def executemany(self, query: str, params: List[tuple]) -> sqlite3.Cursor:
        """Execute a SQL statement multiple times."""
        return self.connection.executemany(query, params)

    def fetchone(self, query: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        """Execute query and fetch one result."""
        cursor = self.execute(query, params)
        return cursor.fetchone()

    def fetchall(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """Execute query and fetch all results."""
        cursor = self.execute(query, params)
        return cursor.fetchall()

    def _initialize_schema(self):
        """Create database schema if it doesn't exist."""
        cursor = self.connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
        )

        if cursor.fetchone() is None:
            # New database, create all tables
            self._create_schema()
        else:
            # Existing database, check version and migrate if needed
            version = self.get_schema_version()
            if version < self.SCHEMA_VERSION:
                self._migrate_schema(version, self.SCHEMA_VERSION)

    def get_schema_version(self) -> int:
        """Get current database schema version."""
        cursor = self.connection.execute("SELECT version FROM schema_version")
        row = cursor.fetchone()
        return row[0] if row else 0

    def _create_schema(self):
        """Create all database tables and indexes."""
        with self.transaction():
            # Schema version tracking
            self.execute("""
                CREATE TABLE schema_version (
                    version INTEGER PRIMARY KEY
                )
            """)
            self.execute("INSERT INTO schema_version (version) VALUES (?)", (self.SCHEMA_VERSION,))

            # Floor Plans table
            self.execute("""
                CREATE TABLE floor_plans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    width REAL NOT NULL,
                    height REAL NOT NULL,
                    unit TEXT DEFAULT 'feet',
                    background_image_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    google_sheet_id TEXT,
                    last_synced_at TIMESTAMP
                )
            """)

            # Layers table
            self.execute("""
                CREATE TABLE layers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    floor_plan_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    visible INTEGER DEFAULT 1,
                    locked INTEGER DEFAULT 0,
                    z_index INTEGER DEFAULT 0,
                    opacity REAL DEFAULT 1.0,
                    FOREIGN KEY (floor_plan_id) REFERENCES floor_plans(id) ON DELETE CASCADE
                )
            """)

            # Shapes table
            self.execute("""
                CREATE TABLE shapes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    floor_plan_id INTEGER NOT NULL,
                    layer_id INTEGER,
                    shape_type TEXT NOT NULL,
                    geometry TEXT NOT NULL,
                    style TEXT,
                    label TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (floor_plan_id) REFERENCES floor_plans(id) ON DELETE CASCADE,
                    FOREIGN KEY (layer_id) REFERENCES layers(id) ON DELETE SET NULL
                )
            """)

            # Categories table
            self.execute("""
                CREATE TABLE categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    parent_category_id INTEGER,
                    color TEXT,
                    FOREIGN KEY (parent_category_id) REFERENCES categories(id) ON DELETE SET NULL
                )
            """)

            # Inventory Items table
            self.execute("""
                CREATE TABLE inventory_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sku TEXT UNIQUE,
                    name TEXT NOT NULL,
                    description TEXT,
                    category_id INTEGER,
                    quantity INTEGER DEFAULT 0,
                    min_stock_level INTEGER DEFAULT 0,
                    unit_price REAL,
                    image_url TEXT,
                    image_data BLOB,
                    tags TEXT,
                    custom_fields TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
                )
            """)

            # Inventory Placements table
            self.execute("""
                CREATE TABLE inventory_placements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    inventory_item_id INTEGER NOT NULL,
                    floor_plan_id INTEGER NOT NULL,
                    x_position REAL NOT NULL,
                    y_position REAL NOT NULL,
                    rotation REAL DEFAULT 0.0,
                    marker_style TEXT,
                    notes TEXT,
                    FOREIGN KEY (inventory_item_id) REFERENCES inventory_items(id) ON DELETE CASCADE,
                    FOREIGN KEY (floor_plan_id) REFERENCES floor_plans(id) ON DELETE CASCADE
                )
            """)

            # Sync State table
            self.execute("""
                CREATE TABLE sync_state (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_type TEXT NOT NULL,
                    entity_id INTEGER NOT NULL,
                    sheet_row_id INTEGER,
                    local_hash TEXT,
                    remote_hash TEXT,
                    sync_status TEXT,
                    last_synced_at TIMESTAMP,
                    UNIQUE(entity_type, entity_id)
                )
            """)

            # Create indexes for performance
            self.execute("CREATE INDEX idx_shapes_floor_plan ON shapes(floor_plan_id)")
            self.execute("CREATE INDEX idx_shapes_layer ON shapes(layer_id)")
            self.execute("CREATE INDEX idx_layers_floor_plan ON layers(floor_plan_id)")
            self.execute("CREATE INDEX idx_placements_item ON inventory_placements(inventory_item_id)")
            self.execute("CREATE INDEX idx_placements_floor_plan ON inventory_placements(floor_plan_id)")
            self.execute("CREATE INDEX idx_sync_entity ON sync_state(entity_type, entity_id)")
            self.execute("CREATE INDEX idx_inventory_category ON inventory_items(category_id)")

            # Full-text search for inventory items
            self.execute("""
                CREATE VIRTUAL TABLE inventory_fts USING fts5(
                    name,
                    description,
                    tags,
                    content=inventory_items,
                    content_rowid=id
                )
            """)

            # Triggers to keep FTS index updated
            self.execute("""
                CREATE TRIGGER inventory_fts_insert AFTER INSERT ON inventory_items BEGIN
                    INSERT INTO inventory_fts(rowid, name, description, tags)
                    VALUES (new.id, new.name, new.description, new.tags);
                END
            """)

            self.execute("""
                CREATE TRIGGER inventory_fts_update AFTER UPDATE ON inventory_items BEGIN
                    UPDATE inventory_fts SET
                        name = new.name,
                        description = new.description,
                        tags = new.tags
                    WHERE rowid = new.id;
                END
            """)

            self.execute("""
                CREATE TRIGGER inventory_fts_delete AFTER DELETE ON inventory_items BEGIN
                    DELETE FROM inventory_fts WHERE rowid = old.id;
                END
            """)

            # Trigger to update updated_at timestamp
            self.execute("""
                CREATE TRIGGER update_inventory_timestamp
                AFTER UPDATE ON inventory_items
                BEGIN
                    UPDATE inventory_items SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
                END
            """)

            self.execute("""
                CREATE TRIGGER update_floor_plan_timestamp
                AFTER UPDATE ON floor_plans
                BEGIN
                    UPDATE floor_plans SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
                END
            """)

    def _migrate_schema(self, from_version: int, to_version: int):
        """
        Migrate database schema from one version to another.

        Args:
            from_version: Current schema version
            to_version: Target schema version
        """
        # Future migrations will be implemented here
        # Example:
        # if from_version < 2 and to_version >= 2:
        #     self._migrate_v1_to_v2()
        pass

    @staticmethod
    def calculate_hash(data: Dict[str, Any]) -> str:
        """
        Calculate SHA256 hash of data dictionary for sync tracking.

        Args:
            data: Dictionary of data to hash

        Returns:
            Hexadecimal hash string
        """
        # Sort keys for consistent hashing
        json_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()

    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close connection."""
        self.close()
        return False


# Singleton instance
_db_instance: Optional[Database] = None


def get_database(db_path: Optional[Path] = None) -> Database:
    """
    Get singleton database instance.

    Args:
        db_path: Path to database file (only used on first call)

    Returns:
        Database instance
    """
    global _db_instance
    if _db_instance is None:
        _db_instance = Database(db_path)
    return _db_instance
