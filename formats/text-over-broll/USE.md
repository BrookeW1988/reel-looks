# How each skill uses Text over B-roll

Calm everyday footage, slowed and warm-graded, with one lowercase line written like a text to a friend.

**Format:** `text-over-broll` · gallery name "Text over B-roll" · a Wright Mode format.
Every number is in `SPEC.md`. The code is `cut.py` + `build.py` (HyperFrames). The member fills: CLIPS in cut.py + LINES in build.py.

What the member brings:
- 1-3 steady B-roll clips (no talking)

Editing-pack extras this format takes (GIFs, emojis, callouts, sounds from the member's own pack):
none: its SPEC bans them, so the look stays clean whatever is in the pack.

## Claude Video Editor route: a finished 9:16 MP4

The Video Editor does its own cut first (dead air, ums, retakes), then hands this template the member's own clips: this format isn't a single talking-head take, so Claude copies them into `assets/` and fills the config by hand from SPEC.md.

1. `run.py start <take> --format text-over-broll [--look <a look>]` then `run.py cut <edit folder>`
   (the editor's usual first two steps).
2. `run.py look <edit folder>` copies this folder and `_shared/` into `<edit folder>/look/`, adds the fonts and
   the words, and prints what to fill.
3. Claude fills CLIPS in cut.py + LINES in build.py from SPEC.md "How a member's version differs": source = `assets/take.mp4`, keep = the whole
   take (`[[0, <length>]]`: the editor already cut it), speed the speed in its config / cut.py.
4. `run.py look <edit folder> run cut.py ...` and `run.py look <edit folder> run build.py ...` run the template with the
   editor's Python (Mac or Linux: a stand-in for mlx_whisper in `_shared/compat/` does the words if needed).
   Words behind the head need the person cut out: `run.py look <edit folder> cutout` (fast on a Mac).
5. `run.py build` adds any GIFs, emojis, callouts and sounds from the member's editing pack on top, then stills to check;
   `run.py render` renders `index.html` (the full reel, not the overlay); `run.py finish` mixes the pack sounds,
   sets -14 LUFS and makes the contact sheet.

## Instagram Edits route: an editable Edits project

- **Quick:** built with Edits' own tools from `styles/text-over-broll.md` in the instagram-edits skill.
  Skip what Edits can't do and say what premium would add.
- **Premium:** run the template's overlay build (graphics only, transparent background), render it as a `.mov`
  (`--format mov`, ProRes 4444 with alpha), then in Edits: the cut clip at 0 s, the overlay on top at 0 s, x 0.5,
  y 0.5, scale 1.0. Edits then does natively: **nothing extra**. See `references/premium-build.md` in instagram-edits.
