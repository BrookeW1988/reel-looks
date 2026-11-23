# SPEC: "Inspired by Codie Sanchez" studio editorial

> **Using this template:** the skill copies this folder (and `_shared/` next to it) into its build folder (see `USE.md`), adds the
> fonts below to `assets/fonts/`, puts your SDR take in `~/Movies/Edits-inbox/`, fills the plan (there's no config file:
> Claude writes a `screens.json` in the shape of the `PLAN_EXAMPLE` block in `build.py`, and picks the `--keep` ranges for
> `cut.py`), then runs
> `$PY cut.py --src ~/Movies/Edits-inbox/your-take.mov --keep <a-b> <c-d>` and
> `$PY build.py --screens screens.json`, checks with
> `npx --yes hyperframes@0.9.83 check --json`, and renders the overlay `.mov` for Edits
> (`npx --yes hyperframes@0.9.83 render overlay --format mov`). Needs HyperFrames (Node 22+) and the skill's Python venv.
> Before `cut.py`, the word timings come from one command:
> `$PY -c "import json,os,sys,mlx_whisper as m; r=m.transcribe(os.path.expanduser(sys.argv[1]),path_or_hf_repo='mlx-community/whisper-large-v3-turbo',word_timestamps=True,language='en'); json.dump([{'text':w['word'].strip(),'start':round(w['start'],3),'end':round(w['end'],3)} for s in r['segments'] for w in s['words']],open('assets/words-src.json','w'),indent=1)" ~/Movies/Edits-inbox/your-take.mov`
> Fonts (all SIL Open Font Licence, from Google Fonts; build.py measures every line with these exact files, so they
> must be there): [EB Garamond](https://fonts.google.com/specimen/EB+Garamond) variable roman, saved as
> `assets/fonts/EBGaramond-VF.ttf`, and variable italic, saved as `assets/fonts/EBGaramond-Italic-VF.ttf`;
> [Montserrat](https://fonts.google.com/specimen/Montserrat) variable, saved as `assets/fonts/Montserrat-VF.ttf`.
> (In the Google Fonts download they're called `EBGaramond-VariableFont_wght.ttf`,
> `EBGaramond-Italic-VariableFont_wght.ttf` and `Montserrat-VariableFont_wght.ttf`.)

Goal: the quiet, expensive founder look. One signature caption (bold book-serif lead-in over a light sans line that
types on word by word), warm grade, hard cuts between two framings, a soft lofi bed and nothing else. No SFX, no
colour, no motion except the payoff line. We copy technique only: none of Codie's footage, mic flag, logos,
catchphrases, keywords or music. References: [@codiesanchez](https://www.instagram.com/codiesanchez/) (reel links in
`card.json`).

The demo: one seated talking-head take (1080x1920, 30 fps), two keep ranges joined into **17.84 s at 1.0x** (Codie
never speeds up). The join is hidden by a framing change (B -> A at 13.567 s in the demo), how Codie hides her own
jump cuts.

## Files
| File | Job |
|---|---|
| `cut.py` | rough cut: keeps the ranges, 12 ms audio fades at every seam, 2-pass loudnorm to -14.2 LUFS, remaps word times |
| `assets/words-src.json` | mlx_whisper large-v3-turbo word times on the SOURCE clock (made by the command above), edges checked against the audio |
| `assets/words-cut.json` | the same words on the cut clock (made by cut.py) |
| `build.py` | writes `index.html` (the reel) and `overlay/index.html` (captions only, transparent). All numbers below live in its `STYLE` dict; the per-take plan is the `PLAN_EXAMPLE` block (or `--screens screens.json`) |
| `grade-attr.txt` | the grade, made with `npx --yes hyperframes@0.9.83 media-treatment --selector "#a-roll" --grading <grade.json> --apply` |
| `assets/fonts/` | EB Garamond (roman + italic, variable) and Montserrat (variable), SIL OFL: not shipped, see the box above |
| `assets/music/your-bed.m4a` | optional, not shipped: a soft lofi bed (mellow keys, light vinyl texture). If it isn't there the reel has no bed; add music in the Edits window yourself (library music goes silent in Claude exports) or use your own file |

## Palette (only these)
| Token | Hex | Used for |
|---|---|---|
| caption-white | `#FFFFFF` | every caption glyph |
| glow | `rgba(0,0,0,0.45)` | `text-shadow: 0 0 24px` behind every caption, offset 0 |
| plate | `#0F0A0B` | page background (never seen; Codie's measured shadow tone) |
| skin target | `#CD8B76` | grade target. Measured on the demo render: forehead `#C3816E` |

## Type (1080x1920)
| Element | Font | Size / weight / tracking | Position (baseline) | Notes |
|---|---|---|---|---|
| Line 1 lead-in | EB Garamond | 94 px / 700 / -2% | y 1561 | cap height 62 px, x-height 41 (Codie measured 61 / 40) |
| Line 2 continuation | Montserrat | 86 px / 300 / -1% | y 1645 (84 px under line 1) | cap 61, x-height 45 (Codie 47). Words cut on at their onsets from a fixed left edge |
| Solo emphasis | EB Garamond | 128 px / 700 / -2% | y 1615 | 1.3x line 1. Builds word by word. A long one auto-fits (one went to 110 px in the demo) |
| Payoff (last screen) | EB Garamond | 104 px / 500 / -1%, line 2 *italic* + underline 4 px, offset 12 px | y 1580 and 1680 | 2 lines, the words from `italic_from` on in italic |

- Max line width **760 px**. build.py measures every line with the real font file (PIL) and shrinks it in 2 px steps,
  never below 80% (then it stops and asks for a re-split). In the demo one line fitted 86 -> 80 px, one 128 -> 110 px.
- Line 1 = 2-4 words (median 3), line 2 = 2-4 words. No punctuation (full stops and commas stripped), sentence case,
  no stroke, no highlight, no emoji.
- Screens: a new one every ~1.6 s. The demo had 11 screens, 3 solo (27%, Codie ~20%), each living 0.80-2.10 s, the
  payoff screen from 16.20 s to the end.

### Why the captions sit at 81% down, not Codie's 61%
Codie's framing has her chest in shot; her caption block sits at y ~1087-1232. A tight close-up (like the demo: hairline
y ~580, mouth ~1330, chin 1400-1460) would have Codie's slot over the mouth (rule: nothing over the face). So the block
moves to the chest, just under the chin: **line 1 cap-top 1500 -> line 2 descender ~1665**. Check in every snapshot
that the chin never reaches the block. Cost: it sits below the platform title-safe line (1330), so on Instagram the
bottom of line 2 can meet the username/caption row. See "How a member's version differs".

## Motion
- **Captions:** screen 0 is on screen at frame 0 (thumbnail). Every other screen hard-swaps in on its first word's
  onset (snapped to the frame), 0-frame cut-on: no fade, pop, scale or typewriter. Each screen dies 4 ms before the next
  is born so two can never show at once. Line 2 and solo words appear at their own spoken onsets.
- **Payoff only:** 0.2 s (6 frames) slide x -40 -> 0 + opacity 0 -> 1, `power2.out`, with a horizontal-only SVG blur
  14 px -> 0 (motion blur). Holds to the last frame. Nothing else in the reel animates.
- **Camera:** two "angles" from one phone. A = scale 1.00. B = scale **1.18**, origin bottom-right (the face rises and
  moves ~90 px left, like a second camera). Hard `gsap.set` cuts on phrase boundaries, never eased, never creeping.
  The demo: A 0 | B 2.03 | A 3.33 | B 5.43 | A 6.73 | B 9.73 | A 13.57 (the join) | B 16.20 (payoff).
  Shots 2.03 / 1.30 / 2.10 / 1.30 / 3.00 / 3.83 / 2.63 / 1.63 s: mean 2.23 s, shortest 1.30 s, 23.5 cuts/min
  (Codie: mean 2.38-3.03, shortest 0.75-0.90, 18.5-24/min). First cut 2.03 s (Codie 0.83-3.7).
- No transitions, no speed ramps, no zooms that move. Ends on the payoff: the video stops ~0.05 s after the last word
  ends (17.78 -> 17.83 s in the demo; Codie: final cut within ~0.3 s of the last word). The payoff held 1.63 s.

## Sound
| Layer | Number |
|---|---|
| Voice | levelled in cut.py to -14.2 LUFS integrated (two-pass loudnorm, TP -1.5) |
| Music bed | a soft lofi bed (Edits: search "lofi" or "ambient"), `--music-start` 3.00 s into the track (skips a silent intro so frame 0 lands on its first hit), `data-volume` **0.13** (a -13 LUFS track -> -30.6 LUFS in place = 16.5 dB under the voice), fade-in 0.02 s, fade-out 0.25 s, runs 0:00 to the last frame, no swells. Not shipped: add it in the Edits window yourself (library music goes silent in Claude exports) or use your own file |
| SFX | none (Codie's format A has none: silence apart from voice + bed is the luxury signal) |
| Measured on the demo render | -14.0 LUFS integrated, true peak -1.4 dBFS, LRA 1.0 LU |

## Grade (media-treatment, rec709)
`exposure -0.03, contrast +0.08, highlights -0.15, shadows -0.05, blacks +0.06, temperature +0.14, tint +0.02,
saturation +0.12, vignette 0, grain 0`.
Measured on the demo render (1 fps) vs Codie: luma mean 93.0 (her studio 63-64, daylight 97-110: a grey daylight
room sits just under her daylight range, moodier), V 135.6 (her 133-150), U 122.9 (her 120-127), saturation
10.9 (her 9-22), forehead `#C3816E` (target `#CD8B76`), low end 16.3 (her 20-33; the demo's top was true black).
The demo source before grade: luma 105.5, V 132.6, U 126.0, saturation 8.0.
No vignette: Codie's own grade is lighting, not a filter.

## Banned here
Colour-highlighted words, stroked/outlined/all-caps captions, emoji, pop/bounce/typewriter flicker, any transition,
creeping zoom, speed ramp, SFX, a swelling bed, end card, logo, "follow for more", captions over the face, lines
wider than 760 px, Codie's catchphrases/keywords/logos/music/footage.

## How a member's version differs
1. **Footage + words:** make `assets/words-src.json` with the command in the box at the top, then run
   `$PY cut.py --src <their take> --keep <ranges>`. Then write a `screens.json` (screens +
   camera word indexes, the same shape as `PLAN_EXAMPLE` in build.py) and run
   `$PY build.py --footage assets/cut.mp4 --words assets/words-cut.json --screens screens.json`.
   The `lead` number per screen says how many words get the serif lead-in; `kind: solo` makes a serif emphasis screen;
   the last screen is `payoff` with `italic_from`.
2. **Caption height:** if they film the Codie way (phone a bit further back, chest in shot, eyes about a third down),
   move the block up to Codie's slot: `l1_baseline 1150, l2_baseline 1232, solo_baseline 1190,
   payoff_baselines (1150, 1250)`. That puts it inside every platform's safe area. A tight close-up needs 1561.
   Always check the chin in snapshots: the block must clear it.
3. **Camera B:** 1.18 is right for 1080 p footage. With 4K footage they can go to 1.25-1.3 and get a clearer
   "second camera".
4. **Grade:** re-run `npx --yes hyperframes@0.9.83 media-treatment --analyze`, then aim for the measured targets above
   (warm V 133-150, saturation 9-22, soft blacks); a lamp-lit room needs less temperature than a grey daylight room.
5. **Music:** in Edits, use Edits' own library. Pick a soft lofi/ambient track, set it 16-20 dB under the voice (Edits
   volume about 10-15%), export from the Edits window (library songs can go silent in automated exports).
6. **In Edits:** the overlay `.mov` carries every caption with its glow and timing; hard cuts and the 1.18 punch-in
   are native Edits moves (scale keyframes, hard). Fallback without the overlay: Edits auto captions with imported
   EB Garamond 700, two lines, no highlight, shadow on, at the same height. That loses the two-font pairing.
