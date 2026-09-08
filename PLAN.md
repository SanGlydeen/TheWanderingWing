# Plan and status

Living document. I keep this current so you don't have to remember where
things stand. Last updated: 8 September 2026, after the repository tidy.

**13 places, 106 photographs.** Canterbury, Chongqing, Devon, Dover,
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
| B1 | **Read the copy and correct it** | I have written all thirteen places short and factual, using only things you actually told me or that are plainly visible in the frames. Nothing is invented — which also means several places say very little. Add a real memory to any of them and I will work it in. |
| B2 | **Test the immersive hover** | Desktop only. Reminder set for 9 Sep. |

---

## Next, in order

1. **The 6,000-file album** — its own session. Sort by date, infer the
   place from the date, then you pick the highlights.
2. **Whatever B1 turns up** — the four thin places especially.
3. **Turn on Cloudflare Web Analytics** — free, no cookie banner, one
   toggle in the dashboard. I argued for Cloudflare partly because of it
   and then never enabled it.

---

## Done

- **Content integrity checked.** Kunming was fronted by its YouTube
  thumbnail rather than a photograph; the build now refuses a hero from
  outside its own place. Kunming was also labelled June when none of its
  photographs are from June — the June visit is the film — so it reads
  July now, with the June story kept in the writing. Two frames in Mount
  Siguniang turned out to be 1200px web copies of shots already there at
  full size; they are out of the set. Also verified: every hero is in its
  own photo list, feature numbers run 1-5 with no gaps, no photograph
  appears under two places, and every other place's date matches when its
  photographs were taken.
- **CLAUDE.md written** so a new session understands the project cold.
- **Repository tidied.** One-off scripts moved to `tools/` and
  `reorganise.py` now refuses to run twice — it had already been applied,
  and a second run would have refiled everything. Dropped three published
  logo variants nothing loaded, an unused helper, an orphaned CSS rule, an
  empty `templates/` directory and a stale `.gitignore` entry. `README.md`
  documents what each file is for.
- **Favicon content-hashed.** It sat at a stable path under a thirty-day
  cache, so changing the logo would not have reached anyone for a month —
  the same bug already fixed for CSS and JS.
- **Structure audited.** A place earns its own page once it has six or more
  photographs, or a film. Seven qualify; the other six gather on one
  *Elsewhere* page as titled sections and graduate automatically as they
  grow. Homepage features the five strongest.
- **Copy rewritten** across all thirteen places and the three section
  intros — short and factual, nothing invented.
- **Portrait photographs used properly.** The phone hero is now an
  art-directed portrait frame rather than a cropped landscape, and the
  galleries lay out in columns so portrait and landscape can sit together
  at their own proportions.
- **Alt text** now describes each frame from its filename — "Changping
  Valley, Mount Siguniang" rather than "Aerial photograph".
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
