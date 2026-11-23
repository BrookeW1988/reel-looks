#!/usr/bin/env python3
"""Builds the "inspired by Nana DelRey" reel (index.html) and, with --overlay, its transparent Edits overlay.

Every number is explained in SPEC.md. A member's version changes reel.json, not this file:
    footage / cutout / words   -> their rough cut, its person cut-out, its word timings
    stacks                     -> which spoken phrases become giant word stacks, and the lilac payoff word(s)
    bed                        -> their music bed and where it enters (optional: no file = no bed)
Media isn't shipped: a missing music bed or cut-out is left out with a note, never a crash. The font must be in
assets/fonts/ (it is measured to lay the words out).
Run:
    python3 build.py                 # writes index.html (the reel) and applies both grades
    python3 build.py --overlay       # writes index.html as the transparent Edits overlay (render it, then rebuild)
    python3 build.py --config other.json
    python3 build.py --debug-no-cutout   # same, but hides the cut-out (used to measure how much of each giant word the head covers)

WHY a generator: in HyperFrames every timed element must be written in the HTML with fixed times, and the subtitle
chunks and stack words come from the word timings. Hand-writing ~60 timed elements is where mistakes creep in.
"""
import argparse, html, json, math, os, re, subprocess
from PIL import ImageFont

def has(p):
    """True if a media file is there (why: fonts, music and renders aren't shipped; skip, never crash)."""
    return bool(p) and os.path.exists(p)

W, H, FPS = 1080, 1920, 30
FONT_FILE = "assets/fonts/InterTight-VariableFont_wght.ttf"
if not has(FONT_FILE):   # the only file the build can't do without: every line is laid out from measured widths
    raise SystemExit(f"{FONT_FILE} not found: download Inter Tight (variable) from https://fonts.google.com/specimen/Inter+Tight")

# ---- palette (SPEC.md section 1, sampled from her reels) ----
COL = {"butter": "#F8F49C", "lilac": "#E4C8EC", "cream": "#FCF4AC", "white": "#FCF8FC"}

# ---- type (SPEC.md section 2, adapted to 1080 wide) ----
SMALL = {"size": 76, "weight": 700, "track": -0.03}   # connector lines in a stack
HERO = {"max_size": 236, "weight": 800, "track": -0.05, "max_width": 900}
SUB = {"weight": 400, "track": -0.02}
LEAD = 0.86                                           # stack line-height (her leading ~0.85)
STACK_X = 90                                          # stack box = x 90..990 (900 wide)
MIN_HOLD = 0.45                                       # a stack never cuts off sooner than this after its last word lands

ap = argparse.ArgumentParser()
ap.add_argument("--config", default="reel.json")
ap.add_argument("--debug-no-cutout", action="store_true")
ap.add_argument("--overlay", action="store_true", help="write index.html as the transparent Edits overlay variant")
args = ap.parse_args()
C = json.load(open(args.config))
WORDS = json.load(open(C["words"]))
CUTS = C.get("shot_cuts", [])

def run(cmd):
    return subprocess.run(cmd, check=True, capture_output=True, text=True)

DUR = math.floor(float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                            C["footage"]]).stdout) * FPS) / FPS          # whole frames, never past the file

def fr(t):  # snap to the frame grid, never later than the word (light arrives before sound)
    return max(0.0, math.floor(t * FPS + 1e-6) / FPS)

def cut_frame(c):  # first frame of the new shot (ffmpeg keeps frames with pts < the cut in the old shot)
    return math.ceil(c * FPS - 1e-6) / FPS

def norm(t):
    return re.sub(r"[^a-z0-9']", "", t.lower())

def show(t):  # her subtitles: all lowercase, no full stops or commas
    return re.sub(r"[.,!?;:]", "", t.lower())

_fonts = {}
def width(text, size, weight, track):
    key = (size, weight)
    if key not in _fonts:
        f = ImageFont.truetype(FONT_FILE, size); f.set_variation_by_axes([weight]); _fonts[key] = f
    return _fonts[key].getlength(text) + track * size * len(text)

