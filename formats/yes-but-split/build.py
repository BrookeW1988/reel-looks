#!/usr/bin/env python3
"""Builds index.html (the finished reel) and overlays/index.html (labels only, transparent) for Yes... but split.

WHY a generator: labels, crops, grades and the BUT delay all come from config.json, so a member's version is a new
config + `cut.py` + this. Every number is in SPEC.md.
    $PY build.py && npx --yes hyperframes@0.9.83 check --json
"""
import html, json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_shared"))
import reeltools as rt

C = json.load(open("config.json"))
DUR = round(min(rt.duration("assets/yes.mp4"), rt.duration("assets/but.mp4")) - 0.02, 3)
G = {s: (open(f"grade-{s}.txt").read().strip() if os.path.exists(f"grade-{s}.txt") else "") for s in ("yes", "but")}
HALF, DIV = 957, 6                       # two 1080x957 halves + a 6 px white divider = 1920
BUT_AT = C["but_delay"]
# label tops: the top half's sits at y 280 (Instagram's top UI covers y 0-268; 292 clears the outline); the bottom half's at 60 px into its half
LABEL_TOP = {"yes": 292, "but": HALF + DIV + 60}

# The record scratch isn't shipped (why: licences). If assets/sfx/record-scratch.mp3 isn't there, it's left out.
SCRATCH = "assets/sfx/record-scratch.mp3"
HAS_SCRATCH = os.path.exists(SCRATCH)
scratch_at = rt.sfx_start(BUT_AT, SCRATCH) if HAS_SCRATCH else None


def label(side):
    c = C[side]
    sub = "".join(f'<span class="sl">{html.escape(x)}</span>' for x in c["sub"])
    start = 0 if side == "yes" else BUT_AT
    return (f'<div id="lab-{side}" class="clip label" data-start="{start:.3f}" data-duration="{DUR - start:.3f}" '
            f'data-track-index="{5 if side == "yes" else 6}" style="top:{LABEL_TOP[side]}px">'
            f'<div class="big" id="big-{side}">{html.escape(c["label"])}</div><div class="sub" id="sub-{side}">{sub}</div></div>')


def page(overlay=False):
    halves = "" if overlay else f'''
    <div class="half" id="h-yes" style="top:0">
      <video id="v-yes" class="clip" src="assets/yes.mp4" {G["yes"]} muted playsinline data-start="0" data-duration="{DUR}" data-track-index="1"
             style="object-position: 50% {C["yes"]["focus_y"] * 100:.1f}%"></video>
    </div>
    <div id="divider"></div>
    <div class="half" id="h-but" style="top:{HALF + DIV}px">
      <video id="v-but" class="clip" src="assets/but.mp4" {G["but"]} muted playsinline data-start="0" data-duration="{DUR}" data-track-index="2"
             style="object-position: 50% {C["but"]["focus_y"] * 100:.1f}%"></video>
    </div>
''' + (f'''
    <audio id="sfx-scratch" class="clip" src="{SCRATCH}" data-start="{scratch_at:.3f}" data-duration="1.2"
           data-volume="0.18" data-fade-out="0.15" data-track-index="30"></audio>''' if HAS_SCRATCH else "")
    return f"""<!doctype html>
<html lang="en" data-resolution="portrait">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1080, height=1920" />
<script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
<style>
  @font-face {{ font-family: "Anton"; src: url("assets/fonts/Anton-Regular.ttf"); font-weight: 400; }}
  @font-face {{ font-family: "Inter"; src: url("assets/fonts/Inter-Bold.ttf"); font-weight: 700; }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  html, body {{ width: 1080px; height: 1920px; overflow: hidden; background: {"transparent" if overlay else "#FFFFFF"}; }}
  .half {{ position: absolute; left: 0; width: 1080px; height: {HALF}px; overflow: hidden; background: #000; }}
  .half video {{ position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }}
  #divider {{ position: absolute; left: 0; top: {HALF}px; width: 1080px; height: {DIV}px; background: #FFFFFF; z-index: 3; }}
  /* meme labels: white, 6 px black outline, top-left of each half */
  .label {{ position: absolute; left: 74px; z-index: 5; }}
  .big {{ font: 400 72px/1.05 "Anton"; color: #FFFFFF; text-transform: uppercase; letter-spacing: 0.01em;
         -webkit-text-stroke: 12px #000000; paint-order: stroke fill; transform-origin: 0% 60%; }}
  .sub {{ margin-top: 6px; }}
  .sl {{ display: block; font: 700 40px/1.15 "Inter", sans-serif; color: #FFFFFF; -webkit-text-stroke: 8px #000000; paint-order: stroke fill; }}
</style>
</head>
<body>
  <div id="root" data-composition-id="main" data-start="0" data-duration="{DUR}" data-width="1080" data-height="1920">
    {halves}
    {label("yes")}
    {label("but")}
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
    // YES is up from frame 0 (the thumbnail) and never moves.
    // BUT slams in a beat later (the comic timing), then holds dead still; its sub-label follows 3 frames behind.
    tl.fromTo("#big-but", {{ scale: 1.35, opacity: 0, filter: "blur(10px)" }}, {{ scale: 1, opacity: 1, filter: "blur(0px)", duration: 0.16, ease: "expo.out" }}, {BUT_AT:.3f});
    tl.fromTo("#sub-but", {{ opacity: 0, x: -14 }}, {{ opacity: 1, x: 0, duration: 0.18, ease: "power3.out" }}, {BUT_AT + 0.1:.3f});
    window.__timelines["main"] = tl;
  </script>
</body>
</html>
"""


open("index.html", "w").write(page(False))
rt.write_overlays(page(True))
print(f"index.html + overlays/index.html: {DUR}s; BUT at {BUT_AT}s; scratch starts {scratch_at}")
