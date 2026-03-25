"""
blog_tracker.py
===============
Tracks all published blog posts in CSV and generates Excel reports.
"""

import os
import logging
import platform
import subprocess
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)

TRACKER_HEADERS = [
    "Post ID",
    "Platform",
    "Title",
    "Published URL",
    "Target URL",
    "Anchor Text",
    "Tags",
    "Word Count",
    "Status",
    "Error",
    "Date Published",
    "verified",
    "ping_result",
]


def log_post(result: dict, filepath: str):
    """Append a single post result to the tracking CSV."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    record = {
        "Post ID": result.get("post_id", ""),
        "Platform": result.get("platform", ""),
        "Title": result.get("title", ""),
        "Published URL": result.get("url", ""),
        "Target URL": result.get("target_url", ""),
        "Anchor Text": result.get("anchor_text", ""),
        "Tags": ", ".join(result.get("tags", [])),
        "Word Count": result.get("word_count", 0),
        "Status": result.get("status", "unknown"),
        "Error": result.get("error", ""),
        "Date Published": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "verified": result.get("verified", ""),
        "ping_result": result.get("ping_result", ""),
    }

    df_new = pd.DataFrame([record])

    if os.path.exists(filepath):
        try:
            df_existing = pd.read_csv(filepath)
            df = pd.concat([df_existing, df_new], ignore_index=True)
        except Exception:
            df = df_new
    else:
        df = df_new

    df.to_csv(filepath, index=False)
    logger.info(f"Post logged: {record['Platform']} - {record['Status']}")


def update_post_verification(filepath: str, published_url: str, verified: bool, ping_result: str) -> None:
    """Update the verified and ping_result columns for a specific post URL."""
    if not published_url or not os.path.exists(filepath):
        return
    try:
        df = pd.read_csv(filepath)
        mask = df["Published URL"] == published_url
        if mask.any():
            df.loc[mask, "verified"] = "true" if verified else "false"
            df.loc[mask, "ping_result"] = ping_result
            df.to_csv(filepath, index=False)
    except Exception as e:
        logger.warning(f"Could not update verification for {published_url}: {e}")


def get_published_posts(filepath: str) -> pd.DataFrame:
    """Read the tracking CSV and return as DataFrame."""
    if not os.path.exists(filepath):
        return pd.DataFrame(columns=TRACKER_HEADERS)
    try:
        return pd.read_csv(filepath)
    except Exception:
        return pd.DataFrame(columns=TRACKER_HEADERS)


def get_used_topics(filepath: str) -> list:
    """Return all titles already used (to avoid duplicates)."""
    df = get_published_posts(filepath)
    if "Title" in df.columns:
        return df["Title"].dropna().tolist()
    return []


def get_post_count_by_platform(filepath: str) -> dict:
    """Return post counts grouped by platform."""
    df = get_published_posts(filepath)
    if df.empty:
        return {}
    return df["Platform"].value_counts().to_dict()


def get_today_post_count(filepath: str, platform: str = None) -> int:
    """Count posts made today, optionally filtered by platform."""
    df = get_published_posts(filepath)
    if df.empty:
        return 0

    today = datetime.now().strftime("%Y-%m-%d")
    df["_date"] = df["Date Published"].astype(str).str[:10]
    today_df = df[df["_date"] == today]

    if platform:
        today_df = today_df[today_df["Platform"].str.lower() == platform.lower()]

    return len(today_df)


def is_duplicate_post(title: str, platform: str, filepath: str) -> bool:
    """Check if this title was already posted to this platform."""
    df = get_published_posts(filepath)
    if df.empty:
        return False
    matches = df[
        (df["Title"].str.lower() == title.lower()) &
        (df["Platform"].str.lower() == platform.lower())
    ]
    return len(matches) > 0


def generate_report(filepath: str, output_xlsx: str):
    """Generate a formatted Excel report from the post log."""
    df = get_published_posts(filepath)
    if df.empty:
        logger.warning("No posts to report")
        return

    os.makedirs(os.path.dirname(output_xlsx), exist_ok=True)

    with pd.ExcelWriter(output_xlsx, engine="openpyxl") as writer:
        # Summary sheet
        summary_data = {
            "Metric": [
                "Total Posts",
                "Successful Posts",
                "Failed Posts",
                "Platforms Used",
                "Date Range",
            ],
            "Value": [
                len(df),
                len(df[df["Status"] == "published"]),
                len(df[df["Status"] == "failed"]),
                df["Platform"].nunique(),
                f"{df['Date Published'].min()} to {df['Date Published'].max()}",
            ],
        }
        pd.DataFrame(summary_data).to_excel(writer, sheet_name="Summary", index=False)

        # All posts sheet
        df.to_excel(writer, sheet_name="All Posts", index=False)

        # Per-platform sheets
        for platform in df["Platform"].unique():
            platform_df = df[df["Platform"] == platform]
            sheet_name = platform[:31]  # Excel limit
            platform_df.to_excel(writer, sheet_name=sheet_name, index=False)

        # Failed posts
        failed = df[df["Status"] == "failed"]
        if not failed.empty:
            failed.to_excel(writer, sheet_name="Failed Posts", index=False)

    logger.info(f"Report saved: {output_xlsx} ({len(df)} posts)")


def open_file(filepath: str):
    """Open file with OS default application."""
    filepath = os.path.abspath(filepath)
    if not os.path.exists(filepath):
        return
    try:
        if platform.system() == "Windows":
            os.startfile(filepath)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", filepath])
        else:
            subprocess.Popen(["xdg-open", filepath])
    except Exception as e:
        logger.warning(f"Could not auto-open: {e}")
