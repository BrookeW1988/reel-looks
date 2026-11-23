#!/usr/bin/env python3
"""Builds the podcast-clip look inspired by The Diary of a CEO (every number is in SPEC.md).

Writes two compositions from ONE config, so they can never drift apart:
  index.html     the finished reel (footage, grade, hook frame, ID card, captions, B&W ending, sound)
  overlays/index.html  the same graphics with footage and background hidden, for a transparent .mov (Edits addOverlay)

WHY a generator: HyperFrames captions must be real HTML elements with fixed times, and they come from word timings.
A member's version = new footage + words file + hook text + ID card facts; everything else is the style.
Claude fills the "CLAUDE CHANGES PER TAKE" block below (and passes --hook / --hook-red) for every take.

    python3 cut.py                     # rough cut -> assets/cut.mp4, assets/react.mp4, assets/words-cut.json
    $PY build.py --hook "LINE ONE|LINE TWO" --hook-red WORD
                                       # -> index.html + overlays/index.html (the venv has PIL for the hook width-lock)
    npx --yes hyperframes@0.9.83 check --json
    npx --yes hyperframes@0.9.83 render --workers 2 -o renders/diary-of-a-ceo.mp4
    npx --yes hyperframes@0.9.83 render overlays --format mov --workers 2 -o renders/diary-of-a-ceo-overlays.mov

Options (all optional; the defaults are EXAMPLE placeholders, not a real take):
    --footage assets/cut.mp4          the speaking cut (its sound is the voice track)
    --react assets/react.mp4          a silent listening shot for the hook's second panel ("" = single-shot hook)
    --words assets/words-cut.json     [{"text","start","end","speaker"}], cut clock, speaker = "guest" | "host"
    --hook "YOUR HOOK LINE ONE|LINE TWO WITH WORD"   two lines split by |, caps, the member's own words
    --hook-red WORD                   the ONE word in the hook set in the emphasis colour
    --guest-colour "#FCFCFC" --host-colour "#F2B840" --emphasis-colour "#E04B4D"
    --music path.mp3                  optional bed, mixed 17 dB under the voice and dropped out for the B&W beat
"""
import argparse, html, json, math, os, re, subprocess

ap = argparse.ArgumentParser()
ap.add_argument("--footage", default="assets/cut.mp4")
ap.add_argument("--react", default="assets/react.mp4")
ap.add_argument("--words", default="assets/words-cut.json")
ap.add_argument("--hook", default="YOUR HOOK LINE ONE|LINE TWO WITH WORD")
ap.add_argument("--hook-red", default="WORD")
ap.add_argument("--guest-colour", default="#FCFCFC")   # paper: the guest / main speaker
ap.add_argument("--host-colour", default="#F2B840")    # host amber: host lines + the name label
ap.add_argument("--emphasis-colour", default="#E04B4D")  # alarm red: ONE word per caption block
ap.add_argument("--music", default="")          # not shipped: only the member's own licensed track
ap.add_argument("--music-under-db", type=float, default=17.0)
args = ap.parse_args()

# ------------------------------------------------------------------------------------------------- CONFIG
FPS = 30
def has(p):
    """Media isn't shipped with the template: anything whose file is missing is skipped, never a crash."""
    return bool(p) and os.path.exists(p)
DUR = math.floor(float(subprocess.check_output(   # the VIDEO stream: AAC padding makes the file ~0.1 s longer
    ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=duration", "-of", "csv=p=0",
     args.footage]).strip()) * FPS) / FPS
HOOK_END = 2.20            # hook frame held 2.2 s, then a hard cut (DOAC: 1.3-3.8 s). = react.mp4 length here.
PANEL_SCALE = 1.15         # split panels are scaled from the top so the heads sit under the hook (1080p: keep <= 1.3)
SPEAKER_PANEL_X = 405      # source x (at 1.0) of the left edge of each 540-px split panel (frames the face)
REACT_PANEL_X = 276

