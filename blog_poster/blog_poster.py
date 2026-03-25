"""
blog_poster.py
==============
Main orchestration pipeline for the Blog Auto-Poster system.

Usage:
    python -m blog_poster.blog_poster                              # Interactive mode
    python -m blog_poster.blog_poster --platform telegraph         # Post to Telegraph
    python -m blog_poster.blog_poster --all-platforms              # Post to all enabled
    python -m blog_poster.blog_poster --all-platforms --count 3    # 3 articles total
    python -m blog_poster.blog_poster --schedule                   # Daily auto-posting
    python -m blog_poster.blog_poster --report                     # Generate Excel report
    python -m blog_poster.blog_poster --validate                   # Test all credentials
"""

import os
import sys
import time
import random
import logging
import argparse
import threading
import schedule
from datetime import datetime

# Add parent directory to path so imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from blog_poster import blog_config as config
from blog_poster.blog_platforms import PosterFactory
from blog_poster.blog_tracker import (
    log_post, get_used_topics, get_today_post_count,
    is_duplicate_post, generate_report, open_file,
    update_post_verification,
)
from blog_poster.verifier import verify_post, log_failed_verification
from blog_poster.blog_utils import (
    generate_article_from_template, get_next_topic,
    inject_backlinks, build_author_bio, add_authority_links,
    generate_with_ollama, generate_with_openai,
)
from blog_poster.templates.article_templates import get_templates, get_all_niches


# ===========================================================
# LOGGING
# ===========================================================

def setup_logging():
    os.makedirs(config.BLOG_OUTPUT_DIR, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(
                os.path.join(config.BLOG_OUTPUT_DIR, "poster.log"),
                encoding="utf-8",
            ),
        ],
    )

logger = logging.getLogger(__name__)


# ===========================================================
# GOOGLE INDEXING PING
# ===========================================================

def ping_search_engines(url: str) -> str:
    """
    Ping Bing and IndexNow with the published URL to request indexing.
    Runs in a daemon thread — bounded by an 8-second join.
    Returns: "success" | "fail" | "error:<message>"
    """
    result_holder = [""]

    def _ping():
        try:
            import requests as req
            results = []

            # Bing sitemap ping (no key required)
            try:
                r = req.get(
                    f"https://www.bing.com/ping?sitemap={url}",
                    timeout=5,
                )
                results.append("bing:ok" if r.status_code in (200, 302) else f"bing:{r.status_code}")
            except Exception as e:
                results.append(f"bing:err:{str(e)[:40]}")

            # IndexNow ping (Bing endpoint — fastest indexing for new pages)
            try:
                r2 = req.get(
                    f"https://api.indexnow.org/indexnow?url={url}&key=scotle2026indexnow",
                    timeout=5,
                )
                results.append("indexnow:ok" if r2.status_code in (200, 202) else f"indexnow:{r2.status_code}")
            except Exception as e:
                results.append(f"indexnow:err:{str(e)[:40]}")

            result_holder[0] = "success" if any("ok" in r for r in results) else "fail"
        except Exception as e:
            result_holder[0] = f"error:{str(e)[:80]}"

    t = threading.Thread(target=_ping, daemon=True)
    t.start()
    t.join(timeout=8)
    return result_holder[0] or "error:timeout"


# Keep old name as alias for backwards compatibility
def ping_google(url: str) -> str:
    return ping_search_engines(url)


# ===========================================================
# CONTENT GENERATION PIPELINE
# ===========================================================

