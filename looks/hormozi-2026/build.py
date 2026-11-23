#!/usr/bin/env python3
"""Builds index.html (or the transparent overlay page) for "Inspired by Hormozi: 2026" (solo-desk format B).
Every number is in SPEC.md.

WHY a generator: HyperFrames captions must be real HTML elements with fixed times, and they come from the word
timings in assets/words-cut.json (made by cut.py). To rebuild the look on a member's take:
    1. edit config.json: footage, keep ranges, speed, hook tag, caption groups + emphasis words, the list card,
       the meter, the punch-in word, optional CTA
    2. $PY transcribe.py   (word stamps, source seconds)
       $PY cut.py          (rough cut + word timings on the cut clock)
    3. python3 build.py                    (writes index.html)
       python3 build.py --overlay          (writes overlay/index.html: tag, captions, card, meter; transparent, for Edits)
    4. npx --yes hyperframes@0.9.83 check --json, snapshot, render (see SPEC.md "How a member's version differs")

Command-line overrides: --footage assets/x.mp4  --words assets/w.json  --hook "TAG TEXT"  --config other.json
"""
import argparse, html, json, os, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
ap = argparse.ArgumentParser()
ap.add_argument("--config", default="config.json")
ap.add_argument("--footage", default="assets/cut.mp4", help="the rough-cut take (output of cut.py)")
ap.add_argument("--words", default="assets/words-cut.json")
ap.add_argument("--hook", default=None, help="the red label tag, 3-4 words")
ap.add_argument("--overlay", action="store_true", help="transparent graphics only -> overlay/index.html")
A = ap.parse_args()
C = json.load(open(A.config))
W = json.load(open(A.words))
TAG = (A.hook or C["hook_tag"]).upper()
OV = A.overlay

DUR = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                            A.footage], capture_output=True, text=True).stdout) - 0.02
def at(i):
    """start of word i on the cut clock"""
    return W[i]["start"] if i else 0.0

# ---------------- style numbers (SPEC.md) ----------------
RED, VIOLET, TRACK = C["hook_colour"], C["meter_colour"], "#E6E6EA"
CAP_Y = C["caption_centre_y"]          # caption line centre (under the chin on a close-up; 940 in a desk framing)
ORIGIN_Y = C["zoom_origin_y"]          # the one punch-in scales around the chin so the face grows up, not into text
KEEP_CASE = set(C.get("keep_case", ["AI", "I"]))   # words that keep their capitals in sentence-case captions

def caption_text(t):
    """sentence case as spoken, no full stops or commas; config "keep_case" words (AI, I...) keep their capitals"""
    t = t.replace(".", "").replace(",", "")
    return t if t in KEEP_CASE or t.isupper() and len(t) > 1 else t.lower()

def captions():
    out = []
    G = C["caption_groups"]
    for g, grp in enumerate(G):
        a, b, emph = grp[0], grp[1], (grp[2] if len(grp) > 2 else None)
        start = at(a) if g else 0.0
        end = at(G[g + 1][0]) if g + 1 < len(G) else DUR
        words = []
        for i in range(a, b + 1):
            t = html.escape(caption_text(W[i]["text"]))
            words.append(f"<b>{t}</b>" if emph is not None and i == emph else t)
        # hard swap: on at its first word, off when the next caption starts. No entrance, no exit, no karaoke.
        out.append(f'<div id="cg{g}" class="clip cap" data-start="{start:.3f}" data-duration="{end - start:.3f}" '
                   f'data-track-index="20" data-layout-allow-safe-zone><span>{" ".join(words)}</span></div>')
    return "\n      ".join(out)

