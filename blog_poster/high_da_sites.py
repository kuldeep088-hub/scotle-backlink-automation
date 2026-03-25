"""
high_da_sites.py
================
Curated database of 50+ high-DA blog posting & article sites.
Includes DA score, auth type, submission URL, and education niche suitability.

Usage:
    from blog_poster.high_da_sites import get_all_sites, get_sites_by_da, export_sites_csv
    sites = get_sites_by_da(min_da=80, auth_type="free")
    export_sites_csv("high_da_sites.csv")
"""

import csv
import os
from dataclasses import dataclass, field, asdict
from typing import List, Optional

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class HighDASite:
    name: str
    url: str
    da: int                      # Domain Authority (approximate, Moz scale)
    submission_url: str          # Direct URL to post/submit
    auth_type: str               # free | api_key | oauth | browser | premium
    platform_key: str            # matches blog_config.py key, or "" if not integrated
    education_friendly: bool     # Accepts education/school content
    notes: str = ""
    tags: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# THE DATABASE — 55 high-DA sites
# ---------------------------------------------------------------------------

SITES: List[HighDASite] = [

    # -----------------------------------------------------------------------
    # DA 95+ — Top Tier
    # -----------------------------------------------------------------------
    HighDASite(
        name="LinkedIn Articles",
        url="https://www.linkedin.com",
        da=99,
        submission_url="https://www.linkedin.com/post/new",
        auth_type="browser",
        platform_key="linkedin",
        education_friendly=True,
        notes="DA 99, excellent for school/education content. Needs account + browser automation.",
        tags=["professional", "education", "high-da"],
    ),
    HighDASite(
        name="WordPress.com",
        url="https://wordpress.com",
        da=98,
        submission_url="https://wordpress.com/post",
        auth_type="oauth",
        platform_key="wordpress",
        education_friendly=True,
        notes="DA 98. Free blog. Needs OAuth2 token from developer.wordpress.com/apps/",
        tags=["blog", "education", "high-da"],
    ),
    HighDASite(
        name="Tumblr",
        url="https://www.tumblr.com",
        da=97,
        submission_url="https://www.tumblr.com/new/text",
        auth_type="oauth",
        platform_key="tumblr",
        education_friendly=True,
        notes="DA 97. Free. OAuth1 — get keys from api.tumblr.com/console",
        tags=["blog", "education", "high-da"],
    ),
    HighDASite(
        name="Medium",
        url="https://medium.com",
        da=95,
        submission_url="https://medium.com/new-story",
        auth_type="api_key",
        platform_key="medium",
        education_friendly=True,
        notes="DA 95. Integration token from medium.com/me/settings",
        tags=["blog", "education", "high-da"],
    ),
    HighDASite(
        name="GitHub Gist",
        url="https://gist.github.com",
        da=96,
        submission_url="https://gist.github.com",
        auth_type="api_key",
        platform_key="github",
        education_friendly=True,
        notes="DA 96. Free token: github.com/settings/tokens → gist scope only",
        tags=["developer", "paste", "high-da"],
    ),
    HighDASite(
        name="GitLab Snippets",
        url="https://gitlab.com",
        da=95,
        submission_url="https://gitlab.com/-/snippets/new",
        auth_type="api_key",
        platform_key="gitlab",
        education_friendly=True,
        notes="DA 95. Free token: gitlab.com/-/user_settings/personal_access_tokens → api scope",
        tags=["developer", "paste", "high-da"],
    ),
    HighDASite(
        name="Reddit (r/India / r/education)",
        url="https://www.reddit.com",
        da=98,
        submission_url="https://www.reddit.com/r/india/submit",
        auth_type="browser",
        platform_key="",
        education_friendly=True,
        notes="DA 98. Post in r/india, r/IndiaEducation, r/jee, r/NEET_Exam. Needs Reddit account.",
        tags=["community", "education", "india", "high-da"],
    ),
    HighDASite(
        name="Blogger / Blogspot",
        url="https://www.blogger.com",
        da=97,
        submission_url="https://www.blogger.com/blog/post/create",
        auth_type="api_key",
        platform_key="blogger",
        education_friendly=True,
        notes="DA 97. Already integrated! Google API key in blog_config.py",
        tags=["blog", "education", "high-da", "integrated"],
    ),
    HighDASite(
        name="Quora Spaces",
        url="https://www.quora.com",
        da=92,
        submission_url="https://www.quora.com/spaces",
        auth_type="browser",
        platform_key="",
        education_friendly=True,
        notes="DA 92. Post in education/Jaipur/CBSE spaces. High SEO value for India.",
        tags=["qa", "education", "india", "high-da"],
    ),
    HighDASite(
        name="Pastebin",
        url="https://pastebin.com",
        da=92,
        submission_url="https://pastebin.com/api",
        auth_type="api_key",
        platform_key="pastebin",
        education_friendly=True,
        notes="DA 92. Free API key after registration. api.dev_key from pastebin.com/api",
        tags=["paste", "high-da"],
    ),
    HighDASite(
        name="LiveJournal",
        url="https://www.livejournal.com",
        da=93,
        submission_url="https://www.livejournal.com/update.bml",
        auth_type="api_key",
        platform_key="livejournal",
        education_friendly=True,
        notes="DA 93. Free account. XMLRPC API with username/password.",
        tags=["blog", "high-da"],
    ),
    HighDASite(
        name="JustPaste.it",
        url="https://justpaste.it",
        da=91,
        submission_url="https://justpaste.it/create",
        auth_type="premium",
        platform_key="justpasteit",
        education_friendly=True,
        notes="DA 91. Free manual posting. API requires premium. Great for long-form content.",
        tags=["paste", "high-da"],
    ),
    HighDASite(
        name="Dev.to",
        url="https://dev.to",
        da=90,
        submission_url="https://dev.to/new",
        auth_type="api_key",
        platform_key="devto",
        education_friendly=False,
        notes="DA 90. Tech-focused. Works for school tech topics. API key from dev.to/settings/extensions",
        tags=["developer", "technology", "high-da"],
    ),
    HighDASite(
        name="Wix Blog",
        url="https://www.wix.com",
        da=94,
        submission_url="https://manage.wix.com/blog",
        auth_type="browser",
        platform_key="",
        education_friendly=True,
        notes="DA 94. Free Wix blog. Manual posting via browser.",
        tags=["blog", "education", "high-da"],
    ),
    HighDASite(
        name="Weebly",
        url="https://www.weebly.com",
        da=90,
        submission_url="https://www.weebly.com/app/blog",
        auth_type="browser",
        platform_key="",
        education_friendly=True,
        notes="DA 90. Free blog builder. Manual posting.",
        tags=["blog", "education", "high-da"],
    ),
    HighDASite(
        name="Flipboard",
        url="https://flipboard.com",
        da=92,
        submission_url="https://flipboard.com/create",
        auth_type="browser",
        platform_key="",
        education_friendly=True,
        notes="DA 92. Create a magazine and share education articles. Good for India audience.",
        tags=["social", "education", "high-da"],
    ),

    # -----------------------------------------------------------------------
    # DA 80–94 — High Value
    # -----------------------------------------------------------------------
    HighDASite(
        name="Scoop.it",
        url="https://www.scoop.it",
        da=85,
        submission_url="https://www.scoop.it/post",
        auth_type="browser",
        platform_key="",
        education_friendly=True,
        notes="DA 85. Content curation + blog. Free account. Great for education topics.",
        tags=["curation", "education", "high-da"],
    ),
    HighDASite(
        name="Steemit",
        url="https://steemit.com",
        da=80,
        submission_url="https://steemit.com/submit",
        auth_type="browser",
        platform_key="",
        education_friendly=True,
        notes="DA 80. Blockchain blogging. Free. Posts indexed by Google.",
        tags=["blog", "education"],
    ),
    HighDASite(
        name="Hashnode",
        url="https://hashnode.com",
        da=82,
        submission_url="https://hashnode.com/post",
        auth_type="api_key",
        platform_key="hashnode",
        education_friendly=False,
        notes="DA 82. Dev-focused. API token from hashnode.com/settings/developer",
        tags=["developer", "blog"],
    ),
    HighDASite(
        name="Diigo",
        url="https://www.diigo.com",
        da=87,
        submission_url="https://www.diigo.com/post",
        auth_type="browser",
        platform_key="",
        education_friendly=True,
        notes="DA 87. Social bookmarking + blog posts. Free account.",
        tags=["bookmark", "education"],
    ),
    HighDASite(
        name="HubPages",
        url="https://hubpages.com",
        da=80,
        submission_url="https://hubpages.com/create",
        auth_type="browser",
        platform_key="",
        education_friendly=True,
        notes="DA 80. Article publishing platform. Good for education how-to articles.",
        tags=["article", "education"],
    ),
    HighDASite(
        name="EzineArticles",
        url="https://ezinearticles.com",
        da=79,
        submission_url="https://ezinearticles.com/members/",
        auth_type="browser",
        platform_key="",
        education_friendly=True,
        notes="DA 79. Classic article directory. Education category available.",
        tags=["article-directory", "education"],
    ),
    HighDASite(
        name="Mix.com",
        url="https://mix.com",
        da=75,
        submission_url="https://mix.com/submit",
        auth_type="browser",
        platform_key="",
        education_friendly=True,
        notes="DA 75. Social bookmarking. Submit blog URLs for traffic.",
        tags=["bookmark", "social"],
    ),
    HighDASite(
        name="Pearltrees",
        url="https://www.pearltrees.com",
        da=78,
        submission_url="https://www.pearltrees.com",
        auth_type="browser",
        platform_key="",
        education_friendly=True,
        notes="DA 78. Visual bookmarking. Add scotle.org articles to education trees.",
        tags=["bookmark", "education"],
    ),
    HighDASite(
        name="Notion.site",
        url="https://www.notion.so",
        da=90,
        submission_url="https://www.notion.so/new",
        auth_type="api_key",
        platform_key="",
        education_friendly=True,
        notes="DA 90. Public Notion pages indexed by Google. Notion API: developers.notion.com",
        tags=["productivity", "education", "high-da"],
    ),
    HighDASite(
        name="Vocal.media",
        url="https://vocal.media",
        da=77,
        submission_url="https://vocal.media/write",
        auth_type="browser",
        platform_key="",
        education_friendly=True,
        notes="DA 77. Article platform. Education community available. Free account.",
        tags=["article", "education"],
    ),

    # -----------------------------------------------------------------------
    # DA 60–79 — Medium Value
    # -----------------------------------------------------------------------
    HighDASite(
        name="HackMD",
        url="https://hackmd.io",
        da=77,
        submission_url="https://hackmd.io/new",
        auth_type="free",
        platform_key="hackmd",
        education_friendly=True,
        notes="DA 77. No signup needed for public notes. Already integrated + enabled.",
        tags=["paste", "integrated", "free"],
    ),
    HighDASite(
        name="Telegra.ph",
        url="https://telegra.ph",
        da=72,
        submission_url="https://telegra.ph",
        auth_type="free",
        platform_key="telegraph",
        education_friendly=True,
        notes="DA 72. No signup needed. Token auto-generated. Note: some ISPs block it.",
        tags=["paste", "integrated", "free"],
    ),
    HighDASite(
        name="Write.as",
        url="https://write.as",
        da=69,
        submission_url="https://write.as/new",
        auth_type="free",
        platform_key="writeas",
        education_friendly=True,
        notes="DA 69. No signup needed for anonymous posts. Already integrated + enabled.",
        tags=["blog", "integrated", "free"],
    ),
    HighDASite(
        name="Penzu",
        url="https://penzu.com",
        da=72,
        submission_url="https://penzu.com",
        auth_type="browser",
        platform_key="",
        education_friendly=True,
        notes="DA 72. Online journal. Free account. Public journals indexed by Google.",
        tags=["blog", "education"],
    ),
    HighDASite(
        name="Publish0x",
        url="https://www.publish0x.com",
        da=60,
        submission_url="https://www.publish0x.com/create-post",
        auth_type="browser",
        platform_key="",
        education_friendly=True,
        notes="DA 60. Crypto blogging. Posts indexed by Google. Education content accepted.",
        tags=["blog", "education"],
    ),
    HighDASite(
        name="Hive Blog",
        url="https://hive.blog",
        da=72,
        submission_url="https://hive.blog/new",
        auth_type="browser",
        platform_key="",
        education_friendly=True,
        notes="DA 72. Decentralized blogging. Permanent links. Education content accepted.",
        tags=["blog", "education"],
    ),
    HighDASite(
        name="Minds.com",
        url="https://www.minds.com",
        da=72,
        submission_url="https://www.minds.com/newsfeed/blog/new",
        auth_type="browser",
        platform_key="",
        education_friendly=True,
        notes="DA 72. Open social platform. Blog posts indexed by Google.",
        tags=["social", "blog"],
    ),
    HighDASite(
        name="Rentry.co",
        url="https://rentry.co",
        da=60,
        submission_url="https://rentry.co",
        auth_type="free",
        platform_key="rentry",
        education_friendly=True,
        notes="DA 60. No signup needed. Markdown paste. Already integrated + enabled.",
        tags=["paste", "integrated", "free"],
    ),
    HighDASite(
        name="dpaste.org",
        url="https://dpaste.org",
        da=55,
        submission_url="https://dpaste.org",
        auth_type="free",
        platform_key="dpaste",
        education_friendly=True,
        notes="DA 55. No signup needed. Already integrated + enabled.",
        tags=["paste", "integrated", "free"],
    ),
    HighDASite(
        name="paste.gg",
        url="https://paste.gg",
        da=50,
        submission_url="https://paste.gg",
        auth_type="free",
        platform_key="pastegg",
        education_friendly=True,
        notes="DA 50. No signup needed. Already integrated + enabled.",
        tags=["paste", "integrated", "free"],
    ),
    HighDASite(
        name="Folkd",
        url="https://www.folkd.com",
        da=62,
        submission_url="https://www.folkd.com/submit",
        auth_type="browser",
        platform_key="",
        education_friendly=True,
        notes="DA 62. Social bookmarking. Submit scotle.org URLs for backlinks.",
        tags=["bookmark"],
    ),
    HighDASite(
        name="ArticleBase",
        url="https://www.articlesbase.com",
        da=65,
        submission_url="https://www.articlesbase.com/add-article",
        auth_type="browser",
        platform_key="",
        education_friendly=True,
        notes="DA 65. Article directory. Education category available.",
        tags=["article-directory", "education"],
    ),
    HighDASite(
        name="ArticleBiz",
        url="https://www.articlebiz.com",
        da=55,
        submission_url="https://www.articlebiz.com/submit",
        auth_type="browser",
        platform_key="",
        education_friendly=True,
        notes="DA 55. Article directory with education niche.",
        tags=["article-directory", "education"],
    ),
    HighDASite(
        name="SooperArticles",
        url="https://www.sooperarticles.com",
        da=60,
        submission_url="https://www.sooperarticles.com/submit-articles",
        auth_type="browser",
        platform_key="",
        education_friendly=True,
        notes="DA 60. Article directory. Education & career section.",
        tags=["article-directory", "education"],
    ),
    HighDASite(
        name="Zupyak",
        url="https://www.zupyak.com",
        da=55,
        submission_url="https://www.zupyak.com/create",
        auth_type="browser",
        platform_key="",
        education_friendly=True,
        notes="DA 55. Free article publishing. SEO-optimized. Good for local India content.",
        tags=["article", "education", "india"],
    ),
    HighDASite(
        name="Newsbreak",
        url="https://www.newsbreak.com",
        da=78,
        submission_url="https://creators.newsbreak.com",
        auth_type="browser",
        platform_key="",
        education_friendly=True,
        notes="DA 78. News + blog platform. Local India education content does well.",
        tags=["news", "education", "india"],
    ),
    HighDASite(
        name="Speakol",
        url="https://www.speakol.com",
        da=50,
        submission_url="https://www.speakol.com",
        auth_type="browser",
        platform_key="",
        education_friendly=True,
        notes="DA 50. South Asian content platform. India-focused.",
        tags=["article", "india"],
    ),

    # -----------------------------------------------------------------------
    # Education-Specific Sites
    # -----------------------------------------------------------------------
    HighDASite(
        name="Edutopia (Guest Posts)",
        url="https://www.edutopia.org",
        da=80,
        submission_url="https://www.edutopia.org/contact",
        auth_type="browser",
        platform_key="",
        education_friendly=True,
        notes="DA 80. Top education blog. Accepts guest posts. Highly relevant for school content.",
        tags=["education", "guest-post", "high-da"],
    ),
    HighDASite(
        name="TeachThought",
        url="https://www.teachthought.com",
        da=70,
        submission_url="https://www.teachthought.com/write-for-us",
        auth_type="browser",
        platform_key="",
        education_friendly=True,
        notes="DA 70. Education blog. Write for us page. School content welcome.",
        tags=["education", "guest-post"],
    ),
    HighDASite(
        name="eLearning Industry",
        url="https://elearningindustry.com",
        da=77,
        submission_url="https://elearningindustry.com/authors",
        auth_type="browser",
        platform_key="",
        education_friendly=True,
        notes="DA 77. eLearning-focused. Strong Google indexing. Education articles.",
        tags=["education", "guest-post"],
    ),
    HighDASite(
        name="Jagranjosh",
        url="https://www.jagranjosh.com",
        da=72,
        submission_url="https://www.jagranjosh.com/contact",
        auth_type="browser",
        platform_key="",
        education_friendly=True,
        notes="DA 72. India's top education website. JEE/NEET/CBSE content. India-focused.",
        tags=["education", "india", "guest-post"],
    ),
    HighDASite(
        name="AglaSem",
        url="https://aglasem.com",
        da=60,
        submission_url="https://aglasem.com/contact",
        auth_type="browser",
        platform_key="",
        education_friendly=True,
        notes="DA 60. India education portal covering CBSE, JEE, NEET. Highly relevant.",
        tags=["education", "india", "cbse", "jee", "neet"],
    ),
    HighDASite(
        name="Shiksha.com",
        url="https://www.shiksha.com",
        da=68,
        submission_url="https://www.shiksha.com/contact",
        auth_type="browser",
        platform_key="",
        education_friendly=True,
        notes="DA 68. India's leading school/college listing. Highly relevant for scotle.org.",
        tags=["education", "india", "school", "jaipur"],
    ),
    HighDASite(
        name="CollegeDunia",
        url="https://collegedunia.com",
        da=65,
        submission_url="https://collegedunia.com/contact",
        auth_type="browser",
        platform_key="",
        education_friendly=True,
        notes="DA 65. India college/school listings. Relevant for Jaipur school content.",
        tags=["education", "india", "school", "jaipur"],
    ),

    # -----------------------------------------------------------------------
    # Google Properties (very high DA)
    # -----------------------------------------------------------------------
    HighDASite(
        name="Google Sites",
        url="https://sites.google.com",
        da=98,
        submission_url="https://sites.google.com/create",
        auth_type="browser",
        platform_key="",
        education_friendly=True,
        notes="DA 98. Free Google Sites pages are indexed fast. Use for dedicated scotle.org content pages.",
        tags=["blog", "education", "high-da", "google"],
    ),
    HighDASite(
        name="Google Docs (Public)",
        url="https://docs.google.com",
        da=98,
        submission_url="https://docs.google.com/document/u/0/create",
        auth_type="browser",
        platform_key="",
        education_friendly=True,
        notes="DA 98. Public Google Docs get indexed. Add school content with backlink.",
        tags=["blog", "education", "high-da", "google"],
    ),
    HighDASite(
        name="Blogger (Existing Blog)",
        url="https://scotle.blogspot.com",
        da=97,
        submission_url="https://www.blogger.com/blog/post/create",
        auth_type="api_key",
        platform_key="blogger",
        education_friendly=True,
        notes="DA 97. Already integrated and enabled with blog ID + API key in blog_config.py",
        tags=["blog", "integrated", "high-da", "google"],
    ),
]


