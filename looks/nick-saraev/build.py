#!/usr/bin/env python3
"""Builds the Nick Saraev-inspired "editorial recompose" reel (see SPEC.md for every number used here).

The look: the frame rearranges itself around each sentence. One presenter frame moves between three states:
  face  = the take full frame;
  split = the take in a rounded box in the bottom half, one explanatory object in the paper field above;
  full  = the take slides out, the proof or the type holds the whole paper field.
The paper is ONE element: a transparent "hole" whose huge box-shadow paints the paper everywhere outside it. The hole
and the footage move together, so nothing ever cuts: it recomposes. In --overlay mode the footage is left out and the
same paper-with-a-hole renders over transparency, so Edits can keyframe the member's own clip underneath (SPEC.md).

Usage:
  python3 build.py                                   # index.html from plan.json
  python3 build.py --plan other.json --footage assets/x.mp4 --words assets/x-words.json
  python3 build.py --overlay                         # overlay/index.html: footage hidden, transparent ground
Then: npx --yes hyperframes@0.9.83 check --json, snapshot, render (see SPEC.md "Build and render").
--overlay writes into overlay/, which must already be its own HyperFrames project (hyperframes.json, package.json,
meta.json, and an `assets` symlink to ../assets): this script does not create it.
Missing media never stops the build: sounds, logos and page captures that aren't there are left out (with a note).
"""
import argparse, html, json, math, os, re

# BRAND: Claude fills these from the member's profile.md before each build (why: the look is fixed,
# the colours and fonts are hers). These defaults are neutral placeholders.
BRAND_INK, BRAND_ACCENT, BRAND_CREAM = "#141414", "#FF5A36", "#FAF7F2"
# This look only takes the ACCENT from the brand. Its paper, sage and ink below belong to the look, so BRAND_INK and
# BRAND_CREAM aren't used here. plan.json "accent" (if set) wins over BRAND_ACCENT.

def has(p):
    """True if a media file is there (why: fonts, sounds, logos and captures aren't shipped; skip, never crash)."""
    return bool(p) and os.path.exists(p)

ap = argparse.ArgumentParser()
ap.add_argument("--plan", default="plan.json")
ap.add_argument("--footage")
ap.add_argument("--words")
ap.add_argument("--proof-dir", default="assets/proof")
ap.add_argument("--overlay", action="store_true")
ap.add_argument("--out")
args = ap.parse_args()

PLAN = json.load(open(args.plan))
FOOTAGE = args.footage or PLAN["footage"]
W = json.load(open(args.words or PLAN["words"]))
DUR = PLAN["duration"]
OVERLAY = args.overlay
OUT = args.out or ("overlay/index.html" if OVERLAY else "index.html")   # overlay/ = its own project (assets symlinked)
FPS = 30

# ---------------- palette + type (SPEC.md "Palette", "Type") ----------------
PAPER, SAGE, INK, ACCENT = "#F7F6F3", "#E9ECEB", "#101012", PLAN.get("accent", BRAND_ACCENT)

def tint(hex_col, keep=0.14):
    """The accent mixed with white (14% accent): the pale box behind hook line 2, so it follows any accent."""
    c = [int(hex_col.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)]
    return "#" + "".join(f"{round(255 - (255 - v) * keep):02X}" for v in c)
ACCENT_TINT = tint(ACCENT)         # pale accent for the hook's second box (his boxed line 2, in the member colour)
FIELDS = {"paper": PAPER, "sage": SAGE}

# ---------------- presenter states (1080x1920) ----------------
# hole = the window the footage shows through. Its base box is the SPLIT rectangle; face/off are transforms of it.
HOLE = dict(left=48, top=940, w=984, h=1060, r=44)          # bottom bleeds to y 2000 (off-frame)
STATE = {
    "face":  {"hole": dict(scaleX=1080 / 984, scaleY=2000 / 1060, y=0, borderRadius=0),
              "cam": dict(scale=1.0, y=0)},
    "split": {"hole": dict(scaleX=1, scaleY=1, y=0, borderRadius=HOLE["r"]),
              "cam": dict(scale=0.92, y=432)},              # face (src y 560-1380) lands at y 1024-1778, inside the box
    "full":  {"hole": dict(scaleX=1, scaleY=1, y=1060, borderRadius=HOLE["r"]),
              "cam": dict(scale=0.92, y=432 + 1060)},       # take slides out with its box
}
MOVE_DUR, MOVE_EASE, LEAD = 0.5, "power3.inOut", 0.13       # recompositions start 0.13 s before their word

