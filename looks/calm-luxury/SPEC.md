# SPEC: Calm luxury

> **Using this template:** the skill copies this folder (and `_shared/` next to it) into its build folder (see `USE.md`), adds the
> fonts below to `assets/fonts/`, puts your SDR take in `~/Movies/Edits-inbox/`, fills `reel.json` (and SRC/KEEP/REFRAME
> in `cut.py`), then runs `python3 cut.py` and `python3 build.py` (and `python3 build.py --overlay` for the overlay),
> checks with `npx --yes hyperframes@0.9.83 check --json`, and renders the overlay `.mov` for Edits. Needs HyperFrames
> (Node 22+) and the skill's Python venv (for the mlx_whisper word timings, see cut.py). Fonts: Newsreader, variable
> file with the `opsz` axis, `assets/fonts/Newsreader-opsz-wght.ttf` (https://fonts.google.com/specimen/Newsreader,
> SIL Open Font Licence). This is the look's own font, not a brand font.

**Inspired by:** Jess Bergeron, [@jkb.journal](https://www.instagram.com/jkb.journal/) (reels listed in `card.json`).
We copy editing TECHNIQUES only: none of her footage, wording, product, logos or styling.

**The look in one line:** the camera never moves, only the speaker does. One small white serif line that swaps on the phrase,
hard cuts, a warm natural grade, no zooms, no text animation, no sound effects, and it loops.

**Honest note:** Jess's reels are faceless hands-at-work footage. The demo had no hands or process footage, so it is
the *talking-head extension* (our addition): the locked-off talking segment is the "process hold", and there are no
detail bursts because there is nothing to cut away to. It is the calm look applied to a face, not a recreation of
Jess's reels. If you have hands or product footage, use version 2 under "How a member's version differs".

---

## Choosing the take

| A take works if | Why |
|---|---|
| Phone on a stand (locked off), soft window light from one side or behind | the look is stillness and window light |
| Dark top (a dark ground for white text) | white text vanishes on bright walls or a busy printed top (a "Never do") |
| Calm register, one thought, no spoken CTA | the calm look puts the CTA in the IG caption, never on screen; hype lines are the opposite register |
| Already SDR (convert iPhone HDR first) | the grade below assumes SDR |

**Script:** the speaker's own words at their natural speed (the demo: 50 words, ~170 words a minute, unchanged speed),
one thought that can loop back into its own opening line.

Transcript check: word times from mlx_whisper large-v3-turbo (`word_timestamps=True`), edges snapped to a 40 ms and
15 ms RMS envelope. Where models disagree on a word, listen to it before captioning.

## Rough cut (`cut.py`)

| What | Number | Why |
|---|---|---|
| Range A (demo, example values) | source 20.867-34.467 s (frames 626-1034), 13.600 s | one unbroken "process hold" (Jess: 8-15 s); it opens inside a silence (demo 20.61-20.93), so the voice starts on frame 1 |
| Range B (demo, example values) | source 51.000-55.133 s (frames 1530-1654), 4.133 s | the closing line. Starts in the dip after a dropped filler word; ends after the last word dies (-49 dB at 55.06) |
| Total | **17.733 s, 532 frames** at 30 fps (demo) | inside a 10-20 s brief |
| Speed | 1.0x | calm = stillness, not speed; the demo's 170 wpm already matched Jess's 162-172 |
| Hard cuts | 1 (at 13.600 s) | no jump cuts inside a sentence; no punch-in to hide the cut (banned) |
| Audio edge fades | 12 ms in/out at each edit | no clicks |
| Reframe | static crop, scale **1.12**, anchored bottom-centre (crop 964x1714 at x 58, y 206, Lanczos up to 1080x1920) | lifted the demo chin from y ~1400 to ~1338 so the caption line sits on the dark top, not the neck. Never animated, so not a zoom |

## Palette

### Frame (demo medians sampled from the graded render at 0.1, 4, 8, 12, 15 s; yours will differ)
| Token | Hex | Use |
|---|---|---|
| ground | `#140F09` | page background behind the footage (never visible; Jess's shadow-ink) |
| top | `#0F0B05` | the dark top (y 1650-1800): the ground every caption sits on |
| skin-warm | `#995F4C` | the warmed skin mid-tone (centre of face) |
| window | `#C3D0BE` | the blurred window top-centre, held below clipping |
| wall | `#6D6467` | the shaded wall at frame left |

### Text and overlay
| Token | Hex | Use |
|---|---|---|
| text | `#FFFFFF` | every word. 100% opacity. No shadow, no stroke, no box, no accent colour, ever |

## Type (1080x1920)

| Element | Font | Size / weight | Where |
|---|---|---|---|
| Caption line | Newsreader (variable, `opsz` 16), 400, roman | **51 px**, line box 60 px, sentence case, one line, no wrap | centred x 540; line centre **y 1480** (box y 1450-1510); the demo's widest line (32 characters) ~700 px |
| Hook title (off here) | Newsreader opsz 16, 400 | 60 px, leading 1.42 | centre y 700 (reel.json `title`, for hands footage) |

- Font file: `assets/fonts/Newsreader-opsz-wght.ttf` (Google Fonts, SIL Open Font Licence, free to ship to members).
- **One line, not Jess's 2-3-line chunks.** Why: on a face, a 2-line block needs ~60 px more height and would sit on the
  chin. One line also answers the brief's "one small white serif line". 10 lines of 3-6 words (≤ 32 characters), split at
  phrase boundaries.
- **Position vs platform UI:** HyperFrames flags y > 1248 as outside Instagram's clear band (`outside_safe_zone`,
  kept on purpose). Jess's own captions sit at y 1360-1510 on a 1.1M-view reel; ours end at y ~1510. Moving the line up
  would put it on the face, which is a hard rule. If a member's framing allows, raise `caption_centre_y` to ~1435.

## Motion: none

- Camera: locked. No zoom, punch-in, Ken Burns, shake or speed ramp. The static 1.12 reframe never changes.
- Text: hard on/off by clip window. No fade, slide, blur, typewriter or word highlight. The GSAP timeline is empty on purpose.
- Caption timing (`build.py`): line 1 is on screen at **frame 0** (the thumbnail). Each later line swaps on at its first
  word's start minus 0.05 s, snapped to the frame. A line next to a hard cut swaps **on** the cut (demo: cap8 moved
  13.533 to 13.600 s). A pause over 0.35 s between phrases blanks the screen until the next line (none in the demo).
