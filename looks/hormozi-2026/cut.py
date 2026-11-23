#!/usr/bin/env python3
"""Rough cut + word timings for a Hormozi-style reel. Reads config.json (same file build.py reads).

WHY: both Hormozi looks live on a word-tight cut. This keeps the ranges in config["keep"] (source seconds),
speeds them up, levels the voice to -14 LUFS, and remaps every word onto the cut clock so captions land on
the spoken frame.

Timing method (whisper alone drifts, and puts the first word after a pause too early):
  1. word list from mlx_whisper large-v3-turbo with word_timestamps (config["whisper_words"], source seconds)
  2. each word's start is snapped forward to the first 10 ms window louder than -28 dBFS (the real onset)
  3. times are remapped through the keep ranges and the speed-up

Run:  $PY cut.py   (needs numpy; writes assets/cut.mp4 + assets/words-cut.json,
      prints the words). Run transcribe.py first so config["whisper_words"] exists.
"""
import json, re, subprocess, sys, wave, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
C = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "config.json"))
# expanduser: the config holds "~/Movies/Edits-inbox/..." and ffmpeg doesn't expand "~" itself
SRC, KEEP, SPEED = os.path.expanduser(C["footage"]), [tuple(k) for k in C["keep"]], C["speed"]
os.makedirs("assets", exist_ok=True)

# ---- 1. picture + sound: trim each range (12 ms audio fades stop clicks), join, speed up, level ----
parts = []
for i, (a, b) in enumerate(KEEP):
    parts.append(f"[0:v]trim={a}:{b},setpts=PTS-STARTPTS[v{i}];"
                 f"[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS,afade=t=in:d=0.012,afade=t=out:st={b-a-0.012:.3f}:d=0.012[a{i}];")
n = len(KEEP)
fc = "".join(parts) + "".join(f"[v{i}][a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[v][a];" \
     f"[v]setpts=PTS/{SPEED}[vo];[a]atempo={SPEED}[ao]"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", SRC, "-filter_complex", fc, "-map", "[vo]", "-map", "[ao]",
                "-c:v", "libx264", "-crf", "17", "-preset", "medium", "-g", "30", "-r", "30", "-pix_fmt", "yuv420p",
                "-c:a", "pcm_s16le", "assets/_cut_raw.mov"], check=True)
# two-pass loudnorm to -14 LUFS (the voice is the mix: sounds sit 6-10 dB under it)
m = subprocess.run(["ffmpeg", "-hide_banner", "-i", "assets/_cut_raw.mov", "-af",
                    "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                   capture_output=True, text=True).stderr
ln = json.loads(m[m.rfind("{"):m.rfind("}") + 1])
af = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={ln['input_i']}:measured_TP={ln['input_tp']}:"
      f"measured_LRA={ln['input_lra']}:measured_thresh={ln['input_thresh']}:offset={ln['target_offset']}:linear=true,"
      f"aresample=48000")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "assets/_cut_raw.mov", "-c:v", "copy", "-af", af,
                "-c:a", "aac", "-b:a", "192k", "assets/cut.mp4"], check=True)
os.remove("assets/_cut_raw.mov")

# ---- 2. word onsets from the source audio's energy ----
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", SRC, "-vn", "-ac", "1", "-ar", "16000", "assets/_src.wav"], check=True)
w = wave.open("assets/_src.wav")
pcm = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(float) / 32768
os.remove("assets/_src.wav")

def db_at(t):
    i = int(t * 16000)
    seg = pcm[max(i, 0):i + 160]
    return 20 * np.log10(np.sqrt(np.mean(seg ** 2)) + 1e-9) if len(seg) else -99

def snap_start(t):
    """first 10 ms window from t-0.03 to t+0.45 that is louder than -28 dBFS"""
    x = t - 0.03
    while x < t + 0.45:
        if db_at(x) > -28:
            return round(max(x, t - 0.03), 3)
        x += 0.01
    return t

def remap(t):
    acc = 0.0
    for a, b in KEEP:
        if a - 0.06 <= t <= b + 0.06:
            return round((acc + min(max(t, a), b) - a) / SPEED, 3)
        acc += b - a
    return None

# ---- 3. words: merge whisper's split hyphen words ("hyper" + "-focus"), apply proofreading fixes ----
raw = json.load(open(C["whisper_words"]))
merged = []
for wd in raw:
    if wd["text"].startswith("-") and merged:
        merged[-1]["text"] += wd["text"]; merged[-1]["end"] = wd["end"]
    else:
        merged.append(dict(wd))
lo, hi = KEEP[0][0], KEEP[-1][1]
fixes = C.get("fixes", {})
out = []
for wd in merged:
    # a word belongs to the cut if it ENDS after the first keep starts (whisper starts the first word early)
    if wd["end"] <= lo + 0.05 or wd["start"] >= hi:
        continue
    # hand-checked onsets win (key = whisper's "text@start"); everything else is snapped to the energy
    key = f'{wd["text"]}@{wd["start"]}'
    s = C.get("time_fixes", {}).get(key) or snap_start(wd["start"])
    if out and s < out[-1]["src_start"]:
        s = out[-1]["src_start"] + 0.05
    cs, ce = remap(max(s, KEEP[0][0])), remap(wd["end"])
    if cs is None:
        continue
    txt = fixes.get(wd["text"], wd["text"])
    out.append({"id": f"w{len(out)}", "text": txt, "start": cs, "end": max(ce or cs + 0.15, cs + 0.08),
                "src_start": s})
for wd in out:
    wd["src_start"] = round(wd["src_start"], 3)
for i in range(len(out) - 1):          # a word never runs into the next one
    out[i]["end"] = min(out[i]["end"], out[i + 1]["start"])
json.dump(out, open("assets/words-cut.json", "w"), indent=1)
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                            "assets/cut.mp4"], capture_output=True, text=True).stdout)
print(f"cut.mp4 {dur:.3f} s, {len(out)} words, {len(out) / dur * 60:.0f} wpm")
print(" ".join(f"{i}:{w['text']}@{w['start']}" for i, w in enumerate(out)))
