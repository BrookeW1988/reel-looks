#!/usr/bin/env python3
"""Measure the rendered mix: integrated loudness + true peak of the render, and each sound effect's level against
the voice. WHY: we can't listen, so the rule "voice -14 LUFS, each effect 6-10 dB under the voice" is checked by numbers.

How a hit is measured: the effect alone (its file, at its gain, at its start) is rendered to a stem; its loudest
400 ms momentary loudness (EBU R128 M) is compared with the voice's integrated loudness.
Usage: python3 measure_audio.py renders/<slug>.mp4   (reads sfx.json + the voice file named in it, written by build.py)
"""
import json, subprocess, sys, re

def r128(path, extra_filter=""):
    p = subprocess.run(["ffmpeg", "-nostats", "-i", path, "-filter_complex", f"[0:a:0]{extra_filter}ebur128=peak=true:metadata=1,"
                        "ametadata=print:key=lavfi.r128.M:file=/dev/stderr", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    I = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", p)[-1])
    tp = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", p)
    M = [(float(t), float(m)) for t, m in re.findall(r"pts_time:([\d.]+)\s*\n?lavfi.r128.M=(-?[\d.]+)", p)]
    return I, (float(tp[-1]) if tp else None), M

render = sys.argv[1]
cfg = json.load(open("sfx.json"))
I, tp, _ = r128(render)
print(f"RENDER {render}: integrated {I:.1f} LUFS, true peak {tp} dBTP")
if cfg.get("voice"):
    vI, vtp, vM = r128(cfg["voice"], f"volume={cfg.get('voice_gain', 1)},")
    print(f"VOICE  {cfg['voice']} (x{cfg.get('voice_gain', 1)}): integrated {vI:.1f} LUFS")
else:
    vI = None
for h in cfg["sfx"]:
    # stem = the effect file at its gain, padded so the momentary meter has context
    trim = f"atrim={h.get('offset', 0)}:{h.get('offset', 0) + h['slot']}," if h.get("slot") else ""
    f = f"{trim}volume={h['gain']},apad=pad_dur=1,"
    hI, htp, hM = r128(h["file"], f)
    mmax = max((m for _, m in hM), default=float("nan"))
    rel = f"{mmax - vI:+.1f} dB vs voice" if vI is not None else ""
    print(f"  {h['id']:12s} at {h['start']:6.3f}s  max momentary {mmax:6.1f} LUFS  {rel}")
