#!/usr/bin/env python3
"""Builds index.html (+ overlays/index.html) for a Serialised episode. Every number is in SPEC.md.

WHY a generator: captions must be real HTML elements with fixed times (HyperFrames rule) and they come from the
word timings in assets/words-cut.json; sounds are placed from each file's MEASURED peak, so swapping a sound or a
take keeps everything in sync. A member's episode = change the EPISODE block below, run cut.py, then:
    python3 build.py && npx --yes hyperframes@0.9.83 check --json

overlays/index.html is the same timeline with the footage and audio removed and a transparent page, for Edits' addOverlay
(render it with --format mov).
"""
import json, html, os, subprocess, array, tempfile, sys

# BRAND: Claude fills these from the member's profile.md before each build (why: the look is fixed,
# the colours and fonts are hers). These defaults are neutral placeholders.
BRAND_INK, BRAND_ACCENT, BRAND_CREAM = "#141414", "#FF5A36", "#FAF7F2"

# ======================= EPISODE (the only block a member's version changes) =======================
SERIES = "Your series"        # series name: never changes between episodes
EPISODE = 1                   # bump by one every episode (keep a list of your episodes: never skip or repeat)
EPISODES_SHOWN = 3            # how many ticks the episode rail shows (e.g. a list of three reasons = 3)
TOPIC = ["Your", "episode", "topic"]   # your words; TOPIC_MARK = the index of the word that gets the highlighter
TOPIC_MARK = 0
ACCENT = BRAND_ACCENT         # badge, ticks, keyword chips, highlighter
INK, PAPER = BRAND_INK, BRAND_CREAM
SIGNATURE = "assets/sfx/signature-stamp.mp3"   # the SAME file every episode, forever. Not shipped: use your own
SIGNATURE_GAIN = 0.78         # measured: loudest 400 ms sits ~8 dB under the voice (measure_audio.py)
# a-roll look, saved once and reused every episode (applied through `hyperframes media-treatment`)
GRADE = {"preset": "skin-soft", "intensity": 0.6,
         "adjust": {"exposure": 0.04, "contrast": 0.06, "highlights": -0.08, "shadows": 0.06,
                    "temperature": 0.04, "saturation": 0.03},
         "details": {"vignette": 0.05}}
# caption groups: word index ranges (inclusive), 2-3 words (a 4th only for tiny words).
# EXAMPLE VALUES from a 44-word demo take: rewrite them from your assets/words-cut.json.
GROUPS = [(0, 2), (3, 5), (6, 8), (9, 10), (11, 14), (15, 16), (17, 18), (19, 21), (22, 23), (24, 25), (26, 27),
          (28, 30), (31, 32), (33, 33), (34, 35), (36, 38), (39, 40), (41, 43)]
KEYWORDS = {"keyword", "another"}   # lower-case spoken words that flip to an accent chip
# =====================================================================================================

FPS, FRAME = 30, 1 / 30
CUT = "assets/cut.mp4"
W = json.load(open("assets/words-cut.json"))
T = lambda i: W[i]["start"]

def probe_duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                         capture_output=True, text=True, check=True).stdout
    return float(out)

DUR = round(int(probe_duration(CUT) * FPS) / FPS - FRAME, 3)   # whole frames, one under the file's end

def has(p):
    """Media isn't shipped with the template: anything missing is skipped, never a crash."""
    return os.path.exists(p)

