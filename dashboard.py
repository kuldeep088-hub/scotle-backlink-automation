"""
Scotle.org Backlink CRM Dashboard
==================================
Run:  python dashboard.py
Open: http://localhost:5000

Routes:
  /              - Full CRM (multi-tab)
  /api/stats     - JSON summary stats
  /api/posts     - JSON all posts (filterable)
  /api/check     - POST {"url": "..."} -> live URL check
  /api/check_all - GET -> check all live URLs (slow)
  /export/csv    - Download all posts as CSV
"""

import os
import csv
import io
import json
import time
import threading
import requests
from datetime import datetime, timedelta
from flask import Flask, render_template_string, jsonify, request, Response

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
POSTS_LOG    = os.path.join(BASE_DIR, "blog_poster", "output", "posts_log.csv")
RECENT_CSV   = os.path.join(BASE_DIR, "data", "backlinks_recent30.csv")
FAILED_CSV   = os.path.join(BASE_DIR, "data", "failed_posts.csv")
DATA_DIR     = os.path.join(BASE_DIR, "data")

# Platform DA scores lookup
PLATFORM_DA = {
    "blogger":   100,
    "tumblr":     98,
    "hashnode":   92,
    "devto":      90,
    "dev.to":     90,
    "writeas":    69,
    "write.as":   69,
    "hackmd":     65,
    "dpaste":     55,
    "bytebin":    50,
    "substack":   89,
    "medium":     95,
    "livejournal":93,
    "hackmd.io":  65,
}

