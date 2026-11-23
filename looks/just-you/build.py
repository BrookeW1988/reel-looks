#!/usr/bin/env python3
"""Builds index.html (the reel) and _overlay/index.html (the same graphics on a transparent ground, for Edits' addOverlay)
for the JUST YOU look. Every number is in SPEC.md; everything a member changes is in reel.json.

    $PY cut.py      # once per take: segments + word timings
    $PY build.py && npx --yes hyperframes@0.9.83 check --json

WHY a generator: captions must be real HTML elements with fixed times (HyperFrames rule) and they come from the word
timings, so a new take = new reel.json + new words, same look. Moments are spoken phrases, not seconds, so nothing
needs re-timing by hand.
"""
import html, json, os, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
A = lambda p: os.path.join(HERE, p)
CFG = json.load(open(A(next((a for a in sys.argv[1:] if a.endswith(".json")), "reel.json"))))
CUT = json.load(open(A("assets/words-cut.json")))
W, SEGS = CUT["words"], CUT["segments"]
DUR = round(CUT["duration"] - 0.02, 3)        # a hair under the media so the last frame is never black
FRAME = 1 / 30

# BRAND: Claude fills these from the member's profile.md before each build (why: the look is fixed,
# the colours and fonts are hers). These defaults are neutral placeholders.
BRAND_INK, BRAND_ACCENT, BRAND_CREAM = "#141414", "#FF5A36", "#FAF7F2"
BRAND_CAP_FONT, BRAND_CAP_FILE, BRAND_CAP_WEIGHT = "Inter", "Inter-Bold.ttf", 700   # caption font, in assets/fonts/

# ---------------------------------------------------------------- LOOK (SPEC.md). Members don't change these.
INK, PINK, CREAM, WHITE = BRAND_INK, BRAND_ACCENT, BRAND_CREAM, "#FFFFFF"
HOOK_TOP, HOOK_START_PX, HOOK_MAX_W, HOOK_PAD = 290, 92, 1000, (15, 30)   # the Taki-style hook numbers (SPEC.md)
CAP_FONT, CAP_PX, CAP_CENTRE_Y = BRAND_CAP_FONT, 54, 1540
CARD_TOP, CARD_FRAME, CARD_RADIUS = 280, 8, 24
SFX = {  # moment -> (file, volume). Start = moment + 1 frame - the file's measured peak (see peak()).
    "cta_in":  ("card-snap.mp3", 0.98),     # measured: peak M -24 LUFS = 10 dB under the -14 voice
    "card_in": ("paper-slide-1.mp3", 0.30),  # measured: peak M -22 LUFS = 8 dB under
}
VOICE_TRIM = 1.0    # the renderer is transparent; voice level is set in cut.py (loudnorm -14 + -3 dBFS limiter)
SF_PRO = "/System/Library/Fonts/SFNS.ttf"      # the hook face. Apple's font, not shipped: copied from your own Mac at build.
HOOK_FALLBACK = A("assets/fonts/Inter-ExtraBold.ttf")   # used when SF Pro isn't on this computer


def has(p):
    """True if a media file is really there (why: fonts, SFX and images aren't shipped; missing ones are skipped)."""
    return os.path.exists(A(p))


def rgba(hex_colour, alpha):
    """'#141414', .35 -> 'rgba(20,20,20,.35)' (why: the card shadow is the brand ink, see-through)."""
    h = hex_colour.lstrip("#")
    return f"rgba({int(h[0:2], 16)},{int(h[2:4], 16)},{int(h[4:6], 16)},{alpha})"


# ---------------------------------------------------------------- helpers
def bare(t):
    return re.sub(r"[^\w'-]", "", t).lower()


def at(phrase, after=0.0, edge="start"):
    """Time of a spoken phrase on the reel clock ('END' = the end of the reel)."""
    if phrase == "END":
        return DUR
    want = [bare(x) for x in phrase.split()]
    for i in range(len(W) - len(want) + 1):
        if W[i]["start"] >= after - 0.01 and [bare(w["text"]) for w in W[i:i + len(want)]] == want:
            return W[i]["start"] if edge == "start" else W[i + len(want) - 1]["end"]
    sys.exit(f"phrase not found in the words: {phrase!r}")


def peak(path):
    """Seconds from a sound file's start to its loudest 10 ms (so its hit can land 1 frame after the picture)."""
    import numpy as np
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", "48000", "-f", "f32le", "-"],
                         capture_output=True).stdout
    x = np.frombuffer(raw, np.float32)
    n = 480
    e = [float(np.sqrt(np.mean(x[i:i + n] ** 2))) for i in range(0, len(x) - n, n)]
    return e.index(max(e)) * n / 48000 + 0.005


