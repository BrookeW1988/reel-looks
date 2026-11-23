#!/usr/bin/env python3
"""MEASURE the rendered mix (we can't listen, so we measure). Run after rendering:  python3 measure.py
1. Final mix: integrated loudness + true peak of renders/iman-gadzhi.mp4 (target -14 LUFS, peak <= -1 dBTP).
2. Every effect: rebuilt as its own stem from assets/sfx/placements.json + the <audio> tags in index.html, then its
   momentary-max loudness (400 ms) is compared with the voice: target 6-10 dB under the voice's -14 LUFS.
3. Proof the effects are really IN the render: residual = rendered mix minus the voice track; its loudest moment near
   each placement must land within 2 frames of picture + 1 frame.
Writes renders/audio-measure.json and prints a table for REVIEW.md.
"""
import json, re, subprocess
import numpy as np

SR = 48000
REN = "renders/iman-gadzhi.mp4"

def pcm(path, extra=()):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, *extra, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()

def loud(path):
    out = subprocess.run(["ffmpeg", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    return float(re.findall(r"I:\s+(-?[\d.]+) LUFS", out)[-1]), float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", out)[-1])

def ebur_m_max(x):
    """EBU R128 momentary (400 ms) max of a mono float buffer, in LUFS (ffmpeg ebur128)."""
    p = subprocess.run(["ffmpeg", "-v", "info", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-",
                        "-af", "apad=pad_dur=0.5,ebur128=metadata=1,ametadata=print:key=lavfi.r128.M", "-f", "null", "-"],
                       input=x.astype(np.float32).tobytes(), capture_output=True)
    vals = [float(v) for v in re.findall(r"lavfi.r128.M=(-?[\d.]+)", p.stderr.decode())]
    return max(vals) if vals else -120.0

I, TP = loud(REN)
voice = pcm("assets/cut.mp4")
mix = pcm(REN)
n = min(len(voice), len(mix))
resid = mix[:n] - voice[:n]

tags = {m.group(1): m.group(0) for m in re.finditer(r'<audio id="([^"]+)"[^>]*>', open("index.html").read())}
rows = []
STARTS = sorted(float(re.search(r'data-start="([\d.]+)"', v).group(1)) for v in tags.values())
for p in json.load(open("assets/sfx/placements.json")):
    tag = tags[p["id"]]
    start = float(re.search(r'data-start="([\d.]+)"', tag).group(1))
    vol = float(re.search(r'data-volume="([\d.]+)"', tag).group(1))
    ms = float((re.search(r'data-media-start="([\d.]+)"', tag) or [None, 0])[1])
    d = float(re.search(r'data-duration="([\d.]+)"', tag).group(1))
    fx = pcm(f"assets/sfx/{p['file']}", ("-ss", str(ms), "-t", str(d))) * vol
    fx_m = ebur_m_max(fx)
    a, b = int(start * SR), int((start + d) * SR)
    v_m = ebur_m_max(voice[max(0, a - SR // 5): b + SR // 5])          # the voice around the hit
    # where the hit actually peaks in the render (residual), 5 ms envelope
    nxt = [s for s in STARTS if s > start + 1e-3]
    b_r = min(b, int(nxt[0] * SR)) if nxt else b                       # stop before the next effect starts
    seg = resid[a: min(b_r, n)]
    hop = SR // 200
    env = np.array([np.sqrt(np.mean(seg[k:k + hop] ** 2)) for k in range(0, max(1, len(seg) - hop), hop)])
    hit = start + float(np.argmax(env)) * hop / SR if len(env) else None
    target = p["picture"] + 1 / 30
    rows.append({"id": p["id"], "file": p["file"], "picture": p["picture"], "render_peak": round(hit, 3) if hit else None,
                 "peak_vs_picture_frames": round((hit - p["picture"]) * 30, 1) if hit else None,
                 "fx_momentary_max_lufs": round(fx_m, 1), "under_voice_db": round(-14.0 - fx_m, 1),
                 "under_local_voice_db": round(v_m - fx_m, 1)})

res = {"render": REN, "integrated_lufs": I, "true_peak_dbtp": TP, "effects": rows}
json.dump(res, open("renders/audio-measure.json", "w"), indent=1)
print(f"mix: {I} LUFS integrated, true peak {TP} dBTP")
print(f"{'effect':16s} {'picture':>7s} {'render pk':>9s} {'frames':>6s} {'fx M max':>8s} {'under -14':>9s} {'under local':>11s}")
for r in rows:
    print(f"{r['id']:16s} {r['picture']:7.3f} {r['render_peak'] or 0:9.3f} {r['peak_vs_picture_frames'] or 0:6.1f} "
          f"{r['fx_momentary_max_lufs']:8.1f} {r['under_voice_db']:9.1f} {r['under_local_voice_db']:11.1f}")
