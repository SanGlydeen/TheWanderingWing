#!/usr/bin/env python3
"""Static site generator for The Wandering Wing.

Reads content/*.md, combines it with photo-manifest.json (written by
photos.py) and writes a complete static site into public/.

Deliberately dependency-free: it runs on the Python that ships with
macOS, so there is no toolchain to install or keep alive.

    python3 photos.py    # resize originals  (slow, only when photos change)
    python3 build.py     # generate the site (fast, run any time)
"""

import hashlib
import html
import json
import re
import shutil
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent
CONTENT = ROOT / "content"
STATIC = ROOT / "static"
OUT = ROOT / "public"

MONTHS = ["", "January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]


# --------------------------------------------------------------------
# content parsing
# --------------------------------------------------------------------

def parse_front_matter(text):
    """Split a `---` fenced header from the body.

    Supports `key: value` and indented `- item` lists. That is all the
    content here needs, and it keeps the parser small enough to trust.
    """
    meta, body = {}, text
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            head = text[3:end].strip("\n")
            body = text[end + 4:].lstrip("\n")
            key = None
            for line in head.split("\n"):
                if not line.strip():
                    continue
                if line.lstrip().startswith("- ") and key:
                    meta.setdefault(key, [])
                    if isinstance(meta[key], list):
                        meta[key].append(line.lstrip()[2:].strip())
                elif ":" in line and not line.startswith((" ", "\t")):
                    key, _, val = line.partition(":")
                    key, val = key.strip(), val.strip()
                    meta[key] = val if val else []
    return meta, body


def parse_sections(body):
    """Split a body on `## name` headings into {name: text}."""
    sections, current, buf = {}, None, []
    for line in body.split("\n"):
        if line.startswith("## "):
            if current:
                sections[current] = "\n".join(buf).strip()
            current, buf = line[3:].strip(), []
        else:
            buf.append(line)
    if current:
        sections[current] = "\n".join(buf).strip()
    return sections


def paragraphs(text):
    """Blank-line separated paragraphs -> <p>. Supports *emphasis*."""
    out = []
    for chunk in re.split(r"\n\s*\n", (text or "").strip()):
        chunk = chunk.strip()
        if not chunk:
            continue
        esc = html.escape(chunk).replace("\n", " ")
        esc = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", esc)
        out.append(f"<p>{esc}</p>")
    return "\n".join(out)


def lead_sentence(text):
    """First sentence of a body, used as a teaser on index pages."""
    first = re.split(r"\n\s*\n", (text or "").strip())[0]
    return first.replace("\n", " ").strip()


def is_true(v):
    return str(v).strip().lower() in ("yes", "true", "1")


def pretty_date(value):
    """`2025-08` -> `August 2025`."""
    if not value:
        return ""
    parts = str(value).split("-")
    if len(parts) >= 2 and parts[1].isdigit():
        return f"{MONTHS[int(parts[1])]} {parts[0]}"
    return str(value)


# --------------------------------------------------------------------
# images
# --------------------------------------------------------------------

MANIFEST = json.loads((ROOT / "photo-manifest.json").read_text())


MISSING = []


def img(key, alt, sizes="100vw", cls="", eager=False, max_width=2400):
    """Render a responsive <img> for a manifest key like `london/london-06`."""
    p = MANIFEST.get(key)
    if not p:
        MISSING.append(key)
        return f"<!-- missing photo: {key} -->"

    widths = [w for w in p["sizes"] if w <= max_width] or p["sizes"]
    srcset = ", ".join(f"/photos/{p['group']}/{p['name']}-{w}.jpg {w}w"
                       for w in widths)
    src = f"/photos/{p['group']}/{p['name']}-{max(widths)}.jpg"
    loading = "" if eager else ' loading="lazy"'
    fetch = ' fetchpriority="high"' if eager else ""
    cls = f' class="{cls}"' if cls else ""

    return (
        f'<img src="{src}" srcset="{srcset}" sizes="{sizes}"'
        f' width="{p["width"]}" height="{p["height"]}"'
        f' alt="{html.escape(alt)}"{cls}{loading}{fetch} decoding="async">'
    )


def full_src(key, width=2400):
    p = MANIFEST.get(key)
    if not p:
        return ""
    w = max(x for x in p["sizes"] if x <= width) if any(
        x <= width for x in p["sizes"]) else max(p["sizes"])
    return f"/photos/{p['group']}/{p['name']}-{w}.jpg"


# --------------------------------------------------------------------
# load content
# --------------------------------------------------------------------

site_meta, site_body = parse_front_matter((CONTENT / "site.md").read_text())
SITE = site_meta
SECTIONS = parse_sections(site_body)

PLACES = []
for f in sorted((CONTENT / "places").glob("*.md")):
    meta, body = parse_front_matter(f.read_text())
    meta["slug"] = f.stem
    meta["body"] = body
    meta["photos"] = meta.get("photos") or []
    PLACES.append(meta)

FILMS = []
for f in sorted((CONTENT / "films").glob("*.md")):
    meta, body = parse_front_matter(f.read_text())
    meta["body"] = body
    FILMS.append(meta)

BY_SLUG = {p["slug"]: p for p in PLACES}
FEATURED = sorted([p for p in PLACES if p.get("feature")],
                  key=lambda p: int(p["feature"]))
GALLERIES = [p for p in PLACES if p["photos"]]
GALLERIES.sort(key=lambda p: str(p.get("date", "")), reverse=True)

# A place earns its own page once there is enough of it to be worth the
# trip — or if there is a film, which carries a page on its own. The rest
# gather on one "Elsewhere" page as titled sections, and graduate out of
# it automatically as they grow.
OWN_PAGE_MIN = 6
JOURNEYS = [p for p in GALLERIES
            if len(p["photos"]) >= OWN_PAGE_MIN or p.get("film")]
ELSEWHERE = [p for p in GALLERIES if p not in JOURNEYS]

# Photos on the homepage highlight strip, in the order they appear.
HIGHLIGHTS = [
    "canterbury/cathedral-02",
    "menorca/menorca-08",
    "london/london-03",
    "menorca/cavalleria-02",
    "mount-siguniang/changping-valley-03",
    "mount-siguniang/changping-valley-04",
]


# --------------------------------------------------------------------
# assets
# --------------------------------------------------------------------

# The bird, inlined as a <symbol> so each placement inherits its colour
# from CSS. An <img src="*.svg"> renders in its own document and would
# ignore currentColor entirely.
_mark_svg = (STATIC / "img" / "mark.svg").read_text()
MARK_VIEWBOX = re.search(r'viewBox="([^"]+)"', _mark_svg).group(1)
MARK_PATH = re.search(r"(<path\b[^>]*/?>)", _mark_svg).group(1)


def mark_sprite():
    return (f'<svg class="sprite" aria-hidden="true" focusable="false">'
            f'<symbol id="ww-mark" viewBox="{MARK_VIEWBOX}">{MARK_PATH}</symbol>'
            f'</svg>')


def mark(cls=""):
    cls = f' class="{cls}"' if cls else ""
    return (f'<svg{cls} viewBox="{MARK_VIEWBOX}" aria-hidden="true" '
            f'focusable="false"><use href="#ww-mark"/></svg>')


def asset(rel):
    """Copy static/<rel> to public/ under a content-hashed name."""
    src = STATIC / rel
    digest = hashlib.md5(src.read_bytes()).hexdigest()[:8]
    stem, dot, ext = rel.rpartition(".")
    return f"/{stem}.{digest}.{ext}"


CSS_HREF = asset("css/site.css")
JS_SRC = asset("js/site.js")
FAVICON = asset("img/favicon.png")

# --------------------------------------------------------------------
# layout
# --------------------------------------------------------------------

def nav(active):
    items = [("Home", "/"), ("Gallery", "/gallery/"), ("Films", "/films/")]
    links = "".join(
        f'<a href="{href}"{" aria-current=\"page\"" if label == active else ""}>'
        f'{label}</a>'
        for label, href in items
    )
    return links


# Instagram and YouTube marks from Simple Icons (simpleicons.org), whose
# SVG data is CC0. The marks themselves are trademarks of their owners;
# both companies permit using them unmodified to link to your own profile,
# which is what these do. Previously these were my own approximations
# drawn from memory — worse looking, and worse practice, since a redrawn
# trademark is a modified one.

ICON_IG = ('<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">'
           '<path fill="currentColor" d="M7.0301.084c-1.2768.0602-2.1487.264-2.911.5634-.7888.3075-1.4575.72-2.1228 1.3877-.6652.6677-1.075 1.3368-1.3802 2.127-.2954.7638-.4956 1.6365-.552 2.914-.0564 1.2775-.0689 1.6882-.0626 4.947.0062 3.2586.0206 3.6671.0825 4.9473.061 1.2765.264 2.1482.5635 2.9107.308.7889.72 1.4573 1.388 2.1228.6679.6655 1.3365 1.0743 2.1285 1.38.7632.295 1.6361.4961 2.9134.552 1.2773.056 1.6884.069 4.9462.0627 3.2578-.0062 3.668-.0207 4.9478-.0814 1.28-.0607 2.147-.2652 2.9098-.5633.7889-.3086 1.4578-.72 2.1228-1.3881.665-.6682 1.0745-1.3378 1.3795-2.1284.2957-.7632.4966-1.636.552-2.9124.056-1.2809.0692-1.6898.063-4.948-.0063-3.2583-.021-3.6668-.0817-4.9465-.0607-1.2797-.264-2.1487-.5633-2.9117-.3084-.7889-.72-1.4568-1.3876-2.1228C21.2982 1.33 20.628.9208 19.8378.6165 19.074.321 18.2017.1197 16.9244.0645 15.6471.0093 15.236-.005 11.977.0014 8.718.0076 8.31.0215 7.0301.0839m.1402 21.6932c-1.17-.0509-1.8053-.2453-2.2287-.408-.5606-.216-.96-.4771-1.3819-.895-.422-.4178-.6811-.8186-.9-1.378-.1644-.4234-.3624-1.058-.4171-2.228-.0595-1.2645-.072-1.6442-.079-4.848-.007-3.2037.0053-3.583.0607-4.848.05-1.169.2456-1.805.408-2.2282.216-.5613.4762-.96.895-1.3816.4188-.4217.8184-.6814 1.3783-.9003.423-.1651 1.0575-.3614 2.227-.4171 1.2655-.06 1.6447-.072 4.848-.079 3.2033-.007 3.5835.005 4.8495.0608 1.169.0508 1.8053.2445 2.228.408.5608.216.96.4754 1.3816.895.4217.4194.6816.8176.9005 1.3787.1653.4217.3617 1.056.4169 2.2263.0602 1.2655.0739 1.645.0796 4.848.0058 3.203-.0055 3.5834-.061 4.848-.051 1.17-.245 1.8055-.408 2.2294-.216.5604-.4763.96-.8954 1.3814-.419.4215-.8181.6811-1.3783.9-.4224.1649-1.0577.3617-2.2262.4174-1.2656.0595-1.6448.072-4.8493.079-3.2045.007-3.5825-.006-4.848-.0608M16.953 5.5864A1.44 1.44 0 1 0 18.39 4.144a1.44 1.44 0 0 0-1.437 1.4424M5.8385 12.012c.0067 3.4032 2.7706 6.1557 6.173 6.1493 3.4026-.0065 6.157-2.7701 6.1506-6.1733-.0065-3.4032-2.771-6.1565-6.174-6.1498-3.403.0067-6.156 2.771-6.1496 6.1738M8 12.0077a4 4 0 1 1 4.008 3.9921A3.9996 3.9996 0 0 1 8 12.0077"/></svg>')

ICON_YT = ('<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">'
           '<path fill="currentColor" d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>')


def socials(cls="socials"):
    return (
        f'<div class="{cls}">'
        f'<a href="{SITE["instagram"]}" rel="me noopener" target="_blank"'
        f' aria-label="Instagram">{ICON_IG}</a>'
        f'<a href="{SITE["youtube"]}" rel="me noopener" target="_blank"'
        f' aria-label="YouTube">{ICON_YT}</a>'
        f'</div>'
    )


def page(title, body, active, description, hero_header=False, css_extra="",
         path=None, share_image=None):
    """Wrap page content in the shared shell."""
    header_cls = " site-header--hero" if hero_header else ""
    year = date.today().year

    # The site answers on both the apex and www, so every page names the apex
    # as canonical. Omitted on pages that should never be indexed.
    canonical = ""
    if path:
        url = f"https://{SITE['domain']}{path}"
        canonical = (f'<link rel="canonical" href="{url}">\n'
                     f'<meta property="og:url" content="{url}">')

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)} · {html.escape(SITE['name'])}</title>
<meta name="description" content="{html.escape(description)}">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(description)}">
<meta property="og:type" content="website">
{canonical}
<meta property="og:image" content="https://{SITE['domain']}{full_src(share_image or SITE['hero'], 1400)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#152739">
<link rel="icon" href="{FAVICON}" type="image/png">
<link rel="apple-touch-icon" href="{FAVICON}">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;1,300;1,400&display=swap">
<link rel="stylesheet" href="{CSS_HREF}">
{css_extra}
</head>
<body>
{mark_sprite()}
<a class="skip" href="#main">Skip to content</a>