# In-memory cache for live check results {url: {status, verified, checked_at, response_ms}}
_check_cache = {}
_check_lock  = threading.Lock()


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_posts():
    """Load all posts from posts_log.csv. Returns list of dicts."""
    posts = []
    if not os.path.exists(POSTS_LOG):
        return posts
    try:
        with open(POSTS_LOG, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                posts.append(dict(row))
    except Exception:
        pass
    return posts


def load_recent():
    """Load backlinks_recent30.csv (different schema). Returns list of dicts."""
    rows = []
    if not os.path.exists(RECENT_CSV):
        return rows
    try:
        with open(RECENT_CSV, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(dict(row))
    except Exception:
        pass
    return rows


def get_da(platform_name: str) -> int:
    key = platform_name.lower().strip()
    return PLATFORM_DA.get(key, 0)


# ---------------------------------------------------------------------------
# Stats computation
# ---------------------------------------------------------------------------

def compute_stats(posts):
    total     = len(posts)
    published = [p for p in posts if p.get("Status", "").lower() == "published"]
    failed    = [p for p in posts if p.get("Status", "").lower() == "failed"]
    verified  = [p for p in published if str(p.get("verified", "")).lower() == "true"]
    success_rate = round(len(published) / total * 100, 1) if total else 0
    verify_rate  = round(len(verified)  / len(published) * 100, 1) if published else 0

    # Per-platform
    platform_stats = {}
    for p in posts:
        plat = p.get("Platform", "unknown").lower()
        if plat not in platform_stats:
            platform_stats[plat] = {
                "total": 0, "published": 0, "failed": 0, "verified": 0, "da": get_da(plat)
            }
        platform_stats[plat]["total"] += 1
        if p.get("Status", "").lower() == "published":
            platform_stats[plat]["published"] += 1
            if str(p.get("verified", "")).lower() == "true":
                platform_stats[plat]["verified"] += 1
        else:
            platform_stats[plat]["failed"] += 1

    # Sort platforms by DA desc
    platform_stats = dict(
        sorted(platform_stats.items(), key=lambda x: -x[1]["da"])
    )

    # Daily chart — last 14 days
    now      = datetime.now()
    week_ago = now - timedelta(days=7)
    daily    = {}
    for i in range(14):
        d = (now - timedelta(days=i)).strftime("%Y-%m-%d")
        daily[d] = {"published": 0, "failed": 0}
    for p in posts:
        try:
            dt = datetime.strptime(p.get("Date Published", ""), "%Y-%m-%d %H:%M")
            d  = dt.strftime("%Y-%m-%d")
            if d in daily:
                if p.get("Status", "").lower() == "published":
                    daily[d]["published"] += 1
                else:
                    daily[d]["failed"] += 1
        except Exception:
            pass
    daily_sorted = sorted(daily.items())

    # Last 7 days count
    recent_7d = sum(
        1 for p in posts
        if _parse_dt(p.get("Date Published", "")) and
           _parse_dt(p.get("Date Published", "")) >= week_ago
    )

    # Top anchors
    anchors = {}
    for p in published:
        anchor = p.get("Anchor Text", "").strip()
        if anchor:
            anchors[anchor] = anchors.get(anchor, 0) + 1
    top_anchors = sorted(anchors.items(), key=lambda x: -x[1])[:10]

    # Live links list (published with URL, sorted newest first)
    live_links = [
        {
            "url":      p.get("Published URL", ""),
            "title":    p.get("Title", ""),
            "platform": p.get("Platform", ""),
            "date":     p.get("Date Published", ""),
            "anchor":   p.get("Anchor Text", ""),
            "verified": p.get("verified", ""),
            "da":       get_da(p.get("Platform", "")),
        }
        for p in reversed(posts)
        if p.get("Status", "").lower() == "published" and p.get("Published URL", "")
    ]

    return {
        "total":          total,
        "published":      len(published),
        "failed":         len(failed),
        "verified":       len(verified),
        "success_rate":   success_rate,
        "verify_rate":    verify_rate,
        "recent_7d":      recent_7d,
        "platform_stats": platform_stats,
        "daily_chart":    daily_sorted,
        "top_anchors":    top_anchors,
        "live_links":     live_links,
        "recent_posts":   list(reversed(posts))[:30],
    }


def _parse_dt(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d %H:%M")
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Live URL checker
# ---------------------------------------------------------------------------

def check_url_live(url: str) -> dict:
    """HTTP GET the URL, check status + scotle.org in body."""
    if not url or not url.startswith("http"):
        return {"status": "invalid", "verified": False, "response_ms": 0, "http_code": 0}

    with _check_lock:
        cached = _check_cache.get(url)
    if cached and (time.time() - cached.get("ts", 0)) < 3600:
        return cached

    start = time.time()
    try:
        resp = requests.get(url, timeout=10, allow_redirects=True,
                            headers={"User-Agent": "Mozilla/5.0 Backlink-CRM/1.0"})
        ms   = int((time.time() - start) * 1000)
        body = resp.text.lower()
        live = resp.status_code < 400
        verified = live and "scotle.org" in body
        result = {
            "status":      "live" if live else "dead",
            "verified":    verified,
            "http_code":   resp.status_code,
            "response_ms": ms,
            "ts":          time.time(),
        }
    except requests.exceptions.ConnectionError:
        result = {"status": "dead",    "verified": False, "http_code": 0,   "response_ms": 0, "ts": time.time()}
    except requests.exceptions.Timeout:
        result = {"status": "timeout", "verified": False, "http_code": 0,   "response_ms": 10000, "ts": time.time()}
    except Exception as e:
        result = {"status": "error",   "verified": False, "http_code": 0,   "response_ms": 0, "ts": time.time(), "error": str(e)}

    with _check_lock:
        _check_cache[url] = result
    return result


# ---------------------------------------------------------------------------
# HTML Template
# ---------------------------------------------------------------------------

TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Scotle.org Backlink CRM</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Segoe UI', Arial, sans-serif; background: #0a0c12; color: #e2e8f0; min-height: 100vh; }

/* ---- Header ---- */
.header {
  background: linear-gradient(135deg, #111827 0%, #0d1b2a 100%);
  padding: 18px 32px;
  border-bottom: 1px solid #1f2d3d;
  display: flex; align-items: center; justify-content: space-between;
}
.header-brand { display: flex; align-items: center; gap: 14px; }
.header-logo {
  width: 38px; height: 38px; border-radius: 10px;
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  display: flex; align-items: center; justify-content: center;
  font-size: 1.1rem; font-weight: 700; color: #fff;
}
.header h1 { font-size: 1.25rem; font-weight: 700; color: #f1f5f9; }
.header .tagline { font-size: 0.75rem; color: #64748b; margin-top: 1px; }
.header-meta { text-align: right; font-size: 0.75rem; color: #475569; line-height: 1.6; }
.header-meta strong { color: #94a3b8; }

/* ---- Nav Tabs ---- */
.nav-bar {
  background: #0f1623;
  border-bottom: 1px solid #1e2d3d;
  padding: 0 32px;
  display: flex; gap: 0;
}
.nav-tab {
  padding: 13px 20px;
  font-size: 0.82rem; font-weight: 500;
  color: #64748b;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all 0.15s;
  user-select: none;
}
.nav-tab:hover { color: #94a3b8; }
.nav-tab.active { color: #60a5fa; border-bottom-color: #3b82f6; }

/* ---- Layout ---- */
.container { max-width: 1440px; margin: 0 auto; padding: 24px 28px; }
.tab-content { display: none; }
.tab-content.active { display: block; }

/* ---- KPI Cards ---- */
.kpi-row { display: grid; grid-template-columns: repeat(6, 1fr); gap: 14px; margin-bottom: 22px; }
.kpi {
  background: #111827; border: 1px solid #1e2d3d;
  border-radius: 12px; padding: 18px 16px;
  position: relative; overflow: hidden;
}
.kpi::after {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
}
.kpi.blue::after   { background: #3b82f6; }
.kpi.green::after  { background: #10b981; }
.kpi.red::after    { background: #ef4444; }
.kpi.purple::after { background: #8b5cf6; }
.kpi.cyan::after   { background: #06b6d4; }
.kpi.orange::after { background: #f59e0b; }
.kpi-label  { font-size: 0.68rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 8px; }
.kpi-value  { font-size: 1.9rem; font-weight: 700; line-height: 1; }
.kpi.blue .kpi-value   { color: #60a5fa; }
.kpi.green .kpi-value  { color: #34d399; }
.kpi.red .kpi-value    { color: #f87171; }
.kpi.purple .kpi-value { color: #a78bfa; }
.kpi.cyan .kpi-value   { color: #22d3ee; }
.kpi.orange .kpi-value { color: #fbbf24; }
.kpi-sub { font-size: 0.7rem; color: #374151; margin-top: 5px; }

/* ---- Card ---- */
.card {
  background: #111827; border: 1px solid #1e2d3d;
  border-radius: 12px; padding: 20px;
  margin-bottom: 16px;
}
.card-title {
  font-size: 0.78rem; font-weight: 600; color: #94a3b8;
  text-transform: uppercase; letter-spacing: 0.06em;
  margin-bottom: 16px; display: flex; align-items: center; gap: 8px;
}
.dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.dot-blue   { background: #3b82f6; }
.dot-green  { background: #10b981; }
.dot-red    { background: #ef4444; }
.dot-purple { background: #8b5cf6; }
.dot-orange { background: #f59e0b; }
.dot-cyan   { background: #06b6d4; }

/* ---- Grid ---- */
.g2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; }
.g3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; margin-bottom: 16px; }
.g4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 16px; }

/* ---- Bar Chart ---- */
.bar-chart { display: flex; align-items: flex-end; gap: 3px; height: 90px; }
.bar-group  { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 2px; }
.bar-wrap   { display: flex; gap: 2px; align-items: flex-end; height: 72px; }
.bar        { min-width: 5px; border-radius: 2px 2px 0 0; }
.bar-p      { background: #10b981; }
.bar-f      { background: #ef4444; }
.bar-lbl    { font-size: 0.5rem; color: #374151; text-align: center; }
.chart-legend { display: flex; gap: 16px; margin-top: 10px; font-size: 0.72rem; }
.legend-dot { width: 8px; height: 8px; border-radius: 2px; display: inline-block; margin-right: 5px; }

/* ---- Platform Table ---- */
.plat-table { width: 100%; border-collapse: collapse; }
.plat-table th {
  text-align: left; font-size: 0.68rem; color: #64748b;
  text-transform: uppercase; letter-spacing: 0.05em;
  padding: 0 10px 10px;
}
.plat-table td { padding: 9px 10px; font-size: 0.82rem; border-top: 1px solid #1e2d3d; }
.plat-table tr:hover td { background: #161f2e; }
.da-badge {
  display: inline-block; padding: 1px 7px; border-radius: 4px;
  font-size: 0.68rem; font-weight: 700;
}
.da-high   { background: #064e3b; color: #34d399; }
.da-mid    { background: #1e3a5f; color: #60a5fa; }
.da-low    { background: #292524; color: #d97706; }
.progress-bar { height: 3px; background: #1e2d3d; border-radius: 2px; margin-top: 4px; }
.progress-fill { height: 100%; border-radius: 2px; }

/* ---- Badges ---- */
.badge { display: inline-block; padding: 2px 8px; border-radius: 9999px; font-size: 0.7rem; font-weight: 600; }
.badge-green  { background: #064e3b; color: #34d399; }
.badge-red    { background: #450a0a; color: #f87171; }
.badge-gray   { background: #1e2d3d; color: #94a3b8; }
.badge-yellow { background: #451a03; color: #fbbf24; }
.badge-blue   { background: #1e3a5f; color: #60a5fa; }
.plat-tag {
  display: inline-block; padding: 2px 8px; border-radius: 4px;
  font-size: 0.68rem; background: #1e2d3d; color: #94a3b8;
}

/* ---- Anchor Tags ---- */
.anchor-wrap { display: flex; flex-wrap: wrap; gap: 8px; }
.anchor-chip {
  background: #1e2d3d; border: 1px solid #2d4a6e;
  color: #93c5fd; padding: 4px 12px; border-radius: 9999px;
  font-size: 0.75rem; display: flex; align-items: center; gap: 6px;
}
.anchor-chip .cnt { color: #3b82f6; font-weight: 700; }

/* ---- Backlinks Table ---- */
.bl-controls {
  display: flex; gap: 12px; align-items: center; margin-bottom: 14px; flex-wrap: wrap;
}
.bl-search {
  flex: 1; min-width: 200px; max-width: 340px;
  background: #0d1421; border: 1px solid #1e2d3d;
  color: #e2e8f0; padding: 7px 12px; border-radius: 8px;
  font-size: 0.82rem; outline: none;
}
.bl-search:focus { border-color: #3b82f6; }
.bl-select {
  background: #0d1421; border: 1px solid #1e2d3d;
  color: #e2e8f0; padding: 7px 10px; border-radius: 8px;
  font-size: 0.82rem; outline: none;
}
.bl-select:focus { border-color: #3b82f6; }
.btn {
  padding: 7px 14px; border-radius: 8px; font-size: 0.78rem;
  font-weight: 500; cursor: pointer; border: 1px solid transparent;
  transition: opacity 0.15s;
}
.btn:hover { opacity: 0.85; }
.btn-primary { background: #1d4ed8; color: #fff; border-color: #2563eb; }
.btn-success { background: #065f46; color: #34d399; border-color: #059669; }
.btn-danger  { background: #450a0a; color: #f87171; border-color: #dc2626; }
.btn-gray    { background: #1e2d3d; color: #94a3b8; border-color: #2d3748; }

.bl-count { font-size: 0.75rem; color: #64748b; margin-left: auto; }

.data-table { width: 100%; border-collapse: collapse; font-size: 0.8rem; }
.data-table th {
  text-align: left; font-size: 0.68rem; color: #64748b;
  text-transform: uppercase; letter-spacing: 0.05em;
  padding: 0 10px 10px; cursor: pointer; user-select: none;
  white-space: nowrap;
}
.data-table th:hover { color: #94a3b8; }
.data-table th .sort-arrow { font-size: 0.6rem; margin-left: 4px; }
.data-table td { padding: 8px 10px; border-top: 1px solid #1e2d3d; vertical-align: middle; }
.data-table tr:hover td { background: #161f2e; }
.td-url {
  color: #60a5fa; text-decoration: none; display: block;
  max-width: 280px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.td-url:hover { color: #93c5fd; text-decoration: underline; }
.td-title {
  max-width: 260px; overflow: hidden; text-overflow: ellipsis;
  white-space: nowrap; display: block; color: #94a3b8;
}
.td-date { white-space: nowrap; color: #475569; }
.status-live   { color: #34d399; font-weight: 600; font-size: 0.72rem; }
.status-failed { color: #f87171; font-weight: 600; font-size: 0.72rem; }

/* ---- Pagination ---- */
.pagination { display: flex; gap: 6px; justify-content: center; margin-top: 16px; }
.page-btn {
  padding: 5px 10px; border-radius: 6px; font-size: 0.75rem;
  cursor: pointer; background: #1e2d3d; color: #94a3b8;
  border: 1px solid #2d3748;
}
.page-btn.active, .page-btn:hover { background: #1d4ed8; color: #fff; border-color: #3b82f6; }
.page-info { font-size: 0.75rem; color: #64748b; display: flex; align-items: center; padding: 0 8px; }

/* ---- Live Checker ---- */
.checker-box {
  background: #0d1421; border: 1px solid #1e2d3d;
  border-radius: 10px; padding: 16px; margin-bottom: 12px;
}
.checker-input-row { display: flex; gap: 10px; margin-bottom: 14px; }
.checker-input {
  flex: 1; background: #0a0c12; border: 1px solid #1e2d3d;
  color: #e2e8f0; padding: 9px 14px; border-radius: 8px;
  font-size: 0.85rem; font-family: monospace; outline: none;
}
.checker-input:focus { border-color: #3b82f6; }

.check-result {
  border-radius: 8px; padding: 14px 18px; margin-top: 10px;
  display: none; font-size: 0.85rem;
}
.check-result.live    { background: #052e16; border: 1px solid #166534; }
.check-result.dead    { background: #1c0404; border: 1px solid #7f1d1d; }
.check-result.timeout { background: #1c1204; border: 1px solid #78350f; }
.check-result.invalid { background: #1c1204; border: 1px solid #78350f; }
.check-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-top: 10px; }
.check-item label { font-size: 0.65rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; display: block; margin-bottom: 3px; }
.check-item value { font-size: 0.9rem; font-weight: 600; }

.bulk-check-wrap { margin-top: 20px; }
.bulk-progress { margin-top: 12px; }
.bulk-bar-wrap { background: #1e2d3d; border-radius: 4px; height: 6px; margin: 8px 0; overflow: hidden; }
.bulk-bar-fill { height: 100%; background: #3b82f6; border-radius: 4px; transition: width 0.3s; }
.bulk-log {
  background: #080c14; border: 1px solid #1e2d3d; border-radius: 8px;
  padding: 12px; max-height: 300px; overflow-y: auto;
  font-family: monospace; font-size: 0.75rem; color: #94a3b8;
  margin-top: 10px;
}
.log-live   { color: #34d399; }
.log-dead   { color: #f87171; }
.log-skip   { color: #64748b; }
.log-check  { color: #60a5fa; }

/* ---- Quick Commands ---- */
.cmd-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
.cmd-card {
  background: #0d1421; border: 1px solid #1e2d3d;
  border-radius: 8px; padding: 12px 14px;
}
.cmd-label { font-size: 0.68rem; color: #64748b; margin-bottom: 5px; }
.cmd-code  { font-size: 0.76rem; color: #34d399; font-family: monospace; word-break: break-all; }

/* ---- Platform Health ---- */
.platform-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 16px; }
.platform-card {
  background: #111827; border: 1px solid #1e2d3d;
  border-radius: 12px; padding: 16px;
}
.pc-name  { font-weight: 600; font-size: 0.88rem; color: #f1f5f9; margin-bottom: 6px; text-transform: capitalize; }
.pc-da    { font-size: 2rem; font-weight: 700; }
.pc-meta  { font-size: 0.7rem; color: #64748b; margin-top: 4px; }
.pc-stats { display: flex; gap: 8px; margin-top: 12px; flex-wrap: wrap; }

/* ---- Misc ---- */
.footer { text-align: center; padding: 24px; color: #1e2d3d; font-size: 0.72rem; }
.empty-state { text-align: center; color: #475569; padding: 40px; font-size: 0.85rem; }
.spinner { display: inline-block; width: 14px; height: 14px; border: 2px solid #1e2d3d; border-top-color: #3b82f6; border-radius: 50%; animation: spin 0.6s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.verified-yes { color: #34d399; }
.verified-no  { color: #64748b; }
.tag-strip { display: flex; gap: 4px; flex-wrap: wrap; }

@media (max-width: 1100px) {
  .kpi-row { grid-template-columns: repeat(3, 1fr); }
  .platform-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 700px) {
  .kpi-row { grid-template-columns: repeat(2, 1fr); }
  .g2, .g3, .g4 { grid-template-columns: 1fr; }
  .cmd-grid { grid-template-columns: 1fr; }
  .platform-grid { grid-template-columns: 1fr; }
}
</style>
</head>
<body>

<!-- Header -->
<div class="header">
  <div class="header-brand">
    <div class="header-logo">S</div>
    <div>
      <h1>Scotle.org Backlink CRM</h1>
      <div class="tagline">CBSE High School, Jaipur &mdash; Backlink Automation &amp; Monitor</div>
    </div>
  </div>
  <div class="header-meta">
    <strong>Last loaded:</strong> {{ now }}<br>
    <strong>Target:</strong> scotle.org &nbsp;|&nbsp; <strong>Goal:</strong> 50+ backlinks/week
  </div>
</div>

<!-- Nav -->
<div class="nav-bar">
  <div class="nav-tab active" onclick="switchTab('overview', this)">Overview</div>
  <div class="nav-tab" onclick="switchTab('backlinks', this)">All Backlinks ({{ stats.published }})</div>
  <div class="nav-tab" onclick="switchTab('platforms', this)">Platform Health</div>
  <div class="nav-tab" onclick="switchTab('checker', this)">Live Checker</div>
  <div class="nav-tab" onclick="switchTab('activity', this)">Activity Log</div>
</div>

<div class="container">

<!-- ================================================================ TAB: OVERVIEW -->
<div class="tab-content active" id="tab-overview">

  <!-- KPI Row -->
  <div class="kpi-row">
    <div class="kpi blue">
      <div class="kpi-label">Total Attempted</div>
      <div class="kpi-value">{{ stats.total }}</div>
      <div class="kpi-sub">All time posts</div>
    </div>
    <div class="kpi green">
      <div class="kpi-label">Live Backlinks</div>
      <div class="kpi-value">{{ stats.published }}</div>
      <div class="kpi-sub">Published successfully</div>
    </div>
    <div class="kpi red">
      <div class="kpi-label">Failed</div>
      <div class="kpi-value">{{ stats.failed }}</div>
      <div class="kpi-sub">Need attention</div>
    </div>
    <div class="kpi cyan">
      <div class="kpi-label">Verified Live</div>
      <div class="kpi-value">{{ stats.verified }}</div>
      <div class="kpi-sub">scotle.org confirmed</div>
    </div>
    <div class="kpi purple">
      <div class="kpi-label">Success Rate</div>
      <div class="kpi-value">{{ stats.success_rate }}%</div>
      <div class="kpi-sub">Published / Attempted</div>
    </div>
    <div class="kpi orange">
      <div class="kpi-label">Last 7 Days</div>
      <div class="kpi-value">{{ stats.recent_7d }}</div>
      <div class="kpi-sub">Recent posts</div>
    </div>
  </div>

  <div class="g2">
    <!-- Daily Chart -->
    <div class="card">
      <div class="card-title"><span class="dot dot-blue"></span>Posts Per Day &mdash; Last 14 Days</div>
      <div class="bar-chart" id="daily-chart">
        {% set max_v = namespace(v=1) %}
        {% for day, c in stats.daily_chart %}
          {% if (c.published + c.failed) > max_v.v %}{% set max_v.v = c.published + c.failed %}{% endif %}
        {% endfor %}
        {% for day, c in stats.daily_chart %}
        <div class="bar-group">
          <div class="bar-wrap">
            {% if c.published > 0 %}<div class="bar bar-p" style="height:{{ [c.published * 68 // max_v.v, 2]|max }}px" title="{{ c.published }} published on {{ day }}"></div>{% endif %}
            {% if c.failed   > 0 %}<div class="bar bar-f" style="height:{{ [c.failed   * 68 // max_v.v, 2]|max }}px" title="{{ c.failed }} failed on {{ day }}"></div>{% endif %}
          </div>
          <div class="bar-lbl">{{ day[5:] }}</div>
        </div>
        {% endfor %}
      </div>
      <div class="chart-legend">
        <span><span class="legend-dot" style="background:#10b981;"></span>Published</span>
        <span><span class="legend-dot" style="background:#ef4444;"></span>Failed</span>
      </div>
    </div>

    <!-- Platform Summary -->
    <div class="card">
      <div class="card-title"><span class="dot dot-green"></span>Platform Summary</div>
      <table class="plat-table">
        <thead><tr><th>Platform</th><th>DA</th><th>Live</th><th>Failed</th><th>Rate</th></tr></thead>
        <tbody>
          {% for plat, d in stats.platform_stats.items() %}
          {% set rate = (d.published / d.total * 100)|round(0)|int if d.total else 0 %}
          <tr>
            <td style="font-weight:600;text-transform:capitalize;">{{ plat }}</td>
            <td>
              <span class="da-badge {% if d.da >= 90 %}da-high{% elif d.da >= 60 %}da-mid{% else %}da-low{% endif %}">
                {% if d.da > 0 %}{{ d.da }}{% else %}?{% endif %}
              </span>
            </td>
            <td><span class="badge badge-green">{{ d.published }}</span></td>
            <td><span class="badge {% if d.failed > 0 %}badge-red{% else %}badge-gray{% endif %}">{{ d.failed }}</span></td>
            <td>
              <span style="font-size:0.73rem;color:{% if rate>=70 %}#34d399{% elif rate>=40 %}#fbbf24{% else %}#f87171{% endif %};">{{ rate }}%</span>
              <div class="progress-bar"><div class="progress-fill" style="width:{{ rate }}%;background:{% if rate>=70 %}#10b981{% elif rate>=40 %}#f59e0b{% else %}#ef4444{% endif %};"></div></div>
            </td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
  </div>

  <div class="g2">
    <!-- Top Anchors -->
    <div class="card">
      <div class="card-title"><span class="dot dot-purple"></span>Top Anchor Texts</div>
      <div class="anchor-wrap">
        {% for anchor, cnt in stats.top_anchors %}
        <div class="anchor-chip">{{ anchor }}<span class="cnt">x{{ cnt }}</span></div>
        {% endfor %}
        {% if not stats.top_anchors %}
        <p style="color:#475569;font-size:0.82rem;">No data yet.</p>
        {% endif %}
      </div>
    </div>

    <!-- Quick Commands -->
    <div class="card">
      <div class="card-title"><span class="dot dot-orange"></span>Quick Commands</div>
      <div class="cmd-grid" style="grid-template-columns:1fr 1fr;">
        {% for label, cmd in [
          ('Quick Test', 'python unified_poster.py --mode quick'),
          ('Mega Mode 56x', 'python unified_poster.py --mode mega --count 56'),
          ('Bulk Write.as', 'python unified_poster.py --mode bulk'),
          ('Validate Creds', 'python -m blog_poster.blog_poster --validate'),
          ('Force School', 'python -m blog_poster.blog_poster --niche school'),
          ('Dry Run Local', 'python -m blog_poster.local_content_pipeline --dry-run'),
        ] %}
        <div class="cmd-card">
          <div class="cmd-label">{{ label }}</div>
          <div class="cmd-code">{{ cmd }}</div>
        </div>
        {% endfor %}
      </div>
    </div>
  </div>

  <!-- Recent Live Backlinks mini preview -->
  <div class="card">
    <div class="card-title">
      <span class="dot dot-green"></span>
      Recent Live Backlinks (last 10)
      <a href="#" onclick="switchTabByName('backlinks'); return false;" style="font-size:0.72rem;color:#3b82f6;text-decoration:none;margin-left:auto;">View all →</a>
    </div>
    {% if stats.live_links %}
    <table class="data-table">
      <thead><tr><th>Platform</th><th>DA</th><th>Title</th><th>URL</th><th>Date</th><th>Verified</th></tr></thead>
      <tbody>
        {% for link in stats.live_links[:10] %}
        <tr>
          <td><span class="plat-tag">{{ link.platform }}</span></td>
          <td><span class="da-badge {% if link.da >= 90 %}da-high{% elif link.da >= 60 %}da-mid{% else %}da-low{% endif %}">{% if link.da > 0 %}{{ link.da }}{% else %}?{% endif %}</span></td>
          <td><span class="td-title" title="{{ link.title }}">{{ link.title }}</span></td>
          <td><a class="td-url" href="{{ link.url }}" target="_blank" title="{{ link.url }}">{{ link.url }}</a></td>
          <td class="td-date">{{ link.date[:10] if link.date else '' }}</td>
          <td>
            {% if link.verified|lower == 'true' %}
            <span class="verified-yes">✓</span>
            {% else %}
            <span class="verified-no">—</span>
            {% endif %}
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
    {% else %}
    <div class="empty-state">No live backlinks yet. Run the poster first.</div>
    {% endif %}
  </div>

</div>
<!-- end overview -->


<!-- ================================================================ TAB: ALL BACKLINKS -->
<div class="tab-content" id="tab-backlinks">

  <div class="card">
    <div class="card-title"><span class="dot dot-green"></span>All Live Backlinks &mdash; {{ stats.live_links|length }} total</div>

    <div class="bl-controls">
      <input class="bl-search" id="bl-search" type="text" placeholder="Search title, URL, anchor..." oninput="filterTable()">
      <select class="bl-select" id="bl-plat" onchange="filterTable()">
        <option value="">All Platforms</option>
        {% for plat in stats.platform_stats.keys() %}
        <option value="{{ plat }}">{{ plat }}</option>
        {% endfor %}
      </select>
      <select class="bl-select" id="bl-verified" onchange="filterTable()">
        <option value="">All</option>
        <option value="true">Verified Only</option>
        <option value="false">Unverified Only</option>
      </select>
      <select class="bl-select" id="bl-da" onchange="filterTable()">
        <option value="">Any DA</option>
        <option value="90">DA 90+</option>
        <option value="70">DA 70+</option>
        <option value="50">DA 50+</option>
      </select>
      <a href="/export/csv" class="btn btn-success" style="text-decoration:none;">⬇ Export CSV</a>
      <span class="bl-count" id="bl-count">Showing all {{ stats.live_links|length }}</span>
    </div>

    <table class="data-table" id="bl-table">
      <thead>
        <tr>
          <th onclick="sortTable('bl-table',0)">#</th>
          <th onclick="sortTable('bl-table',1)">Platform <span class="sort-arrow">↕</span></th>
          <th onclick="sortTable('bl-table',2)">DA <span class="sort-arrow">↕</span></th>
          <th onclick="sortTable('bl-table',3)">Title <span class="sort-arrow">↕</span></th>
          <th>URL</th>
          <th onclick="sortTable('bl-table',5)">Anchor Text <span class="sort-arrow">↕</span></th>
          <th onclick="sortTable('bl-table',6)">Date <span class="sort-arrow">↕</span></th>
          <th onclick="sortTable('bl-table',7)">Verified <span class="sort-arrow">↕</span></th>
          <th>Check</th>
        </tr>
      </thead>
      <tbody id="bl-tbody">
        {% for link in stats.live_links %}
        <tr
          data-platform="{{ link.platform|lower }}"
          data-verified="{{ link.verified|lower }}"
          data-da="{{ link.da }}"
          data-search="{{ (link.title + ' ' + link.url + ' ' + link.anchor)|lower }}"
        >
          <td style="color:#475569;">{{ loop.index }}</td>
          <td><span class="plat-tag">{{ link.platform }}</span></td>
          <td><span class="da-badge {% if link.da >= 90 %}da-high{% elif link.da >= 60 %}da-mid{% else %}da-low{% endif %}">{% if link.da > 0 %}{{ link.da }}{% else %}?{% endif %}</span></td>
          <td><span class="td-title" title="{{ link.title }}">{{ link.title }}</span></td>
          <td><a class="td-url" href="{{ link.url }}" target="_blank">{{ link.url }}</a></td>
          <td style="font-size:0.75rem;color:#64748b;max-width:160px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{{ link.anchor }}</td>
          <td class="td-date">{{ link.date[:10] if link.date else '' }}</td>
          <td>
            {% if link.verified|lower == 'true' %}
            <span class="verified-yes" title="scotle.org confirmed in page">✓ Yes</span>
            {% else %}
            <span class="verified-no">—</span>
            {% endif %}
          </td>
          <td>
            <button class="btn btn-gray" style="font-size:0.7rem;padding:3px 8px;"
              onclick="quickCheck(this, '{{ link.url }}')">Check</button>
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>

    <div class="pagination" id="bl-pagination"></div>
  </div>

</div>
<!-- end backlinks -->


<!-- ================================================================ TAB: PLATFORM HEALTH -->
<div class="tab-content" id="tab-platforms">

  <div class="platform-grid">
    {% for plat, d in stats.platform_stats.items() %}
    {% set rate = (d.published / d.total * 100)|round(0)|int if d.total else 0 %}
    <div class="platform-card">
      <div class="pc-name">{{ plat }}</div>
      <div class="pc-da {% if d.da >= 90 %}verified-yes{% elif d.da >= 60 %}' style='color:#60a5fa'{% else %}' style='color:#fbbf24'{% endif %}">
        {% if d.da > 0 %}DA {{ d.da }}{% else %}DA ?{% endif %}
      </div>
      <div class="pc-meta">
        Success rate: <strong style="color:{% if rate>=70 %}#34d399{% elif rate>=40 %}#fbbf24{% else %}#f87171{% endif %};">{{ rate }}%</strong>
      </div>
      <div class="pc-stats">
        <span class="badge badge-green">{{ d.published }} live</span>
        {% if d.failed > 0 %}<span class="badge badge-red">{{ d.failed }} failed</span>{% endif %}
        {% if d.verified > 0 %}<span class="badge badge-blue">{{ d.verified }} verified</span>{% endif %}
      </div>
      <div class="progress-bar" style="margin-top:10px;">
        <div class="progress-fill" style="width:{{ rate }}%;background:{% if rate>=70 %}#10b981{% elif rate>=40 %}#f59e0b{% else %}#ef4444{% endif %};"></div>
      </div>
    </div>
    {% endfor %}
  </div>

  <!-- Detailed platform table -->
  <div class="card">
    <div class="card-title"><span class="dot dot-cyan"></span>Full Platform Statistics</div>
    <table class="plat-table">
      <thead>
        <tr>
          <th>Platform</th>
          <th>DA Score</th>
          <th>Total Attempts</th>
          <th>Published</th>
          <th>Failed</th>
          <th>Verified</th>
          <th>Success %</th>
          <th>Verify %</th>
        </tr>
      </thead>
      <tbody>
        {% for plat, d in stats.platform_stats.items() %}
        {% set rate = (d.published / d.total * 100)|round(1) if d.total else 0 %}
        {% set vrate = (d.verified / d.published * 100)|round(1) if d.published else 0 %}
        <tr>
          <td style="font-weight:600;text-transform:capitalize;">{{ plat }}</td>
          <td>
            <span class="da-badge {% if d.da >= 90 %}da-high{% elif d.da >= 60 %}da-mid{% else %}da-low{% endif %}">
              {% if d.da > 0 %}{{ d.da }}{% else %}N/A{% endif %}
            </span>
          </td>
          <td>{{ d.total }}</td>
          <td><span class="badge badge-green">{{ d.published }}</span></td>
          <td><span class="badge {% if d.failed > 0 %}badge-red{% else %}badge-gray{% endif %}">{{ d.failed }}</span></td>
          <td><span class="badge badge-blue">{{ d.verified }}</span></td>
          <td style="color:{% if rate>=70 %}#34d399{% elif rate>=40 %}#fbbf24{% else %}#f87171{% endif %};">{{ rate }}%</td>
          <td style="color:{% if vrate>=70 %}#34d399{% elif vrate>=40 %}#fbbf24{% else %}#f87171{% endif %};">{{ vrate }}%</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>

</div>
<!-- end platforms -->


<!-- ================================================================ TAB: LIVE CHECKER -->
<div class="tab-content" id="tab-checker">

  <!-- Single URL Check -->
  <div class="card">
    <div class="card-title"><span class="dot dot-cyan"></span>Check Single URL</div>
    <div class="checker-box">
      <div class="checker-input-row">
        <input class="checker-input" id="single-url" type="text" placeholder="https://write.as/abc123" value="">
        <button class="btn btn-primary" onclick="checkSingleUrl()">Check URL</button>
      </div>
      <div class="check-result" id="single-result">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
          <span id="sr-icon" style="font-size:1.4rem;"></span>
          <span id="sr-status" style="font-weight:700;font-size:1rem;"></span>
        </div>
        <div class="check-grid">
          <div class="check-item">
            <label>HTTP Status</label>
            <value id="sr-code">—</value>
          </div>
          <div class="check-item">
            <label>scotle.org Found</label>
            <value id="sr-verified">—</value>
          </div>
          <div class="check-item">
            <label>Response Time</label>
            <value id="sr-ms">—</value>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Bulk Checker -->
  <div class="card">
    <div class="card-title"><span class="dot dot-orange"></span>Bulk URL Checker &mdash; All Live Backlinks</div>
    <p style="font-size:0.82rem;color:#64748b;margin-bottom:14px;">
      Checks all {{ stats.live_links|length }} backlinks one by one. Verifies HTTP status and scotle.org presence.
    </p>
    <div style="display:flex;gap:10px;flex-wrap:wrap;">
      <button class="btn btn-primary" onclick="startBulkCheck()" id="bulk-start-btn">Start Bulk Check</button>
      <button class="btn btn-danger" onclick="stopBulkCheck()" id="bulk-stop-btn" style="display:none;">Stop</button>
      <span id="bulk-summary" style="font-size:0.8rem;color:#64748b;display:flex;align-items:center;"></span>
    </div>
    <div class="bulk-progress" id="bulk-progress" style="display:none;">
      <div style="font-size:0.75rem;color:#64748b;" id="bulk-progress-text">Checking...</div>
      <div class="bulk-bar-wrap"><div class="bulk-bar-fill" id="bulk-bar" style="width:0%"></div></div>
      <div class="bulk-log" id="bulk-log"></div>
    </div>
  </div>

  <!-- URLs list for bulk check (hidden data) -->
  <script>
    var ALL_URLS = [
      {% for link in stats.live_links %}
      { url: {{ link.url|tojson }}, title: {{ link.title|tojson }}, platform: {{ link.platform|tojson }} }{% if not loop.last %},{% endif %}
      {% endfor %}
    ];
  </script>

</div>
<!-- end checker -->


<!-- ================================================================ TAB: ACTIVITY LOG -->
<div class="tab-content" id="tab-activity">

  <div class="card">
    <div class="card-title"><span class="dot dot-blue"></span>Full Activity Log (All Posts)</div>

    <div class="bl-controls">
      <input class="bl-search" id="act-search" type="text" placeholder="Search title, platform..." oninput="filterActivity()">
      <select class="bl-select" id="act-status" onchange="filterActivity()">
        <option value="">All Status</option>
        <option value="published">Published Only</option>
        <option value="failed">Failed Only</option>
      </select>
      <select class="bl-select" id="act-plat" onchange="filterActivity()">
        <option value="">All Platforms</option>
        {% for plat in stats.platform_stats.keys() %}
        <option value="{{ plat }}">{{ plat }}</option>
        {% endfor %}
      </select>
      <span class="bl-count" id="act-count">Showing all {{ stats.recent_posts|length }}</span>
    </div>

    <table class="data-table" id="act-table">
      <thead>
        <tr>
          <th>Date</th>
          <th>Platform</th>
          <th>Title</th>
          <th>Status</th>
          <th>Anchor Text</th>
          <th>Words</th>
          <th>Verified</th>
          <th>Error</th>
        </tr>
      </thead>
      <tbody id="act-tbody">
        {% for p in stats.recent_posts %}
        <tr
          data-status="{{ p['Status']|lower }}"
          data-platform="{{ p['Platform']|lower }}"
          data-search="{{ (p['Title'] + ' ' + p['Platform'])|lower }}"
        >
          <td class="td-date">{{ p['Date Published'][:16] if p['Date Published'] else '' }}</td>
          <td><span class="plat-tag">{{ p['Platform'] }}</span></td>
          <td>
            {% if p['Published URL'] %}
            <a class="td-url" href="{{ p['Published URL'] }}" target="_blank" style="max-width:280px;">{{ p['Title'] }}</a>
            {% else %}
            <span class="td-title">{{ p['Title'] }}</span>
            {% endif %}
          </td>
          <td>
            {% if p['Status'] == 'published' %}
            <span class="status-live">✓ LIVE</span>
            {% else %}
            <span class="status-failed">✗ FAILED</span>
            {% endif %}
          </td>
          <td style="font-size:0.72rem;color:#64748b;max-width:140px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{{ p['Anchor Text'] or '—' }}</td>
          <td style="color:#475569;">{{ p['Word Count'] or '—' }}</td>
          <td>
            {% if p.get('verified','') | lower == 'true' %}
            <span class="verified-yes">✓</span>
            {% else %}
            <span class="verified-no">—</span>
            {% endif %}
          </td>
          <td style="font-size:0.7rem;color:#64748b;max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="{{ p['Error'] }}">
            {{ p['Error'][:60] if p['Error'] else '—' }}
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>

</div>
<!-- end activity -->

</div><!-- /container -->

<div class="footer">
  Scotle.org Backlink CRM &mdash; {{ stats.published }} live backlinks &mdash; Target: 50+/week
</div>

<!-- ================================================================ JAVASCRIPT -->
<script>
// ----- Tab switching -----
function switchTab(name, el) {
  document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
  document.getElementById('tab-' + name).classList.add('active');
  if (el) el.classList.add('active');
}
function switchTabByName(name) {
  const tabs = document.querySelectorAll('.nav-tab');
  const names = ['overview','backlinks','platforms','checker','activity'];
  const idx = names.indexOf(name);
  if (idx >= 0) switchTab(name, tabs[idx]);
}

// ----- Backlinks table filter -----
function filterTable() {
  const q    = document.getElementById('bl-search').value.toLowerCase();
  const plat = document.getElementById('bl-plat').value.toLowerCase();
  const ver  = document.getElementById('bl-verified').value.toLowerCase();
  const da   = parseInt(document.getElementById('bl-da').value) || 0;
  const rows = document.querySelectorAll('#bl-tbody tr');
  let count  = 0;
  rows.forEach(row => {
    const rowPlat = row.dataset.platform || '';
    const rowVer  = row.dataset.verified || '';
    const rowDa   = parseInt(row.dataset.da) || 0;
    const rowSrch = row.dataset.search || '';
    const show =
      (!q    || rowSrch.includes(q)) &&
      (!plat || rowPlat === plat) &&
      (!ver  || rowVer === ver) &&
      (!da   || rowDa >= da);
    row.style.display = show ? '' : 'none';
    if (show) count++;
  });
  document.getElementById('bl-count').textContent = 'Showing ' + count;
}

// ----- Activity log filter -----
function filterActivity() {
  const q      = document.getElementById('act-search').value.toLowerCase();
  const status = document.getElementById('act-status').value.toLowerCase();
  const plat   = document.getElementById('act-plat').value.toLowerCase();
  const rows   = document.querySelectorAll('#act-tbody tr');
  let count    = 0;
  rows.forEach(row => {
    const show =
      (!q      || (row.dataset.search || '').includes(q)) &&
      (!status || (row.dataset.status || '') === status) &&
      (!plat   || (row.dataset.platform || '') === plat);
    row.style.display = show ? '' : 'none';
    if (show) count++;
  });
  document.getElementById('act-count').textContent = 'Showing ' + count;
}

// ----- Sort table -----
var sortState = {};
function sortTable(tableId, colIdx) {
  const key = tableId + '_' + colIdx;
  const asc = !sortState[key];
  sortState[key] = asc;
  const tbody = document.querySelector('#' + tableId + ' tbody');
  const rows  = Array.from(tbody.querySelectorAll('tr'));
  rows.sort((a, b) => {
    const at = a.cells[colIdx] ? a.cells[colIdx].innerText.trim() : '';
    const bt = b.cells[colIdx] ? b.cells[colIdx].innerText.trim() : '';
    const an = parseFloat(at), bn = parseFloat(bt);
    if (!isNaN(an) && !isNaN(bn)) return asc ? an - bn : bn - an;
    return asc ? at.localeCompare(bt) : bt.localeCompare(at);
  });
  rows.forEach(r => tbody.appendChild(r));
}

// ----- Quick check button in backlinks table -----
function quickCheck(btn, url) {
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span>';
  fetch('/api/check', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({url: url})
  })
  .then(r => r.json())
  .then(d => {
    btn.disabled = false;
    if (d.status === 'live') {
      btn.innerHTML = d.verified ? '✓ Live' : '⚠ Live';
      btn.style.color = d.verified ? '#34d399' : '#fbbf24';
    } else {
      btn.innerHTML = '✗ Dead';
      btn.style.color = '#f87171';
    }
  })
  .catch(() => { btn.disabled = false; btn.innerHTML = '?'; });
}

// ----- Single URL checker -----
function checkSingleUrl() {
  const url = document.getElementById('single-url').value.trim();
  if (!url) return;
  const res = document.getElementById('single-result');
  res.style.display = 'none';
  fetch('/api/check', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({url: url})
  })
  .then(r => r.json())
  .then(d => {
    res.className = 'check-result ' + d.status;
    document.getElementById('sr-icon').textContent    = d.status==='live' ? '✅' : d.status==='timeout' ? '⏱' : '❌';
    document.getElementById('sr-status').textContent  = d.status.toUpperCase() + (d.http_code ? ' (' + d.http_code + ')' : '');
    document.getElementById('sr-code').textContent    = d.http_code || '—';
    document.getElementById('sr-verified').textContent= d.verified ? '✓ YES' : '✗ NO';
    document.getElementById('sr-ms').textContent      = d.response_ms ? d.response_ms + ' ms' : '—';
    res.style.display = 'block';
  })
  .catch(e => {
    res.className = 'check-result dead';
    document.getElementById('sr-status').textContent = 'Request failed: ' + e;
    res.style.display = 'block';
  });
}
document.getElementById('single-url').addEventListener('keydown', e => {
  if (e.key === 'Enter') checkSingleUrl();
});

// ----- Bulk checker -----
var bulkRunning = false;
var bulkStop    = false;

function startBulkCheck() {
  if (bulkRunning) return;
  bulkRunning = true;
  bulkStop    = false;
  document.getElementById('bulk-start-btn').style.display = 'none';
  document.getElementById('bulk-stop-btn').style.display  = '';
  document.getElementById('bulk-progress').style.display  = '';
  document.getElementById('bulk-log').innerHTML = '';
  document.getElementById('bulk-summary').textContent = '';
  runBulkCheck(0, 0, 0, 0);
}

function stopBulkCheck() {
  bulkStop = true;
}

function runBulkCheck(idx, live, dead, verified) {
  if (bulkStop || idx >= ALL_URLS.length) {
    bulkRunning = false;
    document.getElementById('bulk-start-btn').style.display = '';
    document.getElementById('bulk-stop-btn').style.display  = 'none';
    const total = Math.min(idx, ALL_URLS.length);
    document.getElementById('bulk-summary').innerHTML =
      '<span style="color:#34d399;">✓ ' + live + ' live</span> &nbsp;' +
      '<span style="color:#f87171;">✗ ' + dead + ' dead</span> &nbsp;' +
      '<span style="color:#60a5fa;">⚑ ' + verified + ' verified</span>' +
      (bulkStop ? ' &nbsp;<span style="color:#fbbf24;">(stopped)</span>' : '');
    return;
  }
  const pct  = Math.round(idx / ALL_URLS.length * 100);
  const item = ALL_URLS[idx];
  document.getElementById('bulk-bar').style.width = pct + '%';
  document.getElementById('bulk-progress-text').textContent =
    'Checking ' + (idx+1) + ' / ' + ALL_URLS.length + ' — ' + pct + '%';
  const log = document.getElementById('bulk-log');
  const line = document.createElement('div');
  line.className = 'log-check';
  line.textContent = '[' + (idx+1) + '] Checking: ' + item.url.substring(0,60) + '...';
  log.appendChild(line);
  log.scrollTop = log.scrollHeight;

  fetch('/api/check', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({url: item.url})
  })
  .then(r => r.json())
  .then(d => {
    const isLive = d.status === 'live';
    live     += isLive ? 1 : 0;
    dead     += isLive ? 0 : 1;
    verified += d.verified ? 1 : 0;
    line.className = isLive ? 'log-live' : 'log-dead';
    const vTag = d.verified ? ' [scotle.org ✓]' : '';
    const ms   = d.response_ms ? ' (' + d.response_ms + 'ms)' : '';
    line.textContent = (isLive ? '✓ LIVE ' : '✗ DEAD ') +
      '[' + item.platform + '] ' + item.title.substring(0,50) + vTag + ms;
    setTimeout(() => runBulkCheck(idx+1, live, dead, verified), 400);
  })
  .catch(() => {
    dead++;
    line.className = 'log-dead';
    line.textContent = '✗ ERROR — ' + item.url;
    setTimeout(() => runBulkCheck(idx+1, live, dead, verified), 400);
  });
}
</script>

</body>
</html>"""


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def dashboard():
    posts = load_posts()
    stats = compute_stats(posts)
    now   = datetime.now().strftime("%Y-%m-%d %H:%M")
    return render_template_string(TEMPLATE, stats=stats, now=now)


@app.route("/api/stats")
def api_stats():
    posts = load_posts()
    stats = compute_stats(posts)
    # Serialize for JSON
    return jsonify({
        "total":        stats["total"],
        "published":    stats["published"],
        "failed":       stats["failed"],
        "verified":     stats["verified"],
        "success_rate": stats["success_rate"],
        "verify_rate":  stats["verify_rate"],
        "recent_7d":    stats["recent_7d"],
        "platform_stats": stats["platform_stats"],
        "top_anchors":  stats["top_anchors"],
        "as_of":        datetime.now().isoformat(),
    })


@app.route("/api/posts")
def api_posts():
    posts  = load_posts()
    status = request.args.get("status", "")
    plat   = request.args.get("platform", "")
    if status:
        posts = [p for p in posts if p.get("Status", "").lower() == status.lower()]
    if plat:
        posts = [p for p in posts if p.get("Platform", "").lower() == plat.lower()]
    return jsonify({"count": len(posts), "posts": posts})


@app.route("/api/check", methods=["POST"])
def api_check():
    data = request.get_json(force=True, silent=True) or {}
    url  = data.get("url", "").strip()
    result = check_url_live(url)
    return jsonify(result)


@app.route("/api/check_all")
def api_check_all():
    """Check all live backlink URLs. May be slow."""
    posts   = load_posts()
    live    = [p for p in posts if p.get("Status", "").lower() == "published" and p.get("Published URL")]
    results = []
    for p in live:
        url = p.get("Published URL", "")
        r   = check_url_live(url)
        results.append({
            "url":      url,
            "platform": p.get("Platform", ""),
            "title":    p.get("Title", ""),
            **r,
        })
    live_count     = sum(1 for r in results if r["status"] == "live")
    verified_count = sum(1 for r in results if r.get("verified"))
    return jsonify({
        "total":    len(results),
        "live":     live_count,
        "dead":     len(results) - live_count,
        "verified": verified_count,
        "results":  results,
    })


@app.route("/export/csv")
def export_csv():
    posts = load_posts()
    if not posts:
        return "No data", 404
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=posts[0].keys())
    writer.writeheader()
    writer.writerows(posts)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=scotle_backlinks_{datetime.now().strftime('%Y%m%d')}.csv"}
    )


if __name__ == "__main__":
    print("\n" + "="*52)
    print("  Scotle.org Backlink CRM")
    print("  Open: http://localhost:5000")
    print("  Tabs: Overview | Backlinks | Platforms | Checker")
    print("="*52 + "\n")
    app.run(debug=False, port=5000, threaded=True)