# caption placement per state: (top px, colour class)
CAP = {"face": (1466, "on-footage"), "split": (858, "on-paper"), "full": (1466, "on-paper")}

# ---------------- time refs ----------------
def T(ref):
    """'w12' -> start of word 12; 'w12+0.3' / 'w12-0.1' -> offset; number -> seconds."""
    if isinstance(ref, (int, float)):
        return float(ref)
    m = re.fullmatch(r"w(\d+)([+-][\d.]+)?", ref)
    if not m:
        raise SystemExit(f"bad time ref {ref!r}")
    return round(W[int(m.group(1))]["start"] + float(m.group(2) or 0), 3)

def state_at(t):
    cur = PLAN["beats"][0]
    for b in PLAN["beats"]:
        if T(b["at"]) <= t + 1e-6:
            cur = b
    return cur["state"]

esc = html.escape
js = []                                   # timeline lines, in order
body = []                                 # markup
def J(line): js.append(line)

def place_js(sel, place, at, dur, ease):
    J(f'tl.to("{sel}", {{ y: {place["cy"]}, scale: {place["scale"]}, duration: {dur}, ease: "{ease}" }}, {at:.3f});')

# ---------------- object renderers ----------------
def logo_img(name, size):
    src = f"{args.proof_dir}/{name}.svg"
    if not has(src):                       # no logo file: the chip shows its label alone
        print(f"note: logo {src} not found, chip shows the label only")
        return ""
    return f'<img class="logo" src="{src}" style="width:{size}px;height:{size}px" alt="{esc(name)}">'

def r_chips(o):
    chips = "".join(f'<span class="chip">{logo_img(l, 60)}<span>{esc(n)}</span></span>' for l, n in o["logos"])
    return f'<div class="chips">{chips}</div>'

def r_word(o):
    cls = "w-serif" if o.get("font") == "serif" else "w-sans"
    style = f'font-size:{o["size"]}px;' + (f"color:{ACCENT};" if o.get("accent") else "")
    halo = " halo" if o.get("halo") else ""
    return f'<div class="bigword {cls}{halo}" style="{style}">{esc(o["text"])}</div>'

def r_listcard(o):
    head = "".join(f'<span class="chip sm">{logo_img(l, 46)}<span>{esc(n)}</span></span>' for l, n in o["logos"])
    rows = []
    for i, r in enumerate(o["rows"]):
        mark = ""
        if r["mark"] == "tick":
            mark = (f'<svg class="tick" viewBox="0 0 60 60"><path id="{o["id"]}-tick{i}" d="M10 32 L25 46 L51 15" /></svg>')
        elif r["mark"] == "strike":
            mark = f'<i class="strike" id="{o["id"]}-strike{i}"></i>'
        rows.append(f'<div class="lrow" id="{o["id"]}-row{i}"><b class="num">{i + 1}</b>'
                    f'<span class="ltext">{esc(r["text"])}{mark}</span></div>')
    return f'<div class="card list"><div class="lhead">{head}</div>{"".join(rows)}</div>'

def r_pagecard(o):
    meta = json.load(open(f'{args.proof_dir}/{o["proof"]}.json'))
    k = 920 / meta["w"]                                    # screenshot shown 920 px wide inside a 1000 px card
    hl = []
    for mi, m in enumerate(o.get("marks", [])):
        names = m["mark"] if isinstance(m["mark"], list) else [m["mark"]]
        for ni, nm in enumerate(names):
            for ri, b in enumerate(meta["marks"][nm]):
                hl.append(f'<i class="hl" id="{o["id"]}-hl{mi}-{ni}-{ri}" style="left:{b["x"] * k - 6:.0f}px;'
                          f'top:{b["y"] * k + 2:.0f}px;width:{b["w"] * k + 12:.0f}px;height:{b["h"] * k - 4:.0f}px"></i>')
    return (f'<div class="card page"><div class="src"><i class="dot"></i>{esc(o["source"])}</div>'
            f'<div class="shot" style="height:{meta["h"] * k:.0f}px"><img src="{args.proof_dir}/{o["proof"]}.png" '
            f'style="width:920px;height:{meta["h"] * k:.0f}px" alt="">{"".join(hl)}</div></div>')

