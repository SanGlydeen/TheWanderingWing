# Plan and status

Living document. I keep this current so you don't have to remember where
things stand. Last updated: 8 September 2026.

**Places now on file:** Canterbury, Chongqing, Devon, Dover, Kunming,
Lago Maggiore, Leshan, London, Menorca, Mount Siguniang, Segovia, Toledo.

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
| B1 | **Two questions, 7 photographs** — see [/identify/](https://thewanderingwing.com/identify/) | The spelling of "Sujo", and which of three November shots are Canterbury vs Dover. Everything else is filed: 95 photographs, 11 places. |
| B2 | **The copy, place by place** | Tell me what you actually remember about Siguniang, Segovia, Menorca, Lago Maggiore, London, Chongqing. I cut it down. 6 places still flagged. |
| B3 | **The tagline** | "I don't fly a machine, I fly" pins the site to the drone. Keep, change, or drop — your call, and it matters before camera work lands. |

---

## Next, in order

1. **Reorganise the photo library** — script written and dry-run clean
   (`reorganise.py`). Files by place with readable names, 14 byte-identical
   duplicates dropped, 59 new portraits folded in. **Waiting on B1.**
2. **Immersive hover** — currently the photo widens to the full screen
   width but keeps the row height, so it reads as a zoom rather than an
   immersion. Should fill the whole viewport, and contract as soon as the
   cursor leaves where the photo used to be.
3. **Rewrite the copy** with you (B2).
4. **Use the portraits** — 55 of the new photos are portrait, which fixes
   phone heroes cropping badly.

---

## Done

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
