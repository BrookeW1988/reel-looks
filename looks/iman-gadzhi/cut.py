#!/usr/bin/env python3
"""Rough cut for the Iman Gadzhi-inspired reel. Reads reel.json (source, keep, speed, voice_lufs).

WHY: a take with a numbered list ("three reasons") keeps the hook claim, each reason's value sentence and the
closing line, drops the elaboration between them, trims slack sentence pauses, then speeds up 1.1x.
Cut points go in measured pauses (ffmpeg silencedetect -20 dB, d=0.06) so no word is clipped.

Inputs : reel.json, assets/words-src.json (mlx_whisper large-v3-turbo word timings of the WHOLE source take; SPEC.md
         "Using this template" has the one-line command that makes it)
Outputs: assets/cut.mp4 (voice levelled to voice_lufs), assets/words-cut.json (word times on the cut clock)
Run    : python3 cut.py
"""
import json, os, re, subprocess, sys

CFG = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "reel.json"))
# expanduser: reel.json holds "~/Movies/Edits-inbox/..." and ffmpeg doesn't expand "~" itself
SRC, KEEP, SPEED = os.path.expanduser(CFG["source"]), CFG["keep"], CFG["speed"]
os.makedirs("assets", exist_ok=True)
TARGET = CFG.get("voice_lufs", -14.0)

def run(cmd):
    return subprocess.run(cmd, check=True, capture_output=True, text=True)

# 1. trim + concat + speed. 12 ms audio fades at every seam stop clicks; -g 30 = a keyframe every second for seeking.
parts = []
for i, (a, b) in enumerate(KEEP):
    parts.append(f"[0:v]trim={a}:{b},setpts=PTS-STARTPTS[v{i}];"
                 f"[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS,afade=t=in:d=0.012,"
                 f"afade=t=out:st={b - a - 0.012:.3f}:d=0.012[a{i}];")
n = len(KEEP)
fc = "".join(parts) + "".join(f"[v{i}][a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[v][a];" \
     f"[v]setpts=PTS/{SPEED}[vo];[a]atempo={SPEED}[ao]"
run(["ffmpeg", "-v", "error", "-y", "-i", SRC, "-filter_complex", fc, "-map", "[vo]", "-map", "[ao]",
     "-c:v", "libx264", "-crf", "17", "-preset", "medium", "-g", "30", "-pix_fmt", "yuv420p",
     "-c:a", "pcm_s16le", "assets/.cut-raw.mov"])

# 2. level the voice: measure integrated loudness, apply ONE linear gain (no compression, so delivery is untouched).
m = run(["ffmpeg", "-i", "assets/.cut-raw.mov", "-af", "ebur128=peak=true", "-f", "null", "-"]).stderr
integ = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", m)[-1])
peak = float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", m)[-1])
gain = TARGET - integ
if peak + gain > -1.0:                     # never push a peak past -1 dBTP
    gain = -1.0 - peak
run(["ffmpeg", "-v", "error", "-y", "-i", "assets/.cut-raw.mov", "-c:v", "copy", "-af", f"volume={gain:.2f}dB",
     "-c:a", "aac", "-b:a", "192k", "assets/cut.mp4"])
print(f"voice: {integ:.1f} LUFS, true peak {peak:.1f} dB -> gain {gain:+.2f} dB")

# 3. remap word times from the source clock to the cut clock; words outside KEEP are dropped.
def remap_word(s, e):
    """Map a word to the cut clock via the KEEP segment it overlaps most (whisper edges are loose by ~0.1 s,
    so a strict 'start inside the segment' test drops real words). Returns None if the word was cut out."""
    acc, best = 0.0, None
    for a, b in KEEP:
        ov = min(e, b) - max(s, a)
        if ov > 0.04 and (best is None or ov > best[0]):
            best = (ov, acc + max(s, a) - a, acc + min(e, b) - a)
        acc += b - a
    if best is None:
        return None, None
    return round(best[1] / SPEED, 3), round(best[2] / SPEED, 3)

words = json.load(open("assets/words-src.json"))
SNAP = {k.lower(): v for k, v in CFG.get("snap_src", {}).items()}
DROP = {k.lower() for k in CFG.get("drop_src", [])}
kept = []
for w in words:                            # apply the measured snaps / drops on the SOURCE clock, before merging
    key = f"{w['text']}@{w['start']:g}".lower()
    if key in DROP:
        continue
    if key in SNAP:
        s, e = SNAP.pop(key)
        if s is not None: w["start"] = s
        if e is not None: w["end"] = e
    kept.append(w)
if SNAP:
    sys.exit(f"snap keys not found in words-src.json: {list(SNAP)}")
words = kept
merged = []                                # whisper splits "hyper" + "-focus": join them back into one caption word
for w in words:
    if merged and w["text"].startswith("-"):
        merged[-1]["text"] += w["text"]; merged[-1]["end"] = w["end"]
    else:
        merged.append(dict(w))
out = []
for w in merged:
    s, e = remap_word(w["start"], w["end"])
    if s is None:
        continue
    out.append({"id": f"w{len(out)}", "text": w["text"], "start": s, "end": max(e, s + 0.08)})
for i, fix in CFG.get("caption_fixes", {}).items():   # proofreading fixes (casing etc.), by cut-word index
    out[int(i)]["text"] = fix
json.dump(out, open("assets/words-cut.json", "w"), indent=1)
dur = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", "assets/cut.mp4"]).stdout
print(len(out), "words; cut length", dur.strip(), "s")
print(" ".join(f"{w['text']}@{w['start']}" for w in out))
