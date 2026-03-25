# EXAMPLE CONFIG — copy to blog_config.py and fill in your credentials
# cp blog_poster/blog_config.example.py blog_poster/blog_config.py

"""
blog_config.py
==============
Central configuration for the Blog Auto-Poster system.
All settings, credentials, and tunable parameters are here.

Setup:
    1. Set your TARGET_URL (the website you want backlinks to)
    2. Set your TARGET_KEYWORDS and ANCHOR_TEXTS
    3. Add platform credentials (start with Telegraph - no signup needed)
    4. Run: python -m blog_poster.blog_poster --validate
"""

import os

# ===========================================================
# TARGET WEBSITE (your website that needs backlinks)
# ===========================================================

TARGET_URL = "https://scotle.org/"               # Your website
TARGET_BRAND = "Scotle"                          # Your brand

# Keywords related to your business (used in article generation)
TARGET_KEYWORDS = [
    # Primary brand + location keywords
    "best CBSE school in Jaipur",
    "Scotle High School Jaipur",
    "CBSE school admission Jaipur 2026",
    "top school in Jaipur with JEE NEET coaching",
    # Long-tail specific keywords
    "best school near Vaishali Nagar Jaipur",
    "JEE NEET coaching school Jaipur fees",
    "top rated CBSE school Jaipur with hostel",
    "affordable CBSE school Jaipur 2026",
    "Scotle High School Jaipur reviews",
    "CBSE school Jaipur with smart classroom",
    "school admissions Jaipur 2026",
    "best high school Jaipur science stream",
    # Parent-focused keywords
    "how to choose school in Jaipur",
    "best school for JEE preparation Jaipur",
    "best school for NEET preparation Jaipur",
    "top CBSE schools Jaipur fees structure",
    "CBSE school Jaipur Class 11 science",
    "school with smart classroom Jaipur",
    "CBSE school Jaipur with transport facility",
    "best school for class 9 10 Jaipur",
    # Brand + intent
    "Scotle High School admission 2026",
    "scotle.org Jaipur",
    "Scotle school Jaipur reviews",
    "best school Jaipur for science students",
]

# Anchor texts — diverse mix (brand, URL, generic, long-tail, keyword)
ANCHOR_TEXTS = [
    # Brand anchors (~30%)
    "Scotle",
    "Scotle.org",
    "scotle.org",
    "Scotle High School",
    "Scotle High School Jaipur",
    # Generic anchors (~40%)
    "click here",
    "visit website",
    "find out more",
    "check it out",
    "learn more",
    "read more here",
    "see full details",
    "explore this",
    "get information here",
    "view details",
    "more information",
    "official website",
    # Keyword anchors (~30%)
    "Best CBSE School in Jaipur",
    "top school in Jaipur",
    "Admissions Open at Scotle",
    "CBSE school Jaipur",
    "school with JEE NEET coaching Jaipur",
    "best high school in Jaipur",
    "CBSE school admission Jaipur 2026",
    "Scotle school Jaipur",
    "top CBSE school Jaipur science stream",
    "school near Vaishali Nagar Jaipur",
]

# ===========================================================
# PLATFORM CREDENTIALS
# ===========================================================

# Telegraph - NO SIGNUP NEEDED (token auto-generated on first run)
# NOTE: telegra.ph is blocked by some ISPs. Disable if connection fails.
TELEGRAPH_CONFIG = {
    "enabled": False,   # Disabled - connection blocked by ISP
    "author_name": TARGET_BRAND,
    "author_url": TARGET_URL,
    "access_token": "",  # Auto-generated, saved to telegraph_token.txt
}

# WordPress.com - Register app at developer.wordpress.com/apps/
WORDPRESS_CONFIG = {
    "enabled": False,
    "site_url": "yourblog.wordpress.com",       # Your free WordPress.com blog URL
    "access_token": "",                          # OAuth2 access token
}

# Blogger (Google) - Enable Blogger API in Google Cloud Console
BLOGGER_CONFIG = {
    "enabled": True,
    "blog_id": "YOUR_BLOGGER_BLOG_ID",
    "api_key": "YOUR_BLOGGER_API_KEY",
    "client_id": "YOUR_GOOGLE_CLIENT_ID",
    "client_secret": "YOUR_GOOGLE_CLIENT_SECRET",
    "refresh_token": "YOUR_GOOGLE_REFRESH_TOKEN",
}

# Tumblr - Register app at tumblr.com/oauth/apps
TUMBLR_CONFIG = {
    "enabled": True,
    "blog_name": "scotlehighschool",
    "consumer_key": "YOUR_TUMBLR_CONSUMER_KEY",
    "consumer_secret": "YOUR_TUMBLR_CONSUMER_SECRET",
    "oauth_token": "YOUR_TUMBLR_OAUTH_TOKEN",
    "oauth_secret": "YOUR_TUMBLR_OAUTH_SECRET",
}

# Medium - Get token from medium.com/me/settings -> Integration tokens
MEDIUM_CONFIG = {
    "enabled": False,        # Set True after filling integration_token below
    "integration_token": "", # Get from medium.com/me/settings -> Integration tokens
}

# Hashnode - Get token from hashnode.com/settings/developer
HASHNODE_CONFIG = {
    "enabled": True,
    "token": "YOUR_HASHNODE_TOKEN",
    "publication_id": "YOUR_HASHNODE_PUBLICATION_ID",
}

# Dev.to (DA 90) - Get API key from https://dev.to/settings/extensions
DEVTO_CONFIG = {
    "enabled": True,
    "api_key": "YOUR_DEVTO_API_KEY",
}

