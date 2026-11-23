#!/usr/bin/env python3
"""Builds index.html (and, with --overlay, overlays.html) for the Iman Gadzhi-inspired reel. Every number is in SPEC.md.

THE RULE THIS FILE ENFORCES: only "value sentences" get a graphic (the hook claim, the big claim, each numbered reason,
the number). Everything else stays on the bare face. build.py prints the animated share of the runtime and refuses to
build above reel.json's value_budget (35%).

WHY a generator: captions must be real HTML elements with fixed times (HyperFrames rule) and every event is anchored to
a spoken word, so times come from the word file, never typed by hand. A member edits reel.json, then:
    python3 cut.py && $PY build.py && npx --yes hyperframes@0.9.83 check --json
    $PY build.py --overlay && npx --yes hyperframes@0.9.83 render -c overlays.html \
        --format mov --workers 2 -o renders/iman-gadzhi-overlays.mov && rm overlays.html
(build.py needs PIL and numpy: the skill's venv has both. overlays.html is removed after rendering because two root
compositions in one folder fail `check`.)
Flags: --config reel.json  --words assets/words-cut.json  --footage assets/cut.mp4  --overlay (graphics only, for Edits)
"""
import argparse, html, json, math, os, random, re, subprocess
from PIL import ImageFont

ap = argparse.ArgumentParser()
ap.add_argument("--config", default="reel.json")
ap.add_argument("--words", default="assets/words-cut.json")
ap.add_argument("--footage", default="assets/cut.mp4")
ap.add_argument("--overlay", action="store_true", help="write overlays.html: no footage, no audio, transparent ground")
ARGS = ap.parse_args()

CFG = json.load(open(ARGS.config))
W = json.load(open(ARGS.words))
ACCENT, INK, PAPER = CFG["accent"], CFG["ink"], CFG["paper"]
FPS, FRAME = 30, 1 / 30
ANTON = "assets/fonts/Anton-Regular.ttf"
os.makedirs("assets/sfx", exist_ok=True)      # the measure cache and placements.json live here

def ffprobe_dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                                capture_output=True, text=True, check=True).stdout)
DUR = round(math.floor(ffprobe_dur(ARGS.footage) * FPS) / FPS - FRAME, 3)   # clamp a frame under the file

# ---------------------------------------------------------------- word lookup (phrases are matched on the cut clock)
def norm(t):
    return re.sub(r"[^a-z0-9'\-]", "", t.lower().replace("’", "'"))
TOK = [norm(w["text"]) for w in W]

def find(phrase, after=0.0):
    """Index of the first word of `phrase` (case/punctuation ignored) starting at or after `after` seconds."""
    p = [norm(x) for x in phrase.split()]
    for i in range(len(W) - len(p) + 1):
        if W[i]["start"] >= after - 1e-6 and TOK[i:i + len(p)] == p:
            return i
    raise SystemExit(f"phrase not found in {ARGS.words}: {phrase!r} (after {after}s)")

def last(phrase, after=0.0):
    return find(phrase, after) + len(phrase.split()) - 1

# ---------------------------------------------------------------- type fitting (Anton measured with PIL, not guessed)
def anton_w(text, px, track=0.0):
    return ImageFont.truetype(ANTON, px).getlength(text) + track * px * max(0, len(text) - 1)

def fit(text, base, floor, max_w, track=0.0):
    px = base
    while px > floor and anton_w(text, px, track) > max_w:
        px -= 2
    return px

if not os.path.exists("assets/grain.png"):
    import numpy as np
    from PIL import Image
    g = np.clip(np.random.default_rng(11).normal(128, 34, (960, 540)), 0, 255).astype("uint8")
    Image.fromarray(g, "L").save("assets/grain.png", optimize=True)

# ================================================================ EVENT TIMES (all derived from spoken words)
EVENTS = []          # (name, start, end) of every value graphic, for the 35% budget

hook = CFG["hook"]
HOOK_OUT = W[find(hook["out_on"])]["start"]
HOOK_STAMP = W[find(hook["stamp_on"])]["start"]
EVENTS.append(("hook", 0.0, HOOK_OUT + 0.2))