def r_typewall(o):
    pills = "".join('<span class="pill">idea</span>' for _ in range(7 * 15))
    subs = " ".join(f'<span class="sub" id="{o["id"]}-sub{i}">{esc(s)}</span>' for i, (s, _) in enumerate(o["sub"]))
    return (f'<div class="wall"><div class="pills" data-layout-ignore>{pills}</div><div class="glow" data-layout-ignore></div>'
            f'<div class="big w-serif" id="{o["id"]}-big">{esc(o["big"])}</div><div class="subs">{subs}</div></div>')

RENDER = {"chips": r_chips, "word": r_word, "listcard": r_listcard, "pagecard": r_pagecard, "typewall": r_typewall}

def object_js(o):
    oid, mv = o["id"], f'#{o["id"]}-mv'
    t_in, t_out = T(o["enter"]["at"]), T(o["exit"]["at"])
    how = o["enter"]["how"]
    if o["type"] != "typewall":
        p = o["enter"]["place"]
        J(f'tl.set("{mv}", {{ xPercent: -50, yPercent: -50, x: 540, y: {p["cy"]}, scale: {p["scale"]} }}, 0);')
        if how == "rise":       # arrives from below, sharpening, long tail
            J(f'tl.fromTo("{mv}", {{ y: {p["cy"] + 420}, opacity: 0, filter: "blur(14px)" }}, {{ y: {p["cy"]}, opacity: 1, filter: "blur(0px)", duration: 0.5, ease: "power4.out" }}, {t_in:.3f});')
        elif how == "pop":
            J(f'tl.fromTo("{mv}", {{ scale: {p["scale"] * 0.6}, opacity: 0 }}, {{ scale: {p["scale"]}, opacity: 1, duration: 0.4, ease: "back.out(1.6)" }}, {t_in:.3f});')
            J(f'tl.fromTo("{mv} .chip", {{ y: 24 }}, {{ y: 0, duration: 0.35, ease: "power4.out", stagger: 0.08 }}, {t_in:.3f});')
        elif how == "slam":
            J(f'tl.fromTo("{mv}", {{ scale: {p["scale"] * 1.3}, opacity: 0, filter: "blur(12px)" }}, {{ scale: {p["scale"]}, opacity: 1, filter: "blur(0px)", duration: 0.22, ease: "expo.out" }}, {t_in:.3f});')
        elif how == "blurin":
            J(f'tl.fromTo("{mv}", {{ opacity: 0, filter: "blur(8px)" }}, {{ opacity: 1, filter: "blur(0px)", duration: 0.18, ease: "power4.out" }}, {t_in:.3f});')
        for m in o.get("moves", []):
            place_js(mv, m["place"], T(m["at"]), MOVE_DUR, MOVE_EASE)
    # inner reveals
    if o["type"] == "typewall":
        J(f'tl.fromTo("{mv} .pill", {{ opacity: 0, scale: 0.6 }}, {{ opacity: 1, scale: 1, duration: 0.25, ease: "power4.out", stagger: {{ grid: [15, 7], from: "center", amount: 0.8 }} }}, {T(o["enter"]["at"]) + 0.05:.3f});')  # texture builds while the lead-in words are spoken
        J(f'tl.fromTo("#{oid}-big", {{ opacity: 0, scale: 1.15, filter: "blur(12px)" }}, {{ opacity: 1, scale: 1, filter: "blur(0px)", duration: 0.2, ease: "expo.out" }}, {T(o["big_at"]):.3f});')
        for i, (_, at) in enumerate(o["sub"]):
            J(f'tl.fromTo("#{oid}-sub{i}", {{ opacity: 0, filter: "blur(6px)" }}, {{ opacity: 1, filter: "blur(0px)", duration: 0.14, ease: "power4.out" }}, {T(at):.3f});')
    if o["type"] == "listcard":
        for i, r in enumerate(o["rows"]):
            J(f'tl.fromTo("#{oid}-row{i}", {{ opacity: 0.18 }}, {{ opacity: 1, duration: 0.12, ease: "power2.out" }}, {T(r["at"]):.3f});')
            if r["mark"] == "tick":
                J(f'tl.fromTo("#{oid}-tick{i}", {{ strokeDasharray: 80, strokeDashoffset: 80 }}, {{ strokeDashoffset: 0, duration: 0.3, ease: "power2.out" }}, {T(r["at"]) + 0.2:.3f});')
            if r["mark"] == "strike":
                J(f'tl.fromTo("#{oid}-strike{i}", {{ scaleX: 0 }}, {{ scaleX: 1, duration: 0.35, ease: "power2.inOut" }}, {T(r["mark_at"]):.3f});')
                J(f'tl.to("#{oid}-row{i} .ltext", {{ color: "rgba(16,16,18,0.45)", duration: 0.2 }}, {T(r["mark_at"]) + 0.2:.3f});')
    if o["type"] == "pagecard":
        for mi, m in enumerate(o.get("marks", [])):
            t = T(m["at"])
            J(f'tl.fromTo("#{oid}-mv [id^=\'{oid}-hl{mi}-\']", {{ scaleX: 0 }}, {{ scaleX: 1, duration: 0.3, ease: "power2.inOut", stagger: 0.28 }}, {t:.3f});')
    # exit
    eh = o["exit"]["how"]
    if eh == "blur":
        J(f'tl.to("{mv}", {{ opacity: 0, filter: "blur(8px)", duration: 0.18, ease: "power2.in" }}, {t_out:.3f});')
    elif eh == "up":            # leaves with the recomposition: one accelerating move, motion-blurred
        J(f'tl.to("{mv}", {{ y: "-=1500", filter: "blur(16px)", duration: 0.4, ease: "power3.in" }}, {t_out:.3f});')
    return t_in, t_out

