#!/usr/bin/env python3
"""Static site generator for The Wandering Wing.

Reads content/*.md, combines it with photo-manifest.json (written by
photos.py) and writes a complete static site into public/.

Deliberately dependency-free: it runs on the Python that ships with
macOS, so there is no toolchain to install or keep alive.

    python3 photos.py    # resize originals  (slow, only when photos change)
    python3 build.py     # generate the site (fast, run any time)
"""

import html
import json
import re
import shutil
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


def img(key, alt, sizes="100vw", cls="", eager=False, max_width=2400):
    """Render a responsive <img> for a manifest key like `london/img-5943`."""
    p = MANIFEST.get(key)
    if not p:
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


def aspect(key):
    p = MANIFEST.get(key)
    return p["aspect"] if p else 1.5


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

# Photos on the homepage highlight strip, in the order they appear.
HIGHLIGHTS = [
    "highlights/dji-20241130155638-0141-d",
    "highlights/dji-20250704203954-0062-d",
    "highlights/dji-20250930151411-0039-d-2",
    "highlights/img-3133",
    "highlights/img-4555",
    "highlights/img-4873",
]


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


ICON_IG = ('<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2.2c3.2 0 '
           '3.6 0 4.9.07 1.2.05 1.8.25 2.2.42.6.22 1 .48 1.4.9.44.43.7.83.92 '
           '1.42.17.4.37 1 .42 2.2.06 1.3.07 1.7.07 4.9s0 3.6-.07 4.9c-.05 '
           '1.2-.25 1.8-.42 2.2-.22.6-.48 1-.92 1.42-.42.42-.82.68-1.41.9-.4.'
           '17-1 .37-2.2.42-1.3.06-1.7.07-4.9.07s-3.6 0-4.9-.07c-1.2-.05-1.8-.'
           '25-2.2-.42-.6-.22-1-.48-1.42-.9-.42-.42-.68-.82-.9-1.41-.17-.4-.37'
           '-1-.42-2.2C2.2 15.6 2.2 15.2 2.2 12s0-3.6.07-4.9c.05-1.2.25-1.8.42'
           '-2.2.22-.6.48-1 .9-1.42.42-.42.82-.68 1.42-.9.4-.17 1-.37 2.2-.42C'
           '8.4 2.2 8.8 2.2 12 2.2m0 2.16c-3.14 0-3.5.01-4.74.07-1.15.05-1.77.'
           '24-2.18.4-.55.21-.94.47-1.35.88-.41.41-.67.8-.88 1.35-.16.41-.35 1'
           '.03-.4 2.18-.06 1.24-.07 1.6-.07 4.74s.01 3.5.07 4.74c.05 1.15.24 '
           '1.77.4 2.18.21.55.47.94.88 1.35.41.41.8.67 1.35.88.41.16 1.03.35 2'
           '.18.4 1.24.06 1.6.07 4.74.07s3.5-.01 4.74-.07c1.15-.05 1.77-.24 2.'
           '18-.4.55-.21.94-.47 1.35-.88.41-.41.67-.8.88-1.35.16-.41.35-1.03.4'
           '-2.18.06-1.24.07-1.6.07-4.74s-.01-3.5-.07-4.74c-.05-1.15-.24-1.77-'
           '.4-2.18a3.6 3.6 0 0 0-.88-1.35 3.6 3.6 0 0 0-1.35-.88c-.41-.16-1.0'
           '3-.35-2.18-.4-1.24-.06-1.6-.07-4.74-.07m0 3.67a5.97 5.97 0 1 1 0 1'
           '1.94 5.97 5.97 0 0 1 0-11.94m0 9.85a3.88 3.88 0 1 0 0-7.76 3.88 3.'
           '88 0 0 0 0 7.76m7.6-10.09a1.4 1.4 0 1 1-2.79 0 1.4 1.4 0 0 1 2.79 '
           '0"/></svg>')

