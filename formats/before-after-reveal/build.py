#!/usr/bin/env python3
"""Builds index.html (+ overlays/index.html) for the Before-and-after reveal. Every number is in SPEC.md.

The demo's story: the REAL washed-out iPhone HDR file (before) -> the real fix, step by step (the conversion command,
the HDR->SDR switch, the real colour scopes of both files, a wipe) -> flash + push into the REAL converted file with
the after grade (warm, +10 saturation, +contrast), held to the end.

A member's version: run cut.py on your before/after clips, then change the REVEAL block (hook, labels, process
beats, grade). Process beats are cards because the demo's transformation happens inside a computer; a member with
filmed process clips (sanding, cutting, styling) swaps each card for a 0.5-1 s clip of the action itself.
    $PY build.py && npx --yes hyperframes@0.9.83 check --json
"""
import json, html, os, subprocess, array, tempfile

# ============================ REVEAL (what a member's version changes) ============================
# Example values from the demo (an HDR -> SDR colour fix); Claude sets these per reel.
HOOK = "Your question hook?"                  # question hook, first 2 s (e.g. "Would you [keep/buy/grab] this?")
LABEL_BEFORE, LABEL_AFTER = "BEFORE", "AFTER"
GOLD, INK, WHITE = "#F5C451", "#111111", "#FFFFFF"
GRADE_AFTER = {"adjust": {"temperature": 0.06, "saturation": 0.10, "contrast": 0.08}}   # warm, +10 sat, +contrast
CMD = "your-real-command your-file.mov"     # beat 1: the REAL command you ran (never an invented one)
FROM_TAGS = ["HDR", "HLG", "Rec.2020", "10-bit"]   # demo: ffprobe of the raw file: arib-std-b67 / bt2020 / yuv420p10le
TO_TAGS = ["SDR", "Rec.709", "8-bit"]              # demo: ffprobe of the fixed file: bt709 / bt709 / yuv420p
# caption groups (word index ranges, inclusive), e.g. [(0, 3), (4, 5), (6, 9)]. None = automatic: up to 3 words,
# break after punctuation (why: a new take has different word counts, so the demo's ranges don't fit it).
GROUPS = None
# sounds: id, file, picture moment (cut clock, filled in below), gain, media offset, slot length
# gains set so each hit's loudest 400 ms sits 6-10 dB under the voice (measured: measure_audio.py, REVIEW.md)
GAIN = {"typing": 1.8, "toggle": 0.83, "slide": 0.27, "sparkle": 0.77}
VOICE_GAIN = 1.11   # demo: voice.wav measured -14.9 LUFS integrated; x1.11 (+0.9 dB) landed the mix on -14. Re-measure yours.
# ===================================================================================================

FPS, FRAME = 30, 1 / 30
C = json.load(open("cut.json"))
W = json.load(open("assets/words-cut.json"))
STATS = json.load(open("assets/scope-stats.json"))
DUR = round(int(C["duration"] * FPS) / FPS - FRAME, 3)
P0, REV = C["process_at"], C["reveal_at"]          # montage start, reveal (flash peak) on the cut clock
# montage beats (each one a "process clip": 0.6-0.7 s, motion inside, hard cuts between)
B1, B2, B3, B4 = P0, P0 + 0.70, P0 + 1.30, P0 + 1.96
TYPE_END = B1 + 0.42                                # the command finishes typing
TOGGLE_LAND = B2 + 0.32                             # switch knob lands on SDR
SCOPE_SWAP = B3 + 0.18                              # before scope becomes the after scope
SPARK = REV + 0.14                                  # sparkle sticker lands

if GROUPS is None:
    GROUPS, _a = [], 0
    for _i, _w in enumerate(W):
        _next_gap = W[_i + 1]["start"] - _w["end"] if _i + 1 < len(W) else 0
        if _i - _a + 1 >= 3 or _w["text"][-1] in ".,?!" or _next_gap >= 1.0 or _i == len(W) - 1:
            GROUPS.append((_a, _i)); _a = _i + 1

