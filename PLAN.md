# Plan and status

Living document. I keep this current so you don't have to remember where
things stand. Last updated: 8 September 2026.

**13 places, 116 photographs.** Canterbury, Chongqing, Devon, Dover,
Kunming, Lago Maggiore, Leshan, London, Menorca, Mount Siguniang, Segovia,
Suzhou, Toledo.

---

## Where we are

The site is **live on Cloudflare**, off Tilda, at
[thewanderingwing.com](https://thewanderingwing.com). Everything below is
polish and content.

---

## Blocked on you

Nothing moves on these until you answer.

| # | What I need | Why it's blocked |
|---|---|---|
| B1 | **The copy, place by place** | Tell me what you actually remember about each place and I cut it down. **12 places** now carry placeholder or old text. Start with any one — no need to do them all at once. |
| B2 | **The tagline** | "I don't fly a machine, I fly" pins the site to the drone. Keep, change, or drop — your call, and it matters before camera work lands. |

---

## Next, in order

1. **Use the portraits on phone heroes** — 55 portrait frames are now
   available; the hero still crops a landscape one.
3. **Rewrite the copy** with you (B1).
4. **Homepage features** — still the same five places. Worth deciding
   which of the thirteen belong there.

---

## Done

- **Immersive hover** — hovering a homepage photograph opens it to the
  whole viewport, with the writing as a card over it; it closes the moment
  the pointer leaves the patch of page the photograph came from. Desktop
  and fine-pointer only; touch and reduced-motion keep the plain layout.
- **Photo library reorganised** — one folder per journey, readable
  filenames, 14 duplicates dropped, all 59 new photographs filed. Public
  URLs went from `/photos/highlights/dji-20250704200720-0003-d.jpg` to
  `/photos/menorca/cavalleria-02.jpg`. Reversible via `reorganise-map.json`.
- **Six new places published** — Canterbury, Devon, Dover, Leshan, Suzhou,
  Toledo. Every place now shows all its photographs: Menorca 4 to 21,
  Chongqing 6 to 14, Mount Siguniang 12 to 23.
- **Working pages taken off the public site** — `/preview/` and
  `/identify/` are gone; review pages come as files from now on.
- **Rebuilt off Tilda** as static HTML, two dependency-free Python scripts
  (`photos.py`, `build.py`). No Node, nothing to rot.
- **Cloudflare Workers hosting**, deploying automatically from GitHub on
  every push. Apex and www, valid certificate, HTTP redirects to HTTPS.
- **Domain renewed** and moved to Cloudflare DNS. Registration stays at
  Namecheap. Reminder set for 20 Sep 2026 to check Tilda hasn't re-charged.
- **Photo pipeline** — originals stay untouched in iCloud; the build makes
  five sizes of each. An 11 MB frame becomes 733 KB full-size, 101 KB
  thumbnail. Photos cached 30 days.
- **Segovia published** — shot but never on the old site.
- **Stock placeholders removed** — the old "Coming Soon" strip was
  Unsplash photos by other photographers.
- **Chongqing, Kunming and Menorca galleries** created from photos you
  identified. Arenal d'en Castell widened to Menorca.
- **Real SVG logo** inlined as a sprite, coloured from CSS.
- **Layout**: hybrid on phones, side-by-side with hover on desktop.
  Highlights is a carousel; About is centred with an oval portrait.
- **Films page** aligned to the page rather than a floating centred column.
- **AI training crawlers blocked**; search and agent crawlers allowed.

### Bugs found and fixed along the way

- Highlights showed 5 photos, not 6 — a key pointed at a London shot filed
  under `highlights/`. Missing keys now stop the build instead of silently
  becoming an HTML comment.
- CSS and JS cached an hour under fixed names, so fresh HTML could pair
  with a stale script. Filenames now carry a content hash.
- Carousel arrows jumped on hover — centring used `translate`, hover used
  `transform`, and they compounded.
- A band across the hero photograph — the gradient held a constant opacity
  between 38% and 62%, and the slope change read as a line.
- The bird was squished in the header — my crop box was 500×250 but the
  bird's real bounds are 206×190, so it filled 41% of the width.

---

## How it works

See [README.md](README.md). Short version: originals live in iCloud and
are never modified; `photos.py` resizes them, `build.py` writes the site,
push to `main` and Cloudflare deploys.
