#!/usr/bin/env python3
"""Builds index.html (the finished reel) and overlays.html (graphics only, transparent) for Green-screen proof.

WHY a generator: captions must be real HTML elements with fixed times (HyperFrames rule) and they come from the word
timings; the page zoom and the red marks come from the measured positions of the real key lines (shots.py). A member's
version = new config.json + `cut.py` + `shots.py` + this, nothing hand-edited. Every number is in SPEC.md.
    $PY build.py && npx --yes hyperframes@0.9.83 check --json
"""
import html, json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_shared"))
import reeltools as rt

C = json.load(open("config.json"))
SHOTS = json.load(open("assets/shots.json"))
DUR = round(rt.duration("assets/cut.mp4") - 0.02, 3)
GRADE = open("grade-attr.txt").read().strip() if os.path.exists("grade-attr.txt") else ""

# ---- words: merge whisper's split "hyper" + "-focus" so a caption never breaks a word ----
raw = json.load(open("assets/words-cut.json"))
W = []
for w in raw:
    if W and w["text"].startswith("-"):
        W[-1]["text"] += w["text"]; W[-1]["end"] = w["end"]
    else:
        W.append(dict(w))


def at(phrase, after=0.0):
    """Start time of the first time `phrase` (one or more words) is spoken at or after `after`.
    Case and punctuation are ignored, so config can say "We can do this" and land on the right "We"."""
    want = [x.strip(".,!?").lower() for x in phrase.split()]
    norm = [w["text"].strip(".,!?").lower() for w in W]
    for i in range(len(W) - len(want) + 1):
        if W[i]["start"] >= after - 1e-6 and norm[i:i + len(want)] == want:
            return W[i]["start"]
    raise SystemExit(f"phrase {phrase!r} not found after {after}")


# ---- layout (1080x1920). Image fills the top ~57%, the speaker's cut-out the bottom ~53% (she overlaps it) ----
SHOT = dict(x=42, y=108, w=996, h=1100, border=6)       # white 6 px frame
IW, IH = SHOT["w"] - 2 * SHOT["border"], SHOT["h"] - 2 * SHOT["border"]   # 984 x 1088 visible page
CUT_SCALE = 0.60                                         # cut-out scale, bottom-centred: head top ~y 1100, chin ~y 1600 (SPEC)
CAP_Y = 1040                                             # caption centre: between the page and her head, inside Instagram's safe band (the format's 1600 landed on the face of the demo take)
RED, YELLOW, PAPER, INK = "#E63946", "#FFF34F", "#F4F1EA", "#000000"   # the LOOK's colours (newsprint + red pen), not brand


def has(p):
    """Media isn't shipped with the template: a missing sound or image is skipped, never a crash."""
    return os.path.exists(p)

# ---- backgrounds: when each one arrives and where its camera sits ----
bgs = []
t = 0.0
for i, b in enumerate(C["backgrounds"]):
    start = 0.0 if i == 0 else at(b["from_word"], t + 0.5)
    shot = SHOTS[b["id"]]
    page_h = round(IW * shot["clip_h_ratio"], 1)
    keys = [{k: q[k] * IW for k in q} for q in shot["key_rects"]]
    mark_t = at(b["mark_word"], start) if b.get("mark_word") else None
    bgs.append(dict(b, start=start, page_h=page_h, keys=keys, mark_t=mark_t))
    t = start
for i, b in enumerate(bgs):
    b["end"] = bgs[i + 1]["start"] if i + 1 < len(bgs) else DUR


def focus(b, s, cy_frac=0.36):
    """Transform (scale s, x, y) that puts the key lines' centre at cy_frac of the visible page, clamped so the page
    always covers the frame (no empty edges)."""
    if not b["keys"]:
        return s, 0, 0
    x0 = min(k["x"] for k in b["keys"]); x1 = max(k["x"] + k["w"] for k in b["keys"])
    y0 = min(k["y"] for k in b["keys"]); y1 = max(k["y"] + k["h"] for k in b["keys"])
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    s = max(1.0, min(s, (IW - 40) / (x1 - x0 + 60)))   # never zoom so far that the key text runs off the page edges
    tx = IW / 2 - cx * s
    ty = IH * cy_frac - cy * s
    tx = min(0, max(IW - IW * s, tx))
    ty = min(0, max(IH - b["page_h"] * s, ty))
    return s, round(tx, 1), round(ty, 1)


