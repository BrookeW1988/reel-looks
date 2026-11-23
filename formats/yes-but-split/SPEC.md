# SPEC: Yes... but split

> **Using this template:** the skill copies this folder (and `_shared/` next to it) into its build folder (see `USE.md`), adds the
> fonts below to `assets/fonts/`, puts your two SDR clips in `~/Movies/Edits-inbox/`, fills `config.json`, then runs
> `$PY cut.py` and `$PY build.py`, checks with
> `npx --yes hyperframes@0.9.83 check --json`, and renders the overlay `.mov` for Edits. Needs HyperFrames (Node 22+)
> and the skill's Python venv. Fonts: Anton (https://fonts.google.com/specimen/Anton, `Anton-Regular.ttf`, SIL Open
> Font Licence) and Inter Bold (https://fonts.google.com/specimen/Inter or https://rsms.me/inter/, a static Bold TTF
> saved as `Inter-Bold.ttf`, SIL Open Font Licence).

Format file: the skill's `styles/yes-but-split.md`. Sources: the member's own clips.
- **YES (the dream):** a bright, sunny clip, outside, talking to camera. In the demo: 0.00-3.95 s of the source,
  slowed to **0.7x** (5.67 s).
- **BUT (the catch):** the less glamorous reality, e.g. at the desk. In the demo: 0.20-5.84 s, opening on a blank stare
  off to the side (the punchline face), then talking.

Labels follow the format's own formula: "YES: <the dream>" / "BUT: <the catch>". A joke, not a claim, no numbers.

## Look (1080x1920)
| Element | Spec used | Format file says |
|---|---|---|
| Layout | two halves 1080x**957** + **6 px** white divider (957+6+957 = 1920); each clip `object-fit: cover`, no letterboxing, no stretch | top/bottom halves, 6 px white divider |
| Crops | YES window at 28% down the clip, BUT window at 58% down: the whole face in each half, clear of the labels (x 74-330) | crop to fill, no stretched faces |
| Label | Anton **72 px**, caps, white, **6 px** black outline (12 px stroke under the fill), line-height 1.05 | same |
| Sub-label | Inter Bold **40 px**, white, **4 px** outline (8 px stroke under the fill), 2 short lines | same |
| Label position | x **74**; YES top **292** (y 60 is under Instagram's top bar), BUT top **1023** (= 60 px into its half) | x 50, y 60 within the half |
| Timing | both clips play together the whole time; YES label on from frame 0; **BUT label lands 0.8 s later** (scale 1.35->1, blur 10->0, 0.16 s expo.out), its sub-label 0.1 s after (x -14->0, 0.18 s power3.out), then everything holds still | together, or BUT 0.5-1 s later |
| Grade YES (media-treatment) | exposure **+0.08**, contrast **+0.04**, temperature **+0.12**, saturation **+0.18** | bright, warm, +saturation |
| Grade BUT (media-treatment) | exposure **-0.08**, contrast **-0.02**, temperature **-0.15**, saturation **-0.30** | cooler, -saturation, slightly dim |
| Length | **5.65 s** | 5-12 s |

## Sound
One record scratch (Edits: searchSoundEffects "record scratch"; file name the code looks for:
`assets/sfx/record-scratch.mp3`) with its peak one frame after BUT lands: in the demo it started at 0.213 s, 1.2 s
slot, volume 0.18 (set from the render measurement), 0.15 s fade-out. No voice (both clips muted: the style is
labels + trending audio the member adds in Edits). Level set to sit under a -14 LUFS track.

SFX aren't shipped. Either drop your own files into assets/sfx/ with these names, or skip them in the overlay and add
them natively in Edits with searchSoundEffects + addSoundEffect. (`build.py` leaves the scratch out if the file isn't there.)

Music: add it in the Edits window yourself (library music goes silent in Claude exports) or use your own file.

## Overlay MOV
`renders/yes-but-split-overlays.mov` (not shipped: you render your own) = both labels (with the BUT slam) on
transparent. In Edits the member builds the split screen from her two clips, grades each half, then lays this on top.

## Banned here
Captions; the same grade on both halves (the contrast is the joke); letterboxing or squashed faces; labels longer than
a one-second read.

## How a member's version differs
- `config.json`: `yes` and `but` each take `src`, `keep` [start, end], `speed`, `label`, `sub` (1-2 short lines) and
  `focus_y` (0 = show the top of the clip, 1 = the bottom: move it until her face fills the half and clears the
  label). `but_delay` sets the comic beat (0 = both labels from frame 0).
- Make both clips the same length: slow the shorter one with `speed` (0.7 in the demo) or trim the longer.
- Then `cut.py` and `build.py`. Grades: re-run `rt.grade("#v-yes", {...}, "grade-yes.txt")` and
  `rt.grade("#v-but", {...}, "grade-but.txt")` (from `../_shared/reeltools.py`, with the numbers in the Look table) if
  her footage is darker or warmer than the demo's. `grade-yes.txt` / `grade-but.txt` are re-inserted on every build.

## Rebuild
Needs `../_shared/` (reeltools.py: cut, word timings, sound placement, grade; check.sh; render.sh; measure.py).
`$PY cut.py && $PY build.py && ../_shared/check.sh .`
then `../_shared/render.sh "$PWD"` and `$PY ../_shared/measure.py .` (adjust any sound
outside 6-10 dB under and re-render with `MP4_ONLY=1`).
