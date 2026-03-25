"""
main.py
=======
Entry point for the Business Lead Generator.

This script orchestrates the full pipeline:
    1. Accept user input (City + Category)
    2. Scrape business listings from JustDial
    3. Clean and deduplicate the data
    4. Filter high-quality leads (optional)
    5. Save to CSV (and optionally Excel)
    6. Auto-open the output file
    7. Upload to Google Sheets (only if credentials are available)

Usage:
    python main.py                                  # Interactive mode
    python main.py --city Jaipur --category Gyms   # Direct mode
    python main.py --city Jaipur --category Gyms --quality-filter
    python main.py --city Jaipur --category Gyms --excel
    python main.py --city Jaipur --category Gyms --schedule
"""

import os
import sys
import time
import logging
import argparse
import schedule
from datetime import datetime

# Import our modules
import config
from scraper import ScraperFactory
from utils import (
    clean_text,
    normalize_phone,
    parse_rating,
    remove_duplicates,
    filter_high_quality_leads,
    add_metadata,
    save_backup_csv,
    save_excel,
    open_file,
)


# ===========================================================
# LOGGING SETUP
# ===========================================================

def setup_logging():
    """Configure logging to print to console AND write to a log file."""
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.StreamHandler(sys.stdout),                            # Console output
            logging.FileHandler('output/scraper.log', encoding='utf-8'), # File output
        ]
    )


logger = logging.getLogger(__name__)


# ===========================================================
# USER INPUT
# ===========================================================

def get_user_input() -> tuple:
    """
    Prompt the user interactively for City, Category, and filter preference.

    Returns:
        Tuple of (city: str, category: str, apply_quality_filter: bool)
    """
    print("\n" + "=" * 55)
    print("       Business Lead Generator")
    print("=" * 55)
    print("  Scrapes JustDial -> Cleans Data -> Saves to Sheets")
    print("=" * 55 + "\n")

    # Get city
    city = input("Enter City (e.g., Jaipur, Mumbai, Delhi): ").strip()
    if not city:
        print("[ERROR] City cannot be empty!")
        sys.exit(1)

    # Get category
    category = input("Enter Business Category (e.g., Restaurants, Salons, Gyms): ").strip()
    if not category:
        print("[ERROR] Category cannot be empty!")
        sys.exit(1)

    # Quality filter preference
    print(f"\nQuality Filter: Keep only leads with rating > {config.MIN_RATING} AND phone number")
    qf = input("Apply quality filter? [y/N]: ").strip().lower()
    apply_quality_filter = qf in ('y', 'yes')

    # Excel export preference
    xls = input("Also export to Excel (.xlsx)? [y/N]: ").strip().lower()
    export_excel = xls in ('y', 'yes')

    return city, category, apply_quality_filter, export_excel


# ===========================================================
# DATA CLEANING PIPELINE
# ===========================================================

def clean_records(raw_records: list) -> list:
    """
    Apply cleaning and normalization to all raw scraped records.

    Steps:
        - clean_text: Remove whitespace and junk characters
        - normalize_phone: Standardize to +91XXXXXXXXXX format
        - parse_rating: Convert string to float
        - Filter out records with no name (useless)

    Args:
        raw_records: Raw data from scraper
    Returns:
        List of cleaned record dicts
    """
    cleaned = []
    for record in raw_records:
        cleaned_record = {
            'Name':    clean_text(record.get('Name', '')),
            'Phone':   normalize_phone(record.get('Phone', '')),
            'Address': clean_text(record.get('Address', '')),
            'Rating':  str(parse_rating(record.get('Rating', ''))) or '',
            'Website': record.get('Website', '').strip(),
        }

        # Only keep records that at least have a name
        if cleaned_record['Name']:
            cleaned.append(cleaned_record)

    logger.info(f"Cleaning: {len(raw_records)} raw -> {len(cleaned)} with valid names")
    return cleaned


# ===========================================================
# MAIN PIPELINE
# ===========================================================

