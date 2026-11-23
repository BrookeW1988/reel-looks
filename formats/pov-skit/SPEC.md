# SPEC: POV micro-skit

> **Using this template:** the skill copies this folder (and `_shared/` next to it) into its build folder (see `USE.md`), adds the
> fonts below to `assets/fonts/`, puts your SDR take in `~/Movies/Edits-inbox/`, fills `config.json`, then runs
> `$PY cut.py` and `$PY build.py` (inside the folder),
> checks with `npx --yes hyperframes@0.9.83 check --json`, and renders the overlay `.mov` for Edits
> (`npx --yes hyperframes@0.9.83 render overlays --format mov -o renders/pov-skit-overlays.mov`). Needs HyperFrames
> (Node 22+) and the skill's Python venv. cut.py and build.py use `../_shared/reeltools.py`. Fonts: Poppins SemiBold
> as `assets/fonts/Poppins-SemiBold.ttf` (https://fonts.google.com/specimen/Poppins, SIL Open Font Licence 1.1).

Reference: https://www.instagram.com/hannah.shapes/reel/DcHZeQNy76e/

**The demo:** a short talking-head take of a CTA said cleanly, then a tight-lipped "did I nail it?" smile before a
reach for the phone. That smile was the reaction beat. The joke was true (it really was a third take in under a
minute); no numbers are claimed on screen. Keep yours true too.

## Cut (cut.py, config.json; demo numbers)
| | Source | On the reel |
|---|---|---|
| Setup | 0.50-4.45 s at 1.0x (0.5 s of nothing trimmed off the front) | 0.00-3.95 s |
| Reaction | 4.45-5.00 s at **0.5x** (the smile, slowed so it lands) | 3.95-5.03 s |
| Cut | at 5.00 s source, the moment the reaction ends: nothing after it | total **5.03 s** |
Voice levelled with ffmpeg loudnorm (target -14, TP -1.5); the short demo clip came out at -14.9, so the reel played
it at `voice_gain` **1.11** (+0.9 dB) = **-14.1 LUFS** measured in the render. Word times: mlx_whisper
large-v3-turbo, start edges snapped past leading silence (< -38 dBFS). ASR fixes: `FIXES` in `../_shared/reeltools.py`.

## Look (1080x1920)
| Element | Spec used | Format file says |
|---|---|---|
| POV text | Poppins SemiBold 600, **48 px**, line-height 1.2, ink `#1A1A1A` on white `#FFFFFF` pill, radius **14**, padding **12/22**, one pill per line, 8 px gap | same |
| POV copy | your line, 2 lines, sentence case (e.g. "POV: you finally" / "nail your CTA") | max 2 lines |
| POV position | centred, top **290 px**, on from frame 0 to the end, never moves | y ~300 |
| Captions | Poppins SemiBold **44 px**, white, 6 px black stroke (3 px visible, paint-order stroke) + soft shadow `0 3px 10px rgba(0,0,0,.35)`; groups of ~3-4 words (16+ characters, never ending on "on/the/to/..."); top **1180 px** | y ~1450 (moved: see below) |
| Caption entrance | opacity 0->1, y +6->0, 0.08 s power2.out; gone the frame the reaction punch lands | - |
| Reaction punch | hard cut (gsap.set) to **130%** at the reaction start, origin your face (`face_centre`, demo 540, 650) | 130% for last 1-1.5 s (demo 1.08 s) |
| Reaction emoji | a 3D emoji PNG you add to `assets/img/` (e.g. Microsoft Fluent Emoji 3D, MIT licence, https://github.com/microsoft/fluentui-emoji; demo: "face holding back tears", 256 px) at 210x210, left 770, top 470 (beside your head, not over your face); lands 0.12 s after the punch: scale 0.2->1, rotate -18->0, opacity 0->1, 0.42 s back.out(2.2), then dead still. No PNG = no emoji | one sound OR one 3D emoji |
| Grade | media-treatment's own measured correction on the demo: temperature **-0.023**, nothing else (natural phone look). `grade-attr.txt` ships empty: no grade unless you make one | natural |
| Sound | your voice only. No SFX (the format allows one sound OR one emoji: the emoji was chosen because it reads muted). Music: add trending audio in the Edits window yourself (library music goes silent in Claude exports) or use your own file | one reaction sound or none |

### Why two numbers moved
Instagram's Reels UI covers everything below y 1248 and above y 269 (HyperFrames' safe-area table, `outside_safe_zone`).
At y 1450 the captions sat under the caption/username overlay, so they moved up to 1180 (over the mic hand and top,
well clear of the face). The POV line was split onto two pills so it stays inside x 65-1015.

## Overlay MOV
`renders/pov-skit-overlays.mov` = POV pills + captions + emoji on transparent (ProRes 4444), no footage, no sound
(not shipped: you render your own).

## Banned here
A hook on top of the POV line; captions that explain the joke; anything after the reaction; slow creeping zoom (the
punch is a hard cut); emoji over your face.

## How a member's version differs
- Your clip, your POV line, your reaction emoji: edit `config.json` (`take`, `keep`, `pov_lines`, `reaction_emoji`,
  `face_centre`, `punch`), then `$PY cut.py && $PY build.py`.
- `keep`: setup range(s) first, the reaction last with a third number for its speed (`[a, b, 0.5]`). Cut where you
  stop reacting.
- If you don't speak, captions disappear on their own (no words). If you want a sound instead of the emoji, use one
  of the format's sounds (record scratch, crickets, gasp, boing: Edits searchSoundEffects + addSoundEffect) placed
  1 frame after the punch.
- Claude offers three POV lines in your voice if you have none; keep each readable in under 2 s (about 8 words).

## Rebuild
Needs `../_shared/` (reeltools.py: cut, word timings, sound placement, grade; check.sh; render.sh; measure.py).
`$PY cut.py && $PY build.py && ../_shared/check.sh .`
then `../_shared/render.sh "$PWD"` and `$PY ../_shared/measure.py .` (adjust any sound
outside 6-10 dB under and re-render with `MP4_ONLY=1`).