majors = []
for m in CFG["majors"]:
    i0 = find(m["phrase"])
    i1 = i0 + len(m["phrase"].split()) - 1
    t_in = W[find(m["in_on"], W[i0]["start"])]["start"] if m.get("in_on") else W[i0]["start"]
    t_out = min(W[i1]["end"] + m.get("tail", 0.12), DUR)
    if i1 + 1 < len(W):                        # never run into the next sentence's first word by more than 0.1 s
        t_out = min(t_out, W[i1 + 1]["start"] + 0.08)
    majors.append(dict(m, i0=i0, i1=i1, t_in=round(t_in, 3), t_out=round(t_out, 3)))
    EVENTS.append((f"major-{len(majors)}", t_in, t_out))

MAP_ON = W[find(CFG["map"]["on"])]["start"]

chapters = []
for c in CFG["chapters"]:
    i0 = find(c["on"])
    t_out = W[last(c["out_after"], W[i0]["start"])]["end"] + c.get("hold", 0.2)
    chapters.append(dict(c, i0=i0, t_in=round(W[i0]["start"], 3), t_out=round(t_out, 3)))
    EVENTS.append((f"chapter-{c['n']}", W[i0]["start"] - 0.02, t_out + 0.22))   # visible span incl. the exit

animated = sum(b - a for _, a, b in EVENTS)
SHARE = animated / DUR
print(f"animated: {animated:.2f}s of {DUR:.2f}s = {SHARE:.1%} (budget {CFG['value_budget']:.0%})")
for n, a, b in EVENTS:
    print(f"  {n:10s} {a:6.2f} -> {b:6.2f}  ({b - a:.2f}s)")
if SHARE > CFG["value_budget"] + 1e-9:
    raise SystemExit("over the animation budget: shorten holds/tails or drop the weakest event")

# ================================================================ CAMERA: hard-cut punch-ins hide every jump cut
SEAMS, acc = [], 0.0
for a, b in CFG["keep"][:-1]:
    acc += (b - a) / CFG["speed"]
    SEAMS.append(round(acc, 3))
PUNCH = [1.08, 1.0, 1.06, 1.0, 1.08, 1.0, 1.06, 1.0]   # alternating scale after each seam; max 1.08 so the chin
                                                      # (y~1390 in the demo) stays above the captions
CAM = [(0.0, 1.0)]
for k, s in enumerate(SEAMS):
    CAM.append((s, PUNCH[k % len(PUNCH)]))
EP = CFG.get("emphasis_punch")                        # optional: one emphasis punch inside the hook sentence
if EP:
    CAM += [(W[find(EP["on"])]["start"], 1.08), (W[find(EP["off"])]["start"], 1.0)]
CAM.sort()

# ================================================================ CAPTIONS (the speaker's words, proofread in cut.py)
def in_major(t):
    return any(m["t_in"] - 0.02 <= t < m["t_out"] for m in majors)

def clean(t):
    t = t.replace("’", "'")
    return re.sub(r"[.,]+$", "", t)

groups, cur = [], []
for i, w in enumerate(W):
    if in_major(w["start"]):
        if cur: groups.append(cur); cur = []
        continue
    if cur:
        prev = W[cur[-1]]
        seam = any(prev["start"] < s <= w["start"] + 0.01 for s in SEAMS)       # never caption across a jump cut
        brk = (seam or len(cur) >= 3 or re.search(r"[.,?!]$", prev["text"]) or w["start"] - prev["end"] > 0.15
               or len(" ".join(clean(W[j]["text"]) for j in cur + [i])) > 22)
        if brk: groups.append(cur); cur = []
    cur.append(i)
if cur: groups.append(cur)