- Demo line holds: 1.27-2.17 s (median 1.85 s). The last line held 2.10 s.

Demo caption windows (10 lines, on / off in seconds): 0.000/1.267, 1.267/3.300, 3.300/4.667, 4.667/6.467,
6.467/8.367, 8.367/9.733, 9.733/11.433, 11.433/13.600, 13.600/15.633 (first line after the hard cut), 15.633/17.733.

## The loop

The reel ends on its closing line and loops straight back to the opening line, so the words carry on as one thought.
The camera is locked, so the framing matches exactly at the loop. **The pose may not:** in the demo the last frame had
the eyes down and the first was looking at the lens, so the loop read as one more hard cut, not an invisible join. Jess's bookend (last shot = first shot) only fully works with object footage; see
the member notes below.

## Sound

| Element | Number |
|---|---|
| Voice | demo: **-14.1 LUFS integrated, -1.9 dBTP true peak, LRA 1.0 LU** (measured on the render; the source was already levelled, so cut.py makes no gain change: level yours to about -14 LUFS) |
| Music bed | **Optional, not shipped.** Add it in the Edits window yourself (library music goes silent in Claude exports) or use your own file in `reel.json` `music`. Spec: one soft instrumental (piano, acoustic, ambient) at 80-100 BPM, **18 dB under the voice** (`music` → volume 0.126), no fade-in (sound from frame 0), 0.6 s fade-out. A missing file is left out of the build |
| Sound effects | None (banned in this look) |

## Grade (via `hyperframes media-treatment`, stored in `grade-attr.txt`)

