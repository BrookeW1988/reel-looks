#!/usr/bin/env python3
"""Builds the "Inspired by Codie Sanchez" (studio editorial) look on any talking-head take. Every number is in SPEC.md.

WHY a generator: captions must be real HTML elements with fixed times (HyperFrames rule), and they come from word
timings. Re-skinning a member's video = new footage + words file + a screens plan, then re-run:

    python3 build.py --footage assets/cut.mp4 --words assets/words-cut.json --screens screens.json
    npx hyperframes check --json

Writes TWO root compositions:
  index.html     the finished reel (graded footage, camera A/B cuts, captions, music bed)
  overlay/index.html  captions only on a transparent canvas: `npx hyperframes render overlay --format mov` (Edits addOverlay)

screens.json (one entry per caption screen, in order; word indexes refer to the words file):
  {"words": [0, 6], "kind": "pair", "lead": 3}   serif lead-in = first 3 words, light-sans line = the rest
  {"words": [19, 21], "kind": "solo"}            one big serif emphasis line, builds word by word
  {"words": [47, 50], "kind": "payoff", "split": 2, "italic_from": 2}
                                                 closing line: serif 500, 2 lines, words from italic_from on are
                                                 italic + underlined; the only element that animates in
plus a "camera" list of word indexes where the hard cut to the other angle lands, e.g. "camera": [7, 12, 19].
If --screens is omitted the EXAMPLE plan below (PLAN_EXAMPLE) is used: Claude replaces it per take.
"""
import argparse, html, json, os, shutil, subprocess
from PIL import ImageFont

FPS = 30
# ---------------- STYLE (SPEC.md "Type" + "Palette"; change here, nowhere else) ----------------
STYLE = dict(
    serif_px=94, sans_px=86, solo_px=128, payoff_px=104,        # sizes that hit Codie's measured x-heights
    max_line_px=760,                                            # Codie: lines never wider than ~760 px (70%)
    min_px_ratio=0.80,                                          # a line may shrink to 80% of its size to fit
    l1_baseline=1561, l2_baseline=1645,                         # chest height on a tight close-up (see SPEC.md)
    solo_baseline=1615, payoff_baselines=(1580, 1680),
    glow="0 0 24px rgba(0,0,0,0.45)",                           # soft dark glow, measured blur ~24 px
    white="#FFFFFF", plate="#0F0A0B",
    cam_b_scale=1.18, cam_b_origin="100% 100%",                 # "camera B": 1.18x, anchored bottom-right
)
FONTS = {  # file, PIL variation weight
    "serif": ("assets/fonts/EBGaramond-VF.ttf", 700),
    "sans": ("assets/fonts/Montserrat-VF.ttf", 300),
    "payoff": ("assets/fonts/EBGaramond-VF.ttf", 500),
    "payoff_i": ("assets/fonts/EBGaramond-Italic-VF.ttf", 500),
}
# ================ CLAUDE CHANGES PER TAKE ================
# The screens plan for the member's take: word indexes refer to assets/words-cut.json (cut.py prints them).
# These are EXAMPLE values from a 17.84 s, 51-word demo cut; they only show the shape. For a real take, write a
# screens.json (same shape) and pass --screens, or replace this block. Nothing else in the file changes per take.
PLAN_EXAMPLE = {
    "screens": [
        {"words": [0, 6], "kind": "pair", "lead": 3},      # serif lead-in (3 words) / light sans line (the rest)
        {"words": [7, 11], "kind": "pair", "lead": 2},
        {"words": [12, 18], "kind": "pair", "lead": 4},
        {"words": [19, 21], "kind": "solo"},               # one big serif emphasis line
        {"words": [22, 26], "kind": "pair", "lead": 3},
        {"words": [27, 31], "kind": "pair", "lead": 2},
        {"words": [32, 38], "kind": "pair", "lead": 3},
        {"words": [39, 40], "kind": "solo"},
        {"words": [41, 44], "kind": "pair", "lead": 2},
        {"words": [45, 46], "kind": "solo"},
        {"words": [47, 50], "kind": "payoff", "split": 2, "italic_from": 2},   # closing line, 2 lines, line 2 italic
    ],
    "camera": [7, 12, 19, 22, 32, 41, 47],                 # A at 0, then alternate B/A on these words' onsets
}
# ================ end of the per-take block ================

