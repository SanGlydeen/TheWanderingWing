# The Wandering Wing — context for a new session

Read this first. It is written for a Claude session starting cold, with no
memory of how this project got here.

## What this is

Samuel Salesas's aerial photography site — **https://thewanderingwing.com**.
Drone films and photographs from his travels. A hobby project, not a
business. He is a Politics and Economics student.

It was originally built on **Tilda** (a website builder). In September 2026
we rebuilt it from scratch as a static site and moved it to **Cloudflare**.
The Tilda subscription runs out 4 October 2026 and is not being renewed.

## How it works

Two Python scripts and no dependencies. No Node, no framework, nothing to
rot. macOS `sips` does the image resizing.

    photos.py       reads originals from the iCloud library, writes
                    web-sized JPEGs into public/photos/, and records
                    everything in photo-manifest.json
    build.py        reads content/*.md plus the manifest, writes the
                    whole site into public/
    assignments.py  FOLDERS maps a place slug to its library folder;
                    read by photos.py on every build
    tools/          one-off migration scripts, already run

The **originals live in iCloud and are never modified**:

    ~/Library/Mobile Documents/com~apple~CloudDocs/Files/Personal/
      Hobbies/Photography/Drone/The Wandering Wing/

    Photos/YYYY-MM Place/    one folder per journey
    Brand/                   portrait + Logo/ subfolder
    Film stills/             YouTube thumbnails
    Video/                   the one large source film
    Photos/_superseded/      low-resolution duplicates, kept out of the way

**Deployment**: push to `main` on
github.com/SanGlydeen/TheWanderingWing (public) and Cloudflare Workers
builds and deploys automatically. `public/` is committed — Cloudflare
serves it as-is with no build step, so a large batch of photographs can
stall a single push; push a folder at a time.

See README.md for how to add a place. PLAN.md is the live status document.

## Rules that matter

- **A place page needs six photographs, or a film.** Below that it appears
  as a section on `/gallery/elsewhere/` and graduates automatically.
- **Never publish working or review pages to the live domain.** Samuel
  asked for this explicitly after `/preview/` and `/identify/` were briefly
  reachable. Build them locally and send the file instead.
- **Never invent detail in the copy.** Everything on the site is either
  something he said or something plainly visible in the frames. Several
  places consequently say very little, and that is correct. Ask rather
  than pad.
- **His voice**: first person, comparative, plain about what he felt. "My
  first time back in China since 2019." "More relaxed than the cities I
  had known." Not: benedictions, triads, "a city where sky and water seem
  to meet". He noticed the original copy read AI-written and disliked it.
- **Response style**: one line naming the problem or action, then numbered
  steps. He does not want essays when he is following along in a dashboard.

## Things that have bitten us

- **The browser pane cannot be trusted for anything animated.** It runs
  hidden and never repaints, so CSS transitions freeze at their start
  value and `requestAnimationFrame` never fires. Geometry can be measured;
  interactions cannot be seen. Samuel's eyes are the test.
- **This Mac's DNS resolver caches hard.** Check with `dig @1.1.1.1` and
  `curl --resolve`, never a plain curl, or you will wrongly conclude a
  deploy failed. His router (192.168.8.1) held the old delegation for
  hours after the nameserver switch.
- **`position: fixed` resolves against a transformed ancestor**, and
  `.feature` carries a transform from the scroll-reveal. Anything that
  must fill the viewport belongs in an overlay on `<body>`.
- **Stable filenames plus long caches go stale.** CSS, JS and the favicon
  carry content hashes for this reason. Photographs do not, so their cache
  is capped at thirty days.

## Open questions for Samuel

Four places say almost nothing because nothing is known about them:
**London**, **Suzhou**, **Devon**, **Leshan**. Also worth asking: is
Menorca somewhere he goes regularly rather than a one-off trip; were
Toledo and Canterbury/Dover day trips; and does he want his About
paragraph plained up or left as he wrote it.

The **tagline** — "I don't fly a machine, I fly" — ties the site to the
drone, which matters as camera work arrives. He has deferred deciding.

## Coming next

A separate session for **an album of 6,000+ files**: sort by date, infer
the place from the date, then he picks the highlights. Use EXIF timestamps
rather than filenames — the library mixes DJI and iPhone naming.
