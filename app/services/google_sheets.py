"""
Google Sheets API service.

Handles OAuth 2.0 authentication and communication with Google Sheets API.
"""

import json
import os
from typing import Optional, List, Dict, Any
from pathlib import Path

import gspread
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from gspread.exceptions import SpreadsheetNotFound, APIError

from app.config import get_config


# Google Sheets API scopes
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# Default sheet headers for inventory
INVENTORY_HEADERS = [
    'ID',
    'SKU',
    'Name',
    'Description',
    'Quantity',
    'Min Stock Level',
    'Unit Price',
    'Category',
    'Tags',
    'Custom Fields',
    'Last Modified',
    'Hash'
]


class GoogleSheetsService:
    """
    Service for interacting with Google Sheets API.

    Handles authentication, spreadsheet access, and data synchronization.
    """

    def __init__(self):
        """Initialize Google Sheets service."""
        self.config = get_config()
        self.client: Optional[gspread.Client] = None
        self.credentials: Optional[Credentials] = None

        # Credentials file paths
        self.token_file = self._get_token_path()
        self.credentials_file = self._get_credentials_path()

    def _get_token_path(self) -> Path:
        """Get path to token file."""
        data_dir = Path.home() / '.config' / 'InventoryMapper'
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir / 'token.json'

    def _get_credentials_path(self) -> Path:
        """Get path to credentials file."""
        # Check for credentials in multiple locations
        locations = [
            Path.home() / '.config' / 'InventoryMapper' / 'credentials.json',
            Path('credentials.json'),
            Path('client_secret.json')
        ]

        for path in locations:
            if path.exists():
                return path

        # Return default location
        return locations[0]

    def is_authenticated(self) -> bool:
        """
        Check if user is authenticated.

        Returns:
            True if authenticated, False otherwise
        """
        return self.client is not None

    def authenticate(self) -> bool:
        """
        Authenticate with Google Sheets API.

        Returns:
            True if authentication successful, False otherwise

        Raises:
            FileNotFoundError: If credentials file not found
            Exception: If authentication fails
        """
        # Load existing token if available
        if self.token_file.exists():
            try:
                self.credentials = Credentials.from_authorized_user_file(
                    str(self.token_file), SCOPES
                )
            except Exception as e:
                print(f"Error loading token: {e}")
                self.credentials = None

        # Refresh or obtain new credentials
        if not self.credentials or not self.credentials.valid:
            if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                # Refresh expired token
                try:
                    self.credentials.refresh(Request())
                except Exception as e:
                    print(f"Error refreshing token: {e}")
                    self.credentials = None

            if not self.credentials:
                # Obtain new credentials
                if not self.credentials_file.exists():
                    raise FileNotFoundError(
                        f"Credentials file not found at {self.credentials_file}\n"
                        "Please download credentials from Google Cloud Console:\n"
                        "1. Go to https://console.cloud.google.com/\n"
                        "2. Create or select a project\n"
                        "3. Enable Google Sheets API\n"
                        "4. Create OAuth 2.0 credentials (Desktop app)\n"
                        "5. Download and save as credentials.json"
                    )

                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_file), SCOPES
                )
                self.credentials = flow.run_local_server(port=0)

            # Save credentials for next time
            self.token_file.write_text(self.credentials.to_json())

        # Create gspread client
        self.client = gspread.authorize(self.credentials)
        return True

    def create_inventory_sheet(self, title: str = "Inventory Mapper") -> str:
        """
        Create a new Google Sheet for inventory.

        Args:
            title: Title for the new spreadsheet

        Returns:
            Spreadsheet ID

        Raises:
            Exception: If not authenticated or creation fails
        """
        if not self.client:
            raise Exception("Not authenticated. Call authenticate() first.")

        # Create new spreadsheet
        spreadsheet = self.client.create(title)

        # Get first worksheet
        worksheet = spreadsheet.sheet1
        worksheet.update_title("Inventory")

        # Add headers
        worksheet.update('A1:L1', [INVENTORY_HEADERS])

        # Format header row
        worksheet.format('A1:L1', {
            'textFormat': {'bold': True},
            'backgroundColor': {'red': 0.8, 'green': 0.8, 'blue': 0.8}
        })

        # Freeze header row
        worksheet.freeze(rows=1)

        return spreadsheet.id

    def get_spreadsheet(self, spreadsheet_id: str) -> gspread.Spreadsheet:
        """
        Get spreadsheet by ID.

        Args:
            spreadsheet_id: Google Sheets spreadsheet ID

        Returns:
            Spreadsheet object

        Raises:
            Exception: If not authenticated
            SpreadsheetNotFound: If spreadsheet doesn't exist
        """
        if not self.client:
            raise Exception("Not authenticated. Call authenticate() first.")

        return self.client.open_by_key(spreadsheet_id)

    def get_inventory_worksheet(self, spreadsheet_id: str) -> gspread.Worksheet:
        """
        Get inventory worksheet from spreadsheet.

        Args:
            spreadsheet_id: Google Sheets spreadsheet ID

        Returns:
            Worksheet object

        Raises:
            Exception: If spreadsheet or worksheet not found
        """
        spreadsheet = self.get_spreadsheet(spreadsheet_id)

        # Try to find "Inventory" worksheet
        try:
            return spreadsheet.worksheet("Inventory")
        except gspread.WorksheetNotFound:
            # Use first worksheet if "Inventory" not found
            return spreadsheet.sheet1

    def read_inventory_data(self, spreadsheet_id: str) -> List[Dict[str, Any]]:
        """
        Read all inventory data from Google Sheet.

        Args:
            spreadsheet_id: Google Sheets spreadsheet ID

        Returns:
            List of inventory item dictionaries
        """
        worksheet = self.get_inventory_worksheet(spreadsheet_id)

        # Get all values
        rows = worksheet.get_all_values()

        if not rows:
            return []

        # First row is headers
        headers = rows[0]

        # Convert rows to dictionaries
        items = []
        for row in rows[1:]:  # Skip header row
            if not any(row):  # Skip empty rows
                continue

            item = {}
            for i, header in enumerate(headers):
                value = row[i] if i < len(row) else ''
                item[header] = value

            items.append(item)

        return items

    def write_inventory_data(self, spreadsheet_id: str, items: List[Dict[str, Any]]) -> None:
        """
        Write inventory data to Google Sheet.

        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            items: List of inventory item dictionaries
        """
        worksheet = self.get_inventory_worksheet(spreadsheet_id)

        # Prepare rows
        rows = [INVENTORY_HEADERS]

        for item in items:
            row = [
                str(item.get(header, ''))
                for header in INVENTORY_HEADERS
            ]
            rows.append(row)

        # Clear existing data and write new data
        worksheet.clear()
        worksheet.update('A1', rows)

        # Format header row
        worksheet.format('A1:L1', {
            'textFormat': {'bold': True},
            'backgroundColor': {'red': 0.8, 'green': 0.8, 'blue': 0.8}
        })

        # Freeze header row
        worksheet.freeze(rows=1)

    def update_inventory_row(self, spreadsheet_id: str, row_index: int, item: Dict[str, Any]) -> None:
        """
        Update a single inventory row.

        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            row_index: Row index (1-based, excluding header)
            item: Inventory item dictionary
        """
        worksheet = self.get_inventory_worksheet(spreadsheet_id)

        # Prepare row data
        row = [
            str(item.get(header, ''))
            for header in INVENTORY_HEADERS
        ]

        # Update row (add 2 because: 1 for header, 1 for 1-based indexing)
        worksheet.update(f'A{row_index + 2}', [row])

    def append_inventory_row(self, spreadsheet_id: str, item: Dict[str, Any]) -> None:
        """
        Append a new inventory row.

        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            item: Inventory item dictionary
        """
        worksheet = self.get_inventory_worksheet(spreadsheet_id)

        # Prepare row data
        row = [
            str(item.get(header, ''))
            for header in INVENTORY_HEADERS
        ]

        # Append row
        worksheet.append_row(row)

    def delete_inventory_row(self, spreadsheet_id: str, row_index: int) -> None:
        """
        Delete an inventory row.

        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            row_index: Row index (1-based, excluding header)
        """
        worksheet = self.get_inventory_worksheet(spreadsheet_id)

        # Delete row (add 2 because: 1 for header, 1 for 1-based indexing)
        worksheet.delete_rows(row_index + 2)

    def disconnect(self) -> None:
        """Disconnect from Google Sheets API."""
        self.client = None
        self.credentials = None