cap_html, cap_js = [], []
for g, idx in enumerate(groups):
    a, b = idx[0], idx[-1]
    start = max(0.1, W[a]["start"] - 0.05)
    nxt = groups[g + 1][0] if g + 1 < len(groups) else None
    end = W[b]["end"] + 0.3
    if nxt is not None: end = min(end, W[nxt]["start"] - 0.05)
    for m in majors:                                                  # captions are off during full-screen majors
        if start < m["t_in"] < end: end = m["t_in"] - 0.02
    end = min(end, DUR)
    if end - start < 0.2: end = start + 0.2
    spans = " ".join(f'<span id="cw{i}" class="cw">{html.escape(clean(W[i]["text"]))}</span>' for i in idx)
    cap_html.append(f'<div id="cg{g}" class="clip capgroup" data-start="{start:.3f}" data-duration="{end - start:.3f}" '
                    f'data-track-index="20">{spans}</div>')
    cap_js.append(f'tl.fromTo("#cg{g}", {{opacity: 0, y: 10}}, {{opacity: 1, y: 0, duration: 0.12, ease: "power3.out"}}, {start:.3f});')
    for k, i in enumerate(idx):                                       # active word gets the accent block
        cap_js.append(f'tl.set("#cw{i}", {{backgroundColor: "{ACCENT}"}}, {W[i]["start"]:.3f});')
        if k < len(idx) - 1:
            cap_js.append(f'tl.set("#cw{i}", {{backgroundColor: "rgba(34, 48, 232, 0)"}}, {W[idx[k + 1]]["start"]:.3f});')
    cap_js.append(f'tl.to("#cg{g}", {{opacity: 0, duration: 0.08, ease: "power2.in"}}, {end - 0.08:.3f});')

# ================================================================ SOUND: placed by measured peak, levelled by measured loudness
SFX_TARGET = CFG.get("sfx_target_lufs", -22.0)   # momentary max of each hit = voice (-14) minus 8 dB (spec: 6-10 dB under)
CACHE_P = "assets/sfx/measure.json"
CACHE = json.load(open(CACHE_P)) if os.path.exists(CACHE_P) else {}

def measure(f, ms, d):
    """Peak time (s, inside the slice) and momentary-max loudness (LUFS, 400 ms) of a slice of an effect file."""
    key = f"{f}|{ms}|{d}"
    if key not in CACHE:
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(ms), "-t", str(d), "-i", f"assets/sfx/{f}",
                              "-ac", "1", "-ar", "48000", "-f", "f32le", "-"], capture_output=True, check=True).stdout
        import numpy as np
        x = np.frombuffer(raw, dtype=np.float32)
        hop = 240                                                    # 5 ms
        env = np.array([np.sqrt(np.mean(x[k:k + hop] ** 2)) for k in range(0, len(x) - hop, hop)])
        peak_t = float(np.argmax(env) * hop / 48000)
        out = subprocess.run(["ffmpeg", "-v", "info", "-ss", str(ms), "-t", str(d), "-i", f"assets/sfx/{f}",
                              "-af", "apad=pad_dur=0.5,ebur128=metadata=1,ametadata=print:key=lavfi.r128.M",
                              "-f", "null", "-"], capture_output=True, text=True).stderr
        mvals = [float(v) for v in re.findall(r"lavfi.r128.M=(-?[\d.]+)", out)]
        CACHE[key] = {"peak": round(peak_t, 3), "mmax": max(mvals)}
        json.dump(CACHE, open(CACHE_P, "w"), indent=1)
    return CACHE[key]

SFX = []   # (id, file, picture_time, media_start, duration)
def sfx(id_, f, picture, ms=0.0, d=0.6):
    # SFX aren't shipped with the template: a sound whose file isn't in assets/sfx/ is skipped (add it in Edits instead)
    if os.path.exists(f"assets/sfx/{f}"):
        SFX.append((id_, f, picture, ms, d))

# ================================================================ HTML pieces
def letters(text, cls):
    return "".join(f'<span class="{cls}">{html.escape(ch) if ch != " " else "&nbsp;"}</span>' for ch in text)