def mark_svg(b):
    """Hand-drawn red mark in PAGE coordinates (so it zooms with the page). underline = one stroke under each wrapped
    line of the key text; circle = one loose loop round all of it."""
    paths = []
    if b.get("mark") == "underline":
        for j, k in enumerate(b["keys"]):
            y = k["y"] + k["h"] + 1
            x0, x1 = k["x"] - 2, k["x"] + k["w"] + 4
            wob = 2.2 if j % 2 == 0 else -2.0        # a slight hand wobble, different on each line
            paths.append(f'M{x0:.1f} {y + 1:.1f} C {x0 + (x1 - x0) * .3:.1f} {y - wob:.1f}, {x0 + (x1 - x0) * .7:.1f} {y + wob:.1f}, {x1:.1f} {y - 1:.1f}')
    elif b.get("mark") == "circle-each":
        # one loose pen loop round each wrapped piece of the key text (e.g. "task" | "initiation")
        for k in b["keys"]:
            x0, x1 = k["x"] - 10, k["x"] + k["w"] + 10
            y0, y1 = k["y"] - 6, k["y"] + k["h"] + 6
            mx, my = (x0 + x1) / 2, (y0 + y1) / 2
            paths.append(f'M{mx - 6:.1f} {y0:.1f} C {x1 + 4:.1f} {y0 - 6:.1f}, {x1 + 10:.1f} {y1 + 2:.1f}, {mx:.1f} {y1 + 3:.1f} '
                         f'C {x0 - 8:.1f} {y1 + 4:.1f}, {x0 - 10:.1f} {y0 - 2:.1f}, {mx + 14:.1f} {y0 - 3:.1f}')
    elif b.get("mark") == "circle":
        x0 = min(k["x"] for k in b["keys"]) - 14; x1 = max(k["x"] + k["w"] for k in b["keys"]) + 14
        y0 = min(k["y"] for k in b["keys"]) - 10; y1 = max(k["y"] + k["h"] for k in b["keys"]) + 10
        mx = (x0 + x1) / 2
        # starts top-middle, goes round clockwise and overshoots past its start like a real pen loop
        paths.append(f'M{mx - 40:.1f} {y0 + 4:.1f} C {x1 - 60:.1f} {y0 - 12:.1f}, {x1 + 18:.1f} {y0 + 6:.1f}, {x1 + 6:.1f} {(y0 + y1) / 2:.1f} '
                     f'C {x1 - 4:.1f} {y1 + 14:.1f}, {x0 + 40:.1f} {y1 + 10:.1f}, {x0 - 4:.1f} {(y0 + y1) / 2 + 6:.1f} '
                     f'C {x0 - 10:.1f} {y0 + 8:.1f}, {mx - 120:.1f} {y0 - 14:.1f}, {mx + 30:.1f} {y0 - 6:.1f}')
    out = "".join(f'<path id="{b["id"]}-m{j}" d="{p}" />' for j, p in enumerate(paths))
    return f'<svg class="mark" viewBox="0 0 {IW} {b["page_h"]}" style="height:{b["page_h"]}px">{out}</svg>', len(paths)


# ---- caption groups: 2-3 words, break after punctuation (style: "2-3 words") ----
def groups():
    gs, cur = [], []
    for i, w in enumerate(W):
        cur.append(i)
        punct = w["text"][-1] in ".,!?"
        if len(cur) == 3 or punct or (len(cur) == 2 and i + 1 < len(W) and len(W[i + 1]["text"]) > 9):
            gs.append(cur); cur = []
    if cur:
        gs.append(cur)
    return gs


GROUPS = groups()