# HackMD - No signup needed for public notes
HACKMD_CONFIG = {
    "enabled": True,         # Works without credentials (public notes)
    "api_url": "https://hackmd.io/api/notes",
}

# Write.as (DA 69) - NO SIGNUP NEEDED for anonymous posts
WRITEAS_CONFIG = {
    "enabled": True,       # Works without credentials (anonymous mode)
    "access_token": "",     # Optional: for posting to your blog
    "collection_alias": "", # Optional: your blog name (e.g., "myblog")
}

# JustPaste.it (DA 91) - Requires premium account for API access
JUSTPASTEIT_CONFIG = {
    "enabled": False,      # Requires premium API key
    "api_key": "",          # Get from JustPaste.it premium account
}

# Substack (DA 89) - Requires account + Playwright browser automation
SUBSTACK_CONFIG = {
    "enabled": True,
    "email": "enquiry@scotlehighschool.com",
    "password": "YOUR_PASSWORD",
    "publication": "scotlehighschool",
}

# LinkedIn Articles (DA 99) - Requires account + Playwright
# WARNING: LinkedIn has aggressive bot detection. Use with caution.
LINKEDIN_CONFIG = {
    "enabled": False,
    "email": "",
    "password": "",
}

# GitHub Gist (DA 96) - Free token: github.com/settings/tokens -> New token -> check "gist" scope only
GITHUB_CONFIG = {
    "enabled": False,
    "token": "",   # github.com/settings/tokens -> Generate new token (classic) -> gist scope only
}

# LiveJournal (DA 93) - Register free account at livejournal.com
LIVEJOURNAL_CONFIG = {
    "enabled": True,
    "username": "ext-6851967",
    "password": "YOUR_PASSWORD",
}

# GitLab Snippet (DA 95) - Free token: gitlab.com/-/user_settings/personal_access_tokens -> api scope
GITLAB_CONFIG = {
    "enabled": False,
    "token": "",   # gitlab.com/-/user_settings/personal_access_tokens -> api scope
}

# paste.gg (DA 50) - No account needed
PASTEGG_CONFIG = {
    "enabled": False,   # Disabled - Cloudflare 403 blocks API requests from India
}

# dpaste.org (DA 55) - No account needed
# NOTE: dpaste.org API returns 405; falls back to dpaste.com automatically
DPASTE_CONFIG = {
    "enabled": True,    # Re-enabled for batch posting rotation
}

# ByteBin (bytebin.lucko.me) - No account needed, no spam filter
BYTEBIN_CONFIG = {
    "enabled": True,    # Works anonymously, no credentials needed
}

# rentry.co (DA 60) - No account needed
RENTRY_CONFIG = {
    "enabled": False,   # Disabled - connection timeout from India ISPs
}

# Pastebin.com (DA 92) - Free API key: pastebin.com/api (register free account)
PASTEBIN_CONFIG = {
    "enabled": False,
    "api_dev_key": "",  # pastebin.com/api -> Your Unique Developer API Key
}


# ===========================================================
# CONTENT GENERATION
# ===========================================================

# Method: "template" (default, no AI) | "ollama" (free local AI) | "openai" (paid API)
CONTENT_METHOD = "template"

# Article length
MIN_WORD_COUNT = 800
MAX_WORD_COUNT = 1500

# Content spinning (make articles unique per platform)
SPIN_CONTENT = True

# Ollama (free local AI) - Install from ollama.ai
OLLAMA_MODEL = "llama3"
OLLAMA_URL = "http://localhost:11434"

# OpenAI (paid) - Optional
OPENAI_API_KEY = ""
OPENAI_MODEL = "gpt-3.5-turbo"


# ===========================================================
# BACKLINK INJECTION
# ===========================================================

MAX_BACKLINKS_PER_POST = 1          # One backlink per post
ADD_AUTHOR_BIO = True               # Add author bio with link at end
NOFOLLOW_PERCENTAGE = 30            # % of links marked nofollow (natural look)

# Authority sites to link to (makes your links look editorial)
AUTHORITY_LINKS = [
    ("Wikipedia", "https://en.wikipedia.org"),
    ("Forbes", "https://www.forbes.com"),
    ("HubSpot", "https://www.hubspot.com"),
]


# ===========================================================
# POSTING SCHEDULE & ANTI-SPAM
# ===========================================================

POSTS_PER_DAY = 500                 # Total posts across all platforms per day
MAX_POSTS_PER_PLATFORM = 10         # Max posts to a single platform per day
MIN_DELAY_SECONDS = 3               # 3 seconds minimum between posts
MAX_DELAY_SECONDS = 8               # 8 seconds maximum between posts
DAILY_POST_TIME = "10:00"           # When to start daily posting (HH:MM)
ROTATE_PLATFORMS = True             # Round-robin through enabled platforms


# ===========================================================
# OUTPUT / TRACKING
# ===========================================================

BLOG_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
POSTS_LOG_CSV = os.path.join(BLOG_OUTPUT_DIR, "posts_log.csv")
POSTS_REPORT_XLSX = os.path.join(BLOG_OUTPUT_DIR, "posts_report.xlsx")
TELEGRAPH_TOKEN_FILE = os.path.join(os.path.dirname(__file__), "telegraph_token.txt")
FAILED_POSTS_CSV = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "failed_posts.csv")


# ===========================================================
# HTTP / REQUEST SETTINGS
# ===========================================================

REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_DELAY = 5

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
]
