#!/usr/bin/env python3
"""Builds index.html (+ overlays/index.html) for the Text over B-roll template (micro-lesson variant: one short line per
clip, earlier lines stay). Every number is in SPEC.md.

WHY a generator: the text beats are timed from the clip cuts in assets/clips.json (written by cut.py), so a member's
version is: her clips in cut.py, her lines in LINES below, then
    python3 cut.py && python3 build.py && npx --yes hyperframes@0.9.83 check --json
The format stays calm on purpose: no captions, no stickers, no sound effects, no music in the file (she adds a
song in Edits). The craft is in the grade, the slow motion, the per-word arrival and a clean loop.
"""
import json, html, os, subprocess, tempfile

# ============================== the member's version changes this block ==============================
# one line per clip, lowercase, no full stop, about 24 characters max, written like a text to a friend
# example placeholders: replace with her own lines (one per clip in cut.py, or a single line held to the end)
LINES = ["your first line here", "your second line here", "and your third line"]
LINE_DELAY = [0.0, 0.25, 0.35]     # seconds after each clip's cut that its line starts arriving (line 1 is on at frame 0)
# warm film: the Film Memory treatment (vintage-wash) + warmth, lifted blacks, a little less contrast, grain
GRADE = {"preset": "vintage-wash", "intensity": 0.6,
         "adjust": {"temperature": 0.07, "contrast": -0.05, "blacks": 0.05},
         "details": {"vignette": 0.12, "grain": 0.12, "grainSize": 0.2, "grainRoughness": 0.6}}
TEXT_X, TEXT_TOP, TEXT_PX, LINE_H = 90, 272, 46, 1.25
SHADE = 0.34      # darkest point of the soft shade behind the text block (0 = off)
# ======================================================================================================

FPS, FRAME = 30, 1 / 30
CLIPS = json.load(open("assets/clips.json"))
DUR = round(int((CLIPS[-1]["start"] + CLIPS[-1]["duration"]) * FPS) / FPS - FRAME, 3)
OUT_AT = round(DUR - 0.42, 3)      # lines 2+ leave here, so the last frame = the first frame (clean loop)

def grade_attr(payload, cache="grade-attr.txt"):
    """Validate + expand the grade through `hyperframes media-treatment` once, then cache it."""
    key = json.dumps(payload, sort_keys=True)
    if os.path.exists(cache):
        first, rest = open(cache).read().split("\n", 1)
        if first == key:
            return rest.strip()
    d = tempfile.mkdtemp()
    open(f"{d}/index.html", "w").write('<!doctype html><html><body><div id="root" data-composition-id="main" '
        'data-start="0" data-duration="1" data-width="1080" data-height="1920"><video id="v" class="clip" src="a.mp4" '
        'data-start="0" data-duration="1" muted></video></div></body></html>')
    subprocess.run(["npx", "--yes", "hyperframes@0.9.83", "media-treatment", "--project", d, "--file", "index.html",
                    "--selector", "#v", "--grading", key, "--apply", "--json"], check=True, capture_output=True)
    src = open(f"{d}/index.html").read()
    i = src.index('data-color-grading="')
    attr = src[i:src.index('"', i + len('data-color-grading="')) + 1]
    open(cache, "w").write(key + "\n" + attr + "\n")
    return attr

