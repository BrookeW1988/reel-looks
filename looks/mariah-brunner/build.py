#!/usr/bin/env python3
"""Builds the "inspired by Mariah Brunner" reel as HyperFrames HTML (see SPEC.md for every number used here).

WHY a generator: captions must be real timed HTML elements, and every graphic is anchored to a spoken word. Keeping the
cues in reel.json (by word index) means a member's version is: new footage + new words file + new cue list, re-run.

    python3 build.py                         # index.html  (footage + graphics + captions + sounds)
    python3 build.py --overlays              # overlays/index.html (graphics + captions + sounds, NO footage, transparent)
                                             # render: npx hyperframes render overlays --format mov -o renders/<name>-overlays.mov
    python3 build.py --config my-reel.json --footage assets/my-cut.mp4 --words assets/my-words.json
then:  npx hyperframes check --json  ->  snapshot  ->  render

Style tokens (palette, type, motion) live in the STYLE block below; cues live in reel.json.
"""
import argparse, html, json, os, re, subprocess

ap = argparse.ArgumentParser()
ap.add_argument("--config", default="reel.json")
ap.add_argument("--footage", help="overrides reel.json 'footage'")
ap.add_argument("--words", help="overrides reel.json 'words'")
ap.add_argument("--overlays", action="store_true", help="write overlays/index.html: footage + background hidden, for Edits")
a = ap.parse_args()
C = json.load(open(a.config))
FOOTAGE = a.footage or C["footage"]
W = json.load(open(a.words or C["words"]))

# ---------------- STYLE (SPEC.md: Palette / Type / Motion) ----------------
YELLOW, WHITE, INK = "#F8F098", "#FFFFFF", "#0C0C0E"
COLOURS = {"yellow": YELLOW, "white": WHITE, "ink": INK}
SHADOW_CARD = "16px 20px 16px rgba(0,0,0,.35)"            # [B] alpha 90/255, blur 16, offset 16/20
POP_DUR, POP_FROM, POP_EASE = 0.33, 0.78, "back.out(1.7)"  # [B] 0.78 -> overshoot -> 1.0 in 0.32-0.35 s
BLUR_IN = 0.23                                            # [B] blur 8 -> 0 over the first ~70% of the pop
EXIT_DUR = 0.18                                           # ours (GAP in the spec): ~45% shorter than the entrance

dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", FOOTAGE],
                           capture_output=True, text=True).stdout)
DUR = round(dur - 0.01, 3)       # clamp just under the file so the last frame is never black

def has(p):
    """Screenshots, logos, GIFs, emojis and SFX are the member's own files and aren't shipped: a cue whose file is
    missing is skipped (with a note), never a crash."""
    if p and os.path.exists(p):
        return True
    print(f"  skipped (file not found): {p}")
    return False

def T(x):
    """'w12' -> start of word 12; 'w12+0.1' / 'w12-0.2' offsets; 'end' -> reel end; numbers pass through."""
    if isinstance(x, (int, float)):
        return float(x)
    if x == "end":
        return DUR
    m = re.fullmatch(r"w(\d+)([+-][\d.]+)?", x)
    return round(W[int(m.group(1))]["start"] + float(m.group(2) or 0), 3)

js = []          # GSAP lines, in order
def J(s): js.append(s)

def pop_in(sel, t, scale_from=POP_FROM, rot=None):
    """The house pop: scale overshoot + blur 8 -> 0 + quick opacity. Opacity never bounces, so it is its own tween."""
    r = f", rotation: {rot}" if rot is not None else ""
    J(f'tl.fromTo("{sel}", {{ scale: {scale_from}{r} }}, {{ scale: 1{r}, duration: {POP_DUR}, ease: "{POP_EASE}" }}, {t:.3f});')
    J(f'tl.fromTo("{sel}", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.1, ease: "power2.out" }}, {t:.3f});')
    J(f'tl.fromTo("{sel}", {{ filter: "blur(8px)" }}, {{ filter: "blur(0px)", duration: {BLUR_IN}, ease: "power2.out" }}, {t:.3f});')

