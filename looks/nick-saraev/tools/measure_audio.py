#!/usr/bin/env python3
"""MEASURE the mix (we can't hear it): loudness, each effect's level under the voice, and where each effect peaks.

Inputs: the final render (voice + effects), the voice-only cut (assets/cut.mp4) and an effects-only stem
(the overlay MOV's audio: its footage, and so its voice, is left out).
Usage: python3 tools/measure_audio.py renders/nick-saraev.mp4 renders/nick-saraev-overlays.mov
Prints a table and writes renders/audio-measure.json. It pairs each built <audio> cue with plan.json "sounds" in order,
so run it when every sound in the plan was built (none skipped for a missing file).
"""
import json, re, subprocess, sys, statistics, array

FINAL, STEM = sys.argv[1], sys.argv[2]
VOICE = "assets/cut.mp4"

def ebur(path):
    out = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    I = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", out)[-1])
    tp = float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", out)[-1])
    M = [(float(t), float(m)) for t, m in re.findall(r"t:\s*([\d.]+).*?M:\s*(-?[\d.]+)", out)]
    return I, tp, M

def pcm(path, sr=8000):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(sr), "-f", "s16le", "-"],
                         capture_output=True).stdout
    return array.array("h", raw), sr

fI, fTP, _ = ebur(FINAL)
vI, vTP, vM = ebur(VOICE)
sI, sTP, sM = ebur(STEM)
print(f"final mix: {fI} LUFS integrated, true peak {fTP} dBTP | voice alone {vI} LUFS | effects stem {sI} LUFS")

html = open("index.html").read()
cues = re.findall(r'<audio id="(sfx\d+)" class="clip" src="assets/sfx/([^"]+)" data-start="([\d.]+)" '
                   r'data-duration="([\d.]+)" data-volume="([\d.]+)"[^>]*></audio><!-- ([^>]*) -->', html)
plan = json.load(open("plan.json"))
words = json.load(open("assets/words-cut.json"))
def T(ref):
    m = re.fullmatch(r"w(\d+)([+-][\d.]+)?", ref)
    return words[int(m.group(1))]["start"] + float(m.group(2) or 0)
stem, sr = pcm(STEM)
print(f"{'cue':6} {'file':20} {'picture':>8} {'peak@':>8} {'off(fr)':>7} {'sfx M max':>9} {'voice M':>8} {'under':>6}")
rows = []
starts = [float(c[2]) for c in cues]
for k, ((cid, f, st, du, vol, why), (_, at, _)) in enumerate(zip(cues, plan["sounds"])):
    st, du = float(st), float(du)
    # window ends where the next effect starts, so an overlap never gets counted twice
    nxt = min([s for s in starts if s > st] + [st + du])
    du = min(du, nxt - st)
    pic = T(at)
    # effect level: max momentary (400 ms) loudness of the stem inside the cue window
    sm = [m for t, m in sM if st + 0.1 <= t <= st + du + (0.3 if nxt >= st + du else 0)]
    smax = max(sm) if sm else float("nan")
    # voice level around the cue: median momentary loudness over +-1.5 s while speaking (> -40 LUFS)
    vm = [m for t, m in vM if st - 1.5 <= t <= st + 1.5 and m > -40]
    vmed = statistics.median(vm) if vm else float("nan")
    # where the effect actually peaks (absolute sample peak in the stem window)
    a, b = int(st * sr), int((st + du) * sr)
    seg = stem[a:b]
    pk = (a + max(range(len(seg)), key=lambda i: abs(seg[i]))) / sr if seg else float("nan")
    rows.append((cid, f, pic, pk, (pk - pic) * 30, smax, vmed, vmed - smax))
    print(f"{cid:6} {f:20} {pic:8.3f} {pk:8.3f} {(pk - pic) * 30:7.1f} {smax:9.1f} {vmed:8.1f} {vmed - smax:6.1f}")
json.dump({"final_I": fI, "final_TP": fTP, "voice_I": vI, "stem_I": sI, "cues": rows},
          open("renders/audio-measure.json", "w"), indent=1)