# ================ CLAUDE CHANGES PER TAKE (the values below are EXAMPLES that show the shape) ================
NAME_LABEL = "Your Name, your role"     # amber label under the hook (the member's own name / role, from profile.md)

# One camera = three crops of the same take: (scale, x, y) on a 50%/50% origin. Never cut M<->T (only 1.08x apart).
CROPS = {"W": (1.0, 0, 0), "M": (1.2, -60, -144), "T": (1.3, 0, -266)}
CAMERA = [  # (cut-clock second, crop). Every audio join cut.py prints gets a change (demo joins: 5.755, 11.809,
            # 17.027, 24.064). Example times from the demo cut.
    (0.00, "W"), (3.86, "T"), (9.20, "T"), (11.809, "W"), (13.84, "M"), (17.027, "W"),
    (19.45, "M"), (21.58, "W"), (22.95, "T"), (24.064, "W"),
]
IDCARD = (5.755, 9.20)     # 20-33% of runtime; starts on an audio join so the card hides that jump cut
IDCARD_FACTS = {           # real facts only (from the member's profile.md), never invented
    "label": "PROFILE",
    "name": ["FIRST", "LAST"],
    "role": "One line on what you do, in your words.",
    "tags": ["YOUR ROLE", "A REAL FACT", "YOUR BUSINESS"],
    "photo": "assets/portrait.png",     # the member's own photo (or a still from her take); skipped if missing
}
BW_RAMP = (24.73, 1.70)    # emotional beat: colour -> B&W from a word in the last line, over 1.7 s, held to the end
EMPHASIS = {"word", "another"}   # lower case: words the speaker stresses; ONE per caption block turns red
CAP_Y = 1545               # caption centre: below the chin, in every crop (SPEC.md "Type")
# ================ end of the per-take block ================
MAX_WORDS, MAX_CHARS, PAUSE_BREAK = 3, 22, 0.15

GRADES = {  # media-treatment patches (validated + normalised by the CLI, cached in grades.json)
    # spec member recipe + "bright home office" (exposure -0.15, shadows -0.30); highlights/whites pulled further
    # because the demo had a bright window behind the head
    "colour": {"adjust": {"exposure": -0.18, "contrast": 0.15, "highlights": -0.35, "whites": -0.20, "shadows": -0.30,
                          "blacks": -0.20, "saturation": -0.12, "temperature": 0.03}, "details": {"vignette": 0.38}},
    "bw": {"adjust": {"exposure": -0.18, "contrast": 0.22, "highlights": -0.35, "whites": -0.20, "shadows": -0.30,
                      "blacks": -0.25, "saturation": -1.0}, "details": {"vignette": 0.42, "grain": 0.08}},
    "print": {"adjust": {"contrast": 0.30, "saturation": -1.0, "exposure": 0.05},
              "effects": {"halftone": 0.85, "halftoneSize": 0.16}, "details": {"grain": 0.10}},
}
SFX = [  # id, file in assets/sfx/, picture moment, measured peak in the file (s), duration, volume
         # demo volumes put each hit 6-8 dB under the voice's loud moments; peaks are the demo files' (measure yours)
         # not shipped: a file that isn't in assets/sfx/ is skipped (add the sound natively in Edits instead)
    ("sfx-photo", "paper-slide.mp3", IDCARD[0] + 0.30, 0.540, 1.10, 0.55),
    ("sfx-tag1", "stamp-1.mp3", IDCARD[0] + 0.75, 0.000, 0.20, 0.42),
    ("sfx-tag2", "stamp-2.mp3", IDCARD[0] + 1.05, 0.000, 0.20, 0.66),
    ("sfx-tag3", "stapler.mp3", IDCARD[0] + 1.35, 0.083, 0.45, 0.58),
]
FRAME = 1 / FPS

