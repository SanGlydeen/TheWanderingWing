#!/usr/bin/env python3
"""Build /identify/ — the photographs I need Samuel to place.

Temporary, like preview.py. Delete both this and public/identify/ once the
library reorganisation has run.

    python3 identify.py
"""

import html
import re
import subprocess
from collections import defaultdict
from pathlib import Path

import assignments
import build

LIB = Path(
    "/Users/samuelsalesas/Library/Mobile Documents/com~apple~CloudDocs"
    "/Files/Personal/Hobbies/Photography/Drone/The Wandering Wing"
)
OUT = build.ROOT / "public" / "identify"
THUMBS = OUT / "img"

# date-group -> (my guess, needs confirming vs unknown)
GUESSES = {
    "2024-05": ("Segovia", "guess"),
    "2024-07": ("Lago Maggiore", "guess"),
    "2024-08": (None, "unknown"),
    "2024-11": (None, "unknown"),
    "2024-12": ("Chongqing", "guess"),
    "2025-07": ("Menorca", "guess"),
    "2025-08": ("Mount Siguniang", "guess"),
    "2025-09": ("London", "guess"),
    "2025-12": (None, "unknown"),
    "2026-05": (None, "unknown"),
}

# Already in the library but never placed.
STRAYS = [LIB / "Highlights" / "IMG_3133.JPG",
          LIB / "Highlights" / "DJI_20241130155638_0141_D.JPG"]


def taken(path):
    r = subprocess.run(["sips", "-g", "creation", str(path)],
                       capture_output=True, text=True)
    m = re.match(r"DJI_(\d{4})(\d{2})(\d{2})", path.name)
    if m:
        return f"{m.group(1)}-{m.group(2)}"
    for line in r.stdout.splitlines():
        line = line.strip()
        if line.startswith("creation:"):
            return line.split(":", 1)[1].strip()[:7].replace(":", "-")
    return "unknown"


def thumb(path, name):
    dest = THUMBS / f"{name}.jpg"
    if not dest.exists():
        subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions",
                        "72", "-Z", "900", str(path), "--out", str(dest)],
                       capture_output=True)
    return f"/identify/img/{name}.jpg"


def main():
    THUMBS.mkdir(parents=True, exist_ok=True)

    lookup = {}
    for f in LIB.rglob("*"):
        if f.is_file() and not f.name.startswith("."):
            lookup.setdefault(f.stem, f)

    sections, n = [], 0
    for title, meta in assignments.OPEN.items():
        cells = []
        for stem in meta["stems"]:
            src_file = lookup.get(stem)
            if not src_file:
                continue
            n += 1
            src = thumb(src_file, f"open{n:02d}")
            cells.append(
                f'<figure><img src="{src}" alt="" loading="lazy">'
                f'<figcaption>{html.escape(src_file.name)}</figcaption></figure>')
        sections.append(f"""
<section class="grp grp--unknown">
  <h2>{html.escape(title)}</h2>
  <p class="q">{html.escape(meta["question"])}</p>
  <div class="shots">{''.join(cells)}</div>
</section>""")

    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>Two questions left</title>
<link rel="icon" href="/favicon.png" type="image/png">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400;500&display=swap">
<link rel="stylesheet" href="{build.CSS_HREF}">
<style>
  body {{ background: var(--paper); }}
  .idwrap {{ width: min(100% - 2rem, 1100px); margin: 0 auto;
             padding: clamp(2rem, 6vw, 4rem) 0 6rem; }}
  .grp {{ margin-bottom: clamp(2rem, 5vw, 3rem); padding: 1.6rem;
          background: #fff8ef; border: 1px solid rgba(200, 120, 40, 0.3);
          border-radius: 3px; }}
  .grp h2 {{ margin-bottom: 0.3rem; font-size: clamp(1.5rem, 3vw, 2rem); }}
  .q {{ color: #6b4a22; max-width: 62ch; margin-bottom: 1.4rem; }}
  .shots {{ display: grid; gap: 0.6rem;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); }}
  .shots figure {{ margin: 0; }}
  .shots img {{ width: 100%; aspect-ratio: 3/4; object-fit: cover;
                border-radius: 2px; background: var(--cream-deep); }}
  .shots figcaption {{ font-size: 0.72rem; color: var(--muted);
                       margin-top: 0.3rem; word-break: break-all; }}
  .done {{ background: var(--cream); border: 0; padding: 1.4rem 1.6rem;
           border-radius: 3px; }}
</style>
</head>
<body>
<div class="idwrap">
  <h1>Two questions left</h1>
  <p class="measure">Everything else is filed — 95 photographs across 11
  places. These 7 are the last of it.</p>
  {''.join(sections)}
  <p class="done"><strong>Once these are answered</strong> I run the
  migration: every photograph filed by place with a readable name, 14
  byte-identical duplicates dropped, and all 59 new portraits folded in.</p>
  <p><a class="link-arrow" href="/">Back to the site</a></p>
</div>
</body>
</html>
"""
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "index.html").write_text(page)
    print(f"wrote /identify/ — {n} photographs, {len(assignments.OPEN)} questions")


if __name__ == "__main__":
    main()
