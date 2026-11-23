#!/usr/bin/env python3
"""Builds index.html (the reel) and _overlay/index.html (the same graphics on a transparent ground, for Edits' addOverlay)
for the FULL look: Just you with more layered on. Every number is in SPEC.md; everything a member changes is in
reel.json.

    $PY cut.py      # once per take: segments + word timings
    $PY build.py && npx --yes hyperframes@0.9.83 check --json

WHY a generator: captions must be real HTML elements with fixed times (HyperFrames rule) and they come from the word
timings, so a new take = new reel.json + new words, same look. Moments are spoken phrases, not seconds.
The look's one hard rule is checked here, not by eye: never two extras (list card, sticker, zoom) at once.
"""
import html, json, os, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
A = lambda p: os.path.join(HERE, p)
CFG = json.load(open(A(next((a for a in sys.argv[1:] if a.endswith(".json")), "reel.json"))))
CUT = json.load(open(A("assets/words-cut.json")))
W, SEGS = CUT["words"], CUT["segments"]
DUR = round(CUT["duration"] - 0.02, 3)
FRAME = 1 / 30

# BRAND: Claude fills these from the member's profile.md before each build (why: the look is fixed,
# the colours and fonts are hers). These defaults are neutral placeholders.
BRAND_INK, BRAND_ACCENT, BRAND_CREAM = "#141414", "#FF5A36", "#FAF7F2"
BRAND_CAP_FONT, BRAND_CAP_FILE, BRAND_CAP_WEIGHT = "Inter", "Inter-ExtraBold.ttf", 800   # caption font, in assets/fonts/

# ---------------------------------------------------------------- LOOK (SPEC.md). Members don't change these.
INK, PINK, CREAM, WHITE = BRAND_INK, BRAND_ACCENT, BRAND_CREAM, "#FFFFFF"   # PINK = the brand accent
HOOK_TOP, HOOK_START_PX, HOOK_MAX_W, HOOK_PAD = 290, 92, 1000, (15, 30)
CAP_FONT, CAP_PX, CAP_CENTRE_Y = BRAND_CAP_FONT, 56, 1540
FACE_ORIGIN = "540px 1380px"           # zoom pivot = the chin line: a punch grows the face UP, never down into the captions
STICKER_TOP, STICKER_H, STICKER_EDGE = 300, 270, 56
LIST_TOP, LIST_X = 300, 64
SOUNDS = {  # name -> (file, volume, duration). Start = moment + 1 frame - the file's measured peak.
    # volumes set by measure.py: sustained sounds peak ~8 dB under the -14 LUFS voice, short hits ~10 dB under
    "list_in":  ("soft-whoosh-2.mp3", 0.52, 0.8),
    "list_out": ("swoosh.mp3", 0.30, 0.6),
    "typing":   ("typing_2s.mp3", 1.25, None),      # runs the length of the sticker, starts on its first frame
    "pop":      ("card-pop.mp3", 1.17, 0.6),
    "thud":     ("soft-thud.mp3", 0.40, 0.9),
}
VOICE_TRIM = 1.0    # measured on the demo: a one-segment reel renders at -14.0 LUFS as levelled (no trim needed)
SF_PRO = "/System/Library/Fonts/SFNS.ttf"      # the hook face. Apple's font, not shipped: copied from your own Mac at build.
HOOK_FALLBACK = A("assets/fonts/Inter-ExtraBold.ttf")   # used when SF Pro isn't on this computer


def has(p):
    """True if a media file is really there (why: fonts, SFX and sticker art aren't shipped; missing ones are skipped)."""
    return os.path.exists(A(p))


def rgba(hex_colour, alpha):
    """'#141414', .35 -> 'rgba(20,20,20,.35)' (why: the sticker shadow is the brand ink, see-through)."""
    h = hex_colour.lstrip("#")
    return f"rgba({int(h[0:2], 16)},{int(h[2:4], 16)},{int(h[4:6], 16)},{alpha})"


# ---------------------------------------------------------------- helpers
def bare(t):
    return re.sub(r"[^\w'-]", "", t).lower()


