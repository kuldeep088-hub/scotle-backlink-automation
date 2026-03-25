"""
unified_poster.py
=================
Single CLI entry point for all posting modes.
Replaces: post_30_blogs.py, post_30_sites.py, mega_post.py, bulk_post.py, post_batch3.py

Usage:
    python unified_poster.py --mode quick
    python unified_poster.py --mode mega
    python unified_poster.py --mode mega --count 56
    python unified_poster.py --mode bulk
    python unified_poster.py --mode batch
    python unified_poster.py --mode local
    python unified_poster.py --mode local --csv output/business_leads_backup.csv
    python unified_poster.py --mode quick --dry-run
    python unified_poster.py --mode quick --content-method ollama
    python unified_poster.py --mode discover
    python unified_poster.py --mode discover --min-da 80
    python unified_poster.py --mode discover --auth free
    python unified_poster.py --mode discover --export-csv
    python unified_poster.py --mode gsheet --sheet-id YOUR_GOOGLE_SHEET_ID
    python unified_poster.py --mode gsheet  (no sheet-id = export CSV instead)
"""

import os
import sys
import argparse
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from blog_poster import blog_config as config
from blog_poster.blog_platforms import PosterFactory
from blog_poster.blog_poster import setup_logging, post_to_platform, post_to_all_platforms

logger = logging.getLogger(__name__)

DEFAULT_LOCAL_CSV = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "output", "business_leads_backup.csv",
)

