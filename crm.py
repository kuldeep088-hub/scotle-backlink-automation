"""
Scotle.org Backlink CRM
========================
Run:   python crm.py
Opens: http://localhost:5050  (auto-opens browser)
"""

import os, csv, json, io, time, threading, webbrowser, requests as req
from datetime import datetime, timedelta
from flask import Flask, render_template_string, jsonify, request, Response

app  = Flask(__name__)
BASE = os.path.dirname(os.path.abspath(__file__))

POSTS_LOG  = os.path.join(BASE, "blog_poster", "output", "posts_log.csv")
RECENT_CSV = os.path.join(BASE, "data", "backlinks_recent30.csv")
FAILED_CSV = os.path.join(BASE, "data", "failed_posts.csv")

PLATFORM_DA = {
    "blogger":93, "blogspot":93, "tumblr":98, "hashnode":92,
    "devto":90, "dev.to":90, "writeas":69, "write.as":69,
    "hackmd":65, "hackmd.io":65, "dpaste":55, "bytebin":50,
    "substack":89, "medium":95, "livejournal":93,
}

_url_cache = {}

# ─── Data ──────────────────────────────────────────────────────────────────

def load_posts():
    rows = []
    if not os.path.exists(POSTS_LOG):
        return rows
    with open(POSTS_LOG, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append(dict(r))
    return rows

def load_recent30():
    """Load data/backlinks_recent30.csv — normalise to common field names."""
    rows = []
    if not os.path.exists(RECENT_CSV):
        return rows
    with open(RECENT_CSV, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append({
                "Platform":      r.get("Platform", ""),
                "Title":         r.get("Title", ""),
                "Published URL": r.get("URL", ""),
                "Date Published":r.get("Date Published", ""),
                "Target URL":    r.get("Target URL", ""),
                "Anchor Text":   r.get("Anchor Text", ""),
                "Word Count":    r.get("Word Count", ""),
                "verified":      r.get("Verified", ""),
            })
    return rows

def da(platform):
    return PLATFORM_DA.get(platform.lower().strip(), 0)

def parse_dt(s):
    try:    return datetime.strptime(s[:16], "%Y-%m-%d %H:%M")
    except: return None

def stats(posts):
    total     = len(posts)
    published = [p for p in posts if p.get("Status","").lower() == "published"]
    failed    = [p for p in posts if p.get("Status","").lower() != "published"]
    verified  = [p for p in published if str(p.get("verified","")).lower() == "true"]

    now       = datetime.now()
    week_ago  = now - timedelta(days=7)
    last7     = sum(1 for p in published if parse_dt(p.get("Date Published","")) and parse_dt(p.get("Date Published","")) >= week_ago)

    # platforms
    plats = {}
    for p in posts:
        k = p.get("Platform","?").lower()
        if k not in plats:
            plats[k] = {"name":k,"da":da(k),"total":0,"live":0,"failed":0,"verified":0}
        plats[k]["total"] += 1
        if p.get("Status","").lower() == "published":
            plats[k]["live"] += 1
            if str(p.get("verified","")).lower() == "true":
                plats[k]["verified"] += 1
        else:
            plats[k]["failed"] += 1
    plats = sorted(plats.values(), key=lambda x: -x["da"])

    # daily last 14
    days = {}
    for i in range(14):
        d = (now - timedelta(days=i)).strftime("%Y-%m-%d")
        days[d] = {"d":d,"pub":0,"fail":0}
    for p in posts:
        dt = parse_dt(p.get("Date Published",""))
        if dt:
            d = dt.strftime("%Y-%m-%d")
            if d in days:
                if p.get("Status","").lower() == "published": days[d]["pub"]  += 1
                else:                                          days[d]["fail"] += 1
    daily = sorted(days.values(), key=lambda x: x["d"])

    # anchors
    anchors = {}
    for p in published:
        a = p.get("Anchor Text","").strip()
        if a: anchors[a] = anchors.get(a,0)+1
    top_anchors = sorted(anchors.items(), key=lambda x:-x[1])[:12]

    return {
        "total":total, "published":len(published), "failed":len(failed),
        "verified":len(verified), "last7":last7,
        "success_pct": round(len(published)/total*100,1) if total else 0,
        "verify_pct":  round(len(verified)/len(published)*100,1) if published else 0,
        "platforms":plats, "daily":daily, "anchors":top_anchors,
    }

# ─── Live checker ──────────────────────────────────────────────────────────

def check_url(url):
    if not url or not url.startswith("http"):
        return {"ok":False,"code":0,"ms":0,"has_scotle":False,"status":"invalid"}
    cached = _url_cache.get(url)
    if cached and time.time()-cached.get("ts",0)<3600:
        return cached
    t = time.time()
    try:
        r = req.get(url, timeout=10, allow_redirects=True,
                    headers={"User-Agent":"Mozilla/5.0 CRM/1.0"})
        ms = int((time.time()-t)*1000)
        ok = r.status_code < 400
        hs = "scotle.org" in r.text.lower()
        res = {"ok":ok,"code":r.status_code,"ms":ms,"has_scotle":hs,
               "status":"live" if ok else "dead","ts":time.time()}
    except req.exceptions.Timeout:
        res = {"ok":False,"code":0,"ms":9999,"has_scotle":False,"status":"timeout","ts":time.time()}
    except Exception as e:
        res = {"ok":False,"code":0,"ms":0,"has_scotle":False,"status":"error","err":str(e),"ts":time.time()}
    _url_cache[url] = res
    return res

# ─── Routes ────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    posts    = load_posts()
    s        = stats(posts)
    recent30 = load_recent30()          # 30 backlinks from data/backlinks_recent30.csv
    all_rows = list(reversed(posts))
    return render_template_string(HTML, s=s, published=recent30, all_rows=all_rows,
                                  now=datetime.now().strftime("%d %b %Y, %H:%M"))

@app.route("/api/check", methods=["POST"])
def api_check():
    url = (request.get_json(force=True, silent=True) or {}).get("url","")
    return jsonify(check_url(url))

@app.route("/api/check_all")
def api_check_all():
    posts = [p for p in load_posts()
             if p.get("Status","").lower()=="published" and p.get("Published URL","")]
    results = []
    for p in posts:
        r = check_url(p["Published URL"])
        results.append({"url":p["Published URL"],"platform":p.get("Platform",""),
                        "title":p.get("Title",""),"da":da(p.get("Platform","")),"check":r})
    return jsonify({"total":len(results),"live":sum(1 for r in results if r["check"]["ok"]),
                    "verified":sum(1 for r in results if r["check"]["has_scotle"]),"results":results})

@app.route("/export")
def export():
    rows = load_recent30()
    buf  = io.StringIO()
    if rows:
        w = csv.DictWriter(buf, fieldnames=rows[0].keys())
        w.writeheader(); w.writerows(rows)
    return Response(buf.getvalue(), mimetype="text/csv",
        headers={"Content-Disposition":f"attachment;filename=backlinks_recent30_{datetime.now().strftime('%Y%m%d')}.csv"})

# ─── HTML ──────────────────────────────────────────────────────────────────

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Scotle CRM</title>
<style>
:root{
  --bg:#07090f;--bg2:#0d1117;--bg3:#111827;--bg4:#161e2e;
  --border:#1e2a3a;--border2:#243044;
  --text:#e2e8f0;--muted:#64748b;--muted2:#94a3b8;
  --blue:#3b82f6;--green:#10b981;--red:#ef4444;
  --purple:#8b5cf6;--orange:#f59e0b;--cyan:#06b6d4;
}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Segoe UI',system-ui,sans-serif;background:var(--bg);color:var(--text);min-height:100vh;font-size:14px}

/* scrollbar */
::-webkit-scrollbar{width:6px;height:6px}
::-webkit-scrollbar-track{background:var(--bg2)}
::-webkit-scrollbar-thumb{background:var(--border2);border-radius:3px}

/* ── Header ─────────────────── */
.topbar{
  background:linear-gradient(90deg,#0d1117,#111827);
  border-bottom:1px solid var(--border);
  padding:14px 28px;
  display:flex;align-items:center;justify-content:space-between;
  position:sticky;top:0;z-index:100;
}
.logo{display:flex;align-items:center;gap:12px}
.logo-icon{
  width:36px;height:36px;border-radius:9px;
  background:linear-gradient(135deg,var(--blue),var(--purple));
  display:flex;align-items:center;justify-content:center;
  font-weight:800;font-size:16px;color:#fff;flex-shrink:0;
}
.logo-text h1{font-size:16px;font-weight:700;color:#f8fafc}
.logo-text p{font-size:11px;color:var(--muted);margin-top:1px}
.topbar-right{font-size:11px;color:var(--muted);text-align:right;line-height:1.7}
.topbar-right strong{color:var(--muted2)}

/* ── Sidebar nav ─────────────── */
.layout{display:flex;height:calc(100vh - 61px)}
.sidebar{
  width:200px;flex-shrink:0;background:var(--bg2);
  border-right:1px solid var(--border);
  padding:16px 0;overflow-y:auto;
}
.nav-section{padding:6px 16px 4px;font-size:10px;font-weight:600;
  color:var(--muted);text-transform:uppercase;letter-spacing:.08em;margin-top:8px}
.nav-item{
  display:flex;align-items:center;gap:10px;
  padding:9px 16px;font-size:13px;cursor:pointer;
  color:var(--muted2);border-left:2px solid transparent;
  transition:all .15s;user-select:none;
}
.nav-item:hover{color:var(--text);background:var(--bg3)}
.nav-item.active{color:var(--blue);background:rgba(59,130,246,.08);border-left-color:var(--blue)}
.nav-item .icon{font-size:15px;width:18px;text-align:center;flex-shrink:0}
.nav-badge{
  margin-left:auto;background:var(--border2);color:var(--muted2);
  font-size:10px;font-weight:600;padding:1px 6px;border-radius:9999px;
}

/* ── Main content ────────────── */
.main{flex:1;overflow-y:auto;padding:24px 28px}
.page{display:none}.page.active{display:block}

/* ── KPI grid ────────────────── */
.kpi-grid{display:grid;grid-template-columns:repeat(6,1fr);gap:12px;margin-bottom:20px}
.kpi{
  background:var(--bg3);border:1px solid var(--border);
  border-radius:10px;padding:16px;position:relative;overflow:hidden;
}
.kpi::before{content:'';position:absolute;top:0;left:0;right:0;height:2px}
.kpi.b::before{background:var(--blue)}.kpi.g::before{background:var(--green)}
.kpi.r::before{background:var(--red)}.kpi.p::before{background:var(--purple)}
.kpi.c::before{background:var(--cyan)}.kpi.o::before{background:var(--orange)}
.kpi-lbl{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;margin-bottom:6px}
.kpi-val{font-size:26px;font-weight:700;line-height:1}
.kpi.b .kpi-val{color:#60a5fa}.kpi.g .kpi-val{color:#34d399}
.kpi.r .kpi-val{color:#f87171}.kpi.p .kpi-val{color:#a78bfa}
.kpi.c .kpi-val{color:#22d3ee}.kpi.o .kpi-val{color:#fbbf24}
.kpi-sub{font-size:11px;color:var(--muted);margin-top:5px}

/* ── Section card ────────────── */
.card{background:var(--bg3);border:1px solid var(--border);border-radius:10px;padding:18px;margin-bottom:16px}
.card-head{display:flex;align-items:center;justify-content:space-between;margin-bottom:16px}
.card-title{font-size:12px;font-weight:600;color:var(--muted2);text-transform:uppercase;letter-spacing:.06em;display:flex;align-items:center;gap:8px}
.pill{width:7px;height:7px;border-radius:50%;flex-shrink:0}
.pill-b{background:var(--blue)}.pill-g{background:var(--green)}
.pill-o{background:var(--orange)}.pill-p{background:var(--purple)}
.pill-c{background:var(--cyan)}.pill-r{background:var(--red)}

/* ── Grids ───────────────────── */
.g2{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:16px}
.g3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;margin-bottom:16px}

/* ── Bar chart ───────────────── */
.bchart{display:flex;align-items:flex-end;gap:3px;height:80px;margin-bottom:8px}
.bgrp{flex:1;display:flex;flex-direction:column;align-items:center;gap:2px}
.bwrap{display:flex;gap:2px;align-items:flex-end;height:64px}
.bar{min-width:5px;border-radius:2px 2px 0 0}
.bp{background:var(--green)}.bf{background:var(--red)}
.blbl{font-size:9px;color:var(--muted);text-align:center}
.blegend{display:flex;gap:14px;font-size:11px;color:var(--muted)}
.blegend span::before{content:'■';margin-right:4px}
.blegend .lb-g::before{color:var(--green)}.blegend .lb-r::before{color:var(--red)}

/* ── Data table ──────────────── */
.tbl-wrap{overflow-x:auto}
.tbl{width:100%;border-collapse:collapse;font-size:12.5px}
.tbl th{
  text-align:left;font-size:10px;color:var(--muted);
  text-transform:uppercase;letter-spacing:.05em;
  padding:0 10px 10px;cursor:pointer;user-select:none;white-space:nowrap;
}
.tbl th:hover{color:var(--muted2)}
.tbl td{padding:8px 10px;border-top:1px solid var(--border);vertical-align:middle}
.tbl tr:hover td{background:var(--bg4)}
.tbl-link{color:var(--blue);text-decoration:none;display:block;max-width:260px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.tbl-link:hover{color:#93c5fd;text-decoration:underline}
.tbl-title{color:var(--muted2);display:block;max-width:240px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}

/* ── Badges ──────────────────── */
.badge{display:inline-block;padding:2px 8px;border-radius:9999px;font-size:11px;font-weight:600}
.bg-g{background:#052e16;color:#34d399}.bg-r{background:#3b0a0a;color:#f87171}
.bg-b{background:#0c2048;color:#60a5fa}.bg-gr{background:var(--border2);color:var(--muted2)}
.bg-y{background:#3b2400;color:#fbbf24}
.da-chip{display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;font-weight:700}
.da-hi{background:#052e16;color:#34d399}.da-mid{background:#0c2048;color:#60a5fa}.da-lo{background:#292524;color:#d97706}
.plat-tag{display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;background:var(--border2);color:var(--muted2);text-transform:capitalize}
.st-live{color:#34d399;font-weight:700;font-size:11px}
.st-fail{color:#f87171;font-weight:700;font-size:11px}
.vfy-yes{color:#34d399}.vfy-no{color:var(--muted)}

/* ── Controls ────────────────── */
.ctrl{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:14px}
.inp{
  background:var(--bg2);border:1px solid var(--border2);
  color:var(--text);padding:7px 11px;border-radius:7px;font-size:12px;outline:none;
}
.inp:focus{border-color:var(--blue)}
.inp-search{width:240px}.inp-sm{width:auto}
.btn{padding:7px 14px;border-radius:7px;font-size:12px;font-weight:500;cursor:pointer;border:1px solid transparent;transition:opacity .15s}
.btn:hover{opacity:.85}.btn:disabled{opacity:.5;cursor:not-allowed}
.btn-blue{background:#1d4ed8;color:#fff;border-color:#2563eb}
.btn-green{background:#065f46;color:#34d399;border-color:#059669}
.btn-red{background:#7f1d1d;color:#f87171;border-color:#b91c1c}
.btn-gray{background:var(--border2);color:var(--muted2);border-color:var(--border)}
.lbl-count{font-size:11px;color:var(--muted);margin-left:auto}

/* ── Pagination ──────────────── */
.pager{display:flex;gap:5px;justify-content:center;align-items:center;margin-top:14px;flex-wrap:wrap}
.pg-btn{padding:4px 9px;border-radius:5px;font-size:11px;cursor:pointer;background:var(--border2);color:var(--muted2);border:1px solid var(--border)}
.pg-btn.on,.pg-btn:hover{background:var(--blue);color:#fff;border-color:var(--blue)}
.pg-info{font-size:11px;color:var(--muted);padding:0 8px}

/* ── Platform cards ──────────── */
.plat-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:16px}
.plat-card{background:var(--bg3);border:1px solid var(--border);border-radius:10px;padding:14px}
.plat-card-name{font-weight:700;font-size:14px;color:#f8fafc;text-transform:capitalize;margin-bottom:4px}
.plat-da{font-size:28px;font-weight:800;margin-bottom:4px}
.plat-card .pbar{height:3px;background:var(--border);border-radius:2px;margin-top:10px}
.plat-card .pbar-fill{height:100%;border-radius:2px}

/* ── Anchor chips ────────────── */
.chip-wrap{display:flex;flex-wrap:wrap;gap:7px}
.chip{
  background:var(--bg4);border:1px solid var(--border2);
  color:#93c5fd;padding:4px 10px;border-radius:9999px;font-size:11px;
  display:flex;align-items:center;gap:5px;
}
.chip .n{color:var(--blue);font-weight:700}

/* ── Checker ─────────────────── */
.checker-box{background:var(--bg2);border:1px solid var(--border);border-radius:9px;padding:16px;margin-bottom:14px}
.check-row{display:flex;gap:8px;margin-bottom:10px}
.check-inp{flex:1;font-family:monospace;font-size:12px}
.check-result{border-radius:8px;padding:14px;display:none;margin-top:10px}
.cr-live{background:#052e16;border:1px solid #166534}
.cr-dead,.cr-error,.cr-invalid{background:#1c0404;border:1px solid #7f1d1d}
.cr-timeout{background:#1c1204;border:1px solid #78350f}
.cr-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:10px}
.cr-item label{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.05em;display:block;margin-bottom:3px}
.cr-item .val{font-size:15px;font-weight:700}
.cr-head{display:flex;align-items:center;gap:10px;margin-bottom:6px}
.cr-icon{font-size:20px}
.cr-status{font-weight:700;font-size:15px}

/* ── Bulk checker ────────────── */
.bulk-bar-bg{background:var(--border);border-radius:3px;height:5px;margin:8px 0;overflow:hidden}
.bulk-bar-fill{height:100%;border-radius:3px;background:var(--blue);transition:width .3s}
.bulk-log{
  background:var(--bg);border:1px solid var(--border);border-radius:7px;
  padding:10px;max-height:260px;overflow-y:auto;
  font-family:monospace;font-size:11px;color:var(--muted2);margin-top:10px;
  line-height:1.6;
}
.log-ok{color:#34d399}.log-dead{color:#f87171}.log-skip{color:var(--muted)}.log-check{color:#60a5fa}

/* ── Progress bar util ───────── */
.prog{height:3px;background:var(--border);border-radius:2px;margin-top:6px}
.prog-fill{height:100%;border-radius:2px}

/* ── Cmd cards ───────────────── */
.cmd-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:9px}
.cmd-card{background:var(--bg2);border:1px solid var(--border);border-radius:7px;padding:10px 12px}
.cmd-lbl{font-size:10px;color:var(--muted);margin-bottom:4px}
.cmd-val{font-family:monospace;font-size:11px;color:#34d399;word-break:break-all}

/* ── Spinner ─────────────────── */
.spin{display:inline-block;width:12px;height:12px;border:2px solid var(--border2);border-top-color:var(--blue);border-radius:50%;animation:sp .6s linear infinite;vertical-align:middle}
@keyframes sp{to{transform:rotate(360deg)}}

/* ── Summary strip ───────────── */
.sum-strip{display:flex;gap:16px;font-size:12px;color:var(--muted);align-items:center;flex-wrap:wrap}
.sum-strip strong{color:var(--muted2)}

@media(max-width:1200px){.kpi-grid{grid-template-columns:repeat(3,1fr)}.plat-grid{grid-template-columns:repeat(2,1fr)}}
@media(max-width:800px){.layout{flex-direction:column}.sidebar{width:100%;height:auto;display:flex;flex-wrap:wrap;padding:8px}.kpi-grid{grid-template-columns:repeat(2,1fr)}.g2,.g3{grid-template-columns:1fr}}
</style>
</head>
<body>

<!-- ── Top bar ──────────────────────────────────────────────────────── -->
<div class="topbar">
  <div class="logo">
    <div class="logo-icon">S</div>
    <div class="logo-text">
      <h1>Scotle.org — Backlink CRM</h1>
      <p>CBSE High School · Jaipur · Vaishali Nagar</p>
    </div>
  </div>
  <div class="topbar-right">
    <strong>Target:</strong> scotle.org &nbsp;|&nbsp;
    <strong>Goal:</strong> 50+ backlinks/week &nbsp;|&nbsp;
    <strong>Updated:</strong> {{ now }}
  </div>
</div>

<!-- ── Layout ───────────────────────────────────────────────────────── -->
<div class="layout">

<!-- Sidebar -->
<div class="sidebar">
  <div class="nav-section">Dashboard</div>
  <div class="nav-item active" onclick="nav('overview',this)"><span class="icon">📊</span> Overview</div>
  <div class="nav-item" onclick="nav('checker',this)"><span class="icon">🔍</span> Live Checker</div>

  <div class="nav-section">Backlinks</div>
  <div class="nav-item" onclick="nav('live',this)">
    <span class="icon">🔗</span> Recent 30 Links
    <span class="nav-badge">{{ published|length }}</span>
  </div>
  <div class="nav-item" onclick="nav('all',this)">
    <span class="icon">📋</span> All Activity
    <span class="nav-badge">{{ all_rows|length }}</span>
  </div>

  <div class="nav-section">Analysis</div>
  <div class="nav-item" onclick="nav('platforms',this)"><span class="icon">🏢</span> Platforms</div>
  <div class="nav-item" onclick="nav('anchors',this)"><span class="icon">⚓</span> Anchor Texts</div>

  <div class="nav-section">Tools</div>
  <div class="nav-item" onclick="window.location='/export'"><span class="icon">⬇️</span> Export CSV</div>
  <div class="nav-item" onclick="location.reload()"><span class="icon">🔄</span> Refresh Data</div>
</div>

<!-- Main -->
<div class="main">

<!-- ══════════════════════════════════════════════ PAGE: OVERVIEW -->
<div class="page active" id="p-overview">

  <!-- KPI -->
  <div class="kpi-grid">
    <div class="kpi b"><div class="kpi-lbl">Total Attempted</div><div class="kpi-val">{{ s.total }}</div><div class="kpi-sub">All time</div></div>
    <div class="kpi g"><div class="kpi-lbl">Live Backlinks</div><div class="kpi-val">{{ s.published }}</div><div class="kpi-sub">Published</div></div>
    <div class="kpi r"><div class="kpi-lbl">Failed Posts</div><div class="kpi-val">{{ s.failed }}</div><div class="kpi-sub">Need attention</div></div>
    <div class="kpi c"><div class="kpi-lbl">Verified</div><div class="kpi-val">{{ s.verified }}</div><div class="kpi-sub">scotle.org confirmed</div></div>
    <div class="kpi p"><div class="kpi-lbl">Success Rate</div><div class="kpi-val">{{ s.success_pct }}%</div><div class="kpi-sub">Live / Attempted</div></div>
    <div class="kpi o"><div class="kpi-lbl">Last 7 Days</div><div class="kpi-val">{{ s.last7 }}</div><div class="kpi-sub">Recent backlinks</div></div>
  </div>

  <div class="g2">
    <!-- Daily chart -->
    <div class="card">
      <div class="card-head"><div class="card-title"><span class="pill pill-b"></span>Posts Per Day — Last 14 Days</div></div>
      {% set mx = namespace(v=1) %}
      {% for d in s.daily %}{% if (d.pub+d.fail)>mx.v %}{% set mx.v=d.pub+d.fail %}{% endif %}{% endfor %}
      <div class="bchart">
        {% for d in s.daily %}
        <div class="bgrp">
          <div class="bwrap">
            {% if d.pub  %}<div class="bar bp" style="height:{{ [d.pub*60//mx.v,2]|max }}px" title="{{ d.pub }} published {{ d.d }}"></div>{% endif %}
            {% if d.fail %}<div class="bar bf" style="height:{{ [d.fail*60//mx.v,2]|max }}px" title="{{ d.fail }} failed {{ d.d }}"></div>{% endif %}
          </div>
          <div class="blbl">{{ d.d[5:] }}</div>
        </div>
        {% endfor %}
      </div>
      <div class="blegend"><span class="lb-g">Published</span><span class="lb-r">Failed</span></div>
    </div>

    <!-- Platform summary -->
    <div class="card">
      <div class="card-head"><div class="card-title"><span class="pill pill-g"></span>Platform Summary</div></div>
      <table class="tbl">
        <thead><tr><th>Platform</th><th>DA</th><th>Live</th><th>Failed</th><th>Rate</th></tr></thead>
        <tbody>
          {% for p in s.platforms %}
          {% set rate=(p.live/p.total*100)|round(0)|int if p.total else 0 %}
          <tr>
            <td style="font-weight:600;text-transform:capitalize;">{{ p.name }}</td>
            <td><span class="da-chip {% if p.da>=90 %}da-hi{% elif p.da>=60 %}da-mid{% else %}da-lo{% endif %}">{% if p.da %}{{ p.da }}{% else %}?{% endif %}</span></td>
            <td><span class="badge bg-g">{{ p.live }}</span></td>
            <td><span class="badge {% if p.failed %}bg-r{% else %}bg-gr{% endif %}">{{ p.failed }}</span></td>
            <td>
              <span style="font-size:11px;color:{% if rate>=70 %}#34d399{% elif rate>=40 %}#fbbf24{% else %}#f87171{% endif %}">{{ rate }}%</span>
              <div class="prog"><div class="prog-fill" style="width:{{ rate }}%;background:{% if rate>=70 %}var(--green){% elif rate>=40 %}var(--orange){% else %}var(--red){% endif %}"></div></div>
            </td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
  </div>

  <!-- Quick commands -->
  <div class="card">
    <div class="card-head"><div class="card-title"><span class="pill pill-o"></span>Quick Commands</div></div>
    <div class="cmd-grid">
      {% for lbl,cmd in [
        ('Quick Post (1/platform)','python unified_poster.py --mode quick'),
        ('Mega Mode (56 posts)','python unified_poster.py --mode mega --count 56'),
        ('Bulk Write.as (24)','python unified_poster.py --mode bulk'),
        ('Validate Credentials','python -m blog_poster.blog_poster --validate'),
        ('Force School Niche','python -m blog_poster.blog_poster --niche school'),
        ('Dry Run Pipeline','python -m blog_poster.local_content_pipeline --dry-run'),
      ] %}
      <div class="cmd-card"><div class="cmd-lbl">{{ lbl }}</div><div class="cmd-val">{{ cmd }}</div></div>
      {% endfor %}
    </div>
  </div>

</div><!-- /overview -->


<!-- ══════════════════════════════════════════════ PAGE: LIVE BACKLINKS -->
<div class="page" id="p-live">
  <div class="card">
    <div class="card-head">
      <div class="card-title"><span class="pill pill-g"></span>Recent 30 Backlinks — from data/backlinks_recent30.csv</div>
      <a href="/export" class="btn btn-green" style="text-decoration:none;font-size:11px;">⬇ Export CSV</a>
    </div>

    <div class="ctrl">
      <input class="inp inp-search" id="lv-q"   type="text"   placeholder="Search title, URL, anchor…" oninput="filterLive()">
      <select class="inp inp-sm"    id="lv-plat" onchange="filterLive()">
        <option value="">All Platforms</option>
        {% for p in s.platforms %}<option value="{{ p.name }}">{{ p.name }}</option>{% endfor %}
      </select>
      <select class="inp inp-sm" id="lv-vfy" onchange="filterLive()">
        <option value="">All</option>
        <option value="yes">Verified Only</option>
        <option value="no">Not Verified</option>
      </select>
      <select class="inp inp-sm" id="lv-da" onchange="filterLive()">
        <option value="0">Any DA</option>
        <option value="90">DA 90+</option>
        <option value="70">DA 70+</option>
        <option value="50">DA 50+</option>
      </select>
      <span class="lbl-count" id="lv-cnt">{{ published|length }} rows</span>
    </div>

    <div class="tbl-wrap">
    <table class="tbl" id="lv-tbl">
      <thead>
        <tr>
          <th onclick="sortTbl('lv-tbl',0)">#</th>
          <th onclick="sortTbl('lv-tbl',1)">Platform ↕</th>
          <th onclick="sortTbl('lv-tbl',2)">DA ↕</th>
          <th onclick="sortTbl('lv-tbl',3)">Title ↕</th>
          <th>Published URL</th>
          <th onclick="sortTbl('lv-tbl',5)">Anchor ↕</th>
          <th onclick="sortTbl('lv-tbl',6)">Date ↕</th>
          <th onclick="sortTbl('lv-tbl',7)">Verified ↕</th>
          <th>Check</th>
        </tr>
      </thead>
      <tbody id="lv-body">
        {% for p in published %}
        {% set d=p.get('Platform','') %}
        <tr data-plat="{{ d|lower }}"
            data-da="{{ {'blogger':93,'tumblr':98,'hashnode':92,'devto':90,'dev.to':90,'writeas':69,'write.as':69,'hackmd':65,'dpaste':55,'bytebin':50}.get(d|lower,0) }}"
            data-vfy="{{ 'yes' if p.get('verified','')|lower=='true' else 'no' }}"
            data-search="{{ (p.get('Title','')+' '+p.get('Published URL','')+' '+p.get('Anchor Text','')+' '+d)|lower }}">
          <td style="color:var(--muted)">{{ loop.index }}</td>
          <td><span class="plat-tag">{{ d }}</span></td>
          <td>
            {% set dav={'blogger':93,'tumblr':98,'hashnode':92,'devto':90,'dev.to':90,'writeas':69,'write.as':69,'hackmd':65,'dpaste':55,'bytebin':50}.get(d|lower,0) %}
            <span class="da-chip {% if dav>=90 %}da-hi{% elif dav>=60 %}da-mid{% else %}da-lo{% endif %}">{% if dav %}{{ dav }}{% else %}?{% endif %}</span>
          </td>
          <td><span class="tbl-title" title="{{ p.get('Title','') }}">{{ p.get('Title','') }}</span></td>
          <td><a class="tbl-link" href="{{ p.get('Published URL','') }}" target="_blank">{{ p.get('Published URL','') }}</a></td>
          <td style="font-size:11px;color:var(--muted);max-width:140px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{{ p.get('Anchor Text','') }}</td>
          <td style="color:var(--muted);white-space:nowrap;font-size:11px;">{{ p.get('Date Published','')[:10] }}</td>
          <td>
            {% if p.get('verified','')|lower=='true' %}
            <span class="vfy-yes">✓ Yes</span>
            {% else %}
            <span class="vfy-no">—</span>
            {% endif %}
          </td>
          <td>
            <button class="btn btn-gray" style="font-size:10px;padding:3px 7px"
              onclick="quickChk(this,'{{ p.get('Published URL','') }}')">Check</button>
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
    </div>
    <div class="pager" id="lv-pager"></div>
  </div>
</div><!-- /live -->


<!-- ══════════════════════════════════════════════ PAGE: ALL ACTIVITY -->
<div class="page" id="p-all">
  <div class="card">
    <div class="card-head"><div class="card-title"><span class="pill pill-b"></span>All Activity — {{ all_rows|length }} entries</div></div>

    <div class="ctrl">
      <input class="inp inp-search" id="al-q" type="text" placeholder="Search…" oninput="filterAll()">
      <select class="inp inp-sm" id="al-plat" onchange="filterAll()">
        <option value="">All Platforms</option>
        {% for p in s.platforms %}<option value="{{ p.name }}">{{ p.name }}</option>{% endfor %}
      </select>
      <select class="inp inp-sm" id="al-status" onchange="filterAll()">
        <option value="">All Status</option>
        <option value="published">Published</option>
        <option value="failed">Failed</option>
      </select>
      <span class="lbl-count" id="al-cnt">{{ all_rows|length }} rows</span>
    </div>

    <div class="tbl-wrap">
    <table class="tbl" id="al-tbl">
      <thead>
        <tr>
          <th onclick="sortTbl('al-tbl',0)">Date ↕</th>
          <th onclick="sortTbl('al-tbl',1)">Platform ↕</th>
          <th onclick="sortTbl('al-tbl',2)">Title ↕</th>
          <th onclick="sortTbl('al-tbl',3)">Status ↕</th>
          <th>Anchor</th>
          <th onclick="sortTbl('al-tbl',5)">Words ↕</th>
          <th onclick="sortTbl('al-tbl',6)">Verified ↕</th>
          <th>Error</th>
        </tr>
      </thead>
      <tbody id="al-body">
        {% for p in all_rows %}
        <tr data-plat="{{ p.get('Platform','')|lower }}"
            data-status="{{ p.get('Status','')|lower }}"
            data-search="{{ (p.get('Title','')+' '+p.get('Platform',''))|lower }}">
          <td style="color:var(--muted);white-space:nowrap;font-size:11px;">{{ p.get('Date Published','')[:16] }}</td>
          <td><span class="plat-tag">{{ p.get('Platform','') }}</span></td>
          <td>
            {% if p.get('Published URL','') %}
            <a class="tbl-link" href="{{ p.get('Published URL','') }}" target="_blank" style="max-width:240px;">{{ p.get('Title','') }}</a>
            {% else %}
            <span class="tbl-title">{{ p.get('Title','') }}</span>
            {% endif %}
          </td>
          <td>{% if p.get('Status','')|lower=='published' %}<span class="st-live">✓ LIVE</span>{% else %}<span class="st-fail">✗ FAILED</span>{% endif %}</td>
          <td style="font-size:11px;color:var(--muted);max-width:120px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{{ p.get('Anchor Text','') or '—' }}</td>
          <td style="color:var(--muted);font-size:11px;">{{ p.get('Word Count','') or '—' }}</td>
          <td>{% if p.get('verified','')|lower=='true' %}<span class="vfy-yes">✓</span>{% else %}<span class="vfy-no">—</span>{% endif %}</td>
          <td style="font-size:10px;color:var(--muted);max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="{{ p.get('Error','') }}">{{ p.get('Error','')[:50] or '—' }}</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
    </div>
    <div class="pager" id="al-pager"></div>
  </div>
</div><!-- /all -->


<!-- ══════════════════════════════════════════════ PAGE: PLATFORMS -->
<div class="page" id="p-platforms">

  <div class="plat-grid">
    {% for p in s.platforms %}
    {% set rate=(p.live/p.total*100)|round(0)|int if p.total else 0 %}
    <div class="plat-card">
      <div class="plat-card-name">{{ p.name }}</div>
      <div class="plat-da {% if p.da>=90 %}da-hi{% elif p.da>=60 %}da-mid{% else %}da-lo{% endif %}" style="font-size:28px;font-weight:800;display:block;margin-bottom:4px">
        {% if p.da %}DA {{ p.da }}{% else %}DA ?{% endif %}
      </div>
      <div style="font-size:11px;color:var(--muted);margin-bottom:8px">
        Success: <strong style="color:{% if rate>=70 %}#34d399{% elif rate>=40 %}#fbbf24{% else %}#f87171{% endif %}">{{ rate }}%</strong>
      </div>
      <div style="display:flex;gap:6px;flex-wrap:wrap">
        <span class="badge bg-g">{{ p.live }} live</span>
        {% if p.failed %}<span class="badge bg-r">{{ p.failed }} failed</span>{% endif %}
        {% if p.verified %}<span class="badge bg-b">{{ p.verified }} verified</span>{% endif %}
      </div>
      <div class="pbar" style="height:3px;background:var(--border);border-radius:2px;margin-top:10px">
        <div class="pbar-fill" style="height:100%;width:{{ rate }}%;border-radius:2px;background:{% if rate>=70 %}var(--green){% elif rate>=40 %}var(--orange){% else %}var(--red){% endif %}"></div>
      </div>
    </div>
    {% endfor %}
  </div>

  <div class="card">
    <div class="card-head"><div class="card-title"><span class="pill pill-c"></span>Detailed Platform Table</div></div>
    <table class="tbl">
      <thead><tr><th>Platform</th><th>DA</th><th>Attempts</th><th>Live</th><th>Failed</th><th>Verified</th><th>Success %</th><th>Verify %</th></tr></thead>
      <tbody>
        {% for p in s.platforms %}
        {% set rate=(p.live/p.total*100)|round(1) if p.total else 0 %}
        {% set vrate=(p.verified/p.live*100)|round(1) if p.live else 0 %}
        <tr>
          <td style="font-weight:600;text-transform:capitalize;">{{ p.name }}</td>
          <td><span class="da-chip {% if p.da>=90 %}da-hi{% elif p.da>=60 %}da-mid{% else %}da-lo{% endif %}">{% if p.da %}{{ p.da }}{% else %}?{% endif %}</span></td>
          <td>{{ p.total }}</td>
          <td><span class="badge bg-g">{{ p.live }}</span></td>
          <td><span class="badge {% if p.failed %}bg-r{% else %}bg-gr{% endif %}">{{ p.failed }}</span></td>
          <td><span class="badge bg-b">{{ p.verified }}</span></td>
          <td style="color:{% if rate>=70 %}#34d399{% elif rate>=40 %}#fbbf24{% else %}#f87171{% endif %}">{{ rate }}%</td>
          <td style="color:{% if vrate>=70 %}#34d399{% elif vrate>=40 %}#fbbf24{% else %}#f87171{% endif %}">{{ vrate }}%</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</div><!-- /platforms -->


<!-- ══════════════════════════════════════════════ PAGE: ANCHOR TEXTS -->
<div class="page" id="p-anchors">
  <div class="card">
    <div class="card-head"><div class="card-title"><span class="pill pill-p"></span>Anchor Text Usage</div></div>
    <div class="chip-wrap" style="margin-bottom:24px">
      {% for anchor,cnt in s.anchors %}
      <div class="chip">{{ anchor }}<span class="n">×{{ cnt }}</span></div>
      {% endfor %}
    </div>

    <div class="card-title" style="margin-bottom:14px"><span class="pill pill-p"></span>All Anchor Texts — Full List</div>
    <table class="tbl">
      <thead><tr><th>Anchor Text</th><th>Times Used</th><th>% of Total</th></tr></thead>
      <tbody>
        {% for anchor,cnt in s.anchors %}
        {% set pct=(cnt/s.published*100)|round(1) if s.published else 0 %}
        <tr>
          <td>{{ anchor }}</td>
          <td><span class="badge bg-b">{{ cnt }}</span></td>
          <td>
            <span style="font-size:11px;color:var(--muted)">{{ pct }}%</span>
            <div class="prog"><div class="prog-fill" style="width:{{ [pct*3,100]|min }}%;background:var(--purple)"></div></div>
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</div><!-- /anchors -->


<!-- ══════════════════════════════════════════════ PAGE: LIVE CHECKER -->
<div class="page" id="p-checker">

  <!-- Single check -->
  <div class="card">
    <div class="card-head"><div class="card-title"><span class="pill pill-c"></span>Check Single URL</div></div>
    <div class="checker-box">
      <div class="check-row">
        <input class="inp check-inp" id="chk-url" type="text" placeholder="https://write.as/abc123 …"
               onkeydown="if(event.key==='Enter')doCheck()">
        <button class="btn btn-blue" onclick="doCheck()">Check URL</button>
      </div>
      <div class="check-result" id="chk-res">
        <div class="cr-head">
          <span class="cr-icon" id="chk-icon"></span>
          <span class="cr-status" id="chk-status"></span>
        </div>
        <div class="cr-grid">
          <div class="cr-item"><label>HTTP Code</label><span class="val" id="chk-code">—</span></div>
          <div class="cr-item"><label>scotle.org Found</label><span class="val" id="chk-vfy">—</span></div>
          <div class="cr-item"><label>Response Time</label><span class="val" id="chk-ms">—</span></div>
        </div>
      </div>
    </div>
  </div>

  <!-- Bulk check -->
  <div class="card">
    <div class="card-head"><div class="card-title"><span class="pill pill-o"></span>Bulk Check — Recent 30 Backlinks</div></div>
    <p style="font-size:12px;color:var(--muted);margin-bottom:14px">
      Checks all {{ published|length }} recent URLs for HTTP status and scotle.org presence. Takes ~{{ (published|length * 0.4)|round(0)|int }} seconds.
    </p>
    <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap">
      <button class="btn btn-blue" id="bulk-start" onclick="startBulk()">▶ Start Bulk Check</button>
      <button class="btn btn-red"  id="bulk-stop"  onclick="stopBulk()" style="display:none">■ Stop</button>
      <div class="sum-strip" id="bulk-summary"></div>
    </div>
    <div id="bulk-prog" style="display:none;margin-top:12px">
      <div style="font-size:11px;color:var(--muted)" id="bulk-prog-txt">Starting…</div>
      <div class="bulk-bar-bg"><div class="bulk-bar-fill" id="bulk-bar" style="width:0%"></div></div>
      <div class="bulk-log" id="bulk-log"></div>
    </div>
  </div>

  <!-- Embedded URLs for JS bulk check -->
  <script>
    var ALL_URLS = {{ published | map(attribute='Published URL') | list | tojson }};
    var ALL_META = [
      {% for p in published %}
      {url:{{ p.get('Published URL','')|tojson }},plat:{{ p.get('Platform','')|tojson }},title:{{ p.get('Title','')|tojson }}}{% if not loop.last %},{% endif %}
      {% endfor %}
    ];
  </script>
</div><!-- /checker -->

</div><!-- /main -->
</div><!-- /layout -->

<!-- ── JavaScript ────────────────────────────────────────────────────────── -->
<script>
// ── Navigation ──────────────────────────────────────────────────────────
function nav(id, el) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.getElementById('p-' + id).classList.add('active');
  if (el) el.classList.add('active');
}

// ── Pagination helper ───────────────────────────────────────────────────
var PAGE_SIZE = 50;
var _pages = {};

function buildPager(tableId, pagerId, total) {
  if (!_pages[tableId]) _pages[tableId] = 1;
  var pages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  if (_pages[tableId] > pages) _pages[tableId] = 1;
  var cur   = _pages[tableId];
  var pager = document.getElementById(pagerId);
  pager.innerHTML = '';
  if (pages <= 1) return;
  var info = document.createElement('span');
  info.className = 'pg-info';
  info.textContent = 'Page ' + cur + ' of ' + pages;
  pager.appendChild(info);
  for (var i = 1; i <= pages; i++) {
    (function(page) {
      var btn = document.createElement('button');
      btn.className = 'pg-btn' + (page === cur ? ' on' : '');
      btn.textContent = page;
      btn.onclick = function() { _pages[tableId] = page; applyPage(tableId); buildPager(tableId, pagerId, total); };
      pager.appendChild(btn);
    })(i);
  }
}

function applyPage(tableId) {
  var cur  = _pages[tableId] || 1;
  var rows = document.querySelectorAll('#' + tableId + ' tbody tr');
  var vis  = [];
  rows.forEach(r => { if (r.style.display !== 'none') vis.push(r); });
  vis.forEach((r, i) => { r.style.visibility = (i >= (cur-1)*PAGE_SIZE && i < cur*PAGE_SIZE) ? '' : 'hidden'; r.style.height = (i >= (cur-1)*PAGE_SIZE && i < cur*PAGE_SIZE) ? '' : '0'; r.style.overflow = 'hidden'; });
}

// ── Filter: Live backlinks ───────────────────────────────────────────────
function filterLive() {
  var q    = document.getElementById('lv-q').value.toLowerCase();
  var plat = document.getElementById('lv-plat').value.toLowerCase();
  var vfy  = document.getElementById('lv-vfy').value;
  var mda  = parseInt(document.getElementById('lv-da').value) || 0;
  var rows = document.querySelectorAll('#lv-body tr');
  var cnt  = 0;
  rows.forEach(function(r) {
    var show = (!q    || r.dataset.search.includes(q)) &&
               (!plat || r.dataset.plat === plat) &&
               (!vfy  || r.dataset.vfy === vfy) &&
               (!mda  || parseInt(r.dataset.da||0) >= mda);
    r.style.display = show ? '' : 'none';
    if (show) cnt++;
  });
  document.getElementById('lv-cnt').textContent = cnt + ' rows';
  _pages['lv-tbl'] = 1;
  buildPager('lv-tbl', 'lv-pager', cnt);
}

// ── Filter: All activity ─────────────────────────────────────────────────
function filterAll() {
  var q    = document.getElementById('al-q').value.toLowerCase();
  var plat = document.getElementById('al-plat').value.toLowerCase();
  var st   = document.getElementById('al-status').value.toLowerCase();
  var rows = document.querySelectorAll('#al-body tr');
  var cnt  = 0;
  rows.forEach(function(r) {
    var show = (!q    || r.dataset.search.includes(q)) &&
               (!plat || r.dataset.plat === plat) &&
               (!st   || r.dataset.status === st);
    r.style.display = show ? '' : 'none';
    if (show) cnt++;
  });
  document.getElementById('al-cnt').textContent = cnt + ' rows';
  _pages['al-tbl'] = 1;
  buildPager('al-tbl', 'al-pager', cnt);
}

// ── Sort table ───────────────────────────────────────────────────────────
var _sortState = {};
function sortTbl(id, col) {
  var key = id+'_'+col;
  var asc = !_sortState[key];
  _sortState[key] = asc;
  var tbody = document.querySelector('#'+id+' tbody');
  var rows  = Array.from(tbody.querySelectorAll('tr'));
  rows.sort(function(a,b) {
    var at = (a.cells[col]||{}).innerText||'';
    var bt = (b.cells[col]||{}).innerText||'';
    var an = parseFloat(at), bn = parseFloat(bt);
    if (!isNaN(an) && !isNaN(bn)) return asc ? an-bn : bn-an;
    return asc ? at.localeCompare(bt) : bt.localeCompare(at);
  });
  rows.forEach(r => tbody.appendChild(r));
}

// ── Quick check button in table ──────────────────────────────────────────
function quickChk(btn, url) {
  if (!url) return;
  btn.disabled = true;
  btn.innerHTML = '<span class="spin"></span>';
  fetch('/api/check', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({url:url})})
    .then(r=>r.json())
    .then(function(d) {
      btn.disabled = false;
      if (d.ok) {
        btn.textContent = d.has_scotle ? '✓ OK' : '⚠ Live';
        btn.style.color = d.has_scotle ? '#34d399' : '#fbbf24';
      } else {
        btn.textContent = d.status==='timeout' ? '⏱ Timeout' : '✗ Dead';
        btn.style.color = '#f87171';
      }
    })
    .catch(function(){ btn.disabled=false; btn.textContent='?'; });
}

// ── Single checker ───────────────────────────────────────────────────────
function doCheck() {
  var url = document.getElementById('chk-url').value.trim();
  if (!url) return;
  var res = document.getElementById('chk-res');
  res.style.display = 'none';
  fetch('/api/check', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({url:url})})
    .then(r=>r.json())
    .then(function(d) {
      res.className = 'check-result cr-' + d.status;
      document.getElementById('chk-icon').textContent   = d.ok ? '✅' : (d.status==='timeout' ? '⏱️' : '❌');
      document.getElementById('chk-status').textContent = d.status.toUpperCase() + (d.code ? ' (HTTP '+d.code+')' : '');
      document.getElementById('chk-code').textContent   = d.code || '—';
      document.getElementById('chk-vfy').textContent    = d.has_scotle ? '✓ YES' : '✗ NO';
      document.getElementById('chk-ms').textContent     = d.ms ? d.ms+'ms' : '—';
      res.style.display = 'block';
    })
    .catch(function(e){ alert('Error: '+e); });
}

// ── Bulk checker ─────────────────────────────────────────────────────────
var _bulkRunning = false;
var _bulkStop    = false;

function startBulk() {
  if (_bulkRunning) return;
  _bulkRunning = true; _bulkStop = false;
  document.getElementById('bulk-start').style.display = 'none';
  document.getElementById('bulk-stop').style.display  = '';
  document.getElementById('bulk-prog').style.display  = '';
  document.getElementById('bulk-log').innerHTML = '';
  document.getElementById('bulk-summary').innerHTML = '';
  runBulk(0, 0, 0, 0);
}
function stopBulk() { _bulkStop = true; }

function runBulk(i, live, dead, vfy) {
  if (_bulkStop || i >= ALL_META.length) {
    _bulkRunning = false;
    document.getElementById('bulk-start').style.display = '';
    document.getElementById('bulk-stop').style.display  = 'none';
    document.getElementById('bulk-prog-txt').textContent = 'Done — checked ' + i + ' URLs';
    document.getElementById('bulk-bar').style.width = '100%';
    document.getElementById('bulk-summary').innerHTML =
      '<strong style="color:#34d399">✓ ' + live + ' live</strong> &nbsp;' +
      '<strong style="color:#f87171">✗ ' + dead + ' dead</strong> &nbsp;' +
      '<strong style="color:#60a5fa">⚑ ' + vfy  + ' verified</strong>' +
      (_bulkStop ? ' &nbsp;<span style="color:#fbbf24">(stopped)</span>' : '');
    return;
  }
  var pct  = Math.round(i / ALL_META.length * 100);
  var item = ALL_META[i];
  document.getElementById('bulk-bar').style.width = pct + '%';
  document.getElementById('bulk-prog-txt').textContent = 'Checking ' + (i+1) + ' / ' + ALL_META.length + '  (' + pct + '%)';

  var log  = document.getElementById('bulk-log');
  var line = document.createElement('div');
  line.className = 'log-check';
  line.textContent = '[' + (i+1) + '] ' + item.url.substring(0,70);
  log.appendChild(line);
  log.scrollTop = log.scrollHeight;

  fetch('/api/check', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({url:item.url})})
    .then(r=>r.json())
    .then(function(d) {
      live += d.ok ? 1 : 0;
      dead += d.ok ? 0 : 1;
      vfy  += d.has_scotle ? 1 : 0;
      line.className = d.ok ? 'log-ok' : 'log-dead';
      var vt = d.has_scotle ? ' [scotle.org ✓]' : '';
      var mt = d.ms ? ' ('+d.ms+'ms)' : '';
      line.textContent = (d.ok ? '✓ LIVE  ' : '✗ DEAD  ') + '['+item.plat+'] ' + item.title.substring(0,55) + vt + mt;
      setTimeout(function(){ runBulk(i+1, live, dead, vfy); }, 300);
    })
    .catch(function() {
      dead++;
      line.className = 'log-dead';
      line.textContent = '✗ ERROR — ' + item.url;
      setTimeout(function(){ runBulk(i+1, live, dead, vfy); }, 300);
    });
}

// ── Init ─────────────────────────────────────────────────────────────────
window.onload = function() {
  filterLive();
  filterAll();
  buildPager('lv-tbl','lv-pager', document.querySelectorAll('#lv-body tr').length);
  buildPager('al-tbl','al-pager', document.querySelectorAll('#al-body tr').length);
};
</script>
</body>
</html>"""

# ─── Auto-open browser + start server ─────────────────────────────────────

if __name__ == "__main__":
    PORT = 5050
    print("\n" + "="*50)
    print("  Scotle.org Backlink CRM")
    print(f"  Opening: http://localhost:{PORT}")
    print("  Press Ctrl+C to stop")
    print("="*50 + "\n")
    threading.Timer(1.2, lambda: webbrowser.open(f"http://localhost:{PORT}")).start()
    app.run(debug=False, port=PORT, threaded=True)
