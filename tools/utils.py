"""
utils.py
========
Utility functions for data cleaning, normalization,
deduplication, and filtering of business records.
"""

import re
import os
import sys
import logging
import subprocess
import platform
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)


# ===========================================================
# TEXT CLEANING
# ===========================================================

def clean_text(text: str) -> str:
    """
    Remove extra whitespace, newlines, and non-ASCII characters.

    Example:
        "  Joe's  Pizza\n " -> "Joe's Pizza"
    """
    if not text:
        return ""
    # Collapse multiple spaces/newlines into single space
    text = re.sub(r'\s+', ' ', str(text)).strip()
    # Remove non-printable characters
    text = re.sub(r'[^\x20-\x7E\u0900-\u097F]', '', text)
    return text.strip()


# ===========================================================
# PHONE NUMBER NORMALIZATION
# ===========================================================

def normalize_phone(phone: str) -> str:
    """
    Normalize phone numbers to a standard format.
    Handles Indian mobile and landline numbers.

    Examples:
        "022-12345678"    -> "+9122-12345678"  (landline)
        "9876543210"      -> "+919876543210"   (mobile)
        "+91 98765 43210" -> "+919876543210"   (already formatted)
    """
    if not phone:
        return ""

    phone = str(phone).strip()

    # Remove all characters except digits and +
    cleaned = re.sub(r'[^\d+]', '', phone)

    if not cleaned:
        return ""

    # Standardize Indian numbers
    if cleaned.startswith('+91') and len(cleaned) >= 12:
        return cleaned  # Already good

    if cleaned.startswith('91') and len(cleaned) == 12:
        return '+' + cleaned  # Add +

    if cleaned.startswith('0') and len(cleaned) >= 10:
        return '+91' + cleaned[1:]  # Replace leading 0 with +91

    if len(cleaned) == 10 and cleaned[0] in '6789':
        return '+91' + cleaned  # Add country code for Indian mobile

    # Return as-is if we can't determine format but it's long enough
    return cleaned if len(cleaned) >= 8 else ""


# ===========================================================
# RATING PARSING
# ===========================================================

def parse_rating(rating_str) -> float:
    """
    Extract numeric rating from various string formats.

    Examples:
        "4.5 stars"  -> 4.5
        "Rated: 3.8" -> 3.8
        "4"          -> 4.0
        ""           -> 0.0
    """
    if not rating_str:
        return 0.0
    try:
        match = re.search(r'(\d+\.?\d*)', str(rating_str))
        if match:
            value = float(match.group(1))
            # Justdial uses 1-5 scale; validate range
            if 0.0 <= value <= 5.0:
                return value
    except (ValueError, TypeError):
        pass
    return 0.0


# ===========================================================
# DEDUPLICATION
# ===========================================================

def remove_duplicates(records: list) -> list:
    """
    Remove duplicate business entries.
    Duplicates are detected based on: Name + Phone + first 50 chars of Address.

    Args:
        records: List of business record dicts
    Returns:
        Deduplicated list
    """
    if not records:
        return []

    df = pd.DataFrame(records)

    # Build a composite deduplication key
    name_col = df.get('Name', pd.Series([''] * len(df))).fillna('').str.lower().str.strip()
    phone_col = df.get('Phone', pd.Series([''] * len(df))).fillna('').str.strip()
    addr_col = df.get('Address', pd.Series([''] * len(df))).fillna('').str.lower().str.strip().str[:50]

    df['_dedup_key'] = name_col + '|' + phone_col + '|' + addr_col

    before = len(df)
    df = df.drop_duplicates(subset=['_dedup_key'], keep='first')
    df = df.drop(columns=['_dedup_key'])
    after = len(df)

    if before != after:
        logger.info(f"Removed {before - after} duplicate records ({before} -> {after})")

    return df.to_dict('records')


# ===========================================================
# QUALITY FILTER
# ===========================================================

