"""
gsheet_reporter.py
==================
Exports the backlink posting results + high-DA sites database to Google Sheets.

Setup (one-time):
    1. Go to: https://console.cloud.google.com
    2. Create a project → Enable "Google Sheets API" + "Google Drive API"
    3. IAM & Admin → Service Accounts → Create → Download JSON key
    4. Save the JSON file as: blog_poster/google_credentials.json
    5. Create a new Google Sheet at sheets.google.com
    6. Copy the Sheet ID from the URL (the long ID between /d/ and /edit)
    7. Share the Sheet with the service account email (from the JSON file)
    8. Run: python unified_poster.py --mode gsheet --sheet-id YOUR_SHEET_ID

Usage:
    from blog_poster.gsheet_reporter import GSheetReporter
    reporter = GSheetReporter(credentials_path="blog_poster/google_credentials.json")
    reporter.push_all(sheet_id="YOUR_SHEET_ID", posts_csv="blog_poster/output/posts_log.csv")
"""

import os
import csv
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# Optional gspread import — works without it (falls back to CSV export)
try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSPREAD_AVAILABLE = True
except ImportError:
    GSPREAD_AVAILABLE = False


# ---------------------------------------------------------------------------
# Sheet structure
# ---------------------------------------------------------------------------

SHEET_TABS = {
    "Summary":       "Overall backlink campaign stats",
    "All Posts":     "Every post logged by the system",
    "High-DA Sites": "Full database of 55+ high-DA sites",
    "By Platform":   "Post counts grouped by platform",
    "Failed Posts":  "Posts that failed — fix action required",
}

POSTS_HEADERS = [
    "Post ID", "Platform", "Title", "Published URL", "Target URL",
    "Anchor Text", "Tags", "Word Count", "Status", "Error",
    "Date Published", "Verified", "Ping Result",
]

SITES_HEADERS = [
    "Rank", "Site Name", "URL", "DA Score", "Submission URL",
    "Auth Type", "Platform Key", "Education Friendly", "Notes", "Tags",
]


# ---------------------------------------------------------------------------
# GSheetReporter
# ---------------------------------------------------------------------------

