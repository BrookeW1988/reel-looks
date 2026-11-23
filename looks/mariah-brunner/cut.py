#!/usr/bin/env python3
"""Rough cut for the "inspired by Mariah Brunner" demo reel.

WHY this exists: the look is "her talking, tight but never breathless". So the cut keeps whole sentences, drops the
off-topic middle, speeds the take up a touch and levels the voice to -14 LUFS BEFORE any graphics are built, so every
graphic is timed to the final clock.

CLAUDE CHANGES PER TAKE: --src (the member's take) and --keep (her source-second ranges). The defaults are EXAMPLE
values that show the shape; they don't fit any real take.

Usage:
    python3 cut.py --src ~/Movies/Edits-inbox/your-take.mov --keep 3.2-18.9,22.0-30.5 --transcribe
                                                      # --transcribe (re)makes assets/words-src.json with mlx_whisper
                                                      # first, using the skill's venv (or $WHISPER_PYTHON)
    python3 cut.py --src ... --keep ...               # cut + level + remap word times (words-src.json already made)

Outputs: assets/cut.mp4 (1080x1920 30 fps, voice at -14 LUFS) and assets/words-cut.json (word times on the cut clock).
"""
import argparse, json, os, re, subprocess, sys

# The Python running this file does the transcribing (each skill runs templates with its own Python). Override with WHISPER_PYTHON.
WHISPER_PY = os.environ.get("WHISPER_PYTHON") or sys.executable

ap = argparse.ArgumentParser()
ap.add_argument("--src", default="~/Movies/Edits-inbox/your-take.mov")
# Source seconds to keep. Each edge sits in measured near-silence (RMS < -45 dB, see SPEC.md "Rough cut").
ap.add_argument("--keep", default="20.86-40.42,50.76-55.12", help="example values")
ap.add_argument("--speed", type=float, default=1.1)
ap.add_argument("--lufs", type=float, default=-14.0)
ap.add_argument("--words", default="assets/words-src.json", help="word times on the SOURCE clock")
ap.add_argument("--transcribe", action="store_true", help="re-time words with mlx_whisper large-v3-turbo first")
a = ap.parse_args()
a.src = os.path.expanduser(a.src)          # ffmpeg doesn't expand "~" itself
os.makedirs("work", exist_ok=True); os.makedirs("assets", exist_ok=True)
KEEP = [tuple(float(x) for x in r.split("-")) for r in a.keep.split(",")]

if a.transcribe:
    # whisper.cpp drifted up to ~1 s on the demo take; mlx large-v3-turbo with word_timestamps was within ~50 ms.
    lo, hi = KEEP[0][0] - 0.5, KEEP[-1][1] + 0.5
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(lo), "-i", a.src, "-t", str(hi - lo), "-vn", "-ac", "1",
                    "-ar", "16000", "work/seg.wav"], check=True)
    py = f"""
import mlx_whisper, json
r = mlx_whisper.transcribe('work/seg.wav', path_or_hf_repo='mlx-community/whisper-large-v3-turbo', word_timestamps=True, language='en')
ws = [dict(text=w['word'].strip(), start=round(w['start']+{lo},3), end=round(w['end']+{lo},3)) for s in r['segments'] for w in s['words']]
json.dump(ws, open('{a.words}', 'w'), indent=1)
"""
    subprocess.run([WHISPER_PY, "-c", py], check=True)

# ---- 1. cut + speed. 12 ms audio fades on every edge so no edit clicks. ----
parts, n = [], len(KEEP)
for i, (s, e) in enumerate(KEEP):
    parts.append(f"[0:v]trim={s}:{e},setpts=PTS-STARTPTS[v{i}];"
                 f"[0:a]atrim={s}:{e},asetpts=PTS-STARTPTS,afade=t=in:d=0.012,afade=t=out:st={e - s - 0.012:.3f}:d=0.012[a{i}];")
fc = "".join(parts) + "".join(f"[v{i}][a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[v][a];" \
     f"[v]setpts=PTS/{a.speed},fps=30[vo];[a]atempo={a.speed}[ao]"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a.src, "-filter_complex", fc, "-map", "[vo]", "-map", "[ao]",
                "-c:v", "libx264", "-crf", "17", "-preset", "medium", "-g", "30", "-pix_fmt", "yuv420p",
                "-c:a", "pcm_s16le", "work/cut-raw.mov"], check=True)

# ---- 2. level the voice: two-pass loudnorm to -14 LUFS, true peak -1.5 dBTP ----
m = subprocess.run(["ffmpeg", "-hide_banner", "-i", "work/cut-raw.mov", "-af",
                    f"loudnorm=I={a.lufs}:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                   capture_output=True, text=True).stderr
j = json.loads(re.findall(r"\{[^{}]+\}", m)[-1])
ln = (f"loudnorm=I={a.lufs}:TP=-1.5:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:"
      f"measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "work/cut-raw.mov", "-c:v", "copy", "-af", ln + ",aresample=48000",
                "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "assets/cut.mp4"], check=True)

# ---- 3. remap word times from the source clock to the cut clock ----
def remap(t):
    acc = 0.0
    for s, e in KEEP:
        if s - 0.05 <= t <= e + 0.05:
            return round((acc + min(max(t, s), e) - s) / a.speed, 3)
        acc += e - s
    return None

out = []
for w in json.load(open(a.words)):
    # keep a word when its MIDDLE is inside a keep range (whisper starts can sit ~0.1-0.2 s early), clamping its edges
    mid = (w["start"] + w["end"]) / 2
    rng = next(((s0, e0) for s0, e0 in KEEP if s0 <= mid <= e0), None)
    if rng is None:
        continue
    s, e = remap(max(w["start"], rng[0])), remap(min(w["end"], rng[1]))
    if s is None or e is None:
        continue
    out.append({"id": f"w{len(out)}", "text": w["text"], "start": s, "end": max(e, s + 0.08)})
json.dump(out, open("assets/words-cut.json", "w"), indent=1)
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                            "assets/cut.mp4"], capture_output=True, text=True).stdout)
print(f"cut.mp4 {dur:.3f} s, input loudness {j['input_i']} LUFS -> {a.lufs}; {len(out)} words")
print(" ".join(f"{i}:{w['text']}@{w['start']}" for i, w in enumerate(out)))
