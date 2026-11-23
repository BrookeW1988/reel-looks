# SPEC: Text over B-roll

> **Using this template:** the skill copies this folder (and `_shared/` next to it) into its build folder (see `USE.md`), adds the
> font below to `assets/fonts/`, puts your SDR clips in `~/Movies/Edits-inbox/`, fills `CLIPS` at the top of `cut.py`
> and `LINES` at the top of `build.py` (this template has no separate config file), then runs `python3 cut.py` and
> `python3 build.py`, checks with `npx --yes hyperframes@0.9.83 check --json`, and renders the overlay `.mov` for Edits
> (`npx --yes hyperframes@0.9.83 render overlays --format mov -o renders/text-over-broll-overlays.mov`). Needs
> HyperFrames (Node 22+) and ffmpeg (no whisper: nothing is spoken). Font: Instrument Sans Medium
> (https://fonts.google.com/specimen/Instrument+Sans, the variable TTF saved as `InstrumentSans.ttf`, SIL Open Font Licence).

Format file: the skill's `styles/text-over-broll.md` (micro-lesson variant: one short line per clip, earlier lines
stay). References: https://www.instagram.com/reel/DZz6ubJxH0i/ and https://www.instagram.com/reel/DcJaVCfRGZi/

The format stays calm and native: no talking heard, no captions, no stickers, no sound effects, no music baked in
(the member adds a song from Edits' library in the app). The craft is in the footage choice, the slow motion,
the grade, the per-word arrival and a clean loop.

## The line (her voice, lowercase, no full stops; one line per clip)
One short line per clip, written like a text to a friend (format max ~24 characters; the demo's three lines were 15,
23 and 20 characters). True to her real day or workflow; no numbers, no quotes. Other shapes that work:
"thing: done / thing: done / me: outside" and "pov: <what happened> / and <the small payoff>".

## Footage (cut.py; the member's own clips only, all slowed with motion interpolation)
Demo values (example only):
| # | Clip | Source s | Speed | Crop (source px) | On the reel |
|---|---|---|---|---|---|
| 1 | a quiet moment before anything happens | 0.00-1.00 | 0.50x | full frame | 0.000-1.900 |
| 2 | a second quiet moment, closer | 0.10-1.50 | 0.60x | 1800x3200 at 180,0 (1.2x, top-anchored: a step in) | 1.900-4.133 |
| 3 | outside: sky, trees, ends on a smile | 1.60-3.90 | 0.55x | 1800x3200 at 180,0 (1.2x: keeps the head below the text) | 4.133-8.133 (file ends 8.200; the reel stops one frame short) |
Slow motion: ffmpeg `minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1` after `setpts=PTS/speed`;
each clip is measured after encoding (minterpolate drops tail frames). Total 8.13 s (format: 8-12 s micro-lesson).
Hard cuts only. A talking clip with the sound removed (mouth moving, nothing heard) reads as vlog footage at 0.55x;
hands/objects footage (the format's preference) avoids the issue entirely.

## Type (1080x1920)
| Element | Font | Size | Where |
|---|---|---|---|
| Lines ("Friend text") | Instrument Sans Medium (variable, wght 500) | 46 px, line height 1.25, tracking -0.5% | left x 90, first line top **272**, each next line +57.5 px |
White text, shadow 0 2 12 black 45% (format). Moved from the format's y ~720 to 272 on purpose: in the demo clips
the face sits from y ~460 down, and "nothing over the face" wins; 272 is the top of Instagram Reels' clear band.
Soft shade behind the text block: radial ellipse 58%x50% at 34%/50%, black 34% -> 19% at 45% -> 0 (captions.md:
a scrim sized to the text, 30-40%, never a full bar), because bright sky and white walls drop white text to ~2:1.

## Motion
- Frame 0 = the thumbnail: clip 1 + line 1 already on screen (the format's 0.3 s fade-in would leave frame 0 empty).
- Lines 2 and 3 arrive on their clip's cut + 0.25 s / + 0.35 s: per word, blur 6 -> 0 px and opacity 0 -> 1 in 0.14 s
  power2.out, 0.067 s apart, no movement. Landed lines are dead still.
- Loop: at 7.71 s lines 2 and 3 leave (blur 6 + fade, 0.2 s power2.in, 0.03 s stagger), so the last frame shows
  only line 1, like frame 0.
- Film feel (media-treatment Film Memory recipe, temporal part): gate weave on the footage wrapper, finite and
  irregular, sine.inOut segments of 0.7-0.95 s, x/y within 1.3 px, rotation within 0.02 deg, scale 1.006-1.009;
  exposure breathing via `--hf-color-grading-exposure` within +-0.025. Both return to the start state at the end.

## Grade (same on every clip)
Film Memory: `vintage-wash` 0.6, temperature +0.07, contrast -0.05, blacks +0.05 (lifted), vignette 0.12, grain 0.12,
grain size 0.2, roughness 0.6. Via `hyperframes media-treatment` (cached in `grade-attr.txt`).

## Sound
None in the file (format: no SFX; the member adds a familiar song in Edits). Music: add it in the Edits window yourself
(library music goes silent in Claude exports) or use your own file. Mood to suggest: warm, light, mid-tempo acoustic
or lo-fi.

## Overlay MOV
`renders/text-over-broll-overlays.mov` (not shipped: you render your own) = the shade + lines on transparent. In Edits
the member lays her clips (graded warm) underneath, then this on top.

## Banned here
Captions, stickers, sound effects, emojis on screen, hashtags on screen, text in the bottom 20% or under the right
rail, fade-and-slide-up text, a different grade per clip, text over the face.

## How a member's version differs
Her clips should be hands and objects (coffee, the desk, packing an order, the shopfront), so the text can usually
sit at the format's y ~720 (set TEXT_TOP) and the shade can go (SHADE = 0) unless her footage is bright. Put her
clips in CLIPS in `cut.py` (in, out, speed 0.5-1.0, crop or None) and her lines in LINES in `build.py`: one line per
clip, or a single line (LINES with one item) for the plain variant, held to the end. If she has no line, offer three
in her voice. Tell her the song mood; she adds the song in Edits.
