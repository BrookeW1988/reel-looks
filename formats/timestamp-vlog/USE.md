# How each skill uses Timestamp vlog

Short clips stamped with their real recorded time in the same spot, the same swipe between every clip, a warm daylight look and a shutter on the last shot.

**Format:** `timestamp-vlog` · gallery name "Timestamp vlog" · a Wright Mode format.
Every number is in `SPEC.md`. The code is `cut.py` + `build.py` (HyperFrames). The member fills: config.json.

What the member brings:
- vlog clips from through the day

Editing-pack extras this format takes (GIFs, emojis, callouts, sounds from the member's own pack):
none: its SPEC bans them, so the look stays clean whatever is in the pack.

## Claude Video Editor route: a finished 9:16 MP4

The Video Editor does its own cut first (dead air, ums, retakes), then hands this template the member's own clips: this format isn't a single talking-head take, so Claude copies them into `assets/` and fills the config by hand from SPEC.md.

1. `run.py start <take> --format timestamp-vlog [--look <a look>]` then `run.py cut <edit folder>`
   (the editor's usual first two steps).
2. `run.py look <edit folder>` copies this folder and `_shared/` into `<edit folder>/look/`, adds the fonts and
   the words, and prints what to fill.
3. Claude fills config.json from SPEC.md "How a member's version differs": source = `assets/take.mp4`, keep = the whole
   take (`[[0, <length>]]`: the editor already cut it), speed the speed in its config / cut.py.
4. `run.py look <edit folder> run cut.py ...` and `run.py look <edit folder> run build.py ...` run the template with the
   editor's Python (Mac or Linux: a stand-in for mlx_whisper in `_shared/compat/` does the words if needed).
   Words behind the head need the person cut out: `run.py look <edit folder> cutout` (fast on a Mac).
5. `run.py build` adds any GIFs, emojis, callouts and sounds from the member's editing pack on top, then stills to check;
   `run.py render` renders `index.html` (the full reel, not the overlay); `run.py finish` mixes the pack sounds,
   sets -14 LUFS and makes the contact sheet.

## Instagram Edits route: an editable Edits project

Built natively in Edits, with Edits' own tools only (no rendering, no overlay video): `/instagram-edits` follows
`styles/timestamp-vlog.md` in the instagram-edits skill. That recipe takes its numbers and feel from this SPEC and turns them
into Edits steps (captions, text presets and animations, the sound effects library, zooms and keyframes, filters,
transitions, split screen, cut-outs). Where a move here can't be done in Edits, it does the closest Edits version and
says what it swapped. It never runs this folder's build or render commands.

The fully animated version, using the HyperFrames motion templates in this folder, is the Claude Video Editor route
above.