# ---- 1. locate each stack's words in the transcript (in order) ----
cursor, stacks = 0, []
for st in C["stacks"]:
    toks = [(li, tok) for li, line in enumerate(st["lines"]) for tok in line["text"].split()]
    want = [norm(t) for _, t in toks]
    for i in range(cursor, len(WORDS) - len(want) + 1):
        if [norm(w["text"]) for w in WORDS[i:i + len(want)]] == want:
            break
    else:
        raise SystemExit(f"stack '{st['id']}': phrase not found in {C['words']} after word {cursor}")
    idx = list(range(i, i + len(want)))
    cursor = idx[-1] + 1
    start = 0.0 if fr(WORDS[idx[0]]["start"]) <= 3 / FPS else fr(WORDS[idx[0]]["start"])  # frame 0 carries text
    last = WORDS[idx[-1]]["start"]
    if "until" in st:                     # hold until a named later word (that word's subtitle starts the next line)
        j = next(k for k in range(cursor, len(WORDS)) if norm(WORDS[k]["text"]) == norm(st["until"]))
        end = fr(WORDS[j]["start"])
    else:                                 # her rule: cut off on the next phrase or the next shot change
        nxt = WORDS[cursor]["start"] if cursor < len(WORDS) else DUR
        end = fr(max(nxt, last + MIN_HOLD))
    for c in CUTS:
        if start < c < end:
            end = cut_frame(c)                  # off on the shot change, not a frame before it
        if c <= start <= c + 0.15:
            start = cut_frame(c)                # a stack that opens just after a cut opens on the cut
    stacks.append({**st, "idx": idx, "toks": toks, "start": start, "end": min(end, DUR)})

stacked = {i for s in stacks for i in s["idx"]}
windows = [(s["start"], s["end"]) for s in stacks]
def in_stack(t):
    return any(a <= t < b for a, b in windows)

# ---- 2. subtitles: her three-slot line (left, centre, right), filled in that order, cleared together ----
# Landscape slots are fixed points; on a 1080-wide frame the chunks are wide relative to the line, so each line is
# laid out from its measured chunk widths: chunk 1 starts at slot_left_x, chunk 3 ends at slot_right_x, chunk 2 sits
# on the centre line unless that would crowd a neighbour, then it centres in the free space between them.
S = C["subtitles"]
size, GAP = S["size"], S.get("min_gap", 40)
LINE_W = S["slot_right_x"] - S["slot_left_x"]
def sw(text):
    return width(text, size, SUB["weight"], SUB["track"])

sub_words = [i for i, w in enumerate(WORDS) if i not in stacked and not in_stack(w["start"])]
lines = []                                   # each line = list of chunks, each chunk = list of word indices
if C.get("subtitle_lines"):                  # hand-set breaks (the spoken words, in order; checked below)
    pos = 0
    for ln in C["subtitle_lines"]:
        line = []
        for ch in ln:
            ch = ch.lstrip(">")
            n = len(ch.split())
            got = [norm(WORDS[k]["text"]) for k in sub_words[pos:pos + n]]
            if got != [norm(t) for t in ch.split()]:
                raise SystemExit(f"subtitle_lines: '{ch}' does not match the spoken words {got}")
            line.append(sub_words[pos:pos + n]); pos += n
        lines.append(line)
    if pos != len(sub_words):
        raise SystemExit("subtitle_lines leaves words out: " + " ".join(WORDS[k]["text"] for k in sub_words[pos:]))
