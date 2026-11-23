# SPEC: A look inspired by Iman Gadzhi, value-only motion

> **Using this template:** the skill copies this folder (and `_shared/` next to it) into its build folder (see `USE.md`), adds the
> fonts below to `assets/fonts/`, puts your SDR take in `~/Movies/Edits-inbox/`, fills `reel.json`, then runs
> `python3 cut.py` and `$PY build.py` (writes `index.html`), checks with
> `npx --yes hyperframes@0.9.83 check --json`, and renders the overlay `.mov` for Edits:
> `$PY build.py --overlay && npx --yes hyperframes@0.9.83 render -c overlays.html --format mov --workers 2 -o renders/iman-gadzhi-overlays.mov && rm overlays.html`
> (`overlays.html` is deleted after rendering: two root compositions in one folder fail `check`). Needs HyperFrames
> (Node 22+) and the skill's Python venv (build.py uses PIL and numpy).
> Before `cut.py`, the word timings come from one command:
> `$PY -c "import json,os,sys,mlx_whisper as m; r=m.transcribe(os.path.expanduser(sys.argv[1]),path_or_hf_repo='mlx-community/whisper-large-v3-turbo',word_timestamps=True,language='en'); json.dump([{'text':w['word'].strip(),'start':round(w['start'],3),'end':round(w['end'],3)} for s in r['segments'] for w in s['words']],open('assets/words-src.json','w'),indent=1)" ~/Movies/Edits-inbox/your-take.mov`
> Fonts and pen file (none shipped):
> - **Anton** ([Google Fonts](https://fonts.google.com/specimen/Anton), SIL Open Font Licence) saved as
>   `assets/fonts/Anton-Regular.ttf` (build.py measures every condensed word with this exact file, so it must be there).
> - **Caveat 700 + the baked pen strokes** come from the HyperFrames registry block `hw-write-title`. In the project folder
>   run `npx --yes hyperframes@0.9.83 add hw-write-title`: it installs `assets/baked/caveat-pen.js` (Caveat 700 glyph
>   outlines + centreline pen strokes, generated from Caveat) and `assets/fonts/Caveat-700-latin.woff2`. Caveat is SIL
>   Open Font Licence ([Google Fonts](https://fonts.google.com/specimen/Caveat)). The same `add` also drops
>   `compositions/hw-write-title.html`; delete it (the reel doesn't mount it, and an unmounted copy of the block's source
>   is in `registry-source/` for reference). Without `caveat-pen.js` the handwriting can't draw and the page won't build.
> - **Inter** 800 ([Google Fonts](https://fonts.google.com/specimen/Inter), SIL OFL) is bundled with HyperFrames: nothing to add.
> The overlay page is `overlays.html`: graphics + captions, transparent, no audio.

**Goal:** a member watches her own cut and feels that every graphic is a *reward*: the face does most of the talking,
motion only fires on a value sentence, and a numbered rail shows how far through the reasons we are.
**Output:** HyperFrames, 1080 x 1920, 30 fps (the demo: 29.37 s, 881 frames). Techniques only: no Iman footage, logos,
phrases, product names or chapter objects (no chess pieces, safes, plinths). No AI people. Every word on screen is the
speaker's own, apart from short editorial chapter titles (1-2 words) taken from her own points.
References: [@imangadzhi](https://www.instagram.com/imangadzhi/) (reel links in `card.json`).

## Source and cut (cut.py, all numbers in reel.json)
- Footage: one talking-head take, SDR 1080x1920 (the demo: 57.6 s with a spoken "three reasons" list). Words:
  mlx_whisper large-v3-turbo, word timestamps.
- Kept: the hook + claim + "here's why", each numbered point's value sentence, the close (9 keep ranges in the demo,
  example values in `reel.json`). Dropped: the elaboration between reasons.
- Every seam sits in a measured low-energy gap (20 ms RMS profile). Whisper ran up to 0.44 s early after pauses, so the
  demo snapped 17 word edges to measured onsets (`snap_src`) and dropped two phantom words (`drop_src`).
- Speed 1.1x (atempo, pitch kept). Voice levelled with one linear gain to **-14.0 LUFS** (demo measured -14.1, gain
  +0.10 dB; true peak -2.0 dBTP), never pushing a peak past -1 dBTP. 12 ms audio fades at every seam.

## Palette (one accent, black, white: nothing else)
| Token | Hex | Used for |
|---|---|---|
| accent | `#2230E8` (swap for the member's brand colour) | lit rail boxes, handwriting over footage, the hook stamp, the number field's tape, the X of 10X, $ on the bills, active caption word block, the concept field |
| ink | `#0B0B0D` | tape strips, unlit rail boxes (82% fill), the number field, bill linework, underline squiggle, caption stroke |
| paper | `#FFFFFF` | condensed type, handwriting on fields, bills, caption fill |
| texture | grain PNG (seeded noise, sd 34, made by build.py) at 38% overlay + 16 seeded doodles (squiggle, spiral, star, arrow, loop) at 16% (accent field) / 9% (black field) | every full-screen field: never flat |

## Type
| Element | Font | Size | Where |
|---|---|---|---|
| Hook hero | Anton (OFL, assets/fonts) | fitted 110-140 px (134 px in the demo), +1% tracking, ink tape (653 x 160 in the demo) | tape x 94 y 372, rotated -2° |
| Hook note | Caveat 700, baked pen strokes (registry `hw-write-title` engine) | 86 px, accent | x 110 y 296 |
| Hook stamp | Anton | 64 px on accent, padding 10/18/6 | at the tape's right end, rotated 8° |
| Rail boxes 1 2 3 | Anton 44 px in 66 x 66 boxes, 4 px ink border, 14 px gap | unlit = ink 82% + 50% white digit; lit = accent | x 100 y 302 |
| Chapter note (the speaker's words: "one", "number two"...) | Caveat 700 | 66 px, accent | x 362 y 298, right of the rail |
| Chapter title tape | Anton | fitted 90-118 px (the demo: 108, 118, 118), max text width 730 | x 94 y 382, rotated -1.5° |
| Concept field small / hero | Anton | 118 px / fitted 200-320 px to 660 px (250 px in the demo), white | y 350 / y 470, centred |
| Concept field note | Caveat 700 | 104 px, white, ink squiggle underline 8 px | under the hero (y 714 in the demo), centred |
| Number field (10X) | Anton | 480 px, white digits, accent suffix | y 560, centred |
| Number note / tape | Caveat 96 px white / Anton 92 px on accent tape | y 420 / y 1040, rotated -7° |
| Captions | Inter 800 | 62 px, line 1.25, white, 7 px ink stroke; spoken word on an accent block, radius 10 | top y 1440, centred, max 3 words / 22 characters |

**Top band:** every graphic over the face lives between y 280 (Instagram/Shorts top UI) and y 535 (the demo's hairline,
measured at 520-600 across the cut), x 100-900 (TikTok side margins, Shorts action rail). Captions sit at y 1440 because
the demo chin reached y ~1390: under the chin beats on the chin, at the cost of sitting near the platform caption area.

## Animated budget (build.py enforces it)
| Event | Type | On screen (demo, cut s) | Anchored to |
|---|---|---|---|
| Hook | top-band tape + note + stamp | 0.00-1.80 (frame 0 = full hook) | out on `hook.out_on` |
| Concept field | full-screen, accent field | 4.27-6.85 | in on the claim, out after its last word |
| Rail map | 3 boxes stamp in | 7.02 -> end | `map.on` (open loop) |
| Ch 1 | rail box 1 lights + tape | 7.70-9.51 | "one" -> end of its value sentence |
| Ch 2 | rail box 2 + tape | 13.46-14.54 | "number two" -> its `out_after` |
| Ch 3 | rail box 3 + tape | 17.26-18.88 | "number three" -> its `out_after` |
| Number field | full-screen, black field | 24.41-25.60 | in on `in_on`, lands on the number, out before the next sentence |
**Demo total 10.07 s of 29.37 s = 34.3%** (ceiling 35%, `value_budget`). The persistent rail (66 px boxes) is a progress
bar and is not counted. Demo bare-face stretches: 1.8-4.27, 6.85-7.70, 9.51-13.46, 14.54-17.26, 18.88-24.41 (5.5 s,
the longest), 25.60-29.37.

## Motion (eases by role)
- **Cuts:** majors are hard cuts in and out (the Iman grammar: cut to the world, cut straight back to the face).
- **Camera:** hard-cut punch-ins only, never a creep: an optional 1.08 / 1.0 pair inside the hook sentence
  (`emphasis_punch`); then alternating 1.08 / 1.0 / 1.06 / 1.0 at every jump cut (demo: 7.70 1.08 · 9.32 1.0 · 13.46 1.06 ·
  14.06 1.0 · 17.26 1.08 · 19.07 1.0 · 23.29 1.06 · 25.49 1.0). Origin 50% 52% (y ~1000) so the hairline never rises into
  the top band and the chin never drops into the captions.
- **Write-on everything:** Anton letters wipe on left-to-right one by one (clip-path, 0.08-0.1 s each, `steps(3)`,
  stagger 32-45 ms), synced to the spoken word (the small line on its first word, the hero on the hero word).
  Handwriting is pen-traced in stroke order with a curvature-adaptive pen speed (registry `hw-write-title` engine) in
  0.36-0.7 s.
- **Tape:** wipes on from the left (clip-path, 0.26 s `power4.out`, x -40 -> 0); out = collapses back toward its rail
  box (scaleX -> 0 from the left, 0.2 s `power3.in`, 6 px blur): "old items slide left and persist" as the lit box.
- **Stamps** (hook stamp, number tape): slap in, scale 1.7 -> 1, blur 8 -> 0, 0.1-0.12 s `power3.in` (accelerates into
  the surface).
- **Bills:** drop from y -720, 0.34 s `power3.out` quantised to 6 steps (stop-motion paper feel), 70 ms apart.
- **Number counter:** integers `from` -> `to` (1 -> 10 in the demo) over ~0.42 s (`power1.in`), lands exactly on the
  spoken number (24.864 s in the demo) with scale 1.18 -> 1, blur 4 -> 0, 0.24 s `expo.out`.
- **Boil:** handwriting re-poses every 3 frames by ±1.4 px / ±0.5° (hand-drawn, not a floating loop).
- **Captions:** groups fade/rise in 0.12 s, out 0.08 s; never across a jump cut; off during both full-screen majors.

## Sound (no music: voice-led; each hit 1 frame after its picture, levelled to -22 LUFS momentary = 8 dB under the voice)
SFX aren't shipped. Either drop your own files into assets/sfx/ with these names, or skip them in the overlay and add
them natively in Edits with searchSoundEffects + addSoundEffect. build.py skips any file that isn't there.
Music: none in this look. If you want some, add it in the Edits window yourself (library music goes silent in Claude
exports) or use your own file.

| Moment | Sound (file name build.py looks for in assets/sfx/) | Picture time (demo) |
|---|---|---|
| Hook stamp | rubber stamp (Edits: searchSoundEffects "stamp"), `stamp-1.mp3` | 1.26 |
| Concept field cuts in | page turn (Edits: "page turn"), `page-turn.mp3` | 4.27 |
| Bills land | card clack (Edits: "cards"), `card-clack.mp3` | 4.57 |
| Note writes | pen writing on paper (Edits: "pen writing"), `pen.mp3` (a 0.04-0.89 s slice) | 5.47 |
| Ch 1 / 2 / 3 tape | three different whoosh takes (Edits: "whoosh"), `whoosh-a.mp3` / `whoosh-b.mp3` / `whoosh-c.mp3` (a whoosh on step lines) | 7.84 / 13.60 / 17.40 |
| Number lands | soft thud (Edits: "thud"), `thud.mp3` | 24.86 |
| Number tape | a second stamp take, `stamp-2.mp3` | 25.08 |
build.py measures each slice's energy peak (5 ms RMS) and EBU momentary max, then sets `start = picture + 1 frame - peak`
and `volume = 10^((-22 - Mmax)/20)` (capped at +12 dB). After a full render, `python3 measure.py` writes the measured
results to `renders/audio-measure.json` (you render your own).

## Grade (media-treatment on #a-roll)
The demo's analysis: balanced, no clipping (Y 17-237, mean 106). Applied: exposure +0.02, contrast +0.10, blacks -0.04,
temperature -0.04 (a touch cool to sit with the blue accent: "set lighting matches the accent", done in the grade when
you can't relight the room), saturation +0.03, vibrance +0.02, vignette 0.12. Stored in `grade-attr.txt`. With a warm
brand accent, nudge temperature warm instead.

## BANNED here
Fade-and-slide-up on everything; floating/breathing loops; slow creeping zoom; the same whoosh twice; any graphic on a
story/elaboration sentence; more than one accent; a flat untextured field; text over the face; invented stats; AI people;
Iman's footage, chapter objects, product names or catchphrases.

## How a member's version differs
Everything a member changes lives in `reel.json`; then `python3 cut.py && $PY build.py && npx --yes hyperframes@0.9.83 check --json`, then the overlay render in the box at the top.

1. **Find the value sentences first (this IS the style).** Read the transcript and tag only these: a bold claim, a
   definition/concept, any number (always), a structural "number two / step three" line, a promise ("here's why"), real
   proof, a quote. Everything else (stories, "honestly...", caveats, warm-ups, the call to action's chat) stays on the
   bare face. Quick test: *would this sentence still be useful written on a sticky note?* If yes, it's value.
2. **Budget:** 3-6 events in a 30-45 s reel, at most 35% animated (build.py stops you). If you're over, cut the weakest
   claim, never the number.
3. **Pick the two majors:** the hook claim and the biggest number get full screens (`majors`). Compress each to 1-3 words
   + one literal object (cash for money, a clock for time, a door for opportunity), drawn, never AI people. (build.py
   draws bills for the accent field; another object means editing that SVG.)
4. **Chapters:** if you say "one / two / three", list them in `chapters` with your own words as the handwritten label and a
   1-2 word title. No list? Delete the rail (`map.count: 0` and no chapters) and use the tape label for your key phrase.
5. **Your accent:** set `accent` to your brand colour. Keep it the only colour.
6. **Your face position:** check your hairline and chin with a contact sheet; move `NOTE_Y/TAPE_Y` (build.py) and the
   caption `top` (src/page.template.html) so nothing touches your face.
7. **Your words:** re-time with mlx_whisper (command in the box at the top), then snap the edges at each cut and each
   trigger word in `snap_src` (whisper runs early after pauses); proofread captions via `caption_fixes`.
8. In Edits: import `renders/iman-gadzhi-overlays.mov` (you render your own) above your cut, then add the sounds (Edits' own whooshes are fine)
   and captions natively if you prefer Edits' captions (the overlay MOV includes ours).
