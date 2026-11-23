# SPEC: "Inspired by Hormozi: 2026" (solo desk, format B)

> **Using this template:** the skill copies this folder (and `_shared/` next to it) into its build folder (see `USE.md`), adds the
> fonts below to `assets/fonts/`, puts your SDR take in `~/Movies/Edits-inbox/`, fills `config.json`, then runs
> `$PY transcribe.py` and `$PY cut.py`, then
> `python3 build.py --overlay` (and `python3 build.py` for the full preview), checks with
> `npx --yes hyperframes@0.9.83 check --json`, and renders the overlay `.mov` for Edits
> (`npx --yes hyperframes@0.9.83 render overlay --format mov`). Needs HyperFrames (Node 22+) and the skill's Python venv.
> Fonts: Poppins 400 + 700 ([Google Fonts](https://fonts.google.com/specimen/Poppins)), Montserrat Black Italic 900i
> ([Google Fonts](https://fonts.google.com/specimen/Montserrat)), Inter 400-800
> ([Google Fonts](https://fonts.google.com/specimen/Inter)), all SIL Open Font Licence. All three are bundled with
> HyperFrames, so nothing has to go in `assets/fonts/` for this look.

His current look, measured on 5 public @hormozi reels (links in `card.json`): a red label tag from frame 0 to ~4.5 s,
small sentence-case captions that hard-swap with one heavier word, a word-tight cut, one practical prop graphic that
changes on the spoken beat, one hard punch-in near the end, no transitions, ends dead on the line. Editing TECHNIQUES
only: none of his footage, logos, tag wording, keywords or catchphrases.

## Source and cut
- Footage: one talking-head take, 1080x1920, 30 fps, SDR. The demo take was a 12 s close-up with a spoken list
  ("number two ... ") cut from 3 keep ranges (`config.json` `keep`).
- The demo removed a 0.36 s pause and a 0.22 s pause. A take with almost no gaps keeps them: nothing under 0.15 s is
  trimmed (micro-trims read as stutters).
- Speed 1.15x. The demo came out at 12.41 s, 43 words, 208 wpm (his desk reel measured 276 wpm; stop short of
  chipmunking the voice).
- Voice two-pass loudnorm to -14 LUFS / -1.5 dBTP in `cut.py`.
- Word timing: mlx_whisper large-v3-turbo word stamps (`transcribe.py`), starts snapped to the first 10 ms window over
  -28 dBFS (`cut.py`); any onset whisper still gets early goes in `config.json` `time_fixes`.

## Palette
| Token | Hex | Used for | Source |
|---|---|---|---|
| hook-red | `#FF0000` | label tag box | measured on his reels |
| paper | `#FFFFFF` | tag text, captions, card | measured |
| shadow | `rgba(0,0,0,.5)` | caption shadow 0 3 px 9 px | est. |
| meter-violet | `#721CFB` | meter fill | measured |
| meter-track | `#E6E6EA` | meter track | est. |
| ink | `#111114` / `#3A3A42` | card text / sub-lines | ours |
| redaction | `#0B0B0D` | the bars that hide unsaid points | ours |

## Type (1080x1920)
| Element | Font | Size / weight | Where / when |
|---|---|---|---|
| Label tag | Montserrat | 900 italic, 53 px, caps, white on red, padding 16/26, radius 10 | centred, top y 262 (box ~262-347, ~660 px wide in the demo), above the head (started ~570 in the demo). Frame 0 to 4.5 s, hard on/off |
| Captions | Poppins | 72 px, 400, one 700 emphasis word in about half the captions (9 of 17 in the demo) | ONE line, centred, centre y 1478, 2-3 words, sentence case, no full stops/commas, hard swap (on at first word, off when the next starts) |
| Card title | Inter | 800, 29 px | card x 222, y 1548, w 680, white, radius 6, shadow 0 18 44 .45 |
| Card rows | Inter | 500 28 px (numbered), 400 28 px #3A3A42 (sub-lines, indent 44 px), line 1.27 | inside the card |
| Meter label | Poppins | 700, 28 px, white + shadow | above the meter |

Caption text = the speaker's exact words. Words in `config.json` `keep_case` (AI, I, acronyms) keep capitals;
everything else lower case.

## The prop (the real list in the take)
The demo take was a list ("Here's why. One ... Number two ... Number three ..."), so the prop is that list as a
"redacted document", in the speaker's own words:
- Title = the claim at the top of the take, condensed.
- Point 1 shown (covered before the clip starts).
- Point 2 clears on its spoken word; each sub-line clears on its own word (`reveal_word`).
- Point 3 stays redacted (`hidden: true`): it's said after the clip, so it's the reason to keep watching.
- Bars wipe off left to right in 0.15 s `power2.in` (reads as a hard change at his 4 fps cadence, but doesn't flash).
- Meter: 40 x 250 px track at x 140, beside the card. Fill 33% at frame 0, steps to 67% on its word (0.3 s
  `power2.out`), label hard-swaps "1/3" -> "2/3" 0.15 s later. Fraction, not %, because the steps are list points.

## Camera
Locked off. ONE hard punch-in to 1.15 on `punch_word` (9.20 s in the demo), the same frame the prop leaves.
Origin x 540, y 1420 (the chin) so the face grows up and the captions stay clear. No other zooms, no transitions.

## Sound
Voice only, -14 LUFS. No music (his desk reel may have a bed ~20 dB under the voice, but it couldn't be confirmed,
so none). No sound effects (none measured in his reels). If you want a bed anyway: add it in the Edits window yourself
(library music goes silent in Claude exports) or use your own file.

## Grade (media-treatment, `grade-attr.txt`)
High-key and clean, like his white desk set: exposure +0.08, highlights +0.10, contrast +0.03, saturation -0.08.

## End
Stops dead on the last word (0.95 s after it starts in the demo, no outro, no end card). CTA: none unless the take has a
spoken CTA for a real comment-keyword funnel; we never invent a keyword. `config.json` `cta`
({"line1": "COMMENT \"WORD\"", "line2": "..."}) switches on his native-text CTA block (black box line 1, y 1240) for
the last 5 s.

## Layout on a close-up (honest note)
His frame is a medium shot (head top ~360, captions at y ~940, prop on the desk below). A close-up take (head 570-1420,
like the demo) has a shirt where his desk is. So the same stack moves down: tag above the head, captions just
under the chin, the prop on the shirt where his sits on the desk. Captions and card sit below the 1330 px text band:
deliberate, marked `data-layout-allow-safe-zone`; the card's lower rows (1750-1856) sit where IG draws the caption
text, which is why the prop is texture-first (redacted bars) and leaves before the ending.

## Banned here
Caption pop-ins, bounce, karaoke colour sweeps, all-caps captions, more than one bold word, captions over the face,
transitions, zoom ramps, slow pushes, music under the voice, an end card, a tag after ~5 s, a second punch-in.

## How a member's version differs
- Swap `footage` in `config.json` and run `$PY transcribe.py` (word stamps in
  source seconds). Then swap `keep`, `speed` in `config.json`, run `$PY cut.py`,
  proofread the printed words.
- Set `hook_tag` (3-4 word LABEL in their words, not a sentence), `caption_groups` ([first, last, emphasis index]),
  the `card` (title + rows with `reveal_word` indexes; `hidden: true` for a point they make later) and the `meter`
  (from/to fill and labels). The prop only belongs on a take that IS a list or ladder; otherwise delete `card` rows
  down to nothing and drop the meter, keeping tag + captions + punch-in.
- Desk framing (member filmed wider, white desk): set `caption_centre_y` ~940 and card `y` ~1010, as in his reels.
- `hook_colour` can become their loud brand colour; keep one loud box colour, white captions.
- Rebuild: `python3 build.py`, `npx --yes hyperframes@0.9.83 check --json`, snapshot,
  `npx --yes hyperframes@0.9.83 render --workers 2` (you render your own). Overlay for Edits: `python3 build.py --overlay`
  then `npx --yes hyperframes@0.9.83 render overlay --format mov`.
- In Edits natively: tag = text with red background; captions = white Poppins preset, no animation, y ~1480 (or
  ~940 on a desk shot); jump cuts by transcript; one scale keyframe 115% held. The meter and the redacted card need
  the overlay MOV.
