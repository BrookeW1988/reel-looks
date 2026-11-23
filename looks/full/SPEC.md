# SPEC: Full (Just you with more layered on)

> **Using this template:** the skill copies this folder (and `_shared/` next to it) into its build folder (see `USE.md`), adds the
> fonts below to `assets/fonts/`, puts your SDR take in `~/Movies/Edits-inbox/`, fills `reel.json`, then runs
> `$PY cut.py` and `$PY build.py`, checks with
> `npx --yes hyperframes@0.9.83 check --json`, and renders the overlay `.mov` for Edits
> (`npx --yes hyperframes@0.9.83 render _overlay --format mov -o renders/full-overlays.mov`). Needs HyperFrames
> (Node 22+) and the skill's Python venv. Fonts: SF Pro (Apple, not shipped: build.py copies
> `/System/Library/Fonts/SFNS.ttf` from your own Mac into `assets/fonts/SFNS.ttf`); Inter ExtraBold as
> `assets/fonts/Inter-ExtraBold.ttf` (hook fallback + default caption font) from
> https://fonts.google.com/specimen/Inter (SIL Open Font Licence 1.1). If your brand has its own caption font, set
> `BRAND_CAP_FONT` / `BRAND_CAP_FILE` in build.py and drop the file in `assets/fonts/`.

**The look in one line:** the Just you base (face full frame, Taki-style boxed hook, ink captions) plus hard
punch-ins, a numbered list card, one accent-coloured keyword per caption and (optional) animated stickers of your own
art, but never more than one extra thing on screen at once (build.py refuses to build if two overlap).

**Footage:** you only. The demo was one talking-head take, two keep spans with one 0.50 s pause out (before the
numbered point), at 1.3x = 15.20 s.

## BRAND vs LOOK
The colours marked "brand" below come from the BRAND block at the top of `build.py`, which Claude fills from your
`profile.md` before each build. The defaults are neutral placeholders. Every other number is the look: keep it.

## Palette (only these)
| Token | Hex | Used for |
|---|---|---|
| brand ink | default `#141414` | caption box, hook + list-card hard shadows, plate, sticker shadow tint |
| white | `#FFFFFF` | hook boxes, list label, caption text, sticker die-cut edge |
| black | `#000000` | hook + list label text |
| brand accent | default `#FF5A36` | ONE keyword per caption, caption box shadow, list number tile |
| brand cream | default `#FAF7F2` | not used here |
Spec allows yellow `#FFD84D` for GIF frames: not used on the demo.

## Type (1080x1920)
| Element | Font | Size / weight | Where |
|---|---|---|---|
| Hook | SF Pro (`SFNS.ttf`) 800; Inter ExtraBold if SF Pro isn't there | auto-fit from 92 px: **84 px** on the demo; line 1.2; padding 15/30; radius 22; boxes overlap 2 px | centred, top y 290, brand-ink hard shadow 12/12 |
| List number | SF Pro 800 | 84 px, white on an accent tile (min 132 px wide, radius 22 left corners) | x 64, top y 300 |
| List label | SF Pro 800 | 72 px, black on white (padding 22/34/24/28, radius 22 right corners) | beside the number; brand-ink hard shadow 10/10 on the pair |
| Captions | brand caption font (default Inter ExtraBold) | 56 px / 800, line 1.1, box padding 12/24/14, radius 12, accent 6/6 hard shadow | centred, box top y 1498 (centre ~1540) |
| Stickers (optional) | your own sprite art (frame PNGs in `assets/sprites/<name>/f0.png`, `f1.png` ...) | 270 px tall (partner sprite 78%), white 4 px die-cut edge + `0 14px 18px` brand ink at .35 | top y 300, 56 px from the left or right edge |

