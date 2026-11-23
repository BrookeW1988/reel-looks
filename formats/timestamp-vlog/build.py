#!/usr/bin/env python3
"""Builds index.html (the finished reel) and overlays/index.html (graphics only, transparent) for Timestamp vlog.

WHY a generator: the clip order, lengths, recorded times and labels all live in config.json, and every timing below
(swipes, chip swaps, sounds) follows from them. A member's version = new config.json + `cut.py` + this.
Every number is in SPEC.md.
    $PY build.py && npx --yes hyperframes@0.9.83 check --json
"""
import html, json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_shared"))
import reeltools as rt

C = json.load(open("config.json"))
GRADE = open("grade-attr.txt").read().strip() if os.path.exists("grade-attr.txt") else ""
SW = C["swipe_frames"] / rt.FPS            # one swipe-left, 6 frames, the same on every cut

# clip k starts while clip k-1 is swiping out: start_k = start_(k-1) + dur_(k-1) - swipe
starts, t = [], 0.0
for c in C["clips"]:
    starts.append(round(t, 3)); t += c["dur"] - SW
DUR = round(starts[-1] + C["clips"][-1]["dur"], 3)
CUTS = starts[1:]                           # each swipe runs [cut, cut + SW)
LAST = C["clips"][-1]
SHUTTER = starts[-1] + LAST["shutter_at"] if LAST.get("shutter_at") else None
TITLE_OUT = 1.5


def has(p):
    """Sounds aren't shipped with the template (why: licences). A missing file is skipped, never a crash."""
    return os.path.exists(p)

# ---- sound: soft whooshes on the swipes (three takes, never the same twice), a shutter on the final result ----
# Files the member drops into assets/sfx/ with these names (SPEC.md "Sound"); any that aren't there are left out.
SFX_FILES = ["whoosh-1.mp3", "whoosh-2.mp3", "whoosh-3.mp3"]
SFX = []
for n, cut in enumerate(CUTS):
    f = SFX_FILES[n % len(SFX_FILES)]
    SFX.append((f"sfx-sw{n + 1}", f, cut + SW / 2, 0.8, [0.54, 0.46, 0.49][n % 3]))   # peak at the swipe's fastest frame
if SHUTTER:
    SFX.append(("sfx-shutter", "shutter.mp3", SHUTTER, 0.4, 0.86))
SFX = [x for x in SFX if has("assets/sfx/" + x[1])]
sfx_html = "\n    ".join(
    f'<audio id="{i}" class="clip" src="assets/sfx/{f}" data-start="{rt.sfx_start(pic, "assets/sfx/" + f):.3f}" '
    f'data-duration="{d}" data-volume="{v}" data-fade-out="0.1" data-track-index="{30 + n}"></audio>'
    for n, (i, f, pic, d, v) in enumerate(SFX))


def chips():
    out, js = [], []
    for k, c in enumerate(C["clips"]):
        s = 0.0 if k == 0 else CUTS[k - 1] + SW / 2           # the label changes at the middle of the swipe
        e = (CUTS[k] + SW / 2) if k + 1 < len(C["clips"]) else DUR
        out.append(f'<div id="chip{k + 1}" class="clip chip" data-start="{s:.3f}" data-duration="{e - s:.3f}" data-track-index="{10 + k}">'
                   f'<span class="ct">{html.escape(c["when"])} · {html.escape(c["label"])}</span></div>')
        if k > 0:   # blur swap on one stage: the chip never moves, only its words change
            js.append(f'tl.fromTo("#chip{k + 1} .ct", {{ opacity: 0, filter: "blur(6px)" }}, {{ opacity: 1, filter: "blur(0px)", duration: 0.13, ease: "power2.out" }}, {s:.3f});')
    return "\n    ".join(out), "\n    ".join(js)


chip_html, chip_js = chips()


