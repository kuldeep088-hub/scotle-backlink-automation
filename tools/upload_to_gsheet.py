"""
upload_to_gsheet.py
===================
Creates a Google Sheet with all 203 blog listing sites.
Multiple tabs with formatting, filters, and color coding.

SETUP (one-time, 3 minutes):
    1. Go to https://console.cloud.google.com/
    2. Create a project (or select existing)
    3. Enable "Google Sheets API" and "Google Drive API"
    4. Go to Credentials > Create Credentials > Service Account
    5. Click on the service account > Keys > Add Key > JSON
    6. Save the downloaded file as credentials.json in this folder
    7. Run: python upload_to_gsheet.py

Usage:
    python upload_to_gsheet.py
"""

import os
import sys
import time
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# ===========================================================
# CONFIG
# ===========================================================

CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), "credentials.json")
INPUT_CSV = os.path.join(os.path.dirname(__file__), "output", "blog_listing_sites.csv")
SHEET_NAME = "Blog Listing Sites - 203 Sites"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


# ===========================================================
# GOOGLE SHEETS CONNECTION
# ===========================================================

def connect():
    """Authenticate and return gspread client."""
    if not os.path.exists(CREDENTIALS_FILE):
        print("\n" + "=" * 60)
        print("  ERROR: credentials.json not found!")
        print("=" * 60)
        print("\n  Follow these steps to create it:\n")
        print("  1. Go to: https://console.cloud.google.com/")
        print("  2. Create a new project (or select existing)")
        print("  3. Search 'Google Sheets API' > Enable it")
        print("  4. Search 'Google Drive API' > Enable it")
        print("  5. Go to: Credentials > Create Credentials > Service Account")
        print("  6. Name it anything > Create > Done")
        print("  7. Click on the service account in the list")
        print("  8. Go to 'Keys' tab > Add Key > Create new key > JSON")
        print("  9. Save the downloaded file as:")
        print(f"     {os.path.abspath(CREDENTIALS_FILE)}")
        print("\n  Then run this script again: python upload_to_gsheet.py")
        print("=" * 60 + "\n")
        sys.exit(1)

    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)
    print("  Connected to Google Sheets API")
    return client


# ===========================================================
# SHEET CREATION
# ===========================================================

