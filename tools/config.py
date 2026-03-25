"""
config.py
=========
Central configuration file for the Business Lead Generator.
All constants, settings, and tunable parameters are here.
"""

import os

# ===========================================================
# SCRAPING CONFIGURATION
# ===========================================================

# Justdial base URL pattern
BASE_URL_JUSTDIAL = "https://www.justdial.com/{city}/{category}"

# Rotate these user-agents to avoid bot detection
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
]

# Delay between requests (seconds) - be respectful to servers
MIN_DELAY = 2
MAX_DELAY = 5

# Retry logic
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds to wait before retrying

# ===========================================================
# PLAYWRIGHT CONFIGURATION
# ===========================================================

HEADLESS = True              # Run browser in headless mode (no UI)
PAGE_TIMEOUT = 30000         # Page load timeout in milliseconds
SCROLL_PAUSE = 2             # Seconds to wait between each scroll
MAX_SCROLLS = 10             # How many times to scroll down (more = more results)

# ===========================================================
# OUTPUT CONFIGURATION
# ===========================================================

OUTPUT_DIR = "output"
BACKUP_CSV = os.path.join(OUTPUT_DIR, "business_leads_backup.csv")
BACKUP_XLSX = os.path.join(OUTPUT_DIR, "business_leads_backup.xlsx")

# Auto-open the output file after scraping
AUTO_OPEN = True

# Column headers for output files
HEADERS = [
    "Name",
    "Phone",
    "Address",
    "Rating",
    "Website",
    "City",
    "Category",
    "Source",
    "Date Scraped"
]

# ===========================================================
# GOOGLE SHEETS CONFIGURATION (optional)
# ===========================================================
# To enable Google Sheets upload, place your service account
# credentials.json in the project root. The system works
# fully without it — data is saved to CSV/Excel locally.

CREDENTIALS_FILE = "credentials.json"   # Your Google service account key file
SHEET_NAME = "Business Leads"           # Name of the Google Spreadsheet

# ===========================================================
# QUALITY FILTER SETTINGS
# ===========================================================

MIN_RATING = 4.0       # Minimum rating to consider a "high quality" lead
REQUIRE_PHONE = True   # High quality leads must have a phone number

# ===========================================================
# SCHEDULER CONFIGURATION
# ===========================================================

DAILY_RUN_TIME = "09:00"   # Time to run daily job (24-hour format HH:MM)
