# SPEC: Serialised episode

> **Using this template:** the skill copies this folder (and `_shared/` next to it) into its build folder (see `USE.md`), adds the
> fonts below to `assets/fonts/`, puts your SDR take in `~/Movies/Edits-inbox/`, fills the EPISODE block in `build.py`
> and SRC / KEEP / SPEED / SCRIPT in `cut.py` (this format has no separate config file), then runs
> `$PY cut.py` and `python3 build.py`, checks with
> `npx --yes hyperframes@0.9.83 check --json`, and renders the overlay `.mov` for Edits
> (`npx --yes hyperframes@0.9.83 render overlays --format mov -o renders/serialised-episode-overlays.mov`).
> Needs HyperFrames (Node 22+) and the skill's Python venv. Fonts: Archivo (`Archivo.ttf`, variable,
> https://fonts.google.com/specimen/Archivo) and Archivo Black (`ArchivoBlack-Regular.ttf`,
> https://fonts.google.com/specimen/Archivo+Black), both SIL Open Font License.

Format file: the skill's `styles/serialised-episode.md`. Reference: https://www.instagram.com/reel/DbDWjWvIv6k/

The demo episode = the series premise line + one point from a longer list take. `cut.py` keeps six source ranges,
all edges in measured dips (silencedetect -20 dB + 30 ms RMS envelope). The numbers below are the demo's
(example values: yours come from your own take):

