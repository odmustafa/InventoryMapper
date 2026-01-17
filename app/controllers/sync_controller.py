"""
Sync Controller for Google Sheets synchronization.

Implements two-way synchronization with hash-based change detection
and conflict resolution.
"""

import hashlib
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum

from PySide6.QtCore import QObject, Signal

from app.models.inventory_item import InventoryItem
from app.models.database import Database
from app.services.google_sheets import GoogleSheetsService


class SyncStatus(Enum):
    """Sync status enumeration."""
    NOT_CONFIGURED = "not_configured"
    SYNCING = "syncing"
    SUCCESS = "success"
    ERROR = "error"
    CONFLICT = "conflict"


class SyncConflict:
    """Represents a sync conflict."""

    def __init__(
        self,
        item_id: int,
        local_item: InventoryItem,
        remote_item: Dict[str, Any],
        local_hash: str,
        remote_hash: str
    ):
        """
        Initialize sync conflict.

        Args:
            item_id: Inventory item ID
            local_item: Local inventory item
            remote_item: Remote item data
            local_hash: Hash of local item
            remote_hash: Hash of remote item
        """
        self.item_id = item_id
        self.local_item = local_item
        self.remote_item = remote_item
        self.local_hash = local_hash
        self.remote_hash = remote_hash


class SyncController(QObject):
    """
    Controller for Google Sheets synchronization.

    Implements two-way sync with hash-based change detection.

    Signals:
        sync_started: Emitted when sync begins
        sync_progress: Emitted during sync (progress_percent, message)
        sync_completed: Emitted when sync completes (success, message)
        sync_conflict: Emitted when conflict detected (conflict)
        status_changed: Emitted when sync status changes (status)
    """

    sync_started = Signal()
    sync_progress = Signal(int, str)  # progress, message
    sync_completed = Signal(bool, str)  # success, message
    sync_conflict = Signal(object)  # SyncConflict
    status_changed = Signal(str)  # status message

    def __init__(self):
        """Initialize sync controller."""
        super().__init__()

        self.sheets_service = GoogleSheetsService()
        self.db = Database()
        self.spreadsheet_id: Optional[str] = None
        self.status = SyncStatus.NOT_CONFIGURED

        # Track conflicts
        self.pending_conflicts: List[SyncConflict] = []

    def set_spreadsheet(self, spreadsheet_id: str):
        """
        Set Google Sheets spreadsheet ID.

        Args:
            spreadsheet_id: Spreadsheet ID
        """
        self.spreadsheet_id = spreadsheet_id
        self.status = SyncStatus.SUCCESS if spreadsheet_id else SyncStatus.NOT_CONFIGURED
        self._emit_status("Connected to Google Sheets" if spreadsheet_id else "Not configured")

    def is_configured(self) -> bool:
        """
        Check if sync is configured.

        Returns:
            True if spreadsheet ID is set, False otherwise
        """
        return self.spreadsheet_id is not None

    def authenticate(self) -> bool:
        """
        Authenticate with Google Sheets.

        Returns:
            True if authentication successful, False otherwise
        """
        try:
            return self.sheets_service.authenticate()
        except Exception as e:
            self.status = SyncStatus.ERROR
            self._emit_status(f"Authentication failed: {str(e)}")
            return False

    def create_new_sheet(self, title: str = "Inventory Mapper") -> Optional[str]:
        """
        Create a new Google Sheet.

        Args:
            title: Sheet title

        Returns:
            Spreadsheet ID if successful, None otherwise
        """
        try:
            spreadsheet_id = self.sheets_service.create_inventory_sheet(title)
            self.set_spreadsheet(spreadsheet_id)
            return spreadsheet_id
        except Exception as e:
            self.status = SyncStatus.ERROR
            self._emit_status(f"Failed to create sheet: {str(e)}")
            return None

    def sync(self, resolve_conflicts: bool = False) -> bool:
        """
        Perform two-way synchronization.

        Args:
            resolve_conflicts: If True, will attempt to resolve conflicts

        Returns:
            True if sync successful, False if conflicts or errors
        """
        if not self.is_configured():
            self._emit_status("Sync not configured")
            return False

        if not self.sheets_service.is_authenticated():
            if not self.authenticate():
                return False

        try:
            self.status = SyncStatus.SYNCING
            self.sync_started.emit()
            self._emit_status("Starting synchronization...")

            # Step 1: Load local inventory
            self.sync_progress.emit(10, "Loading local inventory...")
            local_items = InventoryItem.load_all()

            # Step 2: Load remote inventory
            self.sync_progress.emit(30, "Loading remote inventory...")
            remote_items = self.sheets_service.read_inventory_data(self.spreadsheet_id)

            # Step 3: Build sync state maps
            self.sync_progress.emit(40, "Analyzing changes...")
            sync_state = self._load_sync_state()

            # Step 4: Detect changes and conflicts
            self.sync_progress.emit(50, "Detecting changes...")
            changes = self._detect_changes(local_items, remote_items, sync_state)

            # Step 5: Handle conflicts
            if changes['conflicts']:
                self.status = SyncStatus.CONFLICT
                self.pending_conflicts = changes['conflicts']

                for conflict in self.pending_conflicts:
                    self.sync_conflict.emit(conflict)

                if not resolve_conflicts:
                    self._emit_status(f"Sync paused: {len(self.pending_conflicts)} conflicts")
                    return False

            # Step 6: Apply changes
            self.sync_progress.emit(70, "Applying changes...")
            self._apply_changes(changes)

            # Step 7: Update sync state
            self.sync_progress.emit(90, "Updating sync state...")
            self._save_sync_state(local_items, remote_items)

            # Complete
            self.status = SyncStatus.SUCCESS
            self.sync_progress.emit(100, "Sync complete")
            self.sync_completed.emit(True, "Synchronization successful")
            self._emit_status(f"Last sync: {datetime.now().strftime('%H:%M:%S')}")

            return True

        except Exception as e:
            self.status = SyncStatus.ERROR
            error_msg = f"Sync failed: {str(e)}"
            self.sync_completed.emit(False, error_msg)
            self._emit_status(error_msg)
            return False

    def _detect_changes(
        self,
        local_items: List[InventoryItem],
        remote_items: List[Dict[str, Any]],
        sync_state: Dict[int, Dict[str, str]]
    ) -> Dict[str, List]:
        """
        Detect changes between local and remote data.

        Returns:
            Dictionary with keys: push, pull, conflicts
        """
        changes = {
            'push': [],      # Items to push to remote
            'pull': [],      # Items to pull from remote
            'conflicts': []  # Conflicting items
        }

        # Build remote items map by ID
        remote_map = {int(item['ID']): item for item in remote_items if item.get('ID')}

        # Check local items
        for local_item in local_items:
            local_hash = self._calculate_item_hash(local_item)
            remote_item = remote_map.get(local_item.id)
            stored_state = sync_state.get(local_item.id, {})

            if not remote_item:
                # New local item - push to remote
                changes['push'].append(local_item)
            else:
                remote_hash = remote_item.get('Hash', '')
                stored_local_hash = stored_state.get('local_hash', '')
                stored_remote_hash = stored_state.get('remote_hash', '')

                local_changed = local_hash != stored_local_hash
                remote_changed = remote_hash != stored_remote_hash

                if local_changed and remote_changed:
                    # Both changed - conflict
                    conflict = SyncConflict(
                        item_id=local_item.id,
                        local_item=local_item,
                        remote_item=remote_item,
                        local_hash=local_hash,
                        remote_hash=remote_hash
                    )
                    changes['conflicts'].append(conflict)
                elif local_changed:
                    # Only local changed - push
                    changes['push'].append(local_item)
                elif remote_changed:
                    # Only remote changed - pull
                    changes['pull'].append(remote_item)

        # Check for new remote items
        local_ids = {item.id for item in local_items}
        for remote_item in remote_items:
            if remote_item.get('ID'):
                remote_id = int(remote_item['ID'])
                if remote_id not in local_ids:
                    changes['pull'].append(remote_item)

        return changes

    def _apply_changes(self, changes: Dict[str, List]):
        """
        Apply sync changes.

        Args:
            changes: Changes dictionary from _detect_changes
        """
        # Push local changes to remote
        for local_item in changes['push']:
            self._push_item(local_item)

        # Pull remote changes to local
        for remote_item in changes['pull']:
            self._pull_item(remote_item)

    def _push_item(self, item: InventoryItem):
        """Push local item to remote."""
        item_dict = {
            'ID': str(item.id),
            'SKU': item.sku or '',
            'Name': item.name,
            'Description': item.description or '',
            'Quantity': str(item.quantity),
            'Min Stock Level': str(item.min_stock_level),
            'Unit Price': str(item.unit_price or 0),
            'Category': '',  # TODO: Add category support
            'Tags': json.dumps(item.tags) if item.tags else '',
            'Custom Fields': json.dumps(item.custom_fields) if item.custom_fields else '',
            'Last Modified': datetime.now().isoformat(),
            'Hash': self._calculate_item_hash(item)
        }

        # TODO: Implement efficient row finding/updating
        # For now, we'll reload and update entire sheet
        self.sheets_service.append_inventory_row(self.spreadsheet_id, item_dict)

    def _pull_item(self, remote_item: Dict[str, Any]):
        """Pull remote item to local."""
        item_id = int(remote_item['ID']) if remote_item.get('ID') else None

        if item_id:
            # Update existing item
            item = InventoryItem.load(item_id)
            if item:
                item.sku = remote_item.get('SKU', '')
                item.name = remote_item.get('Name', '')
                item.description = remote_item.get('Description', '')
                item.quantity = int(remote_item.get('Quantity', 0) or 0)
                item.min_stock_level = int(remote_item.get('Min Stock Level', 0) or 0)
                item.unit_price = float(remote_item.get('Unit Price', 0) or 0)

                # Parse JSON fields
                if remote_item.get('Tags'):
                    try:
                        item.tags = json.loads(remote_item['Tags'])
                    except:
                        pass

                if remote_item.get('Custom Fields'):
                    try:
                        item.custom_fields = json.loads(remote_item['Custom Fields'])
                    except:
                        pass

                item.save()

    def _calculate_item_hash(self, item: InventoryItem) -> str:
        """
        Calculate hash for inventory item.

        Args:
            item: Inventory item

        Returns:
            SHA256 hash string
        """
        # Include relevant fields in hash
        hash_data = f"{item.sku}|{item.name}|{item.description}|{item.quantity}|" \
                   f"{item.min_stock_level}|{item.unit_price}|{json.dumps(item.tags)}|" \
                   f"{json.dumps(item.custom_fields)}"

        return hashlib.sha256(hash_data.encode()).hexdigest()

    def _load_sync_state(self) -> Dict[int, Dict[str, str]]:
        """
        Load sync state from database.

        Returns:
            Dictionary mapping item IDs to sync state
        """
        rows = self.db.execute(
            """
            SELECT entity_id, local_hash, remote_hash
            FROM sync_state
            WHERE entity_type = 'inventory_item'
            """
        ).fetchall()

        return {
            row[0]: {'local_hash': row[1], 'remote_hash': row[2]}
            for row in rows
        }

    def _save_sync_state(
        self,
        local_items: List[InventoryItem],
        remote_items: List[Dict[str, Any]]
    ):
        """
        Save sync state to database.

        Args:
            local_items: List of local inventory items
            remote_items: List of remote item dictionaries
        """
        # Build remote map
        remote_map = {int(item['ID']): item for item in remote_items if item.get('ID')}

        with self.db.transaction():
            for local_item in local_items:
                local_hash = self._calculate_item_hash(local_item)
                remote_item = remote_map.get(local_item.id)
                remote_hash = remote_item.get('Hash', '') if remote_item else ''

                # Upsert sync state
                self.db.execute(
                    """
                    INSERT OR REPLACE INTO sync_state
                    (entity_type, entity_id, local_hash, remote_hash, last_sync_time)
                    VALUES ('inventory_item', ?, ?, ?, ?)
                    """,
                    (local_item.id, local_hash, remote_hash, datetime.now().isoformat())
                )

    def _emit_status(self, message: str):
        """Emit status change signal."""
        self.status_changed.emit(message)

    def resolve_conflict(self, conflict: SyncConflict, use_local: bool):
        """
        Resolve a sync conflict.

        Args:
            conflict: Conflict to resolve
            use_local: If True, use local version; otherwise use remote
        """
        if use_local:
            # Push local to remote
            self._push_item(conflict.local_item)
        else:
            # Pull remote to local
            self._pull_item(conflict.remote_item)

        # Remove from pending conflicts
        if conflict in self.pending_conflicts:
            self.pending_conflicts.remove(conflict)

    def get_pending_conflicts(self) -> List[SyncConflict]:
        """
        Get list of pending conflicts.

        Returns:
            List of unresolved conflicts
        """
        return self.pending_conflicts.copy()
