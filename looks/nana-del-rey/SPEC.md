# SPEC: "Soft Cinema", a look inspired by Nana DelRey

> **Using this template:** the skill copies this folder (and `_shared/` next to it) into its build folder (see `USE.md`), adds the
> fonts below to `assets/fonts/`, puts your SDR take in `~/Movies/Edits-inbox/`, fills `reel.json` (and SRC/KEEP in
> `cut.py`), then runs `python3 cut.py` and `$PY build.py` (after
> `npx --yes hyperframes@0.9.83 remove-background assets/cut.mp4 -o assets/cutout.webm --quality best`), checks with
> `npx --yes hyperframes@0.9.83 check --json`, and renders the overlay `.mov` for Edits
> (`$PY build.py --overlay`, render, then rebuild). Needs HyperFrames (Node 22+) and the
> skill's Python venv (build.py uses Pillow to measure the words). Fonts: Inter Tight, variable file
> `assets/fonts/InterTight-VariableFont_wght.ttf` (https://fonts.google.com/specimen/Inter+Tight, SIL Open Font
> Licence). This is the look's own font, not a brand font.

The style copies Nana DelRey's editing techniques only (references: her reels listed in `card.json`). Nothing of hers
is used: no footage, rooms, people, names, keywords, catchphrases or logos. Every word on screen is the speaker's own,
from their own take.

Files: `cut.py` (rough cut + word timings) -> `reel.json` (everything a member changes) -> `build.py` (writes
`index.html`, applies the grades) -> `measure_cover.py` (how much of each giant word the head covers).

---

## 1. The mode decision: 9:16 "soft cinema" (Mode A techniques, recomposed for vertical)

Nana's two best talking heads are landscape (Mode A, Cinema). Her vertical mode (Mode B) is built for
screen-demo build-alongs: a typed hook, screen cards over a blurred background, a "details below" end card.

The demo footage is a 9:16 talking head with no screens, tightly framed (crown y ~585, chin y ~1320-1400 on
1080x1920). So:

- **Not Mode B.** Without screens there is nothing for its cards, blur and icon end card to do; it would be the
  typed hook and a subtitle, which isn't what makes her reels feel like her.
- **Not a landscape crop.** A 16:9 frame cut out of a tight 9:16 take would be the face only, edge to edge, with no
  air for the giant words, and Instagram is the delivery target.
- **So: Mode A's techniques, recomposed for 9:16.** Her three-slot cream subtitles, giant butter stacks with a lilac
  payoff word behind the head, the slow pace, hard cuts only, a warm soft grade and a quiet bed. What changes for
  vertical: the "empty side of the frame" becomes the **air above the head** (y 168-548), and the three-slot
  subtitle line moves up into that same air (baseline y 480). Her rule that subtitles drop out while a stack is up
  means the two never meet. The slots span 840 px instead of 1616 px, so each line is laid out from its measured
  chunk widths.
- **Why the subtitles are not at the bottom:** in the demo the chin reached y ~1510. Measured frame by frame,
  a bottom line at y 1478 crossed the bottom of the chin at 5.2 s, 8.0 s and 10.9 s, and anything below ~1530 sits
  in Instagram's caption/username area. The head's highest point across the demo (from the cut-out matte) was
  y 548, so a line at 445-492 can never touch it, and it sits inside Instagram's safe band (y 269-1248).

## 2. The cut (cut.py)

| | Number (demo values) | Why |
|---|---|---|
| Source | your take, 1080x1920, 30 fps, SDR (`SRC` in cut.py) | |
| Kept | 20.84-34.46 s, then 50.76-55.70 s (source; example values) | one continuous 13.62 s run, one jump cut at a sentence end |
| Length | 18.567 s (557 frames) | inside a 15-25 s brief |
| Speed | 1.0x | her pace is slow; energy comes from the words, not the cuts |
| Cuts | 1 plain hard cut at 13.62 s, no punch-in | she cuts at sentence ends and never zooms on a jump cut |
| Cut points | in measured silence (20 ms RMS below -45 dBFS) | whisper's segment starts can run ~0.2 s early (demo: first word really started 20.92, whisper said 20.68); fix them in `ONSET_FIX` |
| Edit fades | 12 ms audio fade at each edit | no click |
| Word timings | mlx_whisper `whisper-large-v3-turbo`, word timestamps, re-mapped to the cut clock (`assets/words-cut.json`; command in cut.py) | whisper.cpp drifted up to 1 s on the demo take |
| Voice | two-pass linear loudnorm to -14.2 LUFS target, TP -1.5; demo measured **-14.0 LUFS, peak -1.8 dBFS** | voice -14 LUFS |