# ---------------- build markup + timeline ----------------
# 1) presenter states + field colour
J('tl.set("#cam", { scale: 1, y: 0, transformOrigin: "50% 50%" }, 0);')
s0 = PLAN["beats"][0]
J(f'tl.set("#hole", {{ transformOrigin: "50% 100%", {", ".join(f"{k}: {v}" for k, v in STATE[s0["state"]]["hole"].items())}, '
  f'boxShadow: "0 0 0 2600px {FIELDS[s0["field"]]}" }}, 0);')
J(f'tl.set("#cam", {{ {", ".join(f"{k}: {v}" for k, v in STATE[s0["state"]]["cam"].items())} }}, 0);')
for b in PLAN["beats"][1:]:
    t = T(b["at"]) - LEAD
    st = STATE[b["state"]]
    hole = ", ".join(f"{k}: {v}" for k, v in st["hole"].items())
    J(f'tl.to("#hole", {{ {hole}, boxShadow: "0 0 0 2600px {FIELDS[b["field"]]}", duration: {MOVE_DUR}, ease: "{MOVE_EASE}" }}, {t:.3f});')
    J(f'tl.to("#cam", {{ {", ".join(f"{k}: {v}" for k, v in st["cam"].items())}, duration: {MOVE_DUR}, ease: "{MOVE_EASE}" }}, {t:.3f});')

# 2) hook (frame 0 = already set; small settle so the first frames move)
hk = PLAN["hook"]
t_hook_out = T(hk["until"])
body.append(f'''<div id="hook" class="clip" data-start="0" data-duration="{t_hook_out + 0.2:.3f}" data-track-index="4">
      <div id="hook-in"><div class="hbox h1">{esc(hk["line1"])}</div><br><div class="hbox h2">{esc(hk["line2"])} <em>{esc(hk["line2_em"])}</em><i id="hook-ul"></i></div></div>
    </div>''')
J('tl.fromTo("#hook-in", { scale: 1.04 }, { scale: 1, duration: 0.35, ease: "expo.out" }, 0);')
J('tl.fromTo("#hook-ul", { scaleX: 0 }, { scaleX: 1, duration: 0.3, ease: "power2.inOut" }, 0.55);')
J(f'tl.to("#hook-in", {{ opacity: 0, filter: "blur(8px)", duration: 0.18, ease: "power2.in" }}, {t_hook_out:.3f});')