rng = random.Random(7)
def doodles(opacity, seed):
    """Faint hand-drawn scribbles for the field texture (seeded, so every render is identical)."""
    r = random.Random(seed)
    out = []
    for k in range(16):
        x, y = r.uniform(40, 1040), r.uniform(80, 1860)
        kind = k % 5
        if kind == 0:   # squiggle
            d = f"M{x:.0f} {y:.0f}" + "".join(f" q{r.uniform(15,30):.0f} {(-1)**j*r.uniform(18,34):.0f} {r.uniform(34,54):.0f} 0" for j in range(5))
        elif kind == 1: # spiral
            d = f"M{x:.0f} {y:.0f}" + "".join(f" a{6+j*7} {6+j*7} 0 0 1 {(-1)**j*(12+j*14)} 0" for j in range(5))
        elif kind == 2: # star
            pts = [(x + math.cos(a) * (34 if j % 2 == 0 else 14), y + math.sin(a) * (34 if j % 2 == 0 else 14))
                   for j, a in enumerate([-math.pi / 2 + j * math.pi / 5 for j in range(10)])]
            d = "M" + " L".join(f"{px:.0f} {py:.0f}" for px, py in pts) + " Z"
        elif kind == 3: # arrow
            d = f"M{x:.0f} {y:.0f} q60 -50 120 -10 m-26 -24 l26 24 l-34 12"
        else:           # loop + cross
            d = f"M{x:.0f} {y:.0f} c40 -40 80 30 30 40 c-40 8 -30 -50 30 -40 M{x+90:.0f} {y-20:.0f} l24 24 m0 -24 l-24 24"
        out.append(f'<path d="{d}" />')
    return (f'<svg class="doodles" viewBox="0 0 1080 1920" style="opacity:{opacity}">' + "".join(out) + "</svg>")