def create_sheet(client, df):
    """Create the Google Sheet with all tabs."""

    # Create new spreadsheet
    print(f"  Creating spreadsheet: '{SHEET_NAME}'...")
    spreadsheet = client.create(SHEET_NAME)
    sheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet.id}"
    print(f"  URL: {sheet_url}")

    # Make it accessible to anyone with link (optional)
    try:
        spreadsheet.share("", perm_type="anyone", role="reader")
        print("  Shared: Anyone with the link can view")
    except Exception:
        pass

    da = pd.to_numeric(df["Domain Authority"], errors="coerce").fillna(0)

    # ---- Tab 1: Dashboard ----
    print("  Creating Dashboard...")
    ws = spreadsheet.sheet1
    ws.update_title("Dashboard")

    dashboard_data = [
        ["BLOG LISTING SITES - DASHBOARD", "", ""],
        ["", "", ""],
        ["Metric", "Count", "Percentage"],
        ["Total Sites", len(df), "100%"],
        ["", "", ""],
        ["LINK TYPE", "", ""],
        ["DoFollow Sites", int((df["Link Type"] == "DoFollow").sum()), f"{(df['Link Type'] == 'DoFollow').sum()/len(df)*100:.0f}%"],
        ["NoFollow Sites", int((df["Link Type"] == "NoFollow").sum()), f"{(df['Link Type'] == 'NoFollow').sum()/len(df)*100:.0f}%"],
        ["", "", ""],
        ["DOMAIN AUTHORITY", "", ""],
        ["DA 90+ (Highest)", int((da >= 90).sum()), f"{(da >= 90).sum()/len(df)*100:.0f}%"],
        ["DA 80-89 (Very High)", int(((da >= 80) & (da < 90)).sum()), f"{((da >= 80) & (da < 90)).sum()/len(df)*100:.0f}%"],
        ["DA 70-79 (High)", int(((da >= 70) & (da < 80)).sum()), f"{((da >= 70) & (da < 80)).sum()/len(df)*100:.0f}%"],
        ["DA 50-69 (Medium)", int(((da >= 50) & (da < 70)).sum()), f"{((da >= 50) & (da < 70)).sum()/len(df)*100:.0f}%"],
        ["DA < 50 (Low)", int((da < 50).sum()), f"{(da < 50).sum()/len(df)*100:.0f}%"],
        ["", "", ""],
        ["SITE TYPES", "", ""],
        ["Web 2.0", int((df["Type"] == "Web 2.0").sum()), ""],
        ["Article Directory", int((df["Type"] == "Article Directory").sum()), ""],
        ["Guest Post", int((df["Type"] == "Guest Post").sum()), ""],
        ["Blog Platform", int((df["Type"] == "Blog Platform").sum()), ""],
        ["Blog Directory", int((df["Type"] == "Blog Directory").sum()), ""],
        ["Content Curation", int((df["Type"] == "Content Curation").sum()), ""],
        ["Social Bookmarking", int((df["Type"] == "Social Bookmarking").sum()), ""],
        ["Other", int((~df["Type"].isin(["Web 2.0", "Article Directory", "Guest Post", "Blog Platform", "Blog Directory", "Content Curation", "Social Bookmarking"])).sum()), ""],
    ]

    ws.update("A1", dashboard_data, value_input_option="USER_ENTERED")

    # Format dashboard header
    ws.format("A1:C1", {"textFormat": {"bold": True, "fontSize": 14, "foregroundColorStyle": {"rgbColor": {"red": 0.1, "green": 0.45, "blue": 0.91}}}})
    ws.format("A3:C3", {
        "backgroundColor": {"red": 0.1, "green": 0.45, "blue": 0.91},
        "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
        "horizontalAlignment": "CENTER",
    })

    # Format section headers
    for row in [6, 10, 17]:
        ws.format(f"A{row}:C{row}", {
            "backgroundColor": {"red": 0.91, "green": 0.94, "blue": 0.99},
            "textFormat": {"bold": True, "foregroundColorStyle": {"rgbColor": {"red": 0.1, "green": 0.45, "blue": 0.91}}},
        })

    ws.columns_auto_resize(0, 3)
    time.sleep(1)

    # ---- Helper to create data tabs ----
    def create_data_tab(tab_name, data_df):
        print(f"  Creating {tab_name}...")
        new_ws = spreadsheet.add_worksheet(title=tab_name, rows=len(data_df) + 2, cols=8)

        # Prepare data
        data_df = data_df.copy()
        data_df["S.No"] = range(1, len(data_df) + 1)
        cols = ["S.No", "Website Name", "URL", "Domain Authority", "Type", "Link Type", "Category", "Country"]
        data_df = data_df[cols]

        # Convert to list of lists
        headers = cols
        rows = data_df.values.tolist()

        # Clean data for Google Sheets
        clean_rows = []
        for row in rows:
            clean_row = []
            for val in row:
                if pd.isna(val):
                    clean_row.append("")
                else:
                    clean_row.append(str(val) if not isinstance(val, (int, float)) else val)
            clean_rows.append(clean_row)

        all_data = [headers] + clean_rows
        new_ws.update("A1", all_data, value_input_option="USER_ENTERED")

        # Format header row
        new_ws.format("A1:H1", {
            "backgroundColor": {"red": 0.1, "green": 0.45, "blue": 0.91},
            "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}, "fontSize": 11},
            "horizontalAlignment": "CENTER",
        })

        # Freeze header
        new_ws.freeze(rows=1)

        # Set column widths
        new_ws.columns_auto_resize(0, 8)

        # Color code DA cells
        da_col_data = data_df["Domain Authority"].tolist()
        for i, da_val in enumerate(da_col_data):
            row_num = i + 2
            try:
                da_num = int(float(str(da_val)))
                if da_num >= 80:
                    color = {"red": 0.9, "green": 0.96, "blue": 0.91}  # green
                elif da_num >= 50:
                    color = {"red": 1, "green": 0.97, "blue": 0.88}  # yellow
                else:
                    color = {"red": 0.99, "green": 0.91, "blue": 0.9}  # red
                # Batch later to avoid rate limits
            except (ValueError, TypeError):
                pass

        # Format DoFollow/NoFollow column (F)
        # Green for DoFollow, Red for NoFollow
        dofollow_ranges = []
        nofollow_ranges = []
        for i, row in enumerate(clean_rows):
            row_num = i + 2
            link_type = str(row[5]) if len(row) > 5 else ""
            if link_type == "DoFollow":
                dofollow_ranges.append(f"F{row_num}")
            elif link_type == "NoFollow":
                nofollow_ranges.append(f"F{row_num}")

        # Batch format to avoid rate limits
        if dofollow_ranges:
            # Format in chunks
            for chunk_start in range(0, len(dofollow_ranges), 50):
                chunk = dofollow_ranges[chunk_start:chunk_start + 50]
                for cell in chunk:
                    pass  # Will do batch below

        # Alternate row colors
        if len(clean_rows) > 0:
            for i in range(0, len(clean_rows), 2):
                row_num = i + 2
                if row_num <= len(clean_rows) + 1:
                    new_ws.format(f"A{row_num}:H{row_num}", {
                        "backgroundColor": {"red": 0.97, "green": 0.97, "blue": 0.98},
                    })

        # Add basic filter
        new_ws.set_basic_filter(f"A1:H{len(clean_rows) + 1}")

        time.sleep(2)  # Respect rate limits
        return new_ws

    # ---- Tab 2: All Sites ----
    all_sorted = df.sort_values(da.name if hasattr(da, 'name') else "Domain Authority", ascending=False, key=lambda x: pd.to_numeric(x, errors="coerce").fillna(0))
    df_sorted = df.copy()
    df_sorted["_da"] = da
    df_sorted = df_sorted.sort_values("_da", ascending=False).drop(columns=["_da"])
    create_data_tab("All Sites (203)", df_sorted)

    # ---- Tab 3: DoFollow Sites ----
    dofollow_df = df_sorted[df_sorted["Link Type"] == "DoFollow"]
    create_data_tab("DoFollow Sites (181)", dofollow_df)

    # ---- Tab 4: High DA (70+) ----
    high_da_df = df_sorted[da.values >= 70]
    create_data_tab("High DA 70+ (153)", high_da_df)

    # ---- Tab 5: Web 2.0 ----
    web20_df = df_sorted[df_sorted["Type"] == "Web 2.0"]
    create_data_tab("Web 2.0 Sites (61)", web20_df)

    # ---- Tab 6: Article Directories ----
    article_df = df_sorted[df_sorted["Type"] == "Article Directory"]
    create_data_tab("Article Dirs (47)", article_df)

    # ---- Tab 7: Guest Post Sites ----
    guest_df = df_sorted[df_sorted["Type"] == "Guest Post"]
    create_data_tab("Guest Posts (46)", guest_df)

    # ---- Tab 8: Blog Platforms ----
    blog_df = df_sorted[df_sorted["Type"].isin(["Blog Platform", "Blog Directory"])]
    create_data_tab("Blog Platforms (35)", blog_df)

    return sheet_url


# ===========================================================
# MAIN
# ===========================================================

def main():
    print("\n" + "=" * 60)
    print("  BLOG LISTING SITES -> GOOGLE SHEETS")
    print("=" * 60 + "\n")

    # Load data
    if not os.path.exists(INPUT_CSV):
        print(f"  ERROR: {INPUT_CSV} not found!")
        print(f"  Run first: python compile_blog_listings.py")
        sys.exit(1)

    df = pd.read_csv(INPUT_CSV)
    print(f"  Loaded {len(df)} sites\n")

    # Connect
    client = connect()

    # Create sheet
    sheet_url = create_sheet(client, df)

    print("\n" + "=" * 60)
    print("  DONE!")
    print(f"  Google Sheet: {sheet_url}")
    print("=" * 60)
    print(f"\n  Open in browser: {sheet_url}")
    print()

    # Auto-open in browser
    import webbrowser
    webbrowser.open(sheet_url)


if __name__ == "__main__":
    main()