ap = argparse.ArgumentParser()
ap.add_argument("--footage", default="assets/cut.mp4")
ap.add_argument("--words", default="assets/words-cut.json")
ap.add_argument("--screens", help="JSON file with {screens, camera}; default = PLAN_EXAMPLE above")
# music isn't shipped: the bed is only added if this file exists (most members add music in the Edits window instead)
ap.add_argument("--music", default="assets/music/your-bed.m4a")
ap.add_argument("--music-start", type=float, default=3.0, help="seconds into the track (skip a silent intro)")
ap.add_argument("--music-volume", type=float, default=0.13, help="bed 16-20 dB under the voice; measure after render")
ap.add_argument("--grade", default="grade-attr.txt", help="file holding the data-color-grading attribute")
a = ap.parse_args()

PLAN = json.load(open(a.screens)) if a.screens else PLAN_EXAMPLE
W = json.load(open(a.words))
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", a.footage],
                           capture_output=True, text=True).stdout)
DUR = round(int(dur * FPS) / FPS, 3)         # clamp to a whole frame at or under the file length
try:
    GRADE = open(a.grade).read().strip()
except FileNotFoundError:
    GRADE = ""

def fr(t):                                     # snap a time to the frame it falls in
    return int(round(t * FPS)) / FPS

def clean(word):                               # Codie: no punctuation except apostrophes, ? and the label colon
    return word.strip().strip(".,!;\"“”")

_ft = {}
def width(kind, text, px):
    path, wght = FONTS[kind]
    if (kind, px) not in _ft:
        f = ImageFont.truetype(path, px)
        f.set_variation_by_axes([wght])
        _ft[(kind, px)] = f
    return _ft[(kind, px)].getlength(text)

def fit(kind, text, px):
    """Largest size <= px that keeps the line inside max_line_px (WHY: Edits/IG crop wide lines; Codie never goes
    past ~70% of the frame). Refuses to shrink below min_px_ratio: re-split the screen instead."""
    size = px
    while width(kind, text, size) > STYLE["max_line_px"] and size > px * STYLE["min_px_ratio"]:
        size -= 2
    if width(kind, text, size) > STYLE["max_line_px"]:
        raise SystemExit(f"line too wide even at {size}px: '{text}' -> split this screen differently")
    return size

def word_spans(idx, hidden=()):
    # (the hidden-style string is built outside the f-string so this runs on Python 3.9 too, e.g. macOS's own python3)
    hid = ' style="opacity:0"'
    return " ".join(f'<span id="w{i}" class="w"{hid if i in hidden else ""}>'
                    f'{html.escape(clean(W[i]["text"]))}</span>' for i in idx)