# ---------------- the list card ("redacted document") + meter ----------------
CARD = C["card"]
def card_html():
    rows = [f'<div class="ctitle">{html.escape(CARD["title"])}</div>']
    for r, row in enumerate(CARD["rows"]):
        cls = "row sub" if row.get("sub") else "row"
        num = f'<span class="num">{html.escape(row["num"])}</span>' if row.get("num") else ""
        redacted = row.get("reveal_word") is not None or row.get("hidden")
        bar = f'<i class="bar" id="bar{r}"></i>' if redacted else ''
        # redacted text is meant to be unreadable until its bar clears: tell the layout/contrast checks to skip it
        hide = ' data-layout-ignore' if redacted else ''
        rows.append(f'<div class="{cls}">{num}<span class="txt" id="txt{r}"{hide}>{html.escape(row["text"])}{bar}</span></div>')
    return "\n        ".join(rows)

def card_js():
    js = []
    for r, row in enumerate(CARD["rows"]):
        if row.get("reveal_word") is not None:
            # the black bar wipes off left-to-right in 0.15 s on the spoken word (reads as a hard change at 4 fps)
            t = at(row["reveal_word"])
            js.append(f'tl.to("#bar{r}", {{ scaleX: 0, duration: 0.15, ease: "power2.in" }}, {t:.3f});')
    M = C["meter"]
    js.append(f'tl.set("#mfill", {{ scaleY: {M["from"]} }}, 0);')
    js.append(f'tl.to("#mfill", {{ scaleY: {M["to"]}, duration: 0.3, ease: "power2.out" }}, {at(M["step_word"]):.3f});')
    js.append(f'tl.set("#ml0", {{ opacity: 0 }}, {at(M["step_word"]) + 0.15:.3f});')
    js.append(f'tl.set("#ml1", {{ opacity: 1 }}, {at(M["step_word"]) + 0.15:.3f});')
    return "\n    ".join(js)

PUNCH_T = at(C["punch_word"])          # prop leaves + one hard +15% punch-in on this word
cap_html = captions()
GRADE = open(C["grade"]).read().strip() if os.path.exists(C["grade"]) else ""