<header class="site-header{header_cls}">
  <div class="wrap site-header__inner">
    <a class="brand" href="/">
      {mark("brand__mark")}
      <span>{html.escape(SITE['name'])}</span>
    </a>
    <nav class="site-nav" aria-label="Main">{nav(active)}</nav>
  </div>
</header>

<main id="main">
{body}
</main>

<footer class="site-footer">
  <div class="wrap">
    {mark("site-footer__mark")}
    <p class="site-footer__tagline">{html.escape(SITE['tagline'])}</p>
    {socials()}
    <p class="site-footer__legal">© {year} {html.escape(SITE['name'])} |
      {html.escape(SITE['author'])}. All rights reserved.</p>
  </div>
</footer>

<script src="{JS_SRC}" defer></script>
</body>
</html>
"""


# --------------------------------------------------------------------
# sections
# --------------------------------------------------------------------


def hero_picture():
    wide = MANIFEST.get(SITE["hero"])
    tall = MANIFEST.get(SITE.get("hero_portrait", ""))
    if not wide:
        return ""
    if not tall:
        return img(SITE["hero"], "Aerial view", sizes="100vw", eager=True)
    tall_set = ", ".join(f"/photos/{tall['group']}/{tall['name']}-{w}.jpg {w}w"
                         for w in tall["sizes"])
    wide_set = ", ".join(f"/photos/{wide['group']}/{wide['name']}-{w}.jpg {w}w"
                         for w in wide["sizes"])
    return (
        f'<picture>'
        f'<source media="(max-width: 700px)" srcset="{tall_set}" sizes="100vw">'
        f'<source srcset="{wide_set}" sizes="100vw">'
        f'<img src="/photos/{wide["group"]}/{wide["name"]}-{max(wide["sizes"])}.jpg"'
        f' alt="Mount Siguniang, Sichuan" width="{wide["width"]}"'
        f' height="{wide["height"]}" fetchpriority="high" decoding="async">'
        f'</picture>'
    )


def about_section():
    return f"""
