# SPEC: "Inspired by Hormozi: classic"

> **Using this template:** the skill copies this folder (and `_shared/` next to it) into its build folder (see `USE.md`), adds the
> fonts below to `assets/fonts/`, puts your SDR take in `~/Movies/Edits-inbox/`, fills `config.json`, then runs
> `$PY transcribe.py` and `$PY cut.py`, then
> `python3 build.py --overlay` (and `python3 build.py` for the full preview), checks with
> `npx --yes hyperframes@0.9.83 check --json`, and renders the overlay `.mov` for Edits
> (`npx --yes hyperframes@0.9.83 render overlay --format mov`). Needs HyperFrames (Node 22+) and the skill's Python venv.
> Fonts: Montserrat Black 900 ([Google Fonts](https://fonts.google.com/specimen/Montserrat), SIL Open Font Licence).
> It's bundled with HyperFrames, so nothing has to go in `assets/fonts/` for this look.

The famous 2022-23 short-form look: big bold all-caps captions, the spoken word lit up, a cut or punch-in every
1-3 s, zero dead air, no music. Editing TECHNIQUES only: no Hormozi footage, logos, catchphrases, comment keywords
or brand assets. (His 2026 reels look different: see `../hormozi-2026/`.)
Reference: [@hormozi on Instagram](https://www.instagram.com/hormozi/).

Sources for the numbers: public breakdowns of the caption recipe, checked 23/11/2026: Montserrat Black 900, all caps,
~85 px, thick black outline, spoken word in yellow (green as the alternative), word-synced timing
([Submagic](https://www.submagic.co/blog/how-to-make-alex-hormozi-captions),
[Choppity](https://www.choppity.com/tools/recreate-video-editing-style/alex-hormozi/),
[Fluxnote](https://fluxnote.io/guides/how-to-make-alex-hormozi-style-captions)). None of these is an official
Hormozi source: the values are approximations everyone copies, not measurements of his files.

## Source and cut
- Footage: one talking-head take, 1080x1920, 30 fps, SDR. The demo take was a 16 s close-up cut from 3 keep ranges.
- Keep ranges (source s) live in `config.json` `keep`. Cut every breath and pause (the demo removed a 0.48 s breath,
  a 0.64 s pause and a 0.37 s pause). Words never clipped: cut points sit in measured dips under -36 dBFS, with 12 ms
  audio fades.
- Speed 1.2x (style range 1.2-1.3). The demo came out at 15.98 s, 42 words, 158 wpm.
- Voice two-pass loudnorm to -14 LUFS / -1.5 dBTP in `cut.py`.
- Word timing: mlx_whisper large-v3-turbo word stamps (`transcribe.py`), each start snapped to the first 10 ms window
  over -28 dBFS (`cut.py`). Any onset whisper still gets early (it was 0.5 s early on two words in the demo) goes in
  `config.json` `time_fixes`.

## Palette (only these)
| Token | Hex | Used for |
|---|---|---|
| paper | `#FFFFFF` | caption and hook fill |
| ink | `#000000` | 10 px outline, shadow `rgba(0,0,0,.55)` |
| highlight | `#FFE600` | the word being spoken; the accent word in the hook |

## Type (1080x1920)
| Element | Font | Size / weight / tracking | Where / when |
|---|---|---|---|
| Hook | Montserrat | 900, 72 px, line-height 1.08, +1%, caps, 10 px black stroke (paint-order stroke), shadow 0 6 16 .55 | 2 lines centred, top y 300 (above the head, which started ~570 in the demo). On at frame 0, hard off at 2.0 s |
| Hook accent | same | same, `#FFE600` | the one `hook_accent_word` |
| Captions | Montserrat | 900, 84 px, line-height 1.08, +1%, caps; extra 0.13 em each side of a word | one line, centred, block top y 1452, max width 920 px. A long group fits down to 72 px (width estimate 0.77 em a character) rather than wrap |
| Hero word | Montserrat | 900, 132 px | the one `hero_words` word, its own group, with the 130% punch-in |

Caption text: the speaker's exact words, upper case, full stops and commas removed. 20 groups of 1-3 words in the demo
(`config.json` `caption_groups`), each on hard at its first word and off when the next group starts.

## Motion
| Thing | Numbers |
|---|---|
| Active word | turns `#FFE600` on its start frame; pops scale 1.10 -> 1.00 in 0.10 s `power2.out`; back to white when the next word starts (last word of a group stays lit) |
| Keywords (`config.json` `keywords`, 7 in the demo) | harder pop 1.18 -> 1.00 in 0.10 s; nothing holds scaled (held scale pushes words into each other) |
| Punch-ins | hard `gsap.set` (no ramps): 1.00 / 1.18 alternate on phrase starts, 1.30 on the hero word; 13 states in 16 s in the demo (a change every 0.6-2.3 s). The first punch-in waits for the hook to leave (2.33 s in the demo) so the face never grows into it. A change within 0.1 s of a jump cut snaps onto the cut so the zoom hides the jump |
| Zoom origin | x 540, y 1400 = the chin, so every punch-in grows the face UP and the captions under the chin stay clear |
| Hook / captions | no entrances, no exits: hard on, hard off |

## Sound
- Voice only, -14 LUFS. No music (style rule).
- ONE effect: a soft whoosh, tactile air, no synth (Edits: searchSoundEffects "whoosh"), on the 130% punch-in at the
  hero word. It starts at hero word + 1 frame - the file's measured peak (0.472 s into the demo's file, so it started
  at 11.244 s); volume 0.75, 0.10 s fade-out, 6-10 dB under the voice.
- SFX aren't shipped. Either drop your own files into assets/sfx/ with these names, or skip them in the overlay and add
  them natively in Edits with searchSoundEffects + addSoundEffect. `config.json` `sfx` expects `whoosh.mp3`; build.py
  skips it if the file isn't there.

## Grade (media-treatment, `grade-attr.txt`)
contrast +0.10, saturation -0.05, temperature -0.03 (slightly cool), vignette 0.08. Nothing else.

## Layout on a close-up (honest note)
The house spec puts captions at y ~1150 "just under the chin". On a close-up (head 570-1420, like the demo take) y 1150
is the mouth. So captions sit under the real chin instead (top 1452, on the shirt), and punch-ins scale around the
chin. That puts captions below the 1330 px "text band" of the vertical guide: deliberate, marked
`data-layout-allow-safe-zone`. On IG they clear the caption/handle block (which starts ~1600).

## Banned here
Music; more than one highlight colour; captions over the face; slow pushes or zoom ramps; the same whoosh on every
cut (there is exactly one); GIFs, cards, emoji; boxed captions; captions in sentence case.

## How a member's version differs
- Swap `footage` in `config.json` and run `$PY transcribe.py` (word stamps in
  source seconds). Then swap `keep` ranges and `speed` in `config.json`, run `$PY cut.py`.
  Read the printed word list, proofread it (`fixes` for wrong words, `time_fixes` for an onset whisper got early), then
  set `caption_groups` (word index ranges, 1-3 words, break at commas and pauses), `keywords`, `hero_words`,
  `zoom_plan` ([word index, scale], alternate 1.0/1.18, ONE 1.30) and the `hook` lines from THEIR words.
- `caption_top` and `zoom_origin_y` follow their chin: a member filmed wider (chin around y 1150) uses caption_top
  ~1180 and the classic position; a close-up goes under the chin.
- Highlight colour can become their brand accent (one colour only); yellow is the classic.
- Background: the look wants a plain neutral or dark wall. Busy rooms fight the white captions.
- Rebuild: `python3 build.py`, `npx --yes hyperframes@0.9.83 check --json`, `npx --yes hyperframes@0.9.83 snapshot --at ...`,
  then `npx --yes hyperframes@0.9.83 render --workers 2 -o renders/<name>.mp4` (you render your own). Overlay for Edits:
  `python3 build.py --overlay` and `npx --yes hyperframes@0.9.83 render overlay --format mov`.
- Doing it natively in Edits instead: auto captions with a per-word highlight preset (Montserrat Black caps, white,
  outline, yellow word), jump cut every pause, scale keyframes 100/118/130 held (no ramps). The rendered overlay MOV
  only adds the exact pop and hook if their preset can't match.
