"""
bulk_post.py
============
Bulk-publish blog articles to Write.as with scotle.org backlinks.
Each post gets unique content via spinning + random templates.
"""

import os
import sys
import time
import random
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from blog_poster import blog_config as config
from blog_poster.blog_platforms import WriteAsPoster
from blog_poster.blog_tracker import log_post, get_used_topics
from blog_poster.blog_utils import (
    generate_article_from_template, get_next_topic,
    inject_backlinks, build_author_bio, add_authority_links,
)
from blog_poster.templates.article_templates import get_templates, get_all_niches

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

TARGET_COUNT = 24  # Remaining posts needed


def generate_and_post(poster, post_num):
    """Generate unique article and post to Write.as."""
    used = get_used_topics(config.POSTS_LOG_CSV)

    # Pick random niche and template
    niche = random.choice(get_all_niches())
    templates = get_templates(niche)
    template = random.choice(templates)
    keyword = random.choice(config.TARGET_KEYWORDS)
    topic = get_next_topic(config.TARGET_KEYWORDS, used_topics=used)

    # Generate article
    article = generate_article_from_template(
        template=template, keyword=keyword,
        brand=config.TARGET_BRAND, city="Jaipur",
        spin=True,
    )
    article["title"] = topic

    title = article["title"]
    content = article["content_html"]

    # Inject backlinks
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

    # Post
    result = poster.post(title, content, tags=config.TARGET_KEYWORDS[:5])

    # Track
    track_data = {
        "post_id": result.get("post_id", ""),
        "platform": "writeas",
        "title": title,
        "url": result.get("url", ""),
        "target_url": config.TARGET_URL,
        "anchor_text": anchor_text,
        "tags": config.TARGET_KEYWORDS[:5],
        "word_count": article.get("word_count", 0),
        "status": "published" if result.get("success") else "failed",
        "error": result.get("error", ""),
    }
    log_post(track_data, config.POSTS_LOG_CSV)

    return result


def main():
    print("\n" + "=" * 60)
    print(f"  BULK BLOG POSTER - {TARGET_COUNT} Articles")
    print(f"  Target: {config.TARGET_URL}")
    print(f"  Brand: {config.TARGET_BRAND}")
    print("=" * 60 + "\n")

    poster = WriteAsPoster(
        config=config.WRITEAS_CONFIG,
        min_delay=2, max_delay=5,
    )

    success_count = 0
    results = []

    for i in range(1, TARGET_COUNT + 1):
        print(f"  [{i}/{TARGET_COUNT}] Posting...", end=" ", flush=True)

        try:
            result = generate_and_post(poster, i)
            if result.get("success"):
                success_count += 1
                print(f"OK -> {result.get('url')}")
                results.append(result)
            else:
                print(f"FAILED -> {result.get('error')}")
        except Exception as e:
            print(f"ERROR -> {e}")

        # Longer delay to avoid rate limits
        if i < TARGET_COUNT:
            delay = random.uniform(15, 25)
            time.sleep(delay)

    # Summary
    print("\n" + "=" * 60)
    print(f"  DONE! {success_count}/{TARGET_COUNT} published")
    print("=" * 60)
    print(f"\n  ALL LIVE URLS:\n")
    for j, r in enumerate(results, 1):
        print(f"  {j:>2}. {r.get('url')}")
    print(f"\n  All posts link back to: {config.TARGET_URL}")
    print(f"  Log: {config.POSTS_LOG_CSV}\n")


if __name__ == "__main__":
    main()
