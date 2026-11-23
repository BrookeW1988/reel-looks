# SPEC: Pop-up proof

> **Using this template:** the skill copies this folder (and `_shared/` next to it) into its build folder (see `USE.md`), adds
> the fonts below to `assets/fonts/`, puts your SDR take in `~/Movies/Edits-inbox/`, fills `reel.json`, then runs
> `$PY cut.py` and `$PY build.py` (inside the folder),
> checks with `npx --yes hyperframes@0.9.83 check --json`, and renders the overlay `.mov` for Edits
> (`npx --yes hyperframes@0.9.83 render overlays --format mov -o renders/pop-up-proof-overlays.mov`). Needs HyperFrames
> (Node 22+) and the skill's Python venv. cut.py and build.py use `../_shared/reeltools.py`. Fonts: DM Mono Medium as
> `assets/fonts/DMMono-Medium.ttf` (https://fonts.google.com/specimen/DM+Mono, SIL Open Font Licence 1.1); Inter
> variable as `assets/fonts/Inter-Variable.ttf` (https://fonts.google.com/specimen/Inter, SIL Open Font Licence 1.1;
> rename the `Inter-VariableFont_opsz,wght.ttf` file from the download).

**The look in one line:** a pill hook, giant words that slam in behind your head, then your real proof pops up in
white cards while the camera shrinks back to make room, with chapter stamps and bold karaoke captions.

**Proof = yours, real, unchanged.** Each proof card is YOUR OWN screenshot (a client message, a sales dashboard, a
result you got), set in a white frame, with an optional short label and an optional stat circled. The skill asks you
for the screenshots. Never invent, retype or mock up proof. No screenshot = no card (build.py skips it).

**Footage:** the demo was a 15.37 s talking-head take (cut.py: 2 s dead air out, three slack pauses trimmed, 1.1x).
Keep the deliberate pauses that give a line its rhythm (on the demo, the beat between the two giant words).

**Cut-out (for words behind your head):** run `npx --yes hyperframes@0.9.83 remove-background assets/cut.mp4 -o
assets/cutout.webm` after cut.py (VP9 with alpha; slow on CPU, roughly 12 min for 27 s). Without it the giant words
sit over the footage instead of behind you.

## Palette (only these)
| Token | Hex | Used for |
|---|---|---|
| ink | `#0E0E10` | text on white, caption outline, page ground |
| paper | `#FFFFFF` | pill hook, proof cards, captions fill |
| highlighter | `#FFE45C` | the circle on a proof stat, active caption word, chapter number |
| label chip | `#138A4F` on `#E3F6EC` | the optional proof-card label only |
| scrim | `rgba(10,10,12,.45)` | behind proof cards |
| backdrop | radial `#26262E` -> `#121216` (55%) -> `#0B0B0D` | revealed when the camera shrinks |

## Type (1080x1920; every word inside y 168-1330)
| Element | Font | Size / weight / tracking | Where |
|---|---|---|---|
| Pill hook | Inter | 64 / 800 / -1.5% | centred pill, top y 210, radius 999, padding 18/40 |
| Sub-hook | DM Mono | 36 / 500 | white on ink 82%, radius 12, padding 8/18, top y 330, types on |
| Giant words (behind head) | Inter | 260 / 900 / -4%, caps, line-height 0.9 | line 1 top y 215, line 2 top y 410; 30-55% covered by your head |
| Chapter number | Inter | 150 / 900, 6 px ink stroke | `#FFE45C`, x 72, top y 180 |
| Chapter label | Inter | 54 / 800 | ink on white pill (padding 16/28, radius 22), 22 px beside the number |
| Proof card | your screenshot | card x 90, w 900, top 190, radius 36, padding 40/44/44, shadow `0 40px 90px rgba(0,0,0,.45)` + `0 4px 12px rgba(0,0,0,.2)`; screenshot full width, max 760 px tall, radius 20 | |
| Card label chip | Inter | 28 / 700, padding 12/18, radius 999 | top of the card, 26 px above the screenshot |
| Card stat | Inter | 112 / 900 / -3% (small word after it 52 / 800, `#6B6B70`) | under the screenshot, 26 px gap; circle 12 px `#FFE45C` stroke, 34 px outside the stat each side, 175 px tall |
| Captions | Inter | 66 / 800 / -1%, white + 8 px ink stroke + `0 6px 18px rgba(0,0,0,.45)` | top y 1470, side padding 70; 3 words a group; spoken word `#FFE45C` |

## Motion (eases by role; times are offsets from the spoken phrases in reel.json)
- Pill hook: fully set on frame 0 (= thumbnail), settles scale 1.06 -> 1, 0.35 s expo.out.
- Sub-hook: types on from 0.45 s, 0.8 s, steps(28). Hook + sub blur out (8 px, 0.16 s power2.in) 0.2 s before `hook.until`.
- Giant words: each slams in on its spoken word, scale 1.3 -> 1, blur 12 -> 0, 0.2 s expo.out; camera punch 1.0 -> 1.14
  hard on the first; both blur out 0.18 s at `big_words.until`; camera back to 1.0 on the same frame.
- Proof cards alternate two styles. For each card the camera shrinks first, from 0.1 s before the card's `from`
  phrase: scale 0.84, y +154, radius 48, shadow `0 40px 100px rgba(0,0,0,.6)`.
  - Style A (cards 1, 3 ...): camera move 0.5 s power2.inOut; card in 0.10 s after `from`: rises from y +460, rotate
    -7 -> -2, blur 14 -> 0, back.out(1.3) 0.6 s. Out 0.19 s after `until` as a whip down (y +900, rotate 4, blur 16,
    0.3 s power3.in); camera back 0.03 s later (0.3 s power3.inOut).
  - Style B (cards 2, 4 ...): camera move 0.45 s power2.inOut; card in 0.03 s before `from`: whips in from the right
    (x +1100 -> 0, rotate 6 -> 1.5, blur 16 -> 0, 0.45 s power4.out). Out 0.31 s before `until`, whip left
    (x -1100, rotate -4, blur 16, 0.25 s power3.in); camera back 0.03 s later (0.28 s power3.in), landing on `until`.
  - Stat (optional): a whole number counts up from 0 over 0.7 s power2.out, 0.2 s after the card comes in; the
    circle draws round it 0.85 s after the card comes in, 0.5 s power2.inOut.
- Chapter: number slams (scale 1.4 -> 1, blur 10 -> 0, 0.2 s expo.out), label wipes in 0.08 s later (clip-path,
  0.3 s power4.out); camera punch 1.12 hard on the number. Out (blur 8, 0.15 s) 0.2 s before `until`; the camera
  goes back to 1.0 then, unless a proof card's camera move starts there (it then shrinks from the punch).
- Punches (optional): hard sets on big lines, 1.08-1.15, back to 1.0 on `until`. Hard cuts, never slow creeping zooms.
  (The demo ended on 1.15 on a big line, 1.0 on the next word, 1.08 on the last big word.)
- Captions: groups of up to 3 words, break after punctuation; each group fades in 0.12 s (blur 6 -> 0, power3.out)
  and out 0.1 s; the spoken word turns `#FFE45C` (keywords scale 1.08). Off while the giant words are up.

## Sound (tactile, peak 1 frame after the picture; voice -14 LUFS, effects 6-10 dB under)
SFX aren't shipped. Either drop your own files into assets/sfx/ with these names, or skip them in the overlay and add
them natively in Edits with searchSoundEffects + addSoundEffect. (build.py skips any file that isn't there.)
| Moment | Sound (file name build.py looks for) | Volume / length |
|---|---|---|
| Sub-hook typing | keyboard typing, `typing_2s.mp3` (Edits: searchSoundEffects "typing"), cut to 0.9 s | 1.00 / 0.90 s |
| Giant word 1 | soft thud, `soft-thud.mp3` (Edits: searchSoundEffects "thud") | 0.55 / 1.10 s |
| Giant word 2 | deep boom, `boom-impact-2.mp3` (Edits: searchSoundEffects "boom impact"); a different hit, not the same one twice | 0.20 / 1.00 s |
| Card A in / out | soft whoosh in, `soft-whoosh-1.mp3` (Edits: "whoosh"); short whoosh out, `whoosh1_2.mp3` (Edits: "quick whoosh"), 0.28 s after the exit starts | 0.28 / 1.10 s; 0.80 / 0.48 s |
| Circle draws | marker pen, `marker.mp3` (Edits: searchSoundEffects "marker") | 1.90 / 0.50 s |
| Chapter number | pop, `pop.mp3` (Edits: searchSoundEffects "pop") | 1.80 / 0.50 s |
| Card B in / out | paper slide in, `paper-slide-1.mp3` (Edits: "paper slide"); swoosh out, `swoosh-transition-1.mp3` (Edits: "swoosh transition"), 0.22 s after the exit starts | 1.05 / 0.58 s; 0.50 / 0.88 s |
No music (style rule: voice-led). If you want some anyway, add it in the Edits window yourself (library music goes
silent in Claude exports) or use your own file.

## Grade
Clean and bright: exposure +0.05, contrast +0.08, saturation +0.05, temperature +0.03, vignette 0.12, grain 0.06
(`grade-attr.txt`, made with `hyperframes media-treatment`; never CSS filters on footage).

## Banned here
Fade-and-slide-up on everything; floating/breathing loops; slow creeping zoom; the same whoosh twice; text over your
face; any proof that isn't your own real screenshot, unchanged.

## How a member's version differs
- `reel.json`: your take and keep spans, your hook and sub-line, your giant words (or none), your proof cards (your
  screenshots in `assets/cards/`, an optional label, an optional stat exactly as it appears in the screenshot),
  chapters, punches and keywords, all as spoken phrases.
- Your words: `cut.py` transcribes the finished cut; proofread the printed line and add spellings to `word_fixes`.
- In Edits: use `renders/pop-up-proof-overlays.mov` over your take. The camera moves (shrink, punches) stay out of the
  overlay: keyframe them natively in Edits so the graphics line up with the untouched footage.