def pop_out(sel, t, how="shrink"):
    moves = {"shrink": "scale: 0.9", "up": "y: -70", "down": "y: 90", "right": "x: 900, rotation: 8"}
    d = 0.26 if how == "right" else EXIT_DUR
    blur = 14 if how == "right" else 6
    J(f'tl.to("{sel}", {{ {moves[how]}, opacity: 0, filter: "blur({blur}px)", duration: {d}, ease: "power3.in" }}, {t - d:.3f});')

body, css_extra = [], []
track = [10]
def tr():
    track[0] += 1
    return track[0]

def text_layer(text, colour, size, weight=900):
    # ink stroke + soft shadow: the demo take's top third was a BRIGHT window, so yellow needs an outline to read (SPEC).
    return (f'<span class="pop" style="color:{COLOURS[colour]};font-size:{size}px;font-weight:{weight}">'
            f'{html.escape(text)}</span>')

# ---------------- hook (frame 0 = already on screen) ----------------
H = C["hook"]
h_out = T(H["out"])
lines = "".join(f'<div class="hl" id="hl{i}">{text_layer(l["text"], l["color"], H["size"])}</div>'
                for i, l in enumerate(H["lines"]))
body.append(f'<div id="hook" class="clip" style="left:{H["x"]}px;top:{H["y"]}px" data-start="0" '
            f'data-duration="{h_out:.3f}" data-track-index="{tr()}">{lines}</div>')
J('tl.fromTo("#hook", { scale: 1.04 }, { scale: 1, duration: 0.35, ease: "expo.out" }, 0);')  # settles; never empty
for i in range(len(H["lines"])):
    J(f'tl.to("#hl{i}", {{ opacity: 0, filter: "blur(8px)", duration: 0.13, ease: "power2.in" }}, {h_out - 0.2 + i * 0.03:.3f});')

# ---------------- logo tiles (receipt: the real logo of the thing named) ----------------
for tl_ in [t for t in C.get("tiles", []) if has(t["src"])]:
    t0, t1 = T(tl_["at"]), T(tl_["out"])
    s = tl_["size"]
    body.append(f'<div id="{tl_["id"]}" class="clip tile" style="left:{tl_["x"]}px;top:{tl_["y"]}px;width:{s}px;height:{s}px" '
                f'data-start="{t0:.3f}" data-duration="{t1 - t0:.3f}" data-track-index="{tr()}">'
                f'<img src="{tl_["src"]}" alt="" /></div>')
    pop_in(f'#{tl_["id"]}', t0, rot=tl_["rot"])
    J(f'tl.to("#{tl_["id"]}", {{ opacity: 0, scale: 0.9, filter: "blur(6px)", duration: 0.13, ease: "power2.in" }}, {t1 - 0.14:.3f});')

# ---------------- screenshot cards (real screenshots, white frame, soft shadow) ----------------
for c in [c for c in C.get("cards", []) if has(c["src"])]:
    t0, t1 = T(c["at"]), T(c["out"])
    hl = ""
    for k, (x, y, w, h) in enumerate(c.get("highlights", [])):
        hl += f'<div class="hilite" id="{c["id"]}-hl{k}" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px"></div>'
    body.append(f'<div id="{c["id"]}" class="clip card" style="left:{c["x"]}px;top:{c["y"]}px;width:{c["w"]}px" '
                f'data-start="{t0:.3f}" data-duration="{t1 - t0:.3f}" data-track-index="{tr()}">'
                f'<img src="{c["src"]}" alt="" />{hl}</div>')
    pop_in(f'#{c["id"]}', t0, rot=c["rot"])
    for k in range(len(c.get("highlights", []))):
        J(f'tl.fromTo("#{c["id"]}-hl{k}", {{ scaleX: 0 }}, {{ scaleX: 1, duration: 0.22, ease: "power2.out" }}, '
          f'{T(c["highlight_at"]) + k * 0.09:.3f});')
    pop_out(f'#{c["id"]}', t1, c.get("exit", "shrink"))

