#!/usr/bin/env python3
"""Rough cut for a Serialised episode.

WHY: the format is "same opening every episode, cut pauses only, 1.1-1.3x". An episode = the series premise line
(the same sentence every episode) + this episode's point.
For each episode: change SRC, KEEP, SPEED and SCRIPT below, then run
    $PY cut.py
    python3 build.py

Writes assets/cut.mp4 (voice loudness-normalised to -14 LUFS) and assets/words-cut.json (word timings on the cut
clock, from mlx_whisper large-v3-turbo run on the CUT file, so no remapping drift).
"""
import json, os, subprocess, sys, re

# your SDR take (expanduser: so "~" works). Example path: put your own file name here.
SRC = os.path.expanduser("~/Movies/Edits-inbox/your-take.mov")
# Source seconds to keep, in order. EXAMPLE VALUES: replace with your own ranges.
# Edges should sit in measured dips (silencedetect -20 dB + a 30 ms RMS envelope), never mid-word.
KEEP = [
    (2.03, 4.115),   # the series premise line, part 1
    (5.95, 9.62),    # the series premise line, part 2
    (40.93, 42.95),  # "Number <N> is <topic>." (the spoken episode number)
    (43.12, 47.72),  # this episode's point, sentence 1
    (48.08, 50.50),  # sentence 2 (keep a deliberate beat before a payoff word)
    (50.80, 55.00),  # closing sentence
]
SPEED = 1.15
LUFS = -14.0
# The proofread words (what you really say, word for word, in the kept ranges). Caption text comes from here, matched
# to whisper's timings BY POSITION, so ASR slips (e.g. "brain slack hours" for "brains like ours") never reach the
# screen. Leave it "" to use whisper's own words (then check them by eye).
SCRIPT = ""
# Edge snaps on the cut clock where whisper's word edges were loose (measured RMS dips in assets/cut.mp4).
# Shape: {word index: (new start or None, new end or None)}, e.g. {0: (None, 0.40), 1: (0.55, None)}
SNAP = {}
# The python that has mlx_whisper installed (the skill's setup script makes this venv). Override with WHISPER_PYTHON.
WHISPER_PY = os.environ.get("WHISPER_PYTHON") or sys.executable

def run(cmd, **kw):
    return subprocess.run(cmd, check=True, **kw)

def cut():
    os.makedirs("assets", exist_ok=True)   # a fresh copy of the template may not have it yet
    n = len(KEEP)
    parts = []
    for i, (a, b) in enumerate(KEEP):
        parts.append(f"[0:v]trim={a}:{b},setpts=PTS-STARTPTS[v{i}];"
                     f"[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS,afade=t=in:d=0.015,afade=t=out:st={b-a-0.015:.3f}:d=0.015[a{i}];")
    fc = ("".join(parts) + "".join(f"[v{i}][a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[v][a];"
          f"[v]setpts=PTS/{SPEED},fps=30[vo];[a]atempo={SPEED}[ao]")
    run(["ffmpeg", "-v", "error", "-y", "-i", SRC, "-filter_complex", fc, "-map", "[vo]", "-map", "[ao]",
         "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-g", "30", "-pix_fmt", "yuv420p",
         "-c:a", "pcm_s16le", "assets/cut-raw.mov"])
    # two-pass loudnorm so the voice lands on -14 LUFS integrated (the reel's loudness target)
    meas = subprocess.run(["ffmpeg", "-hide_banner", "-i", "assets/cut-raw.mov", "-af",
                           f"loudnorm=I={LUFS}:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                          capture_output=True, text=True).stderr
    i = meas.rindex("{"); m = json.loads(meas[i:meas.index("}", i) + 1])
    af = (f"loudnorm=I={LUFS}:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true,"
          "aresample=48000")
    run(["ffmpeg", "-v", "error", "-y", "-i", "assets/cut-raw.mov", "-af", af, "-c:v", "copy",
         "-c:a", "aac", "-b:a", "256k", "assets/cut.mp4"])

def words():
    code = r'''
import json, mlx_whisper
r = mlx_whisper.transcribe("assets/cut.mp4", path_or_hf_repo="mlx-community/whisper-large-v3-turbo",
                           word_timestamps=True, language="en")
print(json.dumps([{"text": w["word"].strip(), "start": w["start"], "end": w["end"]} for s in r["segments"] for w in s["words"]]))
'''
    out = subprocess.run([WHISPER_PY, "-c", code], capture_output=True, text=True, check=True).stdout
    ws = json.loads(out.strip().splitlines()[-1])
    # merge whisper's split tokens ("hyper" + "-focus") so each caption word is one real word
    merged = []
    for w in ws:
        if merged and w["text"].startswith("-"):
            merged[-1]["text"] += w["text"]; merged[-1]["end"] = w["end"]
        else:
            merged.append(dict(w))
    # ASR spelling fixes: add words your transcript mishears here (lower-case key -> how it should read on screen)
    FIX = {"ai": "AI", "ai,": "AI,", "chatgpt": "ChatGPT"}
    out = []
    for i, w in enumerate(merged):
        t = FIX.get(w["text"].lower(), w["text"])
        out.append({"id": f"w{i}", "text": t, "start": round(w["start"], 3), "end": round(max(w["end"], w["start"] + 0.08), 3)})
    script = SCRIPT.split()
    if script and len(script) != len(out):
        sys.exit(f"SCRIPT has {len(script)} words but whisper found {len(out)}: fix SCRIPT or KEEP\n" + " ".join(w["text"] for w in out))
    for w, t in zip(out, script):   # an empty SCRIPT keeps whisper's words
        w["text"] = t
    for i, (a, b) in SNAP.items():
        if a is not None: out[i]["start"] = a
        if b is not None: out[i]["end"] = b
    json.dump(out, open("assets/words-cut.json", "w"), indent=1)
    print(len(out), "words:", " ".join(f"{w['text']}@{w['start']}" for w in out))

if __name__ == "__main__":
    if "--words-only" not in sys.argv:
        cut()
    words()