ICON_YT = ('<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M23.5 6.5a3 3'
           ' 0 0 0-2.1-2.1C19.5 3.9 12 3.9 12 3.9s-7.5 0-9.4.5A3 3 0 0 0 .5 6.'
           '5C0 8.4 0 12 0 12s0 3.6.5 5.5a3 3 0 0 0 2.1 2.1c1.9.5 9.4.5 9.4.5s'
           '7.5 0 9.4-.5a3 3 0 0 0 2.1-2.1c.5-1.9.5-5.5.5-5.5s0-3.6-.5-5.5M9.6'
           ' 15.6V8.4l6.2 3.6-6.2 3.6"/></svg>')


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
         path=None):
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
<meta property="og:image" content="https://{SITE['domain']}{full_src(SITE['hero'], 1400)}">
<meta name="theme-color" content="#152739">
<link rel="icon" href="/favicon.png" type="image/png">
<link rel="apple-touch-icon" href="/favicon.png">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;1,300;1,400&display=swap">
<link rel="stylesheet" href="/css/site.css">
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

<script src="/js/site.js" defer></script>
</body>
</html>
"""


# --------------------------------------------------------------------
# sections
# --------------------------------------------------------------------

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
    {socials()}
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


def photo_grid(keys, place_title=""):
    """Lightbox-enabled grid. Wide frames span two columns."""
    cells = []
    for i, key in enumerate(keys):
        p = MANIFEST.get(key)
        if not p:
            cells.append(f"<!-- missing photo: {key} -->")
            continue
        wide = " grid__cell--wide" if p["aspect"] >= 2.2 else ""
        tall = " grid__cell--tall" if p["orientation"] == "portrait" else ""
        alt = f"{place_title}" if place_title else "Aerial photograph"
        cells.append(f"""
    <button class="grid__cell{wide}{tall}" type="button"
            data-full="{full_src(key)}"
            data-alt="{html.escape(alt)}">
      {img(key, alt, sizes='(max-width: 700px) 100vw, (max-width: 1100px) 50vw, 33vw', max_width=1400)}
    </button>""")
    return f'<div class="grid">{"".join(cells)}</div>'


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
          aria-label="Previous photograph">&#8249;</button>
  <div class="carousel__viewport">
    <ul class="carousel__track">{"".join(slides)}</ul>
  </div>
  <button class="carousel__nav carousel__nav--next" type="button"
          aria-label="Next photograph">&#8250;</button>
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
    {img(SITE['hero'], 'Aerial view', sizes='100vw', eager=True)}
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


def build_gallery_index():
    cards = []
    for p in GALLERIES:
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

<section class="band band--quiet">
  <div class="wrap">
    <h2 class="band__title">Coming soon</h2>
    <p class="band__text measure">More from Spain, Italy, and elsewhere.
      Stay tuned.</p>
  </div>
</section>

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
                path=f"/gallery/{place['slug']}/")


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
                path="/films/")


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
    for p in GALLERIES:
        write(f"gallery/{p['slug']}/index.html", build_place(p))

    # static assets
    for sub in ("css", "js", "img"):
        src = STATIC / sub
        if src.is_dir():
            shutil.copytree(src, OUT / sub, dirs_exist_ok=True)

    # Cloudflare reads _headers from the root of the served directory.
    for loose in ("_headers", "_redirects"):
        src = STATIC / loose
        if src.is_file():
            shutil.copy(src, OUT / loose)

    favicon = STATIC / "img" / "favicon.png"
    if favicon.exists():
        shutil.copy(favicon, OUT / "favicon.png")

    # sitemap + robots
    urls = ["/", "/gallery/", "/films/"] + [f"/gallery/{p['slug']}/"
                                            for p in GALLERIES]
    today = date.today().isoformat()
    sitemap = "\n".join(
        f"  <url><loc>https://{SITE['domain']}{u}</loc>"
        f"<lastmod>{today}</lastmod></url>" for u in urls)
    write("sitemap.xml",
          '<?xml version="1.0" encoding="UTF-8"?>\n'
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
          f"{sitemap}\n</urlset>\n")
    write("robots.txt",
          f"User-agent: *\nAllow: /\n\n"
          f"Sitemap: https://{SITE['domain']}/sitemap.xml\n")

    pages = 3 + len(GALLERIES)
    photos = sum(len(p["photos"]) for p in GALLERIES) + len(HIGHLIGHTS)
    print(f"built {pages} pages, {len(FILMS)} films, {photos} photo slots")

    todo = [p["title"] for p in PLACES if is_true(p.get("needs_rewrite"))]
    if todo:
        print(f"copy still to rewrite: {', '.join(todo)}")


if __name__ == "__main__":
    main()
