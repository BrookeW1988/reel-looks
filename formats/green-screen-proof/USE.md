# How each skill uses Green-screen proof

You talk in front of the real page you're reacting to, with a highlighter hook, a source chip and a red pen mark on the exact line as you say it.

**Format:** `green-screen-proof` · gallery name "Green-screen proof" · a Wright Mode format.
Every number is in `SPEC.md`. The code is `cut.py` + `build.py` (HyperFrames). The member fills: config.json.

What the member brings:
- real web pages to screenshot (shots.py, needs Playwright)
- the person cut-out (made by `hyperframes remove-background`, slow)

Editing-pack extras this format takes (GIFs, emojis, callouts, sounds from the member's own pack):
gif, emoji, callout, sound.

## Claude Video Editor route: a finished 9:16 MP4

The Video Editor does its own cut first (dead air, ums, retakes), then hands this template the editor's clean take (dead air and retakes already cut) as `assets/take.mp4`, plus its word timings under every file name the templates read (`assets/words-src.json`, `assets/whisper-words.json`, `assets/words-source.json`, `work/words-source.json`).

1. `run.py start <take> --format green-screen-proof [--look <a look>]` then `run.py cut <edit folder>`
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

- **Quick:** built with Edits' own tools from `styles/green-screen-proof.md` in the instagram-edits skill.
  Skip what Edits can't do and say what premium would add.
- **Premium:** run the template's overlay build (graphics only, transparent background), render it as a `.mov`
  (`--format mov`, ProRes 4444 with alpha), then in Edits: the cut clip at 0 s, the overlay on top at 0 s, x 0.5,
  y 0.5, scale 1.0. Edits then does natively: **nothing extra**. See `references/premium-build.md` in instagram-edits.