def captions():
    out, js = [], []
    for g, idx in enumerate(GROUPS):
        a, b = idx[0], idx[-1]
        start = max(0.1, W[a]["start"] - 0.04)
        end = (W[GROUPS[g + 1][0]]["start"] - 0.04) if g + 1 < len(GROUPS) else min(DUR - 0.02, W[b]["end"] + 0.4)
        end = min(end, DUR - 0.02)
        text = " ".join(html.escape(W[i]["text"]) for i in idx)
        out.append(f'<div id="cg{g}" class="clip capgroup" data-start="{start:.3f}" data-duration="{end - start:.3f}" '
                   f'data-track-index="20"><span class="cbox">{text}</span></div>')
        js.append(f'tl.fromTo("#cg{g} .cbox", {{ scale: 0.92, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.1, ease: "power3.out" }}, {start:.3f});')
    return "\n      ".join(out), "\n    ".join(js)


cap_html, cap_js = captions()

# ---- sound: peak lands one frame after the picture (rt.sfx_start measures each file) ----
B2, B3 = bgs[1], bgs[2]
SFX = [  # id, file, picture moment, duration, volume, media offset
    ("sfx-bg2", "soft-whoosh-1.mp3", B2["start"] + 0.12, 1.0, 0.61, 0.0),
    ("sfx-mark2", "marker.mp3", B2["mark_t"] + 0.50, 0.5, 1.78, 0.0),
    ("sfx-bg3", "soft-whoosh-2.mp3", B3["start"] + 0.12, 0.8, 0.51, 0.0),
    ("sfx-mark3", "pen-writing.mp3", B3["mark_t"] + 0.55, 0.62, 3.0, 2.40),
]
sfx_rows = []
for n, (i, f, pic, d, v, ms) in enumerate(SFX):
    if not has(f"assets/sfx/{f}"):
        print(f"skipped sound {f}: not in assets/sfx/ (add it there, or add it in Edits)")
        continue
    if ms:   # a slice of a longer scribble: measure the peak inside the slice
        env = [e for e in rt.envelope(f"assets/sfx/{f}", ms, ms + d, hop=0.01)]
        peak = max(env, key=lambda x: x[1])[0] - ms
        s = round(pic + rt.FRAME - peak, 3)
    else:
        s = rt.sfx_start(pic, f"assets/sfx/{f}")
    sfx_rows.append(f'<audio id="{i}" class="clip" src="assets/sfx/{f}" data-start="{s:.3f}" data-duration="{d}" '
                    + (f'data-media-start="{ms}" ' if ms else "") +
                    f'data-volume="{v}" data-fade-out="0.1" data-track-index="{30 + n}"></audio>')
sfx_html = "\n    ".join(sfx_rows)