def peak_time(path):
    """Seconds from the file's start to its loudest 10 ms (so we can land the peak 1 frame after the picture)."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", "48000", "-f", "s16le", "-"],
                         capture_output=True, check=True).stdout
    a, n, best = array.array("h", raw), 480, (0, 0.0)
    for i in range(0, len(a) - n, n):
        e = sum(x * x for x in a[i:i + n])
        if e > best[0]:
            best = (e, i / 48000)
    return best[1]

def grade_attr(payload, cache="grade-attr.txt"):
    """Run the payload through `hyperframes media-treatment` (validates + fills the full schema) once, cache it."""
    key = json.dumps(payload, sort_keys=True)
    if os.path.exists(cache):
        lines = open(cache).read().split("\n", 1)
        if lines[0] == key:
            return lines[1].strip()
    d = tempfile.mkdtemp()
    open(f"{d}/index.html", "w").write('<!doctype html><html><body><div id="root" data-composition-id="main" '
        'data-start="0" data-duration="1" data-width="1080" data-height="1920"><video id="v" class="clip" src="a.mp4" '
        'data-start="0" data-duration="1" muted></video></div></body></html>')
    subprocess.run(["npx", "--yes", "hyperframes@0.9.83", "media-treatment", "--project", d, "--file", "index.html",
                    "--selector", "#v", "--grading", key, "--apply", "--json"], check=True, capture_output=True)
    src = open(f"{d}/index.html").read()
    i = src.index('data-color-grading="')
    attr = src[i:src.index('"', i + len('data-color-grading="')) + 1]
    open(cache, "w").write(key + "\n" + attr + "\n")
    return attr

# ---------------- key moments (cut clock) ----------------
SEAMS = []           # the jump cuts inside cut.mp4 (from cut.py's KEEP), each hidden by a camera change
try:
    import cut as _cut
    acc = 0.0
    for a, b in _cut.KEEP[:-1]:
        acc += (b - a) / _cut.SPEED
        SEAMS.append(round(acc, 3))
except Exception:
    pass
# EXAMPLE word indices (from the demo take): point each one at the matching word in your assets/words-cut.json.
#   NUMBER = "Number", THREE = the spoken episode number, HYPER = the topic word (highlighter),
#   WE = first word after the signpost (topic line leaves 0.55 s later), then the words that get a camera change.
NUMBER, THREE, HYPER = T(15), T(16), T(18)
WE, HOURS, AND, TENX, LIKE = T(19), T(23), T(28), T(33), T(34)
STAMP_LAND = 0.12                      # badge lands (frame 0 already shows it, slightly large)

# camera: hard punch-ins only (no creeping zoom). Each jump cut gets a framing change so it reads as meant.
CAMERA = [(0.0, 1.0), (SEAMS[0] if SEAMS else 1.81, 1.06), (NUMBER, 1.10), (WE, 1.0), (HOURS, 1.06),
          (AND, 1.0), (TENX, 1.16), (LIKE, 1.04)]

def captions():
    out, js = [], []
    for g, (a, b) in enumerate(GROUPS):
        start = max(0.1, W[a]["start"] - 0.04)
        nxt = GROUPS[g + 1][0] if g + 1 < len(GROUPS) else None
        end = min(DUR - 0.02, (W[nxt]["start"] - 0.04) if nxt is not None else W[b]["end"] + 0.5)
        spans = []
        for i in range(a, b + 1):
            word = W[i]["text"]
            kw = word.strip(".,'").lower() in KEYWORDS
            spans.append(f'<span id="cw{i}" class="cw{" kw" if kw else ""}">{html.escape(word)}</span>')
            if kw:   # keyword turns into a tomato chip on the frame it is spoken
                js.append(f'tl.to("#cw{i}", {{ backgroundColor: "{ACCENT}", color: "#FFFFFF", duration: 0.05 }}, {W[i]["start"]:.3f});')
        out.append(f'<div id="cg{g}" class="clip capgroup" data-layout-allow-safe-zone data-start="{start:.3f}" data-duration="{end - start:.3f}" '
                   f'data-track-index="20"><span class="box">{" ".join(spans)}</span></div>')
        js.append(f'tl.fromTo("#cg{g} .box", {{ opacity: 0, scale: 0.94 }}, {{ opacity: 1, scale: 1, duration: 0.1, ease: "power3.out" }}, {start:.3f});')
        js.append(f'tl.to("#cg{g} .box", {{ opacity: 0, duration: 0.05, ease: "power1.in" }}, {end - 0.05:.3f});')
    return "\n      ".join(out), "\n      ".join(js)

def page(overlay=False):
    cap_html, cap_js = captions()
    grade = grade_attr(GRADE)
    sig_start = STAMP_LAND + FRAME - peak_time(SIGNATURE) if has(SIGNATURE) else 0
    rail = "".join(f'<i class="tick{" now" if n == EPISODE else ""}" id="tick{n}"><b></b></i>'
                   for n in range(1, EPISODES_SHOWN + 1))
    topic = " ".join((f'<span class="tw mark"><i id="hl"></i><span class="t">{html.escape(t)}</span></span>' if k == TOPIC_MARK
                      else f'<span class="tw">{html.escape(t)}</span>') for k, t in enumerate(TOPIC))
    cam_js = "" if overlay else "\n    ".join(f'tl.set("#cam", {{ scale: {s} }}, {t:.3f});' for t, s in CAMERA)
    footage = "" if overlay else f"""
    <div id="cam">
      <video id="a-roll" class="clip" src="{CUT}" {grade} playsinline data-has-audio="true" data-volume="1"
             data-start="0" data-duration="{DUR}" data-track-index="1"></video>
    </div>"""
    audio = "" if overlay or not has(SIGNATURE) else (f'<audio id="sig" class="clip" src="{SIGNATURE}" data-start="{max(0, sig_start):.3f}" '
                                f'data-duration="0.2" data-volume="{SIGNATURE_GAIN}" data-track-index="30"></audio>')
    bg = "transparent" if overlay else INK
    return f"""<!doctype html>
