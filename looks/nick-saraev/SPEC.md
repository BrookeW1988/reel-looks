# SPEC: "The Recompose", a look inspired by Nick Saraev

> **Using this template:** the skill copies this folder (and `_shared/` next to it) into its build folder (see `USE.md`), adds the
> fonts below to `assets/fonts/`, puts your SDR take in `~/Movies/Edits-inbox/`, fills `plan.json` (plus `proof.json`
> for real pages and SRC/KEEP in `cut.py`), then runs `python3 cut.py` and `python3 build.py` (and
> `python3 build.py --overlay` for the Edits overlay), checks with `npx --yes hyperframes@0.9.83 check --json`, and renders the
> overlay `.mov` for Edits. Needs HyperFrames (Node 22+) and the skill's Python venv. Fonts: Playfair Display Italic
> (`assets/fonts/PlayfairDisplay-Italic.ttf`, https://fonts.google.com/specimen/Playfair+Display, SIL Open Font
> Licence) and Inter 600/700/800 (https://fonts.google.com/specimen/Inter, SIL Open Font Licence; no file needed:
> build.py names it by family and HyperFrames fetches it from Google Fonts when it compiles, then caches it).

Goal: a member watches it and thinks "my reel could look like that". Techniques only: no Nick footage,
logos, Maker School branding, catchphrases or his blue. References: https://www.instagram.com/nick_saraev/ and the
reels listed in `card.json`.

## Variant decision: A, Editorial (built) vs B, Design canvas (not built)
**Built A, editorial**, because:
1. **It works on any member's take.** B (canvas) needs a tool or repo with lots of real screens to drag in. Most members
   film mindset / "here's why" explainers. A carries those beats with serif-italic accent words and type
   slides when there is no screenshot, and still uses real pages when there is one.
2. **It is the purest form of the move**: the frame rearranges itself around each sentence (face ->
   split -> full-screen proof -> face). Every beat in this reel is one of those three states.
3. **A member can actually finish it in Edits.** The reframe is two clip positions (keyframes, native) plus ONE
   transparent overlay. B's cursor drags, selection handles and resize-by-handle all live only in overlays, and each card
   needs its own capture work.

**How B differs (if a member wants it):** grey grid canvas `#E4E4DF` instead of flat paper; every object is "selected"
(thin accent outline + 8 square handles); a macOS cursor drags each card in at ~60% size, then drags the corner handle
to full size and clicks the line being said; the take sits in a rounded box bottom half (x 60, y 1160, 960 wide) and
full beats put the card over a blurred, darkened copy of the take; captions on the seam with grey upcoming words. Same
three beat states, same proof rule, more overlay work. Not built in this template.

## Source and cut (`cut.py`)
- Footage: your take, 1080x1920, 30 fps, SDR (`SRC` in cut.py, e.g. `~/Movies/Edits-inbox/your-take.mov`).
- The demo kept two stretches (example values in cut.py): `(1.88, 15.48)` and `(23.69, 36.12)` on the source clock,
  dropping a list opener ("Number two,") and a side point in between.
