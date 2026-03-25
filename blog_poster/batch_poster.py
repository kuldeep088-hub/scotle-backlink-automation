"""
batch_poster.py
===============
Posts a large batch of blog articles across all enabled platforms for scotle.org.

Usage:
    python -m blog_poster.batch_poster               # Post 50 blogs (default)
    python -m blog_poster.batch_poster --count 30    # Post 30 blogs
    python -m blog_poster.batch_poster --delay 15    # 15-second delay between posts
    python -m blog_poster.batch_poster --dry-run     # Preview articles without posting

Rotation:
    - Posts cycle through enabled platforms: never 2 posts to same site in a row
    - DA-sorted: highest DA platforms used first in each cycle
    - Skips platforms that failed 3+ times in a row (auto-recovery)

Progress:
    - Live console progress with DA and URL
    - Final CSV saved to output/batch_results_{timestamp}.csv
"""

import os
import sys
import csv
import time
import random
import logging
import argparse
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from blog_poster import blog_config as config
from blog_poster.blog_platforms import PosterFactory
from blog_poster.blog_tracker import log_post, get_used_topics, is_duplicate_post
from blog_poster.verifier import verify_post, log_failed_verification
from blog_poster.blog_utils import (
    generate_article_from_template, get_next_topic,
    inject_backlinks, build_author_bio, add_authority_links,
    generate_topics,
)
from blog_poster.templates.article_templates import get_templates