# ---------------------------------------------------------------------------
# Query / filter functions
# ---------------------------------------------------------------------------

def get_all_sites() -> List[HighDASite]:
    """Return all sites."""
    return sorted(SITES, key=lambda s: s.da, reverse=True)


def get_sites_by_da(min_da: int = 0, max_da: int = 100) -> List[HighDASite]:
    """Filter sites by DA range."""
    return sorted(
        [s for s in SITES if min_da <= s.da <= max_da],
        key=lambda s: s.da,
        reverse=True,
    )


def get_sites_by_auth(auth_type: str) -> List[HighDASite]:
    """Filter by auth type: free | api_key | oauth | browser | premium"""
    return [s for s in SITES if s.auth_type == auth_type]


def get_education_sites(min_da: int = 0) -> List[HighDASite]:
    """Return education-friendly sites above a minimum DA."""
    return sorted(
        [s for s in SITES if s.education_friendly and s.da >= min_da],
        key=lambda s: s.da,
        reverse=True,
    )


def get_integrated_sites() -> List[HighDASite]:
    """Return sites already integrated in blog_config.py."""
    return [s for s in SITES if s.platform_key]


def get_free_sites(min_da: int = 0) -> List[HighDASite]:
    """Return sites requiring no account or signup."""
    return sorted(
        [s for s in SITES if s.auth_type == "free" and s.da >= min_da],
        key=lambda s: s.da,
        reverse=True,
    )


