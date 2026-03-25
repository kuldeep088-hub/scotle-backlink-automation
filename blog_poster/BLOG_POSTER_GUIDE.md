# Blog Auto-Poster System - Complete Guide

## What Is This?

This is an **automated blog posting system** that creates and publishes blog articles on free platforms to build **SEO backlinks** for your website. It helps your website rank higher on Google.

---

## How It Works (Simple Flow)

```
Step 1: You set your website URL + keywords in blog_config.py
Step 2: System generates a unique 500-1000 word article
Step 3: System injects your website link naturally in the article
Step 4: System publishes to Telegraph/WordPress/Blogger/Tumblr/Medium/Hashnode
Step 5: System saves post URL + details in CSV/Excel report
Step 6: System waits 5-15 minutes, then repeats for next platform
```

---

## Quick Start (5 Minutes)

### Step 1: Edit Configuration
Open `blog_poster/blog_config.py` and change:

```python
TARGET_URL = "https://yourwebsite.com"      # Your website URL
TARGET_BRAND = "Your Brand Name"            # Your brand name
TARGET_KEYWORDS = ["your keyword 1", "your keyword 2", ...]
```

### Step 2: Enable Telegraph (No Signup Needed!)
Telegraph is already enabled by default. No signup, no API key needed.

### Step 3: Run It
```bash
# Post to Telegraph
python -m blog_poster.blog_poster --platform telegraph

# Post to all enabled platforms
python -m blog_poster.blog_poster --all-platforms

# Post 3 articles
python -m blog_poster.blog_poster --all-platforms --count 3
```

### Step 4: Check Results
- CSV log: `blog_poster/output/posts_log.csv`
- Generate Excel report: `python -m blog_poster.blog_poster --report`

---

## All Commands

| Command | What It Does |
|---------|-------------|
| `--platform telegraph` | Post to specific platform |
| `--all-platforms` | Post to all enabled platforms |
| `--all-platforms --count 3` | Post 3 articles across platforms |
| `--topic "Your Topic"` | Use custom topic instead of auto-generated |
| `--niche business` | Use templates from specific niche |
| `--schedule` | Run daily at configured time (auto) |
| `--report` | Generate Excel report of all posts |
| `--validate` | Test all platform credentials |

---

## Platform Setup Guide

### 1. Telegraph (telegra.ph) - NO SETUP NEEDED
- Already enabled by default
- Token is auto-generated on first run
- Just run the command and it works!

### 2. WordPress.com
1. Create free blog at wordpress.com
2. Go to developer.wordpress.com/apps/
3. Create a new application
4. Get the OAuth2 access token
5. Edit `blog_config.py`:
```python
WORDPRESS_CONFIG = {
    "enabled": True,
    "site_url": "yourblog.wordpress.com",
    "access_token": "YOUR_TOKEN_HERE",
}
```

### 3. Blogger (Google)
1. Go to console.cloud.google.com
2. Create a project → Enable "Blogger API"
3. Create API key (Credentials → Create → API Key)
4. Create a blog at blogger.com
5. Get your Blog ID from blog settings URL
6. Edit `blog_config.py`:
```python
BLOGGER_CONFIG = {
    "enabled": True,
    "blog_id": "YOUR_BLOG_ID",
    "api_key": "YOUR_API_KEY",
}
```

### 4. Tumblr
1. Go to tumblr.com/oauth/apps
2. Register a new application
3. Get consumer key, consumer secret, OAuth token, and OAuth secret
4. Edit `blog_config.py`:
```python
TUMBLR_CONFIG = {
    "enabled": True,
    "blog_name": "yourblog",
    "consumer_key": "...",
    "consumer_secret": "...",
    "oauth_token": "...",
    "oauth_secret": "...",
}
```

### 5. Medium
1. Go to medium.com/me/settings
2. Scroll to "Integration tokens"
3. Generate a new token
4. Edit `blog_config.py`:
```python
MEDIUM_CONFIG = {
    "enabled": True,
    "integration_token": "YOUR_TOKEN_HERE",
}
```