def page(overlay=False):
    grade = grade_attr(GRADE)
    lines_html, js = [], []
    for n, text in enumerate(LINES):
        start = 0.0 if n == 0 else CLIPS[n]["start"] + LINE_DELAY[n]
        dur = DUR - start
        words = " ".join(f'<span class="w">{html.escape(w)}</span>' for w in text.split(" "))
        lines_html.append(f'<div id="l{n}" class="clip line" data-start="{start:.3f}" data-duration="{dur:.3f}" '
                          f'data-track-index="{4 + n}" style="top:{TEXT_TOP + n * TEXT_PX * LINE_H:.0f}px">{words}</div>')
        if n > 0:
            # per word: blur 6 -> 0 and opacity, 0.14 s each, 0.067 s apart, no movement (calm)
            js.append(f'tl.fromTo("#l{n} .w", {{ opacity: 0, filter: "blur(6px)" }}, {{ opacity: 1, filter: "blur(0px)", '
                      f'duration: 0.14, ease: "power2.out", stagger: 0.067 }}, {start:.3f});')
            js.append(f'tl.to("#l{n} .w", {{ opacity: 0, filter: "blur(6px)", duration: 0.2, ease: "power2.in", stagger: 0.03 }}, {OUT_AT:.3f});')
    # film feel, temporal part (Film Memory recipe): gentle exposure breathing within +-0.03 and a gate weave of
    # <=1.5 px / 0.03 deg, finite and irregular, back to the start state at the end so the loop has no jump
    weave = [(0.0, 0, 0, 0, 1.006, 0.0), (0.7, 1.2, -0.8, 0.02, 1.008, 0.02), (1.45, -0.9, 0.6, -0.015, 1.007, -0.015),
             (2.3, 0.8, 1.1, 0.01, 1.009, 0.025), (3.1, -1.3, -0.5, -0.02, 1.007, -0.01), (4.0, 0.6, -1.2, 0.02, 1.008, 0.02),
             (4.9, -0.7, 0.9, -0.01, 1.009, -0.02), (5.8, 1.1, 0.3, 0.015, 1.007, 0.015), (6.7, -1.0, -0.9, -0.02, 1.008, -0.01),
             (7.6, 0.5, 0.7, 0.01, 1.007, 0.01), (DUR, 0, 0, 0, 1.006, 0.0)]
    for (t0, *_), (t1, x, y, r, s, e) in zip(weave, weave[1:]):
        js.append(f'tl.to("#cam", {{ x: {x}, y: {y}, rotation: {r}, scale: {s}, duration: {t1 - t0:.3f}, ease: "sine.inOut" }}, {t0:.3f});')
        if not overlay:
            js.append(f'tl.to("#broll", {{ "--hf-color-grading-exposure": {e}, duration: {t1 - t0:.3f}, ease: "sine.inOut" }}, {t0:.3f});')
    footage = "" if overlay else f"""
    <div id="cam">
      <video id="broll" class="clip" src="assets/broll.mp4" {grade} style="--hf-color-grading-exposure: 0" muted playsinline
             data-start="0" data-duration="{DUR}" data-track-index="1"></video>
    </div>"""
    if overlay:
        js = [j for j in js if '"#cam"' not in j]
    bg = "transparent" if overlay else "#000000"
    return f"""<!doctype html>
<html lang="en" data-resolution="portrait">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1080, height=1920" />
<script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
<style>
  @font-face {{ font-family: "Instrument Sans"; src: url("assets/fonts/InstrumentSans.ttf"); font-weight: 400 700; }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  html, body {{ width: 1080px; height: 1920px; overflow: hidden; background: {bg}; }}
  #cam {{ position: absolute; inset: 0; overflow: hidden; transform-origin: 50% 50%; }}
  #cam video {{ position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }}
  /* "Friend text": Instrument Sans Medium 46, white, lowercase, soft shadow 0 2 12 black 45%, left x 90 */
  .line {{ position: absolute; left: {TEXT_X}px; right: 120px; z-index: 5; white-space: nowrap;
          font: 500 {TEXT_PX}px/{LINE_H} "Instrument Sans"; letter-spacing: -0.005em; color: #FFFFFF;
          text-shadow: 0 2px 12px rgba(0,0,0,.45); }}
  .w {{ display: inline-block; }}
  /* bright sky / white walls: a soft shade sized to the text block (captions.md: scrim 30-40%, never a full bar) */
  #shade {{ position: absolute; left: -60px; top: {TEXT_TOP - 150}px; width: 1000px; height: {int(len(LINES) * TEXT_PX * LINE_H) + 300}px;
           z-index: 4; background: radial-gradient(ellipse 58% 50% at 34% 50%, rgba(0,0,0,{SHADE}) 0%, rgba(0,0,0,{SHADE * 0.55:.2f}) 45%, rgba(0,0,0,0) 100%); }}
</style>
</head>
<body>
  <div id="root" data-composition-id="main" data-start="0" data-duration="{DUR}" data-width="1080" data-height="1920">
    {footage}
    <div id="shade" class="clip" data-start="0" data-duration="{DUR}" data-track-index="3"></div>
    {chr(10).join("    " + l for l in lines_html)}
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
    {chr(10).join("    " + j for j in js)}
    window.__timelines["main"] = tl;
  </script>
</body>
</html>
"""

if __name__ == "__main__":
    open("index.html", "w").write(page())
    os.makedirs("overlays", exist_ok=True)
    if not os.path.lexists("overlays/assets"):
        os.symlink("../assets", "overlays/assets")
    open("overlays/index.html", "w").write(page(overlay=True))
    json.dump({"voice": None, "sfx": []}, open("sfx.json", "w"))
    print(f"built: {DUR}s, clips at {[c['start'] for c in CLIPS]}, lines out at {OUT_AT}")
