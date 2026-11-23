# SPEC: Green-screen "proof behind me"

> **Using this template:** the skill copies this folder (and `_shared/` next to it) into its build folder (see `USE.md`), adds the
> fonts below to `assets/fonts/`, puts your SDR take in `~/Movies/Edits-inbox/`, fills `config.json`, then runs
> `$PY cut.py`,
> `npx --yes hyperframes@0.9.83 remove-background assets/cut.mp4 -o assets/cutout.webm`,
> `$PY shots.py` and `$PY build.py`, checks with
> `npx --yes hyperframes@0.9.83 check --json`, and renders the overlay `.mov` for Edits
> (`npx --yes hyperframes@0.9.83 render overlays --format mov -o renders/green-screen-proof-overlays.mov`).
> Needs HyperFrames (Node 22+), the skill's Python venv (plus Playwright for `shots.py`) and `../_shared/reeltools.py`.
> Fonts: Space Grotesk (`SpaceGrotesk.ttf`, variable, https://fonts.google.com/specimen/Space+Grotesk) and Space Mono
> (`SpaceMono-Regular.ttf`, https://fonts.google.com/specimen/Space+Mono), both SIL Open Font License.

Format file: the skill's `styles/green-screen-proof.md`. Source for the demo: a 34 s talking-head take
(source 20.86-55.00 s), cut out of its background with `hyperframes remove-background` (`assets/cutout.webm`, VP9
with alpha, ~12 min on CPU for that length). The proof behind the speaker is a **real** public web page (the demo
used a Wikipedia article), captured by `shots.py` in headless Chrome at iPhone width (412 css px, 4x = 1648 px wide).
Nothing on the page is edited: fundraising/notice banners are hidden, every collapsed section is opened.

## What's said, and the real line behind it (the demo's structure)
| On the reel | What's said | Behind (verbatim from the page) | Mark |
|---|---|---|---|
| 0.00-5.86 s | the opening claim, two sentences | top of the article: title + its first line | none |
| 5.86-16.98 s | the point the page backs up, two sentences | the lead paragraph, with the key phrase (two words) | red loop round each of the two words, drawn on the matching spoken word |
| 16.98-27.28 s | the second point, three sentences | a section further down, with one long key sentence (wraps onto three lines) | red underline under all three lines, drawn on the matching spoken word |
If the page's term differs from the spoken one, mark the page's term for the same thing, never edit the page.
An opinion the speaker says (e.g. "10x") is captioned as said, not shown as a stat.

## Cut (cut.py, config.json)
Demo: keep 20.86-40.30 s and 43.08-55.00 s (drops a list signpost because the reel starts at the second point;
edges measured on a 40 ms RMS envelope, not whisper's times, which ran 0.2-0.3 s early). **1.15x**. Voice **-14 LUFS**
(loudnorm TP -1.5). Length **27.28 s** (format: 20-45 s). Words re-transcribed on the cut (mlx_whisper
large-v3-turbo), "hyper" + "-focus" style splits merged so a caption never splits a word.

## Look (1080x1920)
| Element | Spec used | Format file says |
|---|---|---|
| Ground | newsprint `#F4F1EA` | same |
| Page frame | x 42, y 108, 996x1100, **6 px white** border, shadow 0 30 70 rgba(0,0,0,.28) + 0 4 12 rgba(0,0,0,.14) | top 55-65%, white 6 px frame + shadow |
| Hook | Space Grotesk Bold **60 px**, ink `#000` on highlighter `#FFF34F` stripe, square ends, **-1 deg**, 2 lines (`hook_lines`), padding 6/22/10, top **292 px**, 0-3.0 s | y ~200 |
| Hook motion | on at frame 0 (thumbnail) with a 1.04->1 settle (0.3 s expo.out); leaves as a marker wipe to the right, line by line (clip-path, 0.2 s power3.in, 0.06 s apart) | - |
| Source chip | Space Mono **28 px**, "Source: <source_site>", white on black 70%, radius 4, under the frame at x 42 | 24 px (raised to the 28 px phone floor) |
| Person | cut-out at **0.60** scale, bottom-centred: head top ~y 1100, chin ~y 1600, in front of the frame | bottom 40-45% (= 43% here) |
| Captions | Space Grotesk Bold **52 px**, white on black box radius **6**, padding 8/18/12, 2-3 words, break after punctuation; centre **y 1040** (between the page and the head) | y ~1600 |
| Caption entrance | box scale 0.92->1 + fade, 0.1 s power3.out | - |
| Marks | red `#E63946`, 4.5 px (page px), round caps, hand-drawn bezier paths drawn with stroke-dashoffset: loops 0.3 s each, underlines 0.14 s per line, power2.inOut; drawn in page coordinates so they sit on the real words (positions measured by `shots.py`) | red circle or underline |
| Background change | next page rises from +420 px with blur 14->0, opacity 0->1, 0.38 s power4.out (a fast scroll), on the first word of the sentence it backs up (`from_word`) | switch on the sentence |
| Camera on the page | re-frames to put the key text at 40% of the page height, zoom capped so wrapped key text never runs off the edges (zoom 1.42, or 1.22 for `circle`). When the key lines already sit in the top third and span the full width, the move resolves to no movement (no zoom). Text renders ~38 px. bg3 pulls back to 1.0 on `pullback_word` (0.5 s power2.inOut). | zoomed so the key line is big |
| Camera on the speaker | hard punch 1.0 -> **1.07** on `punch_word`, back on `punch_end_word` | - |
| Grade (media-treatment on the cut-out) | exposure **+0.06**, contrast **+0.04** (neutral, a touch bright to sit with the white page) | neutral, slightly bright |
| Pace | 1.15x | 1.1-1.3x |

### Why numbers moved
Instagram's UI covers y 0-268 and everything under y 1248 (HyperFrames safe-area table). The demo's framing is tight
(face from 30% to 72% of the frame), so at the format's size the y 1600 caption landed on the chin and mouth. Captions
moved to y 1040, between the proof and the head, never over the key line (which sits in the top third). Hook moved
from y 200 to 292 for the same reason.

## Sound (peak 1 frame after the picture; no music)
| Moment | Sound (file name `build.py` looks for in `assets/sfx/`) | Start / slot / volume (demo) |
|---|---|---|
| bg2 arrives (5.86 s) | soft whoosh (Edits: searchSoundEffects "whoosh"), `soft-whoosh-1.mp3` | 5.543 s, 1.0 s, 0.61 |
| loop drawn on the mark word | felt-marker squeak (Edits: searchSoundEffects "marker"), `marker.mp3` | 10.123 s, 0.5 s, 1.78 |
| bg3 arrives (16.98 s) | a different soft whoosh (Edits: searchSoundEffects "swoosh"), `soft-whoosh-2.mp3` | 16.813 s, 0.8 s, 0.51 |
| underline drawn on the mark word | pen scribbling on paper (Edits: searchSoundEffects "pen writing"), `pen-writing.mp3`, slice from 2.40 s | 18.863 s, 0.62 s, 3.0 |
Volumes were set from measurement so each hit is ~8 dB under the voice (-22 LUFS momentary against -14 LUFS);
re-measure with `../_shared/measure.py` when you use your own files.
SFX aren't shipped. Either drop your own files into assets/sfx/ with these names, or skip them in the overlay and add
them natively in Edits with searchSoundEffects + addSoundEffect. (`build.py` skips any file that isn't there.)
Music: add it in the Edits window yourself (library music goes silent in Claude exports) or use your own file.

## Overlay MOV
`renders/green-screen-proof-overlays.mov` = hook + source chip + captions on transparent. The page (with its red
marks) and the cut-out are the "background" and are left out: in Edits the member puts her own image behind her with
the green-screen tool and adds a red callout by hand.

## Banned here
An image without a real source; invented quotes; captions over the key line; text on the face; the same whoosh twice;
slow creeping zoom.

## How a member's version differs
- `config.json`: her take + `keep` ranges + `speed`, `hook_lines`, `source_site`, `pullback_word`, `punch_word`,
  `punch_end_word` (null skips that move), and exactly three `backgrounds` entries (bg1 opener + two marked pages):
  `url`, `anchor` (exact text near the top of the bit to show), `key` (exact text to mark), `mark` (`underline`,
  `circle-each`, `circle`), `from_word` (the phrase where she starts talking about it), `mark_word`.
- Then: `cut.py` -> `npx --yes hyperframes@0.9.83 remove-background assets/cut.mp4 -o assets/cutout.webm` ->
  `shots.py` -> `build.py`. `shots.py` only works for public web pages; for a screenshot or comment she supplies, drop
  the PNG in `assets/` as `bg2.png` etc. and give its key rectangle by hand in `assets/shots.json` (fractions of the
  image width). Blur private names.
- Wider framing (face higher in frame): she can go back to the format's captions on her chest; set `CAP_Y` in build.py
  to sit under her chin and above y 1248.
- Check the cut-out edge on her hair at full size before rendering.

## Rebuild
Needs `../_shared/` (reeltools.py: cut, word timings, sound placement, grade; check.sh; render.sh; measure.py).
`$PY cut.py && $PY build.py && ../_shared/check.sh .`
then `../_shared/render.sh "$PWD"` and `$PY ../_shared/measure.py .` (adjust any sound
outside 6-10 dB under and re-render with `MP4_ONLY=1`). `renders/` is not shipped: you render your own.
