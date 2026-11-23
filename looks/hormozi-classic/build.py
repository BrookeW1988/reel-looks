#!/usr/bin/env python3
"""Builds index.html (or the transparent overlay page) for "Inspired by Hormozi: classic". Every number is in SPEC.md.

WHY a generator: HyperFrames captions must be real HTML elements with fixed times, and they come from the word
timings in assets/words-cut.json (made by cut.py). To rebuild the look on a member's take:
    1. edit config.json: footage, keep ranges, speed, hook lines, caption groups, keywords, zoom plan
    2. $PY transcribe.py   (word stamps, source seconds)
       $PY cut.py          (rough cut + word timings on the cut clock)
    3. python3 build.py                    (writes index.html)
       python3 build.py --overlay          (writes overlay/index.html: hook + captions only, transparent, for Edits)
    4. npx --yes hyperframes@0.9.83 check --json, snapshot, render (see SPEC.md "How a member's version differs")

Command-line overrides (handy for one-off tests): --footage assets/x.mp4  --words assets/w.json
--hook "LINE ONE|LINE TWO"  --config other.json
"""
import argparse, html, json, os, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
ap = argparse.ArgumentParser()
ap.add_argument("--config", default="config.json")
ap.add_argument("--footage", default="assets/cut.mp4", help="the rough-cut take (output of cut.py)")
ap.add_argument("--words", default="assets/words-cut.json")
ap.add_argument("--hook", default=None, help='hook lines split by "|"')
ap.add_argument("--overlay", action="store_true", help="transparent captions/hook only -> overlay/index.html")
A = ap.parse_args()
C = json.load(open(A.config))
W = json.load(open(A.words))
HOOK = A.hook.split("|") if A.hook else C["hook"]

DUR = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                            A.footage], capture_output=True, text=True).stdout) - 0.02
# jump-cut times on the cut clock (where cut.py joined two keep ranges): zoom changes snap to these
CUTS, acc = [], 0.0
for a, b in C["keep"][:-1]:
    acc += b - a
    CUTS.append(round(acc / C["speed"], 3))

# ---------------- style numbers (SPEC.md) ----------------
HI = C["highlight"]              # active word colour (#FFE600 classic yellow)
FONT_PX = 84                     # Montserrat Black, caps
MAX_W = 920                      # caption line width before it wraps
CAP_TOP = C["caption_top"]       # caption block grows DOWN from here (the demo take's chin sat ~1420)
ORIGIN_Y = C["zoom_origin_y"]    # punch-ins scale around the chin so the face never grows into the captions

def clean(t):
    """caption text: caps, no full stops or commas (keeps apostrophes and hyphens)"""
    return t.replace(".", "").replace(",", "").upper()

def word_fit(a, b):
    """estimate the line width; shrink the font so a 2-3 word group stays on one line where it can.
    Montserrat 900 caps averages ~0.75 em a character incl. +1% tracking and the 0.26 em word gaps (measured in snapshots)."""
    words = [clean(W[i]["text"]) for i in range(a, b + 1)]
    if len(words) == 1 and words[0] in C.get("hero_words", {}):
        return C["hero_words"][words[0]]          # the one biggest line gets a bigger word (and the 130% punch-in)
    chars = len(" ".join(words))
    px = min(FONT_PX, int(MAX_W / (chars * 0.77)))
    return max(px, 72)           # never below 72: a longer group wraps to 2 lines instead

def captions():
    out, js = [], []
    G = C["caption_groups"]
    for g, (a, b) in enumerate(G):
        start = W[a]["start"] if g else 0.0
        end = W[G[g + 1][0]]["start"] if g + 1 < len(G) else DUR
        spans = "".join(f'<span id="cw{i}" class="cw">{html.escape(clean(W[i]["text"]))}</span> '
                        for i in range(a, b + 1)).strip()
        out.append(f'<div id="cg{g}" class="clip capgroup" data-start="{start:.3f}" data-duration="{end - start:.3f}" '
                   f'data-track-index="20" data-layout-allow-safe-zone style="font-size:{word_fit(a, b)}px">{spans}</div>')
        for i in range(a, b + 1):
            kw = clean(W[i]["text"]) in C["keywords"]
            s = W[i]["start"]
            # the spoken word lights up and pops 110% -> 100% (keywords pop harder: 118% -> 100%; nothing holds scaled, so words never collide)
            # set + to (not fromTo): a fromTo would show its "from" scale on every frame BEFORE the word,
            # which pre-inflates unspoken words into their neighbours
            js.append(f'tl.set("#cw{i}", {{ color: "{HI}", scale: {1.18 if kw else 1.10} }}, {s:.3f});')
            js.append(f'tl.to("#cw{i}", {{ scale: 1.0, duration: 0.10, ease: "power2.out" }}, {s + 0.001:.3f});')
            if i < b:
                js.append(f'tl.set("#cw{i}", {{ color: "#FFFFFF", scale: 1 }}, {W[i + 1]["start"]:.3f});')
    return "\n      ".join(out), "\n    ".join(js)