<section class="about" id="about">
  <div class="wrap about__inner">
    <div class="about__portrait">
      {img(SITE['portrait'], 'Samuel Salesas',
           sizes='(max-width: 600px) 62vw, 300px', max_width=800)}
    </div>
    <h2>About Me</h2>
    {paragraphs(SECTIONS['about'])}
  </div>
</section>
"""


def feature_block(place, index):
    """Alternating image / text band used on the homepage."""
    side = "left" if index % 2 == 0 else "right"
    title = place["title"]
    meta_bits = [b for b in (place.get("region"),
                             pretty_date(place.get("date"))) if b]
    link = ""
    if place["photos"]:
        link = (f'<a class="link-arrow" href="/gallery/{place["slug"]}/">'
                f'See the photographs</a>')
    elif place.get("film"):
        link = '<a class="link-arrow" href="/films/">Watch the film</a>'

    return f"""
<article class="feature feature--{side}">
  <div class="feature__media">
    {img(place['hero'], title,
         sizes='(max-width: 900px) 100vw, 62vw', max_width=2000)}
  </div>
  <div class="feature__body">
    <p class="eyebrow">{html.escape(' · '.join(meta_bits))}</p>
    <h2>{html.escape(title)}</h2>
    {paragraphs(place['body'])}
    {link}
  </div>