# ------------------------------------------------------------------------------------------------- helpers
def grade_attr(name):
    """Normalised data-color-grading value via `hyperframes media-treatment --dry-run` (cached by patch)."""
    cache = json.load(open("grades.json")) if os.path.exists("grades.json") else {}
    key = json.dumps(GRADES[name], sort_keys=True)
    if cache.get(name, {}).get("patch") != key:
        os.makedirs("_work", exist_ok=True)
        open("_work/grade-probe.html", "w").write(
            '<!doctype html><html><head><meta charset="UTF-8"></head><body><div id="root" data-composition-id="main" '
            'data-start="0" data-duration="1" data-width="1080" data-height="1920"><video id="probe" class="clip" '
            'src="../assets/cut.mp4" muted playsinline data-start="0" data-duration="1" data-track-index="0"></video>'
            '</div><script>window.__timelines={};</script></body></html>')
        out = subprocess.check_output(["npx", "--yes", "hyperframes@0.9.83", "media-treatment", "--file",
                                       "_work/grade-probe.html", "--selector", "#probe", "--grading", key,
                                       "--dry-run", "--json"], stderr=subprocess.DEVNULL)
        res = json.loads(out)
        assert res.get("ok") and res["lint"]["ok"], res
        cache[name] = {"patch": key, "value": res["value"]}
        json.dump(cache, open("grades.json", "w"), indent=1)
    return f'data-color-grading="{html.escape(cache[name]["value"])}"'

def hook_sizes(lines, target=615, font_files=("assets/fonts/Inter-Black.ttf", "assets/fonts/Inter-Black.otf",
                                               os.path.expanduser("~/Library/Fonts/Inter-Black.otf"))):
    """DOAC width-locks the two hook lines: both measure the same width, so the shorter line is set bigger."""
    try:
        from PIL import ImageFont
        f = ImageFont.truetype(next(p for p in font_files if os.path.exists(p)), 100)
        per100 = [f.getlength(l) for l in lines]
    except Exception:                      # no PIL / font: average Inter Black caps advance (~0.69 em)
        per100 = [69 * len(l) for l in lines]
    # CSS letter-spacing -0.01em adds -1 px per char at 100 px
    return [round(target / ((w - len(l)) / 100), 1) for w, l in zip(per100, lines)]

def clean(word):
    return re.sub(r"[.,!?;:]+$", "", word)

WEAK = {"a", "an", "the", "of", "to", "and", "on", "in", "for", "with", "as", "our", "at", "by", "from", "or", "but"}
OPENERS = {"that", "which", "who", "so", "like"}           # clause openers also start a block well
OPENS_BADLY = {"us", "them", "me", "him", "her", "can", "will", "is", "are"}
DANGLING = {"i", "we", "you", "they", "she", "he", "it", "can", "will", "is", "are", "was", "were"}  # need what follows

def caption_groups(words):
    """Tier B: 1-3 words a block. Sentences break on punctuation or a 150 ms pause; inside a sentence a tiny scorer
    picks the split (prefer 3s and 2s, never end a block on a weak word, max 22 characters). Words under the hook
    are skipped (the hook never shares the screen with a caption). "hyper" + "-focus" splits are rejoined."""
    ws = []
    for w in words:
        if w["text"].startswith("-") and ws:
            ws[-1] = dict(ws[-1], text=ws[-1]["text"] + w["text"], end=w["end"])
        else:
            ws.append(dict(w))
    ws = [w for w in ws if w["start"] >= HOOK_END - 0.12]
    sentences, cur = [], []
    for i, w in enumerate(ws):
        cur.append(w)
        nxt = ws[i + 1] if i + 1 < len(ws) else None
        if nxt is None or w["text"][-1] in ".,!?" or nxt["start"] - w["end"] >= PAUSE_BREAK:
            sentences.append(cur); cur = []

    def cost(chunk, alone):
        text = " ".join(clean(x["text"]) for x in chunk)
        if len(chunk) == 4 and len(text) > 16: return 99.0   # 4 short words only ("to keep us stuck")
        c = {1: 0 if alone else 3.0, 2: 0.5, 3: 0.0, 4: 1.0}[len(chunk)]
        last, first = clean(chunk[-1]["text"]).lower(), clean(chunk[0]["text"]).lower()
        if last in WEAK: c += 2.0
        if last in DANGLING and not alone: c += 1.5
        if first in WEAK | OPENERS and len(chunk) > 1: c -= 0.4    # a block that opens on "of / in / and" reads as a phrase
        if first in OPENS_BADLY: c += 0.6                # "us execute", "can have": the start belongs to the last block
        if len(" ".join(clean(x["text"]) for x in chunk)) > MAX_CHARS: c += 10.0
        return c

    groups = []
    for sen in sentences:                      # dynamic programme over split points
        n, best = len(sen), {0: (0.0, [])}
        for j in range(1, n + 1):
            opts = [(best[i][0] + cost(sen[i:j], n == 1), best[i][1] + [sen[i:j]])
                    for i in range(max(0, j - MAX_WORDS - 1), j) if i in best]
            best[j] = min(opts, key=lambda o: o[0])
        groups += best[n][1]
    return groups

