# SPEC: "Receipts Round Your Head", a look inspired by Mariah Brunner

> **Using this template:** the skill copies this folder (and `_shared/` next to it) into its build folder (see `USE.md`), adds the
> fonts below to `assets/fonts/`, puts your SDR take in `~/Movies/Edits-inbox/`, fills `reel.json`, then runs
> `python3 cut.py --src ~/Movies/Edits-inbox/your-take.mov --keep <a-b,c-d> --transcribe` and
> `python3 build.py --overlays` (and `python3 build.py` for the full preview), checks with
> `npx --yes hyperframes@0.9.83 check --json`, and renders the overlay `.mov` for Edits
> (`npx --yes hyperframes@0.9.83 render overlays --format mov -o renders/mariah-brunner-overlays.mov`).
> Needs HyperFrames (Node 22+) and the skill's Python venv (`cut.py --transcribe` calls it for mlx_whisper).
> Fonts: Inter 900 + 800 ([Google Fonts](https://fonts.google.com/specimen/Inter), SIL Open Font Licence). It's bundled
> with HyperFrames (900 in the bundle, 800 fetched from Google Fonts by the compiler), so nothing has to go in
> `assets/fonts/` for this look.
> Your own files go in: `assets/img/` (logos, 3D emoji PNGs), `assets/cards/` (real screenshots), `assets/gif/`
> (a reaction clip as a short `.mp4`), `assets/sfx/` (optional sounds). None are shipped; every cue whose file is missing
> is skipped.

Goal: the speaker stays on screen the whole time, talking like she's on FaceTime with a friend, while real receipts
(a logo, real screenshots), a reaction GIF, butter-yellow keyword stacks and a lavender numbered card pop in AROUND her
head, each on the word it illustrates. Techniques only: none of Mariah's footage, logos, captions, catchphrases or
sign-offs. References: [@itsmariahbrunner](https://www.instagram.com/itsmariahbrunner/) (reel links in `card.json`).

## Source and rough cut (`cut.py`)
| What | Value | Why |
|---|---|---|
| Footage | one talking-head take, 1080x1920, 30 fps, SDR | |
| Kept (source s) | whole sentences only; drop an off-topic middle so the reel stands alone. Every edge sits in measured near-silence (RMS -46 to -61 dB in the demo) | the demo kept two ranges (example values in `cut.py`) |
| Breath trims | only where the gap is really silent | a voiced gap (the demo had one at -14 to -21 dB) would clip the speaker |
| Speed | 1.1x (atempo, pitch kept) | tight, not breathless |
| Edit fades | 12 ms audio in/out on each keep | no clicks |
| Voice level | two-pass loudnorm to -14 LUFS, TP -1.5 dBTP | member default |
| Length | the demo came out at 21.77 s (root clamped to 21.757 s) | 15-25 s brief |
| Word times | mlx_whisper `whisper-large-v3-turbo`, `word_timestamps=True`, re-timed on the cut clock; a word is kept if its MIDDLE is inside a keep | whisper.cpp drifted up to ~1 s on the demo take |

Proofread every caption against the audio before building.

## Safe zones (measure them on each take: a gridded 1 fps contact sheet)
- The demo face box: x ~330-1000, y ~560-1500 (the chin reaches 1450-1500 when leaning in). Nothing is ever placed in
  that box.
- Graphics zone on a close-up: ABOVE the head, y ~200-560, x 72-1010. Caption zone: under the chin, centre y 1545.
- Mariah's own framing is wider (face higher and smaller), so she puts cards UNDER her face and captions on her chest
  (y ~1206). A tight take puts receipts above the head and captions just under the chin. That's the biggest deliberate
  difference from her look (both placements fit the style: "top or side of frame").

## Palette (only these)
| Token | Hex | Used for | Source |
|---|---|---|---|
| butter yellow | `#F8F098` | hook lines 1-2, keyword stack hero words, highlighter sweep (multiply), numbered-card pill | measured on her reels |
| white | `#FFFFFF` | captions, hook line 3, second-voice keyword lines, 4 px frame on cards/GIF/tile | measured |
| ink | `#0C0C0E` | 9 px outline under every text pop, big number, 4 px pill outline, plate | est. |
| lavender | `#DCD3FA` -> `#EEE9FD` (55%) -> `#FFFFFF`, 160° | numbered card | OUR PICK: not measured |
| card shadow | `16px 20px 16px rgba(0,0,0,.35)` | tile, cards, GIF, numbered card | est. |

## Type (Inter only; 900 is bundled, 800 is fetched from Google Fonts)
| Element | Size / weight | Position (px) | Notes |
|---|---|---|---|
| Hook, 3 lines, Title Case | 86 / 900, line-height 1.02, tracking -2% | x 72, top 250 (block 250-~560) | two yellow lines, one white. 9 px ink stroke under the fill + `0 8px 22px rgba(0,0,0,.35)`, no box |
| Keyword stack 1 | hero words 118/900 yellow at (72, 212) and (640, 324); small words 70/900 white at (548, 362) and (72, 490) | staggered left/right above the head | 3D emoji 150 px at (350, 336), rot -10° |
| Keyword stack 2 | small 78 white (72, 214); hero 142 yellow (72, 292); small 78 white (470, 458) | | 3D emoji 150 px at (836, 290), rot 8° |
| Numbered card | number 160/900 ink, tracking -4%; label 64/900; pill 38/900 ink on yellow, 4 px ink outline, nowrap | card (170, 206) 720x330, radius 36, padding 30/40 | |
| Captions, ONE word | 80 / 800, line-height 1.25, tracking -1.5%, white, `0 4px 16px rgba(0,0,0,.6), 0 0 3px rgba(0,0,0,.45)`, no box | full-width, centred, centre y 1545 | lower case as spoken; `keep_case` words keep caps; punctuation stripped |

Why the ink stroke (not in Mariah's hook): the top third of the demo take was a bright window; butter yellow on light grey
had no contrast without it. Members filming against a darker wall can drop it (`-webkit-text-stroke: 0`).

## Receipts (all real, all the member's own files)
| Receipt | File (placeholder in `reel.json`) | Box (px) | Rule |
|---|---|---|---|
| Logo tile | `assets/img/your-logo.svg` on a white 164 px tile, radius 40, rot 6° | (836, 258) | the real logo of the tool she names |
| Screenshot card 1 | `assets/cards/your-screenshot.png` (a tight crop of the real thing) | (240, 204) w 600, rot -2° | her own capture or a public page; pixels never edited |
| Screenshot card 2 | `assets/cards/your-second-screenshot.png` | (92, 198) w 500, rot 1.5° | same |
| Highlighter on rows | yellow bars, multiply blend, sweep scaleX 0->1 0.22 s power2.out, 90 ms apart | boxes `[x, y, w, h]` inside the card (3 rows in the demo) | annotation on the real screenshot; pixels unchanged |
| Reaction GIF | `assets/gif/your-reaction.mp4`, a ~3 s clip cropped to the box | (76, 206) 560x350, rot -3° | a clip she's allowed to use, matching the feeling she names |
| Emojis | `assets/img/your-emoji.png` etc. | as above | e.g. [Microsoft Fluent Emoji 3D](https://github.com/microsoft/fluentui-emoji) (MIT licence) |

## Beat sheet (the demo, cut clock in seconds; every cue anchored to a word in `reel.json`)
| t | What happens | Beat state |
|---|---|---|
| 0.00 | hook already on screen (frame 0), settles 1.04 -> 1 over 0.35 s expo.out | hook |
| 0.96 | logo tile pops on the tool's name | layered receipt |
| 1.95-2.15 | hook + tile blur out word by word (0.13 s, 30 ms apart) as screenshot card 1 pops in at 2.07 | receipt |
| 3.96 / 4.31 / 4.56 / 4.98 | keyword stack 1 builds word by word; emoji on the hero word; card 1 leaves upward on the first stack word | label system |
| 6.73 | stack blurs out | anchor (0.2 s) |
| 6.93 | screenshot card 2 pops | receipt |
| 8.24 | highlighter sweeps three rows | receipt |
| 10.02 | card 2 drops out; GIF pops (drift +3% scale, -1.25° -> +1.25° across the hold) | reaction |
| 11.20 | hard punch-in to 1.10 on the punchline word | anchor |
| 12.36-12.46 | GIF out; punch back to 1.0 | anchor, plain hold to 14.49 |
| 14.49 | lavender numbered card pops on the spoken number, which counts 0 -> the number in 0.55 s | label system |
| 15.66 | yellow pill pops in on its phrase | label system |
| 17.19-17.45 | card swipes out right (x +900, rot 8°, blur 14, 0.26 s power3.in): the only whoosh | |
| 17.78 | jump cut, hidden by a hard punch to 1.07 that holds to the end | anchor |
| 18.02 / 18.51 / 19.18 | keyword stack 2 builds | label system |
| 20.55 | emoji pops; stack holds to the last frame | |
19 visual changes in 21.8 s: denser than Mariah's measured 25 in 62 s overall, close to her measured opening rate
(a change every 1.7-3.0 s), because a 22 s reel is all "opening".

## Motion (eases by role)
- **Pop in** (every receipt, word and emoji): scale 0.78 -> 1 `back.out(1.7)` 0.33 s; blur 8 -> 0 px over 0.23 s
  power2.out; opacity 0 -> 1 in 0.10 s on its own tween (opacity never bounces). Keyword words start at 0.70, emojis at 0.50.
- **Exits** (ours, not measured): 0.18 s power3.in, about 45% shorter than the entrance. Card 1 leaves up
  (y -70), card 2 down (y +90), GIF and tile shrink to 0.9, the numbered card swipes right (0.26 s). Keyword words blur
  out 8 px in 0.13 s, 30 ms apart.
- **Captions**: one word per clip, scale 0.86 -> 1 in 0.10 s expo.out on its start; each word holds to the next word,
  or 0.25 s past its end across a pause over 0.35 s. First caption at 0.10 s (frame 0 is the hook).
- **Camera**: `gsap.set` hard punches only, origin (660, 1000) = the face: 1.10 on the punchline word, 1.0 after it,
  1.07 at the jump cut. No creeping zooms, no floating loops (the GIF drift is one linear move, not a loop).

## Sound (no music; placed by measured peak: start = picture + 1 frame - file peak)
SFX aren't shipped. Either drop your own files into assets/sfx/ with these names, or skip them in the overlay and add
them natively in Edits with searchSoundEffects + addSoundEffect. build.py skips any file that isn't there.
Music: none in this look. If you want some, add it in the Edits window yourself (library music goes silent in Claude
exports) or use your own file.

Peaks come from `npx --yes hyperframes@0.9.83 audio --json`, cross-checked with a 10 ms RMS scan. Pick volumes so each
effect's 400 ms loudness sits ~8 dB under the voice, then MEASURE the render with `measure_audio.py` (it compares the
overlays render, which carries only the effects, against `assets/cut.mp4`). The demo numbers:

| Moment (cut s) | Sound (file name in `reel.json`) | File peak (s) | Volume | Measured hit vs picture | Measured: dB under the voice |
|---|---|---|---|---|---|
| 0.96 logo tile lands | soft pop (Edits: "pop"), `pop-1.mp3` | 0.007 | 0.82 | +26 ms (onset) | 9.4 |
| 2.07 card 1 lands | paper slide (Edits: "paper slide"), `paper-slide-1.mp3` | 0.117 | 0.3 | +27 ms (peak) | 8.6 |
| 3.96 first stack word taps in | soft mouse click (Edits: "mouse click"), `click-soft.mp3` | 0.001 | 1.0 | +26 ms (onset) | 9.6 |
| 4.56 emoji + hero word | bubble pop (Edits: "bubble pop"), `bubble-pop.mp3` | 0.01 | 0.66 | +26 ms (onset) | 8.1 |
| 6.93 card 2 lands | a second paper-slide take, `paper-slide-2.mp3` | 0.58 | 0.35 | +33 ms (peak) | 8.4 |
| 8.24 highlighter sweeps the rows | marker on paper (Edits: "marker"), `marker.mp3` | 0.012 | 1.8 | +24 ms (onset) | 8.3 |
| 10.02 reaction GIF lands | soft thud (Edits: "thud"), `soft-thud.mp3` | 0.0 | 0.42 | +32 ms (onset) | 8.3 |
| 14.49 number card lands | a second pop take, `pop-2.mp3` | 0.006 | 0.47 | +29 ms (onset) | 7.3 |
| 15.65 pill taps in | soft mouse click, `click-soft.mp3` | 0.001 | 1.0 | +25 ms (onset) | 8.5 |
| 17.41 number card swipes out (fastest frame); the only whoosh | swipe / whoosh (Edits: "swipe"), `swipe.mp3` | 0.168 | 0.48 | +27 ms (peak) | 7.5 |
| 18.51 big closing word lands | soft pop, `pop-1.mp3` | 0.007 | 0.82 | +21 ms (onset) | 9.5 |
| 20.55 closing emoji | bubble pop, `bubble-pop.mp3` | 0.01 | 0.66 | +25 ms (onset) | 7.7 |

All 12 landed 21-33 ms after their picture (1 frame = 33 ms) and sat 7.3-9.6 dB under the voice (target 6-10). Pops,
clicks and the thud are judged by onset; slides and the swipe build up, so by their peak. Rotations: two pop takes, two
slide takes, one whoosh only.

Render level check: measure the full MP4 too (target -14 LUFS integrated, true peak <= -1 dBTP). The demo's full render
came out ~1.5 dB under on the voice (-15.4 LUFS, -3.2 dBTP) from the renderer's own mix; `ffmpeg -c:v copy -af volume=1.5dB`
on the MP4's audio brought it to -13.9 LUFS / -1.4 dBTP, LRA 1.1 LU. The overlay `.mov` for Edits carries effects only,
so this only matters for a full MP4.

## Grade (`npx --yes hyperframes@0.9.83 media-treatment`, stored in `grade-attr.txt`)
"Warm and healthy", no vignette, no grain: exposure +0.03, contrast +0.04, shadows +0.04, temperature +0.05,
vibrance +0.06 (the demo's `--analyze` found no technical imbalance: Y avg 106.8, V avg 132.8 = already slightly warm).

## Banned here
Anything over the face; full-screen takeovers (the rule "nothing over the face" beats Mariah's blurred-plate
demonstration beat, see below); fake UI or invented numbers; music; a whoosh per card; the same take of a sound twice in
a row; fade-and-slide-up entrances; text on screen under ~0.8 s; Mariah's catchphrases or sign-offs; a CTA the speaker
didn't say.

## Departures from Mariah's own look, and why
1. Receipts above the head, captions under the chin (tight framing; see Safe zones).
2. No "demonstration" beat (full-screen or blurred-take card): it would cover the face. On a wider take, the split demo
   (screenshot top half, the speaker below) is the one to add.
3. Ink outline on text pops (bright background).
4. Captions 80 px, not ~90 px: they sit under the chin, close to the platform's caption area, so a bit smaller.
5. Lavender hex, exit timing, caption pop and every sound level are our numbers, not measurements of her reels.

## How a member's version differs
- **Their take, their framing.** Step one is a 1 fps gridded contact sheet to find their face box. A wider take (face
  above y ~1250) can use Mariah's own placement: cards under the face, captions on the chest (~y 1206); `caption_y` and
  every x/y in `reel.json` change, the style tokens don't.
- **Their words drive every cue.** Run `python3 cut.py --src <take> --keep a-b,c-d --transcribe`, then re-anchor
  `reel.json` cues to their word indices (`"at": "w12"`). Captions are rebuilt from their words automatically.
- **Their receipts.** Real screenshots of the tools THEY name (their own captures or a headless render of a public page),
  real logos, about 1 reaction GIF per ~10 s. Never mock up UI or invent numbers; a numbered card only shows a
  number they actually say.
- **Their colour.** Swap `#F8F098` (`YELLOW` in build.py) for their brand accent if they have one (keep the ink outline
  if it's light).
- **Sound.** Same rule: tactile pops/taps on landings, one whoosh max, measured 6-10 dB under the voice with
  `python3 measure_audio.py renders/mariah-brunner.mp4 renders/mariah-brunner-overlays.mov` (you render your own).
- **For Edits:** `python3 build.py --overlays` + `npx --yes hyperframes@0.9.83 render overlays --format mov` gives a
  transparent ProRes 4444 overlay (graphics + one-word captions + the effects audio) to drop on their cut with
  `addOverlay`. It only lines up with the exact cut `cut.py` made. If they caption natively in Edits, delete the
  captions block first.