</article>
"""



def describe(key, place_title):
    """A human alt text from the manifest key and its place."""
    name = MANIFEST[key]["name"] if key in MANIFEST else key.split("/")[-1]
    stem = re.sub(r"-\d+$", "", name)
    place_slug = re.sub(r"[^a-z]+", "-", place_title.lower()).strip("-")
    if stem and stem != place_slug:
        area = stem.replace("-", " ").title()
        return f"{area}, {place_title}" if place_title else area
    return place_title or "Aerial photograph"


def photo_grid(keys, place_title=""):
    """Lightbox-enabled grid. Wide frames span two columns."""
    cells = []
    for i, key in enumerate(keys):
        p = MANIFEST.get(key)
        if not p:
            cells.append(f"<!-- missing photo: {key} -->")
            continue
        alt = describe(key, place_title)
        cells.append(f"""
    <button class="grid__cell" type="button"
            data-full="{full_src(key)}"
            data-alt="{html.escape(alt)}">
      {img(key, alt, sizes='(max-width: 700px) 100vw, (max-width: 1100px) 50vw, 33vw', max_width=1400)}
    </button>""")
    return f'<div class="grid">{"".join(cells)}</div>'


CHEVRON = ('<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">'
           '<path d="M15 4 L7 12 L15 20" fill="none" stroke="currentColor" '
           'stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
           '</svg>')


def carousel(keys, label="Highlights"):
    """One photograph at a time, with arrows. Falls back to a plain
    horizontal scroller when JavaScript is unavailable."""
    slides = []
    for i, key in enumerate(keys):
        p = MANIFEST.get(key)
        if not p:
            slides.append(f"<!-- missing photo: {key} -->")
            continue
        slides.append(f"""
      <li class="carousel__slide" data-full="{full_src(key)}"
          data-alt="{html.escape(label)}">
        {img(key, label, sizes='(max-width: 900px) 100vw, 880px',
             eager=(i == 0), max_width=1400)}
      </li>""")

    return f"""