else:                                        # automatic: break at sentence ends, pauses, stacks, shot cuts, width
    line, chunk, prev = [], [], None
    def line_w(chs):
        return sum(sw(" ".join(show(WORDS[k]["text"]) for k in c)) for c in chs) + GAP * (len(chs) - 1)
    for i in sub_words:
        if prev is not None:
            gap = WORDS[i]["start"] - WORDS[prev]["end"]
            hard = (WORDS[prev]["text"].rstrip()[-1:] in ".?!" or gap >= 0.40 or i != prev + 1
                    or any(WORDS[prev]["start"] < c <= WORDS[i]["start"] for c in CUTS))
            if hard:
                line.append(chunk); lines.append(line); line, chunk = [], []
            elif gap >= 0.15 or len(chunk) >= S["max_chunk_words"]:
                line.append(chunk); chunk = []
                if len(line) == 3:
                    lines.append(line); line = []
            if chunk and line_w(line + [chunk + [i]]) > LINE_W:
                line.append(chunk); chunk = []
                if len(line) == 3 or line_w(line + [[i]]) > LINE_W:
                    lines.append(line); line = []
        chunk.append(i); prev = i
    line.append(chunk); lines.append(line)

def layout(texts, right_pins=()):
    ws = [sw(t) for t in texts]
    xs = [S["slot_left_x"]]
    if len(texts) == 2 and 1 in right_pins:       # left + right, centre slot left empty
        xs.append(S["slot_right_x"] - ws[1])
        return [round(x) for x in xs], ws
    if len(texts) == 3:
        right_x = S["slot_right_x"] - ws[2]
        free_a, free_b = xs[0] + ws[0] + GAP, right_x - GAP
        x1 = W / 2 - ws[1] / 2
        if x1 < free_a or x1 + ws[1] > free_b:
            x1 = (free_a + free_b - ws[1]) / 2
        xs += [x1, right_x]
    elif len(texts) == 2:
        xs.append(max(W / 2 - ws[1] / 2, xs[0] + ws[0] + GAP))
    if sum(ws) + GAP * (len(ws) - 1) > LINE_W or xs[-1] + ws[-1] > S["slot_right_x"] + 0.5:
        raise SystemExit(f"subtitle line too wide for the slots: {texts}")
    return [round(x) for x in xs], ws

subs = []   # (id, x, text, start, end)
for li, ln in enumerate(lines):
    first_next = WORDS[lines[li + 1][0][0]]["start"] if li + 1 < len(lines) else None
    last_word = WORDS[ln[-1][-1]]
    nxt_stack = min([a for a, b in windows if a >= WORDS[ln[0][0]]["start"]], default=None)
    if first_next is None and nxt_stack is None:
        end = DUR                                                    # last line holds to the end (no end card)
    else:
        end = last_word["end"] + 0.6                                 # hold, then all slots clear together
        end = min(x for x in (end, first_next, nxt_stack, DUR) if x is not None)
    for c in CUTS:                                                   # a shot change also clears the line
        if last_word["start"] < c < end:
            end = cut_frame(c)
    texts = [" ".join(show(WORDS[k]["text"]) for k in ch) for ch in ln]
    pins = ()
    if C.get("subtitle_lines"):
        pins = tuple(i for i, ch in enumerate(C["subtitle_lines"][li]) if ch.startswith(">"))
    xs, _ = layout(texts, pins)
    for si, ch in enumerate(ln):
        t0 = fr(WORDS[ch[0]]["start"])
        if t0 <= 3 / FPS: t0 = 0.0
        subs.append((f"sub{li}_{si}", xs[si], texts[si], t0, fr(end)))

