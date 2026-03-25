"""
sheets.py
=========
Google Sheets integration using gspread + service account credentials.

What it does:
- Connects to Google Sheets API using credentials.json
- Opens "Business Leads" spreadsheet (creates it if it doesn't exist)
- Ensures headers are present in row 1
- Appends new records without duplicating existing ones
- Returns the sheet URL for easy access

Setup required (see README for full guide):
1. Create a Google Cloud project
2. Enable Google Sheets API + Google Drive API
3. Create a Service Account and download credentials.json
4. Share your spreadsheet with the service account email
"""

import logging
import gspread
from google.oauth2.service_account import Credentials

logger = logging.getLogger(__name__)

# OAuth2 scopes needed for reading and writing Sheets + Drive
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive',
]


class GoogleSheetsManager:
    """
    Manages all interactions with a Google Spreadsheet.

    Usage:
        manager = GoogleSheetsManager("credentials.json", "Business Leads", HEADERS)
        manager.connect()
        manager.open_or_create_sheet()
        manager.append_records(records)
        print(manager.get_sheet_url())
    """

    def __init__(self, credentials_file: str, sheet_name: str, headers: list):
        """
        Args:
            credentials_file: Path to your Google service account JSON key file
            sheet_name: Name of the Google Spreadsheet to use/create
            headers: List of column header names
        """
        self.credentials_file = credentials_file
        self.sheet_name = sheet_name
        self.headers = headers
        self.client = None        # gspread client after authentication
        self.spreadsheet = None  # gspread Spreadsheet object
        self.worksheet = None    # gspread Worksheet (first sheet/tab)

    # ----------------------------------------------------------
    # CONNECTION
    # ----------------------------------------------------------

    def connect(self):
        """
        Authenticate with Google Sheets API using the service account key file.

        Raises:
            FileNotFoundError: If credentials.json doesn't exist
            ConnectionError: If authentication fails
        """
        try:
            creds = Credentials.from_service_account_file(
                self.credentials_file,
                scopes=SCOPES
            )
            self.client = gspread.authorize(creds)
            logger.info("Google Sheets API: Connected successfully")

        except FileNotFoundError:
            raise FileNotFoundError(
                f"\n[ERROR] '{self.credentials_file}' not found!\n"
                "Please follow the Google Sheets setup instructions in README.md\n"
                "to create and download your service account credentials.\n"
            )
        except Exception as e:
            raise ConnectionError(
                f"Failed to connect to Google Sheets API: {e}\n"
                "Check that your credentials.json is valid."
            )

    # ----------------------------------------------------------
    # SPREADSHEET SETUP
    # ----------------------------------------------------------

    def open_or_create_sheet(self):
        """
        Open the spreadsheet by name, or create it if it doesn't exist.
        Also ensures the first row contains the correct column headers.
        """
        if not self.client:
            raise RuntimeError("Call connect() before open_or_create_sheet()")

        # Try to open existing spreadsheet
        try:
            self.spreadsheet = self.client.open(self.sheet_name)
            logger.info(f"Opened existing spreadsheet: '{self.sheet_name}'")
        except gspread.SpreadsheetNotFound:
            # Create new spreadsheet
            self.spreadsheet = self.client.create(self.sheet_name)
            logger.info(f"Created new spreadsheet: '{self.sheet_name}'")

        # Use the first worksheet (Sheet1)
        self.worksheet = self.spreadsheet.sheet1

        # Add headers if the sheet is empty or has wrong headers
        self._ensure_headers()

        logger.info(f"Sheet ready: {self.get_sheet_url()}")

    def _ensure_headers(self):
        """
        Check if headers exist in row 1. Add them if missing.
        This is idempotent - safe to call multiple times.
        """
        try:
            existing_values = self.worksheet.get_all_values()

            if not existing_values:
                # Sheet is completely empty - add headers
                self.worksheet.append_row(self.headers, value_input_option='USER_ENTERED')
                logger.info(f"Headers added: {self.headers}")

            elif existing_values[0] != self.headers:
                # Row 1 has different content - update headers
                end_col = chr(ord('A') + len(self.headers) - 1)
                self.worksheet.update(f'A1:{end_col}1', [self.headers])
                logger.info("Headers updated in row 1")

            else:
                logger.debug("Headers already present - no changes needed")

        except Exception as e:
            logger.error(f"Error checking/setting headers: {e}")

    # ----------------------------------------------------------
    # DATA OPERATIONS
    # ----------------------------------------------------------

    def get_existing_names(self) -> set:
        """
        Fetch all business names already in the sheet.
        Used to prevent uploading duplicate records.

        Returns:
            Set of lowercase business names
        """
        try:
            records = self.worksheet.get_all_records()
            names = {
                str(r.get('Name', '')).lower().strip()
                for r in records
                if r.get('Name')
            }
            logger.debug(f"Found {len(names)} existing names in sheet")
            return names
        except Exception as e:
            logger.warning(f"Could not fetch existing records: {e}. Proceeding without dedup check.")
            return set()

    def append_records(self, records: list) -> int:
        """
        Append new business records to the Google Sheet.
        Skips records whose Name already exists in the sheet.

        Args:
            records: List of business record dicts
        Returns:
            Number of records actually added
        """
        if not records:
            logger.warning("No records provided to upload")
            return 0

        # Get names already in the sheet to avoid duplicates
        existing_names = self.get_existing_names()
        logger.info(f"Sheet has {len(existing_names)} existing records")

        # Build list of rows to add (skip duplicates)
        rows_to_add = []
        skipped = 0

        for record in records:
            name = str(record.get('Name', '')).lower().strip()

            if name in existing_names:
                skipped += 1
                continue

            # Build row in the same order as SHEET_HEADERS
            row = [str(record.get(header, '')) for header in self.headers]
            rows_to_add.append(row)
            existing_names.add(name)  # Mark as seen so we don't add twice from this batch

        if skipped > 0:
            logger.info(f"Skipped {skipped} duplicates already in sheet")

        if not rows_to_add:
            logger.info("No new records to add - all were duplicates")
            return 0

        # Batch append all rows at once (much faster than one-by-one)
        try:
            self.worksheet.append_rows(rows_to_add, value_input_option='USER_ENTERED')
            logger.info(f"Successfully added {len(rows_to_add)} new records to Google Sheets")
            return len(rows_to_add)

        except gspread.exceptions.APIError as e:
            logger.error(f"Google Sheets API error while appending: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while appending records: {e}")
            raise

    # ----------------------------------------------------------
    # UTILITIES
    # ----------------------------------------------------------

    def get_sheet_url(self) -> str:
        """Return the direct URL to open this spreadsheet in a browser."""
        if self.spreadsheet:
            return f"https://docs.google.com/spreadsheets/d/{self.spreadsheet.id}"
        return "URL unavailable (sheet not opened yet)"

    def get_record_count(self) -> int:
        """Return total number of data rows (excluding header)."""
        try:
            all_values = self.worksheet.get_all_values()
            return max(0, len(all_values) - 1)  # subtract header row
        except Exception:
            return 0
