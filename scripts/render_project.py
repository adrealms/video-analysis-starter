#!/usr/bin/env python3
"""Render a video-analysis project folder into an interactive HTML dashboard.

For a given folder, produces:
- <name>.mp4         (converted from .mov if needed)
- <name>.thumb.jpg   (single thumbnail per video — embedded if present, else frame at 20%)
- <name>.html        (interactive per-video view: sticky player + clickable timestamps)
- dashboard_<folder>.html  (project-level overview with cards + cross-stats)

Usage:
  python3 render_project.py <folder>
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

VIDEO_EXTS = {".mp4", ".mov", ".webm", ".m4v", ".mkv"}
ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------- ffmpeg helpers

def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def video_duration(path: Path) -> float:
    r = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(path)])
    try:
        return float(r.stdout.strip())
    except Exception:
        return 0.0


def convert_mov_to_mp4(mov: Path) -> Path:
    """Convert .mov to .mp4 for browser compatibility. Keeps original."""
    mp4 = mov.with_suffix(".mp4")
    if mp4.exists():
        return mp4
    print(f"  converting {mov.name} → {mp4.name}")
    run(["ffmpeg", "-y", "-i", str(mov), "-c:v", "libx264", "-c:a", "aac",
         "-movflags", "+faststart", str(mp4)])
    return mp4


def extract_thumbnail(video: Path, out: Path):
    """Try embedded thumbnail first, fall back to frame at 20% duration."""
    if out.exists():
        return
    # Try embedded cover art
    r = run(["ffmpeg", "-y", "-i", str(video), "-map", "0:v", "-map", "-0:V",
             "-c", "copy", "-f", "image2", str(out)])
    if out.exists() and out.stat().st_size > 1000:
        return
    # Fall back to 20% frame
    dur = video_duration(video)
    seek = max(0.5, dur * 0.2) if dur > 0 else 1.5
    run(["ffmpeg", "-y", "-ss", f"{seek:.2f}", "-i", str(video),
         "-frames:v", "1", "-q:v", "2", str(out)])


# ---------------------------------------------------------------- markdown parsing

def parse_md(md_path: Path) -> dict:
    """Parse a Stage 2 .md file into structured data for the HTML renderer."""
    text = md_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    meta = {
        "filename": md_path.stem,
        "brand": "",
        "concept_type": "",
        "format": "",
        "tone": "",
        "vertical": "",
        "key_takeaway": "",
        "sections": [],
    }

    # Parse top-block (bold-label fields)
    for line in lines:
        m = re.match(r"\*\*([^:]+):\*\*\s*(.+)", line)
        if not m:
            continue
        label = m.group(1).strip().lower()
        value = m.group(2).strip()
        if "brand" in label:
            meta["brand"] = value
        elif "concept" in label:
            meta["concept_type"] = value
        elif "format" in label:
            meta["format"] = value
        elif "tone" in label:
            meta["tone"] = value
        elif "vertical" in label:
            meta["vertical"] = value
        elif "key takeaway" in label:
            meta["key_takeaway"] = value

    # Parse sections (## heading + following table)
    section_re = re.compile(r"^##\s+(.+?)\s*(?:\(([^)]+)\))?\s*$")
    current_section = None
    table_lines = []
    sections = []

    for line in lines:
        sm = section_re.match(line)
        if sm:
            if current_section and table_lines:
                sections.append({**current_section, "rows": _parse_table(table_lines)})
            title = sm.group(1).strip()
            timerange = sm.group(2) or ""
            current_section = {"title": title, "timerange": timerange}
            table_lines = []
            continue
        if current_section is not None:
            if line.strip().startswith("|"):
                table_lines.append(line)
    if current_section and table_lines:
        sections.append({**current_section, "rows": _parse_table(table_lines)})

    # Only keep top-level sections we want (Hook / Body / CTA, skip generic "Notes")
    meta["sections"] = [s for s in sections if s["rows"]]
    return meta


def _parse_table(lines):
    """Parse markdown table into list of dicts."""
    rows = []
    if len(lines) < 2:
        return rows
    # Header
    header_cells = [c.strip() for c in lines[0].strip().strip("|").split("|")]
    # Skip separator line (index 1)
    for line in lines[2:]:
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != len(header_cells):
            continue
        rows.append(dict(zip(header_cells, cells)))
    return rows


# ---------------------------------------------------------------- timestamp utils

TIME_RE = re.compile(r"(\d+(?:\.\d+)?)\s*s?\s*[–-]\s*(\d+(?:\.\d+)?)\s*s?")
SINGLE_TIME_RE = re.compile(r"(\d+(?:\.\d+)?)\s*s")


def parse_first_timestamp(time_cell: str) -> float | None:
    """Return the first numeric seconds value found in the Time cell."""
    if not time_cell:
        return None
    m = TIME_RE.search(time_cell)
    if m:
        return float(m.group(1))
    m = SINGLE_TIME_RE.search(time_cell)
    if m:
        return float(m.group(1))
    return None


def render_clickable_time(time_cell: str) -> str:
    """Turn '0.0–2.1s' into clickable spans that seek the video."""
    if not time_cell:
        return ""
    def replace(m):
        start = m.group(1)
        end = m.group(2)
        return f'<a class="ts" data-t="{start}">{start}s</a><span class="dash">–</span><a class="ts" data-t="{end}">{end}s</a>'
    out = TIME_RE.sub(replace, time_cell)
    if out == time_cell:
        out = SINGLE_TIME_RE.sub(lambda m: f'<a class="ts" data-t="{m.group(1)}">{m.group(1)}s</a>', time_cell)
    return out


# ---------------------------------------------------------------- HTML rendering

BRAND_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700;800&family=DM+Sans:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: 'DM Sans', system-ui, sans-serif;
  background: #0c0c0c;
  color: #f0ede8;
  line-height: 1.5;
  -webkit-font-smoothing: antialiased;
}
a { color: #FFB400; text-decoration: none; }
a:hover { text-decoration: underline; }
h1, h2, h3 { font-family: 'Barlow Condensed', sans-serif; font-weight: 700; line-height: 1.1; }
code, .mono { font-family: 'JetBrains Mono', monospace; }
strong, b { font-weight: 700; }
em, i { font-style: italic; }
"""