<html lang="en" data-resolution="portrait">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1080, height=1920" />
<script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
<style>
  @font-face {{ font-family: "Archivo"; src: url("assets/fonts/Archivo.ttf"); font-weight: 100 900; }}
  @font-face {{ font-family: "Archivo Black"; src: url("assets/fonts/ArchivoBlack-Regular.ttf"); font-weight: 400; }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  html, body {{ width: 1080px; height: 1920px; overflow: hidden; background: {bg}; }}
  body {{ font-family: "Archivo", sans-serif; color: {INK}; }}

  /* the camera: punch-ins are hard scale changes on this wrapper, centred on her face */
  #cam {{ position: absolute; inset: 0; z-index: 1; overflow: hidden; transform-origin: 50% 75%; }}  /* origin at her chin: punches grow up, never into the captions */
  #cam video {{ position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }}

  /* series lockup: badge, episode rail, topic line. Same place, same size, every episode. */
  #lock {{ position: absolute; left: 72px; top: 272px; z-index: 5; }}
  #badge {{ display: inline-flex; align-items: center; gap: 14px; background: {ACCENT}; color: #FFFFFF;
           font: 400 44px/1 "Archivo Black"; letter-spacing: 0.01em; text-transform: uppercase;
           padding: 16px 26px 15px; border-radius: 999px; transform-origin: 0% 50%;
           box-shadow: 0 10px 28px rgba(20,20,20,.28), inset 0 -3px 0 rgba(0,0,0,.12); }}
  #ep {{ display: inline-block; background: #FFFFFF; color: {ACCENT}; padding: 6px 12px 5px; border-radius: 12px;
        font: 400 40px/1 "Archivo Black"; }}
  #rail {{ display: flex; gap: 8px; margin: 14px 0 0 10px; }}
  .tick {{ position: relative; width: 38px; height: 9px; border-radius: 5px; background: rgba(20,20,20,.82);
          box-shadow: 0 2px 8px rgba(0,0,0,.18); overflow: hidden; }}
  .tick.now {{ background: rgba(250,247,242,.92); box-shadow: inset 0 0 0 2px rgba(20,20,20,.82), 0 2px 8px rgba(0,0,0,.18); }}
  .tick b {{ position: absolute; inset: 0; background: {ACCENT}; transform-origin: 0 50%; }}
  #topic {{ display: inline-block; margin-top: 16px; background: {PAPER}; padding: 14px 26px 16px; border-radius: 14px;
           font: 600 56px/1.12 "Archivo"; letter-spacing: -0.015em; color: {INK};
           box-shadow: 0 14px 36px rgba(20,20,20,.22); }}
  #topic .tw {{ position: relative; display: inline-block; }}
  #topic .mark i {{ position: absolute; left: -6px; right: -6px; bottom: 4px; height: 22px; border-radius: 5px;
                    background: {ACCENT}; opacity: .38; transform-origin: 0 50%; }}
  #topic .mark .t {{ position: relative; }}

  /* captions: 2-3 words, ink on an off-white box, centre y ~1520 */
  .capgroup {{ position: absolute; left: 0; right: 0; top: 1495px; text-align: center; z-index: 8; overflow: visible; }}
  .box {{ display: inline-block; background: {PAPER}; color: {INK}; border-radius: 14px; padding: 12px 22px 14px;
         font: 700 48px/1.1 "Archivo"; letter-spacing: -0.01em; box-shadow: 0 10px 30px rgba(20,20,20,.25); }}
  .cw {{ display: inline-block; border-radius: 8px; }}
  .cw.kw {{ padding: 0 8px; margin: 0 2px; }}
