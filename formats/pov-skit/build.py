#!/usr/bin/env python3
"""Builds index.html (the finished reel) and overlays/index.html (graphics only, transparent) for POV micro-skit.

WHY a generator: captions must be real HTML elements with fixed times (HyperFrames rule) and they come from the word
timings; the reaction beat's time comes from the cut (assets/beats.json). A member's version = new config.json +
`cut.py` + this. Every number is in SPEC.md.
    $PY build.py && npx --yes hyperframes@0.9.83 check --json
"""
import html, json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_shared"))
import reeltools as rt

C = json.load(open("config.json"))
W = json.load(open("assets/words-cut.json"))
BEATS = json.load(open("assets/beats.json"))
DUR = round(BEATS["duration"] - 0.02, 3)
REACT = BEATS["reaction_start"]
GRADE = open("grade-attr.txt").read().strip() if os.path.exists("grade-attr.txt") else ""
FX, FY = C["face_centre"]
INK, PILL = "#1A1A1A", "#FFFFFF"


# ---- caption groups: ~3-4 words (16+ characters), break after punctuation, never end on a little word ----
SMALL = {"a", "an", "the", "to", "on", "in", "of", "and", "for", "my", "your"}


def groups():
    gs, cur = [], []
    for i, w in enumerate(W):
        cur.append(i)
        long_enough = len(" ".join(W[j]["text"] for j in cur)) >= 16
        if w["text"][-1] in ".,!?" or (long_enough and w["text"].lower() not in SMALL):
            gs.append(cur); cur = []
    if cur:
        gs.append(cur)
    return gs


GROUPS = groups()


def captions():
    out, js = [], []
    for g, idx in enumerate(GROUPS):
        start = max(0.1, W[idx[0]]["start"] - 0.04)
        end = (W[GROUPS[g + 1][0]]["start"] - 0.04) if g + 1 < len(GROUPS) else W[idx[-1]]["end"] + 0.25
        end = min(end, REACT - 0.02)      # captions are gone the moment the reaction punch lands
        text = " ".join(html.escape(W[i]["text"]) for i in idx)
        out.append(f'<div id="cg{g}" class="clip capgroup" data-start="{start:.3f}" data-duration="{end - start:.3f}" '
                   f'data-track-index="20"><span class="ctext">{text}</span></div>')
        js.append(f'tl.fromTo("#cg{g} .ctext", {{ opacity: 0, y: 6 }}, {{ opacity: 1, y: 0, duration: 0.08, ease: "power2.out" }}, {start:.3f});')
    return "\n      ".join(out), "\n    ".join(js)


cap_html, cap_js = captions()
pov_html = "".join(f'<span class="pl">{html.escape(l)}</span>' for l in C["pov_lines"])
EMOJI_AT = REACT + 0.12          # the emoji lands 4 frames after the punch: punch first, then the feeling
EMOJI = f'assets/img/{C["reaction_emoji"]}' if C.get("reaction_emoji") else None
if EMOJI and not os.path.exists(EMOJI):
    print(f"skipping the reaction emoji: {EMOJI} isn't there (images aren't shipped; add your own PNG)")
    EMOJI = None


def page(overlay=False):
    footage = "" if overlay else f'''
    <div id="cam">
      <video id="a-roll" class="clip" src="assets/cut.mp4" {GRADE} playsinline data-has-audio="true" data-volume="{C.get('voice_gain', 1.0)}"
             data-start="0" data-duration="{DUR}" data-track-index="1"></video>
    </div>'''
    cam_js = "" if overlay else f'''
    tl.set("#cam", {{ scale: 1 }}, 0);
    tl.set("#cam", {{ scale: {C["punch"]} }}, {REACT:.3f});     // hard punch-in on the face for the reaction'''
    return f"""<!doctype html>
<html lang="en" data-resolution="portrait">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1080, height=1920" />
<script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
<style>
  @font-face {{ font-family: "Poppins"; src: url("assets/fonts/Poppins-SemiBold.ttf"); font-weight: 600; }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  html, body {{ width: 1080px; height: 1920px; overflow: hidden; background: {"transparent" if overlay else "#000"}; }}
  #cam {{ position: absolute; inset: 0; overflow: hidden; transform-origin: {FX}px {FY}px; z-index: 1; }}
  #cam video {{ position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }}
  /* the native Instagram text look: ink on a white pill, one pill per line */
  #pov {{ position: absolute; left: 0; right: 0; top: 290px; z-index: 5; text-align: center; }}
  #pov .pl {{ display: table; margin: 0 auto 8px; background: {PILL}; color: {INK}; border-radius: 14px; padding: 12px 22px;
             font: 600 48px/1.2 "Poppins"; letter-spacing: -0.005em; }}
  .capgroup {{ position: absolute; left: 0; right: 0; top: {C.get("caption_top", 1240)}px; text-align: center; z-index: 6; padding: 0 80px; overflow: visible; }}
  .ctext {{ display: inline-block; font: 600 44px/1.2 "Poppins"; color: #FFFFFF; -webkit-text-stroke: 6px #000000;
           paint-order: stroke fill; text-shadow: 0 3px 10px rgba(0,0,0,.35); }}
  #emoji {{ position: absolute; left: 770px; top: 470px; width: 210px; height: 210px; z-index: 7; }}
  #emoji img {{ width: 100%; height: 100%; display: block; }}
</style>
</head>
<body>
  <div id="root" data-composition-id="main" data-start="0" data-duration="{DUR}" data-width="1080" data-height="1920">
    {footage}
    <div id="pov" class="clip" data-start="0" data-duration="{DUR}" data-track-index="4">{pov_html}</div>
    <div id="captions" data-track-kind="captions">
      {cap_html}
    </div>
    {f'''<div id="emoji" class="clip" data-start="{EMOJI_AT:.3f}" data-duration="{DUR - EMOJI_AT:.3f}" data-track-index="7">
      <img id="emoji-img" src="{EMOJI}" alt="" />
    </div>''' if EMOJI else ""}
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
    {cam_js}
    // POV line is on screen from frame 0 and never moves (it is the thumbnail and the joke's setup)
    {cap_js}
    // reaction emoji: springs in beside the head (never over the face), then holds dead still
    {f'tl.fromTo("#emoji-img", {{ scale: 0.2, rotation: -18, opacity: 0 }}, {{ scale: 1, rotation: 0, opacity: 1, duration: 0.42, ease: "back.out(2.2)" }}, {EMOJI_AT:.3f});' if EMOJI else ""}
    window.__timelines["main"] = tl;
  </script>
</body>
</html>
"""


open("index.html", "w").write(page(False))
rt.write_overlays(page(True))
print(f"index.html + overlays/index.html: {DUR}s, {len(GROUPS)} caption groups:",
      [" ".join(W[i]["text"] for i in g) for g in GROUPS], "reaction", REACT)
