#!/usr/bin/env python3
"""Builds index.html (the reel) and overlays/index.html (graphics only, transparent, for Edits' addOverlay) for
Pop-up proof. Every number is in SPEC.md; everything a member changes is in reel.json.

    $PY cut.py      # once per take: assets/cut.mp4 + word timings
    $PY build.py && npx --yes hyperframes@0.9.83 check --json

WHY a generator: captions must be real HTML elements with fixed times (HyperFrames rule) and they come from the
word timings in assets/words-cut.json. Moments are spoken phrases from reel.json, not seconds, so a new take
re-times itself. Proof cards show the member's OWN screenshots: the look never invents or mocks up proof.
"""
import array, html, json, os, re, subprocess, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_shared"))
import reeltools as rt

C = json.load(open("reel.json"))
W = json.load(open("assets/words-cut.json"))
DUR = round(rt.duration("assets/cut.mp4") - 0.01, 2)   # just under the cut's length so the last frame is never black
FRAME = 1 / 30
GRADE = open("grade-attr.txt").read().strip() if os.path.exists("grade-attr.txt") else ""   # the look's grade (SPEC.md)
KEYWORDS = {k.lower() for k in C.get("keywords", [])}   # these get a slightly bigger highlight


def has(p):
    """True if a media file is really there (why: fonts, SFX and images aren't shipped; missing ones are skipped)."""
    return os.path.exists(p)


def bare(t):
    return re.sub(r"[^\w'-]", "", t).lower()


def at(phrase, after=0.0):
    """Start time of a spoken phrase on the cut clock ('END' = the end of the reel)."""
    if phrase == "END":
        return DUR
    want = [bare(x) for x in phrase.split()]
    for i in range(len(W) - len(want) + 1):
        if W[i]["start"] >= after - 0.01 and [bare(w["text"]) for w in W[i:i + len(want)]] == want:
            return W[i]["start"]
    sys.exit(f"phrase not found in the words: {phrase!r} (check reel.json against the heard line cut.py printed)")


