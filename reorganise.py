#!/usr/bin/env python3
"""One-off reorganisation of the iCloud photo library.

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

# Where each original belongs, keyed by filename stem. Places confirmed by
# Samuel; the Siguniang valleys come from the old "O/" subfolders.
PLACES = {
    "2024-05 Segovia": {
        "slug": "segovia",
        "stems": ["DJI_20240517181821_0054_D", "DJI_20240517182022_0057_D",
                  "DJI_20240517182031_0058_D", "DJI_20240517182107_0059_D",
                  "DJI_20240517182222_0063_D", "DJI_20240517182729_0074_D"],
    },
    "2024-06 Kunming": {"slug": "kunming", "stems": ["IMG_8115"]},
    "2024-07 Lago Maggiore": {
        "slug": "lago-maggiore", "stems": ["DJI_20240730152115_0255_D"]},
    "2024-12 Chongqing": {
        "slug": "chongqing",
        "stems": ["IMG_7612", "IMG_7742", "IMG_7743", "IMG_7745",
                  "IMG_7746", "IMG_7818"],
    },
    "2025-07 Menorca": {
        "slug": "menorca",
        "stems": ["DJI_20250704200720_0003_D", "DJI_20250704203954_0062_D",
                  "IMG_3123", "IMG_3246"],
    },
    "2025-08 Mount Siguniang": {
        "slug": "mount-siguniang",
        "stems": ["DJI_20250815035531_0084_D", "DJI_20250815035615_0087_D",
                  "DJI_20250815082103_0001_D 2", "DJI_20250815082129_0004_D",
                  "DJI_20250815082436_0015_D 2", "DJI_20250816112109_0091_D",
                  "IMG_4555", "IMG_4873", "IMG_4874", "IMG_4916",
                  "DJI_20250815012334_0039_D copy",
                  "DJI_20250815012553_0049_D copy",
                  "DJI_20250815035323_0075_D", "DJI_20250816112051_0087_D",
                  "DJI_20250816062954_0039_D", "RESIZED 1", "RESIZED 2",
                  "Banner"],
    },
    "2025-09 London": {
        "slug": "london",
        "stems": ["DJI_20250930150852_0012_D", "DJI_20250930151352_0037_D",
                  "DJI_20250930151411_0039_D 2", "IMG_5942", "IMG_5943",
                  "IMG_5946"],
    },
}

# Within Mount Siguniang the old subfolders recorded which valley each
# frame came from; worth keeping, since it is real information.
SIGUNIANG_AREA = {
    "haizi-valley": ["DJI_20250815035531_0084_D", "DJI_20250815035615_0087_D",
                     "DJI_20250815082103_0001_D 2", "DJI_20250815082129_0004_D",
                     "DJI_20250815082436_0015_D 2"],
    "changping-valley": ["IMG_4555", "IMG_4873", "IMG_4874", "IMG_4916",
                         "Banner", "DJI_20250816112109_0091_D"],
    "rilong-town": ["DJI_20250815012334_0039_D copy",
                    "DJI_20250815012553_0049_D copy",
                    "DJI_20250815035323_0075_D"],
}

# Not yet identified. Parked rather than guessed at.
UNSORTED = ["IMG_3133", "DJI_20241130155638_0141_D"]

BRAND_LOGOS = ["Copy of TheWanderingWing Logo Bigger",
               "Copy of TheWanderingWing Logo", "High Res WanderingWing Logo",
               "TheWanderingWing Logo FINAL", "TheWanderingWing Logo TRANS",
               "TheWanderingWing Logo Website", "TheWanderingWing Logo"]

FILM_STILLS = ["Chongqing", "Kunming", "Lago Maggiore", "Mount Siguniang"]


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

    # Of each set of identical files keep the shallowest, shortest path.
    canonical, dropped = {}, []
    for h, paths in by_hash.items():
        paths.sort(key=lambda p: (len(p.parts), len(p.name)))
        canonical[h] = paths[0]
        dropped.extend(paths[1:])

    stem_to_place = {}
    for folder, meta in PLACES.items():
        for stem in meta["stems"]:
            stem_to_place[stem] = (folder, meta["slug"])
    area_of = {s: a for a, stems in SIGUNIANG_AREA.items() for s in stems}

    grouped, moves, unplaced = defaultdict(list), [], []

    for p in sorted(canonical.values(), key=lambda x: x.name):
        stem = p.stem
        if stem in stem_to_place:
            grouped[stem_to_place[stem]].append(p)
        elif stem in UNSORTED:
            grouped[("Photos/Unsorted", "unsorted")].append(p)
        elif stem in BRAND_LOGOS:
            moves.append((p, LIB / "Brand" / "Logo" / p.name))
        elif stem == "IMG_4771":
            moves.append((p, LIB / "Brand" / "portrait-samuel.jpeg"))
        elif stem in FILM_STILLS:
            moves.append((p, LIB / "Film stills" / f"{stem.lower().replace(' ', '-')}.png"))
        else:
            unplaced.append(p)

    for (folder, slug), paths in grouped.items():
        dest_dir = LIB / ("Photos/" + folder if not folder.startswith("Photos") else folder)
        # Order by capture time where the camera encoded it, else by name.
        paths.sort(key=lambda x: x.name)
        counters = defaultdict(int)
        for p in paths:
            area = area_of.get(p.stem)
            key = area or slug
            counters[key] += 1
            name = f"{key}-{counters[key]:02d}{p.suffix.lower()}"
            moves.append((p, dest_dir / name))

    # Anything not an image: the film, and whatever else turns up.
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
    moves, dropped, unplaced = plan()
    if "--apply" in sys.argv:
        if unplaced:
            raise SystemExit(f"{len(unplaced)} file(s) unplaced — resolve first")
        apply(moves, dropped)
    else:
        show(moves, dropped, unplaced)
