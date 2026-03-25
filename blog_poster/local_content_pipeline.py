"""
local_content_pipeline.py
=========================
Reads scraped JustDial business leads, extracts unique (city, category) pairs,
generates hyper-local articles, and posts them to all enabled platforms.

Usage:
    python -m blog_poster.local_content_pipeline
    python -m blog_poster.local_content_pipeline --csv output/business_leads_backup.csv
    python -m blog_poster.local_content_pipeline --dry-run
"""

import os
import sys
import logging
import argparse
import random
import pandas as pd
from datetime import datetime

# Allow running as script or module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from blog_poster import blog_config as config
from blog_poster.blog_platforms import PosterFactory
from blog_poster.blog_tracker import log_post, update_post_verification
from blog_poster.blog_utils import (
    generate_article_from_template,
    generate_local_content_ollama,
    check_word_count,
    inject_backlinks,
    build_author_bio,
    add_authority_links,
)
from blog_poster.templates.article_templates import get_templates
from blog_poster.blog_poster import ping_google
from blog_poster.verifier import verify_post, log_failed_verification

logger = logging.getLogger(__name__)

DEFAULT_CSV = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "output", "business_leads_backup.csv",
)


def load_city_category_pairs(csv_path: str) -> list:
    """
    Read the leads CSV and return a sorted list of unique (city, category) tuples.
    Skips rows with null City or Category.
    """
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        logger.error(f"Leads CSV not found: {csv_path}")
        return []
    except Exception as e:
        logger.error(f"Failed to read leads CSV: {e}")
        return []

    if "City" not in df.columns or "Category" not in df.columns:
        logger.error("CSV must have 'City' and 'Category' columns")
        return []

    df = df.dropna(subset=["City", "Category"])
    pairs = sorted(set(zip(df["City"].str.strip(), df["Category"].str.strip())))
    logger.info(f"Found {len(pairs)} unique city/category pairs")
    return pairs


def generate_local_article(city: str, category: str) -> dict:
    """
    Generate a hyper-local article for the given city and category.
    Tries Ollama first (if configured), falls back to template.
    Always returns a valid article dict.
    """
    title = f"Top 10 {category} in {city} — Best Local Services {datetime.now().year}"

    # Try Ollama if configured
    if config.CONTENT_METHOD == "ollama":
        logger.info(f"Generating with Ollama: {city} / {category}")
        result = generate_local_content_ollama(
            city, category, config.OLLAMA_URL, config.OLLAMA_MODEL
        )
        if result and check_word_count(result["content_html"], config.MIN_WORD_COUNT):
            return result
        if result:
            logger.warning(
                f"Ollama output below {config.MIN_WORD_COUNT} words "
                f"({result['word_count']}), falling back to template"
            )
        else:
            logger.warning("Ollama unavailable, falling back to template")

    # Template fallback
    logger.info(f"Generating from template: {city} / {category}")
    templates = get_templates("local_services")
    template = random.choice(templates)
    article = generate_article_from_template(
        template=template,
        keyword=category,
        city=city,
        brand=config.TARGET_BRAND,
        spin=config.SPIN_CONTENT,
    )
    article["title"] = title
    return article


def post_local_article(city: str, category: str, dry_run: bool = False) -> list:
    """
    Generate and post a local article to all enabled platforms.
    Returns a list of result dicts.
    """
    logger.info(f"\n{'='*55}")
    logger.info(f"  LOCAL CONTENT: {category} in {city}")
    logger.info(f"{'='*55}")

    article = generate_local_article(city, category)
    title = article["title"]
    content = article["content_html"]
    tags = [
        category.lower(),
        city.lower(),
        "scotle.org",
        "local business",
        str(datetime.now().year),
    ]

    # Inject backlinks and extras
    anchor_text = random.choice(config.ANCHOR_TEXTS)
    content = inject_backlinks(
        content, config.TARGET_URL, config.ANCHOR_TEXTS,
        max_links=config.MAX_BACKLINKS_PER_POST,
        nofollow_pct=config.NOFOLLOW_PERCENTAGE,
    )
    content = add_authority_links(content, config.AUTHORITY_LINKS)
    if config.ADD_AUTHOR_BIO:
        bio = build_author_bio(config.TARGET_URL, config.TARGET_BRAND, anchor_text)
        content += "\n\n" + bio

    platforms = PosterFactory.get_enabled_platforms(config)
    if not platforms:
        logger.error("No platforms enabled")
        return []

    results = []

    for platform_name in platforms:
        if dry_run:
            logger.info(f"  [DRY RUN] Would post to {platform_name}: {title}")
            results.append({"platform": platform_name, "dry_run": True, "title": title})
            continue

        logger.info(f"Posting to {platform_name}...")
        try:
            poster = PosterFactory.get_poster(platform_name, config)
            result = poster.post(title, content, tags=tags)
        except Exception as e:
            logger.error(f"Posting to {platform_name} failed: {e}")
            result = {
                "success": False, "url": "", "platform": platform_name,
                "post_id": "", "error": str(e),
            }

        track_data = {
            "post_id": result.get("post_id", ""),
            "platform": platform_name,
            "title": title,
            "url": result.get("url", ""),
            "target_url": config.TARGET_URL,
            "anchor_text": anchor_text,
            "tags": tags,
            "word_count": article.get("word_count", 0),
            "status": "published" if result.get("success") else "failed",
            "error": result.get("error", ""),
        }
        log_post(track_data, config.POSTS_LOG_CSV)

        if result.get("success"):
            post_url = result.get("url", "")
            logger.info(f"  SUCCESS: {post_url}")

            logger.info("  Pinging Google...")
            ping_result = ping_google(post_url)
            logger.info(f"  Google ping: {ping_result}")

            logger.info("  Verifying post...")
            verified = verify_post(post_url)
            logger.info(f"  Verification: {'PASS' if verified else 'FAIL'}")

            if not verified:
                log_failed_verification(track_data, config.FAILED_POSTS_CSV)

            update_post_verification(config.POSTS_LOG_CSV, post_url, verified, ping_result)
        else:
            logger.error(f"  FAILED: {result.get('error', 'Unknown error')}")

        results.append(result)

    return results


def run_pipeline(csv_path: str = DEFAULT_CSV, dry_run: bool = False) -> None:
    """
    Main pipeline: load city/category pairs and post for each.
    """
    pairs = load_city_category_pairs(csv_path)
    if not pairs:
        logger.error("No city/category pairs found. Check your leads CSV.")
        return

    total = len(pairs)
    success_count = 0

    for i, (city, category) in enumerate(pairs, 1):
        logger.info(f"\nProcessing pair {i}/{total}: {category} in {city}")
        results = post_local_article(city, category, dry_run=dry_run)
        success_count += sum(1 for r in results if r.get("success") or r.get("dry_run"))

    logger.info(f"\n{'='*55}")
    logger.info(f"Pipeline complete: {total} pairs processed")
    if not dry_run:
        logger.info(f"Posts log: {config.POSTS_LOG_CSV}")
    logger.info(f"{'='*55}\n")


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    parser = argparse.ArgumentParser(
        description="Local Content Pipeline — post hyper-local articles from JustDial data"
    )
    parser.add_argument(
        "--csv", default=DEFAULT_CSV,
        help=f"Path to leads CSV (default: {DEFAULT_CSV})",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview what would be posted without actually posting",
    )
    args = parser.parse_args()

    run_pipeline(csv_path=args.csv, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