def peak(path):
    """Seconds from a sound file's start to its loudest 10 ms (so its hit lands 1 frame after the picture)."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", "48000", "-f", "s16le", "-"],
                         capture_output=True, check=True).stdout
    a, n, best = array.array("h", raw), 480, (0, 0.0)
    for i in range(0, len(a) - n, n):
        e = sum(x * x for x in a[i:i + n])
        if e > best[0]:
            best = (e, i / 48000)
    return best[1]


# ---------------------------------------------------------------- moments (all from the spoken words)
HOOK = C["hook"]
HOOK_END = at(HOOK["until"])

BIG = C.get("big_words") or None
if BIG:
    BIG_T, t = [], 0.0
    for p in BIG["at"]:
        t = at(p, after=t)
        BIG_T.append(t)
        t += 0.05
    BIG_IN, BIG_OUT = BIG_T[0], at(BIG["until"], after=BIG_T[-1] + 0.05)
CUTOUT = "assets/cutout.webm" if BIG and has("assets/cutout.webm") else None   # your cut-out, for words behind the head

# Proof card motion, two alternating styles (the demo's numbers). Offsets are seconds from the card's `from` phrase
# (enter) and `until` phrase (exit). Style A rises from below; style B whips in from the right.
CARD_STYLES = [
    {"enter": 0.10, "exit": 0.19, "cam_dur": 0.50, "cam_back": 0.30, "cam_back_ease": "power3.inOut",
     "in_from": "y: 460, rotation: -7", "in_to": "y: 0, rotation: -2", "in_dur": 0.6, "in_ease": "back.out(1.3)", "blur_in": 14,
     "out_to": "y: 900, rotation: 4", "out_dur": 0.3, "sfx_in": ("soft-whoosh-1.mp3", 1.10, 0.28),
     "sfx_out": ("whoosh1_2.mp3", 0.28, 0.48, 0.80)},
    {"enter": -0.03, "exit": -0.31, "cam_dur": 0.45, "cam_back": 0.28, "cam_back_ease": "power3.in",
     "in_from": "x: 1100, rotation: 6", "in_to": "x: 0, rotation: 1.5", "in_dur": 0.45, "in_ease": "power4.out", "blur_in": 16,
     "out_to": "x: -1100, rotation: -4", "out_dur": 0.25, "sfx_in": ("paper-slide-1.mp3", 0.58, 1.05),
     "sfx_out": ("swoosh-transition-1.mp3", 0.22, 0.88, 0.50)},
]
CARDS = []
for c in C.get("proof_cards", []):
    if not has(c["image"]):
        print(f"skipping proof card: {c['image']} isn't there (add your own screenshot to assets/cards/)")
        continue
    st = CARD_STYLES[len(CARDS) % 2]
    t_from = at(c["from"])
    t_until = at(c["until"], after=t_from + 0.05)
    CARDS.append({**c, "style": st, "cam_in": t_from - 0.1, "enter": t_from + st["enter"], "exit": t_until + st["exit"]})

CHAPTERS = []
for ch in C.get("chapters", []):
    t_in = at(ch["from"])
    CHAPTERS.append({**ch, "t_in": t_in, "t_out": at(ch["until"], after=t_in + 0.05)})

PUNCHES = []
for p in C.get("punches", []):
    t_in = at(p["at"])
    PUNCHES.append({**p, "t_in": t_in, "t_out": None if p.get("until", "END") == "END" else at(p["until"], after=t_in + 0.05)})


# ---------------------------------------------------------------- captions: max 3 words, off while the big words are up
def in_big(t):
    return bool(BIG) and BIG_IN - 0.02 <= t < BIG_OUT


def groups():
    mw = C.get("captions", {}).get("max_words", 3)
    gs, cur = [], []
    for i, w in enumerate(W):
        if in_big(w["start"]):
            if cur:
                gs.append(cur); cur = []
            continue
        if cur and (len(cur) >= mw or W[cur[-1]]["text"][-1] in ".,?!"):
            gs.append(cur); cur = []
        cur.append(i)
    if cur:
        gs.append(cur)
    return gs


GROUPS = groups()


def caption_html():
    out, js = [], []
    for g, idx in enumerate(GROUPS):
        a, b = idx[0], idx[-1]
        start = max(0.1, W[a]["start"] - 0.05)
        nxt = GROUPS[g + 1][0] if g + 1 < len(GROUPS) else None
        end = min(DUR - 0.02, (W[nxt]["start"] - 0.05) if nxt is not None else W[b]["end"] + 0.35)
        if BIG and start < BIG_IN:           # the group before the big words ends when they slam in
            end = min(end, BIG_IN - 0.02)
        spans = []
        for i in idx:
            word = W[i]["text"]
            spans.append(f'<span id="cw{i}" class="cw">{html.escape(word)}</span>')
            kw = word.strip(".,'?!").lower() in KEYWORDS
            js.append(f'tl.to("#cw{i}", {{ color: "#FFE45C", scale: {1.08 if kw else 1.0}, duration: 0.06 }}, {W[i]["start"]:.3f});')
            if i < b:
                js.append(f'tl.to("#cw{i}", {{ color: "#FFFFFF", scale: 1, duration: 0.08 }}, {W[i + 1]["start"]:.3f});')
        out.append(f'<div id="cg{g}" class="clip capgroup" data-start="{start:.3f}" data-duration="{end - start:.3f}" '
                   f'data-track-index="20">{" ".join(spans)}</div>')
        js.append(f'tl.fromTo("#cg{g}", {{ opacity: 0, filter: "blur(6px)" }}, {{ opacity: 1, filter: "blur(0px)", duration: 0.12, ease: "power3.out" }}, {start:.3f});')
        js.append(f'tl.to("#cg{g}", {{ opacity: 0, duration: 0.1, ease: "power2.in" }}, {end - 0.1:.3f});')
    return "\n      ".join(out), "\n      ".join(js)


cap_html, cap_js = caption_html()


# ---------------------------------------------------------------- sound: start = picture moment + 1 frame - the file's peak
SFX = []   # id, file, start, duration, volume


def sfx(sid, f, moment, dur, vol, fixed=False):
    path = "assets/sfx/" + f
    if not has(path):
        return   # SFX aren't shipped: skip here, add it natively in Edits instead
    SFX.append((sid, f, moment if fixed else moment + FRAME - peak(path), dur, vol))


if HOOK.get("sub"):
    sfx("sfx-type", "typing_2s.mp3", 0.42, 0.90, 1.00, fixed=True)   # a bed under the type-on, from its first key
if BIG:
    sfx("sfx-big0", "soft-thud.mp3", BIG_T[0], 1.10, 0.55)
    if len(BIG_T) > 1:
        sfx("sfx-big1", "boom-impact-2.mp3", BIG_T[1], 1.00, 0.20)   # a different hit: never the same one twice
for k, c in enumerate(CARDS):
    st = c["style"]
    f, d, v = st["sfx_in"]
    sfx(f"sfx-c{k}in", f, c["enter"], d, v)
    if c.get("stat"):
        sfx(f"sfx-c{k}ring", "marker.mp3", c["enter"] + 0.85, 0.50, 1.90)
    f, off, d, v = st["sfx_out"]
    sfx(f"sfx-c{k}out", f, c["exit"] + off, d, v)
for k, ch in enumerate(CHAPTERS):
    sfx(f"sfx-chap{k}", "pop.mp3", ch["t_in"], 0.50, 1.80)
sfx_html = "\n    ".join(
    f'<audio id="{i}" class="clip" src="assets/sfx/{f}" data-start="{max(0, s):.3f}" data-duration="{d}" '
    f'data-volume="{v}" data-fade-out="0.12" data-track-index="{30 + n}"></audio>' for n, (i, f, s, d, v) in enumerate(SFX))


# ---------------------------------------------------------------- the graphics
hook_words = " ".join(f'<span class="hw" id="hw{i}">{html.escape(w)}</span>' for i, w in enumerate(HOOK["text"].split()))
sub_html = (f'<div id="sub" class="clip" data-start="0.45" data-duration="{HOOK_END - 0.5:.3f}" data-track-index="5">'
            f'<span>{html.escape(HOOK["sub"])}</span></div>') if HOOK.get("sub") else ""

big_html = ""
if BIG:
    lines = "".join(f'<div id="big{k}" class="bigword" style="top:{215 + 195 * k}px">{html.escape(l)}</div>'
                    for k, l in enumerate(BIG["lines"][:2]))   # the look is one or two lines
    big_html = (f'<div id="big" class="clip" data-start="{BIG_IN - 0.02:.3f}" data-duration="{BIG_OUT - BIG_IN + 0.22:.3f}" '
                f'data-track-index="2" data-layout-allow-overlap>{lines}</div>')


def count_js(k, stat, t):
    """Count a stat up from 0 if it's a whole number ('485', '$1,300', '3x'); anything else just shows."""
    m = re.match(r"^(\D*)(\d[\d,]*)(\D*)$", stat)
    if not m:
        return ""
    pre, num, post = m.group(1), int(m.group(2).replace(",", "")), m.group(3)
    fmt = 'Math.round(o.v).toLocaleString("en-US")' if "," in m.group(2) else "Math.round(o.v)"
    return (f'(() => {{ const o = {{ v: 0 }}; tl.fromTo(o, {{ v: 0 }}, {{ v: {num}, duration: 0.7, ease: "power2.out", '
            f'onUpdate: () => {{ document.querySelector("#sv{k}").textContent = {json.dumps(pre)} + {fmt} + {json.dumps(post)}; }} }}, {t:.3f}); }})();')