def peak_time(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", "48000", "-f", "s16le", "-"],
                         capture_output=True, check=True).stdout
    a, n, best = array.array("h", raw), 480, (0, 0.0)
    for i in range(0, len(a) - n, n):
        e = sum(x * x for x in a[i:i + n])
        if e > best[0]:
            best = (e, i / 48000)
    return best[1]

def grade_attr(payload, cache="grade-attr.txt"):
    """Validate + expand the grade through `hyperframes media-treatment` once, then cache it."""
    key = json.dumps(payload, sort_keys=True)
    if os.path.exists(cache):
        first, rest = open(cache).read().split("\n", 1)
        if first == key:
            return rest.strip()
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

def sounds():
    # (id, file, picture moment, media offset, slot). start = moment + 1 frame - (peak - media offset)
    plan = [("sfx-typing", "assets/sfx/typing.mp3", None, 1.00, TYPE_END - B1 + 0.05, GAIN["typing"]),
            ("sfx-toggle", "assets/sfx/toggle.mp3", TOGGLE_LAND, 0.0, 0.30, GAIN["toggle"]),
            ("sfx-slide", "assets/sfx/paper-slide.mp3", SCOPE_SWAP, 0.0, 0.55, GAIN["slide"]),
            ("sfx-sparkle", "assets/sfx/sparkle.mp3", SPARK, 0.0, 0.75, GAIN["sparkle"])]
    out = []
    for sid, f, moment, off, slot, gain in plan:
        if not os.path.exists(f):
            continue   # SFX aren't shipped: skip it here, add it natively in Edits instead
        if moment is None:           # a bed under the typing: starts with the first key
            start = B1 + 0.02
        else:
            start = moment + FRAME - (peak_time(f) - off)
        out.append({"id": sid, "file": f, "start": round(start, 3), "offset": off, "slot": round(slot, 3), "gain": gain})
    return out

def captions():
    out, js = [], []
    for g, (a, b) in enumerate(GROUPS):
        start = max(0.1, W[a]["start"] - 0.05)
        nxt = GROUPS[g + 1][0] if g + 1 < len(GROUPS) else None
        if nxt is not None and W[nxt]["start"] - W[b]["end"] < 1.0:
            end = W[nxt]["start"] - 0.05
        else:                       # before the montage gap / at the end: hold 0.45 s after the last word
            end = min(W[b]["end"] + 0.45, (P0 - 0.02) if W[b]["end"] <= P0 else DUR - 0.02)
        words = " ".join(html.escape(W[i]["text"]) for i in range(a, b + 1))
        out.append(f'<div id="cg{g}" class="clip capgroup" data-layout-allow-safe-zone data-start="{start:.3f}" '
                   f'data-duration="{end - start:.3f}" data-track-index="20"><span class="cap">{words}</span></div>')
        js.append(f'tl.fromTo("#cg{g} .cap", {{ opacity: 0, scale: 0.92 }}, {{ opacity: 1, scale: 1, duration: 0.12, ease: "back.out(1.8)" }}, {start:.3f});')
        js.append(f'tl.to("#cg{g} .cap", {{ opacity: 0, duration: 0.06, ease: "power1.in" }}, {end - 0.06:.3f});')
    return "\n      ".join(out), "\n      ".join(js)

# Inter and JetBrains Mono load from assets/fonts/ when they're there (why: not every Mac has them installed)
OPTIONAL_FACES = " ".join(
    f'@font-face {{ font-family: "{fam}"; src: url("assets/fonts/{f}"); font-weight: {wt}; }}'
    for fam, f, wt in (("Inter", "Inter-Variable.ttf", "100 900"), ("JetBrains Mono", "JetBrainsMono-Medium.ttf", 500))
    if os.path.exists(f"assets/fonts/{f}"))

