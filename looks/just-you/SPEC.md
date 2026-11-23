# SPEC: Just you (inspired by Taki Wong, @taki.gpt)

> **Using this template:** the skill copies this folder (and `_shared/` next to it) into its build folder (see `USE.md`), adds the
> fonts below to `assets/fonts/`, puts your SDR take in `~/Movies/Edits-inbox/`, fills `reel.json`, then runs
> `$PY cut.py` and `$PY build.py`, checks with
> `npx --yes hyperframes@0.9.83 check --json`, and renders the overlay `.mov` for Edits
> (`npx --yes hyperframes@0.9.83 render _overlay --format mov -o renders/just-you-overlays.mov`). Needs HyperFrames
> (Node 22+) and the skill's Python venv. Fonts: SF Pro (Apple, not shipped: build.py copies
> `/System/Library/Fonts/SFNS.ttf` from your own Mac into `assets/fonts/SFNS.ttf`); Inter ExtraBold as
> `assets/fonts/Inter-ExtraBold.ttf` (hook fallback) and Inter Bold as `assets/fonts/Inter-Bold.ttf` (default caption
> font), both from https://fonts.google.com/specimen/Inter (SIL Open Font Licence 1.1). If your brand has its own
> caption font, set `BRAND_CAP_FONT` / `BRAND_CAP_FILE` in build.py and drop the file in `assets/fonts/`.

**The look in one line:** your face full frame the whole way, a Taki-style boxed hook on frame 0, small ink captions on
your chest, and ONE real picture card only when you name a real thing. Everything else is just you.
Reference: Taki Wong, https://www.instagram.com/taki.gpt/ (the boxed-hook technique).

**Footage:** you only. The demo was a 16.22 s talking-head take at 1.3x, from two takes:
- seg0: a studio-mic take, one keep span = 10.84 s. It starts on a whole thought (the leading "Number two," dropped).
- seg1: an iPhone take in another room, two keep spans with one 0.28 s pause out = 5.40 s (the CTA).
- Cut points measured on a 10-20 ms RMS envelope (silence < -40 dBFS), never mid-word. No trim saving < 0.15 s.

## BRAND vs LOOK
The colours marked "brand" below come from the BRAND block at the top of `build.py`, which Claude fills from your
`profile.md` before each build. The defaults are neutral placeholders. Every other number is the look: keep it.

## Palette (only these)
| Token | Hex | Used for |
|---|---|---|
| brand ink | default `#141414` | caption box, hook-stack hard shadow, plate behind footage, card shadow tint |
| white | `#FFFFFF` | hook + CTA boxes, card frame, caption text |
| black | `#000000` | hook text (Taki measured `#000000`) |
| brand accent | default `#FF5A36` | the ONE accent: 6 px hard shadow on the caption box |
| brand cream | default `#FAF7F2` | not used here (kept for variants: card frame on dark rooms) |

## Type (1080x1920)
| Element | Font | Size / weight | Where |
|---|---|---|---|
| Hook | SF Pro (`/System/Library/Fonts/SFNS.ttf`, weight 800; Inter ExtraBold if SF Pro isn't there) | auto-fit from 92 px down in 2 px steps until widest line + padding <= 1000 px: **80 px** on the demo; line-height 1.2; box padding 15/30; radius 22 | centred, top y 290, one white box per line, boxes overlap 2 px (touching), ONE hard shadow 12/12 px brand ink on the whole stack |
| CTA box | same as hook, one line (your CTA text) | 80 px | top y 290 |
| Captions | brand caption font (default Inter Bold) | 54 px / 700, line 1.1, box padding 12/24/14, radius 12 | centred, box top y 1500 (centre ~1540), on your chest |
| Card | a real screenshot of the thing you name | 880 px wide (demo image 864x460), white 8 px frame, radius 24, shadow `0 24px 60px` brand ink at .35 + `0 3px 10px` brand ink at .18 | centred, top y 280, bottom y ~756; head top ~y 785 after the slide-down |

## Layout
- Take slid DOWN 240 px on the demo's second take (top strip = the top 60 px of your own frame, stretched + Gaussian
  blur sigma 14), so the card sits above your head. The first take wasn't slid (head top ~y 580 already clears the hook).
