# SPEC: Podcast clip, inspired by The Diary of a CEO

> **Using this template:** the skill copies this folder (and `_shared/` next to it) into its build folder (see `USE.md`), adds the
> fonts below to `assets/fonts/`, puts your SDR take in `~/Movies/Edits-inbox/`, fills the two "CLAUDE CHANGES PER TAKE"
> blocks (there's no separate config file: the block at the top of `cut.py` holds SRC, KEEP, SPEED, REACT; the block in
> `build.py` holds the name label, camera plan, ID card facts, B&W beat and red words), then runs `python3 cut.py` and
> `$PY build.py --hook "LINE ONE|LINE TWO" --hook-red WORD`, checks with
> `npx --yes hyperframes@0.9.83 check --json`, and renders the overlay `.mov` for Edits
> (`npx --yes hyperframes@0.9.83 render overlays --format mov --workers 2 -o renders/diary-of-a-ceo-overlays.mov`).
> Needs HyperFrames (Node 22+) and the skill's Python venv.
> Before `cut.py`, the word timings come from one command:
> `$PY -c "import json,os,sys,mlx_whisper as m; r=m.transcribe(os.path.expanduser(sys.argv[1]),path_or_hf_repo='mlx-community/whisper-large-v3-turbo',word_timestamps=True,language='en'); json.dump([{'text':w['word'].strip(),'start':round(w['start'],3),'end':round(w['end'],3)} for s in r['segments'] for w in s['words']],open('assets/words-src.json','w'),indent=1)" ~/Movies/Edits-inbox/your-take.mov`
> Fonts: Inter 500-900 ([Google Fonts](https://fonts.google.com/specimen/Inter)) and EB Garamond italic 500
> ([Google Fonts](https://fonts.google.com/specimen/EB+Garamond)), both SIL Open Font Licence and both bundled with
> HyperFrames, so nothing has to go in `assets/fonts/`. Optional: `assets/fonts/Inter-Black.ttf` (`_shared/get_fonts.sh diary-of-a-ceo` gets it; or `Inter-Black.otf` from the
> [Inter release zip](https://github.com/rsms/inter/releases), SIL OFL) makes the hook width-lock exact; without it
> build.py uses an average-width estimate.

**What it is:** the member default for this look: the **Tier B "Quick clip"** system (1-3 word captions, hard
switches, fixed position, speaker colours, dark moody grade, no SFX on cuts) plus **3 Tier A "Documentary" moves**:
(1) the hook frame (side-by-side split, glowing divider, width-locked caps on black boxes, one red word), (2) the ID card
at 21-33% of runtime, (3) the emotional colour-to-B&W beat on the last line.
Techniques only: no DOAC footage, logo, wordmark, end card, ID-card art, guest images, exact hooks or CTA line.
References: [@thediaryofaceo](https://www.instagram.com/thediaryofaceo/) (reel links in `card.json`).
The demo: one camera, one speaker, 1080x1920, 30 fps, SDR.

Files: `cut.py` (rough cut + word re-timing) -> `build.py` (writes `index.html` and `overlays/index.html`) ->
`npx --yes hyperframes@0.9.83 check` -> render. Grades live in `grades.json` (made by `hyperframes media-treatment`).

## Rough cut (`cut.py`)
| What | Number |
|---|---|
| Source stretch | one self-contained ~34 s stretch of the take in the demo (example KEEP ranges in `cut.py`) |
| Dropped | list signposts ("number two", "number three is...": a clip isn't a list), plus slack pauses (0.38, 0.22, 0.36 s in the demo) |
| Pauses kept on purpose | ~0.1 s pauses (trimming them makes 0.1 s jump cuts one camera can't hide) |
| Speed | 1.1x (atempo, pitch kept). The demo: 80 words in 27.95 s of speech = 172 wpm (DOAC Tier B measured 177-184) |
| Result (demo) | `assets/cut.mp4` 28.00 s video (840 frames) / 27.95 s audio. Audio joins at 5.755, 11.809, 17.027, 24.064 s |
| Edges | measured on a 10 ms loudness envelope, 12 ms audio fades on every join; first word starts at 0.00 s (DOAC: all 8 refs) |
| Word timings | mlx_whisper large-v3-turbo, word_timestamps, clamped into the kept range they overlap most (`assets/words-cut.json`) |
| Listening shot | `assets/react.mp4` = a 2 s silent stretch, mouth closed (the demo used source 0.05-2.05 s, before the speaker starts) at 0.9x = 2.20 s, muted |
| ID-card portrait | `assets/portrait.png` = the member's own photo, or a still from her take (the demo: a 900x1125 crop, looking at camera, mouth closed). Not shipped; skipped if missing |

## Palette (only these)
| Token | Hex | Used for |
|---|---|---|
| ink | `#000000` | hook boxes, name-label box, ID-card ground, page background |
| paper | `#FCFCFC` | hook words, guest captions (`--guest-colour`) |
| host amber | `#F2B840` | host captions (`--host-colour`) and the name label under the hook |
| alarm red | `#E04B4D` | the ONE red word in the hook (`--hook-red`) and one word per caption block (`--emphasis-colour`) |
| dossier paper | `#EFE4D6` (gradient `#F4EBDD` -> `#E2D3BF`) | ID card |
| dossier red | `#7F140C` | ID-card tags, PROFILE label and rule; tag text `#F3E9DA` |
| print white | `#FAF7F0` | photo-print border |
| divider | `#FBFBFB` + glow `0 0 18px 4px rgba(255,255,255,.65), 0 0 46px 14px rgba(255,255,255,.22)` | 12 px line at x 534-546 |
One emphasis colour family per clip (red). No topic accent, no rose.

## Type (1080x1920)
| Element | Font | Size / weight / case | Where |
|---|---|---|---|
| Hook, 2 lines | Inter 900, tracking -1% | **width-locked: both lines 615 px wide** (59.2 px and 62.1 px in the demo, measured with PIL on Inter Black) | black box per line, padding 24/30/22, radius 8; top y 292, 10 px gap; centre x 540 |
| Name label | Inter 700, 38 px, sentence case | amber on a black box (padding 10/18), radius 6 | top y 548 (amber on a bright window measured 2.07:1 in the demo, so it gets a box) |
| Captions | Inter 700, 66 px, line 1.2, tracking -1% | as spoken, end punctuation dropped | fixed, centre y 1545, padding 60 px; shadow `0 3px 12px rgba(0,0,0,.6)` |
| ID card label | Inter 900, 28 px, tracking .28em, caps | "PROFILE", dossier red + 3 px rule at 55% | card x48 y42 |
| ID card name | Inter 900, 128 px, line 0.9, tracking -3%, caps, 2 lines | ink `#0A0A0A` | card x42 y640 |
| ID card role | EB Garamond italic 500, 44 px, line 1.18, `text-wrap: balance` | `#2A2320` | card x48 y886, w 740 |
| ID card tags | Inter 900, 32 px, tracking .06em, caps | printed labels, padding 14/18/12, tilts -2, 1.2, -0.8 deg, 22 px apart | card x458 y178 |

## Layout and camera
| Frame | Numbers |
|---|---|
| Hook frame (0-2.20 s) | side-by-side split, two 540x1920 panels, each video at 1.15x scaled from the top (1242x2208). Left = the speaking cut (source x offset 405 at 1.0), right = the listening shot (offset 276), looking toward the speaker |
| Crops (one camera) | W = 1.0; M = 1.2, x -60, y -144 (eyes ~840); T = 1.3, y -266 (eyes ~720). Origin 50%/50%. 1.3 is the cap on 1080p. **Never cut M<->T** (only 1.08x apart) |
| Shot list (demo, cut clock) | 0 split · 2.20 W · 3.86 T · 5.755 ID card · 9.20 T · 11.809 W · 13.84 M · 17.027 W · 19.45 M · 21.58 W · 22.95 T (the number punch) · 24.064 W to the end |
| Shot lengths | 1.7-3.9 s (median ~2.2 s); the demo tightened to 1.4 s and 1.1 s on purpose into its big number line |
| Joins | every audio join lands on a crop change or the ID card, so no jump cut shows |
| ID card (5.755-9.20 s = 21-33% of runtime) | full-screen insert on black. Paper x100 y252 880x1056, rotate -1.2 deg, shadow `0 50px 120px rgba(0,0,0,.75)`, SVG fractal-noise grain at 22% multiply (seed 7) + one stain |
| Print | x46 y122 in the card, 380x474, 16 px border (50 px bottom), tape strip 170x52; photo graded B&W halftone (below) |

## Motion
- **Hook: static on frame 0, no entrance.** Leaves on a hard cut at 2.20 s together with the split (DOAC: 1.28-3.79 s). The hook never shares the screen with a caption.
- **Camera:** hard cuts only (`gsap.set`), no creeping zoom anywhere.
- **Captions:** hard switch, 0 frames in and out (Tier B). A block opens 0.03 s before its first word and holds until the next block. First caption at 2.20 s.
- **ID card:** hard cut in (on an audio join) and hard cut out. Print lands 0.02 s in: opacity 0->1, scale 1.12->1, rotate -9->-4, blur 10->0 px, 0.38 s expo.out. Tags stamp in at +0.75, +1.05, +1.35 s: scale 1.35->1 + opacity, 0.12 s power4.out (a slam, no bounce). Then 1.7 s dead still.
- **B&W beat:** from a word in the last line (24.73 s in the demo) a B&W-graded copy of the same frames fades over the colour shot, 1.70 s power1.inOut, held to the end. (Saturation can't be keyframed in the grade, so it's a matched second layer.)

## Caption blocks (built by `build.py`, 1-3 words)
Rules: break on `. , ? !` or a 150 ms pause; inside a sentence a small scorer prefers 3s then 2s (single words cost 3, a
4-word block only if 16 characters or less), never ends a block on a weak word (a, the, of, to, and, on, in, for...) or a
dangling subject/auxiliary (we, can, is...), and favours blocks that open on "of / in / and / that / so / like".
Red words (one per block max): the `EMPHASIS` set in build.py, the speaker's own stressed words (7 in the demo).
The demo came out at 26 blocks over 28 s.

## Sound (measured on the demo)
| Moment | Sound | Placed by peak | Volume |
|---|---|---|---|
| Voice | `cut.mp4` own audio | | 1.0 (the demo cut measured -14.3 LUFS integrated, true peak -1.8 dBTP) |
| Print lands (card in + 0.30 s) | a paper slide (Edits: searchSoundEffects "paper slide"), file `paper-slide.mp3` (the demo file peaked 0.540 s in) | start = moment + 1 frame - peak | 0.55 -> 6.4 dB under the voice |
| Tag 1 / 2 / 3 (card in + 0.75 / 1.05 / 1.35 s) | two different rubber-stamp takes and a stapler (Edits: searchSoundEffects "stamp", "stapler"), files `stamp-1.mp3`, `stamp-2.mp3`, `stapler.mp3` (the demo peaks 0.000, 0.000, 0.083 s) | same rule | 0.42 / 0.66 / 0.58 -> 7.3 / 7.2 / 6.8 dB under |
| Cuts | nothing (DOAC: no SFX on cuts) | | |
"under" = 150 ms maximum of the effect (voice subtracted from the render) vs the voice's loud moments over the card (-10.8 dB).
Demo final mix: **-14.2 LUFS integrated, LRA 1.6 LU, true peak -1.0 dBFS.**
Target: voice -14 LUFS integrated; effects 6-10 dB under the voice; a bed 15-20 dB under.
SFX aren't shipped. Either drop your own files into assets/sfx/ with these names, or skip them in the overlay and add them
natively in Edits with searchSoundEffects + addSoundEffect. build.py skips any file that isn't there.
**Music:** none by default. Add it in the Edits window yourself (library music goes silent in Claude exports) or use your
own licensed file: `build.py --music <track>` adds it at 17 dB under the voice and drops it to 3% (about -30 dB) under the
B&W line, which is DOAC's measured drama move.

## Grade (`hyperframes media-treatment`, cached in `grades.json`)
| Layer | Controls |
|---|---|
| Footage (colour) | exposure -0.18, contrast +0.15, highlights -0.35, whites -0.20, shadows -0.30, blacks -0.20, saturation -0.12, temperature +0.03, vignette 0.38 |
| B&W beat | same, plus contrast +0.22, blacks -0.25, saturation -1.0, vignette 0.42, grain 0.08 |
| ID-card print | contrast +0.30, saturation -1.0, exposure +0.05, halftone 0.85 size 0.16, grain 0.10 |
Starting point is the DOAC member recipe plus its "bright home office" note (exposure -0.15, shadows -0.30). Highlights
and whites go further when a window sits right behind the head (as in the demo).

## How a member's version differs
1. **Their footage, their words.** Make `assets/words-src.json` (command in the box at the top), edit the per-take block in `cut.py` (SRC, KEEP, SPEED, REACT), run it, then `$PY build.py --hook "LINE ONE|LINE TWO" --hook-red WORD`. Proofread every caption against the audio.
2. **Hook line** = their first spoken sentence sharpened into a claim, a "how" or a question, 3-6 words, 2 lines, one red word. Never a different moment from the clip.
3. **ID card** = their own photo and real facts only (`IDCARD_FACTS`). No invented titles, numbers or awards.
4. **One camera (most members):** keep the W/M/T crops and the "never M<->T" rule. On 1080p cap the tight crop at 1.3x; 4K phone footage can go to 1.5x. Put a crop change on every audio join.
5. **Two-person Zoom / Riverside recording:** this is the closest a member gets to the real two-camera exchange.
   - Crop each person out of the two-up recording to their own panel. The hook frame uses the side-by-side split exactly as here (speaker left, listener right), or a stacked 50/50 split with the seam at y 962 and the host on top.
   - Tag every word with `"speaker": "host"` or `"guest"` (Riverside exports per-speaker tracks; a Zoom recording needs speaker diarisation or a manual pass). `build.py` colours host words amber `#F2B840` and guest words white; keep red for one word per block.
   - After the hook, cut between the two people on the sentence, not every line: 2-4 s shots, plus a 2-3 s silent listening shot of the host after a big line.
   - Zoom halves are often 640-960 px wide: a 1.3x crop of a half goes soft. Use 1.0 and 1.15 only, and record locally in Riverside (4K per person) when possible.
   - If each person's audio is on its own track, keep both and mix them, don't pick one.
6. **Music:** only their own licensed track (`--music`), 15-20 dB under the voice. Edits' library music drops out of automated exports.
7. **Ending:** a resolved line (Tier B) unless there's a real full episode or replay to send people to; then an open loop plus "Full episode: [show name]" in Inter 800 for the last 4.7-5.7 s. Never the show's own end-card wording or logo.
8. **In Edits** (no full render): the overlays render (`renders/diary-of-a-ceo-overlays.mov`, you render your own) carries the hook, divider, name label, ID card and captions with alpha. Lay it over their own cut with addOverlay; do the crops, the B&W beat (split the clip, B&W filter on the second half) and the grade sliders natively.

## Banned here
Animating the hook in; a caption on screen with the hook; bouncy or typewriter captions; more than one red word per block;
SFX on cuts or stock whooshes; slow creeping zooms; bright creator grading; captions over the mouth or eyes; the ID card in
the first 15%; any fact, quote, number or guest that isn't real; any DOAC asset.