`exposure -0.04, contrast +0.03, highlights -0.02, shadows -0.02, whites +0.06, blacks 0, temperature +0.22,
tint -0.04, vibrance +0.04, saturation 0`. No vignette, no grain, no LUT (all banned as a style).

| Measure (luma 0-255, ffmpeg frames, 10 samples) | Demo ungraded | Demo graded | Jess (measured) |
|---|---|---|---|
| Mean luma | 96.0 | **94.1** | 83-106 |
| Blacks (1st percentile) | 9.2 | **4.4** | 4-8 |
| Highlights (99th percentile) | 218 | 219 | 228-233 |
| Contrast (luma std dev) | 56.5 | **57.8** | 55-58 |
| Warmth (mean R - B) | +16.2 | **+26.8** | +25 to +41 |
| Saturation (mean HSV) | 0.21 | **0.37** | 0.29-0.45 |
| Green vs avg(R, B) | -4.3 | -2.2 | 0 to +4 |

How it was tuned on the demo: temperature +0.14 with blacks -0.06 was short on warmth and crushed the blacks;
temperature +0.22 fixed the warmth but left green low; tint -0.04 with blacks 0 is final. Highlights stay a little under
Jess's because her window light is brighter than the demo room; pushing them would blow the window. Measure your own
footage against the Jess column, don't copy these numbers blind.

**Edits sliders that get close (estimate, not tested in Edits):** Warmth +10, Exposure -3, Tint toward green a touch,
everything else 0.

## Banned here

Zooms or punch-ins (including on the jump cut), any text animation, coloured or highlighted words, caps hooks, emoji,
stroke/shadow/box behind text, sound effects, music louder than -18 dB under the voice, vignette, grain, lifted blacks,
on-screen CTA or end card, a second font or second caption size, text on the face.

## What Edits can do natively vs the rendered overlay

**This look needs almost nothing rendered.** Edits can do all of it natively: hard cuts, a locked shot, the grade
sliders, white serif captions with an imported font (Newsreader), no background, hard on/off. The one thing Edits can't
promise is exact control: no line-height or letter-spacing, and auto-caption chunking chooses its own breaks.
`renders/calm-luxury-overlays.mov` (ProRes 4444 with alpha, captions only) is for members who want the exact one-line
phrasing and y 1480 placement: drop it on top of their own clip with addOverlay and switch Edits' auto captions off. It
only lines up with the cut it was built from; render your own from `build.py --overlay`.

## How a member's version differs

1. **A member talking to camera (like this demo):** film locked off at eye level, window at 45° to one side, dark top.
   Run `cut.py` with your `SRC`/`KEEP` (one long hold, cuts only in real pauses), put your proofread phrases in `reel.json`
   `lines`, check the caption line clears your chin at your framing (adjust `REFRAME` or `caption_centre_y`), grade by
   measuring against the table above, not by copying these numbers.
2. **A member WITH hands/process footage (the real Jess look):** this is the better version, and the template already
   takes it. `shots` becomes a list: one 8-15 s process hold (hands working, voice running), then detail bursts of
   0.6-1.9 s each (`"audio": false`), cut on the finished action. Put the voiceover in `voice` (or keep it on the hold
   shot), use Jess's caption placement (`caption_centre_y` ~1435, 2-3 line chunks of 8-14 words), and set `bookend`
   (`{"dur": 1.2}`) so the last shot repeats the opening hero shot and the loop is invisible.
3. **A music-only member reel (Jess's identity loop, 7-30 s):** set `lines` to `[]` with no `words`, set `title` to one
   2-3 line sentence ("I help [who] [do the thing]") held for the whole reel, add `music`, and use only hands shots of
   0.8-1.6 s, with the bookend on.

In every version any CTA goes in the Instagram caption, never on screen (a comment-keyword CTA only if you really
have that keyword funnel set up).

## Files

`cut.py` (rough cut + word remap + cut points) → `assets/cut.mp4`, `assets/words-cut.json`, `assets/cut-points.json`;
`reel.json` (everything a member changes) → `build.py` → `index.html`; `grade-attr.txt` (the grade);
`renders/calm-luxury.mp4`, `renders/calm-luxury-overlays.mov` (not shipped: you render your own).