### 6. Hashnode
1. Go to hashnode.com/settings/developer
2. Generate a Personal Access Token
3. Get your publication ID from your blog settings
4. Edit `blog_config.py`:
```python
HASHNODE_CONFIG = {
    "enabled": True,
    "token": "YOUR_TOKEN_HERE",
    "publication_id": "YOUR_PUB_ID",
}
```

---

## Content Generation Methods

### Method 1: Templates (Default - No AI Needed)
- Uses 10+ pre-built article templates
- Organized by niche: business, local_services, technology, how_to, health, education
- Placeholders auto-filled with your keywords
- Content spinning makes each article unique
- **No internet or API needed for generation**

### Method 2: Ollama (Free Local AI)
- Install Ollama from ollama.ai
- Run: `ollama pull llama3`
- Set in config: `CONTENT_METHOD = "ollama"`
- Generates high-quality unique articles locally
- **Free, no API key needed, runs on your PC**

### Method 3: OpenAI (Paid)
- Set your API key in config: `OPENAI_API_KEY = "sk-..."`
- Set: `CONTENT_METHOD = "openai"`
- Uses GPT-3.5 or GPT-4 for premium content
- **Requires paid OpenAI API credits**

---

## How Backlinks Are Injected

The system places your website link naturally inside articles:

1. **In-content links** (2 per article):
   - One in the first third of the article
   - One in the last third
   - Uses random anchor text from your list

2. **Author bio link**:
   - "This article was contributed by [Your Brand](yoursite.com)"
   - Added at the end of every article

3. **Anti-spam protection**:
   - Different anchor text each time
   - 70% dofollow + 30% nofollow mix
   - Links to authority sites (Wikipedia, Forbes) mixed in
   - Unique content per platform (never duplicate)

---

## Anti-Spam Measures

| Protection | How It Works |
|------------|-------------|
| Unique content | Each platform gets a different spun version |
| Random delays | 5-15 minutes between posts |
| Anchor rotation | Different link text for each post |
| Nofollow mix | 30% links marked nofollow (looks natural) |
| Word count variation | Articles are 500-1200 words (random) |
| Daily limits | Max posts per day and per platform |
| Authority link mix | Links to Wikipedia etc. alongside yours |

---

## File Structure

```
blog_poster/
├── __init__.py              # Package init
├── blog_config.py           # All settings (EDIT THIS FIRST)
├── blog_utils.py            # Content generation engine
├── blog_platforms.py        # Platform API integrations
├── blog_poster.py           # Main pipeline
├── blog_tracker.py          # Post tracking & reporting
├── telegraph_token.txt      # Auto-generated Telegraph token
├── templates/
│   └── article_templates.py # Article templates by niche
├── output/
│   ├── posts_log.csv        # All posts logged here
│   ├── posts_report.xlsx    # Excel report
│   └── poster.log           # Debug log
└── BLOG_POSTER_GUIDE.md     # This file
```

---

## Scheduling (Auto Daily Posting)

Run daily at 10:00 AM (configurable):
```bash
python -m blog_poster.blog_poster --schedule
```

Change time in `blog_config.py`:
```python
DAILY_POST_TIME = "10:00"  # Change to your preferred time
POSTS_PER_DAY = 3          # Total posts per day
```

Keep the terminal open or run as a background service.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "No platforms enabled" | Edit blog_config.py, set `"enabled": True` for at least one platform |
| Telegraph connection error | Check internet connection, try again |
| WordPress 401 error | Regenerate your OAuth token |
| Blogger 403 error | Check API key and Blog ID |
| Medium rate limit | Wait 24 hours, Medium limits API usage |
| Hashnode error | Check token and publication_id |

---

## Tips for Best SEO Results

1. **Start with Telegraph** (easiest, no setup)
2. **Add platforms gradually** (1 new platform per week)
3. **Use relevant keywords** in TARGET_KEYWORDS
4. **Vary your anchor texts** (add 5-10 different options)
5. **Don't overdo it** (2-3 posts/day is enough)
6. **Be patient** (SEO takes 2-3 months to show results)
7. **Monitor your rankings** with Google Search Console