def page(overlay=False):
    shots, swipe_js = [], []
    for k, c in enumerate(C["clips"]):
        end = (CUTS[k] + SW) if k + 1 < len(C["clips"]) else DUR
        shots.append(f'''<div class="shot" id="shot{k + 1}">
      <video id="v{k + 1}" class="clip" src="assets/clip{k + 1}.mp4" {GRADE} muted playsinline
             data-start="{starts[k]:.3f}" data-duration="{end - starts[k]:.3f}" data-track-index="{1 + k}"></video>
    </div>''')
        swipe_js.append(f'tl.set("#shot{k + 1}", {{ x: {0 if k == 0 else 1080} }}, 0);')
    for k, cut in enumerate(CUTS):
        # one swipe-left: the old clip and the new one move together, fastest in the middle
        swipe_js.append(f'tl.to("#shot{k + 1}", {{ x: -1080, duration: {SW:.3f}, ease: "power2.inOut" }}, {cut:.3f});')
        swipe_js.append(f'tl.to("#shot{k + 2}", {{ x: 0, duration: {SW:.3f}, ease: "power2.inOut" }}, {cut:.3f});')
    flash = "" if overlay or not SHUTTER else f'<div id="flash" class="clip" data-start="{SHUTTER:.3f}" data-duration="0.2" data-track-index="9"></div>'
    flash_js = "" if overlay or not SHUTTER else f'tl.fromTo("#flash", {{ opacity: 0.85 }}, {{ opacity: 0, duration: 0.17, ease: "power2.out" }}, {SHUTTER:.3f});'
    footage = "" if overlay else "\n    ".join(shots)
    return f"""<!doctype html>
<html lang="en" data-resolution="portrait">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1080, height=1920" />
<script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
<style>
  @font-face {{ font-family: "JetBrains Mono"; src: url("assets/fonts/JetBrainsMono.ttf"); font-weight: 100 800; }}
  @font-face {{ font-family: "Instrument Serif"; src: url("assets/fonts/InstrumentSerif-Italic.ttf"); font-style: italic; font-weight: 400; }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  html, body {{ width: 1080px; height: 1920px; overflow: hidden; background: {"transparent" if overlay else "#000"}; }}
  .shot {{ position: absolute; inset: 0; overflow: hidden; }}
  .shot video {{ position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }}
  #flash {{ position: absolute; inset: 0; background: #FFFFFF; z-index: 8; }}
  /* the timestamp chip: same spot, same style on every clip */
  .chip {{ position: absolute; left: 66px; top: 280px; z-index: 10; }}
  .ct {{ display: inline-block; font: 500 40px/1.2 "JetBrains Mono"; color: #FFFFFF; background: rgba(0,0,0,.6);
        border-radius: 10px; padding: 8px 16px; letter-spacing: -0.02em; }}
  #title {{ position: absolute; left: 0; right: 0; top: 1010px; z-index: 10; text-align: center;
           font: italic 400 72px/1.1 "Instrument Serif"; color: #FFFFFF; text-shadow: 0 4px 24px rgba(0,0,0,.45); }}
</style>
</head>
<body>
  <div id="root" data-composition-id="main" data-start="0" data-duration="{DUR}" data-width="1080" data-height="1920" >
    {footage}
    {flash}
    <div id="title" class="clip" data-start="0" data-duration="{TITLE_OUT:.2f}" data-track-index="8"><span id="title-t">{html.escape(C["title"])}</span></div>
    {chip_html}
    {"" if overlay else sfx_html}
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
    {chr(10).join("    " + x for x in ([] if overlay else swipe_js))}
    // title: on screen at frame 0 (the thumbnail), leaves with a soft blur before the first swipe
    tl.to("#title-t", {{ opacity: 0, filter: "blur(8px)", duration: 0.2, ease: "power2.in" }}, {TITLE_OUT - 0.22:.2f});
    {chip_js}
    {flash_js}
    window.__timelines["main"] = tl;
  </script>
</body>
</html>
"""


open("index.html", "w").write(page(False))
rt.write_overlays(page(True))
print(f"index.html + overlays/index.html: {DUR}s; clip starts {starts}; swipes at {CUTS}; shutter {SHUTTER}")