def render_video_html(meta: dict, video_filename: str, folder_name: str) -> str:
    """Per-video HTML: sticky player + scrollable analysis with clickable timestamps."""
    sections_html = ""
    for section in meta["sections"]:
        title = section["title"]
        timerange = section["timerange"]
        rows = section["rows"]
        if not rows:
            continue
        # Pick columns we care about — use the header order from the first row
        cols = list(rows[0].keys())
        head_cells = "".join(f"<th>{c}</th>" for c in cols)
        body_rows = ""
        for r in rows:
            cells = ""
            for c in cols:
                val = r.get(c, "")
                if c.lower() == "time":
                    val = render_clickable_time(val)
                cells += f"<td data-col=\"{c.lower()}\">{val}</td>"
            body_rows += f"<tr>{cells}</tr>"
        timerange_html = f' <span class="timerange">({timerange})</span>' if timerange else ""
        sections_html += f"""
        <section class="block">
          <h2>{title}{timerange_html}</h2>
          <table class="analysis">
            <thead><tr>{head_cells}</tr></thead>
            <tbody>{body_rows}</tbody>
          </table>
        </section>
        """

    # Header meta items (grid format)
    meta_items = []
    for label, key in [("Concept", "concept_type"), ("Brand", "brand"), ("Format", "format"),
                       ("Tone", "tone"), ("Vertical", "vertical")]:
        v = meta.get(key)
        if v:
            meta_items.append(f'<div class="meta-cell"><div class="meta-label">{label}</div><div class="meta-value">{v}</div></div>')
    meta_grid = "\n".join(meta_items)

    takeaway_html = ""
    if meta.get("key_takeaway"):
        takeaway_html = f'<div class="takeaway"><div class="takeaway-label">Key takeaway</div><div class="takeaway-text">{meta["key_takeaway"]}</div></div>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{meta["filename"]}</title>
<style>
{BRAND_CSS}