- Cut points sit in 20 ms RMS dips: in the demo 1.88 (-62 dB, first word onset 1.92), 15.48 (-43 dB after the last
  word's tail at 15.44), 23.69 (-43 dB, onset 23.74), 36.12 (-56 dB after the last word ends 36.04).
- Joins: 15 ms equal-power (`qsin`) fades either side. Speed 1.1x (`setpts`/`atempo`). Demo result **23.73 s, 712 frames**.
- Voice: two-pass `loudnorm` I=-14, TP=-1.5, LRA=11, linear.
- Words: mlx_whisper `whisper-large-v3-turbo`, `word_timestamps=True` (command in cut.py's docstring); hyphenated
  words that whisper splits ("hyper" + "-focus") are merged; loose edges can be snapped to the envelope (`SNAP` in
  cut.py). Re-transcribing `cut.mp4` should give the same words; in the demo timing drift was median 0.01 s, worst 0.25 s.

## Palette (only these)
| Token | Hex | Used for |
|---|---|---|
| paper | `#F7F6F3` | field on proof and split beats (the box-shadow of the presenter "hole") |
| sage | `#E9ECEB` | field on type / equation slides (beats 2 and 7) |
| ink | `#101012` | headlines, list rows, captions on paper |
| accent | brand accent (default `#FF5A36`; `BRAND_ACCENT` in build.py or `accent` in plan.json) | italic accent words, the payoff number, highlighter (34% multiply), tick, strike, row numbers, caption keyword |
| accent tint | the accent mixed 14% with white (worked out in build.py; default `#FFE8E3`) | hook line-2 box (3 px accent outline) |
| white | `#FFFFFF` | cards, hook line 1, captions over footage |

## Type (1080x1920)
| Element | Font | Size / weight / tracking | Where |
|---|---|---|---|
| Hook line 1 | Inter | 70 / 800 / -2%, white box, padding 12/30/16, radius 18 | top 188 |
| Hook line 2 | Inter + Playfair Display Italic | 70 / 800 (last word 80 / 800 italic, accent, 6 px accent underline) | 12 px under line 1 |
| Logo chips | Inter | 46 / 700, 60 px real logos, white pill, radius 999 | cy 462 (scale 0.8) beat 1; cy 845 beat 7 |
| Type slide big word | Playfair Display Italic | 210 / 700 / -2% | top 700 |
| Type slide sub | Inter | 70 / 800 / -2% | top 965 |
| "idea" texture pills | Inter | 30 / 600, ink 26%, 2 px ink-13% border; 7 x 15 grid from y 210 | decoration only |
| List rows | Inter | 78 / 800 / -2.5%; numbers Playfair Italic 76 accent | list card |
| Page card source line | Inter | 30 / 600, ink 62%, 14 px accent dot | above each screenshot |
| Chapter word | Playfair Display Italic | 150 / 700, paper halo | cy 330, then cy 222 at scale 0.62 |
| "×" | Inter | 120 / 800 | cy 720 |
| Payoff number | Playfair Display Italic | 330 / 700, accent | cy 1110 |
| Captions | Inter | 58 / 800 / -1%, 2-4 words a group | face/full: top 1466; split: top 858 |
| Caption colour | n/a | over footage white + shadow `0 2px 3px .55, 0 4px 16px .35`; on paper ink; upcoming words 42% opacity, spoken 100%; one keyword per group turns accent | n/a |

## The three frame states (`build.py` STATE)
The paper is a transparent `#hole` (base box = the split rectangle x 48, y 940, 984 x 1060, radius 44) with
`box-shadow: 0 0 0 2600px <field>`; the footage wrapper `#cam` moves with it. Transform origin of the hole: bottom centre.
| State | Hole | Footage (`#cam`) | Meaning |
|---|---|---|---|
| face | scaleX 1.0976, scaleY 1.8868, radius 0 (hole = whole frame, paper invisible) | scale 1, y 0 | presenter |
| split | scale 1, y 0, radius 44 | scale 0.92, y +432 (face lands at y 1024-1778) | presenter + one object above (field y 170-850) |
| full | y +1060 (slid off frame) | scale 0.92, y +1492 | proof / type holds the frame |
Every change: one 0.5 s `power3.inOut` tween on hole + footage + field colour together, starting 0.13 s before its word.

## Beats (demo timings on the cut clock; word refs in `plan.json` are example values)
| # | Move | State, field | Line type | What's on screen |
|---|---|---|---|---|
| 1 | 0 | face, paper | the opening claim | hook set at frame 0 (settle 1.04 -> 1, 0.35 s expo.out; underline 0.55 s); two logo chips pop on the tool's name (0.945) |
| 2 | 2.85-3.35 | full, sage | a big idea or number said out loud | the big word blurs in on the word (3.945, 0.2 s expo.out, 1.15 -> 1); 105 "idea" pills stagger from centre over 0.7 s; the sub lines on their words. Captions off (the slide is the spoken words) |
| 3 | 5.78-6.28 | split, paper | explaining what the tool does | list card rises in (0.5 s power4.out, from +420 px, blur 14 -> 0): chips header, row 1 + tick (6.909), row 2 + strike-through (8.709) |
| 4a | 9.75 | split, paper | naming a real problem | a real page card rises in (scale 0.8, cy 545); highlighter on the first phrase at 10.15 |
| 4b | 10.29-10.79 | full, paper | the problem's name | the SAME card grows to full (scale 1.0, cy 830) as the take slides out; highlighter on the second phrase at 11.18 |
| 5 | 12.28-12.78 | face | new subject | card whips up (0.4 s power3.in, blur 16); the take rises back full frame (the jump cut at 12.364 happens while it is off frame); the chapter word blurs in above the head at 13.34 |
| 6 | 13.71-14.21 | split, paper | the definition | the chapter word carries up to a title (cy 222, 0.62); a real definition card rises (scale 0.92, cy 585); highlighter sweeps three phrases from 14.39, 0.28 s apart |
| 7 | 16.64-17.14 | full, sage | the payoff | the definition card shrinks to cy 400 / 0.7 (persists), "×" on "with", chips on the tool's name, the spoken number slams on its word (18.664: scale 1.3 -> 1, blur 12 -> 0, 0.22 s expo.out). Caption off for the number |
| 8 | 19.43-19.93 | face | the closing line | equation whips up; face, captions, end. Root duration 23.70 s |
Visual changes: 8 states + 2 inner recompositions (4a, the chapter carry) = a change about every 2.4 s (Nick measured 2.3-2.6 s).
Exits: `blur` = opacity 0 + 8 px blur, 0.18 s power2.in; `up` = y -1500 + 16 px blur, 0.4 s power3.in.

## Proof (all real)
| Card | Source | Capture |
|---|---|---|
| A page you name | a real public article (`proof.json` entry 1) | headless Chrome, 430 css px, 3x, light, crop 262 css px from the line named in `top_text` |
| A definition | e.g. the mobile Wikipedia page (`proof.json` entry 2, first sentence) | 330 css px, 3x, crop 168 css px; page actions / hatnote / tabs hidden (chrome only, text untouched) |
| Tools | real logo SVGs in `assets/proof/<name>.svg` (not shipped: use the tool's official logo) | real logos; names as labels |
`$PY tools/capture_proof.py proof.json` captures them and records the highlighter boxes
from the live text (needs Playwright + Google Chrome, see the script). Shown 920 px wide in a 1000 px white card
(radius 28, 2 px ink-10% border, shadow `0 30px 70px .16`). A card whose capture is missing is left out of the build.
No numbers anywhere except ones actually spoken.

## Sound (`plan.json` "sounds"; tactile, no music)
SFX aren't shipped. Either drop your own files into assets/sfx/ with these names, or skip them in the overlay and add
them natively in Edits with searchSoundEffects + addSoundEffect. Music: add it in the Edits window yourself (library
music goes silent in Claude exports) or use your own file. build.py skips any sound whose file is missing.

Start = picture moment + 1 frame (0.033 s) - the file's absolute sample peak (`tools/measure_sfx.py` -> `spk` in
`assets/sfx/peaks.txt`, next to the `npx --yes hyperframes@0.9.83 audio` fields). Level: volume = 10^((target - mmax)/20), where
`mmax` = the file's max 400 ms momentary loudness AS PLAYED (mono files upmixed: +3 LU) and target = -22.5 LUFS
(`boom.mp3` -21.2, `paper-slide-2.mp3` -23.5) against the voice at ~-14 LUFS momentary.
| Picture moment | Sound (file name in assets/sfx/) |
|---|---|
| chips pop (beats 1, 7) | quick pop, `pop.mp3` (Edits: searchSoundEffects "pop") |
| presenter out to type / equation slide (fastest frame) | soft whoosh, `whoosh-soft.mp3` (Edits: searchSoundEffects "whoosh") |
| the big word lands | soft low thud, `thud.mp3` (Edits: searchSoundEffects "thud") |
| list card / second page card land | paper slide, `paper-slide.mp3` / `paper-slide-2.mp3` (a second take, pitched +8%) (Edits: searchSoundEffects "paper slide") |
| tick | small click, `click.mp3` (Edits: searchSoundEffects "click") |
| strike-through, second phrase highlight | marker stroke, `marker.mp3` (Edits: searchSoundEffects "marker") |
| first phrase, definition highlights | marker stroke pitched -10%, `marker-2.mp3` (Edits: searchSoundEffects "marker") |
| real page card lands | camera shutter, `shutter.mp3` (Edits: searchSoundEffects "shutter") |
| face returns | whoosh, `whoosh.mp3` (Edits: searchSoundEffects "whoosh") |
| the payoff number | deep boom impact, `boom.mp3`, once (Edits: searchSoundEffects "boom") |

## Grade (`grade-attr.txt`, written by `hyperframes media-treatment`)
Natural Portrait seed, a touch cooler for Nick's neutral daylight: preset `skin-soft` 0.55; exposure +0.04 (preset),
contrast +0.04, highlights -0.06, shadows +0.06, temperature -0.03, vibrance +0.02; no vignette, no grain.

## Banned here
Hard cuts between beats (it recomposes); fade-and-slide-up on everything; floating / breathing loops; text over the
face; mocked-up UI or invented numbers; Nick's blue, his icons, his caption formula; music; the same whoosh twice in a row.

## Build and render
```
python3 cut.py                       # rough cut + voice -14 LUFS + words-cut.json (needs assets/words-src.json)
$PY tools/capture_proof.py proof.json
python3 tools/measure_sfx.py         # only if you use your own SFX (after npx --yes hyperframes@0.9.83 audio wrote assets/sfx/peaks.txt)
python3 build.py                     # index.html  (--plan / --footage / --words / --proof-dir to reuse)
npx --yes hyperframes@0.9.83 check --json && npx --yes hyperframes@0.9.83 snapshot --at 0,3.1,6.4,10.6,13.4,14.9,18.9,23.5
npx --yes hyperframes@0.9.83 render --workers 2 --quality delivery -o renders/nick-saraev.mp4
python3 build.py --overlay           # overlay/index.html: footage left out, transparent
npx --yes hyperframes@0.9.83 render overlay --format mov --workers 2 -o renders/nick-saraev-overlays.mov
python3 tools/measure_audio.py renders/nick-saraev.mp4 renders/nick-saraev-overlays.mov   # levels + peak timing
```
`overlay/` must be its own HyperFrames project before `--overlay`: copy `hyperframes.json` and `package.json` into
it (plus a `meta.json` with an id and name), and symlink `overlay/assets` to `../assets`. build.py doesn't make it.
`renders/` is not shipped: you render your own.

## Overlay deliverable (`renders/nick-saraev-overlays.mov`)
ProRes 4444 with alpha (`yuva444p12le`), 1080x1920, 30 fps, AAC audio = the effects only (no voice).
Built from the same plan with `--overlay`: the footage element is left out and the page ground is transparent, so:
face beats = transparent except the hook, chips and white captions; split beats = paper with a transparent rounded
window where the member's clip must sit; full beats = opaque paper with the proof. **The look depends on reframing the
footage itself (the clip shrinking into the box and sliding out), which an overlay cannot do**, so Edits must keyframe
the main clip natively (table below). Big file (~200 MB for 23.7 s): fine on desktop Edits; for phone transfer, trim or export a
HEVC-with-alpha copy.

## How a member's version differs
- **Their take, their words.** Run cut.py's method on their footage: pick a 15-30 s explanatory stretch, cut in
  envelope dips, re-transcribe to check. Replace `plan.json` beats/objects/captions with word indices from their words file.
- **Layout per sentence** is the only creative call: mark each sentence face / split / full. Rule of thumb: claim =
  face, "here's the thing" = split, anything to read = full, new subject = face again. A change every 2-3 s.
- **Their proof.** Real pages they name (`proof.json` + capture_proof.py), real logos, their own screenshots or results.
  No proof for a sentence? Use a type slide (`typewall`, `word`) with their exact words, never an invented card.
- **Their accent.** `BRAND_ACCENT` in build.py (Claude fills it from the member's profile) or `accent` in plan.json; the
  hook tint follows it. Keep paper / sage / ink.
- **Face position.** Split state assumes the face sits around y 560-1380 in the source (centred-ish, head and
  shoulders). A wider or off-centre take needs the split `cam` scale/y changed so the face lands inside the box (y 980-1800).
- **In Edits:** add `renders/<their>-overlays.mov` as an overlay over the full timeline, then keyframe the main clip
  (it can't be done inside an overlay, because the overlay can't move their footage):
  | Overlay state | Main clip in Edits |
  |---|---|
  | face | Scale 100%, Position 0, 0 |
  | split | Scale 92%, Position y +432 px (down 22.5% of frame height), x 0 |
  | full | Scale 92%, Position y +1492 px (slides out with the box). If Edits clamps the position, leaving it at +432 px also works once the move ends (the paper covers the frame); only the 0.5 s slide looks different |
  Add a keyframe pair at each move listed in the Beats table (start and start + 0.5 s), with Ease In/Out. Overlay
  audio carries the sound effects, so leave its volume at 100%.