def run_scraper(city: str, category: str, apply_quality_filter: bool = False, export_excel: bool = False):
    """
    Full pipeline: scrape -> clean -> filter -> save -> open -> upload (if available).

    Args:
        city: Target city
        category: Business category
        apply_quality_filter: Whether to apply the quality filter
        export_excel: Whether to also export as .xlsx
    """
    # --- Header Banner ---
    logger.info("")
    logger.info("=" * 55)
    logger.info(f"  SCRAPING: {category} in {city}")
    logger.info(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 55)

    # ================================================================
    # STEP 1: SCRAPE
    # ================================================================
    logger.info("Scraping started...")

    try:
        scraper = ScraperFactory.get_scraper('justdial', config)
        raw_records = scraper.scrape(city, category)
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        return

    logger.info(f"{len(raw_records)} raw records found")

    if not raw_records:
        logger.warning("No records found. Possible reasons:")
        logger.warning("  - JustDial blocked the request (try again later)")
        logger.warning("  - No listings for this city/category combination")
        logger.warning("  - Playwright not installed (run: pip install playwright && playwright install chromium)")
        return

    # ================================================================
    # STEP 2: CLEAN & DEDUPLICATE
    # ================================================================
    logger.info("Cleaning and normalizing records...")
    cleaned = clean_records(raw_records)
    cleaned = remove_duplicates(cleaned)

    # Add city, category, source, and date to every record
    cleaned = add_metadata(cleaned, city, category, source='Justdial')

    logger.info(f"{len(cleaned)} records after cleaning and deduplication")

    if not cleaned:
        logger.warning("No valid records after cleaning. Exiting.")
        return

    # ================================================================
    # STEP 3: QUALITY FILTER (optional)
    # ================================================================
    if apply_quality_filter:
        logger.info(f"Applying quality filter (rating >= {config.MIN_RATING}, phone required)...")
        cleaned = filter_high_quality_leads(
            cleaned,
            min_rating=config.MIN_RATING,
            require_phone=config.REQUIRE_PHONE,
        )
        logger.info(f"{len(cleaned)} high-quality leads remain")

        if not cleaned:
            logger.warning("No records passed the quality filter.")
            logger.info("Tip: Try without quality filter, or lower MIN_RATING in config.py")
            return

    # ================================================================
    # STEP 4: SAVE CSV (primary output)
    # ================================================================
    try:
        save_backup_csv(cleaned, config.BACKUP_CSV)
    except Exception as e:
        logger.error(f"Failed to save CSV: {e}")

    # ================================================================
    # STEP 5: SAVE EXCEL (optional)
    # ================================================================
    if export_excel:
        try:
            save_excel(cleaned, config.BACKUP_XLSX)
        except Exception as e:
            logger.error(f"Failed to save Excel: {e}")

    # ================================================================
    # STEP 6: UPLOAD TO GOOGLE SHEETS (only if credentials exist)
    # ================================================================
    upload_to_sheets(cleaned)

    # ================================================================
    # STEP 7: AUTO-OPEN OUTPUT FILE
    # ================================================================
    if config.AUTO_OPEN:
        output_path = config.BACKUP_XLSX if export_excel else config.BACKUP_CSV
        open_file(output_path)

    # --- Summary ---
    logger.info("")
    logger.info("=" * 55)
    logger.info(f"  DONE! {len(cleaned)} total records processed")
    logger.info(f"  CSV: {config.BACKUP_CSV}")
    if export_excel:
        logger.info(f"  Excel: {config.BACKUP_XLSX}")
    logger.info("=" * 55)
    logger.info("")


# ===========================================================
# GOOGLE SHEETS (optional — only runs if credentials exist)
# ===========================================================