## 3. Palette (only these: the look's own colours, sampled from her reels)

| Token | Hex | Used for here |
|---|---|---|
| butter | `#F8F49C` | stack connector lines; most hero words |
| lilac | `#E4C8EC` | the payoff word (in the demo: the opening stack's last word and the closing stack's last word) |
| subtitle cream | `#FCF4AC` | every subtitle chunk |
| white | `#FCF8FC` | a connector line on a darker stack (stack 2 in the demo) |

Never more than two colours in a stack. No stroke, box, pill, gradient or drop shadow on any text.

## 4. Type (Inter Tight, Google Font, variable file in `assets/fonts/`)

| Element | Size / weight / tracking / leading | Colour | Where (1080x1920) |
|---|---|---|---|
| Stack connector line | 76 px / 700 / -3% / 0.86 | butter or white | stack box x 90-990, left- or right-aligned, staggered |
| Stack hero word | up to 236 px, fitted to 900 px wide / 800 / -5% / 0.86 | butter, payoff word lilac | centred, or left when the payoff word stands alone; baseline y 718 / 700 / 695 (lower part behind the crown); closing payoff 540, fully clear |
| Subtitle chunk | 48 px / 400 / -2% / lowercase, no full stops or commas | cream | baseline y 480 (the air above the head; the demo's highest point was y 548) |

Hero sizes: 236 px cap, fitted to 900 px wide (a 9-letter word came out 235 px; 4-8 letter words 236 px).

### Subtitle slots
Her landscape slots are fixed points (x 144 / 960 / 1760 on 1920). On 1080 the chunks are wide compared with the
line, so each line is laid out from its measured widths: chunk 1 starts at x 120, chunk 3 ends at x 960
(clear of the Reels action rail), chunk 2 sits centred on x 540 unless that crowds a neighbour (min gap 40 px),
then it centres in the free space. Lines are at most 840 px. In the demo, four lines were hand-set in `reel.json`
(`subtitle_lines`), coming on at 3.733, 5.467, 6.533 and 9.067 s, with 2, 1, 3 and 3 chunks.

`build.py` also has an automatic chunker (breaks at sentence ends, pauses of 0.15 s / 0.40 s, stacks, shot cuts and
width). It works but splits worse (it can leave "on the" / "daily" apart), so a member's version should have Claude
hand-set the lines.

## 5. Motion and timing

- **Everything hard-cuts.** Each giant word appears in one frame on its spoken word (`tl.set`, frame-floored so
  light lands before sound). Each subtitle chunk is a clip that is simply on or off. No fades, scale, blur, slide,
  typewriter, whoosh, transition or camera move anywhere.
- **Frame 0 carries text:** a first word spoken within 3 frames (demo: 0.08 s) is on from frame 0.
- **Stacks (demo):**

| Stack | On / off (s) | Lines | Hold after last word |
|---|---|---|---|
| 1, opening | 0.000 / 3.733 | connector (left) / connector (right) / **payoff** in lilac (left) | 0.79 s (held to a named later word) |
| 2 | 11.033 / 13.633 | connector (left, white) / hero | 1.26 s, off at the shot change |
| 3 | 13.633 / 16.300 | connector (right) / connector (left) / hero (all butter) | 0.78 s (held to a named later word) |
| 4, closing | 16.300 / 18.567 | connector (left) / **payoff** in lilac (centred, above the head) | 1.23 s, to the end |

- Her rule "subtitles drop out while a stack is up" means the subtitle stream skips words spoken during a stack's
  hold (two single words in the demo). Both are heard. Every other spoken word is on screen.
- Subtitle lines clear together on the next line's first word, a stack, the shot change, or 0.6 s after their last
  word.
- **The ending:** her own reels end on the last spoken line as subtitles. In the demo the last line is a giant stack
  instead, because the speaker leans into the lens for it and the jaw fills the bottom of the frame. It holds to the
  end, 2.27 s. No end card, no comment-keyword plate.

## 6. Giant words behind the head

Layer order: graded background plate (z1) -> stacks (z2) -> graded person cut-out (z3,
`hyperframes remove-background`, `assets/cutout.webm`, VP9 alpha) -> subtitles (z4, never over the speaker).
In the demo the shot change is at 13.62 s on the cut clock; the new shot's first frame is 13.633 s, so a stack ending at
the cut is on until 13.633 and the next one opens on 13.633 (its first word is spoken at 13.70): no empty frame at the cut.
Coverage target 30-55% of each hero word's pixels hidden by the head, measured by `measure_cover.py`
(snapshot with and without the cut-out, count hero-coloured pixels in the hero band). Demo results:

| Stack | Hero word | Baseline y | Covered (just after it lands / 0.4 s later / 0.15 s before the stack ends) |
|---|---|---|---|
| 1 | payoff (lilac, own line, left) | 718 | 31% / 31% / 33% |
| 2 | hero | 700 | 32% / 35% / 37% |
| 3 | hero | 695 | 33% / 35% / 39% |
| 4 | payoff (lilac, centred, fully clear of the head) | 540 | 0% by design (matte check: the head's highest point in 16.3-18.57 s was y 556; the word ends at y 545) |

How it was tuned: hero baseline 650 measured 13-17% (words float); 690 gave 25-33%. A per-line number can hide
where the cover falls: with a two-word payoff line centred, the line read 34-52% but the lilac payoff word itself was
mostly behind the head (the head sat right of centre). So each payoff word got its own left-aligned hero line, and
`measure_cover.py` reports the lilac word on its own. For the closing word even that failed: the speaker leans left
into the lens at the end (the head's edge reaches x ~360), so tucked behind the head the word lost its last letter.
The rule is 30-55% covered *at most*, and her style allows giant words fully in the empty air, so the closing payoff
sits fully clear above the head. The opening payoff keeps its last letter tucked behind the hair: that is her own
"bigge(st)" move, and it reads. Band: baseline-200 to baseline+60 px. The face is never under text: stacks sit above
the eyebrows; only hair and crown pass in front.

## 7. Grade (both through `hyperframes media-treatment`, never CSS)

Her rooms read as a neutral greige room with warm light and a lit face. The demo room was a bright window
(luma above the head: mean 160, 90th percentile 206-211), which butter-on-light can't survive (about 2:1 contrast).
So the grade is split with the person cut-out, like a power window:

| Layer | Grade (`grades/*.json`) | Demo result |
|---|---|---|
| Background plate (`#a-roll`) | exposure -0.70, highlights -0.60, whites -0.35, contrast -0.10, temperature +0.14, tint +0.03, shadows +0.04, blacks +0.05, saturation -0.25 | above the head: luma mean 94-104, 90th percentile 115-118 (her greige wall ~106); butter now 4.9-5.3:1 contrast, lilac 3.7-3.9:1, white 5.3-5.7:1 (vs ~2:1 before) |
| Person (`#cutout`) | temperature +0.08, tint +0.02, contrast -0.04, highlights -0.12, shadows +0.08, blacks +0.04, saturation -0.05 | warm natural skin, inside the Natural Portrait ranges |

Check at 3x zoom: no halo at the hair line; in the demo the cheek edge showed a faint light rim that read as rim light.
Choose with `hyperframes grade-compare` if the room is different.

No vignette, no grain (her vignette is 0). The demo source already rolled highlights off like hers (98th percentile
luma 219-222 vs her 194-221).

## 8. Sound

| Thing | Number |
|---|---|
| Voice | -14.0 LUFS integrated (cut.py) |
| Bed | a soft instrumental you hold the rights to (demo: mellow rhodes with vinyl texture, 80 BPM, 3 s bars), entering on a downbeat (`enter_at`, demo 6.805 s into the track). Not shipped: put your file at `bed.src`, or leave it out and add music in the Edits window yourself (library music goes silent in Claude exports). No file = no bed, the build carries on |
| Bed level | measured over the used stretch, then set 14 dB under the voice (target 12-16 dB; demo: -13.0 LUFS bed -> volume 0.1778) |
| Fades | bed in 0.25 s, out 1.2 s |
| SFX | none (she uses none) |
| Demo rendered mix | **-13.9 LUFS integrated, true peak -1.2 dBTP**, LRA 1.0 LU, no clipping. Voice nulled out of the render: residual bed -28.0 LUFS, i.e. **14.0 dB under the voice** |

## 9. How a member's version differs

- **Their footage, their words, their music.** Claude runs `cut.py` on their take (new KEEP list from their pauses),
  transcribes it with mlx_whisper, makes the cut-out, and writes their `reel.json`: which 2-3 phrases go giant,
  which one word goes lilac, and the subtitle line breaks. `build.py` does the rest unchanged.
- **Space above the head decides the stack position.** If they film with more headroom, the stacks move up
  (`baseline_y`) and still need to measure 30-55% covered. If their head fills the frame top, stacks go small or
  sit beside the head instead.
- **Bright room?** Keep the split grade (darker background plate). A dark, warm room (closer to hers) can drop
  the background grade to the same as the person grade.
- **Members who film landscape (16:9 or 4:3):** use her real Mode A: 1920x1080, three fixed subtitle slots
  (left x 144, centre 960, right edge 1760, baseline y 962, 44-46 px), giant stacks in the empty side of the frame
  next to the head (200-280 px hero), top of stack y 150-400. `build.py` needs W/H and the slot numbers changed
  (a landscape config is not built yet). Post it as a 16:9 reel, as she does.
- **In Edits:** put `renders/nana-del-rey-overlays.mov` (ProRes 4444 with alpha, 1080x1920, 30 fps, no audio:
  subtitles + stacks + the graded cut-out, the cut-out only while a stack is up; demo 558 frames) on the overlay track over
  the same rough cut (`assets/cut.mp4`), aligned at 0. Grade the base clip warm and darker in the room (her starting
  grade, plus lower highlights) or butter on a bright window loses contrast. Add the bed with ducking about
  14 dB under. Edits' captions can't do the three-slot line, so the overlay carries the subtitles. Alternative: drop
  the cut-out and use Edits' own subject cut-out above the overlay. Caveat: the overlay's cut-out carries this
  build's person grade, so if the Edits base is graded differently the head shifts colour while a stack is up.

## 10. Rebuild order

```bash
python3 cut.py                       # assets/cut.mp4 + assets/words-cut.json (needs work/words-source.json, see cut.py)
npx --yes hyperframes@0.9.83 remove-background assets/cut.mp4 -o assets/cutout.webm --quality best
$PY build.py            # index.html + both grades
$PY measure_cover.py    # coverage of each hero word (rebuilds index.html at the end)
npx --yes hyperframes@0.9.83 check --json
npx --yes hyperframes@0.9.83 render --workers 2 --quality delivery --format mp4 -o renders/nana-del-rey.mp4
$PY build.py --overlay && npx --yes hyperframes@0.9.83 render --workers 2 --format mov -o renders/nana-del-rey-overlays.mov && $PY build.py
```
`renders/` and `work/` are not shipped: you render your own.

## 11. Banned here

Text over the face; any text animation (pop, slide, fade, blur, typewriter); strokes, boxes, shadows; more than
two colours in a stack; karaoke highlighting; capitals in subtitles; sound effects; transitions or punch-ins;
end card or comment-keyword plate; her footage, names, keywords or catchphrases.