</style>
</head>
<body>
  <div id="root" data-composition-id="main" data-start="0" data-duration="{DUR}" data-width="1080" data-height="1920">
    {footage}

    <div id="lock" class="clip" data-start="0" data-duration="{DUR}" data-track-index="4">
      <div id="badge"><span>{html.escape(SERIES)}</span><span id="ep">#{EPISODE}</span></div>
      <div id="rail">{rail}</div>
      <div id="topic">{topic}</div>
    </div>

    <div id="captions" data-track-kind="captions">
      {cap_html}
    </div>

    {audio}
  </div>

  <script>
    const tl = gsap.timeline({{ paused: true }});

    // ---- camera (hard cuts = gsap.set) ----
    {cam_js}

    // ---- the stamp: frame 0 already shows the whole lockup (thumbnail); the badge lands with the signature sound ----
    tl.fromTo("#badge", {{ scale: 1.12, rotation: -2.5 }}, {{ scale: 1, rotation: 0, duration: {STAMP_LAND}, ease: "power4.out" }}, 0);
    tl.fromTo("#topic", {{ scale: 1.04 }}, {{ scale: 1, duration: 0.22, ease: "expo.out" }}, 0.04);
    tl.set(".tick b", {{ scaleX: 0 }}, 0);

    // ---- "Number <N>": the episode number re-stamps and this episode's tick fills ----
    tl.fromTo("#ep", {{ scale: 1.45, rotation: 8 }}, {{ scale: 1, rotation: 0, duration: 0.3, ease: "back.out(2.2)", immediateRender: false }}, {THREE:.3f});
    tl.fromTo("#tick{EPISODE} b", {{ scaleX: 0 }}, {{ scaleX: 1, duration: 0.22, ease: "power3.out" }}, {THREE + 0.04:.3f});

    // ---- topic: highlighter sweeps under the topic word as she says it, then the topic line leaves ----
    tl.fromTo("#hl", {{ scaleX: 0 }}, {{ scaleX: 1, duration: 0.3, ease: "power3.out" }}, {HYPER:.3f});
    tl.to("#topic", {{ clipPath: "inset(0 100% 0 0 round 14px)", duration: 0.22, ease: "power3.in" }}, {WE + 0.55:.3f});

    // ---- captions (generated from assets/words-cut.json) ----
      {cap_js}

    window.__timelines["main"] = tl;
  </script>
</body>
</html>
"""

if __name__ == "__main__":
    open("index.html", "w").write(page())
    sig_at = round(STAMP_LAND + FRAME - peak_time(SIGNATURE), 3) if has(SIGNATURE) else None
    json.dump({"voice": CUT, "sfx": [{"id": "signature", "file": SIGNATURE, "start": sig_at, "gain": SIGNATURE_GAIN,
                                      "offset": 0, "slot": 0.2}] if has(SIGNATURE) else []}, open("sfx.json", "w"), indent=1)
    # overlays/ is its own tiny project (one root composition per folder) sharing ../assets
    os.makedirs("overlays", exist_ok=True)
    if not os.path.lexists("overlays/assets"):
        os.symlink("../assets", "overlays/assets")
    open("overlays/index.html", "w").write(page(overlay=True))
    if os.path.exists("overlays.html"):
        os.remove("overlays.html")
    print(f"built: {DUR}s, {len(GROUPS)} caption groups, seams {SEAMS}, "
          + (f"signature at {sig_at:.3f}s" if has(SIGNATURE) else f"no signature sound ({SIGNATURE} not found: skipped)"))