def fdur(path):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                                capture_output=True, text=True).stdout.strip())


def hook_px(lines):
    """Auto-fit: start 92 px, shrink 2 px at a time until the widest line + padding <= 1000."""
    from PIL import Image, ImageDraw, ImageFont
    d = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    emo = re.compile("[\U0001F000-\U0001FFFF☀-➿️]")
    face = SF_PRO if os.path.exists(SF_PRO) else HOOK_FALLBACK
    if not os.path.exists(face):
        sys.exit("No hook font: SF Pro isn't on this Mac and assets/fonts/Inter-ExtraBold.ttf is missing (see SPEC.md).")
    px = HOOK_START_PX
    while px > 50:
        f = ImageFont.truetype(face, px)
        try:
            f.set_variation_by_axes([100, 28, 400, 800])
        except Exception:
            pass
        widest = max(d.textlength(emo.sub("", l), font=f) + len(emo.findall(l)) * px * 1.15 for l in lines)
        if widest + 2 * HOOK_PAD[1] <= HOOK_MAX_W:
            return px
        px -= 2
    return px


# ---------------------------------------------------------------- moments (all from the spoken words)
HOOK_END = at(CFG["hook"]["until"]) - 0.05
CTA_IN = at(CFG["cta"]["from"]) - 0.03 if CFG.get("cta") else None
CTA_OUT = at(CFG["cta"]["until"], after=CTA_IN + 0.05) - 0.06 if CFG.get("cta") else None
for c in CFG.get("cards", []):
    if not has(c["image"]):
        print(f"skipping card: {c['image']} isn't there (add your own screenshot to assets/cards/)")
CARDS = [{**c, "t_in": at(c["from"]) - 0.03, "t_out": at(c["until"], after=at(c["from"]) + 0.05) if c["until"] != "END" else DUR}
         for c in CFG.get("cards", []) if has(c["image"])]


# ---------------------------------------------------------------- captions: 1-3 words, off on the hook and CTA
def quiet(t):
    if t < HOOK_END:
        return True
    return CTA_IN is not None and CTA_IN - 0.02 <= t < CTA_OUT


def caption_groups():
    mw, mc = CFG["captions"]["max_words"], CFG["captions"]["max_chars"]
    groups, cur = [], []
    for i, w in enumerate(W):
        if quiet(w["start"]):
            if cur:
                groups.append(cur); cur = []
            continue
        if cur:
            prev = W[cur[-1]]
            text = " ".join(W[j]["text"] for j in cur + [i])
            if (len(cur) >= mw or len(text) > mc or prev["text"][-1] in ".,?!" or w["start"] - prev["end"] >= 0.15
                    or w["seg"] != prev["seg"]):
                groups.append(cur); cur = []
        cur.append(i)
    if cur:
        groups.append(cur)
    out = []
    for g, idx in enumerate(groups):
        start = max(0.1, W[idx[0]]["start"] - 0.04)
        nxt = W[groups[g + 1][0]]["start"] - 0.04 if g + 1 < len(groups) else DUR
        end = min(nxt, W[idx[-1]]["end"] + 0.6, DUR)
        if CTA_IN is not None and start < CTA_IN:
            end = min(end, CTA_IN - 0.02)
        out.append((g, idx, round(start, 3), round(end, 3)))
    return out