cards_html, cards_js = [], []
for k, c in enumerate(CARDS):
    st = c["style"]
    head = f'<div class="head"><div class="chip">{html.escape(c["label"])}</div></div>' if c.get("label") else ""
    stat = ""
    if c.get("stat"):
        small = f' <small>{html.escape(c["stat_small"])}</small>' if c.get("stat_small") else ""
        stat = (f'<div class="stat"><span class="sv" id="sv{k}">{html.escape(c["stat"])}</span>{small}'
                f'<svg class="ring" viewBox="0 0 470 175" preserveAspectRatio="none"><path id="ring{k}" '
                f'd="M60 30 C 200 -8, 430 10, 452 78 C 470 140, 300 172, 170 160 C 60 150, 10 110, 28 66 C 40 38, 80 24, 120 22" /></svg></div>')
    cards_html.append(f'<div id="card{k}" class="card clip" data-start="{c["enter"] - 0.05:.3f}" '
                      f'data-duration="{c["exit"] + 0.33 - (c["enter"] - 0.05):.3f}" data-track-index="{6 + 2 * k}">'
                      f'{head}<img class="shot" src="{html.escape(c["image"])}" alt="proof screenshot">{stat}</div>')
    b = st["blur_in"]
    cards_js += [
        f'tl.to("#cam", {{ scale: 0.84, y: 154, borderRadius: 48, boxShadow: "0 40px 100px rgba(0,0,0,.6)", duration: {st["cam_dur"]}, ease: "power2.inOut" }}, {c["cam_in"]:.3f});',
        f'tl.fromTo("#card{k}", {{ {st["in_from"]}, opacity: 0, filter: "blur({b}px)" }}, {{ {st["in_to"]}, opacity: 1, filter: "blur(0px)", duration: {st["in_dur"]}, ease: "{st["in_ease"]}" }}, {c["enter"]:.3f});',
    ]
    if c.get("stat"):
        cards_js.append(count_js(k, c["stat"], c["enter"] + 0.2))
        cards_js.append(f'tl.fromTo("#ring{k}", {{ strokeDasharray: 1400, strokeDashoffset: 1400 }}, {{ strokeDashoffset: 0, duration: 0.5, ease: "power2.inOut" }}, {c["enter"] + 0.85:.3f});')
    cards_js += [
        f'tl.to("#card{k}", {{ {st["out_to"]}, opacity: 0, filter: "blur(16px)", duration: {st["out_dur"]}, ease: "power3.in" }}, {c["exit"]:.3f});',
        f'tl.to("#cam", {{ scale: 1, y: 0, borderRadius: 0, boxShadow: "0 0 0 rgba(0,0,0,0)", duration: {st["cam_back"]}, ease: "{st["cam_back_ease"]}" }}, {c["exit"] + 0.03:.3f});',
    ]

