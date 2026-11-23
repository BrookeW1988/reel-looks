#!/usr/bin/env python3
"""Builds the Calm luxury reel (index.html); with --overlay, the same page as a text-only transparent overlay.

Every number is in SPEC.md; everything a member changes is in reel.json (or pass another config: build.py my.json).

WHY it is so small: the look is restraint. The camera never moves, text never animates, there are no effects and no
sound effects. So the whole "edit" is: shots placed back to back with hard cuts, one white serif line that swaps on
the frame the next phrase starts, an optional static title, an optional quiet music bed, and a warm grade.

Guards (they stop the build rather than ship something wrong):
- every caption line must match the transcript words in order (the speaker's actual words, proofread for display only);
- nothing in reel.json may animate: there is no animation code to configure.

    python3 build.py && npx --yes hyperframes@0.9.83 check --json
    npx --yes hyperframes@0.9.83 render --workers 2 -o renders/calm-luxury.mp4
    python3 build.py --overlay && npx --yes hyperframes@0.9.83 render --workers 2 --format mov -o renders/calm-luxury-overlays.mov
    python3 build.py            # always rebuild the full reel afterwards
Media isn't shipped: a voice or music file that isn't there is left out (with a note), never a crash.
"""
import json, html, re, sys, os


def has(p):
    """True if a media file is there (why: music and voice files aren't shipped; skip, never crash)."""
    return bool(p) and os.path.exists(p)

FPS = 30
ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
OVERLAY = "--overlay" in sys.argv        # text only, transparent: for Edits' addOverlay (see SPEC.md)
CFG = json.load(open(ARGS[0] if ARGS else "reel.json"))
TY = CFG["type"]


def fr(t):
    """Snap a time to the 30 fps frame grid (hard cuts land on whole frames)."""
    return round(round(t * FPS) / FPS, 4)


# ---- shots: back to back, hard cuts only ----
shots, t = [], 0.0
for i, s in enumerate(CFG["shots"]):
    shots.append({**s, "id": f"shot{i}", "at": fr(t)})
    t += s["dur"]
if CFG.get("bookend"):                     # hands footage: repeat the opening (hero) shot at the end so it loops
    b = CFG["bookend"]
    shots.append({"src": CFG["shots"][0]["src"], "in": CFG["shots"][0]["in"], "dur": b["dur"], "audio": False,
                  "id": "bookend", "at": fr(t)})
    t += b["dur"]
DUR = fr(t)
# every hard cut on the timeline: shot joins + edits made inside a shot by cut.py (assets/cut-points.json)
CUTS = [s["at"] for s in shots[1:]]
for s in shots:
    if s.get("cut_points") and os.path.exists(s["cut_points"]):
        CUTS += [fr(s["at"] + c - s["in"]) for c in json.load(open(s["cut_points"])) if s["in"] < c < s["in"] + s["dur"]]

# ---- caption lines -> transcript words (by position, never by text search: repeated words would take the wrong time) ----
W = json.load(open(CFG["words"])) if CFG.get("words") else []   # music-only reels: no words, no captions
norm = lambda s: re.sub(r"[^a-z0-9']", "", s.lower())
groups, k = [], 0
for line in CFG["lines"]:
    toks = line.split()
    got = W[k:k + len(toks)]
    if [norm(x) for x in toks] != [norm(w["text"]) for w in got]:
        sys.exit(f"Caption line does not match the spoken words at word {k}: {line!r} vs {' '.join(w['text'] for w in got)!r}")
    groups.append({"text": line, "first": got[0], "last": got[-1]})
    k += len(toks)
if k != len(W):
    sys.exit(f"{len(W) - k} transcript words are not captioned: {' '.join(w['text'] for w in W[k:])}")

PAUSE_BLANK = 0.35   # a real pause between phrases -> the screen goes blank (Jess: the odd 0.17 s blank between chunks)
for i, g in enumerate(groups):
    g["start"] = 0.0 if i == 0 else fr(g["first"]["start"] - 0.05)    # frame 0 already shows the first line
    # a line that starts right by a hard cut swaps ON the cut, never a couple of frames before it
    for c in CUTS:
        if abs(c - g["start"]) <= 0.1 and c <= g["first"]["start"] + 0.02:
            g["start"] = c
for i, g in enumerate(groups):
    nxt = groups[i + 1]["start"] if i + 1 < len(groups) else DUR
    gap = (groups[i + 1]["first"]["start"] - g["last"]["end"]) if i + 1 < len(groups) else 0
    g["end"] = fr(min(nxt, g["last"]["end"] + 0.2)) if gap > PAUSE_BLANK else nxt

GRADE = ""
if CFG.get("grade_file") and os.path.exists(CFG["grade_file"]):
    GRADE = open(CFG["grade_file"]).read().strip()     # made by `hyperframes media-treatment` (see SPEC.md "Grade")

