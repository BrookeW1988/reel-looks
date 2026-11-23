#!/usr/bin/env python3
"""Rough cut for the Diary-of-a-CEO-inspired podcast clip (see SPEC.md "Rough cut").

WHY: DOAC clips start on a loaded line at 0.00 s and cut every pause tight (148-206 wpm). This picks a
self-contained stretch of the take, drops list signposts ("number two...": a clip isn't a list), trims the slack
pauses and speeds the result 1.1x. Every KEEP edge should sit on a measured speech onset/offset (a 10 ms loudness
envelope), not on whisper's loose word edges.

Outputs (all in assets/):
  cut.mp4         the speaking take, cut and sped up (picture + sound)
  react.mp4       the silent "listening" shot for the top half of the split hook (muted)
  words-cut.json  every kept word on the cut clock: [{"id","text","start","end","speaker"}]

Needs assets/words-src.json first (mlx_whisper word timings of the whole take; SPEC.md "Using this template" has the
one-line command). Then:  python3 cut.py
"""
import json, os, subprocess, sys

# ================ CLAUDE CHANGES PER TAKE (the values below are EXAMPLES that show the shape) ================
SRC = os.path.expanduser("~/Movies/Edits-inbox/your-take.mov")   # expanduser: ffmpeg doesn't expand "~"
WORDS_SRC = "assets/words-src.json"          # mlx_whisper large-v3-turbo word timings (see SPEC.md)
SPEAKER = "guest"                            # one speaker here; a two-person recording tags words "host"/"guest"
KEEP = [  # source seconds; every join gets a camera-crop change so the jump cut reads as an angle change
    (20.91, 27.24),   # a self-contained opening line
    (27.62, 34.28),
    (34.50, 40.24),
    (42.73, 50.47),   # (a list signpost between these two ranges was dropped)
    (50.83, 55.06),   # the last line (end before a blink)
]
# Pauses of ~0.1 s are KEPT: trimming them makes 0.1 s jump cuts that one camera can't hide without a sub-1.5 s
# crop change.
SPEED = 1.1
REACT = (0.05, 2.05, 0.9)   # source in, out, speed: a closed-mouth listening look (e.g. before the speaker starts)
# ================ end of the per-take block ================
os.makedirs("assets", exist_ok=True)

def run(args):
    subprocess.run(["ffmpeg", "-v", "error", "-y"] + args, check=True)

ENC = ["-c:v", "libx264", "-crf", "17", "-preset", "medium", "-g", "30", "-pix_fmt", "yuv420p"]

# 1. the speaking cut: 12 ms audio fades on every join so no edit clicks
parts = []
for i, (a, b) in enumerate(KEEP):
    parts.append(f"[0:v]trim={a}:{b},setpts=PTS-STARTPTS[v{i}];"
                 f"[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS,afade=t=in:d=0.012,afade=t=out:st={b - a - 0.012:.3f}:d=0.012[a{i}];")
n = len(KEEP)
fc = "".join(parts) + "".join(f"[v{i}][a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[v][a];" \
     f"[v]setpts=PTS/{SPEED}[vo];[a]atempo={SPEED}[ao]"
run(["-i", SRC, "-filter_complex", fc, "-map", "[vo]", "-map", "[ao]", *ENC, "-c:a", "aac", "-b:a", "192k", "assets/cut.mp4"])

# 2. the listening shot (no audio)
a, b, sp = REACT
run(["-ss", str(a), "-t", str(b - a), "-i", SRC, "-an", "-vf", f"setpts=PTS/{sp}", *ENC, "assets/react.mp4"])

# 3. word times: source clock -> cut clock (words outside KEEP are dropped)
def remap(s, e):
    """Map a source word [s, e] into the KEEP range it overlaps most (whisper edges are loose, so a word that
    starts inside a trimmed pause is clamped, not dropped). Words with < 60 ms inside any KEEP are cut words."""
    acc, best = 0.0, None
    for a, b in KEEP:
        ov = min(e, b) - max(s, a)
        if ov > 0.06 and (best is None or ov > best[0]):
            best = (ov, acc, a, b)
        acc += b - a
    if best is None:
        return None, None
    _, acc, a, b = best
    f = lambda t: round((acc + min(max(t, a), b) - a) / SPEED, 3)
    return f(s), f(e)

words = json.load(open(WORDS_SRC))
out = []
for w in words:
    s, e = remap(w["start"], w["end"])
    if s is None:
        continue
    out.append({"id": f"w{len(out)}", "text": w["text"], "start": s, "end": max(e, s + 0.08),
                "speaker": w.get("speaker", SPEAKER)})
# DOAC rule: the first word starts at 0.00 s (whisper often starts it inside the cut-off breath before the first KEEP)
out[0]["start"] = 0.0
json.dump(out, open("assets/words-cut.json", "w"), indent=1)

total = sum(b - a for a, b in KEEP) / SPEED
joins, acc = [], 0.0
for a, b in KEEP[:-1]:
    acc += b - a
    joins.append(round(acc / SPEED, 3))
print(f"{len(out)} words, cut length {total:.3f} s, joins at {joins}")
print(" ".join(f"{i}:{w['text']}@{w['start']}" for i, w in enumerate(out)))