<div class="carousel" data-carousel aria-roledescription="carousel"
     aria-label="{html.escape(label)}">
  <button class="carousel__nav carousel__nav--prev" type="button"
          aria-label="Previous photograph">{CHEVRON}</button>
  <div class="carousel__viewport">
    <ul class="carousel__track">{"".join(slides)}</ul>
  </div>
  <button class="carousel__nav carousel__nav--next" type="button"
          aria-label="Next photograph">{CHEVRON}</button>
  <p class="carousel__count" aria-live="polite"></p>
</div>
"""


def film_block(film):
    """YouTube facade: a poster image that only loads the player on click.

    Avoids pulling in YouTube's scripts (and cookies) on page load.
    """
    yt = film["youtube"]
    poster = film.get("poster")
    poster_img = (img(poster, film["title"],
                      sizes='(max-width: 1000px) 100vw, 900px', max_width=1400)
                  if poster and poster in MANIFEST else
                  f'<img src="https://i.ytimg.com/vi/{yt}/maxresdefault.jpg"'
                  f' alt="{html.escape(film["title"])}" loading="lazy"'
                  f' width="1280" height="720">')

    return f"""
<article class="film">
  <p class="eyebrow">{html.escape(pretty_date(film.get('date')))}</p>
  <h2>{html.escape(film['title'])}</h2>
  <div class="film__text">{paragraphs(film['body'])}</div>
  <div class="film__player" data-youtube="{yt}"
       role="button" tabindex="0"
       aria-label="Play {html.escape(film['title'])}">
    {poster_img}
    <span class="film__play" aria-hidden="true"></span>
  </div>