# 3) objects
for n, o in enumerate(PLAN["objects"]):
    if o["type"] == "pagecard" and not (has(f'{args.proof_dir}/{o["proof"]}.json') and has(f'{args.proof_dir}/{o["proof"]}.png')):
        # no capture yet (run tools/capture_proof.py): leave the card out rather than show an empty or fake page
        print(f"note: page card {o['id']} skipped, {args.proof_dir}/{o['proof']}.png/.json not found")
        continue
    t_in, t_out = object_js(o)
    start = max(0.0, t_in - 0.02)
    end = min(DUR, t_out + 0.45)
    inner = RENDER[o["type"]](o)
    body.append(f'<div id="{o["id"]}" class="clip obj" data-start="{start:.3f}" data-duration="{end - start:.3f}" '
                f'data-track-index="{6 + n}" data-layout-allow-overlap><div class="mv" id="{o["id"]}-mv">{inner}</div></div>')

# 4) captions (the speaker's words, word-timed). Upcoming words dim, spoken words full, one keyword per group in the accent.
off = set()
for a, b in PLAN.get("captions_off", []):
    off.update(range(a, b + 1))
KW = set(PLAN["captions"]["keywords"])
groups = [g for g in PLAN["captions"]["groups"] if not set(range(g[0], g[1] + 1)) <= off]
cap_html = []
for g, (a, b) in enumerate(groups):
    start = max(0.1, W[a]["start"] - 0.05)
    nxt = groups[g + 1][0] if g + 1 < len(groups) else None
    natural_end = W[b]["end"] + 0.3
    end = min(DUR - 0.02, natural_end if nxt is None else min(W[nxt]["start"] - 0.05, natural_end + 0.6))
    # a group never runs into a captions-off stretch
    for i in sorted(off):
        if i > b and W[i]["start"] < end:
            end = W[i]["start"] - 0.05
            break
    st = state_at(start + 0.05)
    top, cls = CAP[st]
    spans = []
    for i in range(a, b + 1):
        word = W[i]["text"]
        kw = word in KW
        spans.append(f'<span id="cw{i}" class="cw">{esc(word)}</span>')
        J(f'tl.fromTo("#cw{i}", {{ opacity: 0.42 }}, {{ opacity: 1, {"color: " + repr(ACCENT) + ", " if kw else ""}duration: 0.06 }}, {W[i]["start"]:.3f});')
    cap_html.append(f'<div id="cg{g}" class="clip capgroup {cls}" style="top:{top}px" data-start="{start:.3f}" '
                    f'data-duration="{end - start:.3f}" data-track-index="40">{" ".join(spans)}</div>')
    J(f'tl.fromTo("#cg{g}", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.1, ease: "power2.out" }}, {start:.3f});')
    J(f'tl.to("#cg{g}", {{ opacity: 0, duration: 0.1, ease: "power2.in" }}, {end - 0.1:.3f});')

# 5) sound: start = picture moment + 1 frame - the file's measured peak; level from its measured short-term max
PEAK, MMAX, SDUR = {}, {}, {}
PEAKS = "assets/sfx/peaks.txt"                     # written by `hyperframes audio` + tools/measure_sfx.py
for line in (open(PEAKS) if has(PEAKS) else []):   # no peaks file = no measured sounds = no sounds (skipped below)
    if not re.search(r"spk ([\d.]+)", line):
        continue
    f = line.split()[0]
    PEAK[f] = float(re.search(r"spk ([\d.]+)", line).group(1))     # absolute sample peak, s
    MMAX[f] = float(re.search(r"mmax (-?[\d.]+)", line).group(1))  # max momentary loudness as played, LUFS
    SDUR[f] = float(re.search(r"dur ([\d.]+)", line).group(1))
# voice sits at -14 LUFS integrated, ~-14 LUFS momentary while speaking: effects ~8.5 dB under, the payoff ~7 dB under
SFX_TARGET = {"default": -22.5, "boom.mp3": -21.2,
              "paper-slide-2.mp3": -23.5}   # demo: measured 5.9 dB under at -22.5 because the voice was softer there
sfx_html = []
for n, (f, at, why) in enumerate(PLAN["sounds"]):
    if f not in PEAK or not has(f"assets/sfx/{f}"):
        # SFX aren't shipped: skip any sound that isn't in assets/sfx/ (or not measured yet) and add it in Edits instead
        print(f"note: sound {f} skipped (not in assets/sfx/ or not measured in {PEAKS})")
        continue
    tgt = SFX_TARGET.get(f, SFX_TARGET["default"])
    vol = min(3.9, round(10 ** ((tgt - MMAX[f]) / 20), 2))
    start = max(0.0, T(at) + 1 / FPS - PEAK[f])
    sfx_html.append(f'<audio id="sfx{n}" class="clip" src="assets/sfx/{f}" data-start="{start:.3f}" data-duration="{min(1.4 if f.startswith('boom') else 0.9, SDUR[f] - 0.01):.2f}" '
                    f'data-volume="{vol}" data-fade-out="0.12" data-track-index="{60 + n}"></audio><!-- {esc(why)} -->')