# ---------------- reaction GIFs (video clip timed; its frame wrapper animated) ----------------
for g in [g for g in C.get("gifs", []) if has(g["src"])]:
    t0, t1 = T(g["at"]), T(g["out"])
    body.append(f'<div id="{g["id"]}" class="gif" style="left:{g["x"]}px;top:{g["y"]}px;width:{g["w"]}px;height:{g["h"]}px">'
                f'<video id="{g["id"]}-v" class="clip" src="{g["src"]}" muted playsinline data-start="{t0:.3f}" '
                f'data-duration="{t1 - t0:.3f}" data-track-index="{tr()}"></video></div>')
    J(f'tl.set("#{g["id"]}", {{ opacity: 0 }}, 0);')
    pop_in(f'#{g["id"]}', t0, rot=g["rot"])
    # [B] slow drift while held: +3% scale, rotation -1.25 -> +1.25 deg, linear across the hold (not a loop)
    J(f'tl.fromTo("#{g["id"]} video", {{ scale: 1, rotation: -1.25 }}, {{ scale: 1.03, rotation: 1.25, duration: {t1 - t0:.3f}, ease: "none" }}, {t0:.3f});')
    J(f'tl.to("#{g["id"]}", {{ opacity: 0, scale: 0.9, filter: "blur(6px)", duration: {EXIT_DUR}, ease: "power3.in" }}, {t1 - EXIT_DUR - 0.02:.3f});')

# ---------------- keyword stacks (words pop on as spoken, staggered round the head) ----------------
for st in C.get("stacks", []):
    t1 = T(st["out"])
    first = min(T(w["at"]) for w in st["words"])
    parts = []
    for k, w in enumerate(st["words"]):
        parts.append(f'<div class="kw" id="{st["id"]}-{k}" style="left:{w["x"]}px;top:{w["y"]}px">'
                     f'{text_layer(w["text"], w["color"], w["size"])}</div>')
    e = st.get("emoji")
    if e and not has(e["src"]):
        e = None
    if e:
        parts.append(f'<img class="emoji" id="{st["id"]}-em" src="{e["src"]}" alt="" '
                     f'style="left:{e["x"]}px;top:{e["y"]}px;width:{e["size"]}px;height:{e["size"]}px" />')
    body.append(f'<div id="{st["id"]}" class="clip stack" data-start="{first - 0.02:.3f}" '
                f'data-duration="{t1 - first + 0.02:.3f}" data-track-index="{tr()}" data-layout-allow-overlap>{"".join(parts)}</div>')
    for k, w in enumerate(st["words"]):
        J(f'tl.set("#{st["id"]}-{k}", {{ opacity: 0 }}, 0);')
        pop_in(f'#{st["id"]}-{k}', T(w["at"]), scale_from=0.7)
    if e:
        J(f'tl.set("#{st["id"]}-em", {{ opacity: 0 }}, 0);')
        pop_in(f'#{st["id"]}-em', T(e["at"]), scale_from=0.5, rot=e["rot"])
    if st["out"] != "end":   # leave word by word, 30 ms apart (blur swap, no slide)
        for k in range(len(st["words"])):
            J(f'tl.to("#{st["id"]}-{k}", {{ opacity: 0, filter: "blur(8px)", duration: 0.13, ease: "power2.in" }}, {t1 - 0.16 + k * 0.03:.3f});')
        if e:
            J(f'tl.to("#{st["id"]}-em", {{ opacity: 0, scale: 0.6, duration: 0.13, ease: "power2.in" }}, {t1 - 0.16:.3f});')

# ---------------- numbered card (label system): lavender card, number counts up ----------------
N = C.get("numcard")
if N:
    t0, t1 = T(N["at"]), T(N["out"])
    body.append(f'<div id="{N["id"]}" class="clip numcard" style="left:{N["x"]}px;top:{N["y"]}px;width:{N["w"]}px;height:{N["h"]}px" '
                f'data-start="{t0:.3f}" data-duration="{t1 - t0:.3f}" data-track-index="{tr()}">'
                f'<div class="numrow"><span class="num" id="{N["id"]}-n">0</span><span class="numlabel">{html.escape(N["label"])}</span></div>'
                f'<div class="pill" id="{N["id"]}-pill">{html.escape(N["pill"])}</div></div>')
    pop_in(f'#{N["id"]}', t0, rot=-1.5)
    J(f'const cnt = {{ v: 0 }};')
    J(f'tl.fromTo(cnt, {{ v: 0 }}, {{ v: {N["number"]}, duration: 0.55, ease: "power2.out", onUpdate: () => '
      f'{{ document.querySelector("#{N["id"]}-n").textContent = Math.round(cnt.v).toLocaleString("en-AU"); }} }}, {t0 + 0.05:.3f});')
    J(f'tl.set("#{N["id"]}-pill", {{ opacity: 0 }}, 0);')
    pop_in(f'#{N["id"]}-pill', T(N["pill_at"]), scale_from=0.8)
    pop_out(f'#{N["id"]}', t1, "right")