.page {{ max-width: 1600px; margin: 0 auto; padding: 28px 32px 60px; }}
.back {{ font-size: 13px; letter-spacing: 0.05em; text-transform: uppercase; color: #888; margin-bottom: 20px; display: inline-block; }}
.back:hover {{ color: #FFB400; text-decoration: none; }}

/* Header above everything — scrolls naturally with page */
.header-card {{
  padding: 26px 30px;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 12px;
  margin-bottom: 32px;
  position: relative;
}}
.header-card::before {{ content: ""; position: absolute; top: 0; left: 0; right: 0; height: 3px; background: linear-gradient(90deg, #FFB400, transparent); border-radius: 12px 12px 0 0; }}
.header-card .filename {{ font-family: 'Barlow Condensed', sans-serif; font-weight: 700; font-size: 28px; color: #fff; margin-bottom: 18px; word-break: break-word; }}
.meta-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 14px 28px; }}
.meta-cell .meta-label {{ font-size: 10px; letter-spacing: 0.18em; text-transform: uppercase; color: #FFB400; font-weight: 600; margin-bottom: 4px; }}
.meta-cell .meta-value {{ color: #f0ede8; font-size: 14px; line-height: 1.45; }}
.takeaway {{ margin-top: 18px; padding: 14px 18px; background: rgba(255,180,0,0.07); border-left: 3px solid #FFB400; border-radius: 4px; }}
.takeaway-label {{ font-size: 10px; letter-spacing: 0.18em; text-transform: uppercase; color: #FFB400; font-weight: 600; margin-bottom: 6px; }}
.takeaway-text {{ font-size: 14px; line-height: 1.55; color: #f0ede8; }}

/* Two-column layout below header */
.layout {{ display: grid; grid-template-columns: minmax(360px, 38%) 1fr; gap: 36px; align-items: start; }}

.player-pane {{ position: sticky; top: 24px; align-self: start; }}
.player-pane video {{
  width: 100%;
  max-height: 80vh;
  display: block;
  border-radius: 10px;
  background: #000;
  box-shadow: 0 4px 30px rgba(0,0,0,0.5);
}}

.analysis-pane {{ min-width: 0; }}
section.block {{ margin-bottom: 36px; }}
section.block h2 {{ font-size: 28px; color: #fff; margin-bottom: 14px; }}
section.block h2 .timerange {{ font-family: 'DM Sans', sans-serif; font-weight: 400; font-size: 14px; color: #888; letter-spacing: 0.04em; }}

table.analysis {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
table.analysis th {{
  text-align: left;
  padding: 10px 12px;
  font-family: 'Barlow Condensed', sans-serif; font-weight: 700;
  font-size: 12px; letter-spacing: 0.1em; text-transform: uppercase;
  color: #888; border-bottom: 1px solid rgba(255,180,0,0.4);
  white-space: nowrap;
}}
table.analysis td {{
  padding: 12px 12px;
  border-bottom: 1px solid rgba(255,255,255,0.05);
  vertical-align: top;
  color: #d8d6d2;
}}
table.analysis td[data-col="time"] {{ white-space: nowrap; }}
table.analysis td[data-col="why it works"] {{ color: #c0bdb8; font-style: italic; }}
table.analysis td[data-col="overlay"] {{ font-family: 'JetBrains Mono', monospace; font-size: 12px; color: #FFB400; }}
table.analysis td[data-col="pattern"] {{ color: #FFB400; }}
table.analysis td[data-col="script"] {{ color: #f0ede8; }}

a.ts {{
  color: #FFB400; cursor: pointer; font-weight: 600;
  border-bottom: 1px dashed rgba(255,180,0,0.5);
}}
a.ts:hover {{ background: rgba(255,180,0,0.12); text-decoration: none; border-bottom-color: #FFB400; }}
span.dash {{ color: #888; margin: 0 4px; }}

@media (max-width: 1000px) {{
  .layout {{ grid-template-columns: 1fr; }}
  .player-pane {{ position: static; }}
  .player-pane video {{ max-height: 50vh; }}
}}
</style>
</head>
<body>
<div class="page">
  <a class="back" href="../dashboard_{folder_name}.html">← back to dashboard</a>

  <div class="header-card">
    <div class="filename">{meta["filename"]}</div>
    <div class="meta-grid">
      {meta_grid}
    </div>
    {takeaway_html}
  </div>

  <div class="layout">
    <div class="player-pane">
      <video id="player" controls preload="metadata">
        <source src="{video_filename}" type="video/mp4">
        Your browser does not support the video tag.
      </video>
    </div>

    <div class="analysis-pane">
      {sections_html}
    </div>
  </div>
</div>

<script>
(function() {{
  var player = document.getElementById('player');
  document.querySelectorAll('a.ts').forEach(function(a) {{
    a.addEventListener('click', function(e) {{
      e.preventDefault();
      var t = parseFloat(a.getAttribute('data-t'));
      if (!isNaN(t)) {{
        player.currentTime = t;
        player.play();
      }}
    }});
  }});
}})();
</script>
</body>
</html>"""


def render_dashboard_html(folder_name: str, videos: list) -> str:
    """Project dashboard with cards and cross-stats."""
    # Cross-stats
    concept_counts = Counter(v["meta"]["concept_type"] for v in videos if v["meta"].get("concept_type"))
    vertical_counts = Counter(v["meta"]["vertical"] for v in videos if v["meta"].get("vertical"))
    # Patterns from all rows of all videos
    pattern_counts = Counter()
    for v in videos:
        seen_patterns = set()
        for section in v["meta"]["sections"]:
            for row in section["rows"]:
                pat = row.get("Pattern") or row.get("pattern") or ""
                # Strip "(N/M)" pagination markers
                pat_clean = re.sub(r"\s*\(\d+/\d+\)", "", pat).strip()
                # Split on "+" if combined patterns
                for p in re.split(r"\s*\+\s*", pat_clean):
                    p = p.strip()
                    if p and p not in seen_patterns:
                        seen_patterns.add(p)
        for p in seen_patterns:
            pattern_counts[p] += 1

    def fmt_count(counter, top_n=5):
        items = counter.most_common(top_n)
        return " · ".join(f"{name} <span class='count'>({n})</span>" for name, n in items)

    cards_html = ""
    for v in sorted(videos, key=lambda x: x["meta"]["filename"]):
        meta = v["meta"]
        thumb = v["thumb_filename"]
        html_link = v["html_filename"]
        concept = meta.get("concept_type") or "—"
        brand = meta.get("brand") or "—"
        fmt = meta.get("format") or "—"
        vertical = meta.get("vertical") or ""
        takeaway = meta.get("key_takeaway") or ""
        # Truncate takeaway for card
        if len(takeaway) > 220:
            takeaway = takeaway[:215] + "…"
        cards_html += f"""
        <a class="card" href="{html_link}">
          <div class="card-thumb"><img src="{thumb}" alt="" loading="lazy"></div>
          <div class="card-body">
            <div class="card-concept">{concept}</div>
            <div class="card-filename">{meta["filename"]}</div>
            <div class="card-meta">
              <div><span class="lbl">Brand</span> {brand}</div>
              <div><span class="lbl">Format</span> {fmt}</div>
              {f'<div><span class="lbl">Vertical</span> {vertical}</div>' if vertical else ""}
            </div>
            <div class="card-takeaway">{takeaway}</div>
          </div>
        </a>
        """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{folder_name} · video analysis dashboard</title>
<style>
{BRAND_CSS}

.page {{ max-width: 1500px; margin: 0 auto; padding: 40px 32px 80px; }}

header {{ margin-bottom: 40px; padding-bottom: 28px; border-bottom: 1px solid rgba(255,255,255,0.08); }}
header h1 {{ font-size: 56px; font-weight: 800; color: #fff; letter-spacing: -0.01em; }}
header h1 .gold {{ color: #FFB400; }}
header .sub {{ margin-top: 8px; font-size: 16px; color: #888; }}

.stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 18px; margin-bottom: 50px; }}
.stat {{ padding: 22px 24px; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.07); border-radius: 12px; }}
.stat::before {{ content: ""; display: block; height: 2px; width: 50%; background: linear-gradient(90deg, #FFB400, transparent); margin: -22px -24px 16px; }}
.stat-label {{ font-size: 11px; letter-spacing: 0.18em; text-transform: uppercase; color: #FFB400; font-weight: 600; margin-bottom: 10px; }}
.stat-value {{ font-size: 14px; color: #d8d6d2; line-height: 1.6; }}
.stat-value .count {{ color: #888; }}

.cards {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 22px; }}
.card {{
  display: flex; flex-direction: column;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 12px;
  overflow: hidden;
  color: inherit;
  transition: transform 0.15s ease, border-color 0.15s ease;
}}
.card:hover {{ transform: translateY(-2px); border-color: rgba(255,180,0,0.35); text-decoration: none; }}
.card-thumb {{ aspect-ratio: 9/16; background: #000; overflow: hidden; }}
.card-thumb img {{ width: 100%; height: 100%; object-fit: cover; display: block; }}
.card-body {{ padding: 16px 18px 20px; flex: 1; display: flex; flex-direction: column; }}
.card-concept {{
  font-family: 'Barlow Condensed', sans-serif; font-weight: 700;
  font-size: 16px; letter-spacing: 0.04em; text-transform: uppercase;
  color: #FFB400; margin-bottom: 8px;
}}
.card-filename {{ font-size: 11px; color: #666; font-family: 'JetBrains Mono', monospace; word-break: break-all; margin-bottom: 12px; }}
.card-meta {{ font-size: 13px; color: #d8d6d2; line-height: 1.6; margin-bottom: 12px; }}
.card-meta .lbl {{ color: #888; text-transform: uppercase; letter-spacing: 0.06em; font-size: 10px; font-weight: 600; margin-right: 4px; }}
.card-takeaway {{ font-size: 12px; color: #b0adaa; line-height: 1.55; font-style: italic; flex: 1; }}
</style>
</head>
<body>
<div class="page">
  <header>
    <h1>{folder_name} <span class="gold">·</span> video analysis</h1>
    <div class="sub">{len(videos)} video{"s" if len(videos) != 1 else ""} analyzed</div>
  </header>

  <div class="stats">
    <div class="stat">
      <div class="stat-label">Top concepts</div>
      <div class="stat-value">{fmt_count(concept_counts) or "—"}</div>
    </div>
    <div class="stat">
      <div class="stat-label">Top patterns</div>
      <div class="stat-value">{fmt_count(pattern_counts, 6) or "—"}</div>
    </div>
    <div class="stat">
      <div class="stat-label">Verticals</div>
      <div class="stat-value">{fmt_count(vertical_counts) or "—"}</div>
    </div>
  </div>

  <div class="cards">
    {cards_html}
  </div>
</div>
</body>
</html>"""


# ---------------------------------------------------------------- main

def resolve_folder(arg: str) -> Path:
    p = Path(arg)
    if p.is_absolute() and p.exists():
        return p
    for base in [ROOT, ROOT / "videos", Path.cwd()]:
        c = base / arg
        if c.exists():
            return c
    raise SystemExit(f"Folder not found: {arg}")


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("folder", help="Project folder (relative to videos/ or absolute)")
    args = parser.parse_args()

    folder = resolve_folder(args.folder)
    folder_name = folder.name
    print(f"\n📁 Rendering project: {folder}\n")

    # Collect videos — but dedupe: if foo.mov AND foo.mp4 both exist, prefer .mp4 (the converted one)
    all_videos = sorted([p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in VIDEO_EXTS])
    mp4_stems = {p.stem for p in all_videos if p.suffix.lower() == ".mp4"}
    raw_videos = [p for p in all_videos
                  if not (p.suffix.lower() != ".mp4" and p.stem in mp4_stems)]
    if not raw_videos:
        print("No videos found.")
        return

    # Subfolders for organized output
    analysis_dir = folder / "analysis"
    dashboard_dir = folder / "dashboard"
    data_dir = dashboard_dir / "data"
    analysis_dir.mkdir(exist_ok=True)
    dashboard_dir.mkdir(exist_ok=True)
    data_dir.mkdir(exist_ok=True)

    processed = []
    for raw in raw_videos:
        # Convert .mov → .mp4 if needed
        if raw.suffix.lower() == ".mov":
            mp4 = convert_mov_to_mp4(raw)
        else:
            mp4 = raw

        stem = mp4.stem
        md_path = analysis_dir / f"{stem}.md"
        if not md_path.exists():
            md_path = analysis_dir / f"{raw.stem}.md"
        if not md_path.exists():
            print(f"  ⚠️  no .md in analysis/ for {mp4.name} — skipping")
            continue

        # Thumbnails + per-video HTML live in dashboard/data/
        thumb_path = data_dir / f"{stem}.thumb.jpg"
        extract_thumbnail(mp4, thumb_path)
        if not thumb_path.exists():
            print(f"  ⚠️  thumbnail extraction failed for {mp4.name}")
            continue

        meta = parse_md(md_path)
        meta["filename"] = stem

        # Per-video HTML lives in dashboard/data/ → video is 2 levels up
        html_path = data_dir / f"{stem}.html"
        html_path.write_text(
            render_video_html(meta, f"../../{mp4.name}", folder_name),
            encoding="utf-8"
        )
        print(f"  ✓ {stem}")

        processed.append({
            "meta": meta,
            "video_filename": mp4.name,
            "thumb_filename": f"data/{thumb_path.name}",
            "html_filename": f"data/{html_path.name}",
        })

    # Dashboard at dashboard/ root, links into data/
    dashboard_path = dashboard_dir / f"dashboard_{folder_name}.html"
    dashboard_path.write_text(render_dashboard_html(folder_name, processed), encoding="utf-8")

    print(f"\n✓ Done. {len(processed)} video(s) rendered.")
    print(f"📊 Dashboard: {dashboard_path}")
    print(f"   Open in browser: file://{dashboard_path}\n")


if __name__ == "__main__":
    main()
