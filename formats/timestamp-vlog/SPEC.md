# SPEC: Timestamp vlog

> **Using this template:** the skill copies this folder (and `_shared/` next to it) into its build folder (see `USE.md`), adds the
> fonts below to `assets/fonts/`, puts your SDR clips in `~/Movies/Edits-inbox/`, fills `config.json`, then runs
> `$PY cut.py` and `$PY build.py`, checks with
> `npx --yes hyperframes@0.9.83 check --json`, and renders the overlay `.mov` for Edits. Needs HyperFrames (Node 22+)
> and the skill's Python venv. Fonts: JetBrains Mono Medium (https://fonts.google.com/specimen/JetBrains+Mono, saved as
> `JetBrainsMono.ttf`, SIL Open Font Licence) and Instrument Serif Italic
> (https://fonts.google.com/specimen/Instrument+Serif, `InstrumentSerif-Italic.ttf`, SIL Open Font Licence).

Format file: the skill's `styles/timestamp-vlog.md`. Sources: the member's own clips. Every chip shows the clip's
**recorded** time from its file metadata (`com.apple.quicktime.creationdate`, local time), printed by `cut.py`.
Nothing is made up.

The demo build used four clips (example values, also in `config.json`):

| Clip | Window used | Chip shape |
|---|---|---|
| 1 | 0.0-2.8 s | `13 nov · 9:26 am · <label>` |
| 2 | 0.9-3.2 s | `13 nov · 9:26 am · <label>` |
| 3 | 2.8-5.0 s | `13 nov · 9:26 am · <label>` |
| 4 (final) | 0.0-3.9 s | `19 nov · 9:38 am · <label>` |

**Honest times only:** if the clips weren't all filmed on one day, keep the date in every chip so the times always read
forwards ("a week of ..." rather than "a day of ..."). A clip with no recorded time (screen recordings, exports) gets
no invented one: ask the member. Three takes of the same thing at the same minute ("again", "and again") is a joke
the real metadata can give you.

## Cut (cut.py)
Each clip trimmed to its window (+0.25 s handle for the swipe), 1080x1920, 30 fps, a keyframe every 30 frames, sound
removed (no voiceover in this style; the member adds an upbeat track in Edits).

## Look (1080x1920)
| Element | Spec used | Format file says |
|---|---|---|
| Chip | JetBrains Mono Medium **40 px**, white on black **60%**, radius **10**, padding **8/16**, tracking -0.02em, format `date · time · label`, lowercase am/pm | same |
| Chip position | top-left x **66**, y **280**, identical on every clip | x 60, y 140 |
| Chip change | the chip never moves; at the middle of each swipe the new words blur in (6 px -> 0, 0.13 s power2.out) | same spot and style |
| Opening title | Instrument Serif Italic **72 px**, lowercase title, white + soft shadow, centred at y 1010 (on the chest, under the chin), on at frame 0, blurs out at 1.28-1.5 s | optional, 72 px, first 1.5 s |
| Transitions | one swipe-left, **6 frames (0.2 s)**, power2.inOut, outgoing and incoming clips move together; the same on all three cuts | same swipe throughout |
| Clip lengths | 2.8 / 2.3 / 2.2 / 3.9 s (final held 3.9 s) | 1-3 s, final 3-4 s |
| Final result | 0.17 s white flash (0.85 -> 0) at 9.30 s with the shutter | shutter on the final result |
| Grade (media-treatment, the same on all four) | exposure **+0.08**, contrast **-0.10**, temperature **+0.10**, saturation **+0.03** | soft, bright, warm daylight |
| Length | **10.6 s** | 10-25 s |

### Why the chip moved
y 140 sits under Instagram's top bar (the safe band starts at y 269), so the chip is at y 280, x 66.

## Sound (peak 1 frame after the picture; no voice, no music in the file)
| Moment | Sound (file name the code looks for in `assets/sfx/`) | Start / slot / volume |
|---|---|---|
| swipe 1 (2.60 s) | soft whoosh, take 1 (`whoosh-1.mp3`; Edits: searchSoundEffects "whoosh") | 2.263 s, 0.8 s, 0.54 |
| swipe 2 (4.70 s) | soft whoosh, take 2 (`whoosh-2.mp3`; Edits: searchSoundEffects "soft whoosh") | 4.513 s, 0.8 s, 0.46 |
| swipe 3 (6.70 s) | quick swipe (`whoosh-3.mp3`; Edits: searchSoundEffects "swipe") | 6.673 s, 0.8 s, 0.49 |
| flash (9.30 s) | camera shutter (`shutter.mp3`; Edits: searchSoundEffects "camera shutter") | 9.313 s, 0.4 s, 0.86 |

Three different whoosh takes, never the same twice. Start times above are from the demo files (each start is set so
that file's peak lands one frame after the picture); your files give slightly different starts. Levels were set from
measurement to -22/-23 LUFS momentary, i.e. 8-9 dB under a -14 LUFS music bed the member adds.

SFX aren't shipped. Either drop your own files into assets/sfx/ with these names, or skip them in the overlay and add
them natively in Edits with searchSoundEffects + addSoundEffect. (`build.py` simply leaves out any file that isn't there.)

Music: add it in the Edits window yourself (library music goes silent in Claude exports) or use your own file.

## Overlay MOV
`renders/timestamp-vlog-overlays.mov` (not shipped: you render your own) = title + chips on transparent (no footage,
no flash, no sound). In Edits the member lays her clips in order with Edits' own swipe transition, then this on top.

## Banned here
Captions or voiceover; mixing transition types; times going backwards; a time that isn't the clip's real time.

## How a member's version differs
- `config.json`: `title`, and one entry per clip in time order: `src`, `media_start`, `dur`, `when`, `label`
  (+ `shutter_at` on the last one = seconds into it). `cut.py` prints each clip's recorded time: copy it into `when`.
  If a clip has none (screen recordings, exports), ask her for the time; never guess it.
- All on one day: drop the date from `when` ("9:02 am") for the format's original look.
- Then `cut.py` and `build.py`. Clip starts, swipes, chip swaps and sounds follow from the durations.

## Rebuild
Needs `../_shared/` (reeltools.py: cut, word timings, sound placement, grade; check.sh; render.sh; measure.py).
`$PY cut.py && $PY build.py && ../_shared/check.sh .`
then `../_shared/render.sh "$PWD"` and `$PY ../_shared/measure.py .` (adjust any sound
outside 6-10 dB under and re-render with `MP4_ONLY=1`).