def tape_edges(seed, w, h):
    """Torn-tape polygon: straight top/bottom, jagged ends (seeded)."""
    r = random.Random(seed)
    left = [(r.uniform(0, 10), y) for y in range(0, h + 1, max(8, h // 9))]
    right = [(w - r.uniform(0, 10), y) for y in range(h, -1, -max(8, h // 9))]
    return "polygon(" + ", ".join(f"{x:.0f}px {y:.0f}px" for x, y in left + right) + ")"

# ---------------- layout: everything over the footage lives in the TOP BAND, y 280-550 (Instagram/Shorts top UI ends
# ~280 px, the demo's hairline was at ~555 px), x 100-900 (TikTok side margins, YouTube Shorts action rail).
X0, TEXT_MAX_W = 100, 790
NOTE_Y, TAPE_Y = 300, 382          # handwritten line, then the tape strip under it

# ---------------- hook (frame 0 = the hook already on screen)
HOOK_PX = fit(hook["hero"], 140, 110, TEXT_MAX_W - 200, 0.01)   # leaves room for the stamp at the tape end
HOOK_W = int(anton_w(hook["hero"], HOOK_PX, 0.01) + 2 * 34)
HOOK_H = int(HOOK_PX * 1.06 + 18)
hook_html = f"""
    <div id="hook" class="clip" data-start="0" data-duration="{HOOK_OUT + 0.2:.3f}" data-track-index="4" data-layout-allow-overlap>
      <div id="hook-note-w" class="note-w" style="left:{X0 + 10}px; top:{NOTE_Y - 4}px"><svg id="hook-note" class="note-svg"></svg></div>
      <div id="hook-tape" class="tape-w" style="left:{X0 - 6}px; top:{TAPE_Y - 10}px; width:{HOOK_W}px; height:{HOOK_H}px">
        <div class="tape-bg" data-layout-allow-occlusion style="clip-path:{tape_edges(3, HOOK_W, HOOK_H)}"></div><span class="tape-text" style="font-size:{HOOK_PX}px">{letters(hook['hero'], 'hk')}</span></div>
      <div id="hook-stamp" class="stamp" style="left:{X0 + HOOK_W - 22}px; top:{TAPE_Y - 10 + HOOK_H // 2 - 46}px">{html.escape(hook['stamp'])}</div>
    </div>"""
sfx("sfx-stamp-hook", "stamp-1.mp3", HOOK_STAMP + 0.06, 0.0, 0.2)

# ---------------- progress rail (the chapter device: numbered boxes, lit as each reason is reached)
N = CFG["map"]["count"]
rail_boxes = "".join(f'<div id="rb{k}" class="rbox"><span>{k}</span></div>' for k in range(1, N + 1))
rail_html = f"""
    <div id="rail" class="clip" style="left:{X0}px; top:{NOTE_Y + 2}px" data-start="{MAP_ON:.3f}" data-duration="{DUR - MAP_ON:.3f}" data-track-index="6">{rail_boxes}</div>"""

# ---------------- chapters
chap_html = []
for c in chapters:
    n = c["n"]
    px = fit(c["title"], 118, 90, TEXT_MAX_W - 60, 0.01)
    w = int(anton_w(c["title"], px, 0.01) + 2 * 30)
    h = int(px * 1.06 + 16)
    c["label"] = c["label"]                                         # the speaker's own words, e.g. "one" / "number two"
    chap_html.append(f"""
    <div id="ch{n}" class="clip" data-start="{c['t_in'] - 0.02:.3f}" data-duration="{c['t_out'] - c['t_in'] + 0.24:.3f}" data-track-index="{7 + n}" data-layout-allow-overlap>
      <div id="ch{n}-note-w" class="note-w" style="left:{X0 + 262}px; top:{NOTE_Y - 2}px"><svg id="ch{n}-note" class="note-svg"></svg></div>
      <div id="ch{n}-tape" class="tape-w" style="left:{X0 - 6}px; top:{TAPE_Y}px; width:{w}px; height:{h}px">
        <div class="tape-bg" data-layout-allow-occlusion style="clip-path:{tape_edges(10 + n, w, h)}"></div><span class="tape-text" style="font-size:{px}px">{letters(c['title'], f'c{n}l')}</span></div>
    </div>""")
    sfx(f"sfx-ch{n}", ["whoosh-a.mp3", "whoosh-b.mp3", "whoosh-c.mp3"][(n - 1) % 3], c["t_in"] + 0.12, 0.0,
        [1.0, 0.7, 0.5][(n - 1) % 3])

# ---------------- majors
major_html = []
for k, m in enumerate(majors, 1):
    field = "field-accent" if m["kind"] == "accent" else "field-black"
    dur = m["t_out"] - m["t_in"]
    if m["kind"] == "accent":
        hero_px = fit(m["hero"], 320, 200, 660, 0.01)
        small_px = 118
        notes = "".join(f"""
        <g transform="translate({x} {y}) rotate({rot})"><g class="bill" id="m{k}b{j}">
          <rect x="-260" y="-118" width="520" height="236" rx="10" class="bill-paper"/>
          <rect x="-236" y="-94" width="472" height="188" rx="6" class="bill-line"/>
          <circle cx="0" cy="0" r="64" class="bill-line"/>
          <text x="0" y="30" class="bill-sign">$</text>
          <path d="M-200 -60 h70 M-200 -38 h50 M130 60 h70 M150 38 h50" class="bill-line"/>
        </g></g>""" for j, (x, y, rot) in enumerate([(350, 210, -9), (370, 190, 6), (340, 175, -3), (360, 160, 11)]))
        major_html.append(f"""
    <div id="mj{k}" class="clip major {field}" data-start="{m['t_in']:.3f}" data-duration="{dur:.3f}" data-track-index="{12 + k}" data-layout-allow-overlap data-layout-allow-occlusion>
      <div class="grain"></div>{doodles(0.16, 20 + k)}
      <svg id="mj{k}-cash" class="cash" viewBox="0 0 720 400">{notes}</svg>
      <div id="mj{k}-small" class="mj-small" style="font-size:{small_px}px">{letters(m['small'], f'm{k}s')}</div>
      <div id="mj{k}-hero" class="mj-hero" style="font-size:{hero_px}px">{letters(m['hero'], f'm{k}h')}</div>
      <div id="mj{k}-note-w" class="note-w center" style="top:{int(470 + hero_px * 0.92) + 14}px"><svg id="mj{k}-note" class="note-svg"></svg>
        <svg class="squig" id="mj{k}-squig-svg" width="10" height="40"><path id="mj{k}-squig"/></svg></div>
    </div>""")
        t_small = W[find(m["small"].split()[0], m["t_in"])]["start"]
        t_hero = W[find(m["hero"], m["t_in"])]["start"]
        t_note = W[find(m["note_on"], m["t_in"])]["start"] - 0.04
        m.update(t_small=t_small, t_hero=t_hero, t_note=t_note)
        sfx(f"sfx-m{k}-in", "page-turn.mp3", m["t_in"], 0.0, 0.45)
        sfx(f"sfx-m{k}-bills", "card-clack.mp3", m["t_in"] + 0.30, 0.0, 0.3)
        sfx(f"sfx-m{k}-pen", "pen.mp3", t_note + 0.05, 0.04, 0.85)
    else:
        num_px = 480
        tape_px = 92
        tw = int(anton_w(m["tape"], tape_px, 0.01) + 2 * 26)
        th = int(tape_px * 1.06 + 14)
        major_html.append(f"""
    <div id="mj{k}" class="clip major {field}" data-start="{m['t_in']:.3f}" data-duration="{dur:.3f}" data-track-index="{12 + k}" data-layout-allow-overlap data-layout-allow-occlusion>
      <div class="grain"></div>{doodles(0.09, 30 + k)}
      <div id="mj{k}-note-w" class="note-w center" style="top:420px"><svg id="mj{k}-note" class="note-svg"></svg></div>
      <div id="mj{k}-num" class="mj-num" style="font-size:{num_px}px"><span id="mj{k}-digits">{m['from']}</span><span class="acc">{html.escape(m['suffix'])}</span></div>
      <div id="mj{k}-tape" class="tape-w tape-accent" style="left:{(1080 - tw) // 2}px; top:1040px; width:{tw}px; height:{th}px">
        <div class="tape-bg" data-layout-allow-occlusion style="clip-path:{tape_edges(40 + k, tw, th)}"></div><span class="tape-text" style="font-size:{tape_px}px">{html.escape(m['tape'])}</span></div>
    </div>""")
        t_land = W[find(m["phrase"].split()[-1], m["t_in"])]["start"]   # the number word itself
        m.update(t_land=t_land, t_tape=t_land + 0.12)
        sfx(f"sfx-m{k}-thud", "thud.mp3", t_land, 0.0, 0.9)
        sfx(f"sfx-m{k}-tape", "stamp-2.mp3", t_land + 0.12 + 0.10, 0.0, 0.2)

# ================================================================ TIMELINE SCRIPT
js = []
def J(s): js.append(s)

# camera: hard cuts only (gsap.set), never a creeping zoom
for t, s in CAM:
    J(f'tl.set("#cam", {{scale: {s}}}, {t:.3f});')

# hook: frame 0 already shows the note and the tape; the stamp slaps on stamp_on; whole hook whips up and out on out_on
J('hwOn(tl, NOTES.hook, 0);')
J('tl.fromTo("#hook-tape", {scale: 1.04, rotation: -2.6}, {scale: 1, rotation: -2, duration: 0.4, ease: "expo.out"}, 0);')
J(f'tl.fromTo("#hook-stamp", {{opacity: 0, scale: 1.7, rotation: 14, filter: "blur(8px)"}}, {{opacity: 1, scale: 1, rotation: 8, filter: "blur(0px)", duration: 0.12, ease: "power3.in"}}, {HOOK_STAMP - 0.06:.3f});')
J(f'tl.fromTo("#hook-tape", {{y: 0}}, {{y: 8, duration: 0.06, ease: "power2.out", yoyo: true, repeat: 1, immediateRender: false}}, {HOOK_STAMP + 0.06:.3f});')
J(f'tl.to(["#hook-tape", "#hook-stamp", "#hook-note-w"], {{y: -260, opacity: 0, filter: "blur(10px)", duration: 0.2, ease: "power3.in"}}, {HOOK_OUT - 0.04:.3f});')

# rail: the boxes stamp in on map.on, e.g. "here's why" (the open loop: the whole map is visible before reason one)
J(f'tl.fromTo("#rail .rbox", {{opacity: 0, scale: 1.5, filter: "blur(6px)"}}, {{opacity: 1, scale: 1, filter: "blur(0px)", duration: 0.16, ease: "expo.out", stagger: 0.07}}, {MAP_ON:.3f});')

for c in chapters:
    n, t0, t1 = c["n"], c["t_in"], c["t_out"]
    J(f'tl.to("#rb{n}", {{backgroundColor: "{ACCENT}", borderColor: "{ACCENT}", duration: 0.1, ease: "power2.out"}}, {t0:.3f});')
    J(f'tl.fromTo("#rb{n}", {{scale: 1.35}}, {{scale: 1, duration: 0.3, ease: "expo.out", immediateRender: false}}, {t0:.3f});')
    J(f'tl.set("#rb{n} span", {{color: "#FFFFFF", opacity: 1}}, {t0:.3f});')
    J(f'hwWrite(tl, NOTES.ch{n}, {t0 + 0.02:.3f}, 0.38);')
    J(f'tl.fromTo("#ch{n}-tape", {{clipPath: "inset(0 100% 0 0)", x: -40, rotation: -1.5}}, {{clipPath: "inset(0 0% 0 0)", x: 0, rotation: -1.5, duration: 0.26, ease: "power4.out"}}, {t0 + 0.04:.3f});')
    J(f'tl.fromTo("#ch{n} .c{n}l", {{clipPath: "inset(0 100% 0 0)"}}, {{clipPath: "inset(0 0% 0 0)", duration: 0.09, ease: "steps(3)", stagger: 0.032}}, {t0 + 0.1:.3f});')
    # out: the title collapses back toward its lit box on the rail (old items shrink away; the box keeps the progress)
    J(f'tl.to("#ch{n}-tape", {{scaleX: 0, x: -30, transformOrigin: "0% 50%", filter: "blur(6px)", duration: 0.2, ease: "power3.in"}}, {t1:.3f});')
    J(f'tl.to("#ch{n}-note-w", {{opacity: 0, x: -30, filter: "blur(6px)", duration: 0.16, ease: "power2.in"}}, {t1:.3f});')

for k, m in enumerate(majors, 1):
    if m["kind"] == "accent":
        # bills fall in on the cut, stop-motion stepped (12 fps feel), each one lands a little later
        for j in range(4):
            J(f'tl.fromTo("#m{k}b{j}", {{y: -720, opacity: 1}}, {{y: 0, duration: 0.34, ease: stepEase("power3.out", 6)}}, {m["t_in"] + 0.02 + j * 0.07:.3f});')
        J(f'tl.fromTo("#mj{k} .m{k}s", {{clipPath: "inset(0 100% 0 0)"}}, {{clipPath: "inset(0 0% 0 0)", duration: 0.08, ease: "steps(3)", stagger: 0.035}}, {m["t_small"] - 0.03:.3f});')
        J(f'tl.fromTo("#mj{k} .m{k}h", {{clipPath: "inset(0 100% 0 0)"}}, {{clipPath: "inset(0 0% 0 0)", duration: 0.1, ease: "steps(3)", stagger: 0.045}}, {m["t_hero"] - 0.03:.3f});')
        J(f'hwWrite(tl, NOTES.mj{k}, {m["t_note"]:.3f}, 0.7);')
        J(f'squiggle(tl, "mj{k}-squig", NOTES.mj{k}.wPx, {m["t_note"] + 0.72:.3f});')
    else:
        J(f'hwWrite(tl, NOTES.mj{k}, {m["t_in"] + 0.02:.3f}, 0.36);')
        J(f'counter(tl, "#mj{k}-digits", {m["from"]}, {m["to"]}, {m["t_in"] + 0.04:.3f}, {m["t_land"]:.3f});')
        J(f'tl.fromTo("#mj{k}-num", {{scale: 1.18, filter: "blur(4px)"}}, {{scale: 1, filter: "blur(0px)", duration: 0.24, ease: "expo.out", immediateRender: false}}, {m["t_land"]:.3f});')
        J(f'tl.fromTo("#mj{k}-tape", {{opacity: 0, scale: 1.7, rotation: -14, filter: "blur(8px)"}}, {{opacity: 1, scale: 1, rotation: -7, filter: "blur(0px)", duration: 0.1, ease: "power3.in"}}, {m["t_tape"]:.3f});')

# note texts (built once from the baked Caveat pen table, then written on by the timeline)
NOTE_DEFS = {"hook": (hook["note"], 86, ACCENT)}
for c in chapters:
    NOTE_DEFS[f"ch{c['n']}"] = (c["label"], 66, ACCENT)
for k, m in enumerate(majors, 1):
    NOTE_DEFS[f"mj{k}"] = (m["note"], 104 if m["kind"] == "accent" else 96, PAPER)
notes_js = ",\n      ".join(f'{k}: hwBuild("{k.replace("hook", "hook")}", {json.dumps(t)}, {px}, "{col}")' for k, (t, px, col) in NOTE_DEFS.items())

# ================================================================ SOUND HTML
sfx_html = []
if not ARGS.overlay:
    for n, (id_, f, picture, ms, d) in enumerate(SFX):
        meas = measure(f, ms, d)
        start = picture + FRAME - meas["peak"]               # the hit lands one frame after its picture
        vol = min(3.98, 10 ** ((SFX_TARGET - meas["mmax"]) / 20))
        if start < 0:
            ms, d, start = ms - start, d + start, 0.0
        media = f' data-media-start="{ms:.3f}"' if ms > 0 else ""
        sfx_html.append(f'<audio id="{id_}" class="clip" src="assets/sfx/{f}"{media} data-start="{start:.3f}" data-duration="{d:.3f}" '
                        f'data-volume="{vol:.3f}" data-fade-out="0.06" data-track-index="{30 + n}"></audio>')
    json.dump([{"id": i, "file": f, "picture": round(p, 3), "media_start": ms, "duration": d,
                "peak_in_slice": measure(f, ms, d)["peak"], "mmax_lufs": measure(f, ms, d)["mmax"]} for i, f, p, ms, d in SFX],
              open("assets/sfx/placements.json", "w"), indent=1)

GRADE = open("grade-attr.txt").read().strip() if os.path.exists("grade-attr.txt") else ""

# ================================================================ PAGE
footage = "" if ARGS.overlay else f"""<video id="a-roll" class="clip" src="{ARGS.footage}" {GRADE} playsinline data-has-audio="true" data-volume="1"
             data-start="0" data-duration="{DUR}" data-track-index="1"></video>"""
ground = "transparent" if ARGS.overlay else INK

page = open("src/page.template.html").read()
for k, v in {
    "%%DUR%%": f"{DUR}", "%%ACCENT%%": ACCENT, "%%INK%%": INK, "%%PAPER%%": PAPER, "%%GROUND%%": ground,
    "%%FOOTAGE%%": footage, "%%HOOK%%": hook_html, "%%RAIL%%": rail_html, "%%CHAPTERS%%": "".join(chap_html),
    "%%MAJORS%%": "".join(major_html), "%%CAPTIONS%%": "\n      ".join(cap_html), "%%SFX%%": "\n    ".join(sfx_html),
    "%%NOTES%%": notes_js, "%%TIMELINE%%": "\n    ".join(js), "%%CAPJS%%": "\n    ".join(cap_js),
}.items():
    page = page.replace(k, v)
out = "overlays.html" if ARGS.overlay else "index.html"
open(out, "w").write(page)
print(f"{out} written: {DUR}s, {len(groups)} caption groups, {len(SFX) if not ARGS.overlay else 0} sounds, "
      f"{len(SEAMS)} seams punched")