# ---------------- camera: hard punches only (gsap.set), never a creeping zoom ----------------
for cam in C.get("camera", []):
    J(f'tl.set("#cam", {{ scale: {cam["scale"]} }}, {T(cam["at"]):.3f});')

# ---------------- captions: ONE word at a time, the speaker's words, lower case as spoken ----------------
def cap_text(t):
    t = t.strip().strip(".,!?;:")
    return t if t.upper() in C["keep_case"] else t.lower()

caps, n = [], len(W)
for i, w in enumerate(W):
    s = max(0.1, w["start"])
    nxt = W[i + 1]["start"] if i + 1 < n else None
    # hold to the next word; across a pause > 0.35 s hold only 0.25 s past this word's end
    e = nxt if (nxt is not None and nxt - w["end"] <= 0.35) else min(w["end"] + 0.25, nxt or DUR, DUR)
    e = min(e, DUR)
    caps.append(f'<div id="c{i}" class="clip cap" data-start="{s:.3f}" data-duration="{e - s:.3f}" data-track-index="90" data-layout-allow-safe-zone>'
                f'<span>{html.escape(cap_text(w["text"]))}</span></div>')
    J(f'tl.fromTo("#c{i} span", {{ scale: 0.86 }}, {{ scale: 1, duration: 0.1, ease: "expo.out" }}, {s:.3f});')

# ---------------- sound: start = picture moment + 1 frame - the file's measured peak ----------------
sfx = []
for k, f in enumerate([f for f in C.get("sfx", []) if has(f"assets/sfx/{f['file']}")]):
    st_ = max(0.0, T(f["at"]) + 1 / 30 - f["peak"])
    sfx.append(f'<audio id="sfx{k}" class="clip" src="assets/sfx/{f["file"]}" data-start="{st_:.3f}" data-duration="{f["dur"]}" '
               f'data-volume="{f["vol"]}" data-fade-out="0.08" data-track-index="{40 + k}"></audio>')

CID = "overlays" if a.overlays else "main"
GRADE = open("grade-attr.txt").read().strip() if not a.overlays else ""
cy = C["caption_y"]

footage = "" if a.overlays else f"""
    <div id="plate" class="clip" data-start="0" data-duration="{DUR}" data-track-index="0"></div>
    <div id="cam">
      <video id="a-roll" class="clip" src="{FOOTAGE}" {GRADE} playsinline data-has-audio="true" data-volume="1"
             data-start="0" data-duration="{DUR}" data-track-index="1"></video>
    </div>"""

