# SPEC: Before-and-after reveal

> **Using this template:** the skill copies this folder (and `_shared/` next to it) into its build folder (see `USE.md`),
> adds the fonts below to `assets/fonts/`, puts your SDR before and after clips in `~/Movies/Edits-inbox/`, fills the
> per-take block at the top of `cut.py` and the REVEAL block at the top of `build.py`, then runs
> `$PY cut.py` and `$PY build.py` (inside the folder),
> checks with `npx --yes hyperframes@0.9.83 check --json`, and renders the overlay `.mov` for Edits
> (`npx --yes hyperframes@0.9.83 render overlays --format mov -o renders/before-after-reveal-overlays.mov`). Needs
> HyperFrames (Node 22+) and the skill's Python venv. Fonts: Bebas Neue as `assets/fonts/BebasNeue-Regular.ttf`
> (https://fonts.google.com/specimen/Bebas+Neue), Inter variable as `assets/fonts/Inter-Variable.ttf`
> (https://fonts.google.com/specimen/Inter; rename the `Inter-VariableFont_opsz,wght.ttf` file from the download),
> JetBrains Mono Medium as `assets/fonts/JetBrainsMono-Medium.ttf` (https://fonts.google.com/specimen/JetBrains+Mono),
> all SIL Open Font Licence 1.1.

Reference: https://www.instagram.com/reel/DcO1EWSgTDG/

**The demo's transformation was real:** the same iPhone take as the camera saved it (HLG HDR, Rec.2020, 10-bit:
grey and washed out in any editor that skips the tone map) and after an HDR -> SDR conversion (Apple avconvert tone
map to SDR Rec.709 8-bit), plus the format's after grade. Nothing was faked: the before was NOT given the format's
"cooler, -15 saturation" grade, because the change being shown IS the colour; grading the before down would
exaggerate the result.

## Clock (cut.py -> cut.json; the demo ran 11.47 s, format range 12-30 s: the demo take was 9.9 s long)
| Cut s | What | Source |
|---|---|---|
| 0.00-3.96 | BEFORE: raw file, the setup line | raw, 0.90-4.86 |
| 3.96-6.56 | PROCESS: four beats, no voice (2.6 s gap), tactile sounds | |
| 6.56-11.47 | AFTER: flash + push, the payoff line, then a 1.6 s silent hold (after = 4.9 s) | fixed, 4.95-9.90 |
Voice = the after file's audio (same take), loudnorm -14 LUFS (the demo measured -14.9 because of the gap) x1.11 in
the mix (`VOICE_GAIN`; re-measure yours with `measure_audio.py`).
Word timings: whisper on voice.wav; optionally proofread with `SCRIPT` (replaces whisper's spelling by position);
`SNAP` moves word starts to measured RMS onsets where whisper drifts after a silence (the demo snapped the first
word to 0.73 and the first word after the gap to 6.83).
The VOICE_KEEP, START, GAP and SCOPE_AT numbers in cut.py are example values for the demo take; Claude sets them per take.

## Palette (only these)
| Hex | Used for |
|---|---|
| `#111111` | question pill, caption outline; BEFORE plate is black at 80% |
| `#FFFFFF` | label and caption text, wipe line, flash (`#FFFDF6`) |
| `#F5C451` | AFTER plate, the sparkle, process step titles, "to" tags, switch track |
Process beats sit on a dark desk: radial `#1E1E21` -> `#0E0E0F`.

## Type
| Element | Font | Size | Where |
|---|---|---|---|
| BEFORE / AFTER | Bebas Neue | 96 caps, +2% | plate radius 14, padding 14/26/6, x 64, **top 272** (format: y 160) |
| Question hook | Inter Bold | 58 / 700 | ink pill, centred, top 410 (format: y ~320; moved under the label) |
| Captions | Inter Bold | 48 / 700, white, 6 px ink stroke, shadow 0 4 14 35% | top 1420 (format: y ~1450) |
| Step titles | Bebas Neue | 64, +6%, gold | centred, top 330 |
| Terminal | JetBrains Mono | 44 / 500 | card x 64-1016, top 640, radius 26 |
| Tags | Inter Bold | 40 | radius 14 |
| Scope readout | Inter Bold 46, numbers Inter Black gold | | centred, top 1150 |
Labels moved down from the format's y 160 into the Instagram Reels clear band (y 14-65%).

## Beats and motion (demo times)
- 0.00: frame 0 = thumbnail: raw take + BEFORE plate + question already on screen; question settles 1.05 -> 1 in
  0.3 s expo.out; leaves at 1.80 (blur 8 + fade, 0.18 s power2.in). Holds 1.8 s (4 words need 1.7 s).
- 3.96 Beat 1 "1 · CONVERT" (0.70 s): the real command types on in 0.39 s (steps = its character count);
  terminal settles 1.04 -> 1, 0.6 s expo.out.
- 4.66 Beat 2 "2 · HDR OFF" (0.60 s): "from" tags (ffprobe of the raw file) -> switch knob slides 184 px in 0.26 s
  power3.inOut, lands 4.98; track floods gold; "to" tags (ffprobe of the fixed file) light up, 0.04 s stagger.
- 5.26 Beat 3 "3 · COLOUR BACK" (0.66 s): real vectorscopes (ffmpeg, same frame at source `SCOPE_AT`) of both files;
  after-scope grows 0.72 -> 1 at 5.44 (0.3 s expo.out) while the readout counts 6.5 -> 11.2 on the demo (ffmpeg
  signalstats SATAVG, average saturation; the fixed file had 1.7x the colour). Scope turns -8 -> 0 deg over the beat.
- 5.92 Beat 4 (0.64 s): the raw take full frame with the fixed take wiping in from the left, line to 62% of the
  width, power2.inOut, so the split crosses your face.
- 6.56 REVEAL: white flash rises 0.05 s from 6.50, falls 0.3 s (4 frames near full); after shot pushes 1.10 -> 1.0
  in 0.5 s expo.out; AFTER plate slides x -60 -> 0 in 0.35 s expo.out; sparkle pops 0 -> 1, -60 -> 0 deg, 0.32 s
  back.out(2.4), landing 6.70. Hold to the end (4.9 s; format: 3-4 s minimum, "longer than feels comfortable").
- Captions: whole group pops 0.92 -> 1, 0.12 s back.out(1.8); out 0.06 s. Groups: `GROUPS` in build.py, or
  automatic (up to 3 words, break after punctuation and at the montage gap).
- The step titles, tags and scope beats are the demo's process (a computer fix). Swap them for your own process.

## Sound (each peak 1 frame after its picture; levels measured with measure_audio.py)
SFX aren't shipped. Either drop your own files into assets/sfx/ with these names, or skip them in the overlay and add
them natively in Edits with searchSoundEffects + addSoundEffect. (build.py skips any file that isn't there.)
| Moment (demo time) | Sound (file name build.py looks for) | Start | Gain |
|---|---|---|---|
| Command typing (3.98-4.40) | keyboard typing, `typing.mp3` (Edits: searchSoundEffects "typing"), 0.47 s slice from 1.0 s | 3.980 | 1.8 |
| Switch lands 4.98 | toggle switch click, `toggle.mp3` (Edits: searchSoundEffects "switch"), peak 0.000 | 5.013 | 0.83 |
| Scope swap 5.44 | paper slide, `paper-slide.mp3` (Edits: searchSoundEffects "paper slide"), peak 0.110 | 5.363 | 0.27 |
| Sparkle lands 6.70 | soft sparkle chime, `sparkle.mp3` (Edits: searchSoundEffects "sparkle"), peak 0.260 | 6.473 | 0.77 |
No whoosh on the flash (the sparkle is the reveal's one sound). No music in the file: add it in the Edits window
yourself (library music goes silent in Claude exports) or use your own file.

## Grade
Before: none (the real raw file). After (and the wipe's after layer): temperature +0.06, saturation +0.10,
contrast +0.08 (format: warm, +10 saturation, +contrast), via `hyperframes media-treatment` (`grade-attr.txt`).

## Banned here
Grading the before to look worse; a cut-short reveal hold; music-only process beats; more than one flash; invented
numbers (every number on screen comes from ffprobe/signalstats of the two files) or an invented command.

## How a member's version differs
Your process is usually filmed (sanding, cutting, styling, packing): swap the three cards for three or four 0.5-1 s
clips of the actions themselves, sped up 2-4x, each with ONE tactile sound of that action (`searchSoundEffects`
"sanding", "scissors", "tape"), and drop the step titles. Your before and after are usually two different clips:
match the angle if you can, and grade them separately (before: cooler, -15 saturation, slightly flat; after: warm,
+10 saturation, +contrast) since your change isn't the colour itself. Set HOOK from the formulas ("Would you
[keep/buy/grab] this?", "[Time] later...", "My client said it couldn't be saved"). Only add a comment-keyword CTA if
you already have that funnel live. In `cut.py`: BEFORE, AFTER, START, VOICE_KEEP, GAP, SCRIPT, SNAP; in `build.py`:
the REVEAL block.