def build(overlay=False):
    caps = caption_groups()
    cap_html, cap_js = [], []
    for g, idx, s, e in caps:
        words = " ".join(html.escape(W[i]["text"]) for i in idx)
        cap_html.append(f'<div id="cg{g}" class="clip capgroup" data-start="{s}" data-duration="{e - s:.3f}" '
                        f'data-track-index="20"><span class="cbox">{words}</span></div>')
        cap_js.append(f'tl.fromTo("#cg{g} .cbox", {{ scale: 0.9 }}, {{ scale: 1, duration: 0.12, ease: "back.out(2)" }}, {s});')

    lines = CFG["hook"]["lines"]
    px = hook_px(lines)
    hook_lines = "".join(f'<div class="hl"><span>{html.escape(l)}</span></div>' for l in lines)

    videos = "" if overlay else "\n      ".join(
        f'<video id="v{i}" class="clip" src="{s["file"]}" playsinline data-has-audio="true" data-volume="{VOICE_TRIM}" '
        f'data-start="{s["start"]}" data-duration="{min(s["duration"], DUR - s["start"]):.3f}" data-track-index="1"></video>'
        for i, s in enumerate(SEGS))
    plate = "" if overlay else (f'<div id="plate" class="clip" data-start="0" data-duration="{DUR}" '
                                f'data-track-index="0"></div>')

    cards_html, cards_js = [], []
    for k, c in enumerate(CARDS):
        w = c.get("width", 780)
        cards_html.append(f'<div id="card{k}" class="clip card" data-start="{c["t_in"]:.3f}" '
                          f'data-duration="{c["t_out"] - c["t_in"]:.3f}" data-track-index="{6 + k}" style="width:{w}px; left:{(1080 - w) // 2}px">'
                          f'<img src="{c["image"]}" alt="{html.escape(c["alt"])}"></div>')
        # slide in simply: down 40 px + blur 10 -> 0, long-tailed ease; leaves 40% faster than it came
        cards_js.append(f'tl.fromTo("#card{k}", {{ y: -40, opacity: 0, filter: "blur(10px)" }}, '
                        f'{{ y: 0, opacity: 1, filter: "blur(0px)", duration: 0.35, ease: "power3.out" }}, {c["t_in"]:.3f});')
        if c["t_out"] < DUR - 0.05:
            cards_js.append(f'tl.to("#card{k}", {{ y: -30, opacity: 0, filter: "blur(8px)", duration: 0.2, ease: "power2.in" }}, {c["t_out"] - 0.2:.3f});')

    sounds, n = [], 0
    moments = {"cta_in": CTA_IN, "card_in": CARDS[0]["t_in"] if CARDS else None}
    for key, (f, vol) in SFX.items():
        if moments.get(key) is None or not has("assets/sfx/" + f):
            continue   # no moment, or the sound isn't in assets/sfx/ (add it natively in Edits instead)
        start = max(0, moments[key] + FRAME - peak(A("assets/sfx/" + f)))
        sounds.append(f'<audio id="sfx-{key}" class="clip" src="assets/sfx/{f}" data-start="{start:.3f}" '
                      f'data-duration="{min(0.6, fdur(A("assets/sfx/" + f))):.2f}" data-volume="{vol}" data-fade-out="0.1" data-track-index="{30 + n}"></audio>')
        n += 1

    cta_html = ""
    if CTA_IN is not None:
        cta_html = (f'<div id="cta" class="clip" data-start="{CTA_IN:.3f}" data-duration="{CTA_OUT - CTA_IN:.3f}" '
                    f'data-track-index="5"><div class="fade"><div class="stack"><div class="hl"><span>{html.escape(CFG["cta"]["text"])}</span></div></div></div></div>')

    ground = "transparent" if overlay else INK
    page = f"""<!doctype html>
<html lang="en" data-resolution="portrait">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1080, height=1920" />
<script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
<style>
  @font-face {{ font-family: "SF Pro Hook"; src: url("assets/fonts/SFNS.ttf"); font-weight: 1 1000; }}
  @font-face {{ font-family: "Inter"; src: url("assets/fonts/Inter-ExtraBold.ttf"); font-weight: 800; }}
  @font-face {{ font-family: "{CAP_FONT}"; src: url("assets/fonts/{BRAND_CAP_FILE}"); font-weight: {BRAND_CAP_WEIGHT}; }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  html, body {{ width: 1080px; height: 1920px; overflow: hidden; background: {ground}; }}
  #plate {{ position: absolute; inset: 0; background: {INK}; z-index: 0; }}
  #cam {{ position: absolute; inset: 0; z-index: 1; overflow: hidden; }}
  #cam video {{ position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }}

  /* Taki-style hook: one white rounded box per line, boxes touching, ONE hard ink offset shadow round the stack */
  #hook, #cta {{ position: absolute; left: 0; right: 0; top: {HOOK_TOP}px; z-index: 5; text-align: center; }}
  .fade {{ display: inline-block; }}
  .stack {{ display: inline-flex; flex-direction: column; align-items: center; filter: drop-shadow(12px 12px 0 {INK}); }}
  .hl {{ background: {WHITE}; border-radius: 22px; padding: {HOOK_PAD[0]}px {HOOK_PAD[1]}px; margin-top: -2px; }}
  .hl span {{ display: block; font: 800 {px}px/1.2 "SF Pro Hook", "Inter", sans-serif; color: #000; white-space: nowrap;
             letter-spacing: -0.005em; }}

  .card {{ position: absolute; top: {CARD_TOP}px; z-index: 6; background: {WHITE}; padding: {CARD_FRAME}px;
          border-radius: {CARD_RADIUS}px; box-shadow: 0 24px 60px {rgba(INK, .35)}, 0 3px 10px {rgba(INK, .18)}; }}
  .card img {{ display: block; width: 100%; border-radius: {CARD_RADIUS - CARD_FRAME}px; }}

  /* captions: 1-3 words, white on an ink box, low on the chest, one hard shadow in the brand accent */
  .capgroup {{ position: absolute; left: 0; right: 0; top: {CAP_CENTRE_Y - 40}px; text-align: center; z-index: 8; overflow: visible; }}
  .cbox {{ display: inline-block; font: {BRAND_CAP_WEIGHT} {CAP_PX}px/1.1 "{CAP_FONT}", sans-serif; color: {WHITE}; background: {INK};
          padding: 12px 24px 14px; border-radius: 12px; box-shadow: 6px 6px 0 {PINK}; letter-spacing: -0.005em; }}
</style>
</head>
<body>
  <div id="root" data-composition-id="main" data-start="0" data-duration="{DUR}" data-width="1080" data-height="1920">
    {plate}
    <div id="cam">
      {videos}
    </div>

    <div id="hook" class="clip" data-start="0" data-duration="{HOOK_END:.3f}" data-track-index="4">
      <div class="fade"><div class="stack">{hook_lines}</div></div>
    </div>
    {cta_html}
    {"".join(cards_html)}

    <div id="captions" data-track-kind="captions">
      {chr(10).join("      " + c for c in cap_html).strip()}
    </div>

    {chr(10).join("    " + s for s in sounds).strip()}
  </div>

  <script>
    window.__timelines = window.__timelines || {{}};
    const tl = gsap.timeline({{ paused: true }});

    // hook: fully set on frame 0 (the cover); leaves with a short blur-out as the spoken hook ends
    tl.set("#hook .fade", {{ opacity: 1, filter: "blur(0px)" }}, 0);
    tl.to("#hook .fade", {{ opacity: 0, filter: "blur(8px)", duration: 0.18, ease: "power2.in" }}, {HOOK_END - 0.18:.3f});
    {"" if CTA_IN is None else f'''tl.fromTo("#cta .fade", {{ opacity: 0, scale: 1.06 }}, {{ opacity: 1, scale: 1, duration: 0.16, ease: "expo.out" }}, {CTA_IN:.3f});
    tl.to("#cta .fade", {{ opacity: 0, duration: 0.14, ease: "power2.in" }}, {CTA_OUT - 0.14:.3f});'''}

    // cards
    {chr(10).join("    " + j for j in cards_js).strip()}

    // captions (generated from assets/words-cut.json): pop 90% -> 100%, no word highlight
    {chr(10).join("    " + j for j in cap_js).strip()}

    window.__timelines["main"] = tl;
  </script>
</body>
</html>
"""
    return page, len(caps), px


