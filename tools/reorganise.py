#!/usr/bin/env python3
"""One-off reorganisation of the iCloud photo library. ALREADY RUN.

Applied on 8 September 2026: 117 files moved, 14 duplicates dropped.
Kept for the record and because reorganise-map.json reverses it.
Do not run it again — the library is already in its target shape.

The library grew as folders named after posts ("Posts/1. Mount Siguniang
1&2/O/2. Changping Valley"), with camera filenames, several copies of the
same frame, and photographs from one trip scattered across Highlights and
Posts. Since the source filename becomes the public URL, that also meant
addresses like /photos/mount-siguniang/dji-20250815082103-0001-d-2.jpg.

This rewrites the library as one folder per journey, with readable names,
and drops byte-identical duplicates.

    python3 reorganise.py          # show the plan, change nothing
    python3 reorganise.py --apply  # do it

Every move is recorded in reorganise-map.json so it can be undone.
"""

import hashlib
import json
import shutil
import sys
from collections import defaultdict
from pathlib import Path

LIB = Path(
    "/Users/samuelsalesas/Library/Mobile Documents/com~apple~CloudDocs"
    "/Files/Personal/Hobbies/Photography/Drone/The Wandering Wing"
)
MAP_FILE = Path(__file__).parent / "reorganise-map.json"

import sys as _sys
_sys.path.insert(0, str(Path(__file__).parent.parent))
import assignments

def digest(path):
    h = hashlib.md5()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sources():
    for p in sorted(LIB.rglob("*")):
        if p.is_file() and not p.name.startswith("."):
            yield p


def plan():
    """Return (moves, dropped, unplaced)."""
    by_hash = defaultdict(list)
    for p in sources():
        if p.suffix.lower() in (".jpg", ".jpeg", ".png"):
            by_hash[digest(p)].append(p)

    # Of each set of byte-identical files keep the shallowest, shortest path.
    canonical, dropped = {}, []
    for h, paths in by_hash.items():
        paths.sort(key=lambda p: (len(p.parts), len(p.name)))
        canonical[h] = paths[0]
        dropped.extend(paths[1:])

    grouped, moves, unplaced = defaultdict(list), [], []

    for p in sorted(canonical.values(), key=lambda x: x.name):
        stem = p.stem
        if stem in assignments.ASSIGN:
            grouped[assignments.ASSIGN[stem][0]].append(p)
        elif stem in assignments.BRAND_LOGOS:
            moves.append((p, LIB / "Brand" / "Logo" / p.name))
        elif stem == assignments.PORTRAIT:
            moves.append((p, LIB / "Brand" / "portrait-samuel.jpeg"))
        elif stem in assignments.FILM_STILLS:
            slug = stem.lower().replace(" ", "-")
            moves.append((p, LIB / "Film stills" / f"{slug}.png"))
        else:
            unplaced.append(p)

    for slug, paths in grouped.items():
        folder = assignments.FOLDERS[slug]
        dest_dir = LIB / folder if folder.startswith("Photos") else LIB / "Photos" / folder
        paths.sort(key=lambda x: x.name)
        counters = defaultdict(int)
        for p in paths:
            area = assignments.ASSIGN[p.stem][1]
            key = area or slug
            counters[key] += 1
            ext = ".jpg" if p.suffix.lower() in (".jpg", ".jpeg") else p.suffix.lower()
            moves.append((p, dest_dir / f"{key}-{counters[key]:02d}{ext}"))

    for p in sources():
        if p.suffix.lower() in (".jpg", ".jpeg", ".png"):
            continue
        if p.suffix.lower() == ".mp4":
            moves.append((p, LIB / "Video" / "kunming-2024.mp4"))
        else:
            unplaced.append(p)

    return moves, dropped, unplaced


def show(moves, dropped, unplaced):
    print(f"{len(moves)} files to move, {len(dropped)} duplicates to drop\n")
    by_dest = defaultdict(list)
    for src, dst in moves:
        by_dest[dst.parent.relative_to(LIB)].append((src, dst))
    for folder in sorted(by_dest, key=str):
        print(f"{folder}/")
        for src, dst in sorted(by_dest[folder], key=lambda x: x[1].name):
            print(f"   {dst.name:<34} <- {src.relative_to(LIB)}")
        print()
    if dropped:
        print("duplicates (identical bytes, removed):")
        for p in sorted(dropped, key=str):
            print(f"   {p.relative_to(LIB)}")
        print()
    if unplaced:
        print("!! not placed, left where they are:")
        for p in unplaced:
            print(f"   {p.relative_to(LIB)}")


def apply(moves, dropped):
    record = {"moves": [], "dropped": []}
    for src, dst in moves:
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists():
            raise SystemExit(f"refusing to overwrite {dst}")
        shutil.move(str(src), str(dst))
        record["moves"].append([str(src.relative_to(LIB)), str(dst.relative_to(LIB))])
    for p in dropped:
        record["dropped"].append([str(p.relative_to(LIB)), digest(p)])
        p.unlink()
    MAP_FILE.write_text(json.dumps(record, indent=2))

    # Remove the folders left empty behind us.
    for d in sorted((p for p in LIB.rglob("*") if p.is_dir()),
                    key=lambda p: len(p.parts), reverse=True):
        try:
            if not any(x for x in d.iterdir() if x.name != ".DS_Store"):
                for junk in d.iterdir():
                    junk.unlink()
                d.rmdir()
        except OSError:
            pass
    print(f"moved {len(record['moves'])}, dropped {len(record['dropped'])}")
    print(f"map written to {MAP_FILE.name}")


if __name__ == "__main__":
    # This has already run. Running it again against an already-reorganised
    # library would file things a second time and misplace anything added
    # since. The map's existence is the record that it happened.
    if MAP_FILE.exists() and "--force" not in sys.argv:
        raise SystemExit(
            f"Already applied — see {MAP_FILE.name}.\n"
            "The library is in its target shape; re-running would misfile it.\n"
            "Pass --force only if you genuinely mean to."
        )

    moves, dropped, unplaced = plan()
    if "--apply" in sys.argv:
        if unplaced:
            raise SystemExit(f"{len(unplaced)} file(s) unplaced — resolve first")
        apply(moves, dropped)
    else:
        show(moves, dropped, unplaced)
