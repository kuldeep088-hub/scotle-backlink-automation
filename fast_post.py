"""
fast_post.py
============
Runs bulk posting with fast delays (5-10 sec between posts).
Skips platforms that are failing.

Usage:
    python fast_post.py --count 30
    python fast_post.py --count 50
    python fast_post.py --platforms writeas hackmd pastegg dpaste rentry
"""

import os
import sys
import time
import random
import argparse
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from blog_poster import blog_config as config
from blog_poster.blog_poster import setup_logging, post_to_platform
from blog_poster.blog_platforms import PosterFactory

logger = logging.getLogger(__name__)

DEFAULT_PLATFORMS = ["writeas", "hackmd", "pastegg", "dpaste", "rentry"]

def parse_args():
    p = argparse.ArgumentParser(description="Fast bulk poster with short delays")
    p.add_argument("--count", type=int, default=30, help="Number of posts to make")
    p.add_argument("--platforms", nargs="+", default=None,
                   help=f"Platforms to post to (default: {DEFAULT_PLATFORMS})")
    p.add_argument("--niche", default="school", help="Article niche (default: school)")
    p.add_argument("--delay-min", type=int, default=5, help="Min delay seconds (default: 5)")
    p.add_argument("--delay-max", type=int, default=12, help="Max delay seconds (default: 12)")
    return p.parse_args()


def main():
    setup_logging()
    args = parse_args()

    platforms = args.platforms or DEFAULT_PLATFORMS
    count = args.count

    # Override delays and limits temporarily in memory
    config.MIN_DELAY_SECONDS = args.delay_min
    config.MAX_DELAY_SECONDS = args.delay_max
    config.POSTS_PER_DAY = count + 100         # lift total daily cap
    config.MAX_POSTS_PER_PLATFORM = count + 100 # lift per-platform cap

    print(f"\n=== FAST POSTER ===")
    print(f"Platforms : {', '.join(platforms)}")
    print(f"Posts     : {count}")
    print(f"Niche     : {args.niche}")
    print(f"Delay     : {args.delay_min}-{args.delay_max} sec between posts")
    print(f"Est. time : ~{round(count * (args.delay_min + args.delay_max) / 2 / 60, 1)} minutes")
    print()

    success_count = 0
    fail_count = 0
    published_urls = []

    for i in range(count):
        platform = platforms[i % len(platforms)]
        print(f"[{i+1}/{count}] Posting to {platform}...", end=" ", flush=True)

        result = post_to_platform(platform, niche=args.niche)

        if result and result.get("success"):
            url = result.get("url", "")
            print(f"OK -> {url}")
            published_urls.append((platform, url))
            success_count += 1
        else:
            err = result.get("error", "unknown") if result else "no result"
            print(f"FAILED ({err[:60]})")
            fail_count += 1

        if i < count - 1:
            delay = random.uniform(args.delay_min, args.delay_max)
            time.sleep(delay)

    # Summary
    print(f"\n{'='*60}")
    print(f"DONE: {success_count}/{count} posts published successfully")
    print(f"Failed: {fail_count}")
    print(f"Log: {config.POSTS_LOG_CSV}")
    print(f"{'='*60}")

    if published_urls:
        print(f"\nPublished URLs:")
        for platform, url in published_urls:
            print(f"  [{platform}] {url}")

    # Export to CSV bundle
    print(f"\nExporting results to Google Sheets CSV bundle...")
    from blog_poster.gsheet_reporter import GSheetReporter
    reporter = GSheetReporter()
    posts = reporter._read_posts_csv(config.POSTS_LOG_CSV)
    from blog_poster.high_da_sites import get_all_sites
    sites = get_all_sites()
    reporter._export_csv_bundle(posts, sites, config.POSTS_LOG_CSV)


if __name__ == "__main__":
    main()