chap_html, chap_js = [], []
for k, ch in enumerate(CHAPTERS):
    chap_html.append(f'<div id="chap{k}" class="chap clip" data-start="{ch["t_in"] - 0.05:.3f}" data-duration="{ch["t_out"] - ch["t_in"]:.3f}" '
                     f'data-track-index="{7 + 2 * k}"><div class="chap-num">{html.escape(ch["number"])}</div>'
                     f'<div class="chap-label">{html.escape(ch["label"])}</div></div>')
    chap_js += [
        f'tl.set("#cam", {{ scale: 1.12 }}, {ch["t_in"]:.3f});   // punch on the chapter number',
        f'tl.fromTo("#chap{k} .chap-num", {{ opacity: 0, scale: 1.4, filter: "blur(10px)" }}, {{ opacity: 1, scale: 1, filter: "blur(0px)", duration: 0.2, ease: "expo.out" }}, {ch["t_in"]:.3f});',
        f'tl.fromTo("#chap{k} .chap-label", {{ clipPath: "inset(0 100% 0 0 round 22px)" }}, {{ clipPath: "inset(0 0% 0 0 round 22px)", duration: 0.3, ease: "power4.out" }}, {ch["t_in"] + 0.08:.3f});',
        f'tl.to("#chap{k}", {{ opacity: 0, filter: "blur(8px)", duration: 0.15, ease: "power2.in" }}, {ch["t_out"] - 0.2:.3f});',
    ]
    # back to full frame, unless a proof card's camera move starts right here (it then shrinks from the punch, as on the demo)
    if not any(abs(c["cam_in"] - ch["t_out"]) < 0.4 for c in CARDS):
        chap_js.append(f'tl.set("#cam", {{ scale: 1 }}, {ch["t_out"] - 0.2:.3f});')

cam_js = ['tl.set("#cam", { scale: 1, y: 0, borderRadius: 0 }, 0);']
if BIG:
    cam_js += [f'tl.set("#cam", {{ scale: 1.14 }}, {BIG_IN:.3f});   // punch on the first big word',
               f'tl.set("#cam", {{ scale: 1 }}, {BIG_OUT:.3f});']
for p in PUNCHES:
    cam_js.append(f'tl.set("#cam", {{ scale: {p["scale"]} }}, {p["t_in"]:.3f});')
    if p["t_out"] is not None:
        cam_js.append(f'tl.set("#cam", {{ scale: 1 }}, {p["t_out"]:.3f});')

big_js = ""
if BIG:
    big_js = "\n    ".join(
        f'tl.fromTo("#big{k}", {{ opacity: 0, scale: 1.3, filter: "blur(12px)" }}, {{ opacity: 1, scale: 1, filter: "blur(0px)", duration: 0.2, ease: "expo.out" }}, {t:.3f});'
        for k, t in enumerate(BIG_T[:2]))
    big_js += f'\n    tl.to("#big .bigword", {{ opacity: 0, filter: "blur(10px)", duration: 0.18, ease: "power2.in" }}, {BIG_OUT:.3f});'

hook_out = '["#hook .pill", "#sub span"]' if HOOK.get("sub") else '"#hook .pill"'
inter_face = ('@font-face { font-family: "Inter"; src: url("assets/fonts/Inter-Variable.ttf"); font-weight: 100 900; }'
              if has("assets/fonts/Inter-Variable.ttf") else "")