class GSheetReporter:
    """
    Pushes backlink data to Google Sheets.
    Falls back to CSV if gspread is not installed or credentials are missing.
    """

    def __init__(self, credentials_path: str = None):
        self.credentials_path = credentials_path or os.path.join(
            os.path.dirname(__file__), "google_credentials.json"
        )
        self.client = None
        self._connected = False

    def connect(self) -> bool:
        """Authenticate with Google Sheets API."""
        if not GSPREAD_AVAILABLE:
            logger.warning("gspread not installed. Run: pip install gspread google-auth")
            return False

        if not os.path.exists(self.credentials_path):
            logger.warning(f"Credentials not found: {self.credentials_path}")
            logger.warning("See setup instructions in gsheet_reporter.py docstring.")
            return False

        try:
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
            ]
            creds = Credentials.from_service_account_file(self.credentials_path, scopes=scopes)
            self.client = gspread.authorize(creds)
            self._connected = True
            logger.info("Google Sheets API connected.")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Google Sheets: {e}")
            return False

    def push_all(self, sheet_id: str, posts_csv: str) -> bool:
        """
        Push everything to Google Sheets:
        - Summary stats
        - All posts
        - High-DA sites database
        - By-platform breakdown
        - Failed posts

        Returns True if pushed to Google Sheets, False if fell back to CSV.
        """
        posts = self._read_posts_csv(posts_csv)
        from blog_poster.high_da_sites import get_all_sites, get_stats as site_stats
        sites = get_all_sites()

        if not self.connect():
            # Fall back to CSV export
            logger.info("Falling back to local CSV export (no Google Sheets connection)")
            return self._export_csv_bundle(posts, sites, posts_csv)

        try:
            spreadsheet = self.client.open_by_key(sheet_id)
            logger.info(f"Opened sheet: {spreadsheet.title}")

            self._write_summary(spreadsheet, posts, sites)
            self._write_all_posts(spreadsheet, posts)
            self._write_high_da_sites(spreadsheet, sites)
            self._write_by_platform(spreadsheet, posts)
            self._write_failed_posts(spreadsheet, posts)

            logger.info(f"All data pushed to Google Sheets: https://docs.google.com/spreadsheets/d/{sheet_id}")
            return True

        except Exception as e:
            logger.error(f"Error pushing to Google Sheets: {e}")
            return self._export_csv_bundle(posts, sites, posts_csv)

    # -----------------------------------------------------------------------
    # Sheet writers
    # -----------------------------------------------------------------------

    def _write_summary(self, spreadsheet, posts: List[dict], sites):
        """Write the Summary tab."""
        ws = self._get_or_create_worksheet(spreadsheet, "Summary")
        ws.clear()

        total = len(posts)
        published = len([p for p in posts if p.get("Status", "").lower() == "published"])
        failed = len([p for p in posts if p.get("Status", "").lower() == "failed"])
        platforms = list(set(p.get("Platform", "") for p in posts if p.get("Platform")))
        verified = len([p for p in posts if str(p.get("Verified", "")).lower() == "true"])

        from blog_poster.high_da_sites import get_stats
        site_stat = get_stats()

        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        rows = [
            ["SCOTLE HIGH SCHOOL — BACKLINK CAMPAIGN REPORT"],
            [f"Generated: {now}"],
            [""],
            ["POSTING RESULTS", ""],
            ["Total Posts Logged", total],
            ["Successfully Published", published],
            ["Failed Posts", failed],
            ["Success Rate", f"{round(published/total*100, 1)}%" if total else "0%"],
            ["Platforms Used", len(platforms)],
            ["Verified Live", verified],
            [""],
            ["HIGH-DA SITES DATABASE", ""],
            ["Total Sites in Database", site_stat["total_sites"]],
            ["Average DA", site_stat["avg_da"]],
            ["Sites with DA 90+", site_stat["da_90_plus"]],
            ["Sites with DA 80+", site_stat["da_80_plus"]],
            ["Education-Friendly Sites", site_stat["education_friendly"]],
            ["Free (No Signup) Sites", site_stat["free_no_signup"]],
            ["Integrated in System", site_stat["integrated"]],
            [""],
            ["PLATFORMS ACTIVE", ""],
        ]
        for p in sorted(platforms):
            count = len([x for x in posts if x.get("Platform", "") == p])
            rows.append([p, f"{count} posts"])

        ws.update("A1", rows)

        # Format header
        try:
            ws.format("A1", {"textFormat": {"bold": True, "fontSize": 14}})
            ws.format("A4", {"textFormat": {"bold": True}})
            ws.format("A12", {"textFormat": {"bold": True}})
            ws.format("A21", {"textFormat": {"bold": True}})
        except Exception:
            pass

        logger.info("Summary tab written.")

    def _write_all_posts(self, spreadsheet, posts: List[dict]):
        """Write All Posts tab."""
        ws = self._get_or_create_worksheet(spreadsheet, "All Posts")
        ws.clear()

        if not posts:
            ws.update("A1", [["No posts logged yet."]])
            return

        rows = [POSTS_HEADERS]
        for p in posts:
            rows.append([
                p.get("Post ID", ""),
                p.get("Platform", ""),
                p.get("Title", ""),
                p.get("Published URL", ""),
                p.get("Target URL", ""),
                p.get("Anchor Text", ""),
                p.get("Tags", ""),
                p.get("Word Count", ""),
                p.get("Status", ""),
                p.get("Error", ""),
                p.get("Date Published", ""),
                p.get("verified", ""),
                p.get("ping_result", ""),
            ])

        ws.update("A1", rows)
        try:
            ws.format("A1:M1", {"textFormat": {"bold": True}, "backgroundColor": {"red": 0.2, "green": 0.4, "blue": 0.8}})
        except Exception:
            pass
        logger.info(f"All Posts tab written ({len(posts)} rows).")

    def _write_high_da_sites(self, spreadsheet, sites):
        """Write High-DA Sites tab."""
        ws = self._get_or_create_worksheet(spreadsheet, "High-DA Sites")
        ws.clear()

        rows = [SITES_HEADERS]
        for i, s in enumerate(sites, 1):
            rows.append([
                i,
                s.name,
                s.url,
                s.da,
                s.submission_url,
                s.auth_type,
                s.platform_key or "—",
                "Yes" if s.education_friendly else "No",
                s.notes,
                ", ".join(s.tags),
            ])

        ws.update("A1", rows)
        try:
            ws.format("A1:J1", {"textFormat": {"bold": True}, "backgroundColor": {"red": 0.1, "green": 0.6, "blue": 0.3}})
        except Exception:
            pass
        logger.info(f"High-DA Sites tab written ({len(sites)} rows).")

    def _write_by_platform(self, spreadsheet, posts: List[dict]):
        """Write By Platform tab."""
        ws = self._get_or_create_worksheet(spreadsheet, "By Platform")
        ws.clear()

        from collections import Counter
        platform_counts = Counter(p.get("Platform", "") for p in posts)
        platform_success = Counter(
            p.get("Platform", "") for p in posts
            if p.get("Status", "").lower() == "published"
        )

        rows = [["Platform", "Total Posts", "Published", "Failed", "Success Rate"]]
        for platform, total in sorted(platform_counts.items(), key=lambda x: -x[1]):
            published = platform_success.get(platform, 0)
            failed = total - published
            rate = f"{round(published/total*100, 1)}%" if total else "0%"
            rows.append([platform, total, published, failed, rate])

        ws.update("A1", rows)
        try:
            ws.format("A1:E1", {"textFormat": {"bold": True}})
        except Exception:
            pass
        logger.info("By Platform tab written.")

    def _write_failed_posts(self, spreadsheet, posts: List[dict]):
        """Write Failed Posts tab."""
        ws = self._get_or_create_worksheet(spreadsheet, "Failed Posts")
        ws.clear()

        failed = [p for p in posts if p.get("Status", "").lower() == "failed"]
        if not failed:
            ws.update("A1", [["No failed posts."]])
            return

        rows = [["Platform", "Title", "Error", "Date Published"]]
        for p in failed:
            rows.append([
                p.get("Platform", ""),
                p.get("Title", ""),
                p.get("Error", ""),
                p.get("Date Published", ""),
            ])

        ws.update("A1", rows)
        try:
            ws.format("A1:D1", {"textFormat": {"bold": True}, "backgroundColor": {"red": 0.9, "green": 0.2, "blue": 0.2}})
        except Exception:
            pass
        logger.info(f"Failed Posts tab written ({len(failed)} rows).")

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    def _get_or_create_worksheet(self, spreadsheet, title: str):
        """Get worksheet by title, create if missing."""
        try:
            return spreadsheet.worksheet(title)
        except gspread.exceptions.WorksheetNotFound:
            return spreadsheet.add_worksheet(title=title, rows=2000, cols=20)

    def _read_posts_csv(self, csv_path: str) -> List[dict]:
        """Read posts from the tracking CSV."""
        if not os.path.exists(csv_path):
            logger.warning(f"Posts CSV not found: {csv_path}")
            return []
        try:
            rows = []
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    rows.append(dict(row))
            return rows
        except Exception as e:
            logger.error(f"Error reading CSV: {e}")
            return []

    def _export_csv_bundle(self, posts: List[dict], sites, posts_csv: str) -> bool:
        """
        Fallback: export everything as CSV files when Google Sheets isn't available.
        Creates a bundle in blog_poster/output/gsheet_export/
        """
        base_dir = os.path.join(os.path.dirname(posts_csv), "gsheet_export")
        os.makedirs(base_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M")

        # 1. High-DA Sites CSV
        from blog_poster.high_da_sites import export_sites_csv
        sites_path = os.path.join(base_dir, f"high_da_sites_{timestamp}.csv")
        export_sites_csv(sites_path, sites)
        logger.info(f"Exported: {sites_path}")

        # 2. All Posts CSV (copy with timestamp)
        if posts:
            all_posts_path = os.path.join(base_dir, f"all_posts_{timestamp}.csv")
            with open(all_posts_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=POSTS_HEADERS)
                writer.writeheader()
                for p in posts:
                    writer.writerow({
                        "Post ID": p.get("Post ID", ""),
                        "Platform": p.get("Platform", ""),
                        "Title": p.get("Title", ""),
                        "Published URL": p.get("Published URL", ""),
                        "Target URL": p.get("Target URL", ""),
                        "Anchor Text": p.get("Anchor Text", ""),
                        "Tags": p.get("Tags", ""),
                        "Word Count": p.get("Word Count", ""),
                        "Status": p.get("Status", ""),
                        "Error": p.get("Error", ""),
                        "Date Published": p.get("Date Published", ""),
                        "Verified": p.get("verified", ""),
                        "Ping Result": p.get("ping_result", ""),
                    })
            logger.info(f"Exported: {all_posts_path}")

        # 3. Summary CSV
        summary_path = os.path.join(base_dir, f"summary_{timestamp}.csv")
        total = len(posts)
        published = len([p for p in posts if p.get("Status", "").lower() == "published"])
        failed = total - published
        from blog_poster.high_da_sites import get_stats
        site_stat = get_stats()

        with open(summary_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Metric", "Value"])
            writer.writerow(["Report Generated", datetime.now().strftime("%Y-%m-%d %H:%M")])
            writer.writerow(["Total Posts", total])
            writer.writerow(["Published", published])
            writer.writerow(["Failed", failed])
            writer.writerow(["Success Rate", f"{round(published/total*100, 1)}%" if total else "0%"])
            writer.writerow(["Platforms Used", len(set(p.get("Platform", "") for p in posts))])
            writer.writerow(["", ""])
            writer.writerow(["High-DA Sites Total", site_stat["total_sites"]])
            writer.writerow(["Avg DA", site_stat["avg_da"]])
            writer.writerow(["DA 90+ Sites", site_stat["da_90_plus"]])
            writer.writerow(["Education-Friendly", site_stat["education_friendly"]])
        logger.info(f"Exported: {summary_path}")

        print(f"\n=== CSV EXPORT COMPLETE ===")
        print(f"Location: {base_dir}")
        print(f"Files exported:")
        print(f"  - high_da_sites_{timestamp}.csv  ({len(sites)} sites)")
        print(f"  - all_posts_{timestamp}.csv      ({len(posts)} posts)")
        print(f"  - summary_{timestamp}.csv")
        print(f"\nTo import into Google Sheets:")
        print("  1. Open sheets.google.com -> New spreadsheet")
        print("  2. File -> Import -> Upload -> select each CSV")
        print("  3. Choose 'Insert new sheet(s)' for each file")

        return False  # Indicates fallback was used


# ---------------------------------------------------------------------------
# Convenience function
# ---------------------------------------------------------------------------

def push_to_gsheet(sheet_id: str, posts_csv: str = None, credentials_path: str = None) -> bool:
    """
    One-line function to push everything to Google Sheets.
    Returns True if pushed directly, False if fell back to CSV export.
    """
    if posts_csv is None:
        posts_csv = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "blog_poster", "output", "posts_log.csv"
        )

    reporter = GSheetReporter(credentials_path=credentials_path)
    return reporter.push_all(sheet_id=sheet_id, posts_csv=posts_csv)