</article>
"""


# --------------------------------------------------------------------
# pages
# --------------------------------------------------------------------

def build_home():
    latest = FILMS[0]
    features = "".join(feature_block(p, i) for i, p in enumerate(FEATURED))

    body = f"""
<section class="hero">
  <div class="hero__media">
    {hero_picture()}
  </div>
  <div class="hero__inner">
    {mark("hero__logo")}
    <p class="hero__welcome">Welcome to</p>
    <h1 class="hero__title">{html.escape(SITE['name'])}</h1>
    <p class="hero__tagline">{html.escape(SITE['tagline'])}</p>
  </div>
  <a class="hero__scroll" href="#intro" aria-label="Scroll to content"></a>
</section>

<section class="intro" id="intro">
  <div class="wrap measure">
    {paragraphs(SECTIONS['intro'])}
  </div>
</section>

<div class="features">{features}</div>

<section class="band" id="highlights">
  <div class="wrap">
    <h2 class="band__title">My Highlights</h2>
    <p class="band__text measure">Here you'll find a few more scenes from my
      travels – glimpses of coastlines, cities, and horizons that caught my eye.
      If you'd like to dive deeper into the journey, wander over to the gallery
      to explore more.</p>
    {carousel(HIGHLIGHTS)}
    <p class="band__cta"><a class="button" href="/gallery/">See more</a></p>
  </div>
</section>

<section class="band band--dark" id="latest-film">
  <div class="wrap">
    <h2 class="band__title">My Latest Film</h2>
    <p class="band__text measure">Here you'll find my latest film. Think of it
      as a little invitation to wander with me – to join me on a voyage through
      the skies, where each flight reveals the world in a new light.</p>
    <div class="band__film">{film_block(latest)}</div>
    <p class="band__cta"><a class="button button--light" href="/films/">All films</a></p>
  </div>
</section>

{about_section()}
"""
    return page("Home", body, "Home", lead_sentence(SECTIONS["intro"]),
                hero_header=True, path="/")


def elsewhere_teaser():
    if not ELSEWHERE:
        return ""
    names = [p["title"] for p in ELSEWHERE]
    listed = ", ".join(names[:-1]) + " and " + names[-1] if len(names) > 1 else names[0]
    total = sum(len(p["photos"]) for p in ELSEWHERE)
    return f"""
<section class="band band--quiet">
  <div class="wrap">
    <h2 class="band__title">Elsewhere</h2>
    <p class="band__text measure">Shorter visits — {html.escape(listed)}.
      {total} photographs between them.</p>
    <p class="band__cta"><a class="button" href="/gallery/elsewhere/">See them</a></p>
  </div>
</section>
"""


def build_gallery_index():
    cards = []
    for p in JOURNEYS:
        blurb = p.get("gallery_blurb") or lead_sentence(p["body"])
        meta_bits = [b for b in (p.get("region"),
                                 pretty_date(p.get("date"))) if b]
        cards.append(f"""
  <a class="card" href="/gallery/{p['slug']}/">
    <div class="card__media">
      {img(p['hero'], p['title'],
           sizes='(max-width: 800px) 100vw, 46vw', max_width=1400)}
    </div>
    <div class="card__body">
      <p class="eyebrow">{html.escape(' · '.join(meta_bits))}</p>
      <h2>{html.escape(p['title'])}</h2>
      <p>{html.escape(blurb)}</p>
      <span class="link-arrow">{len(p['photos'])} photographs</span>
    </div>
  </a>""")

    body = f"""