cta = C.get("cta")
cta_html = "" if not cta else f"""
    <div id="cta" class="clip" data-start="{DUR - 5:.3f}" data-duration="5" data-track-index="9">
      <div class="ctaline"><span class="kw">{html.escape(cta["line1"])}</span></div>
      <div class="ctasub">{html.escape(cta["line2"])}</div>
    </div>"""

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
  #plate {{ position: absolute; inset: 0; z-index: 0; background: #000000; }}
  #cam {{ position: absolute; inset: 0; z-index: 1; overflow: hidden; transform-origin: 540px {ORIGIN_Y}px; }}
  #cam video {{ position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }}

  /* red label tag: Montserrat 900 italic 53 px caps, white on red, above the head, frame 0 to ~4.5 s, no animation */
  #tag {{ position: absolute; left: 0; right: 0; top: 262px; z-index: 5; text-align: center; }}
  #tag span {{ display: inline-block; background: {RED}; color: #FFFFFF; font: italic 900 53px/1 "Montserrat";
              padding: 16px 26px; border-radius: 10px; letter-spacing: 0; }}

  /* captions: Poppins 72, 400 + one 700 emphasis word, sentence case, one line, white + soft shadow, hard swaps */
  .cap {{ position: absolute; left: 0; right: 0; top: {CAP_Y - 54}px; height: 108px; z-index: 8; text-align: center;
         font: 400 72px/108px "Poppins"; color: #FFFFFF; white-space: nowrap; letter-spacing: -0.005em; }}
  .cap span {{ text-shadow: 0 3px 9px rgba(0,0,0,.5); }}
  .cap b {{ font-weight: 700; }}

  /* the prop: a "redacted" list card that clears point by point + a violet meter beside it */
  #prop {{ position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; z-index: 6; }}
  #card {{ position: absolute; left: {CARD["x"]}px; top: {CARD["y"]}px; width: {CARD["w"]}px; background: #FFFFFF;
          border-radius: 6px; padding: 22px 28px 22px; box-shadow: 0 18px 44px rgba(0,0,0,.45);
          font-family: "Inter"; color: #111114; }}
  .ctitle {{ font: 800 29px/1.15 "Inter"; letter-spacing: -0.01em; margin-bottom: 8px; }}
  .row {{ display: flex; gap: 12px; font: 500 28px/1.27 "Inter"; margin-top: 4px; }}
  .row.sub {{ padding-left: 44px; font-weight: 400; color: #3A3A42; margin-top: 0; }}
  .num {{ font-weight: 800; min-width: 32px; }}
  .txt {{ position: relative; display: inline-block; }}
  .bar {{ position: absolute; left: -2px; right: -4px; top: 5px; bottom: 5px; background: #0B0B0D; transform-origin: 100% 50%; }}
  #meter {{ position: absolute; left: {C["meter"]["x"]}px; top: {CARD["y"] + 40}px; width: 40px; height: {C["meter"]["h"]}px;
           background: {TRACK}; border-radius: 4px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,.35); }}
  #mfill {{ position: absolute; left: 0; right: 0; bottom: 0; height: 100%; background: {VIOLET}; transform-origin: 50% 100%; }}
  #mlabel {{ position: absolute; left: {C["meter"]["x"] - 30}px; width: 100px; top: {CARD["y"] - 2}px; text-align: center;
            font: 700 28px/1 "Poppins"; color: #FFFFFF; text-shadow: 0 2px 8px rgba(0,0,0,.6); height: 28px; }}
  #mlabel span {{ position: absolute; left: 0; right: 0; top: 0; }}
  #ml1 {{ opacity: 0; }}

  /* optional end CTA, native-text style: line 1 on a black box, line 2 plain white */
  #cta {{ position: absolute; left: 0; right: 0; top: 1240px; z-index: 9; text-align: center; font-family: "Inter"; }}
  .ctaline .kw {{ display: inline-block; background: #000000; color: #FFFFFF; font: 600 48px/1.2 "Inter"; padding: 8px 18px; }}
  .ctasub {{ margin-top: 12px; font: 600 44px/1.25 "Inter"; color: #FFFFFF; text-shadow: 0 2px 10px rgba(0,0,0,.6); }}
</style>
</head>
<body>
  <div id="root" data-composition-id="main" data-start="0" data-duration="{DUR:.3f}" data-width="1080" data-height="1920">
    {footage_html}
    <div id="tag" class="clip" data-start="0" data-duration="{C["hook_seconds"]}" data-track-index="4"><span>{html.escape(TAG)}</span></div>

    <div id="prop" class="clip" data-start="0" data-duration="{PUNCH_T:.3f}" data-track-index="6" data-layout-allow-safe-zone>
      <div id="mlabel"><span id="ml0">{html.escape(C["meter"]["label_from"])}</span><span id="ml1">{html.escape(C["meter"]["label_to"])}</span></div>
      <div id="meter"><div id="mfill"></div></div>
      <div id="card">
        {card_html()}
      </div>
    </div>

    <div id="captions" data-track-kind="captions">
      {cap_html}
    </div>
    {cta_html}
  </div>

  <script>
    window.__timelines = window.__timelines || {{}};
    const tl = gsap.timeline({{ paused: true }});
    // ---- camera: locked off, ONE hard punch-in (+15%) when the prop leaves ----
    {"" if OV else f'tl.set("#cam", {{ scale: 1 }}, 0);' + chr(10) + f'    tl.set("#cam", {{ scale: {C["punch_scale"]} }}, {PUNCH_T:.3f});'}
    // ---- prop: card rows clear on their spoken words; the meter steps on its word ----
    {card_js()}
    window.__timelines["main"] = tl;
  </script>
</body>
</html>
"""
# the overlay lives in its own folder: two root compositions in one project make lint fail (and could double audio)
out = "overlay/index.html" if OV else "index.html"
os.makedirs("overlay", exist_ok=True)
open(out, "w").write(page)
print(f"{out} written: {DUR:.2f} s, {len(C['caption_groups'])} captions, prop off + punch-in at {PUNCH_T:.3f} s")