# ---- 3. HTML pieces ----
def stack_html(s, n):
    out_lines, js = [], []
    lilac = {norm(x) for x in s.get("lilac", [])}
    k = 0
    for li, line in enumerate(s["lines"]):
        hero = line.get("hero", False)
        if hero:
            fit = HERO["max_width"] / (width(line["text"], 100, HERO["weight"], HERO["track"]) / 100)
            fs, fw, tr = min(s.get("hero_size", HERO["max_size"]), math.floor(fit)), HERO["weight"], HERO["track"]
            base_col = COL[s.get("hero_colour", "butter")]
        else:
            fs, fw, tr = SMALL["size"], SMALL["weight"], SMALL["track"]
            base_col = COL[s.get("small_colour", "butter")]
        spans = []
        for tok in line["text"].split():
            wi = s["idx"][k]; k += 1
            col = COL["lilac"] if norm(tok) in lilac else base_col
            sid = f"{s['id']}-w{k}"
            spans.append(f'<span id="{sid}" class="sw" style="color:{col}">{html.escape(tok)}</span>')
            t = s["start"] if k == 1 else fr(WORDS[wi]["start"])
            js.append(f'tl.set("#{sid}", {{ opacity: 1 }}, {t:.3f});')
        out_lines.append(f'<div class="sl" style="text-align:{ {"left": "left", "right": "right"}.get(line["align"], "center")};'
                         f'font-size:{fs}px;font-weight:{fw};letter-spacing:{tr}em">{" ".join(spans)}</div>')
    bottom = H - s["baseline_y"]
    el = (f'<div id="stack-{s["id"]}" class="clip stack" data-start="{s["start"]:.3f}" '
          f'data-duration="{s["end"] - s["start"]:.3f}" data-track-index="{10 + n}" data-layout-allow-overlap '
          f'style="bottom:{bottom}px">\n        ' + "\n        ".join(out_lines) + "\n      </div>")
    return el, js

def sub_html():
    out = []
    for sid, x, text, a, b in subs:
        pos = f"left:{x}px"
        out.append(f'<div id="{sid}" class="clip sub" data-start="{a:.3f}" data-duration="{b - a:.3f}" '
                   f'data-track-index="20" style="{pos}">{html.escape(text)}</div>')
    return "\n      ".join(out)

# ---- 4. music bed level: measured, so it sits exactly under_voice_db below the voice ----
B = C.get("bed") or {}
HAS_BED = has(B.get("src"))
HAS_CUT = has(C.get("cutout"))
if not HAS_BED:
    print(f"note: no music bed ({B.get('src')} not found): add music in the Edits window instead")
if not HAS_CUT:
    print(f"note: no cut-out ({C.get('cutout')} not found): giant words will sit in front of the speaker. "
          "Make it with: npx --yes hyperframes@0.9.83 remove-background assets/cut.mp4 -o assets/cutout.webm --quality best")
bed_lufs, bed_vol = None, 0
if HAS_BED:
    m = run(["ffmpeg", "-hide_banner", "-nostats", "-ss", str(B["enter_at"]), "-t", f"{DUR:.3f}", "-i", B["src"],
             "-af", "ebur128", "-f", "null", "-"]).stderr
    bed_lufs = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", m)[-1])
    bed_vol = round(10 ** ((B["voice_lufs"] - B["under_voice_db"] - bed_lufs) / 20), 4)

stack_parts = [stack_html(s, n) for n, s in enumerate(stacks)]
stacks_el = "\n      ".join(p[0] for p in stack_parts)
stacks_js = "\n    ".join(j for p in stack_parts for j in p[1])
hide_cut = ' style="opacity:0"' if args.debug_no_cutout else ""

CSS = f"""
  @font-face {{ font-family: "Inter Tight"; src: url("assets/fonts/InterTight-VariableFont_wght.ttf"); font-weight: 100 900; }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  html, body {{ width: {W}px; height: {H}px; overflow: hidden; background: BODYBG; }}
  #root {{ font-family: "Inter Tight", sans-serif; }}
  video.full {{ position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }}
  #a-roll {{ z-index: 1; }}
  .stack {{ position: absolute; left: {STACK_X}px; right: {STACK_X}px; z-index: 2; }}
  .sl {{ line-height: {LEAD}; white-space: nowrap; }}
  .sw {{ opacity: 0; }}
  #cutout {{ z-index: 3; }}
  .sub {{ position: absolute; top: {S["baseline_y"] - round(size * 0.97)}px; z-index: 4; font-size: {size}px; line-height: 1.2;
         font-weight: {SUB["weight"]}; letter-spacing: {SUB["track"]}em; color: {COL["cream"]}; white-space: nowrap; }}
"""