## Motion (cut clock; every moment is a spoken anchor in reel.json; times are from the demo)
| Time | Anchor | What |
|---|---|---|
| 0 - 4.25 s | `hook.until` | hook fully set on frame 0; out: opacity + blur 0 -> 8 px, 0.18 s power2.in |
| 1.44 - 2.44 s | zoom 1 `at` -> `to` | punch 1.12 (hard cut in and out, `gsap.set`) |
| 4.27 - 5.63 s | list card `from` -> `until` | list card "03" + label: in x -760 -> 0 + blur 14 -> 0, 0.42 s power4.out; number scale 1.35 -> 1, 0.22 s expo.out at +0.18 s; out x -760 + blur, 0.24 s power3.in |
| 6.24 - 6.92 s | zoom 2 | punch 1.12 |
| 6.89 - 9.49 s | sticker 1 | a typing sprite (right corner), flips 2 frames at 6 fps; in scale 0.55 -> 1, rotate 8 -> 3, 0.32 s back.out(1.7); out scale 0.8 + fade 0.18 s |
| 10.94 - 11.72 s | zoom 3 | punch 1.25 |
| 12.42 - 13.62 s | zoom 4 | punch 1.25 |
| 13.59 s - end | sticker 2 -> END | a cheering sprite + a partner sprite (left corner), 6 fps |
- Zoom pivot: x 540, y 1380 (the chin line), so a punch grows your face UP and never pushes your chin into the captions.
- Gaps between visual changes: max 2.57 s on the demo (spec: one every 2-4 s).
- Captions: after the hook, 1-3 words, max 16 chars; group pops 0.9 -> 1 (0.12 s back.out(2)); each word pops 0.9 -> 1
  as it is said (0.1 s back.out(2.5)); the keyword is the brand accent and lands at 1.05. 14 groups on the demo.
  Keywords come from `reel.json` (first one in a group wins).
- No sticker art? The sticker moments are skipped cleanly; add a GIF in Edits at that moment instead, or leave it out.

## Sound (no music; levels = peak momentary loudness read from the rendered overlay's effects stem on the demo)
SFX aren't shipped. Either drop your own files into assets/sfx/ with these names, or skip them in the overlay and add
them natively in Edits with searchSoundEffects + addSoundEffect. (build.py skips any file that isn't there.)
Finished demo reel: -14.0 LUFS integrated, -1.5 dBTP.
| Moment | Sound (file name build.py looks for) | Volume | Measured peak momentary vs -14 LUFS voice |
|---|---|---|---|
| List card in | soft whoosh, `soft-whoosh-2.mp3` (Edits: searchSoundEffects "whoosh") | 0.52 | -21.9 LUFS, 7.9 dB under |
| List card out | a different, quicker swoosh, `swoosh.mp3` (Edits: searchSoundEffects "swoosh") | 0.30 | -25.3 LUFS, 11.3 dB under (7.9 dB under the speech at that moment) |
| Typing sticker | keyboard typing, about 2 s, `typing_2s.mp3` (Edits: searchSoundEffects "typing") | 1.25 | -20.0 LUFS in the render, 6.0 dB under (predicted -23.0) |
| Biggest punch | soft thud, `soft-thud.mp3` (Edits: searchSoundEffects "thud") | 0.40 | -22.9 LUFS, 8.9 dB under |
| Cheer sticker | card pop, `card-pop.mp3` (Edits: searchSoundEffects "pop") | 1.17 | -24.0 LUFS, 10.0 dB under |
- Hits start at picture + 1 frame - the file's loudest 10 ms; the typing starts on its first key with the sticker's first frame.
- Voice: two-pass loudnorm to -14 LUFS, then a -3 dBFS peak limiter in cut.py.
- Two different whooshes in and out (never the same whoosh twice). The other punches are silent on purpose.
- Music: add it in the Edits window yourself (library music goes silent in Claude exports) or use your own file.

## Grade (media-treatment)
Contrast +0.05, saturation +0.05. No filters.

## Banned here
Two extras at once; slow pushes; more than one accent word per caption; GIFs over your face; stock/AI faces; invented
numbers (any number on screen is one you say yourself); the same whoosh twice; music in the overlay.

## How a member's version differs
- `reel.json`: your keep spans, hook, list cards (number + the label you say), sticker moments, zoom anchors and
  keywords, all as spoken phrases. build.py checks the one-extra-at-a-time rule and prints the gap list.
- Your colours and caption font: the BRAND block in `build.py`, filled from your `profile.md`.
- Stickers: your own brand art (frame PNGs in `assets/sprites/`) or Edits' GIF library (moment map in the skill's
  `SKILL.md`), or none. Same size (~28% width), same corners, ~one every 8-10 s.
- Zooms are native in Edits (keyframe the take); the overlay MOV carries everything else.
- SF Pro comes from your own Mac; Inter ExtraBold if it isn't there.