def page(overlay=False):
    """overlay=True: graphics only (hook, source chip, captions) on transparent; no page, no person, no sound."""
    pages, page_js = [], []
    for k, b in enumerate(bgs):
        svg, npaths = mark_svg(b)
        pages.append(f'''<div id="{b["id"]}" class="clip pg" data-start="{b["start"]:.3f}" data-duration="{b["end"] - b["start"]:.3f}" data-track-index="{2 + k}">
          <div class="slide" id="{b["id"]}-in"><div class="cam" id="{b["id"]}-cam"><img src="assets/{b["id"]}.png" alt="{html.escape(C["source_site"])} page" />{svg}</div></div>
        </div>''')
        cam = f'#{b["id"]}-cam'
        s0, x0, y0 = (1, 0, 0) if k == 0 else focus(b, 1.0, 0.30)
        page_js.append(f'tl.set("{cam}", {{ scale: {s0}, x: {x0}, y: {y0} }}, 0);')
        if k > 0:  # arrives like a fast scroll: up from below with motion blur, lands sharp
            page_js.append(f'tl.fromTo("#{b["id"]}-in", {{ y: 420, opacity: 0, filter: "blur(14px)" }}, {{ y: 0, opacity: 1, filter: "blur(0px)", duration: 0.38, ease: "power4.out" }}, {b["start"]:.3f});')
        if b["mark_t"] is not None:
            s1, x1, y1 = focus(b, 1.22 if b["mark"] == "circle" else 1.42, 0.40)
            # camera moves onto the key line as she starts the words it backs up
            page_js.append(f'tl.to("{cam}", {{ scale: {s1}, x: {x1}, y: {y1}, duration: 0.55, ease: "power2.inOut" }}, {b["mark_t"] - 0.1:.3f});')
            per = {"underline": 0.42 / max(1, npaths), "circle-each": 0.3}.get(b["mark"], 0.55)
            for j in range(npaths):
                page_js.append(f'tl.fromTo("#{b["id"]}-m{j}", {{ strokeDasharray: 2600, strokeDashoffset: 2600 }}, {{ strokeDashoffset: 0, duration: {per:.2f}, ease: "power2.inOut" }}, {b["mark_t"] + 0.5 + j * per:.3f});')
    # bg3: pull back out on config "pullback_word" so the section heading shows again (mark stays); punch on her
    # on "punch_word", released on "punch_end_word" (any of them null = that move is skipped)
    if C.get("pullback_word"):
        AND = at(C["pullback_word"], B3["mark_t"])
        s2, x2, y2 = focus(B3, 1.0, 0.30)
        page_js.append(f'tl.to("#bg3-cam", {{ scale: 1.0, x: 0, y: {min(0, y2)}, duration: 0.5, ease: "power2.inOut" }}, {AND - 0.05:.3f});')
    TENX = at(C["punch_word"]) if C.get("punch_word") else None
    LIKE = at(C["punch_end_word"], TENX) if (TENX is not None and C.get("punch_end_word")) else None
    punch_js = ""
    if TENX is not None:
        punch_js = f'tl.set("#me", {{ scale: 1.07 }}, {TENX:.3f});          // punch on the stressed word'
        if LIKE is not None:
            punch_js += f'\n    tl.set("#me", {{ scale: 1 }}, {LIKE:.3f});'
    pages_html = "\n        ".join(p for k, p in enumerate(pages) if has(f"assets/{bgs[k]['id']}.png"))

    body_layers = "" if overlay else f'''
    <div id="paper" class="clip" data-start="0" data-duration="{DUR}" data-track-index="0"></div>
    <div id="shot">
        {pages_html}
    </div>
    <div id="me">
      <video id="cutout" class="clip" src="assets/cutout.webm" {GRADE} muted playsinline data-layout-allow-occlusion
             data-start="0" data-duration="{DUR}" data-track-index="10"></video>
    </div>
    <audio id="voice" class="clip" src="assets/voice.wav" data-start="0" data-duration="{DUR}" data-volume="1" data-track-index="11"></audio>
    {sfx_html}'''
    me_js = "" if overlay else f'''
    tl.set("#me", {{ scale: 1 }}, 0);
    {punch_js}
    {chr(10).join("    " + x for x in page_js)}'''
    hook_end = 3.0
    return f"""<!doctype html>
<html lang="en" data-resolution="portrait">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1080, height=1920" />
<script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
<style>
  @font-face {{ font-family: "Space Grotesk"; src: url("assets/fonts/SpaceGrotesk.ttf"); font-weight: 300 700; }}
  @font-face {{ font-family: "Space Mono"; src: url("assets/fonts/SpaceMono-Regular.ttf"); font-weight: 400; }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  html, body {{ width: 1080px; height: 1920px; overflow: hidden; background: {"transparent" if overlay else PAPER}; }}
  #paper {{ position: absolute; inset: 0; background: {PAPER}; }}
  /* the proof: the real page in a white 6 px frame */
  #shot {{ position: absolute; left: {SHOT["x"]}px; top: {SHOT["y"]}px; width: {SHOT["w"]}px; height: {SHOT["h"]}px; z-index: 2;
          border: {SHOT["border"]}px solid #FFFFFF; background: #FFFFFF; overflow: hidden;
          box-shadow: 0 30px 70px rgba(0,0,0,.28), 0 4px 12px rgba(0,0,0,.14); }}
  .pg {{ position: absolute; left: 0; top: 0; width: {IW}px; height: {IH}px; overflow: hidden; background: #FFFFFF; }}
  .slide {{ position: absolute; inset: 0; }}
  .cam {{ position: absolute; left: 0; top: 0; width: {IW}px; transform-origin: 0 0; }}
  .cam img {{ display: block; width: {IW}px; }}
  .mark {{ position: absolute; left: 0; top: 0; width: {IW}px; overflow: visible; }}
  .mark path {{ fill: none; stroke: {RED}; stroke-width: 4.5; stroke-linecap: round; stroke-linejoin: round; }}
  /* the speaker, cut out, in front of the page */
  #me {{ position: absolute; inset: 0; z-index: 5; transform-origin: 50% 100%; }}
  #cutout {{ position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; object-fit: cover;
            transform: translate(0px, {1920 * (1 - CUT_SCALE) / 1:.0f}px) scale({CUT_SCALE}); transform-origin: 50% 0%; }}
  /* hook: black on a highlighter stripe, square ends, -1 deg */
  #hook {{ position: absolute; left: 0; right: 0; top: 292px; z-index: 8; text-align: center; }}
  #hook .line {{ display: table; margin: 0 auto 10px; }}
  #hook .line span {{ display: inline-block; background: {YELLOW}; color: {INK}; font: 700 60px/1.12 "Space Grotesk";
                     letter-spacing: -0.01em; padding: 6px 22px 10px; }}
  /* source chip, under the image */
  #chip {{ position: absolute; left: {SHOT["x"]}px; top: {SHOT["y"] + SHOT["h"] + 14}px; z-index: 8; font: 400 28px/1 "Space Mono";
          color: #FFFFFF; background: rgba(0,0,0,.7); padding: 9px 14px; border-radius: 4px; }}
  /* captions: white on a black box, radius 6 */
  .capgroup {{ position: absolute; left: 0; right: 0; top: {CAP_Y - 40}px; text-align: center; z-index: 9; overflow: visible; }}
  .cbox {{ display: inline-block; font: 700 52px/1.15 "Space Grotesk"; color: #FFFFFF; background: {INK};
          padding: 8px 18px 12px; border-radius: 6px; letter-spacing: -0.005em; }}
</style>
</head>
<body>
  <div id="root" data-composition-id="main" data-start="0" data-duration="{DUR}" data-width="1080" data-height="1920">
    {body_layers}

    <div id="hook" class="clip" data-start="0" data-duration="{hook_end:.2f}" data-track-index="12">
      <div class="line" id="hl0"><span>{html.escape(C["hook_lines"][0])}</span></div>
      <div class="line" id="hl1"><span>{html.escape(C["hook_lines"][1])}</span></div>
    </div>
    <div id="chip" class="clip" data-start="0" data-duration="{DUR}" data-track-index="13">Source: {html.escape(C["source_site"])}</div>

    <div id="captions" data-track-kind="captions">
      {cap_html}
    </div>
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
    {me_js}

    // hook: frame 0 already shows it (thumbnail); it leaves as a marker wipe to the right, line by line
    tl.fromTo("#hl0", {{ scale: 1.04, rotation: -1 }}, {{ scale: 1, rotation: -1, duration: 0.3, ease: "expo.out" }}, 0);
    tl.fromTo("#hl1", {{ scale: 1.04, rotation: -1 }}, {{ scale: 1, rotation: -1, duration: 0.3, ease: "expo.out" }}, 0.05);
    tl.to("#hl0 span", {{ clipPath: "inset(0 0 0 100%)", duration: 0.2, ease: "power3.in" }}, {hook_end - 0.3:.2f});
    tl.to("#hl1 span", {{ clipPath: "inset(0 0 0 100%)", duration: 0.2, ease: "power3.in" }}, {hook_end - 0.24:.2f});

    // captions (generated from assets/words-cut.json)
    {cap_js}

    window.__timelines["main"] = tl;
  </script>
</body>
</html>
"""


open("index.html", "w").write(page(False))
rt.write_overlays(page(True))
print(f"index.html + overlays/index.html: {DUR}s, {len(GROUPS)} caption groups, {len(SFX)} sounds; backgrounds at",
      [round(b["start"], 2) for b in bgs], "marks at", [b["mark_t"] for b in bgs])
