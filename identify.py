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

    loose = [p for p in LIB.iterdir()
             if p.is_file() and not p.name.startswith(".")
             and p.suffix.lower() in (".jpg", ".jpeg", ".png")]

    groups = defaultdict(list)
    for p in sorted(loose):
        groups[taken(p)].append(p)

    sections = []
    n = 0
    for date in sorted(groups):
        guess, kind = GUESSES.get(date, (None, "unknown"))
        shots = groups[date]
        cells = []
        for p in shots:
            n += 1
            src = thumb(p, f"g{n:03d}")
            cells.append(
                f'<figure><img src="{src}" alt="" loading="lazy">'
                f'<figcaption>{html.escape(p.name)}</figcaption></figure>')
        head = (f'<span class="tag tag--guess">my guess: {html.escape(guess)}</span>'
                if guess else
                '<span class="tag tag--unknown">I don\'t know — please tell me</span>')
        sections.append(f"""
<section class="grp{' grp--unknown' if not guess else ''}">
  <h2>{date} <small>{len(shots)} photo{'s' if len(shots) != 1 else ''}</small></h2>
  {head}
  <div class="shots">{''.join(cells)}</div>
</section>""")

    stray_cells = []
    for p in STRAYS:
        if not p.exists():
            continue
        n += 1
        src = thumb(p, f"g{n:03d}")
        stray_cells.append(
            f'<figure><img src="{src}" alt="" loading="lazy">'
            f'<figcaption>{html.escape(p.name)}</figcaption></figure>')
    if stray_cells:
        sections.append(f"""
<section class="grp grp--unknown">
  <h2>Already on the site, never placed <small>{len(stray_cells)} photos</small></h2>
  <span class="tag tag--unknown">I don't know — please tell me</span>
  <div class="shots">{''.join(stray_cells)}</div>
</section>""")

    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>Which places are these?</title>
<link rel="icon" href="/favicon.png" type="image/png">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400;500&display=swap">
<link rel="stylesheet" href="{build.CSS_HREF}">
<style>
  body {{ background: var(--paper); }}
  .idwrap {{ width: min(100% - 2rem, 1100px); margin: 0 auto;
             padding: clamp(2rem, 6vw, 4rem) 0 6rem; }}
  .grp {{ margin-bottom: clamp(2.5rem, 6vw, 4rem);
          padding-bottom: clamp(2rem, 4vw, 3rem);
          border-bottom: 1px solid var(--rule); }}
  .grp h2 {{ margin-bottom: 0.4rem; }}
  .grp h2 small {{ font-size: 0.5em; color: var(--muted);
                   letter-spacing: 0.12em; text-transform: uppercase; }}
  .grp--unknown {{ background: #fff8ef; padding: 1.5rem;
                   border: 1px solid rgba(200, 120, 40, 0.3); border-radius: 3px; }}
  .tag {{ display: inline-block; font-family: var(--display);
          font-size: 0.95rem; letter-spacing: 0.12em; text-transform: uppercase;
          padding: 0.3rem 0.8rem; border-radius: 2px; margin-bottom: 1.4rem; }}
  .tag--guess {{ background: var(--cream); color: #3a4f63; }}
  .tag--unknown {{ background: #c2701f; color: #fff; }}
  .shots {{ display: grid; gap: 0.6rem;
            grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); }}
  .shots figure {{ margin: 0; }}
  .shots img {{ width: 100%; aspect-ratio: 3/4; object-fit: cover;
                border-radius: 2px; background: var(--cream-deep); }}
  .shots figcaption {{ font-size: 0.72rem; color: var(--muted);
                       margin-top: 0.3rem; word-break: break-all; }}
</style>
</head>
<body>
<div class="idwrap">
  <h1>Which places are these?</h1>
  <p class="measure">The orange blocks are ones I can't place at all. The rest
  are my guesses from the dates — tell me if any are wrong. Once these are
  settled I can file the whole library by place.</p>
  {''.join(sections)}
  <p><a class="link-arrow" href="/">Back to the site</a></p>
</div>
</body>
</html>
"""
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "index.html").write_text(page)
    print(f"wrote /identify/ — {n} photographs across {len(groups) + 1} groups")


if __name__ == "__main__":
    main()