| Keep (source s) | What it holds |
|---|---|
| 2.03-4.115 | the series premise line, part 1 (a different hook from the same take was dropped) |
| 5.95-9.62 | the series premise line, part 2 |
| 40.93-42.95 | "Number three is <topic>." (the spoken episode number) |
| 43.12-47.72 | the point, sentence 1 |
| 48.08-50.50 | sentence 2 (keeps the speaker's deliberate beat before the payoff word) |
| 50.80-55.00 | the closing sentence |

Speed 1.15x (format: 1.1-1.3x). Result 16.5 s (format: 15-35 s). Voice loudnorm two-pass to -14 LUFS, TP -1.5.
Word timings: mlx_whisper large-v3-turbo run on the CUT file, text replaced by the proofread SCRIPT by position
(whisper heard "brain slack hours" for "brains like ours" in the demo), two edge snaps (w0 end 0.40, w1 start 0.55).

## Palette (only these)
| Token | Hex | Used for |
|---|---|---|
| brand accent (default `#FF5A36`, tomato) | `BRAND_ACCENT` | badge pill, "#3" text, this episode's tick fill, keyword chips, topic highlighter (38%) |
| brand ink (default `#141414`) | `BRAND_INK` | topic and caption text, past-episode ticks (82%) |
| brand cream (default `#FAF7F2`, off-white) | `BRAND_CREAM` | topic box, caption boxes, the empty current tick (92%) |
| white | `#FFFFFF` | badge text, "#3" tile |

## Type (1080x1920)
| Element | Font | Size / weight | Where |
|---|---|---|---|
| Badge (series name) | Archivo Black | 44, caps, tracking +1% | accent pill, padding 16/26, x 72, **top 272** |
| "#3" tile | Archivo Black | 40 | white tile inside the pill, radius 12 |
| Episode rail | 3 ticks 38x9, gap 8, radius 5 | | 14 px under the badge |
| Topic line (3 words) | Archivo SemiBold | 56 / 600, -1.5% | cream box, radius 14, padding 14/26, 16 px under the rail |
| Captions | Archivo Bold | 48 / 700 | ink on cream box, radius 14, padding 12/22, top 1495 (centre ~1530), 2-3 words |

Moved from the format file, on purpose: badge y 140 -> 272 and x 60 -> 72 (HyperFrames' Instagram Reels clear
band is y 14-65%, x 6-94%; 140 sits under the Reels header). Captions stay at the format's y ~1520: in the demo take
the chin is at ~1445, so anything higher lands on the face; marked `data-layout-allow-safe-zone`.

## Motion
- Frame 0 = the thumbnail: badge, rail and topic already readable. Badge lands from scale 1.12 / -2.5 deg to 1 / 0 in
  0.12 s power4.out (the format's 0.3 s slide-in can't coexist with "hook on screen at frame 0"); topic settles
  1.04 -> 1 in 0.22 s expo.out from 0.04 s.
- The spoken episode number ("three", 5.26 s on the demo's cut clock): "#3" re-stamps 1.45 / 8 deg -> 1 / 0, 0.3 s
  back.out(2.2); this episode's tick fills with the accent, scaleX 0 -> 1, 0.22 s power3.out.
- The topic word (5.78 s): highlighter sweeps under it, scaleX 0 -> 1, 0.3 s power3.out.
- Topic leaves 0.55 s after the first word of the point (7.19 s): clip-path wipe to the left, 0.22 s power3.in.
  Badge + rail stay all episode.
- Captions: box scale 0.94 -> 1 + opacity, 0.1 s power3.out; out 0.05 s. Keywords (`KEYWORDS`, six in the demo)
  flip to an accent chip with white text on the frame they're spoken.
- Camera (hard sets, origin 50% 75% = the chin, so punches grow up and never into the captions):
  1.0 at 0; 1.06 at the first jump cut (1.813); 1.10 on "Number"; 1.0 on the first word of the point; 1.06 on a
  stressed word; 1.0 on the next sentence; 1.16 on the payoff word; 1.04 on the closing sentence. Every jump cut in
  cut.mp4 gets a framing change.

## Sound
| Moment | Sound | Placement | Level |
|---|---|---|---|
| Badge lands (0.12 s) | signature stamp, 0.2 s: a short rubber-stamp hit (Edits: searchSoundEffects "stamp"), saved as `assets/sfx/signature-stamp.mp3` | starts 0.153 s (picture + 1 frame - measured peak 0.000) | gain 0.78: loudest 400 ms = -8.0 dB under the voice |

SFX aren't shipped. Either drop your own files into assets/sfx/ with these names, or skip them in the overlay and add
them natively in Edits with searchSoundEffects + addSoundEffect. (`build.py` skips the stamp cleanly if the file
isn't there.) No other effects (format rule). Music: add it in the Edits window yourself (library music goes silent
in Claude exports) or use your own file.

## Grade ("Series look", reused every episode)
`skin-soft` 0.6, exposure +0.04, contrast +0.06, highlights -0.08, shadows +0.06, temperature +0.04, saturation +0.03,
vignette 0.05 (Natural Portrait ranges), applied through `hyperframes media-treatment` (cached in `grade-attr.txt`).

## Banned here
Restyling mid-series; a second sound effect; slow creeping zooms; captions over the face; numbers the speaker didn't say.

## How a member's version differs
Change only the EPISODE block in `build.py` (SERIES, EPISODE, TOPIC, TOPIC_MARK, KEYWORDS, GROUPS and the key-moment
word indices) and SRC/KEEP/SCRIPT in `cut.py`. The accent comes from the BRAND block (her profile). Everything else
(positions, sizes, sound file, grade) is the series template and must NOT change between episodes. Episode 1 only:
pick the series name, accent and signature sound with her and record them plus the episode number in her own
episode list. Her rail shows as many ticks as her list has (EPISODES_SHOWN). If her framing differs (face lower or
higher), re-measure her chin and move the caption top and the camera origin once, in episode 1, then lock them. Her
"#N" must follow the last number in her episode list: never skip or repeat.

## Build and render
```
$PY cut.py        # assets/cut.mp4 + assets/words-cut.json (--words-only to redo words)
python3 build.py                                 # index.html + overlays/index.html + sfx.json
npx --yes hyperframes@0.9.83 check --json
npx --yes hyperframes@0.9.83 render --quality delivery -o renders/serialised-episode.mp4     # optional full preview
npx --yes hyperframes@0.9.83 render overlays --format mov -o renders/serialised-episode-overlays.mov
python3 measure_audio.py renders/serialised-episode.mp4      # signature level vs the voice
```
(`renders/` is not shipped: you render your own.)