def page(overlay):
    """overlay=True: no footage, no music, transparent; the cut-out only while a stack is up (it hides the
    stack words behind the head; outside a stack it would just be a second copy of the speaker over the Edits clip)."""
    if overlay:
        cut_parts = []
        for n, (a, b) in enumerate(windows if HAS_CUT else []):
            cut_parts.append(f'<video id="cutout-{n}" class="clip full cutout-o" src="{C["cutout"]}" muted playsinline '
                             f'data-layout-allow-occlusion data-start="{a:.3f}" data-media-start="{a:.3f}" '
                             f'data-duration="{b - a:.3f}" data-track-index="{3 + n}" style="z-index:3"></video>')
        base = ""
        cut = "\n    ".join(cut_parts)
        audio = ""
    else:
        base = (f'<video id="a-roll" class="clip full" src="{C["footage"]}" playsinline data-has-audio="true" '
                f'data-volume="1" data-start="0" data-duration="{DUR:.3f}" data-track-index="1"></video>')
        cut = (f'<video id="cutout" class="clip full" src="{C["cutout"]}" muted playsinline data-layout-allow-occlusion '
               f'data-start="0" data-duration="{DUR:.3f}" data-track-index="3"{hide_cut}></video>') if HAS_CUT else ""
        audio = "" if not HAS_BED else (f'<audio id="bed" class="clip" src="{B["src"]}" data-start="0" data-media-start="{B["enter_at"]}" '
                 f'data-duration="{DUR:.3f}" data-volume="{bed_vol}" data-fade-in="{B["fade_in"]}" '
                 f'data-fade-out="{B["fade_out"]}" data-track-index="30"></audio>')
    css = CSS.replace("BODYBG", "transparent" if overlay else "#000")
    return f"""<!doctype html>
<html lang="en" data-resolution="portrait">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width={W}, height={H}" />
<script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
<style>{css}</style>
</head>
<body>
  <div id="root" data-composition-id="main" data-start="0" data-duration="{DUR:.3f}" data-width="{W}" data-height="{H}" data-fps="{FPS}">
    {base}
    <div id="stacks" data-track-kind="graphics">
      {stacks_el}
    </div>
    {cut}
    <div id="captions" data-track-kind="captions">
      {sub_html()}
    </div>
    {audio}
  </div>
  <script>
    window.__timelines = window.__timelines || {{}};
    const tl = gsap.timeline({{ paused: true }});
    // giant words hard-cut on, one frame, on their spoken syllable (no fade, scale or blur: SPEC.md section 3)
    {stacks_js}
    tl.set({{}}, {{}}, {DUR:.3f});
    window.__timelines["main"] = tl;
  </script>
</body>
</html>
"""

# One root composition only (two root .html files confuse the runtime), so the overlay variant is written into
# index.html on demand: python3 build.py --overlay && render --format mov ... && python3 build.py
open("index.html", "w").write(page(args.overlay))

# ---- 5. grades through media-treatment (never CSS filters): background plate darker + warmer, the person warm ----
def grade(file, selector, gfile):
    run(["npx", "--yes", "hyperframes@0.9.83", "media-treatment", "--project", ".", "--file", file,
         "--selector", selector, "--grading", gfile, "--apply", "--json"])
if args.overlay:
    if HAS_CUT and windows:
        grade("index.html", ".cutout-o", C["grade_person"])
else:
    grade("index.html", "#a-roll", C["grade_background"])
    if HAS_CUT:
        grade("index.html", "#cutout", C["grade_person"])

print(f"DUR {DUR:.3f}s | " + (f"bed {bed_lufs} LUFS -> volume {bed_vol} ({B['under_voice_db']} dB under {B['voice_lufs']})"
                              if HAS_BED else "no bed"))
for s in stacks:
    print(f"stack {s['id']}: {s['start']:.3f}-{s['end']:.3f}  " + " ".join(t for _, t in s["toks"]))
for sid, x, text, a, b in subs:
    print(f"  {a:6.3f}-{b:6.3f} x={x:<4} {text}")