def filter_high_quality_leads(records: list, min_rating: float = 4.0, require_phone: bool = True) -> list:
    """
    Filter leads to only keep high-quality entries.

    Criteria:
        - Must have a phone number (if require_phone=True)
        - Rating must be >= min_rating (if rating is present)

    Note: Records with NO rating are still kept (not penalized for missing data).

    Args:
        records: List of business record dicts
        min_rating: Minimum acceptable rating
        require_phone: Whether phone number is mandatory
    Returns:
        Filtered list of high-quality leads
    """
    filtered = []

    for record in records:
        phone = record.get('Phone', '').strip()
        rating = parse_rating(record.get('Rating', ''))

        # Skip if phone is required but missing
        if require_phone and not phone:
            continue

        # Skip if rating exists AND it's below threshold
        # (records with no rating are allowed through)
        if rating > 0 and rating < min_rating:
            continue

        filtered.append(record)

    logger.info(f"Quality filter: {len(records)} -> {len(filtered)} records kept")
    return filtered


# ===========================================================
# METADATA INJECTION
# ===========================================================

def add_metadata(records: list, city: str, category: str, source: str) -> list:
    """
    Add city, category, source, and timestamp to every record.
    This is useful for tracking where and when the data came from.
    """
    date_scraped = datetime.now().strftime("%Y-%m-%d %H:%M")
    for record in records:
        record['City'] = city.strip().title()
        record['Category'] = category.strip().title()
        record['Source'] = source
        record['Date Scraped'] = date_scraped
    return records


# ===========================================================
# CSV BACKUP
# ===========================================================

def save_backup_csv(records: list, filepath: str):
    """
    Save records to a local CSV file as backup.
    If file already exists, new records are appended (no duplicates).

    Args:
        records: List of business record dicts
        filepath: Path to save the CSV
    """
    if not records:
        logger.warning("No records to save to CSV")
        return

    # Make sure the output directory exists
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    new_df = pd.DataFrame(records)

    # If file already exists, append without creating duplicates
    if os.path.exists(filepath):
        try:
            existing_df = pd.read_csv(filepath)
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
            # Drop exact duplicate rows
            combined_df = combined_df.drop_duplicates()
            combined_df.to_csv(filepath, index=False)
            logger.info(f"Backup updated: {filepath} ({len(combined_df)} total records)")
        except Exception as e:
            logger.error(f"Failed to append to existing CSV: {e}. Overwriting.")
            new_df.to_csv(filepath, index=False)
    else:
        new_df.to_csv(filepath, index=False)
        logger.info(f"Backup created: {filepath} ({len(new_df)} records)")


# ===========================================================
# EXCEL EXPORT
# ===========================================================

def save_excel(records: list, filepath: str):
    """
    Save records to an Excel .xlsx file.
    If file already exists, new records are appended (no duplicates).

    Args:
        records: List of business record dicts
        filepath: Path to save the .xlsx file
    """
    if not records:
        logger.warning("No records to save to Excel")
        return

    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    new_df = pd.DataFrame(records)

    if os.path.exists(filepath):
        try:
            existing_df = pd.read_excel(filepath)
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
            combined_df = combined_df.drop_duplicates()
            combined_df.to_excel(filepath, index=False)
            logger.info(f"Excel updated: {filepath} ({len(combined_df)} total records)")
        except Exception as e:
            logger.error(f"Failed to append to existing Excel: {e}. Overwriting.")
            new_df.to_excel(filepath, index=False)
    else:
        new_df.to_excel(filepath, index=False)
        logger.info(f"Excel created: {filepath} ({len(new_df)} records)")


# ===========================================================
# OPEN FILE IN DEFAULT APPLICATION
# ===========================================================

def open_file(filepath: str):
    """
    Open a file using the OS default application.
    Works on Windows, macOS, and Linux.
    """
    filepath = os.path.abspath(filepath)
    if not os.path.exists(filepath):
        logger.warning(f"Cannot open file (not found): {filepath}")
        return

    logger.info(f"Opening: {filepath}")
    try:
        if platform.system() == 'Windows':
            os.startfile(filepath)
        elif platform.system() == 'Darwin':
            subprocess.Popen(['open', filepath])
        else:
            subprocess.Popen(['xdg-open', filepath])
    except Exception as e:
        logger.warning(f"Could not auto-open file: {e}")
        logger.info(f"Open manually: {filepath}")
