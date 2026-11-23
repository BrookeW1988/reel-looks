---
name: reel-looks
description: Library, not a skill to run on its own. The shared set of 11 reel looks and 8 formats (SPEC.md with every number, HyperFrames code, and how each skill uses it) read by the instagram-edits skill (editable Edits projects) and the video-editor skill (finished MP4s). Use it only through one of those two; if someone asks for a look directly, route them to /instagram-edits or /video-editor.
---

# Reel Looks (library)

This folder is a **library** used by two skills:

- `/instagram-edits`: builds the look as an editable project in Instagram's Edits app (quick = Edits' own tools,
  premium = a transparent overlay rendered from the template + Edits' own camera moves).
- `/video-editor`: renders the look as a finished 9:16 MP4.

Don't run anything here directly and don't build reels inside this folder. If someone asks for a look by name
("the Codie Sanchez look", "pop-up proof"), use whichever of those two skills they're working in, or ask which one
they want (an editable Edits project, or a finished video file).

## For the skill that reads this
- `index.json` matches what people say to a folder: `name` (gallery name) and `also` (other names). Match loosely.
- Each folder (`looks/<slug>/`, `formats/<slug>/`) has `SPEC.md` (every number), `USE.md` (the two routes),
  `card.json` (gallery card) and the code. Always copy a folder AND `_shared/` side by side into the build folder:
  several templates import `../_shared/reeltools.py`.
- Fonts: `bash _shared/get_fonts.sh <slug> <build folder>`.
- The library path: `$REEL_LOOKS_DIR`, else `~/.agents/skills/reel-looks`, else `~/.claude/skills/reel-looks`.
- Gallery to show people: https://claude.ai/artifact/N46Gep95Kujh6TWQyV2y2r
- Rules every route keeps: technique only (never a creator's footage, logos, music or catchphrases); real proof only
  (the member's own screenshots); no invented numbers; comment-keyword CTAs only if the member's keyword is live.