def upload_to_sheets(records: list):
    """
    Upload records to Google Sheets if credentials.json is present.
    Silently skips if credentials are not configured.
    This allows easy plug-in of Google Sheets later by simply
    dropping a credentials.json file into the project root.
    """
    if not os.path.exists(config.CREDENTIALS_FILE):
        logger.info("Google Sheets: skipped (no credentials.json found)")
        logger.info("Tip: Add credentials.json to enable automatic Sheets upload")
        return

    try:
        from sheets import GoogleSheetsManager

        sheets = GoogleSheetsManager(
            credentials_file=config.CREDENTIALS_FILE,
            sheet_name=config.SHEET_NAME,
            headers=config.HEADERS,
        )
        sheets.connect()
        sheets.open_or_create_sheet()
        added = sheets.append_records(records)

        logger.info(f"Google Sheets: {added} new records uploaded")
        logger.info(f"View your data: {sheets.get_sheet_url()}")

    except Exception as e:
        logger.error(f"Google Sheets upload failed: {e}")
        logger.info("Your data is safe in the local CSV/Excel files")


# ===========================================================
# SCHEDULER
# ===========================================================

def schedule_daily(city: str, category: str, apply_filter: bool, export_excel: bool = False):
    """
    Set up a daily schedule to run the scraper automatically.

    Runs once immediately, then every day at DAILY_RUN_TIME.
    Press Ctrl+C to stop.

    Args:
        city: Target city
        category: Business category
        apply_filter: Whether to apply quality filter
        export_excel: Whether to also export as .xlsx
    """
    run_time = config.DAILY_RUN_TIME

    logger.info(f"Scheduler enabled. Will run daily at {run_time}")
    logger.info("Running immediately for the first time...")
    logger.info("Press Ctrl+C to stop the scheduler\n")

    # Run once immediately
    run_scraper(city, category, apply_filter, export_excel)

    # Schedule daily runs
    schedule.every().day.at(run_time).do(
        run_scraper, city, category, apply_filter, export_excel
    )

    # Keep the script alive
    try:
        while True:
            schedule.run_pending()
            time.sleep(30)  # Check every 30 seconds

    except KeyboardInterrupt:
        logger.info("\nScheduler stopped by user.")
        sys.exit(0)


# ===========================================================
# CLI ARGUMENT PARSER
# ===========================================================

def parse_args():
    """Parse command-line arguments for non-interactive mode."""
    parser = argparse.ArgumentParser(
        description='Business Lead Generator - Scrape JustDial and save to Google Sheets',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py
  python main.py --city Jaipur --category Restaurants
  python main.py --city Mumbai --category Salons --quality-filter
  python main.py --city Delhi  --category Gyms   --excel
  python main.py --city Delhi  --category Gyms   --schedule --no-open
        """
    )
    parser.add_argument('--city',           help='City to search (e.g., Jaipur)')
    parser.add_argument('--category',       help='Business category (e.g., Restaurants)')
    parser.add_argument('--quality-filter', action='store_true',
                        help=f'Only keep leads with rating > {config.MIN_RATING} and phone number')
    parser.add_argument('--excel',          action='store_true',
                        help='Also export to Excel (.xlsx) format')
    parser.add_argument('--no-open',        action='store_true',
                        help='Do not auto-open the output file')
    parser.add_argument('--schedule',       action='store_true',
                        help=f'Run daily at {config.DAILY_RUN_TIME} (set in config.py)')

    return parser.parse_args()


# ===========================================================
# ENTRY POINT
# ===========================================================

def main():
    setup_logging()
    args = parse_args()

    # Override auto-open if --no-open flag is set
    if args.no_open:
        config.AUTO_OPEN = False

    # Determine inputs: from CLI args or interactive prompts
    if args.city and args.category:
        city = args.city.strip()
        category = args.category.strip()
        apply_filter = args.quality_filter
        export_excel = args.excel
        use_schedule = args.schedule
    else:
        # Interactive mode - ask the user
        city, category, apply_filter, export_excel = get_user_input()

        # Ask about scheduling
        print()
        sched = input(f"Run on daily schedule at {config.DAILY_RUN_TIME}? [y/N]: ").strip().lower()
        use_schedule = sched in ('y', 'yes')

    # Run once or on a schedule
    if use_schedule:
        schedule_daily(city, category, apply_filter, export_excel)
    else:
        run_scraper(city, category, apply_filter, export_excel)


if __name__ == "__main__":
    main()
