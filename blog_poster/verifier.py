"""
verifier.py
===========
Verifies that published URLs are live and contain a backlink to scotle.org.

Functions:
    verify_post(url) -> bool
    log_failed_verification(post_data, filepath) -> None
"""

import os
import logging
import requests
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)

FAILED_HEADERS = [
    "Platform",
    "Title",
    "Published URL",
    "Target URL",
    "Anchor Text",
    "Status",
    "Error",
    "Date Published",
    "Failure Reason",
]


def verify_post(url: str, timeout: int = 25) -> bool:
    """
    GET the URL and confirm it returns a 2xx status with 'scotle.org' or 'scotle'
    in the body. Retries once on timeout. Returns False on any error.
    """
    if not url:
        return False

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,*/*;q=0.9",
        "Accept-Language": "en-US,en;q=0.9",
    }

    for attempt in range(2):
        try:
            resp = requests.get(
                url,
                timeout=timeout,
                allow_redirects=True,
                headers=HEADERS,
            )
            if 200 <= resp.status_code < 300:
                text_lower = resp.text.lower()
                # Check for scotle.org URL or brand name in any format
                if "scotle.org" in text_lower or "scotle high school" in text_lower:
                    return True
                # Fallback: check for just "scotle" (catches plain-text posts)
                if "scotle" in text_lower:
                    return True
            return False
        except requests.exceptions.Timeout:
            if attempt == 0:
                logger.warning(f"Verification timeout for {url}, retrying...")
                continue
            logger.warning(f"Verification timed out after retry: {url}")
            return False
        except Exception as e:
            logger.warning(f"Verification failed for {url}: {e}")
            return False
    return False


def log_failed_verification(post_data: dict, filepath: str) -> None:
    """
    Append a failed-verification row to data/failed_posts.csv.
    Creates the file with headers if it doesn't exist.
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    reason = "scotle.org not found in page content or HTTP error"
    record = {
        "Platform": post_data.get("platform", ""),
        "Title": post_data.get("title", ""),
        "Published URL": post_data.get("url", ""),
        "Target URL": post_data.get("target_url", ""),
        "Anchor Text": post_data.get("anchor_text", ""),
        "Status": post_data.get("status", ""),
        "Error": post_data.get("error", ""),
        "Date Published": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "Failure Reason": reason,
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
    logger.info(f"Failed verification logged: {record['Published URL']}")