def page(overlay=False):
    cap_html, cap_js = captions()
    g_after = grade_attr(GRADE_AFTER)
    sfx = sounds()
    json.dump({"voice": "assets/voice.wav", "voice_gain": VOICE_GAIN, "sfx": sfx}, open("sfx.json", "w"), indent=1)
    sat_b, sat_a = STATS["before"]["SATAVG"], STATS["after"]["SATAVG"]
    vid = lambda vid_id, src, start, dur, mstart, extra="": (
        f'<video id="{vid_id}" class="clip" src="{src}" {extra} muted playsinline data-start="{start:.3f}" '
        f'data-duration="{dur:.3f}" data-media-start="{mstart:.3f}" data-track-index="1"></video>')
    footage = "" if overlay else f"""
    <div id="cam-before" class="cam">{vid("v-before", "assets/before.mp4", 0, P0, C["start"])}</div>
    <div id="cam-after" class="cam">{vid("v-after", "assets/after.mp4", REV, DUR - REV, C["reveal_media_start"], g_after)}</div>
    <div id="wipe-before" class="cam">{vid("v-wipe-b", "assets/before.mp4", B4, REV - B4, C["start"] + B4)}</div>
    <div id="wipe-after" class="cam">{vid("v-wipe-a", "assets/after.mp4", B4, REV - B4, C["start"] + B4, g_after)}</div>"""
    audio = "" if overlay else "\n    ".join(
        [f'<audio id="voice" class="clip" src="assets/voice.wav" data-start="0" data-duration="{DUR}" data-volume="{VOICE_GAIN}" data-track-index="29"></audio>'] +
        [f'<audio id="{s["id"]}" class="clip" src="{s["file"]}" data-start="{s["start"]}" data-duration="{s["slot"]}" '
         f'data-media-start="{s["offset"]}" data-volume="{s["gain"]}" data-fade-out="0.06" data-track-index="{30 + n}"></audio>'
         for n, s in enumerate(sfx)])
    tags = lambda ts, cls: "".join(f'<span class="tag {cls}">{html.escape(t)}</span>' for t in ts)
    bg = "transparent" if overlay else "#0E0E0F"
    return f"""<!doctype html>
<html lang="en" data-resolution="portrait">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1080, height=1920" />
<script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
<style>
  @font-face {{ font-family: "Bebas Neue"; src: url("assets/fonts/BebasNeue-Regular.ttf"); font-weight: 400; }}
  {OPTIONAL_FACES}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  html, body {{ width: 1080px; height: 1920px; overflow: hidden; background: {bg}; }}
  body {{ font-family: "Inter", sans-serif; color: {WHITE}; }}

  .cam {{ position: absolute; inset: 0; overflow: hidden; transform-origin: 50% 42%; }}
  .cam video {{ position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }}
  #cam-before {{ z-index: 1; }}  #cam-after {{ z-index: 1; }}
  #wipe-before, #wipe-after {{ z-index: 7; }}
  #wipe-before {{ z-index: 8; }}
  #wipe-line {{ position: absolute; top: 0; bottom: 0; left: 0; width: 6px; margin-left: -3px; z-index: 9; background: {WHITE};
               box-shadow: 0 0 24px rgba(255,255,255,.9), 0 0 4px rgba(255,255,255,1); }}

  /* labels: Bebas Neue 96 caps, top-left (moved down into Instagram's clear band) */
  .label {{ position: absolute; left: 64px; top: 272px; z-index: 12; font: 400 96px/1 "Bebas Neue"; letter-spacing: 0.02em;
           padding: 14px 26px 6px; border-radius: 14px; }}
  #lab-before {{ background: rgba(0,0,0,.8); color: {WHITE}; }}
  #lab-after {{ background: {GOLD}; color: {INK}; box-shadow: 0 16px 40px rgba(0,0,0,.3); }}
  #spark {{ position: absolute; left: 318px; top: 236px; width: 86px; height: 86px; z-index: 13; }}
  #hook {{ position: absolute; left: 0; right: 0; top: 410px; text-align: center; z-index: 12; }}
  #hook span {{ display: inline-block; background: {INK}; color: {WHITE}; font: 700 58px/1.15 "Inter"; letter-spacing: -0.015em;
               padding: 16px 34px 18px; border-radius: 999px; box-shadow: 0 16px 44px rgba(0,0,0,.35); }}

  /* process montage: full-frame "process clips" on a dark editing desk */
  .beat {{ position: absolute; inset: 0; z-index: 6; background: radial-gradient(110% 70% at 50% 40%, #1E1E21 0%, #0E0E0F 70%); }}
  .step {{ position: absolute; left: 0; right: 0; top: 330px; text-align: center; font: 400 64px/1 "Bebas Neue";
          letter-spacing: 0.06em; color: {GOLD}; }}
  .term {{ position: absolute; left: 64px; right: 64px; top: 640px; background: #161618; border-radius: 26px; overflow: hidden;
          box-shadow: 0 40px 90px rgba(0,0,0,.6), inset 0 0 0 1.5px rgba(255,255,255,.08); }}
  .term .bar {{ height: 64px; background: #232326; display: flex; align-items: center; gap: 14px; padding-left: 26px; }}
  .term .bar i {{ width: 20px; height: 20px; border-radius: 50%; background: #5A5A60; }}
  .term .body {{ padding: 40px 40px 48px; font: 500 44px/1.45 "JetBrains Mono"; }}
  .term .ps {{ color: {GOLD}; }}
  #cmd {{ display: inline-block; white-space: nowrap; }}
  #cmdout {{ color: #A6A6AD; font-size: 31px; margin-top: 18px; }}
  .switch-wrap {{ position: absolute; left: 0; right: 0; top: 560px; text-align: center; }}
  .tags {{ display: flex; justify-content: center; gap: 14px; }}
  .tag {{ font: 700 40px/1 "Inter"; padding: 14px 22px; border-radius: 14px; }}
  .tag.from {{ background: rgba(255,255,255,.1); color: #C9C9CF; }}
  .tag.to {{ background: {GOLD}; color: {INK}; }}
  #track {{ position: relative; width: 360px; height: 176px; border-radius: 999px; margin: 64px auto; background: #3A3A3F;
           box-shadow: inset 0 6px 18px rgba(0,0,0,.5); }}
  #trackfill {{ position: absolute; inset: 0; border-radius: 999px; background: {GOLD}; }}
  #knob {{ position: absolute; left: 14px; top: 14px; width: 148px; height: 148px; border-radius: 50%; background: {WHITE};
          box-shadow: 0 10px 26px rgba(0,0,0,.45); }}
  #to-tags {{ margin-top: 0; }}
  .scope {{ position: absolute; left: 220px; top: 470px; width: 640px; height: 640px; border-radius: 50%; overflow: hidden;
           background: #050506; box-shadow: 0 40px 90px rgba(0,0,0,.6), inset 0 0 0 2px rgba(255,255,255,.12); }}
  .scope img {{ position: absolute; inset: 0; width: 100%; height: 100%; mix-blend-mode: screen; }}
  .scope .ring {{ position: absolute; border-radius: 50%; border: 1.5px dashed rgba(255,255,255,.16); }}
  .scope-read {{ position: absolute; left: 0; right: 0; top: 1150px; text-align: center; font: 700 46px/1.3 "Inter"; color: #D9D9DE; }}
  .scope-read b {{ color: {GOLD}; font-weight: 900; }}
  .scope-read small {{ display: block; font: 500 30px/1.3 "Inter"; color: #8E8E95; }}

  #flash {{ position: absolute; inset: 0; z-index: 15; background: #FFFDF6; opacity: 0; }}

  /* captions: Inter Bold 48, white, 6 px outline */
  .capgroup {{ position: absolute; left: 0; right: 0; top: 1420px; text-align: center; z-index: 14; padding: 0 80px; overflow: visible; }}
  .cap {{ display: inline-block; font: 700 48px/1.2 "Inter"; color: {WHITE}; -webkit-text-stroke: 6px {INK}; paint-order: stroke fill;
         text-shadow: 0 4px 14px rgba(0,0,0,.35); }}
</style>
</head>
<body>
  <div id="root" data-composition-id="main" data-start="0" data-duration="{DUR}" data-width="1080" data-height="1920">
    {footage}

    <div id="lab-before" class="label clip" data-start="0" data-duration="{P0:.3f}" data-track-index="10">{LABEL_BEFORE}</div>
    <div id="hook" class="clip" data-start="0" data-duration="2.0" data-track-index="11"><span>{html.escape(HOOK)}</span></div>

    <div id="beat1" class="beat clip" data-start="{B1:.3f}" data-duration="{B2 - B1:.3f}" data-track-index="5">
      <div class="step">1 · convert</div>
      <div class="term"><div class="bar"><i></i><i></i><i></i></div>
        <div class="body"><span class="ps">$ </span><span id="cmd">{html.escape(CMD)}</span></div></div>
    </div>
    <div id="beat2" class="beat clip" data-start="{B2:.3f}" data-duration="{B3 - B2:.3f}" data-track-index="6">
      <div class="step">2 · HDR off</div>
      <div class="switch-wrap"><div class="tags">{tags(FROM_TAGS, "from")}</div>
        <div id="track"><div id="trackfill"></div><div id="knob"></div></div>
        <div class="tags" id="to-tags">{tags(TO_TAGS, "to")}</div></div>
    </div>
    <div id="beat3" class="beat clip" data-start="{B3:.3f}" data-duration="{B4 - B3:.3f}" data-track-index="7">
      <div class="step">3 · colour back</div>
      <div class="scope"><div class="ring" style="inset:160px"></div><div class="ring" style="inset:60px"></div>
        <img id="sc-b" src="assets/scope-before.png" alt="" /><img id="sc-a" src="assets/scope-after.png" alt="" /></div>
      <div class="scope-read">colour <b id="satnum">{sat_b:.1f}</b> → <b>{sat_a:.1f}</b></div>
    </div>
    <div id="wipe-line" class="clip" data-start="{B4:.3f}" data-duration="{REV - B4:.3f}" data-track-index="9"></div>

    <div id="flash" class="clip" data-start="{REV - 0.06:.3f}" data-duration="0.42" data-track-index="13"></div>
    <div id="lab-after" class="label clip" data-start="{REV:.3f}" data-duration="{DUR - REV:.3f}" data-track-index="12">{LABEL_AFTER}</div>
    <svg id="spark" class="clip" data-start="{REV:.3f}" data-duration="{DUR - REV:.3f}" data-track-index="16" viewBox="0 0 100 100">
      <path d="M50 2 C54 36 64 46 98 50 C64 54 54 64 50 98 C46 64 36 54 2 50 C36 46 46 36 50 2 Z" fill="{GOLD}" />
      <path d="M84 6 C85 14 88 17 96 18 C88 19 85 22 84 30 C83 22 80 19 72 18 C80 17 83 14 84 6 Z" fill="{WHITE}" />
    </svg>

    <div id="captions" data-track-kind="captions">
      {cap_html}
    </div>

    {audio}
  </div>

  <script>
    const tl = gsap.timeline({{ paused: true }});

    // ---- BEFORE: frame 0 already shows the label and the question (thumbnail) ----
    tl.fromTo("#hook span", {{ scale: 1.05 }}, {{ scale: 1, duration: 0.3, ease: "expo.out" }}, 0);
    tl.to("#hook span", {{ opacity: 0, filter: "blur(8px)", duration: 0.18, ease: "power2.in" }}, 1.80);

    // ---- beat 1: the real command types on, its real output line appears ----
    tl.fromTo("#cmd", {{ clipPath: "inset(0 100% 0 0)" }}, {{ clipPath: "inset(0 0% 0 0)", duration: {TYPE_END - B1 - 0.03:.3f}, ease: "steps({len(CMD)})" }}, {B1 + 0.03:.3f});
    tl.fromTo("#beat1 .term", {{ scale: 1.04 }}, {{ scale: 1, duration: 0.6, ease: "expo.out" }}, {B1:.3f});

    // ---- beat 2: the switch flips HDR -> SDR ----
    tl.fromTo("#knob", {{ x: 0 }}, {{ x: 184, duration: 0.26, ease: "power3.inOut" }}, {TOGGLE_LAND - 0.26:.3f});
    tl.fromTo("#trackfill", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.2, ease: "power2.out" }}, {TOGGLE_LAND - 0.16:.3f});
    tl.fromTo("#beat2 .tags .from", {{ opacity: 1 }}, {{ opacity: 0.35, duration: 0.15 }}, {TOGGLE_LAND:.3f});
    tl.fromTo("#to-tags .tag", {{ opacity: 0.25, y: 10 }}, {{ opacity: 1, y: 0, duration: 0.18, ease: "expo.out", stagger: 0.04 }}, {TOGGLE_LAND:.3f});

    // ---- beat 3: the real colour scope of the raw file widens into the fixed file's ----
    tl.fromTo("#sc-a", {{ opacity: 0, scale: 0.72 }}, {{ opacity: 1, scale: 1, duration: 0.3, ease: "expo.out" }}, {SCOPE_SWAP:.3f});
    tl.to("#sc-b", {{ opacity: 0, duration: 0.2 }}, {SCOPE_SWAP:.3f});
    const sat = {{ v: {sat_b:.2f} }};
    tl.to(sat, {{ v: {sat_a:.2f}, duration: 0.3, ease: "expo.out", onUpdate: () => {{ document.querySelector("#satnum").textContent = sat.v.toFixed(1); }} }}, {SCOPE_SWAP:.3f});
    tl.fromTo("#beat3 .scope", {{ rotation: -8 }}, {{ rotation: 0, duration: 0.66, ease: "power2.out" }}, {B3:.3f});

    // ---- beat 4: a wipe starts showing the fixed take under the raw one (cut off by the flash) ----
    tl.fromTo("#wipe-before", {{ clipPath: "inset(0 0 0 0%)" }}, {{ clipPath: "inset(0 0 0 62%)", duration: {REV - B4:.3f}, ease: "power2.inOut" }}, {B4:.3f});
    tl.fromTo("#wipe-line", {{ x: 0 }}, {{ x: {1080 * 0.62:.0f}, duration: {REV - B4:.3f}, ease: "power2.inOut" }}, {B4:.3f});

    // ---- REVEAL: 4-frame white flash, fast push into the after shot, gold AFTER plate + one sparkle ----
    tl.fromTo("#flash", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.05, ease: "power2.in" }}, {REV - 0.06:.3f});
    tl.to("#flash", {{ opacity: 0, duration: 0.3, ease: "power2.out" }}, {REV + 0.04:.3f});
    tl.fromTo("#cam-after", {{ scale: 1.10 }}, {{ scale: 1, duration: 0.5, ease: "expo.out" }}, {REV:.3f});
    tl.fromTo("#lab-after", {{ x: -60, opacity: 0 }}, {{ x: 0, opacity: 1, duration: 0.35, ease: "expo.out" }}, {REV + 0.04:.3f});
    tl.fromTo("#spark", {{ scale: 0, rotation: -60 }}, {{ scale: 1, rotation: 0, duration: 0.32, ease: "back.out(2.4)", immediateRender: false }}, {SPARK - 0.1:.3f});
    tl.set("#spark", {{ scale: 0 }}, 0);

    // ---- captions ----
      {cap_js}

    window.__timelines["main"] = tl;
  </script>
</body>
</html>
"""

if __name__ == "__main__":
    open("index.html", "w").write(page())
    os.makedirs("overlays", exist_ok=True)
    if not os.path.lexists("overlays/assets"):
        os.symlink("../assets", "overlays/assets")
    open("overlays/index.html", "w").write(page(overlay=True))
    print(f"built: {DUR}s; montage {P0:.2f}-{REV:.2f}; sounds", [(s['id'], s['start']) for s in sounds()])