- Nothing readable above y 260; nothing over your face (checked in snapshots at 0, 3.2, 4, 7, 11, 13.7, 14.4, 16.1 s
  on the demo).

## Motion
| Moment (spoken anchor) | Time on the demo | Move |
|---|---|---|
| Hook | 0 - 3.35 s (`hook.until` - 0.05) | fully set on frame 0 (= cover); out: opacity 0 + blur 0 -> 8 px, 0.18 s power2.in |
| Captions | from 3.35 s | 1-3 words, max 16 chars, break at punctuation / a pause >= 0.15 s / a take change; open 0.04 s before the first word; pop scale 0.9 -> 1, 0.12 s back.out(2); hard swap to the next group; no word highlight. Off during the hook and the CTA box. 18 groups on the demo |
| CTA box | `cta.from` - 0.03 = 13.45 s -> `cta.until` - 0.06 = 14.20 s | in: opacity 0 -> 1, scale 1.06 -> 1, 0.16 s expo.out; out: opacity, 0.14 s power2.in |
| Card | `cards[].from` - 0.03 = 14.23 s -> end | in: y -40 -> 0, opacity, blur 10 -> 0, 0.35 s power3.out; holds to the last frame |
| Cut seg0 -> seg1 | 10.84 s | hard cut (new room) |
Card on screen 2.0 s of 16.2 s (12%): the rest is just you.

## Sound (no music)
SFX aren't shipped. Either drop your own files into assets/sfx/ with these names, or skip them in the overlay and add
them natively in Edits with searchSoundEffects + addSoundEffect. (build.py skips any file that isn't there.)
| Moment | Sound (file name build.py looks for) | Volume | Measured on the demo |
|---|---|---|---|
| CTA box lands | card snap, `card-snap.mp3` (Edits: searchSoundEffects "snap") | 0.98 | peak momentary -24.0 LUFS = 10.0 dB under the voice |
| Card lands | paper slide, `paper-slide-1.mp3` (Edits: searchSoundEffects "paper slide") | 0.30 | peak momentary -21.9 LUFS = 7.9 dB under the voice |
- Start = picture moment + 1 frame (0.033 s) - the file's loudest 10 ms (build.py `peak()`).
- Voice: each segment two-pass loudnorm to -14 LUFS, then a -3 dBFS peak limiter (alimiter, attack 5 ms, release 50 ms).
  The demo's iPhone take came in at -22.5 LUFS. Without the limiter, AAC overs (+1.5 dBFS) made HyperFrames turn the
  whole mix down 0.7 dB (`audio_lowered`), landing at -14.7 LUFS.
- Music: add it in the Edits window yourself (library music goes silent in Claude exports) or use your own file.

## Grade (media-treatment, never CSS filters on footage)
- Studio-style take: none. Natural.
- iPhone take in a white-walled room (already HDR -> SDR): temperature +0.05 only (it read cold).

## Files
`reel.json` (everything that changes per take) -> `cut.py` (segments + word timings) -> `build.py` (index.html +
`_overlay/index.html`) -> `npx hyperframes check` -> `measure.py` (effect levels) -> render (not shipped: you render
your own).

## Banned here
Zooms, music, emoji stickers, GIFs, a second accent colour, a quoted line of text as a card, text over your face,
fade-and-slide-up on everything, any card that isn't a picture of a real thing you name.

## How a member's version differs
- `reel.json`: your take(s) and keep spans, your hook (2 lines, 5-9 words, one emoji, never 🚀), your CTA words (a
  comment keyword only if you have a real keyword funnel), and a card only for a real thing you name (your own
  screenshot, product page or a real logo). No real thing named = no card.
- Your colours and caption font: the BRAND block in `build.py`, filled from your `profile.md`.
- Your words: `cut.py` re-transcribes; proofread the printed line and add brand spellings to `word_fixes`.
- SF Pro is copied from your own Mac at build time (Apple's font, not shipped). If it isn't there: Inter ExtraBold.
- Slide-down 120-240 px only if a card needs the room. Warmth only if your room is cold.
- In Edits: use `renders/just-you-overlays.mov` (or the hook PNG) over your take; cut, 1.3x and captions are native.