# ------------------------------------------------------------
# DA map — used to sort platforms highest first
# ------------------------------------------------------------
PLATFORM_DA = {
    "blogger":     99,
    "linkedin":    99,
    "wordpress":   94,
    "github":      96,
    "gitlab":      95,
    "medium":      95,
    "pastebin":    92,
    "livejournal": 93,
    "tumblr":      93,
    "hackmd":      90,
    "devto":       90,
    "hashnode":    82,
    "substack":    89,
    "writeas":     69,
    "bytebin":     60,
    "rentry":      60,
    "dpaste":      55,
    "pastegg":     50,
    "justpasteit": 40,
    "telegraph":   74,
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    datefmt="%H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def get_sorted_platforms() -> list:
    """Return enabled platforms sorted by DA score (highest first)."""
    platforms = PosterFactory.get_enabled_platforms(config)
    return sorted(platforms, key=lambda p: PLATFORM_DA.get(p, 0), reverse=True)


def generate_batch_topics(count: int) -> list:
    """Generate 'count' unique topics across all keywords."""
    used = get_used_topics(config.POSTS_LOG_CSV)
    topics = generate_topics(config.TARGET_KEYWORDS, count=count * 2, used_topics=used)
    return topics[:count]


def build_post_content(topic: str) -> tuple:
    """
    Generate article + inject backlinks + add bio.
    Returns (title, content_html, anchor_text, word_count).
    """
    # 70% school, 20% education, 10% how_to
    niche = random.choices(
        ["school"] * 7 + ["education"] * 2 + ["how_to"],
        k=1
    )[0]
    templates = get_templates(niche)
    template = random.choice(templates)
    keyword = random.choice(config.TARGET_KEYWORDS)

    article = generate_article_from_template(
        template=template,
        keyword=keyword,
        brand=config.TARGET_BRAND,
        spin=True,
    )
    title = topic
    content = article["content_html"]

    # Inject backlink
    anchor = random.choice(config.ANCHOR_TEXTS)
    content = inject_backlinks(
        content, config.TARGET_URL, config.ANCHOR_TEXTS,
        max_links=config.MAX_BACKLINKS_PER_POST,
        nofollow_pct=config.NOFOLLOW_PERCENTAGE,
    )

    # Add authority links
    content = add_authority_links(content, config.AUTHORITY_LINKS)

    # Add author bio
    if config.ADD_AUTHOR_BIO:
        bio = build_author_bio(config.TARGET_URL, config.TARGET_BRAND, anchor)
        content += "\n\n" + bio

    return title, content, anchor, article.get("word_count", 0)


def post_batch(count: int = 50, delay: int = 20, dry_run: bool = False):
    """
    Main batch posting loop.

    Args:
        count:   Total number of posts to publish.
        delay:   Seconds to wait between posts.
        dry_run: If True, generate content but do not post.
    """
    platforms = get_sorted_platforms()

    if not platforms:
        logger.error("No platforms enabled! Add credentials in blog_config.py")
        return []

    logger.info("")
    logger.info("=" * 60)
    logger.info("  BATCH POSTER — Scotle High School Backlinks")
    logger.info(f"  Target posts : {count}")
    logger.info(f"  Platforms    : {len(platforms)} ({', '.join(p.upper() for p in platforms)})")
    logger.info(f"  Delay        : {delay}s between posts")
    if dry_run:
        logger.info("  MODE         : DRY RUN (no actual posting)")
    logger.info("=" * 60)
    logger.info("")

    # Pre-generate all topics so we never repeat
    topics = generate_batch_topics(count)
    if len(topics) < count:
        # Pad with timestamped titles if we run out of unique ones
        base = len(topics)
        for i in range(count - base):
            kw = random.choice(config.TARGET_KEYWORDS).title()
            topics.append(f"{kw} — Guide {base + i + 1} ({datetime.now().year})")

    results = []
    fail_counts = {p: 0 for p in platforms}
    MAX_CONSECUTIVE_FAILS = 3

    # Platform rotation index
    platform_idx = 0

    for i in range(count):
        topic = topics[i]

        # Pick next platform — skip ones with too many consecutive failures
        attempts = 0
        chosen = None
        while attempts < len(platforms):
            candidate = platforms[platform_idx % len(platforms)]
            platform_idx += 1
            if fail_counts.get(candidate, 0) < MAX_CONSECUTIVE_FAILS:
                chosen = candidate
                break
            attempts += 1

        if not chosen:
            logger.warning("All platforms failing consecutively. Stopping early.")
            break

        da = PLATFORM_DA.get(chosen, "?")
        logger.info(f"[{i+1:02d}/{count}] {chosen.upper()} (DA {da}) — {topic[:55]}")

        # Generate content
        title, content, anchor, wc = build_post_content(topic)

        if dry_run:
            logger.info(f"         DRY RUN — {wc} words generated, not posted")
            results.append({
                "no": i + 1, "platform": chosen, "da": da,
                "title": title, "url": "DRY_RUN", "verified": "—",
                "words": wc, "error": "",
            })
            time.sleep(1)
            continue

        # Post
        try:
            poster = PosterFactory.get_poster(chosen, config)
            result = poster.post(title, content, tags=config.TARGET_KEYWORDS[:5])
        except Exception as e:
            result = {"success": False, "url": "", "error": str(e)}

        if result.get("success"):
            fail_counts[chosen] = 0  # Reset on success
            post_url = result.get("url", "")

            # Verify
            verified = verify_post(post_url)
            v_str = "PASS" if verified else "FAIL"

            logger.info(f"         OK — {post_url}")
            logger.info(f"         Verify: {v_str} | Words: {wc}")

            # Track
            track = {
                "post_id": result.get("post_id", ""),
                "platform": chosen,
                "title": title,
                "url": post_url,
                "target_url": config.TARGET_URL,
                "anchor_text": anchor,
                "tags": config.TARGET_KEYWORDS[:5],
                "word_count": wc,
                "status": "published",
                "error": "",
            }
            log_post(track, config.POSTS_LOG_CSV)

            if not verified:
                log_failed_verification(track, config.FAILED_POSTS_CSV)

            results.append({
                "no": i + 1, "platform": chosen, "da": da,
                "title": title, "url": post_url, "verified": v_str,
                "words": wc, "error": "",
            })

        else:
            fail_counts[chosen] = fail_counts.get(chosen, 0) + 1
            err = result.get("error", "Unknown")
            logger.warning(f"         FAILED: {err[:80]}")

            # Retry with next platform immediately
            platform_idx -= 1  # Don't advance — retry same position with next platform
            results.append({
                "no": i + 1, "platform": chosen, "da": da,
                "title": title, "url": "", "verified": "FAIL",
                "words": wc, "error": err[:100],
            })

        # Delay between posts
        if i < count - 1:
            time.sleep(delay)

    # Save results CSV
    os.makedirs(config.BLOG_OUTPUT_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = os.path.join(config.BLOG_OUTPUT_DIR, f"batch_results_{ts}.csv")

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["no", "platform", "da", "title", "url", "verified", "words", "error"])
        writer.writeheader()
        writer.writerows(results)

    # Final summary
    success = [r for r in results if r["url"] and r["url"] != "DRY_RUN" and not r["error"]]
    failed  = [r for r in results if r["error"]]
    verified_ok = [r for r in success if r["verified"] == "PASS"]

    logger.info("")
    logger.info("=" * 60)
    logger.info(f"  BATCH COMPLETE")
    logger.info(f"  Total posted   : {len(success)}/{count}")
    logger.info(f"  Verified OK    : {len(verified_ok)}/{len(success)}")
    logger.info(f"  Failed         : {len(failed)}")
    logger.info(f"  Results saved  : {csv_path}")
    logger.info("=" * 60)
    logger.info("")

    # Print live URLs
    if success:
        logger.info("Published URLs:")
        for r in success:
            logger.info(f"  [{r['no']:02d}] DA {r['da']:2} | {r['platform']:10} | {r['url']}")

    return results


def main():
    parser = argparse.ArgumentParser(description="Batch post 50 blogs to scotle.org backlink sites")
    parser.add_argument("--count",   type=int, default=50,    help="Number of posts (default: 50)")
    parser.add_argument("--delay",   type=int, default=20,    help="Seconds between posts (default: 20)")
    parser.add_argument("--dry-run", action="store_true",     help="Generate content only, do not post")
    args = parser.parse_args()

    post_batch(count=args.count, delay=args.delay, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