def at(phrase, after=0.0, edge="start"):
    if phrase == "END":
        return DUR
    want = [bare(x) for x in phrase.split()]
    for i in range(len(W) - len(want) + 1):
        if W[i]["start"] >= after - 0.01 and [bare(w["text"]) for w in W[i:i + len(want)]] == want:
            return W[i]["start"] if edge == "start" else W[i + len(want) - 1]["end"]
    sys.exit(f"phrase not found in the words: {phrase!r}")


def peak(path):
    import numpy as np
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", "48000", "-f", "f32le", "-"],
                         capture_output=True).stdout
    x = np.frombuffer(raw, np.float32)
    n = 480
    e = [float(np.sqrt(np.mean(x[i:i + n] ** 2))) for i in range(0, len(x) - n, n)]
    return e.index(max(e)) * n / 48000 + 0.005


def onset(path):
    """Seconds to the first sound (first 10 ms within 20 dB of the peak): for sounds that run, like typing."""
    import numpy as np
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", "48000", "-f", "f32le", "-"],
                         capture_output=True).stdout
    x = np.frombuffer(raw, np.float32)
    n = 480
    e = np.array([np.sqrt(np.mean(x[i:i + n] ** 2)) for i in range(0, len(x) - n, n)])
    return int(np.argmax(e > e.max() * 0.1)) * n / 48000


def hook_px(lines):
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


# ---------------------------------------------------------------- moments
HOOK_END = at(CFG["hook"]["until"]) - 0.05
def span(start_phrase, end_phrase, lead=0.03, tail=0.05):
    """(in, out) for an extra: in just before the first phrase, out just before the next phrase AFTER it."""
    t_in = at(start_phrase) - lead
    t_out = DUR if end_phrase == "END" else at(end_phrase, after=t_in + 0.05) - tail
    if t_out <= t_in:
        sys.exit(f"'{end_phrase}' is not said after '{start_phrase}'")
    return t_in, t_out


LISTS = [dict(c, **dict(zip(("t_in", "t_out"), span(c["from"], c["until"])))) for c in CFG.get("list_cards", [])]
# stickers are the member's own art (assets/sprites/<name>/f0.png, f1.png ...) and optional: no art = no sticker
def sprite_ok(name):
    return bool(name) and has(f"assets/sprites/{name}/f0.png")


STICKER_CFG = []
for s in CFG.get("stickers", []):
    if not sprite_ok(s.get("sprite")):
        print(f"skipping sticker {s.get('sprite')!r}: no assets/sprites/{s.get('sprite')}/f0.png (use your own art or Edits' GIFs)")
        continue
    if s.get("partner") and not sprite_ok(s["partner"]):
        s = {k: v for k, v in s.items() if k != "partner"}
    STICKER_CFG.append(s)
STICKERS = [dict(s, **dict(zip(("t_in", "t_out"), span(s["from"], s["until"])))) for s in STICKER_CFG]
ZOOMS = [dict(z, **dict(zip(("t_in", "t_out"), span(z["at"], z["to"], 0, 0)))) for z in CFG.get("zooms", [])]
KEYWORDS = {bare(k) for k in CFG.get("keywords", [])}

# the look's rule: never two extras at once
extras = sorted([(c["t_in"], c["t_out"], "list " + c["label"]) for c in LISTS] +
                [(s["t_in"], s["t_out"], "sticker " + s["sprite"]) for s in STICKERS] +
                [(z["t_in"], z["t_out"], f"zoom {z['scale']} on {z['at']}") for z in ZOOMS])
for (a0, a1, an), (b0, b1, bn) in zip(extras, extras[1:]):
    if b0 < a1 - 0.06:      # touching (a hand-off on the same word) is fine
        sys.exit(f"two extras at once: {an} ({a0:.2f}-{a1:.2f}) and {bn} ({b0:.2f}-{b1:.2f})")
changes = sorted({0.0, HOOK_END, DUR} | {t for e in extras for t in e[:2]})
gaps = [round(b - a, 2) for a, b in zip(changes, changes[1:])]


