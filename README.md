# Reel Looks

One shared library of reel **looks** (how a reel looks) and **formats** (how it's structured), used by two skills:

- **instagram-edits**: Claude builds an *editable* project inside Instagram's Edits app on your Mac.
- **Claude Video Editor** (`/video-editor`): Claude renders a *finished* 9:16 MP4 from your talking-head take.

Same looks, same numbers. The Video Editor renders them from the code here; instagram-edits builds them with Edits'
own tools. Pick one by its name in either skill: "edit this in the Codie Sanchez look",
"use the pop-up proof format".

**See every look and format moving:** https://claude.ai/artifact/N46Gep95Kujh6TWQyV2y2r

## What's in it

**11 looks:** Just you · Full · Hormozi classic · Hormozi 2026 · Codie Sanchez · Diary of a CEO · Nana Del Rey ·
Mariah Brunner · Nick Saraev · Iman Gadzhi · Calm luxury

**8 formats:** Pop-up proof · Text over B-roll · Serialised episode · Before-and-after · POV skit · Green-screen proof ·
Timestamp vlog · Yes... but

Looks named after creators are **inspired by their editing techniques** (sizes, pacing, caption style), measured from
their public reels. None of them use the creators' footage, logos, music, wordmarks or catchphrases. Formats that show
proof use **your** proof: real screenshots you supply, never invented.

```
index.json          every look and format: gallery name, other names people use, what it needs, what Edits does natively
looks/<slug>/       one folder per look
formats/<slug>/     one folder per format
  SPEC.md           every number: palette, type sizes and positions, motion timings, sound levels, grade
  USE.md            how each skill uses it (Edits route = built natively with Edits' own tools; Video Editor route = finished MP4)
  card.json         the gallery card (title, one-liner, palette, fonts, references)
  cut.py, build.py  the HyperFrames code (plus whatever helpers that look needs)
  config file       reel.json / config.json / plan.json: example values only, filled per take
_shared/            helpers several templates use (reeltools.py, measure.py, get_fonts.sh, render.sh, check.sh)
_shared/compat/     a stand-in for mlx_whisper so the templates also run on Linux and in the Video Editor's Python
SKILL.md            tells Claude this is a library (used by instagram-edits and video-editor), not a skill to run
```

No fonts, footage, sounds, GIFs or screenshots live here. Fonts are free Google Fonts that `_shared/get_fonts.sh`
downloads per build (see `FONTS.md`). Sounds and GIFs come from your own folder or your editing pack.

## Where it installs

Both skills look for it at **`~/.agents/skills/reel-looks`** (and `~/.claude/skills/reel-looks`, a link to the same
folder, so Claude Code and Codex share one copy). Each skill's install step installs it there if it's missing. To keep
it up to date: `cd ~/.agents/skills/reel-looks && git pull`.

For Claude doing the install:
```bash
mkdir -p ~/.agents/skills ~/.claude/skills
[ -e ~/.agents/skills/reel-looks ] || git clone https://github.com/BrookeW1988/reel-looks ~/.agents/skills/reel-looks
[ -e ~/.claude/skills/reel-looks ] || ln -s ~/.agents/skills/reel-looks ~/.claude/skills/reel-looks
```
(No git? Download https://github.com/BrookeW1988/reel-looks/archive/refs/heads/main.zip, unzip it and rename the folder
to `reel-looks`.) A skill that finds it somewhere else can be pointed at it with the `REEL_LOOKS_DIR` environment variable.

## How to add a look

1. Make a folder: `looks/<new-slug>/` (or `formats/<new-slug>/` for a structure rather than an appearance). Copy the
   closest existing look as a starting point.
2. Measure the creator's reels (instagram-edits: "analyse my editing style frame by frame and save it as a new look").
   Write **every number** into `SPEC.md`: palette, fonts, type sizes and positions, caption rules, camera moves,
   motion timings and eases, sound levels, grade, what's banned. Keep the "How a member's version differs" section.
3. Change `build.py` so its STYLE/plan blocks match the SPEC, and keep one clearly marked "CLAUDE CHANGES PER TAKE"
   block (or a config file) holding everything that changes per take, with example values only.
4. Add `card.json` (title, one-liner, palette, fonts, reference reel links) and a `USE.md` (copy one and change the
   names, the config file and the "Edits does natively" line).
5. Add the fonts it needs to `_shared/get_fonts.sh` and `FONTS.md`.
6. Add an entry to `index.json` (slug, kind, name, other names, config, needs, edits_native, speed).
7. Test it in both skills on a real take, then commit. Add a demo to the gallery.

Your own looks made with "save my style as a new look" stay in each skill's own folder (`my-looks/` in instagram-edits,
`~/.video-editor/styles/` in the Video Editor): this library is the shared, published set.

## Licence

Code and instructions: MIT (see `LICENSE`). No third-party media is included.
