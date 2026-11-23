#!/usr/bin/env python3
"""Rough cut for the Nick Saraev-inspired look (see SPEC.md "Source and cut").

WHY: a take is usually longer than the reel. Keep the 15-30 s explanatory stretch that stands alone (drop list
openers like "Number two,"), joined on a sentence end. Cut points sit in measured envelope dips (20 ms RMS),
never inside a phoneme.

Inputs  SRC (your SDR take, e.g. ~/Movies/Edits-inbox/your-take.mov)
        assets/words-src.json = mlx_whisper large-v3-turbo word times on SRC's clock, a list of
        {"text", "start", "end"}. Make it with the skill's venv:
          $PY -c 'import json,sys,mlx_whisper; r=mlx_whisper.transcribe(sys.argv[1], path_or_hf_repo="mlx-community/whisper-large-v3-turbo", word_timestamps=True); json.dump([{"text": w["word"].strip(), "start": round(w["start"], 3), "end": round(w["end"], 3)} for s in r["segments"] for w in s["words"] if w["word"].strip()], open(sys.argv[2], "w"), indent=1)' ~/Movies/Edits-inbox/your-take.mov assets/words-src.json
Outputs assets/cut.mp4, assets/words-cut.json (word times on the cut clock)

Run: python3 cut.py          (needs ffmpeg; --words-only redoes just the word times)
"""
import json, os, subprocess, sys

SRC = os.path.expanduser("~/Movies/Edits-inbox/your-take.mov")   # your take (SDR: convert iPhone HDR first)
SRC_OFFSET = 0.0                       # only if SRC is an extract of a longer file: where it starts in that file
# Example values from the demo take: replace with your own kept ranges (seconds on SRC's clock).
KEEP = [(1.88, 15.48),                 # first stretch, ends on a sentence end
        (23.69, 36.12)]                # second stretch, after the part you drop
SPEED = 1.1                            # a light lift that keeps the speaker's natural cadence
FADE = 0.015                           # 15 ms equal-power (qsin) fade either side of each join

parts, n = [], len(KEEP)
for i, (a, b) in enumerate(KEEP):
    parts.append(f"[0:v]trim={a}:{b},setpts=PTS-STARTPTS[v{i}];"
                 f"[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS,afade=t=in:d={FADE}:curve=qsin,"
                 f"afade=t=out:st={b - a - FADE:.3f}:d={FADE}:curve=qsin[a{i}];")
fc = "".join(parts) + "".join(f"[v{i}][a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[v][a];" \
     f"[v]setpts=PTS/{SPEED}[vo];[a]atempo={SPEED}[ao]"
if "--words-only" not in sys.argv:
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", SRC, "-filter_complex", fc, "-map", "[vo]", "-map", "[ao]",
                    "-r", "30", "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-g", "30", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "256k", "assets/cut-raw.mp4"], check=True)
    # voice to -14 LUFS / -1.5 dBTP (two-pass loudnorm, linear) so the effects can be set relative to it
    m = subprocess.run(["ffmpeg", "-hide_banner", "-i", "assets/cut-raw.mp4", "-af",
                        "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    j = json.loads(m[m.rindex("{"):m.rindex("}") + 1])
    ln = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:"
          f"measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "assets/cut-raw.mp4", "-c:v", "copy", "-af", ln, "-ar", "48000",
                    "-c:a", "aac", "-b:a", "256k", "assets/cut.mp4"], check=True)
    print("voice was", j["input_i"], "LUFS -> -14")

# ---- word times: source clip clock -> cut clock ----
def remap(t):
    acc = 0.0
    for a, b in KEEP:
        if a - 0.05 <= t <= b + 0.05:
            return round((acc + min(max(t, a), b) - a) / SPEED, 3)
        acc += b - a
    return None

words = json.load(open("assets/words-src.json"))
# whisper splits "hyper-focus" into "hyper" + "-focus": join them back into one caption word
merged = []
for w in words:
    if w["text"].startswith("-") and merged:
        merged[-1] = {"text": merged[-1]["text"] + w["text"], "start": merged[-1]["start"], "end": w["end"]}
    else:
        merged.append(dict(w))
# snap word edges to the measured envelope where whisper was loose (src clip clock).
# Shape: {"word@whisper_start": (new_start or None, new_end or None)}, e.g. {"we@1.7": (1.92, None)}. Example: empty.
SNAP = {}
for w in merged:
    k = f"{w['text']}@{w['start']}"
    if k in SNAP:
        s, e = SNAP[k]
        if s is not None: w["start"] = s
        if e is not None: w["end"] = e
# re-case a word that now opens a sentence because the words before it were cut, e.g. {"we@1.92": "We"}
CAPS = {}
for w in merged:
    w["text"] = CAPS.get(f"{w['text']}@{w['start']}", w["text"])
out = []
for w in merged:
    s, e = remap(w["start"]), remap(w["end"])
    if s is None or e is None:
        continue
    out.append({"id": f"w{len(out)}", "text": w["text"], "start": s, "end": max(e, s + 0.08)})
json.dump(out, open("assets/words-cut.json", "w"), indent=1)
print(len(out), "words; last ends", out[-1]["end"])
print(" ".join(f"{i}:{w['text']}@{w['start']}" for i, w in enumerate(out)))
