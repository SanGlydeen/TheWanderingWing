#!/usr/bin/env python3
"""Where every photograph in the library belongs.

Places confirmed by Samuel on 8 September 2026, against the file listing
he was shown at /identify/. Two sets are still open and are marked OPEN
below; the migration refuses to run while any remain.

Keys are filename stems. Values are (place slug, optional area within it).
The area only exists where it is real information worth keeping — which
valley at Siguniang, which part of Menorca — not as decoration.
"""

# folder name in the library -> place slug
FOLDERS = {
    "canterbury": "2024-11 Canterbury",
    "chongqing": "2024-12 Chongqing",
    "devon": "2026-05 Devon",
    "dover": "2024-11 Dover",
    "kunming": "2024 Kunming",
    "lago-maggiore": "2024-07 Lago Maggiore",
    "leshan": "2024-12 Leshan",
    "london": "2025-09 London",
    "menorca": "2025-07 Menorca",
    "mount-siguniang": "2025-08 Mount Siguniang",
    "segovia": "2024-05 Segovia",
    "suzhou": "2025-12 Suzhou",
    "toledo": "2025-12 Toledo",
}

ASSIGN = {}


def _add(place, stems, area=None):
    for s in stems:
        ASSIGN[s] = (place, area)


# --- already in the library before today ------------------------------

_add("segovia", ["DJI_20240517181821_0054_D", "DJI_20240517182022_0057_D",
                 "DJI_20240517182031_0058_D", "DJI_20240517182107_0059_D",
                 "DJI_20240517182222_0063_D", "DJI_20240517182729_0074_D"])

_add("lago-maggiore", ["DJI_20240730152115_0255_D"])

_add("chongqing", ["IMG_7612", "IMG_7742", "IMG_7743", "IMG_7745",
                   "IMG_7746", "IMG_7818"])

_add("kunming", ["IMG_8115"])

_add("menorca", ["DJI_20250704200720_0003_D", "DJI_20250704203954_0062_D",
                 "IMG_3246"])
_add("menorca", ["IMG_3123", "IMG_3133"], area="cavalleria")

_add("mount-siguniang", ["DJI_20250815035531_0084_D", "DJI_20250815035615_0087_D",
                         "DJI_20250815082103_0001_D 2", "DJI_20250815082129_0004_D",
                         "DJI_20250815082436_0015_D 2"], area="haizi-valley")
_add("mount-siguniang", ["IMG_4555", "IMG_4873", "IMG_4874", "IMG_4916",
                         "Banner", "DJI_20250816112109_0091_D"],
     area="changping-valley")
_add("mount-siguniang", ["DJI_20250815012334_0039_D copy",
                         "DJI_20250815012553_0049_D copy",
                         "DJI_20250815035323_0075_D"], area="rilong-town")
_add("mount-siguniang", ["DJI_20250816112051_0087_D", "DJI_20250816062954_0039_D",
                         "RESIZED 1", "RESIZED 2"])

_add("london", ["DJI_20250930150852_0012_D", "DJI_20250930151352_0037_D",
                "DJI_20250930151411_0039_D 2", "IMG_5942", "IMG_5943",
                "IMG_5946"])

_add("canterbury", ["DJI_20241130155638_0141_D",
                    "DJI_20241130155532_0136_D"], area="cathedral")
# Confirmed from the photographs themselves: the white cliffs with South
# Foreland lighthouse on the clifftop.
_add("dover", ["IMG_6978", "IMG_6979"], area="white-cliffs")

# --- the 59 dropped in the library root on 8 Sep 2026 -----------------

# 2024-05 — Segovia
_add("segovia", ["IMG_2594", "IMG_2595"])

# 2024-07 — Kunming, the last two by the stone karst forest; one stray
# frame from Lago Maggiore sits in the same month.
_add("kunming", ["07F5A85B-045C-43CA-B5EC-3747016A915E_1_201_a",
                 "2E8F614F-FE89-44F5-8FD4-64C2E649F7C8_1_201_a",
                 "DJI_20240724113307_0141_D", "DJI_20240724113316_0142_D",
                 "DJI_20240724113557_0148_D",
                 "E15035EE-D8B6-4EC9-A1DC-88D78BCD85A0_1_201_a"])
_add("kunming", ["IMG_3897", "IMG_3909"], area="stone-forest")
_add("lago-maggiore", ["IMG_4512"])

# 2024-08 — Lago Maggiore
_add("lago-maggiore", ["IMG_4675"])

# 2024-12 — the first two at Leshan, south of Chengdu; then Chongqing;
# the last one back in Kunming.
_add("leshan", ["IMG_7503", "IMG_7504"])
_add("chongqing", ["IMG_7597", "IMG_7601", "IMG_7604", "IMG_7606", "IMG_7607",
                   "IMG_7741", "IMG_7747", "IMG_7816"])
_add("kunming", ["IMG_8111"])

# 2025-07 — Menorca throughout
_add("menorca", ["DJI_20250703203724_0456_D", "DJI_20250703203756_0459_D",
                 "DJI_20250703203930_0464_D", "DJI_20250703205133_0491_D",
                 "DJI_20250704202627_0033_D", "DJI_20250704203521_0050_D",
                 "DJI_20250722200637_0351_D", "DJI_20250722203648_0419_D",
                 "DJI_20250722204524_0444_D", "DJI_20250727132506_0006_D",
                 "IMG_3087", "IMG_3094", "IMG_3239", "IMG_3240",
                 "IMG_3296", "IMG_3298"])

# 2025-08 — Mount Siguniang
_add("mount-siguniang", ["IMG_4554", "IMG_4861", "IMG_4866", "IMG_4869",
                         "IMG_4911", "IMG_4914"])

# 2025-09 — London
_add("london", ["IMG_5945"])

# 2025-12 — Toledo, then Suzhou
_add("toledo", ["DJI_20251217143625_0067_D", "DJI_20251217144758_0089_D"])
_add("suzhou", ["IMG_8244", "IMG_8246", "IMG_8252", "IMG_8253"])

# 2026-05 — Devon
_add("devon", ["DJI_20260523133144_0324_D", "DJI_20260523133202_0327_D",
               "DJI_20260523133540_0345_D"])


# --- nothing left open ------------------------------------------------

OPEN = {}

# Files that are neither photographs of places nor open questions.
BRAND_LOGOS = ["Copy of TheWanderingWing Logo Bigger",
               "Copy of TheWanderingWing Logo", "High Res WanderingWing Logo",
               "TheWanderingWing Logo FINAL", "TheWanderingWing Logo TRANS",
               "TheWanderingWing Logo Website", "TheWanderingWing Logo"]
PORTRAIT = "IMG_4771"
FILM_STILLS = ["Chongqing", "Kunming", "Lago Maggiore", "Mount Siguniang"]


if __name__ == "__main__":
    from collections import Counter
    c = Counter(place for place, _ in ASSIGN.values())
    print(f"{len(ASSIGN)} photographs assigned across {len(c)} places\n")
    for place, n in sorted(c.items()):
        print(f"  {place:<18} {n}")
    open_n = sum(len(v["stems"]) for v in OPEN.values())
    print(f"\n{open_n} still open, in {len(OPEN)} questions:")
    for k, v in OPEN.items():
        print(f"  {k}: {', '.join(v['stems'])}")