def generate_content(topic: str = None, niche: str = None) -> dict:
    """
    Generate a blog article using the configured method.

    Returns:
        dict with: title, content_html, word_count
    """
    used = get_used_topics(config.POSTS_LOG_CSV)

    # Generate topic if not provided
    if not topic:
        topic = get_next_topic(config.TARGET_KEYWORDS, used_topics=used)

    # Method 1: Template-based (default)
    if config.CONTENT_METHOD == "template":
        # Prefer school/education niches — 70% school, 20% education, 10% other
        if not niche:
            niche = random.choices(
                ["school", "school", "school", "school", "school",
                 "school", "school", "education", "education", "how_to"],
                k=1
            )[0]
        templates = get_templates(niche)
        template = random.choice(templates)

        keyword = random.choice(config.TARGET_KEYWORDS)
        article = generate_article_from_template(
            template=template,
            keyword=keyword,
            brand=config.TARGET_BRAND,
            spin=config.SPIN_CONTENT,
        )
        article["title"] = topic  # Use the generated topic as title
        return article

    # Method 2: Ollama (free local AI)
    elif config.CONTENT_METHOD == "ollama":
        result = generate_with_ollama(
            topic, config.TARGET_KEYWORDS,
            config.OLLAMA_URL, config.OLLAMA_MODEL,
        )
        if result:
            return result
        logger.warning("Ollama failed, falling back to template")

    # Method 3: OpenAI (paid)
    elif config.CONTENT_METHOD == "openai" and config.OPENAI_API_KEY:
        result = generate_with_openai(
            topic, config.TARGET_KEYWORDS,
            config.OPENAI_API_KEY, config.OPENAI_MODEL,
        )
        if result:
            return result
        logger.warning("OpenAI failed, falling back to template")

    # Fallback to template
    niche = niche or "school"
    templates = get_templates(niche)
    template = random.choice(templates)
    keyword = random.choice(config.TARGET_KEYWORDS)
    article = generate_article_from_template(template, keyword, brand=config.TARGET_BRAND)
    article["title"] = topic
    return article


# ===========================================================
# POST TO SINGLE PLATFORM
# ===========================================================