def page(overlay=False):
    if CUTOUT:
        # in the overlay the cut-out only shows while the big words sit behind the head (it lines up with your take)
        win = (f'data-start="{BIG_IN - 0.02:.3f}" data-media-start="{BIG_IN - 0.02:.3f}" data-duration="{BIG_OUT - BIG_IN + 0.22:.3f}"'
               if overlay else f'data-start="0" data-duration="{DUR}"')
        cutout = (f'<video id="cutout" class="clip" src="{CUTOUT}" {GRADE} muted playsinline data-layout-allow-occlusion '
                  f'{win} data-track-index="3"></video>')
    else:
        cutout = ""
    hidden = " data-hidden" if overlay else ""
    # camera moves stay with Edits in the overlay: the graphics line up with the untouched footage underneath
    cam = "" if overlay else "\n    ".join(cam_js)
    cjs = [j for j in cards_js + chap_js if not (overlay and j.startswith(('tl.to("#cam"', 'tl.set("#cam"')))]
    return f"""<!doctype html>
<html lang="en" data-resolution="portrait">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1080, height=1920" />
<script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
<style>
  @font-face {{ font-family: "DM Mono"; src: url("assets/fonts/DMMono-Medium.ttf"); font-weight: 500; }}
  {inter_face}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  html, body {{ width: 1080px; height: 1920px; overflow: hidden; background: {"transparent" if overlay else "#0E0E10"}; }}
  body {{ font-family: "Inter", sans-serif; color: #0E0E10; }}

  /* backdrop revealed when the camera shrinks for proof */
  #plate {{ position: absolute; inset: 0; z-index: 0;
           background: radial-gradient(120% 80% at 50% 20%, #26262E 0%, #121216 55%, #0B0B0D 100%); }}
  /* the camera: footage, giant words, then your cut-out, moved as one */
  #cam {{ position: absolute; inset: 0; z-index: 1; overflow: hidden; border-radius: 0; transform-origin: 50% 50%; }}
  #cam video {{ position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }}
  #a-roll {{ z-index: 1; }}
  #big {{ position: absolute; inset: 0; z-index: 2; }}
  #cutout {{ z-index: 3; }}
  .bigword {{ position: absolute; left: 0; right: 0; text-align: center; font: 900 260px/0.9 "Inter"; letter-spacing: -0.04em;
             color: #FFFFFF; text-shadow: 0 10px 40px rgba(0,0,0,.25); }}

  /* hook */
  #hook {{ position: absolute; left: 0; right: 0; top: 210px; text-align: center; z-index: 5; }}
  #hook .pill {{ display: inline-block; background: #FFFFFF; border-radius: 999px; padding: 18px 40px;
                font: 800 64px/1.1 "Inter"; letter-spacing: -0.015em; box-shadow: 0 14px 40px rgba(0,0,0,.25); }}
  #hook .hw {{ display: inline-block; }}
  #sub {{ position: absolute; left: 0; right: 0; top: 330px; text-align: center; z-index: 5; }}
  #sub span {{ display: inline-block; font: 500 36px/1.3 "DM Mono"; color: #FFFFFF; background: rgba(14,14,16,.82);
              padding: 8px 18px; border-radius: 12px; }}

  /* proof cards: YOUR screenshot in a white frame, an optional label chip, an optional circled stat */
  .card {{ position: absolute; left: 90px; top: 190px; width: 900px; z-index: 6; background: #FFFFFF; border-radius: 36px;
          padding: 40px 44px 44px; box-shadow: 0 40px 90px rgba(0,0,0,.45), 0 4px 12px rgba(0,0,0,.2); }}
  .head {{ display: flex; align-items: center; gap: 20px; margin-bottom: 26px; }}
  .chip {{ font: 700 28px/1 "Inter"; color: #138A4F; background: #E3F6EC; padding: 12px 18px; border-radius: 999px; }}
  /* max-height keeps a tall screenshot (and the stat under it) above y 1330, clear of the captions */
  .shot {{ display: block; width: 100%; max-height: 760px; object-fit: contain; border-radius: 20px; }}
  .stat {{ position: relative; display: inline-block; margin-top: 26px; font: 900 112px/1 "Inter"; letter-spacing: -0.03em; }}
  .stat small {{ font: 800 52px "Inter"; color: #6B6B70; letter-spacing: -0.01em; }}
  /* the ring stretches with the stat's width (demo: 470 px round "$1,300 build") */
  .ring {{ position: absolute; left: -34px; top: -30px; width: calc(100% + 68px); height: 175px; overflow: visible; }}
  .ring path {{ fill: none; stroke: #FFE45C; stroke-width: 12; stroke-linecap: round; }}

  /* chapter */
  .chap {{ position: absolute; left: 72px; top: 180px; z-index: 5; display: flex; align-items: center; gap: 22px; }}
  .chap-num {{ font: 900 150px/0.9 "Inter"; color: #FFE45C; letter-spacing: -0.04em; -webkit-text-stroke: 6px #0E0E10; paint-order: stroke fill; }}
  .chap-label {{ font: 800 54px/1.1 "Inter"; background: #FFFFFF; padding: 16px 28px; border-radius: 22px; letter-spacing: -0.015em;
                box-shadow: 0 14px 40px rgba(0,0,0,.25); }}

  /* captions */
  .capgroup {{ position: absolute; left: 0; right: 0; top: 1470px; text-align: center; z-index: 8; overflow: visible;
              font: 800 66px/1.15 "Inter"; letter-spacing: -0.01em; color: #FFFFFF; padding: 0 70px;
              word-spacing: 0.18em; }}  /* WHY the extra space: a keyword grows to 1.08 with an 8 px outline and
                                           otherwise swallows the space next to it ("thedopamineeffect") */
  .cw {{ display: inline-block; -webkit-text-stroke: 8px #0E0E10; paint-order: stroke fill; text-shadow: 0 6px 18px rgba(0,0,0,.45); }}
</style>
</head>
<body>
  <div id="root" data-composition-id="main" data-start="0" data-duration="{DUR}" data-width="1080" data-height="1920">
    <div id="plate" class="clip"{hidden} data-start="0" data-duration="{DUR}" data-track-index="0"></div>

    <div id="cam">
      <video id="a-roll" class="clip"{hidden} src="assets/cut.mp4" {GRADE} playsinline data-has-audio="true" data-volume="1"
             data-start="0" data-duration="{DUR}" data-track-index="1"></video>
      {big_html}
      {cutout}
    </div>

    <div id="hook" class="clip" data-start="0" data-duration="{HOOK_END - 0.05:.3f}" data-track-index="4">
      <span class="pill">{hook_words}</span>
    </div>
    {sub_html}

    {chr(10).join("    " + h for h in cards_html).strip()}
    {chr(10).join("    " + h for h in chap_html).strip()}

    <div id="captions" data-track-kind="captions">
      {cap_html}
    </div>

    {sfx_html}
  </div>

  <script>
    const tl = gsap.timeline({{ paused: true }});

    // ---- camera (hard cuts = gsap.set; moves = one tween each) ----
    {cam}

    // ---- hook: frame 0 = the thumbnail, so the whole hook is already set; the pill lands with a small settle ----
    tl.fromTo("#hook .pill", {{ scale: 1.06 }}, {{ scale: 1, duration: 0.35, ease: "expo.out" }}, 0);
    {'tl.fromTo("#sub span", { clipPath: "inset(0 100% 0 0)" }, { clipPath: "inset(0 0% 0 0)", duration: 0.8, ease: "steps(28)" }, 0.45);' if HOOK.get("sub") else ""}
    tl.to({hook_out}, {{ opacity: 0, filter: "blur(8px)", duration: 0.16, ease: "power2.in" }}, {HOOK_END - 0.2:.3f});

    // ---- giant words behind the head ----
    {big_js}

    // ---- proof cards + chapters ----
    {chr(10).join("    " + j for j in cjs).strip()}

    // ---- captions (generated from assets/words-cut.json) ----
      {cap_js}

    window.__timelines["main"] = tl;
  </script>
</body>
</html>
"""


open("index.html", "w").write(page(False))
rt.write_overlays(page(True))   # graphics-only project in overlays/ (one root composition per project)
if os.path.exists("index-overlays.html"):
    os.remove("index-overlays.html")   # the old single-file overlay; overlays/ replaces it
print(f"index.html + overlays/index.html: {DUR} s, {len(GROUPS)} caption groups, {len(CARDS)} proof cards, "
      f"{len(CHAPTERS)} chapters, {len(SFX)} sounds" + ("" if CUTOUT or not BIG else
      " (no assets/cutout.webm: the big words sit over the footage, not behind the head)"))