page = f"""<!doctype html>
<html lang="en" data-resolution="portrait">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1080, height=1920" />
<script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  html, body {{ width: 1080px; height: 1920px; overflow: hidden; background: {"transparent" if a.overlays else INK}; }}
  body {{ font-family: "Inter", sans-serif; }}
  #plate {{ position: absolute; inset: 0; z-index: 0; background: {INK}; }}
  #cam {{ position: absolute; inset: 0; z-index: 1; overflow: hidden; transform-origin: 660px 1000px; }}
  #cam video {{ position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }}

  /* text pops: Inter Black, ink outline drawn under the fill, soft dark drop shadow, no box */
  .pop {{ display: inline-block; line-height: 1.02; letter-spacing: -0.02em; white-space: nowrap;
         -webkit-text-stroke: 9px {INK}; paint-order: stroke fill; text-shadow: 0 8px 22px rgba(0,0,0,.35); }}
  #hook {{ position: absolute; z-index: 6; transform-origin: 0 0; }}
  .hl {{ display: block; }}
  .stack {{ position: absolute; inset: 0; z-index: 6; }}
  .kw {{ position: absolute; transform-origin: 50% 60%; }}
  .emoji {{ position: absolute; filter: drop-shadow(10px 14px 12px rgba(0,0,0,.3)); }}

  /* receipts */
  .tile {{ position: absolute; z-index: 7; background: {WHITE}; border-radius: 40px; box-shadow: {SHADOW_CARD};
          display: grid; place-items: center; }}
  .tile img {{ width: 62%; height: 62%; }}
  .card {{ position: absolute; z-index: 7; background: {WHITE}; padding: 4px; border-radius: 22px; box-shadow: {SHADOW_CARD}; }}
  .card img {{ display: block; width: 100%; border-radius: 18px; }}
  .hilite {{ position: absolute; background: {YELLOW}; mix-blend-mode: multiply; border-radius: 6px; transform-origin: 0 50%;
            margin: 4px 0 0 4px; }}
  .gif {{ position: absolute; z-index: 7; background: {WHITE}; padding: 4px; border-radius: 22px; box-shadow: {SHADOW_CARD};
         overflow: hidden; }}
  .gif video {{ position: absolute; inset: 4px; width: calc(100% - 8px); height: calc(100% - 8px); object-fit: cover; border-radius: 18px; }}

  /* numbered card: lavender -> white (hex is OUR pick; the spec marks it a GAP) */
  .numcard {{ position: absolute; z-index: 7; border-radius: 36px; padding: 30px 40px; box-shadow: {SHADOW_CARD};
             background: linear-gradient(160deg, #DCD3FA 0%, #EEE9FD 55%, #FFFFFF 100%); border: 4px solid {WHITE}; }}
  .numrow {{ display: flex; align-items: baseline; gap: 22px; color: {INK}; }}
  .num {{ font: 900 160px/0.95 "Inter"; letter-spacing: -0.04em; }}
  .numlabel {{ font: 900 64px/1 "Inter"; letter-spacing: -0.02em; }}
  .pill {{ display: inline-block; margin-top: 18px; background: {YELLOW}; color: {INK}; font: 900 38px/1 "Inter"; white-space: nowrap;
          padding: 14px 24px; border-radius: 999px; border: 4px solid {INK}; transform-origin: 0 50%; }}

  /* captions: one word, white, no box, soft shadow; centred under the chin */
  .cap {{ position: absolute; left: 0; right: 0; top: {cy - 50}px; z-index: 9; text-align: center; overflow: visible; }}
  .cap span {{ display: inline-block; font: 800 80px/1.25 "Inter"; letter-spacing: -0.015em; color: {WHITE};
              text-shadow: 0 4px 16px rgba(0,0,0,.6), 0 0 3px rgba(0,0,0,.45); }}
</style>
</head>
<body>
  <div id="root" data-composition-id="{CID}" data-start="0" data-duration="{DUR}" data-width="1080" data-height="1920">{footage}

    {chr(10).join("    " + b for b in body)}

    <div id="captions" data-track-kind="captions">
      {(chr(10) + "      ").join(caps)}
    </div>

    {(chr(10) + "    ").join(sfx)}
  </div>

  <script>
    const tl = gsap.timeline({{ paused: true }});
    {"tl.set('#cam', { scale: 1 }, 0);" if not a.overlays else ""}
    {(chr(10) + "    ").join(j for j in js if not (a.overlays and '"#cam"' in j))}
    window.__timelines["{CID}"] = tl;
  </script>
</body>
</html>
"""
if a.overlays:
    # A second root file next to index.html makes HyperFrames see two entry points (and can double the audio), so the
    # overlay version is its own tiny project: overlays/index.html, sharing this folder's assets through a link.
    import os, shutil
    os.makedirs("overlays", exist_ok=True)
    if not os.path.lexists("overlays/assets"):
        os.symlink("../assets", "overlays/assets")
    shutil.copy("hyperframes.json", "overlays/hyperframes.json")
    out = "overlays/index.html"
else:
    out = "index.html"
open(out, "w").write(page)
print(f"{out}: {DUR} s, {len(caps)} caption words, {len(sfx)} sounds, {len(body)} graphic layers")