MODE_DEFAULTS = {
    "quick":    1,     # 1 post per enabled platform
    "mega":     30,    # 30 posts round-robin
    "bulk":     24,    # 24 posts to Write.as only
    "batch":    None,
    "local":    None,
    "discover": None,  # show high-DA sites database
    "gsheet":   None,  # push results to Google Sheets
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Unified Blog Poster — single command for all posting modes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modes:
  quick     Post 1 article per enabled platform (credential smoke test)
  mega      Post 30 articles round-robin across all platforms
  bulk      Post 24 articles to Write.as only
  batch     Post to paste sites (from post_batch3.py logic)
  local     Post hyper-local articles from JustDial leads CSV
  discover  Browse 55+ high-DA blog posting sites database
  gsheet    Push all results to Google Sheets (or export CSV bundle)

Examples:
  python unified_poster.py --mode quick
  python unified_poster.py --mode mega --count 56
  python unified_poster.py --mode local --csv output/business_leads_backup.csv
  python unified_poster.py --mode quick --dry-run
  python unified_poster.py --mode mega --content-method ollama
  python unified_poster.py --mode discover
  python unified_poster.py --mode discover --min-da 80
  python unified_poster.py --mode discover --auth free --export-csv
  python unified_poster.py --mode gsheet --sheet-id 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms
  python unified_poster.py --mode gsheet   (no sheet-id = exports CSV files)
        """,
    )
    parser.add_argument(
        "--mode", required=True,
        choices=["quick", "mega", "bulk", "batch", "local", "discover", "gsheet"],
        help="Posting mode",
    )
    parser.add_argument(
        "--count", type=int, default=None,
        help="Number of posts (overrides mode default)",
    )
    parser.add_argument(
        "--platform", default=None,
        help="Restrict to a single platform (for quick/mega modes)",
    )
    parser.add_argument(
        "--csv", default=DEFAULT_LOCAL_CSV,
        help=f"Path to leads CSV for local mode (default: {DEFAULT_LOCAL_CSV})",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview without posting (supported in quick, mega, local modes)",
    )
    parser.add_argument(
        "--niche", default=None,
        help="Article niche: business, local_services, technology, how_to, health, education",
    )
    parser.add_argument(
        "--content-method", default=None, choices=["template", "ollama"],
        help="Override CONTENT_METHOD from config (template or ollama)",
    )
    # discover mode options
    parser.add_argument(
        "--min-da", type=int, default=0,
        help="Minimum DA to show in discover mode (e.g. --min-da 80)",
    )
    parser.add_argument(
        "--auth", default=None,
        choices=["free", "api_key", "oauth", "browser", "premium"],
        help="Filter by auth type in discover mode",
    )
    parser.add_argument(
        "--export-csv", action="store_true",
        help="Export results to CSV (discover: sites CSV; gsheet fallback CSV)",
    )
    # gsheet mode options
    parser.add_argument(
        "--sheet-id", default=None,
        help="Google Sheets ID for gsheet mode (from the sheet URL)",
    )
    parser.add_argument(
        "--credentials", default=None,
        help="Path to Google service account JSON (default: blog_poster/google_credentials.json)",
    )
    return parser.parse_args()


def run_quick(args):
    """Post 1 article per enabled platform."""
    if args.content_method:
        config.CONTENT_METHOD = args.content_method

    platforms = (
        [args.platform] if args.platform
        else PosterFactory.get_enabled_platforms(config)
    )
    if not platforms:
        logger.error("No platforms enabled. Edit blog_config.py to enable platforms.")
        return

    logger.info(f"QUICK MODE — posting to: {', '.join(platforms)}")

    for platform_name in platforms:
        if args.dry_run:
            logger.info(f"  [DRY RUN] Would post to: {platform_name}")
            continue
        post_to_platform(platform_name, niche=args.niche)


def run_mega(args):
    """Post N articles round-robin across all platforms."""
    if args.content_method:
        config.CONTENT_METHOD = args.content_method

    count = args.count or MODE_DEFAULTS["mega"]
    platforms = PosterFactory.get_enabled_platforms(config)

    logger.info(f"MEGA MODE — {count} posts across {len(platforms)} platforms")

    if args.dry_run:
        logger.info(f"  [DRY RUN] Would post {count} articles to: {', '.join(platforms)}")
        return

    # Temporarily lift daily limit for mega mode
    from blog_poster.blog_tracker import get_today_post_count
    original_limit = config.POSTS_PER_DAY
    config.POSTS_PER_DAY = get_today_post_count(config.POSTS_LOG_CSV) + count
    try:
        post_to_all_platforms(count=count, niche=args.niche)
    finally:
        config.POSTS_PER_DAY = original_limit


def run_bulk(args):
    """Post 24 articles to Write.as only."""
    count = args.count or MODE_DEFAULTS["bulk"]
    logger.info(f"BULK MODE — {count} posts to Write.as")

    if args.dry_run:
        logger.info(f"  [DRY RUN] Would post {count} articles to Write.as")
        return

    original_limit = config.POSTS_PER_DAY
    config.POSTS_PER_DAY = count
    try:
        for i in range(count):
            logger.info(f"\nPost {i+1}/{count}")
            post_to_platform("writeas", niche=args.niche)
    finally:
        config.POSTS_PER_DAY = original_limit


def run_batch(args):
    """Run the batch3 paste-site poster."""
    logger.info("BATCH MODE — posting to paste sites via post_batch3")
    if args.dry_run:
        logger.info("  [DRY RUN] batch mode does not support --dry-run; skipping")
        return

    import importlib.util
    batch3_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "post_batch3.py")
    spec = importlib.util.spec_from_file_location("post_batch3", batch3_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.main()


def run_local(args):
    """Run the local content pipeline."""
    from blog_poster.local_content_pipeline import run_pipeline

    if args.content_method:
        config.CONTENT_METHOD = args.content_method

    logger.info(f"LOCAL MODE — reading leads from: {args.csv}")
    run_pipeline(csv_path=args.csv, dry_run=args.dry_run)


def run_discover(args):
    """
    Show the high-DA sites database with optional filtering.
    Optionally export to CSV with --export-csv.
    """
    from blog_poster.high_da_sites import (
        get_all_sites, get_sites_by_da, get_sites_by_auth,
        get_education_sites, print_table, export_sites_csv, get_stats,
    )

    # Apply filters
    if args.auth:
        sites = get_sites_by_auth(args.auth)
        if args.min_da:
            sites = [s for s in sites if s.da >= args.min_da]
        label = f"auth={args.auth}"
    elif args.min_da:
        sites = get_sites_by_da(min_da=args.min_da)
        label = f"DA >= {args.min_da}"
    else:
        sites = get_all_sites()
        label = "all"

    stats = get_stats()
    print(f"\n=== HIGH-DA BLOG POSTING SITES ({label}) ===")
    print(f"Database stats: {stats['total_sites']} total sites | avg DA {stats['avg_da']} | "
          f"{stats['da_90_plus']} sites DA 90+ | {stats['education_friendly']} education-friendly")
    print()
    print_table(sites)

    if args.export_csv:
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        os.makedirs(output_dir, exist_ok=True)
        from datetime import datetime
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        csv_path = os.path.join(output_dir, f"high_da_sites_{ts}.csv")
        export_sites_csv(csv_path, sites)
        print(f"\nExported to CSV: {csv_path}")
        print("Import this CSV into Google Sheets: File → Import → Upload")


def run_gsheet(args):
    """
    Push all posting results + high-DA sites database to Google Sheets.
    If --sheet-id not provided, exports CSV bundle instead.
    """
    from blog_poster.gsheet_reporter import GSheetReporter

    posts_csv = config.POSTS_LOG_CSV

    reporter = GSheetReporter(credentials_path=args.credentials)

    if args.sheet_id:
        logger.info(f"GSHEET MODE — pushing to sheet: {args.sheet_id}")
        success = reporter.push_all(sheet_id=args.sheet_id, posts_csv=posts_csv)
        if success:
            print(f"\nData pushed to Google Sheets!")
            print(f"View: https://docs.google.com/spreadsheets/d/{args.sheet_id}")
        else:
            print("\nFell back to CSV export (see output above for file locations).")
    else:
        logger.info("GSHEET MODE — no --sheet-id provided, exporting CSV bundle")
        posts = reporter._read_posts_csv(posts_csv)
        from blog_poster.high_da_sites import get_all_sites
        sites = get_all_sites()
        reporter._export_csv_bundle(posts, sites, posts_csv)


def main():
    setup_logging()
    args = parse_args()

    dispatch = {
        "quick":    run_quick,
        "mega":     run_mega,
        "bulk":     run_bulk,
        "batch":    run_batch,
        "local":    run_local,
        "discover": run_discover,
        "gsheet":   run_gsheet,
    }

    dispatch[args.mode](args)


if __name__ == "__main__":
    main()