# ---------------- captions ----------------
screens = PLAN["screens"]
cap_html, cap_js, report = [], [], []
for n, sc in enumerate(screens):
    a0, b0 = sc["words"]
    start = 0.0 if n == 0 else fr(W[a0]["start"])            # frame 0 already shows the first line (thumbnail)
    end = fr(W[screens[n + 1]["words"][0]]["start"]) if n + 1 < len(screens) else DUR
    sid = f"s{n}"
    idx = list(range(a0, b0 + 1))
    if sc["kind"] == "pair":
        lead, rest = idx[:sc["lead"]], idx[sc["lead"]:]
        t1 = " ".join(clean(W[i]["text"]) for i in lead)
        t2 = " ".join(clean(W[i]["text"]) for i in rest)
        p1, p2 = fit("serif", t1, STYLE["serif_px"]), fit("sans", t2, STYLE["sans_px"])
        body = (f'<div class="l1" style="font-size:{p1}px">{html.escape(t1)}</div>'
                f'<div class="l2" style="font-size:{p2}px">{word_spans(rest, rest)}</div>')
        reveal = rest                                          # line 1 cuts on whole; line 2 word by word
        report.append(f"{sid} {start:5.2f}-{end:5.2f} pair  '{t1}' ({p1}px) / '{t2}' ({p2}px)")
    elif sc["kind"] == "solo":
        t = " ".join(clean(W[i]["text"]) for i in idx)
        p = fit("serif", t, STYLE["solo_px"])
        body = f'<div class="solo" style="font-size:{p}px">{word_spans(idx, idx[1:])}</div>'
        reveal = idx[1:]                                       # first word is there on the cut, the rest build
        report.append(f"{sid} {start:5.2f}-{end:5.2f} solo  '{t}' ({p}px)")
    else:  # payoff
        sp, it = sc.get("split", len(idx)), sc.get("italic_from", len(idx))
        lines = [idx[:sp], idx[sp:]] if sp < len(idx) else [idx]
        parts = []
        for k, line in enumerate(lines):
            # italic words share ONE span so the underline runs unbroken under all of them
            plain = [clean(W[i]["text"]) for i in line if idx.index(i) < it]
            ital = [clean(W[i]["text"]) for i in line if idx.index(i) >= it]
            spans = ([f'<span class="pw">{html.escape(" ".join(plain))}</span>'] if plain else []) + \
                    ([f'<span class="pw it">{html.escape(" ".join(ital))}</span>'] if ital else [])
            text = " ".join(clean(W[i]["text"]) for i in line)
            kind = "payoff_i" if line and idx.index(line[0]) >= it else "payoff"
            p = fit(kind, text, STYLE["payoff_px"])
            parts.append(f'<div class="pl pl{k}" style="font-size:{p}px">{" ".join(spans)}</div>')
        body = "".join(parts)
        reveal = []
        report.append(f"{sid} {start:5.2f}-{end:5.2f} payoff '{' / '.join(' '.join(clean(W[i]['text']) for i in l) for l in lines)}'")
        # the one animated entrance: 6-frame horizontal motion-blur slide (~40 px) + opacity, power2.out
        cap_js.append(f'tl.fromTo("#{sid} .pin", {{ x: -40, opacity: 0 }}, {{ x: 0, opacity: 1, duration: 0.2, ease: "power2.out" }}, {start:.3f});')
        cap_js.append(f'tl.fromTo("#hblur", {{ attr: {{ stdDeviation: "14 0" }} }}, {{ attr: {{ stdDeviation: "0 0" }}, duration: 0.2, ease: "power2.out" }}, {start:.3f});')
        body = f'<div class="pin">{body}</div>'
    cap_html.append(f'<div id="{sid}" class="clip cap k-{sc["kind"]}" data-start="{start:.3f}" '
                    f'data-duration="{end - start - 0.004:.3f}" data-track-index="10">{body}</div>')
    # hard swap: the screen dies 4 ms before the next one is born, so rounding can never show two at once
    cap_js.append(f'tl.set("#{sid}", {{ opacity: 0 }}, {end - 0.004:.3f});')
    # word-by-word cut-on: a hard set at each spoken onset (no fade, no pop, no scale)
    for i in reveal:
        cap_js.append(f'tl.set("#w{i}", {{ opacity: 1 }}, {max(start, fr(W[i]["start"])):.3f});')

# ---------------- camera: hard cuts A (1.00) / B (1.18), never eased ----------------
cuts = [0.0] + [fr(W[i]["start"]) for i in PLAN["camera"]]
cam_js = []
for k, t in enumerate(cuts):
    b = k % 2 == 1
    cam_js.append(f'tl.set("#cam", {{ scale: {STYLE["cam_b_scale"] if b else 1} }}, {t:.3f});   // {"B" if b else "A"}')
shots = [round(e - s, 2) for s, e in zip(cuts, cuts[1:] + [DUR])]