FONT = f"""@font-face {{ font-family: "Newsreader"; src: url("{TY['font_file']}"); font-weight: 200 800; }}"""
CSS = f"""
  {FONT}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  html, body {{ width: 1080px; height: 1920px; overflow: hidden; background: BG; }}
  /* one serif, one weight, one colour, no shadow, no stroke, no box (SPEC.md "Type") */
  .serif {{ font-family: "Newsreader", serif; font-weight: 400; font-variation-settings: "opsz" 16;
           color: {TY['colour']}; text-align: center; font-kerning: normal; }}
  .shot {{ position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }}
  /* captions: ONE line, centred x 540, centre y {TY['caption_centre_y']}, on the dark top, never on the face */
  .cap {{ position: absolute; left: 0; right: 0; top: {TY['caption_centre_y'] - 30}px; height: 60px; z-index: 10;
          font-size: {TY['caption_px']}px; line-height: 60px; white-space: nowrap; overflow: visible; }}
  .title {{ position: absolute; left: 90px; right: 90px; z-index: 9; font-size: {TY['title_px']}px;
           line-height: {TY['title_leading']}; }}
"""


def shot_tags():
    out = []
    for i, s in enumerate(shots):
        sound = 'data-has-audio="true" data-volume="1"' if s["audio"] else "muted"
        out.append(f'<video id="{s["id"]}" class="clip shot" src="{s["src"]}" {GRADE} playsinline {sound} '
                   f'data-media-start="{s["in"]}" data-start="{s["at"]}" data-duration="{fr(s["dur"])}" '
                   f'data-track-index="{1 + i % 2}"></video>')
    return "\n    ".join(out)


def caption_tags():
    return "\n      ".join(
        f'<div id="cap{i}" class="clip cap serif" data-start="{g["start"]}" data-duration="{fr(g["end"] - g["start"])}" '
        f'data-track-index="20">{html.escape(g["text"])}</div>' for i, g in enumerate(groups))


def title_tag():
    tt = CFG.get("title")
    if not tt:
        return ""
    end = tt.get("end") or DUR
    n = len(tt["lines"]); h = n * TY["title_px"] * TY["title_leading"]
    lines = "<br>".join(html.escape(x) for x in tt["lines"])
    return (f'<div id="title" class="clip title serif" data-start="{tt.get("start", 0)}" data-duration="{fr(end - tt.get("start", 0))}" '
            f'data-track-index="19" style="top:{TY["title_centre_y"] - h / 2:.0f}px">{lines}</div>')


def audio_tags():
    out = []
    for key in ("voice", "music"):
        src = CFG.get(key) if key == "voice" else (CFG.get("music") or {}).get("src")
        if CFG.get(key) and not has(src):
            print(f"note: {key} file {src} not found, left out")
    if CFG.get("voice") and has(CFG["voice"]):
        out.append(f'<audio id="voice" class="clip" src="{CFG["voice"]}" data-start="0" data-duration="{DUR}" '
                   f'data-volume="1" data-track-index="30"></audio>')
    if CFG.get("music") and has(CFG["music"].get("src")):   # quiet bed ~18 dB under the voice (SPEC.md "Sound"); 0.126 = -18 dB
        m = CFG["music"]
        out.append(f'<audio id="bed" class="clip" src="{m["src"]}" data-start="0" data-duration="{DUR}" '
                   f'data-volume="{m.get("volume", 0.126)}" data-fade-in="0" data-fade-out="0.6" data-track-index="31"></audio>')
    return "\n    ".join(out)


def page(overlay):
    bg = "transparent" if overlay else CFG["background"]
    media = "" if overlay else f"{shot_tags()}\n    {audio_tags()}"
    return f"""<!doctype html>
<html lang="en" data-resolution="portrait">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1080, height=1920" />
<script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
<style>{CSS.replace("BG", bg)}</style>
</head>
<body>
  <div id="root" data-composition-id="main" data-start="0" data-duration="{DUR}" data-width="1080" data-height="1920">
    {media}
    {title_tag()}
    <div id="captions" data-track-kind="captions">
      {caption_tags()}
    </div>
  </div>
  <script>
    // Nothing animates in this look: every element is hard-on/hard-off by its clip window. The timeline is empty on purpose.
    const tl = gsap.timeline({{ paused: true }});
    tl.set({{}}, {{}}, {DUR});
    window.__timelines["main"] = tl;
  </script>
</body>
</html>
"""


# ONE root file only (two roots = duplicate audio, a check error), so the overlay is a build mode, not a second file.
open("index.html", "w").write(page(OVERLAY))
print(f"index.html ({'OVERLAY: text only, transparent' if OVERLAY else 'full reel'}): {DUR} s, {len(shots)} shot(s), {len(groups)} caption lines")
for i, g in enumerate(groups):
    print(f"  cap{i}  {g['start']:6.3f} -> {g['end']:6.3f}  ({g['end'] - g['start']:.2f} s)  {g['text']}")