def zooms():
    """hard punch-ins (gsap.set = a cut, never a ramp), snapped onto a real jump cut when one is within 0.1 s"""
    js = []
    for idx, scale in C["zoom_plan"]:
        t = W[idx]["start"] if idx else 0.0
        near = [c for c in CUTS if abs(c - t) <= 0.1]
        t = near[0] if near else t
        js.append(f'tl.set("#cam", {{ scale: {scale} }}, {t:.3f});')
    return "\n    ".join(js)

cap_html, cap_js = captions()
zoom_js = zooms()
GRADE = open(C["grade"]).read().strip() if os.path.exists(C["grade"]) else ""

# ---- sound: ONE whoosh, on the 130% punch-in. start = picture + 1 frame - the file's measured peak ----
# SFX files aren't shipped with the template: a sound whose file isn't in assets/sfx/ is skipped (add it in Edits instead)
big_t = next(W[i]["start"] for i, s in C["zoom_plan"] if s == max(s2 for _, s2 in C["zoom_plan"]))
SFX = [(n, f, big_t + 1 / 30 - peak, d, v) for n, f, peak, d, v in C["sfx"] if os.path.exists(f"assets/sfx/{f}")]
sfx_html = "\n    ".join(
    f'<audio id="{n}" class="clip" src="assets/sfx/{f}" data-start="{s:.3f}" data-duration="{d}" '
    f'data-volume="{v}" data-fade-out="0.10" data-track-index="{30 + k}"></audio>' for k, (n, f, s, d, v) in enumerate(SFX))

hook_lines = "".join(
    '<div class="hl">' + " ".join(
        f'<span class="{"acc" if w == C["hook_accent_word"] else ""}">{html.escape(w)}</span>' for w in line.split()) + "</div>"
    for line in HOOK)

OV = A.overlay
footage_html = "" if OV else f"""
    <div id="plate" class="clip" data-start="0" data-duration="{DUR:.3f}" data-track-index="0"></div>
    <div id="cam">
      <video id="a-roll" class="clip" src="{A.footage}" {GRADE} playsinline data-has-audio="true" data-volume="1"
             data-start="0" data-duration="{DUR:.3f}" data-track-index="1"></video>
    </div>"""

page = f"""<!doctype html>
<html lang="en" data-resolution="portrait">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1080, height=1920" />
<script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  html, body {{ width: 1080px; height: 1920px; overflow: hidden; background: {"transparent" if OV else "#000000"}; }}
  body {{ font-family: "Montserrat", sans-serif; }}
  #plate {{ position: absolute; inset: 0; z-index: 0; background: #000000; }}
  /* the camera: punch-ins scale around the chin (x 540, y {ORIGIN_Y}) so the face grows up, away from the captions */
  #cam {{ position: absolute; inset: 0; z-index: 1; overflow: hidden; transform-origin: 540px {ORIGIN_Y}px; }}
  #cam video {{ position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }}

  /* hook: Montserrat Black 72, caps, white + 10 px black outline, accent word in the highlight colour */
  #hook {{ position: absolute; left: 0; right: 0; top: 300px; z-index: 5; text-align: center; }}
  #hook .hl {{ font: 900 72px/1.08 "Montserrat"; letter-spacing: 0.01em; color: #FFFFFF;
              -webkit-text-stroke: 10px #000000; paint-order: stroke fill; text-shadow: 0 6px 16px rgba(0,0,0,.55); }}
  #hook .acc {{ color: {HI}; }}

  /* captions: Montserrat Black caps, white, 10 px black outline, soft shadow, no box; spoken word lit */
  .capgroup {{ position: absolute; left: 0; right: 0; top: {CAP_TOP}px; z-index: 8; text-align: center; overflow: visible;
              padding: 0 {int((1080 - MAX_W) / 2)}px; font-family: "Montserrat"; font-weight: 900; line-height: 1.08;
              letter-spacing: 0.01em; color: #FFFFFF; }}
  .cw {{ display: inline-block; margin: 0 0.13em; -webkit-text-stroke: 10px #000000; paint-order: stroke fill;
        text-shadow: 0 6px 16px rgba(0,0,0,.55); transform-origin: 50% 60%; }}
</style>
</head>
<body>
  <div id="root" data-composition-id="main" data-start="0" data-duration="{DUR:.3f}" data-width="1080" data-height="1920">
    {footage_html}
    <div id="hook" class="clip" data-start="0" data-duration="{C["hook_seconds"]}" data-track-index="4">{hook_lines}</div>

    <div id="captions" data-track-kind="captions">
      {cap_html}
    </div>

    {"" if OV else sfx_html}
  </div>

  <script>
    window.__timelines = window.__timelines || {{}};
    const tl = gsap.timeline({{ paused: true }});
    {"" if OV else zoom_js}
    // ---- captions (generated from {A.words}) ----
    {cap_js}
    window.__timelines["main"] = tl;
  </script>
</body>
</html>
"""
# the overlay lives in its own folder: two root compositions in one project make lint fail (and could double audio)
out = "overlay/index.html" if OV else "index.html"
os.makedirs("overlay", exist_ok=True)
open(out, "w").write(page)
print(f"{out} written: {DUR:.2f} s, {len(C['caption_groups'])} caption groups, {len(C['zoom_plan'])} zoom states, "
      f"{0 if OV else len(SFX)} sounds; jump cuts at {CUTS}")