CSS = f"""
  @font-face {{ font-family: "EB Garamond"; src: url("assets/fonts/EBGaramond-VF.ttf"); font-weight: 400 800; font-style: normal; }}
  @font-face {{ font-family: "EB Garamond"; src: url("assets/fonts/EBGaramond-Italic-VF.ttf"); font-weight: 400 800; font-style: italic; }}
  @font-face {{ font-family: "Montserrat"; src: url("assets/fonts/Montserrat-VF.ttf"); font-weight: 100 900; }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  html, body {{ width: 1080px; height: 1920px; overflow: hidden; background: %%BG%%; }}
  #cam {{ position: absolute; inset: 0; overflow: hidden; transform-origin: {STYLE["cam_b_origin"]}; }}
  #cam video {{ position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }}
  /* captions: white, soft dark glow, no stroke/highlight/caps. Lines are absolutely placed by BASELINE so a
     member's re-skin only moves two numbers. line-height = font size; the baseline sits ~0.8 em below the top. */
  .cap {{ position: absolute; inset: 0; z-index: 10; overflow: visible; color: {STYLE["white"]};
         text-shadow: {STYLE["glow"]}; text-align: center; }}
  .cap > div, .pin > div {{ position: absolute; left: 0; right: 0; line-height: 1; white-space: nowrap; }}
  .l1 {{ font-family: "EB Garamond"; font-weight: 700; letter-spacing: -0.02em; top: {STYLE["l1_baseline"]}px; transform: translateY(-0.8em); }}
  .l2 {{ font-family: "Montserrat"; font-weight: 300; letter-spacing: -0.01em; top: {STYLE["l2_baseline"]}px; transform: translateY(-0.8em); }}
  .solo {{ font-family: "EB Garamond"; font-weight: 700; letter-spacing: -0.02em; top: {STYLE["solo_baseline"]}px; transform: translateY(-0.8em); }}
  .pin {{ position: absolute; inset: 0; filter: url(#hblurf); }}
  .pl {{ font-family: "EB Garamond"; font-weight: 500; letter-spacing: -0.01em; transform: translateY(-0.8em); }}
  .pl0 {{ top: {STYLE["payoff_baselines"][0]}px; }}  .pl1 {{ top: {STYLE["payoff_baselines"][1]}px; }}
  .it {{ font-style: italic; text-decoration: underline; text-decoration-thickness: 4px; text-underline-offset: 12px; }}
"""

def page(overlay):
    bg = "transparent" if overlay else STYLE["plate"]
    bed = "" if not os.path.exists(a.music) else f"""
    <audio id="bed" class="clip" src="{a.music}" data-media-start="{a.music_start}" data-start="0" data-duration="{DUR}"
           data-volume="{a.music_volume}" data-fade-in="0.02" data-fade-out="0.25" data-track-index="2"></audio>"""
    footage = "" if overlay else f"""
    <div id="cam">
      <video id="a-roll" class="clip" src="{a.footage}" {GRADE} playsinline data-has-audio="true" data-volume="1"
             data-start="0" data-duration="{DUR}" data-track-index="1"></video>
    </div>{bed}"""
    cam = "" if overlay else "\n    ".join(cam_js)
    return f"""<!doctype html>
<html lang="en" data-resolution="portrait">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1080, height=1920" />
<script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
<style>{CSS.replace("%%BG%%", bg)}</style>
</head>
<body>
  <!-- horizontal-only blur for the payoff line's motion-blur entrance -->
  <svg width="0" height="0" style="position:absolute"><filter id="hblurf" x="-20%" y="-50%" width="140%" height="200%">
    <feGaussianBlur id="hblur" in="SourceGraphic" stdDeviation="0 0" /></filter></svg>
  <div id="root" data-composition-id="main" data-start="0" data-duration="{DUR}" data-width="1080" data-height="1920">{footage}
    <div id="captions" data-track-kind="captions">
      {chr(10).join("      " + c for c in cap_html).lstrip()}
    </div>
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
    // ---- camera: A = 1.00, B = {STYLE["cam_b_scale"]} (hard cuts on phrase boundaries) ----
    {cam}
    // ---- captions (generated from {a.words}) ----
    {chr(10).join("    " + j for j in cap_js).lstrip()}
    window.__timelines["main"] = tl;
  </script>
</body>
</html>
"""

open("index.html", "w").write(page(False))
# The overlay is its own HyperFrames project (two root compositions in one folder would both be picked up).
# overlay/assets is a symlink to ../assets so fonts resolve with the same relative paths.
os.makedirs("overlay", exist_ok=True)
if not os.path.exists("overlay/assets"):
    os.symlink("../assets", "overlay/assets")
for f in ("hyperframes.json",):
    shutil.copy(f, "overlay/" + f)
json.dump({"id": "codie-sanchez-overlay", "name": "codie-sanchez-overlay"}, open("overlay/meta.json", "w"))
open("overlay/index.html", "w").write(page(True))
print(f"DUR {DUR}s · {len(screens)} screens · {len(cuts) - 1} cuts · shots {shots}")
print("\n".join(report))