GRADE = open("grade-attr.txt").read().strip() if os.path.exists("grade-attr.txt") else ""
footage = "" if OVERLAY else (
    f'<video id="a-roll" class="clip" src="{FOOTAGE}" {GRADE} playsinline data-has-audio="true" data-volume="1" '
    f'data-start="0" data-duration="{DUR}" data-track-index="1"></video>')
ground = "transparent" if OVERLAY else INK

page = f"""<!doctype html>
<html lang="en" data-resolution="portrait">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1080, height=1920" />
<script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
<style>
  @font-face {{ font-family: "Playfair Display Italic"; src: url("assets/fonts/PlayfairDisplay-Italic.ttf"); font-style: italic; font-weight: 400 900; }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  html, body {{ width: 1080px; height: 1920px; overflow: hidden; background: {ground}; }}
  body {{ font-family: "Inter", sans-serif; color: {INK}; }}

  /* presenter: footage moves on #cam; the paper is the box-shadow of the transparent #hole */
  #cam {{ position: absolute; inset: 0; z-index: 1; }}
  #cam video {{ position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }}
  #hole {{ position: absolute; left: {HOLE["left"]}px; top: {HOLE["top"]}px; width: {HOLE["w"]}px; height: {HOLE["h"]}px;
          border-radius: {HOLE["r"]}px; z-index: 2; pointer-events: none; }}

  /* hook: two boxed lines, line 2 tinted + outlined in the accent, serif-italic accent word */
  #hook {{ position: absolute; left: 0; right: 0; top: 188px; text-align: center; z-index: 5; }}
  #hook-in {{ transform-origin: 50% 0%; }}
  .hbox {{ display: inline-block; position: relative; font: 800 70px/1.12 "Inter"; letter-spacing: -0.02em; padding: 12px 30px 16px;
          border-radius: 18px; box-shadow: 0 12px 34px rgba(16,16,18,.16); }}
  .h1 {{ background: #FFFFFF; }}
  .h2 {{ background: {ACCENT_TINT}; border: 3px solid {ACCENT}; margin-top: 12px; }}
  .h2 em {{ font: italic 800 80px/1 "Playfair Display Italic"; color: {ACCENT}; letter-spacing: -0.01em; }}
  #hook-ul {{ position: absolute; right: 30px; bottom: 12px; width: 92px; height: 6px; background: {ACCENT}; border-radius: 3px;
             transform-origin: 0 50%; }}

  /* objects: .clip is a full-frame layer; .mv is what moves (centred on x 540 / y cy by GSAP) */
  .obj {{ position: absolute; inset: 0; z-index: 6; overflow: visible; }}
  .mv {{ position: absolute; left: 0; top: 0; }}
  .chips {{ display: flex; gap: 22px; white-space: nowrap; }}
  .chip {{ display: inline-flex; align-items: center; gap: 16px; background: #FFFFFF; border: 2px solid rgba(16,16,18,.10);
          border-radius: 999px; padding: 14px 30px 14px 18px; font: 700 46px/1 "Inter"; letter-spacing: -0.01em;
          box-shadow: 0 10px 28px rgba(16,16,18,.14); }}
  .chip.sm {{ font-size: 40px; padding: 10px 24px 10px 14px; gap: 12px; box-shadow: none; }}
  .logo {{ display: block; }}
  .bigword {{ white-space: nowrap; line-height: 1; letter-spacing: -0.02em; text-align: center; }}
  .w-serif {{ font-family: "Playfair Display Italic"; font-style: italic; font-weight: 700; }}
  .w-sans {{ font-family: "Inter"; font-weight: 800; }}
  .halo {{ text-shadow: 0 0 28px rgba(247,246,243,.95), 0 0 8px rgba(247,246,243,.9); }}
  .card {{ width: 1000px; background: #FFFFFF; border-radius: 28px; border: 2px solid rgba(16,16,18,.10);
          box-shadow: 0 30px 70px rgba(16,16,18,.16), 0 3px 10px rgba(16,16,18,.08); }}
  .card.page {{ padding: 34px 40px 40px; }}
  .src {{ display: flex; align-items: center; gap: 12px; font: 600 30px/1 "Inter"; color: rgba(16,16,18,.62); margin-bottom: 22px; }}
  .src .dot {{ width: 14px; height: 14px; border-radius: 50%; background: {ACCENT}; }}
  .shot {{ position: relative; width: 920px; overflow: hidden; border-radius: 10px; }}
  .shot img {{ display: block; }}
  .hl {{ position: absolute; background: {ACCENT}; opacity: .34; mix-blend-mode: multiply; border-radius: 6px; transform-origin: 0 50%; }}
  .card.list {{ padding: 44px 52px 52px; }}
  .lhead {{ display: flex; gap: 16px; margin-bottom: 34px; }}
  .lrow {{ display: flex; align-items: center; gap: 26px; font: 800 78px/1.15 "Inter"; letter-spacing: -0.025em; }}
  .lrow + .lrow {{ margin-top: 22px; }}
  .num {{ font: italic 700 76px/1 "Playfair Display Italic"; color: {ACCENT}; width: 50px; }}
  .ltext {{ position: relative; display: inline-flex; align-items: center; gap: 18px; }}
  .tick {{ width: 70px; height: 70px; overflow: visible; }}
  .tick path {{ fill: none; stroke: {ACCENT}; stroke-width: 9; stroke-linecap: round; stroke-linejoin: round; }}
  .strike {{ position: absolute; left: -8px; right: -8px; top: 52%; height: 11px; background: {ACCENT}; border-radius: 6px; transform-origin: 0 50%; }}
  .wall {{ position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; }}
  .pills {{ position: absolute; left: 40px; top: 210px; width: 1000px; display: grid; grid-template-columns: repeat(7, 1fr); row-gap: 24px; justify-items: center; }}
  .pill {{ font: 600 30px/1 "Inter"; color: rgba(16,16,18,.26); border: 2px solid rgba(16,16,18,.13); border-radius: 999px; padding: 14px 20px; }}
  .glow {{ position: absolute; left: 0; right: 0; top: 520px; height: 760px;
          background: radial-gradient(60% 50% at 50% 50%, {SAGE} 0%, {SAGE} 55%, rgba(233,236,235,0) 100%); }}
  .wall .big {{ position: absolute; left: 0; right: 0; top: 700px; text-align: center; font-size: 210px; line-height: 1; letter-spacing: -0.02em; }}
  .subs {{ position: absolute; left: 0; right: 0; top: 965px; text-align: center; font: 800 70px/1.2 "Inter"; letter-spacing: -0.02em; }}

  /* captions */
  .capgroup {{ position: absolute; left: 0; right: 0; text-align: center; z-index: 9; padding: 0 80px; overflow: visible;
              font: 800 58px/1.15 "Inter"; letter-spacing: -0.01em; }}
  .cw {{ display: inline-block; }}
  .on-footage {{ color: #FFFFFF; text-shadow: 0 2px 3px rgba(0,0,0,.55), 0 4px 16px rgba(0,0,0,.35); }}
  .on-paper {{ color: {INK}; }}
</style>
</head>
<body>
  <div id="root" data-composition-id="main" data-start="0" data-duration="{DUR}" data-width="1080" data-height="1920">
    <div id="cam">{footage}</div>
    <div id="hole" data-layout-ignore></div>

    {chr(10).join("    " + b for b in body)}

    <div id="captions" data-track-kind="captions">
      {chr(10).join("      " + c for c in cap_html)}
    </div>

    {chr(10).join("    " + s for s in sfx_html)}
  </div>

  <script>
    const tl = gsap.timeline({{ paused: true }});
    {chr(10).join("    " + l for l in js)}
    window.__timelines = window.__timelines || {{}};
    window.__timelines["main"] = tl;
  </script>
</body>
</html>
"""
open(OUT, "w").write(page)
print(f"{OUT} written: {len(PLAN['beats'])} beats, {len(PLAN['objects'])} objects, {len(groups)} caption groups, "
      f"{len(sfx_html)} sounds{' (OVERLAY: footage hidden, transparent ground)' if OVERLAY else ''}")