COLOURS = {"guest": args.guest_colour, "host": args.host_colour}

# ------------------------------------------------------------------------------------------------- pieces
words = json.load(open(args.words))
groups = caption_groups(words)

def captions_html():
    out = []
    for g, grp in enumerate(groups):
        start = max(HOOK_END, grp[0]["start"] - 0.03)
        end = (max(HOOK_END, groups[g + 1][0]["start"] - 0.03)) if g + 1 < len(groups) else DUR
        spans, red_used = [], False
        for w in grp:
            t = clean(w["text"])
            colour = COLOURS.get(w.get("speaker", "guest"), args.guest_colour)
            if not red_used and t.lower().strip("'") in EMPHASIS:
                colour, red_used = args.emphasis_colour, True
            spans.append(f'<span style="color:{colour}">{html.escape(t)}</span>')
        out.append(f'<div id="cap{g}" class="clip cap" data-start="{start:.3f}" data-duration="{end - start:.3f}" '
                   f'data-track-index="20">{" ".join(spans)}</div>')
    return "\n      ".join(out)

hook_lines = args.hook.split("|")
hook_px = hook_sizes(hook_lines)
def hook_html():
    rows = []
    for line, px in zip(hook_lines, hook_px):
        inner = " ".join(f'<b class="red">{html.escape(t)}</b>' if t.strip("?.!,'") == args.hook_red else html.escape(t)
                         for t in line.split(" "))
        rows.append(f'<div class="hrow"><span class="hbox" style="font-size:{px}px">{inner}</span></div>')
    return "\n        ".join(rows)

def camera_js():
    js = []
    for t, c in CAMERA:
        s, x, y = CROPS[c]
        js.append(f'tl.set("#cam", {{ scale: {s}, x: {x}, y: {y} }}, {max(t, 0):.3f});  // {c}')
    return "\n    ".join(js)

def sfx_html():
    return "\n    ".join(
        f'<audio id="{i}" class="clip" src="assets/sfx/{f}" data-start="{at + FRAME - pk:.3f}" data-duration="{d}" '
        f'data-volume="{v}" data-fade-out="0.06" data-track-index="{30 + n}"></audio>'
        for n, (i, f, at, pk, d, v) in enumerate(SFX) if has(f"assets/sfx/{f}"))

def music_html():
    if not args.music:
        return "<!-- no music bed: pass --music <your own licensed track> (mixed 17 dB under the voice) -->"
    lufs = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", subprocess.run(
        ["ffmpeg", "-nostats", "-i", args.music, "-af", "ebur128", "-f", "null", "-"],
        capture_output=True, text=True).stderr)[-1])
    vol = round(10 ** ((-14.0 - args.music_under_db - lufs) / 20), 3)
    b0, b1 = BW_RAMP[0], BW_RAMP[0] + 0.8      # DOAC drama move: the bed drops out under the most human line
    auto = json.dumps({"version": 1, "lanes": [{"target": "volume", "points": [
        {"t": 0, "v": 1}, {"t": b0, "v": 1}, {"t": b1, "v": 0.03}, {"t": DUR, "v": 0.03}]}]})
    return (f'<audio id="bed" class="clip" src="{args.music}" data-start="0" data-duration="{DUR}" data-volume="{vol}" '
            f"data-fade-in=\"0.3\" data-fade-out=\"0.8\" data-automation='{auto}' data-track-index=\"29\"></audio>")