os.makedirs(A("assets/fonts"), exist_ok=True)
if not os.path.exists(A("assets/fonts/SFNS.ttf")) and os.path.exists(SF_PRO):
    shutil.copy(SF_PRO, A("assets/fonts/SFNS.ttf"))   # why: Apple's font can't be shipped, so it comes from this Mac
page, ncaps, px = build()
open(A("index.html"), "w").write(page)
# the overlay is its own tiny project (one root composition per project), sharing assets/ through a symlink
os.makedirs(A("_overlay"), exist_ok=True)
for f in ("hyperframes.json", "package.json", "meta.json"):
    if os.path.exists(A(f)):   # meta.json only exists once HyperFrames has made one
        shutil.copy(A(f), A("_overlay/" + f))
if not os.path.lexists(A("_overlay/assets")):
    os.symlink("../assets", A("_overlay/assets"))
open(A("_overlay/index.html"), "w").write(build(overlay=True)[0])
if os.path.exists(A("overlay.html")):
    os.remove(A("overlay.html"))
print(f"index.html + _overlay/index.html: {DUR} s, hook {px} px until {HOOK_END:.2f} s, {ncaps} caption groups, "
      f"cta {CTA_IN and round(CTA_IN, 2)}-{CTA_OUT and round(CTA_OUT, 2)}, cards {[(round(c['t_in'], 2), round(c['t_out'], 2)) for c in CARDS]}")

# grade each segment through media-treatment (house contract: never CSS filters on footage)
for i, seg in enumerate(CFG["segments"]):
    g = {k: v for k, v in seg.get("grade", {}).items() if v}
    if g:
        subprocess.run(["npx", "--yes", "hyperframes@0.9.83", "media-treatment", "--project", HERE, "--selector", f"#v{i}",
                        "--grading", json.dumps({"adjust": g}), "--apply", "--json"], check=True, capture_output=True)
        print(f"graded #v{i}: {g}")
