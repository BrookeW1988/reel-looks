#!/usr/bin/env python3
"""Measure the rendered sound, don't trust the plan.

WHY: nobody can "hear" a render from here, so we measure: (1) the finished reel's loudness and true peak, (2) every
sound effect's level against the voice at the same moment, (3) whether each hit lands 1 frame after its picture.

The overlays render (footage hidden) carries ONLY the effects, so it is a real effects stem from the same engine.
    python3 measure_audio.py renders/mariah-brunner.mp4 renders/mariah-brunner-overlays.mov
"""
import json, os, re, subprocess, sys
import numpy as np

MAIN, STEM = sys.argv[1], sys.argv[2]
VOICE = "assets/cut.mp4"
C = json.load(open("reel.json"))
W = json.load(open(C["words"]))

def T(x):
    m = re.fullmatch(r"w(\d+)([+-][\d.]+)?", x)
    return W[int(m.group(1))]["start"] + float(m.group(2) or 0) if m else float(x)

def momentary(path):
    """ebur128 momentary loudness (400 ms window) every 100 ms -> list of (t, M)."""
    e = subprocess.run(["ffmpeg", "-v", "verbose", "-hide_banner", "-nostats", "-i", path, "-vn", "-af", "ebur128=framelog=verbose", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    return [(float(t), float(m)) for t, m in re.findall(r"t:\s*([\d.]+)\s+TARGET.*?M:\s*(-?[\d.]+|-inf)", e) if m != "-inf"]

def summary(path):
    e = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-vn", "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    s = e[e.rfind("Summary"):]
    return float(re.search(r"I:\s*(-?[\d.]+)", s).group(1)), float(re.search(r"Peak:\s*(-?[\d.]+)", s).group(1))

def pcm(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vn", "-ac", "1", "-ar", "48000", "-f", "s16le", "-"],
                         capture_output=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768

I, TP = summary(MAIN)
print(f"MAIN  integrated {I:.1f} LUFS (target -14), true peak {TP:.1f} dBTP (target <= -1)")
mv, ms = momentary(VOICE), momentary(STEM)
stem = pcm(STEM)
env = np.array([np.sqrt((stem[i:i + 480] ** 2).mean()) for i in range(0, len(stem) - 480, 480)])  # 10 ms RMS

def at(series, t0, t1, f):
    v = [m for t, m in series if t0 <= t <= t1]
    return f(v) if v else float("nan")

rows = []
for s in [s for s in C["sfx"] if os.path.exists(f"assets/sfx/{s['file']}")]:   # skipped (missing) sounds aren't in the render
    pic = T(s["at"])                      # the picture moment
    lo, hi = pic - 0.15, pic + 0.6
    fx = at(ms, pic, pic + 0.6, max)                         # effect's loudest 400 ms after its picture
    vo = at(mv, pic - 0.2, pic + 0.8, lambda v: float(np.median(v)))   # voice level around it (median: robust to gaps)
    a, b = int(lo / 0.01), int((pic + 0.25) / 0.01)
    # onset = first 10 ms frame within 12 dB of the effect's own loudest frame (robust for sustained sounds)
    seg = env[a:b]
    db = 20 * np.log10(seg + 1e-9)
    onset = (a + int(np.argmax(db >= db.max() - 12))) * 0.01
    peak = (a + int(np.argmax(db))) * 0.01
    # transients (pops, clicks, thud) are judged by onset; slides and whooshes build up, so by their peak
    swell = any(k in s["file"] for k in ("slide", "swipe", "whoosh"))
    hit = peak if swell else onset
    rows.append((s["file"], pic, hit, hit - pic, fx, vo, vo - fx))
    print(f"{'peak ' if swell else 'onset'} {s['file']:22s} picture {pic:6.2f}  hit {hit:6.2f} ({(hit - pic) * 1000:+4.0f} ms)  "
          f"fx {fx:6.1f}  voice {vo:6.1f}  -> {vo - fx:4.1f} dB under")
ok = [r for r in rows if 6 <= r[6] <= 10]
print(f"\n{len(ok)}/{len(rows)} effects sit 6-10 dB under the voice; "
      f"hits {sum(1 for r in rows if 0 <= r[3] <= 0.07)}/{len(rows)} land 0-70 ms after the picture (1 frame = 33 ms)")