f = IDCARD_FACTS
tags_html = "\n            ".join(f'<span id="tag{i}" class="tag tag{i}">{html.escape(t)}</span>' for i, t in enumerate(f["tags"]))
TAG_TILT = [-2, 1.2, -0.8]   # printed-label look; the tilt lives in GSAP because GSAP also scales the tag
tags_js = "\n    ".join(
    f'tl.fromTo("#tag{i}", {{ opacity: 0, scale: 1.35, rotation: {TAG_TILT[i % 3]} }}, {{ opacity: 1, scale: 1, '
    f'rotation: {TAG_TILT[i % 3]}, duration: 0.12, ease: "power4.out" }}, {IDCARD[0] + 0.75 + 0.30 * i:.3f});'
    for i in range(len(f["tags"])))

# ------------------------------------------------------------------------------------------------- page
def page(overlay):
    """overlay=True: no footage, no voice, no bed, transparent background (graphics for Edits' addOverlay).
    The ID-card stamps stay in, so the card's sound travels with the card."""
    C, BW, PR = grade_attr("colour"), grade_attr("bw"), grade_attr("print")
    footage = "" if overlay else f"""
    <div id="cam">
      <video id="a-roll" class="clip" src="{args.footage}" {C} playsinline data-has-audio="true" data-volume="1"
             data-start="0" data-duration="{DUR}" data-track-index="1"></video>
      <div id="bwwrap" style="opacity:0">
        <video id="bw" class="clip" src="{args.footage}" {BW} muted playsinline data-start="{BW_RAMP[0]:.3f}"
               data-media-start="{BW_RAMP[0]:.3f}" data-duration="{DUR - BW_RAMP[0]:.3f}" data-track-index="2"></video>
      </div>
    </div>"""
    panels = "" if overlay or not args.react else f"""
      <div class="panel" id="pl"><video id="split-speaker" src="{args.footage}" {C} muted playsinline
           class="clip" data-start="0" data-duration="{HOOK_END}" data-track-index="3" style="left:-{SPEAKER_PANEL_X * PANEL_SCALE:.0f}px"></video></div>
      <div class="panel" id="pr"><video id="split-react" src="{args.react}" {C} muted playsinline
           class="clip" data-start="0" data-duration="{HOOK_END}" data-track-index="4" style="left:-{REACT_PANEL_X * PANEL_SCALE:.0f}px"></video></div>"""
    divider = (f'<div id="divider" class="clip divider" data-start="0" data-duration="{HOOK_END}" data-track-index="5"></div>'
               if args.react else "")
    bg = "transparent" if overlay else "#000000"
    bw_js = "" if overlay else f"""
    // ---- emotional beat: colour -> B&W ramp (a B&W-graded copy of the same frames fades in), held to the end ----
    tl.to("#bwwrap", {{ opacity: 1, duration: {BW_RAMP[1]}, ease: "power1.inOut" }}, {BW_RAMP[0]:.3f});"""
    cam_js = "" if overlay else f"""
    // ---- camera: three crops of one take, hard cuts only (gsap.set), never a creeping zoom ----
    {camera_js()}"""
    return f"""<!doctype html>
<!-- GENERATED by build.py: edit build.py (or its CONFIG) and re-run, not this file. -->
<html lang="en-AU" data-resolution="portrait">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1080, height=1920" />
<script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  html, body {{ width: 1080px; height: 1920px; overflow: hidden; background: {bg}; }}
  body {{ font-family: "Inter", sans-serif; }}
  #cam {{ position: absolute; inset: 0; z-index: 1; overflow: hidden; transform-origin: 50% 50%; }}
  #cam video, #bwwrap {{ position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }}
  #bwwrap {{ z-index: 2; }}

  /* hook frame: side-by-side split, glowing divider, width-locked caps on black boxes (SPEC.md "Hook frame") */
  #split {{ position: absolute; inset: 0; z-index: 4; pointer-events: none; }}
  .panel {{ position: absolute; top: 0; width: 540px; height: 1920px; overflow: hidden; }}
  #pl {{ left: 0; }}  #pr {{ left: 540px; }}
  .panel video {{ position: absolute; top: 0; width: {1080 * PANEL_SCALE:.0f}px; height: {1920 * PANEL_SCALE:.0f}px; object-fit: cover; }}
  .divider {{ position: absolute; left: 534px; top: 0; width: 12px; height: 1920px; background: #FBFBFB;
             box-shadow: 0 0 18px 4px rgba(255,255,255,.65), 0 0 46px 14px rgba(255,255,255,.22); }}
  #hook {{ position: absolute; left: 0; right: 0; top: 292px; z-index: 6; text-align: center; }}
  .hrow + .hrow {{ margin-top: 10px; }}
  .hbox {{ display: inline-block; background: #000000; color: #FCFCFC; font-weight: 900; line-height: 1;
          letter-spacing: -0.01em; padding: 24px 30px 22px; border-radius: 8px; }}
  .hbox .red {{ color: {args.emphasis_colour}; font-weight: 900; }}
  #namelabel {{ position: absolute; left: 0; right: 0; top: 548px; z-index: 6; text-align: center; }}
  #namelabel span {{ display: inline-block; background: #000000; padding: 10px 18px 9px; border-radius: 6px;
                    font: 700 38px/1.1 "Inter"; letter-spacing: -0.005em; color: {args.host_colour}; }}

  /* ID card: full-screen dossier insert (SPEC.md "ID card") */
  #idcard {{ position: absolute; inset: 0; z-index: 5; background: #000000; }}
  .paper {{ position: absolute; left: 100px; top: 252px; width: 880px; height: 1056px; transform: rotate(-1.2deg);
           background: radial-gradient(120% 90% at 20% 10%, #F4EBDD 0%, #EFE4D6 45%, #E2D3BF 100%);
           box-shadow: 0 50px 120px rgba(0,0,0,.75), 0 6px 18px rgba(0,0,0,.5); overflow: hidden; }}
  .paper svg.grain {{ position: absolute; inset: 0; width: 100%; height: 100%; opacity: .22; mix-blend-mode: multiply; }}
  .paper .stain {{ position: absolute; right: -80px; bottom: -60px; width: 420px; height: 420px; border-radius: 50%;
                  background: radial-gradient(closest-side, rgba(150,110,60,.16), rgba(150,110,60,0)); }}
  .plabel {{ position: absolute; left: 48px; top: 42px; font: 900 28px/1 "Inter"; letter-spacing: .28em; color: #7F140C; }}
  .prule {{ position: absolute; left: 48px; right: 48px; top: 86px; height: 3px; background: #7F140C; opacity: .55; }}
  .print {{ position: absolute; left: 46px; top: 122px; width: 380px; height: 474px; background: #FAF7F0; padding: 16px 16px 50px;
           box-shadow: 0 18px 40px rgba(0,0,0,.35), 0 2px 6px rgba(0,0,0,.25); }}
  .print img {{ display: block; width: 348px; height: 408px; object-fit: cover; }}
  .tape {{ position: absolute; left: 110px; top: -22px; width: 170px; height: 52px; background: rgba(226,214,186,.78);
          transform: rotate(-3deg); box-shadow: 0 2px 4px rgba(0,0,0,.12); }}
  .tags {{ position: absolute; left: 458px; top: 178px; display: flex; flex-direction: column; align-items: flex-start; gap: 22px; }}
  .tag {{ display: inline-block; background: #7F140C; color: #F3E9DA; font: 900 32px/1 "Inter"; letter-spacing: .06em;
         padding: 14px 18px 12px; }}
  .pname {{ position: absolute; left: 42px; top: 640px; font: 900 128px/0.9 "Inter"; letter-spacing: -0.03em; color: #0A0A0A; }}
  .prole {{ position: absolute; left: 48px; top: 886px; width: 740px; font: italic 500 44px/1.18 "EB Garamond"; color: #2A2320; text-wrap: balance; }}

  /* captions: Tier B, 1-3 words, hard switches, fixed position, speaker-coloured */
  .cap {{ position: absolute; left: 0; right: 0; top: {CAP_Y - 40}px; z-index: 8; text-align: center; padding: 0 60px;
         font: 700 66px/1.2 "Inter"; letter-spacing: -0.01em; overflow: visible;
         text-shadow: 0 3px 12px rgba(0,0,0,.6), 0 0 2px rgba(0,0,0,.6); }}
</style>
</head>
<body>
  <div id="root" data-composition-id="main" data-start="0" data-duration="{DUR}" data-width="1080" data-height="1920">
    {footage}

    <div id="split">{panels}
      {divider}
    </div>
    <div id="hook" class="clip" data-start="0" data-duration="{HOOK_END}" data-track-index="6">
        {hook_html()}
    </div>
    <div id="namelabel" class="clip" data-start="0" data-duration="{HOOK_END}" data-track-index="7"><span>{html.escape(NAME_LABEL)}</span></div>

    <div id="idcard" class="clip" data-start="{IDCARD[0]:.3f}" data-duration="{IDCARD[1] - IDCARD[0]:.3f}" data-track-index="8">
      <div class="paper">
        <svg class="grain" viewBox="0 0 880 1056" preserveAspectRatio="none"><filter id="pn"><feTurbulence type="fractalNoise"
          baseFrequency="0.85" numOctaves="3" seed="7" stitchTiles="stitch"/><feColorMatrix type="saturate" values="0"/></filter>
          <rect width="880" height="1056" filter="url(#pn)"/></svg>
        <div class="stain"></div>
        <div class="plabel">{html.escape(f["label"])}</div><div class="prule"></div>
        <div class="print" id="print"><div class="tape"></div>{f'<img id="portrait" src="{f["photo"]}" {PR} alt="" />' if has(f["photo"]) else ""}</div>
        <div class="tags">
            {tags_html}
        </div>
        <div class="pname">{"<br>".join(html.escape(n) for n in f["name"])}</div>
        <div class="prole">{html.escape(f["role"])}</div>
      </div>
    </div>

    <div id="captions" data-track-kind="captions">
      {captions_html()}
    </div>

    {sfx_html()}
    {"" if overlay else music_html()}
  </div>

  <script>
    const tl = gsap.timeline({{ paused: true }});
    {cam_js}
    {bw_js}

    // ---- hook: already complete on frame 0 (no entrance); leaves on the hard cut at {HOOK_END} s ----

    // ---- ID card: hard cut in; the print drops, tags stamp in 0.3 s apart; hard cut out ----
    tl.fromTo("#print", {{ opacity: 0, scale: 1.12, rotation: -9, filter: "blur(10px)" }},
              {{ opacity: 1, scale: 1, rotation: -4, filter: "blur(0px)", duration: 0.38, ease: "expo.out" }}, {IDCARD[0] + 0.02:.3f});
    {tags_js}

    window.__timelines["main"] = tl;
  </script>
</body>
</html>
"""

open("index.html", "w").write(page(False))
# overlays/ is its own HyperFrames project (two root compositions in one folder would both be picked up)
os.makedirs("overlays", exist_ok=True)
if not os.path.exists("overlays/assets"):
    os.symlink("../assets", "overlays/assets")
open("overlays/hyperframes.json", "w").write(open("hyperframes.json").read())
# meta.json names the project; the template doesn't ship one, so the overlay gets its own either way
json.dump({"id": "diary-of-a-ceo-overlays", "name": "diary-of-a-ceo-overlays"}, open("overlays/meta.json", "w"))
open("overlays/index.html", "w").write(page(True))
print(f"index.html + overlays/index.html written: {DUR} s, {len(groups)} caption groups, hook sizes {hook_px} px")
for g in groups:
    print(f'  {g[0]["start"]:6.2f}  ' + " ".join(clean(w["text"]) for w in g))