def get_stats() -> dict:
    """Return summary statistics about the database."""
    all_sites = get_all_sites()
    return {
        "total_sites": len(all_sites),
        "avg_da": round(sum(s.da for s in all_sites) / len(all_sites), 1),
        "max_da": max(s.da for s in all_sites),
        "min_da": min(s.da for s in all_sites),
        "da_90_plus": len([s for s in all_sites if s.da >= 90]),
        "da_80_plus": len([s for s in all_sites if s.da >= 80]),
        "education_friendly": len([s for s in all_sites if s.education_friendly]),
        "free_no_signup": len([s for s in all_sites if s.auth_type == "free"]),
        "integrated": len([s for s in all_sites if s.platform_key]),
        "api_key_needed": len([s for s in all_sites if s.auth_type == "api_key"]),
        "browser_only": len([s for s in all_sites if s.auth_type == "browser"]),
    }


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

def export_sites_csv(output_path: str, sites: List[HighDASite] = None) -> str:
    """
    Export sites to CSV (Google Sheets-compatible).
    Returns the path written.
    """
    if sites is None:
        sites = get_all_sites()

    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)

    headers = [
        "Rank", "Site Name", "URL", "DA Score", "Submission URL",
        "Auth Type", "Platform Key", "Education Friendly", "Notes", "Tags",
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for i, site in enumerate(sites, 1):
            writer.writerow({
                "Rank": i,
                "Site Name": site.name,
                "URL": site.url,
                "DA Score": site.da,
                "Submission URL": site.submission_url,
                "Auth Type": site.auth_type,
                "Platform Key": site.platform_key,
                "Education Friendly": "Yes" if site.education_friendly else "No",
                "Notes": site.notes,
                "Tags": ", ".join(site.tags),
            })

    return output_path


def print_table(sites: List[HighDASite] = None):
    """Print a formatted table of sites."""
    if sites is None:
        sites = get_all_sites()

    print(f"\n{'#':<4} {'Site Name':<30} {'DA':>4}  {'Auth':<10} {'Edu':>4}  {'Notes'}")
    print("-" * 100)
    for i, s in enumerate(sites, 1):
        edu = "Yes" if s.education_friendly else "No"
        integrated = " [INTEGRATED]" if s.platform_key else ""
        note = s.notes[:55].encode("ascii", "replace").decode("ascii")
        print(f"{i:<4} {s.name:<30} {s.da:>4}  {s.auth_type:<10} {edu:>4}  {note}{integrated}")
    print(f"\nTotal: {len(sites)} sites")


if __name__ == "__main__":
    stats = get_stats()
    print("\n=== HIGH-DA SITES DATABASE ===")
    print(f"Total sites: {stats['total_sites']}")
    print(f"Average DA:  {stats['avg_da']}")
    print(f"DA 90+:      {stats['da_90_plus']} sites")
    print(f"DA 80+:      {stats['da_80_plus']} sites")
    print(f"Education:   {stats['education_friendly']} sites")
    print(f"Free/no-signup: {stats['free_no_signup']} sites")
    print(f"Integrated:  {stats['integrated']} sites")
    print()
    print_table()