<section class="page-head">
  <div class="wrap">
    <h1>Gallery</h1>
    <p class="measure">{html.escape(SECTIONS['gallery_intro'])}</p>
  </div>
</section>

<section class="cards">
  <div class="wrap cards__grid">{"".join(cards)}</div>
</section>

{elsewhere_teaser()}

{about_section()}
"""
    return page("Gallery", body, "Gallery", SECTIONS["gallery_intro"],
                path="/gallery/")


def build_place(place):
    meta_bits = [b for b in (place.get("region"),
                             pretty_date(place.get("date"))) if b]
    film_link = ""
    if place.get("film"):
        film_link = ('<p class="band__cta"><a class="button" href="/films/">'
                     'Watch the film</a></p>')

    body = f"""
<section class="page-head page-head--place">
  <div class="wrap">
    <p class="eyebrow">{html.escape(' · '.join(meta_bits))}</p>
    <h1>{html.escape(place['title'])}</h1>
    <div class="measure">{paragraphs(place['body'])}</div>
  </div>
</section>

<section class="band band--flush">
  <div class="wrap">
    {photo_grid(place['photos'], place['title'])}
    {film_link}
  </div>
</section>

<section class="band band--quiet">
  <div class="wrap">
    <p class="band__cta"><a class="link-arrow" href="/gallery/">
      Back to the gallery</a></p>
  </div>
</section>
"""
    desc = place.get("gallery_blurb") or lead_sentence(place["body"])
    return page(place["title"], body, "Gallery", desc,
                path=f"/gallery/{place['slug']}/",
                share_image=place.get("hero"))


def build_404():
    body = """
<section class="page-head">
  <div class="wrap">
    <p class="eyebrow">Error 404</p>
    <h1>Off the map</h1>
    <div class="measure">
      <p>This page does not exist, or it has wandered off since you last
      looked. The <a href="/gallery/">gallery</a> and the
      <a href="/films/">films</a> are both still where they should be.</p>
    </div>
    <p style="margin-top:2.5rem"><a class="button" href="/">Back home</a></p>
  </div>
</section>
"""
    return page("Not found", body, "", "This page could not be found.")


def build_elsewhere():
    blocks = []
    for place in ELSEWHERE:
        meta = " · ".join(b for b in (place.get("region"),
                                      pretty_date(place.get("date"))) if b)
        blocks.append(f"""
<section class="elsewhere__place">
  <div class="wrap">
    <p class="eyebrow">{html.escape(meta)}</p>
    <h2>{html.escape(place['title'])}</h2>
    <div class="measure">{paragraphs(place['body'])}</div>
    {photo_grid(place['photos'], place['title'])}
  </div>
</section>""")

    body = f"""
<section class="page-head">
  <div class="wrap">
    <h1>Elsewhere</h1>
    <p class="measure">Places I passed through rather than stayed in. Each
    of these will get a page of its own once there is more of it.</p>
  </div>
</section>

<div class="elsewhere">{"".join(blocks)}</div>

<section class="band band--quiet">
  <div class="wrap">
    <p class="band__cta"><a class="link-arrow" href="/gallery/">
      Back to the gallery</a></p>
  </div>
</section>
"""
    return page("Elsewhere", body, "Gallery",
                "Shorter visits: " + ", ".join(p["title"] for p in ELSEWHERE) + ".",
                path="/gallery/elsewhere/")


def build_films():
    blocks = "".join(f'<div class="films__item">{film_block(f)}</div>'
                     for f in FILMS)
    body = f"""
