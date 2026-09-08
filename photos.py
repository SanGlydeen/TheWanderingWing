#!/usr/bin/env python3
"""Derivative image builder for The Wandering Wing.

Reads full-size originals from the iCloud photo library and writes
web-sized JPEGs into public/photos/. Uses macOS `sips`, so there is
nothing to install.

Originals are never modified. Derivatives are only rebuilt when the
source is newer than the output, so re-runs are cheap.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

# The iCloud folder Samuel drops photos into. Source of truth; read-only.
LIBRARY = Path(
    "/Users/samuelsalesas/Library/Mobile Documents/com~apple~CloudDocs"
    "/Files/Personal/Hobbies/Photography/Drone/The Wandering Wing"
)

ROOT = Path(__file__).parent
OUT = ROOT / "public" / "photos"
MANIFEST = ROOT / "photo-manifest.json"

# Widths we emit. The browser picks one via srcset, so a phone never
# downloads a 2400px frame.
WIDTHS = [400, 800, 1400, 2000, 2400]
QUALITY = 78

# No derivative is taller than this. The ladder is by width, which suits
# landscape frames, but a portrait at 2000 wide is 3556 tall — far more
# than any screen shows and twice the bytes. Tiers past this are skipped.
MAX_HEIGHT = 2600


def sips(*args):
    return subprocess.run(
        ["sips", *args], capture_output=True, text=True, check=False
    )


def dimensions(path):
    """Return (width, height) of an image, honouring EXIF rotation."""
    r = sips("-g", "pixelWidth", "-g", "pixelHeight", str(path))
    w = h = None
    for line in r.stdout.splitlines():
        line = line.strip()
        if line.startswith("pixelWidth:"):
            w = int(line.split(":")[1])
        elif line.startswith("pixelHeight:"):
            h = int(line.split(":")[1])
    if w is None or h is None:
        raise RuntimeError(f"could not read dimensions: {path}")
    return w, h


def slugify(text):
    out = []
    for ch in text.lower():
        if ch.isalnum():
            out.append(ch)
        elif out and out[-1] != "-":
            out.append("-")
    return "".join(out).strip("-")


def build_one(src, group, name):
    """Generate every width for a single source image.

    Returns a manifest entry, or None if the source is unreadable.
    """
    try:
        sw, sh = dimensions(src)
    except RuntimeError as e:
        print(f"  !! {e}", file=sys.stderr)
        return None

    dest_dir = OUT / group
    dest_dir.mkdir(parents=True, exist_ok=True)

    src_mtime = src.stat().st_mtime
    sizes = []

    for w in WIDTHS:
        # Never upscale: a 1600px original gets no 2000px variant.
        if w > sw and sizes:
            break
        target_w = min(w, sw)
        if sizes and round(target_w * sh / sw) > MAX_HEIGHT:
            break
        dest = dest_dir / f"{name}-{w}.jpg"

        if dest.exists() and dest.stat().st_mtime >= src_mtime:
            sizes.append(w)
            continue

        # -Z fits the image inside a square of this size, so it works
        # for portrait and landscape alike; we scale by the long edge.
        long_edge = round(target_w * max(sw, sh) / sw)
        r = sips(
            "-s", "format", "jpeg",
            "-s", "formatOptions", str(QUALITY),
            "-Z", str(long_edge),
            str(src), "--out", str(dest),
        )
        if r.returncode != 0 or not dest.exists():
            print(f"  !! failed {src.name} @{w}: {r.stderr.strip()}", file=sys.stderr)
            continue
        sizes.append(w)

    if not sizes:
        return None

    return {
        "group": group,
        "name": name,
        "width": sw,
        "height": sh,
        "aspect": round(sw / sh, 4),
        "orientation": "portrait" if sh > sw else "landscape",
        "sizes": sizes,
        "src": f"/photos/{group}/{name}-{max(sizes)}.jpg",
        "srcset": ", ".join(
            f"/photos/{group}/{name}-{w}.jpg {w}w" for w in sizes
        ),
        "source": str(src.relative_to(LIBRARY)),
    }


def build(groups):
    """groups: {group_slug: [relative paths within LIBRARY]}"""
    manifest = {}
    if MANIFEST.exists():
        manifest = json.loads(MANIFEST.read_text())

    total = sum(len(v) for v in groups.values())
    done = 0

    for group, rel_paths in groups.items():
        print(f"\n{group}/")
        used = set()
        for rel in rel_paths:
            src = LIBRARY / rel
            done += 1
            if not src.exists():
                print(f"  !! missing: {rel}", file=sys.stderr)
                continue
            name = slugify(Path(rel).stem)
            if name in used:
                # Two originals share a stem (e.g. Logo.jpg and Logo.png).
                # Keep both rather than letting one overwrite the other.
                name = f"{name}-{slugify(Path(rel).suffix)}"
                n = 2
                while name in used:
                    name, n = f"{name}-{n}", n + 1
            used.add(name)
            key = f"{group}/{name}"
            entry = build_one(src, group, name)
            if entry:
                manifest[key] = entry
                print(f"  [{done}/{total}] {name} "
                      f"({entry['width']}x{entry['height']}, "
                      f"{len(entry['sizes'])} sizes)")

    MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True))
    print(f"\nwrote {MANIFEST.name}: {len(manifest)} images")
    return manifest


if __name__ == "__main__":
    # Groups come straight from the library layout: one folder per journey
    # under Photos/, plus the brand assets and the film stills.
    import assignments

    def listing(subdir, exts=(".jpg", ".jpeg", ".png")):
        d = LIBRARY / subdir
        if not d.is_dir():
            return []
        return sorted(
            str(p.relative_to(LIBRARY))
            for p in d.iterdir()
            if p.suffix.lower() in exts and not p.name.startswith(".")
        )

    groups = {}
    for slug, folder in assignments.FOLDERS.items():
        rel = folder if folder.startswith("Photos") else f"Photos/{folder}"
        files = listing(rel)
        if files:
            groups[slug] = files
    groups["brand"] = listing("Brand") + listing("Brand/Logo")
    groups["film-stills"] = listing("Film stills")

    build({k: v for k, v in groups.items() if v})
