#!/usr/bin/env python3
"""Build side-by-side layout options into public/preview/.

Temporary: this exists so Samuel can compare homepage treatments on a real
phone rather than from a screenshot. Delete this file and public/preview/
once a layout is chosen.

    python3 build.py && python3 preview.py
"""

import html
from pathlib import Path

import build

OUT = build.ROOT / "public" / "preview"

VARIANTS = [
    ("a", "Immersive", "Full screen per place, text floating over the photo"),
    ("b", "Browsable", "Photo and text side by side, alternating"),
    ("c", "Hybrid", "Wide photo, text on paper below it"),
]


def switcher(current):
    links = "".join(
        f'<a href="/preview/{key}/"{" class=\"on\"" if key == current else ""}>'
        f'{label}</a>'
        for key, label, _ in VARIANTS
    )
    return (f'<div class="switch"><span>Layout</span>{links}'
            f'<a class="switch__live" href="/">Live site</a></div>')


def blocks(variant):
    out = []
    for i, place in enumerate(build.FEATURED):
        meta = " · ".join(b for b in (place.get("region"),
                                      build.pretty_date(place.get("date"))) if b)
        title = html.escape(place["title"])
        body = build.paragraphs(place["body"])
        eyebrow = f'<p class="eyebrow">{html.escape(meta)}</p>'

        if variant == "a":
            # Photo fills the viewport; the words sit on it.
            side = "left" if i % 2 else "right"
            out.append(f"""
<section class="v-imm v-imm--{side}">
  {build.img(place['hero'], place['title'], sizes='100vw',
             eager=(i == 0), max_width=2400)}
  <div class="v-imm__card">
    {eyebrow}<h2>{title}</h2>{body}
  </div>
</section>""")

        elif variant == "b":
            side = "left" if i % 2 == 0 else "right"
            out.append(f"""
<article class="feature feature--{side}">
  <div class="feature__media">
    {build.img(place['hero'], place['title'],
               sizes='(max-width: 900px) 100vw, 62vw', max_width=2000)}
  </div>
  <div class="feature__body">{eyebrow}<h2>{title}</h2>{body}</div>
</article>""")

        else:
            # Photo gets the width; the words get a readable column under it.
            out.append(f"""
<section class="v-hyb">
  <div class="v-hyb__media">
    {build.img(place['hero'], place['title'], sizes='100vw',
               eager=(i == 0), max_width=2400)}
  </div>
  <div class="v-hyb__body">{eyebrow}<h2>{title}</h2>{body}</div>
</section>""")

    return "".join(out)


def render(key, label, blurb):
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>{label} · layout option</title>
<link rel="icon" href="/favicon.png" type="image/png">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;1,300;1,400&display=swap">
<link rel="stylesheet" href="/css/site.css">
<link rel="stylesheet" href="/css/preview.css">
</head>
<body class="preview">
{switcher(key)}
<p class="preview__note"><strong>{html.escape(label)}</strong> — {html.escape(blurb)}</p>
<main>{blocks(key)}</main>
<p class="preview__note preview__note--end">End of sample. Switch layouts above.</p>
</body>
</html>
"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for key, label, blurb in VARIANTS:
        d = OUT / key
        d.mkdir(exist_ok=True)
        (d / "index.html").write_text(render(key, label, blurb))

    index = "".join(
        f'<li><a href="/preview/{k}/"><strong>{l}</strong><span>{b}</span></a></li>'
        for k, l, b in VARIANTS)
    (OUT / "index.html").write_text(f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex"><title>Layout options</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400&display=swap">
<link rel="stylesheet" href="/css/site.css">
<link rel="stylesheet" href="/css/preview.css"></head>
<body class="preview"><div class="wrap preview__index">
<h1>Layout options</h1>
<p class="measure">Three treatments of the same five places. Look on your
phone as well as a laptop &mdash; they feel different.</p>
<ul>{index}</ul>
<p><a class="link-arrow" href="/">Back to the live site</a></p>
</div></body></html>""")

    print(f"wrote {len(VARIANTS)} layout previews to public/preview/")


if __name__ == "__main__":
    main()