<section class="page-head">
  <div class="wrap">
    <h1>Films</h1>
    <p class="measure">{html.escape(SECTIONS['films_intro'])}</p>
  </div>
</section>

<section class="films">
  <div class="wrap">{blocks}</div>
</section>

{about_section()}
"""
    return page("Films", body, "Films", SECTIONS["films_intro"],
                path="/films/",
                share_image=FILMS[0].get("poster") if FILMS else None)


# --------------------------------------------------------------------
# write
# --------------------------------------------------------------------

def write(rel, content):
    dest = OUT / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(content)
    return dest


def main():
    # public/photos is expensive to regenerate, so clear everything else.
    for item in OUT.iterdir() if OUT.exists() else []:
        if item.name == "photos":
            continue
        shutil.rmtree(item) if item.is_dir() else item.unlink()

    write("index.html", build_home())
    write("gallery/index.html", build_gallery_index())
    write("films/index.html", build_films())
    write("404.html", build_404())
    for p in JOURNEYS:
        write(f"gallery/{p['slug']}/index.html", build_place(p))
    if ELSEWHERE:
        write("gallery/elsewhere/index.html", build_elsewhere())

    # static assets
    (OUT / "css").mkdir(parents=True, exist_ok=True)
    (OUT / "js").mkdir(parents=True, exist_ok=True)
    shutil.copy(STATIC / "css/site.css", OUT / CSS_HREF.lstrip("/"))
    shutil.copy(STATIC / "js/site.js", OUT / JS_SRC.lstrip("/"))
    (OUT / "img").mkdir(parents=True, exist_ok=True)
    shutil.copy(STATIC / "img/favicon.png", OUT / FAVICON.lstrip("/"))

    # Cloudflare reads _headers from the root of the served directory.
    for loose in ("_headers", "_redirects"):
        src = STATIC / loose
        if src.is_file():
            shutil.copy(src, OUT / loose)


    # sitemap + robots
    urls = ["/", "/gallery/", "/films/"] + [f"/gallery/{p['slug']}/"
                                            for p in JOURNEYS]
    if ELSEWHERE:
        urls.append("/gallery/elsewhere/")
    today = date.today().isoformat()
    sitemap = "\n".join(
        f"  <url><loc>https://{SITE['domain']}{u}</loc>"
        f"<lastmod>{today}</lastmod></url>" for u in urls)
    write("sitemap.xml",
          '<?xml version="1.0" encoding="UTF-8"?>\n'
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
          f"{sitemap}\n</urlset>\n")
    write("robots.txt",
          "User-agent: *\n"
          "Allow: /\n"
          "Disallow: /preview/\n"
          "Disallow: /identify/\n"
          "Disallow: /_review/\n\n"
          f"Sitemap: https://{SITE['domain']}/sitemap.xml\n")

    pages = 3 + len(JOURNEYS) + (1 if ELSEWHERE else 0)
    photos = sum(len(p["photos"]) for p in GALLERIES) + len(HIGHLIGHTS)
    print(f"built {pages} pages, {len(FILMS)} films, {photos} photo slots")

    todo = [p["title"] for p in PLACES if is_true(p.get("needs_rewrite"))]
    if todo:
        print(f"copy still to rewrite: {', '.join(todo)}")

    wrong_hero = [
        p["title"] for p in PLACES
        if p.get("hero") and p["hero"] in MANIFEST
        and MANIFEST[p["hero"]]["group"] != p["slug"]
    ]
    if wrong_hero:
        raise SystemExit(
            "hero is not one of the place's own photographs: "
            + ", ".join(wrong_hero)
            + "\n(a film still or another place's frame has been used)"
        )

    if MISSING:
        for key in sorted(set(MISSING)):
            print(f"  !! photo not in manifest, skipped: {key}", file=sys.stderr)
        raise SystemExit(f"{len(set(MISSING))} photo(s) missing — "
                         f"run photos.py or fix the key")


if __name__ == "__main__":
    main()