# ---------------------------------------------------------------- captions: 1-3 words, one accent keyword per group
def caption_groups():
    mw, mc = CFG["captions"]["max_words"], CFG["captions"]["max_chars"]
    groups, cur = [], []
    for i, w in enumerate(W):
        if w["start"] < HOOK_END:
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
        # one accent-coloured word per group: the first listed keyword in it
        kw = next((i for i in idx if bare(W[i]["text"]) in KEYWORDS), None)
        out.append((g, idx, round(start, 3), round(end, 3), kw))
    return out


def sprite_imgs(name, frames, h):
    return "".join(f'<img class="sf sf{f}" src="assets/sprites/{name}/f{f}.png" style="height:{h}px" alt="">'
                   for f in range(frames))


def build(overlay=False):
    js = []
    caps = caption_groups()
    cap_html = []
    for g, idx, s, e, kw in caps:
        spans = " ".join(f'<span id="cw{i}" class="cw{" kw" if i == kw else ""}">{html.escape(W[i]["text"])}</span>'
                         for i in idx)
        cap_html.append(f'<div id="cg{g}" class="clip capgroup" data-start="{s}" data-duration="{e - s:.3f}" '
                        f'data-track-index="20"><span class="cbox">{spans}</span></div>')
        js.append(f'tl.fromTo("#cg{g} .cbox", {{ scale: 0.9 }}, {{ scale: 1, duration: 0.12, ease: "back.out(2)" }}, {s});')
        for i in idx:     # word pop as each word is said; the keyword lands a touch bigger
            big = 1.05 if i == kw else 1.0
            js.append(f'tl.fromTo("#cw{i}", {{ scale: 0.9 }}, {{ scale: {big}, duration: 0.1, ease: "back.out(2.5)" }}, {max(s, W[i]["start"] - 0.02):.3f});')

    lines = CFG["hook"]["lines"]
    px = hook_px(lines)
    hook_lines = "".join(f'<div class="hl"><span>{html.escape(l)}</span></div>' for l in lines)

    videos = "" if overlay else "\n      ".join(
        f'<video id="v{i}" class="clip" src="{s["file"]}" playsinline data-has-audio="true" data-volume="{VOICE_TRIM}" '
        f'data-start="{s["start"]}" data-duration="{min(s["duration"], DUR - s["start"]):.3f}" data-track-index="1"></video>'
        for i, s in enumerate(SEGS))
    plate = "" if overlay else f'<div id="plate" class="clip" data-start="0" data-duration="{DUR}" data-track-index="0"></div>'

    # camera: hard punch-ins, never a slow push (zooms are Edits-native, so the overlay has none)
    js.append('tl.set("#cam", { scale: 1 }, 0);')
    for z in ZOOMS:
        js.append(f'tl.set("#cam", {{ scale: {z["scale"]} }}, {z["t_in"]:.3f});')
        js.append(f'tl.set("#cam", {{ scale: 1 }}, {z["t_out"]:.3f});')

    # list cards: accent number tile + white label, one hard ink shadow; whip in from their side, whip out
    list_html = []
    for k, c in enumerate(LISTS):
        list_html.append(f'<div id="list{k}" class="clip listcard" data-start="{c["t_in"]:.3f}" data-duration="{c["t_out"] - c["t_in"]:.3f}" '
                         f'data-track-index="{6 + k}"><div class="lc"><div class="lcs"><span class="num">{html.escape(c["number"])}</span>'
                         f'<span class="lab">{html.escape(c["label"])}</span></div></div></div>')
        sx = -760 if c.get("side", "left") == "left" else 760
        js.append(f'tl.fromTo("#list{k} .lc", {{ x: {sx}, filter: "blur(14px)" }}, {{ x: 0, filter: "blur(0px)", duration: 0.42, ease: "power4.out" }}, {c["t_in"]:.3f});')
        js.append(f'tl.fromTo("#list{k} .num", {{ scale: 1.35 }}, {{ scale: 1, duration: 0.22, ease: "expo.out" }}, {c["t_in"] + 0.18:.3f});')
        js.append(f'tl.to("#list{k} .lc", {{ x: {sx}, filter: "blur(14px)", duration: 0.24, ease: "power3.in" }}, {c["t_out"] - 0.24:.3f});')

    # stickers = the member's own sprite art (frame PNGs), flipped like a GIF at their fps
    st_html = []
    for k, s in enumerate(STICKERS):
        h = STICKER_H
        inner = f'<div class="sp" id="sp{k}a">{sprite_imgs(s["sprite"], s["frames"], h)}</div>'
        if s.get("partner"):
            inner += f'<div class="sp" id="sp{k}b">{sprite_imgs(s["partner"], s["frames"], int(h * 0.78))}</div>'
        side = "right" if s["corner"] == "right" else "left"
        st_html.append(f'<div id="st{k}" class="clip sticker" data-start="{s["t_in"]:.3f}" data-duration="{s["t_out"] - s["t_in"]:.3f}" '
                       f'data-track-index="{10 + k}" style="{side}:{STICKER_EDGE}px"><div class="si">{inner}</div></div>')
        js.append(f'tl.fromTo("#st{k} .si", {{ scale: 0.55, opacity: 0, rotation: {-8 if side == "left" else 8} }}, '
                  f'{{ scale: 1, opacity: 1, rotation: {-3 if side == "left" else 3}, duration: 0.32, ease: "back.out(1.7)" }}, {s["t_in"]:.3f});')
        if s["t_out"] < DUR - 0.05:
            js.append(f'tl.to("#st{k} .si", {{ scale: 0.8, opacity: 0, duration: 0.18, ease: "power2.in" }}, {s["t_out"] - 0.18:.3f});')
        step, f, t = 1 / s["fps"], 0, s["t_in"]
        while t < s["t_out"]:
            for who in ("a", "b") if s.get("partner") else ("a",):
                js.append(f'tl.set("#sp{k}{who} .sf", {{ opacity: 0 }}, {t:.3f}); tl.set("#sp{k}{who} .sf{f}", {{ opacity: 1 }}, {t:.3f});')
            f, t = (f + 1) % s["frames"], t + step

    # sound, one per moment
    sounds = []
    def add(name, moment, dur=None):
        file, vol, d = SOUNDS[name]
        path = A("assets/sfx/" + file)
        if not os.path.exists(path):
            return   # SFX aren't shipped: skip it here and add it natively in Edits instead
        start = moment + FRAME - (onset(path) if name == "typing" else peak(path))
        sounds.append(f'<audio id="sfx-{len(sounds)}-{name}" class="clip" src="assets/sfx/{file}" data-start="{max(0, start):.3f}" '
                      f'data-duration="{dur or d:.2f}" data-volume="{vol}" data-fade-out="{0.2 if name == "typing" else 0.1}" '
                      f'data-track-index="{30 + len(sounds)}"></audio>')
    for c in LISTS:
        add("list_in", c["t_in"] + 0.2)          # the card's fastest frame
        add("list_out", c["t_out"] - 0.12)
    for s in STICKERS:
        if s.get("sound") == "typing":
            add("typing", s["t_in"], dur=min(2.0, s["t_out"] - s["t_in"]))
        elif s.get("sound"):
            add(s["sound"], s["t_in"] + 0.1)
    for z in ZOOMS:
        if z.get("sound"):
            add(z["sound"], z["t_in"])

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
  #cam {{ position: absolute; inset: 0; z-index: 1; overflow: hidden; transform-origin: {FACE_ORIGIN}; }}
  #cam video {{ position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }}

  #hook {{ position: absolute; left: 0; right: 0; top: {HOOK_TOP}px; z-index: 5; text-align: center; }}
  .fade {{ display: inline-block; }}
  .stack {{ display: inline-flex; flex-direction: column; align-items: center; filter: drop-shadow(12px 12px 0 {INK}); }}
  .hl {{ background: {WHITE}; border-radius: 22px; padding: {HOOK_PAD[0]}px {HOOK_PAD[1]}px; margin-top: -2px; }}
  .hl span {{ display: block; font: 800 {px}px/1.2 "SF Pro Hook", "Inter", sans-serif; color: #000; white-space: nowrap; letter-spacing: -0.005em; }}

  /* list card: the Taki numbered label in the brand colours (accent tile + white label, ink hard shadow) */
  .listcard {{ position: absolute; left: {LIST_X}px; top: {LIST_TOP}px; z-index: 6; }}
  .lcs {{ display: flex; align-items: stretch; filter: drop-shadow(10px 10px 0 {INK}); }}   /* shadow on the inner box: GSAP owns .lc's filter */
  .num {{ display: grid; place-items: center; min-width: 132px; padding: 0 22px; background: {PINK}; color: {WHITE};
         font: 800 84px/1 "SF Pro Hook", "Inter", sans-serif; letter-spacing: -0.03em; border-radius: 22px 0 0 22px; }}
  .lab {{ display: flex; align-items: center; padding: 22px 34px 24px 28px; background: {WHITE}; color: #000;
         font: 800 72px/1.05 "SF Pro Hook", "Inter", sans-serif; letter-spacing: -0.01em; border-radius: 0 22px 22px 0; }}

  /* stickers: pixel sprites with a white die-cut edge and a soft drop, like a GIF sticker */
  .sticker {{ position: absolute; top: {STICKER_TOP}px; z-index: 7; }}
  .si {{ display: flex; align-items: flex-end; gap: 6px;
        filter: drop-shadow(4px 0 0 {WHITE}) drop-shadow(-4px 0 0 {WHITE}) drop-shadow(0 4px 0 {WHITE}) drop-shadow(0 -4px 0 {WHITE})
                drop-shadow(0 14px 18px {rgba(INK, .35)}); }}
  .sp {{ position: relative; display: grid; }}
  .sf {{ grid-area: 1 / 1; display: block; opacity: 0; }}
  .sf0 {{ opacity: 1; }}

  /* captions: 1-3 words, white on an ink box, accent hard shadow, ONE keyword in the brand accent */
  .capgroup {{ position: absolute; left: 0; right: 0; top: {CAP_CENTRE_Y - 42}px; text-align: center; z-index: 8; overflow: visible; }}
  .cbox {{ display: inline-block; font: {BRAND_CAP_WEIGHT} {CAP_PX}px/1.1 "{CAP_FONT}", sans-serif; color: {WHITE}; background: {INK};
          padding: 12px 24px 14px; border-radius: 12px; box-shadow: 6px 6px 0 {PINK}; letter-spacing: -0.005em; }}
  .cw {{ display: inline-block; }}
  .cw.kw {{ color: {PINK}; }}
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
    {chr(10).join("    " + h for h in list_html).strip()}
    {chr(10).join("    " + h for h in st_html).strip()}

    <div id="captions" data-track-kind="captions">
      {chr(10).join("      " + c for c in cap_html).strip()}
    </div>

    {chr(10).join("    " + s for s in sounds).strip()}
  </div>

  <script>
    window.__timelines = window.__timelines || {{}};
    const tl = gsap.timeline({{ paused: true }});

    // hook: fully set on frame 0 (the cover); blur-out as the spoken hook ends
    tl.set("#hook .fade", {{ opacity: 1, filter: "blur(0px)" }}, 0);
    tl.to("#hook .fade", {{ opacity: 0, filter: "blur(8px)", duration: 0.18, ease: "power2.in" }}, {HOOK_END - 0.18:.3f});

    {chr(10).join("    " + j for j in js).strip()}

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
print(f"index.html + _overlay/index.html: {DUR} s, hook {px} px until {HOOK_END:.2f} s, {ncaps} caption groups")
print("extras:", [(round(a, 2), round(b, 2), n) for a, b, n in extras])
print("gaps between visual changes (s):", gaps, "max", max(gaps))

for i, seg in enumerate(CFG["segments"]):
    g = {k: v for k, v in seg.get("grade", {}).items() if v}
    if g:
        subprocess.run(["npx", "--yes", "hyperframes@0.9.83", "media-treatment", "--project", HERE, "--selector", f"#v{i}",
                        "--grading", json.dumps({"adjust": g}), "--apply", "--json"], check=True, capture_output=True)
        print(f"graded #v{i}: {g}")
