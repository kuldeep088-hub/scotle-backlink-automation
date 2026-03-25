"""
export_report.py  —  Scotle.org Backlink Report
Run:  python export_report.py
Out:  data/scotle_backlink_report.html
"""

import os, csv, json, webbrowser
from datetime import datetime

BASE       = os.path.dirname(os.path.abspath(__file__))
RECENT_CSV = os.path.join(BASE, "data", "backlinks_recent30.csv")
OUT_PATH   = os.path.join(BASE, "data", "scotle_backlink_report.html")

DA_MAP = {
    "blogger":100,"tumblr":98,"hashnode":92,"devto":90,"dev.to":90,
    "writeas":69,"write.as":69,"hackmd":65,"dpaste":55,"bytebin":50,
    "substack":89,"medium":95,"livejournal":93,
}

def load_recent30():
    rows = []
    with open(RECENT_CSV, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            plat = r.get("Platform","")
            rows.append({
                "no":       0,
                "platform": plat,
                "da":       DA_MAP.get(plat.lower(), 0),
                "title":    r.get("Title",""),
                "url":      r.get("URL",""),
                "anchor":   r.get("Anchor Text",""),
                "date":     r.get("Date Published","")[:10],
                "words":    r.get("Word Count",""),
                "verified": r.get("Verified","False"),
            })
    for i, r in enumerate(rows):
        r["no"] = i + 1
    return rows

if __name__ == "__main__":
    links     = load_recent30()
    generated = datetime.now().strftime("%d %b %Y, %H:%M")

    # Build table rows HTML
    rows_html = ""
    for r in links:
        da_cls  = "da-hi" if r["da"] >= 90 else "da-mid" if r["da"] >= 60 else "da-lo"
        vfy     = str(r["verified"]).lower() == "true"
        vfy_html= '<span class="vy">&#10003;</span>' if vfy else '<span class="vn">&mdash;</span>'
        rows_html += (
            f'<tr>'
            f'<td class="n">{r["no"]}</td>'
            f'<td><span class="pt">{r["platform"]}</span></td>'
            f'<td><span class="da {da_cls}">{r["da"] or "?"}</span></td>'
            f'<td><span class="tt" title="{r["title"]}">{r["title"]}</span></td>'
            f'<td><a class="lnk" href="{r["url"]}" target="_blank">{r["url"]}</a></td>'
            f'<td class="sm">{r["anchor"]}</td>'
            f'<td class="sm">{r["date"]}</td>'
            f'<td class="sm">{r["words"]}</td>'
            f'<td>{vfy_html}</td>'
            f'</tr>\n'
        )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Scotle.org — 30 Backlinks</title>
<style>
* {{ box-sizing:border-box; margin:0; padding:0; }}
body {{ font-family:'Segoe UI',system-ui,sans-serif; background:#07090f; color:#e2e8f0; padding:28px 24px; }}
.header {{ margin-bottom:24px; }}
.header h1 {{ font-size:20px; font-weight:700; color:#f8fafc; margin-bottom:4px; }}
.header p  {{ font-size:13px; color:#64748b; }}
.header p span {{ color:#94a3b8; }}

.ctrl {{ display:flex; gap:8px; align-items:center; flex-wrap:wrap; margin-bottom:14px; }}
.inp  {{ background:#0d1117; border:1px solid #1e2a3a; color:#e2e8f0;
         padding:7px 12px; border-radius:7px; font-size:13px; outline:none; }}
.inp:focus {{ border-color:#3b82f6; }}
.inp-search {{ width:260px; }}
.cnt {{ font-size:12px; color:#64748b; margin-left:auto; }}
.dl-btn {{ padding:7px 16px; background:#065f46; color:#34d399;
           border:1px solid #059669; border-radius:7px; cursor:pointer;
           font-size:12px; font-weight:500; }}
.dl-btn:hover {{ opacity:.85; }}

.wrap {{ overflow-x:auto; }}
table {{ width:100%; border-collapse:collapse; font-size:13px; }}
th {{
  text-align:left; font-size:11px; color:#64748b;
  text-transform:uppercase; letter-spacing:.05em;
  padding:0 12px 12px; cursor:pointer; user-select:none; white-space:nowrap;
}}
th:hover {{ color:#94a3b8; }}
td {{ padding:9px 12px; border-top:1px solid #1e2a3a; vertical-align:middle; }}
tr:hover td {{ background:#0d1421; }}

.n   {{ color:#475569; }}
.pt  {{ display:inline-block; padding:2px 8px; border-radius:4px; font-size:11px;
        background:#1e2a3a; color:#94a3b8; text-transform:capitalize; }}
.da  {{ display:inline-block; padding:2px 8px; border-radius:4px; font-size:11px; font-weight:700; }}
.da-hi  {{ background:#052e16; color:#34d399; }}
.da-mid {{ background:#0c2048; color:#60a5fa; }}
.da-lo  {{ background:#292524; color:#d97706; }}
.tt  {{ display:block; max-width:260px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; color:#94a3b8; }}
.lnk {{ color:#3b82f6; text-decoration:none; display:block; max-width:280px;
        overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }}
.lnk:hover {{ color:#93c5fd; text-decoration:underline; }}
.sm  {{ font-size:12px; color:#64748b; max-width:150px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }}
.vy  {{ color:#34d399; font-size:16px; }}
.vn  {{ color:#374151; font-size:16px; }}

.footer {{ margin-top:24px; font-size:12px; color:#374151; text-align:center; }}
</style>
</head>
<body>

<div class="header">
  <h1>Scotle.org — Recent 30 Backlinks</h1>
  <p>Target: <span>scotle.org</span> &nbsp;|&nbsp; Generated: <span>{generated}</span> &nbsp;|&nbsp; Source: <span>data/backlinks_recent30.csv</span></p>
</div>

<div class="ctrl">
  <input class="inp inp-search" id="q" type="text" placeholder="Search title, URL, anchor&hellip;" oninput="filter()">
  <select class="inp" id="fp" onchange="filter()"><option value="">All Platforms</option></select>
  <select class="inp" id="fv" onchange="filter()">
    <option value="">All</option>
    <option value="true">Verified Only</option>
    <option value="false">Not Verified</option>
  </select>
  <span class="cnt" id="cnt">30 links</span>
  <button class="dl-btn" onclick="dlCSV()">&#8659; Download CSV</button>
</div>

<div class="wrap">
<table id="tbl">
  <thead><tr>
    <th onclick="srt(0)"># &uarr;&darr;</th>
    <th onclick="srt(1)">Platform &uarr;&darr;</th>
    <th onclick="srt(2)">DA &uarr;&darr;</th>
    <th onclick="srt(3)">Title &uarr;&darr;</th>
    <th>URL</th>
    <th onclick="srt(5)">Anchor &uarr;&darr;</th>
    <th onclick="srt(6)">Date &uarr;&darr;</th>
    <th onclick="srt(7)">Words &uarr;&darr;</th>
    <th onclick="srt(8)">Verified &uarr;&darr;</th>
  </tr></thead>
  <tbody id="tb">{rows_html}</tbody>
</table>
</div>

<div class="footer">Scotle.org Backlink Report &bull; {generated} &bull; 30 backlinks</div>

<script>
var DATA = {json.dumps(links, ensure_ascii=False)};

// Populate platform filter
(function() {{
  var sel = document.getElementById('fp'), seen = {{}};
  DATA.forEach(function(r) {{
    if (!seen[r.platform]) {{
      seen[r.platform] = 1;
      var o = document.createElement('option');
      o.value = r.platform; o.textContent = r.platform;
      sel.appendChild(o);
    }}
  }});
}})();

function filter() {{
  var q    = document.getElementById('q').value.toLowerCase();
  var plat = document.getElementById('fp').value.toLowerCase();
  var vfy  = document.getElementById('fv').value.toLowerCase();
  var rows = document.querySelectorAll('#tb tr');
  var cnt  = 0;
  rows.forEach(function(row) {{
    var cells = row.cells;
    var text  = row.innerText.toLowerCase();
    var rplat = (cells[1] ? cells[1].innerText.toLowerCase() : '');
    var rvfy  = (cells[8] ? (cells[8].innerText.trim() === '✓' ? 'true' : 'false') : '');
    var show  = (!q || text.indexOf(q) >= 0)
             && (!plat || rplat === plat)
             && (!vfy  || rvfy === vfy);
    row.style.display = show ? '' : 'none';
    if (show) cnt++;
  }});
  document.getElementById('cnt').textContent = cnt + ' links';
}}

var _s = {{}};
function srt(col) {{
  var key = 'c'+col; var asc = !_s[key]; _s[key] = asc;
  var tb  = document.getElementById('tb');
  var rows = Array.prototype.slice.call(tb.querySelectorAll('tr'));
  rows.sort(function(a,b) {{
    var at = a.cells[col] ? a.cells[col].innerText.trim() : '';
    var bt = b.cells[col] ? b.cells[col].innerText.trim() : '';
    var an = parseFloat(at), bn = parseFloat(bt);
    if (!isNaN(an) && !isNaN(bn)) return asc ? an-bn : bn-an;
    return asc ? at.localeCompare(bt) : bt.localeCompare(at);
  }});
  rows.forEach(function(r) {{ tb.appendChild(r); }});
}}

function dlCSV() {{
  var cols = ['no','platform','da','title','url','anchor','date','words','verified'];
  var lines = [cols.join(',')];
  DATA.forEach(function(r) {{
    lines.push(cols.map(function(c) {{
      return '"' + (r[c]||'').toString().replace(/"/g,'""') + '"';
    }}).join(','));
  }});
  var a = document.createElement('a');
  a.href = 'data:text/csv;charset=utf-8,' + encodeURIComponent(lines.join('\\n'));
  a.download = 'scotle_backlinks_recent30.csv';
  document.body.appendChild(a); a.click(); document.body.removeChild(a);
}}
</script>
</body>
</html>"""

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\nSaved: data/scotle_backlink_report.html  ({os.path.getsize(OUT_PATH)//1024} KB)")
    print(f"Backlinks: {len(links)}  |  Share this one file.\n")
    webbrowser.open("file:///" + OUT_PATH.replace("\\", "/"))