def post_to_platform(platform_name: str, topic: str = None, niche: str = None) -> dict:
    """
    Full pipeline: generate content -> inject links -> post -> track.

    Returns:
        Post result dict
    """
    logger.info(f"--- Posting to {platform_name.upper()} ---")

    # Check daily limit
    today_count = get_today_post_count(config.POSTS_LOG_CSV, platform_name)
    if today_count >= config.MAX_POSTS_PER_PLATFORM:
        logger.warning(f"Daily limit reached for {platform_name} ({today_count} posts today)")
        return {"success": False, "platform": platform_name, "error": "Daily limit reached"}

    # Step 1: Generate content
    logger.info("Generating article content...")
    article = generate_content(topic=topic, niche=niche)
    title = article["title"]
    content = article["content_html"]

    # Check for duplicate
    if is_duplicate_post(title, platform_name, config.POSTS_LOG_CSV):
        logger.warning(f"Duplicate title for {platform_name}: {title}")
        title = title + f" ({datetime.now().strftime('%B %Y')})"

    # Step 2: Inject backlinks
    logger.info("Injecting backlinks...")
    anchor_text = random.choice(config.ANCHOR_TEXTS)
    content = inject_backlinks(
        content, config.TARGET_URL, config.ANCHOR_TEXTS,
        max_links=config.MAX_BACKLINKS_PER_POST,
        nofollow_pct=config.NOFOLLOW_PERCENTAGE,
    )

    # Add authority links
    content = add_authority_links(content, config.AUTHORITY_LINKS)

    # Add author bio
    if config.ADD_AUTHOR_BIO:
        bio = build_author_bio(config.TARGET_URL, config.TARGET_BRAND, anchor_text)
        content += "\n\n" + bio

    # Step 3: Post to platform
    logger.info(f"Publishing to {platform_name}...")
    try:
        poster = PosterFactory.get_poster(platform_name, config)
        result = poster.post(title, content, tags=config.TARGET_KEYWORDS[:5])
    except Exception as e:
        logger.error(f"Posting failed: {e}")
        result = {"success": False, "url": "", "platform": platform_name, "post_id": "", "error": str(e)}

    # Step 4: Track result
    track_data = {
        "post_id": result.get("post_id", ""),
        "platform": platform_name,
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

    if result.get("success"):
        logger.info(f"SUCCESS: {result.get('url', 'No URL')}")

        post_url = result.get("url", "")

        # Step 5: Google indexing ping (non-blocking, R11-R13)
        logger.info("Pinging Google...")
        ping_result = ping_google(post_url)
        logger.info(f"Google ping: {ping_result}")

        # Step 6: Verify post is live and contains backlink (R19-R20)
        logger.info("Verifying post...")
        verified = verify_post(post_url)
        logger.info(f"Verification: {'PASS' if verified else 'FAIL'}")

        if not verified:
            log_failed_verification(track_data, config.FAILED_POSTS_CSV)

        update_post_verification(config.POSTS_LOG_CSV, post_url, verified, ping_result)
    else:
        logger.error(f"FAILED: {result.get('error', 'Unknown error')}")

    return result


# ===========================================================
# POST TO ALL PLATFORMS
# ===========================================================

def post_to_all_platforms(count: int = 1, niche: str = None):
    """Post articles to all enabled platforms with delays."""
    platforms = PosterFactory.get_enabled_platforms(config)

    if not platforms:
        logger.error("No platforms enabled! Edit blog_config.py to enable at least one platform.")
        logger.info("Tip: Telegraph requires no signup - set TELEGRAPH_CONFIG['enabled'] = True")
        return

    logger.info(f"Enabled platforms: {', '.join(platforms)}")
    logger.info(f"Posts to create: {count}")

    total_today = get_today_post_count(config.POSTS_LOG_CSV)
    if total_today >= config.POSTS_PER_DAY:
        logger.warning(f"Daily total limit reached ({total_today} posts today). Stopping.")
        return

    results = []
    posts_made = 0

    for i in range(count):
        # Rotate platforms
        platform = platforms[i % len(platforms)]

        logger.info(f"\n{'='*50}")
        logger.info(f"Post {i+1}/{count} -> {platform}")
        logger.info(f"{'='*50}")

        result = post_to_platform(platform, niche=niche)
        results.append(result)
        posts_made += 1

        # Check daily limit
        if posts_made >= config.POSTS_PER_DAY:
            logger.info("Daily post limit reached. Stopping.")
            break

        # Delay between posts
        if i < count - 1:
            delay = random.uniform(config.MIN_DELAY_SECONDS, config.MAX_DELAY_SECONDS)
            logger.info(f"Waiting {delay/60:.1f} minutes before next post...")
            time.sleep(delay)

    # Summary
    success = sum(1 for r in results if r.get("success"))
    logger.info(f"\n{'='*50}")
    logger.info(f"DONE: {success}/{len(results)} posts published successfully")
    logger.info(f"Log: {config.POSTS_LOG_CSV}")
    logger.info(f"{'='*50}\n")

    return results


# ===========================================================
# VALIDATE CREDENTIALS
# ===========================================================

def validate_all_credentials():
    """Test credentials for all enabled platforms."""
    platforms = PosterFactory.get_all_platforms()

    logger.info("Validating platform credentials...\n")

    for name in platforms:
        config_map = {
            "telegraph":   config.TELEGRAPH_CONFIG,
            "wordpress":   config.WORDPRESS_CONFIG,
            "blogger":     config.BLOGGER_CONFIG,
            "tumblr":      config.TUMBLR_CONFIG,
            "medium":      config.MEDIUM_CONFIG,
            "hashnode":    config.HASHNODE_CONFIG,
            "devto":       config.DEVTO_CONFIG,
            "writeas":     config.WRITEAS_CONFIG,
            "justpasteit": config.JUSTPASTEIT_CONFIG,
            "substack":    config.SUBSTACK_CONFIG,
            "linkedin":    config.LINKEDIN_CONFIG,
            "hackmd":      config.HACKMD_CONFIG,
            "github":      config.GITHUB_CONFIG,
            "gitlab":      config.GITLAB_CONFIG,
            "livejournal": config.LIVEJOURNAL_CONFIG,
            "pastebin":    config.PASTEBIN_CONFIG,
            "pastegg":     config.PASTEGG_CONFIG,
            "dpaste":      config.DPASTE_CONFIG,
            "rentry":      config.RENTRY_CONFIG,
            "bytebin":     config.BYTEBIN_CONFIG,
        }

        enabled = config_map[name].get("enabled", False)

        if not enabled:
            logger.info(f"  {name:12s} : DISABLED (skip)")
            continue

        try:
            poster = PosterFactory.get_poster(name, config)
            valid = poster.validate_credentials()
            status = "OK" if valid else "FAILED"
            logger.info(f"  {name:12s} : {status}")
        except Exception as e:
            logger.info(f"  {name:12s} : ERROR - {e}")

    logger.info("")


# ===========================================================
# SCHEDULER
# ===========================================================

def schedule_daily(count: int, niche: str = None):
    """Set up daily auto-posting schedule."""
    run_time = config.DAILY_POST_TIME

    logger.info(f"Scheduler enabled. Will post daily at {run_time}")
    logger.info(f"Posts per day: {count}")
    logger.info("Running immediately for the first time...")
    logger.info("Press Ctrl+C to stop\n")

    post_to_all_platforms(count, niche)

    schedule.every().day.at(run_time).do(post_to_all_platforms, count, niche)

    try:
        while True:
            schedule.run_pending()
            time.sleep(30)
    except KeyboardInterrupt:
        logger.info("\nScheduler stopped.")


# ===========================================================
# CLI
# ===========================================================

def parse_args():
    parser = argparse.ArgumentParser(
        description="Blog Auto-Poster - Publish articles to multiple platforms for SEO backlinks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m blog_poster.blog_poster --platform telegraph
  python -m blog_poster.blog_poster --all-platforms --count 3
  python -m blog_poster.blog_poster --schedule
  python -m blog_poster.blog_poster --report
  python -m blog_poster.blog_poster --validate
        """,
    )
    parser.add_argument("--platform", help="Post to specific platform (telegraph, wordpress, blogger, tumblr, medium, hashnode)")
    parser.add_argument("--all-platforms", action="store_true", help="Post to all enabled platforms")
    parser.add_argument("--topic", help="Custom blog topic/title")
    parser.add_argument("--niche", help=f"Article niche: {', '.join(get_all_niches())}")
    parser.add_argument("--count", type=int, default=1, help="Number of articles to post (default: 1)")
    parser.add_argument("--schedule", action="store_true", help=f"Run daily at {config.DAILY_POST_TIME}")
    parser.add_argument("--report", action="store_true", help="Generate Excel report")
    parser.add_argument("--validate", action="store_true", help="Validate platform credentials")
    return parser.parse_args()


# ===========================================================
# MAIN
# ===========================================================

def main():
    setup_logging()
    args = parse_args()

    logger.info("")
    logger.info("=" * 55)
    logger.info("  BLOG AUTO-POSTER")
    logger.info(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 55)

    # Validate credentials
    if args.validate:
        validate_all_credentials()
        return

    # Generate report
    if args.report:
        generate_report(config.POSTS_LOG_CSV, config.POSTS_REPORT_XLSX)
        open_file(config.POSTS_REPORT_XLSX)
        return

    # Schedule mode
    if args.schedule:
        count = args.count or config.POSTS_PER_DAY
        schedule_daily(count, args.niche)
        return

    # Post to specific platform
    if args.platform:
        result = post_to_platform(args.platform, topic=args.topic, niche=args.niche)
        return

    # Post to all enabled platforms
    if args.all_platforms:
        post_to_all_platforms(count=args.count, niche=args.niche)
        return

    # Interactive mode
    print("\n" + "=" * 55)
    print("       Blog Auto-Poster")
    print("=" * 55)
    print("  Generate & publish blog articles for SEO backlinks")
    print("=" * 55 + "\n")

    platforms = PosterFactory.get_enabled_platforms(config)
    if not platforms:
        print("No platforms enabled! Edit blog_poster/blog_config.py first.")
        print("Tip: Set TELEGRAPH_CONFIG['enabled'] = True (no signup needed)")
        return

    print(f"Enabled platforms: {', '.join(platforms)}")
    print(f"Target URL: {config.TARGET_URL}")
    print(f"Keywords: {', '.join(config.TARGET_KEYWORDS[:3])}...\n")

    choice = input("Post to [A]ll platforms or [S]ingle platform? [A/S]: ").strip().upper()

    if choice == "S":
        print(f"\nAvailable: {', '.join(platforms)}")
        platform = input("Enter platform name: ").strip().lower()
        if platform not in platforms:
            print(f"Platform '{platform}' not enabled. Check blog_config.py")
            return
        topic = input("Custom topic (or press Enter for auto): ").strip() or None
        post_to_platform(platform, topic=topic)
    else:
        count = input(f"How many posts? [1-{config.POSTS_PER_DAY}]: ").strip()
        count = int(count) if count.isdigit() else 1
        post_to_all_platforms(count=min(count, config.POSTS_PER_DAY))


if __name__ == "__main__":
    main()
