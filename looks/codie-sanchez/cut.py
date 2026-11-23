#!/usr/bin/env python3
"""Rough cut for the "Inspired by Codie Sanchez" look (see SPEC.md).

WHY: Codie's studio reels have no dead air and no speed-up (1.0x), and they end on a payoff line. Keep one clean
run of the take and jump straight to the payoff line. The join is hidden by a framing change (hard cut A -> B),
exactly how Codie hides her own jump cuts.

CLAUDE CHANGES PER TAKE: --src (the member's take) and --keep (her source-second ranges). The defaults below are
EXAMPLE values that show the shape; they don't fit any real take.

Usage (a member's take):
    python3 cut.py --src ~/Movies/Edits-inbox/your-take.mov --words assets/words-src.json --keep 20.90-34.46 50.82-55.10
words.json = [{"text","start","end"}] on the SOURCE clock (mlx_whisper word_timestamps; SPEC.md "Using this
template" has the one-line command that makes it).
Writes assets/cut.mp4 (voice levelled to -14.2 LUFS) and assets/words-cut.json (word times on the cut clock).
"""
import argparse, json, os, re, subprocess

ap = argparse.ArgumentParser()
ap.add_argument("--src", default="~/Movies/Edits-inbox/your-take.mov")
ap.add_argument("--words", default="assets/words-src.json")
ap.add_argument("--keep", nargs="+", default=["20.90-34.46", "50.82-55.10"], help="source ranges a-b, in order (example values)")
ap.add_argument("--lufs", type=float, default=-14.2, help="voice target; the bed adds ~0.1-0.2 LU on top")
ap.add_argument("--out", default="assets/cut.mp4")
a = ap.parse_args()
a.src = os.path.expanduser(a.src)          # ffmpeg doesn't expand "~" itself
os.makedirs("assets", exist_ok=True)
KEEP = [tuple(float(x) for x in r.split("-")) for r in a.keep]

# ---- 1. cut: hard joins, 12 ms audio fades at every seam so a join never clicks ----
parts = []
for i, (s, e) in enumerate(KEEP):
    parts.append(f"[0:v]trim={s}:{e},setpts=PTS-STARTPTS[v{i}];"
                 f"[0:a]atrim={s}:{e},asetpts=PTS-STARTPTS,afade=t=in:d=0.012,afade=t=out:st={e - s - 0.012:.3f}:d=0.012[a{i}];")
n = len(KEEP)
fc = "".join(parts) + "".join(f"[v{i}][a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[v][a]"

# ---- 2. measure loudness of the joined voice (pass 1), then level it (pass 2) ----
m = subprocess.run(["ffmpeg", "-v", "info", "-i", a.src, "-filter_complex", fc + f";[v]nullsink;[a]loudnorm=I={a.lufs}:TP=-1.5:LRA=11:print_format=json[ao]",
                    "-map", "[ao]", "-f", "null", "-"], capture_output=True, text=True).stderr
j = json.loads(re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", m).group(0))
ln = (f"loudnorm=I={a.lufs}:TP=-1.5:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:"
      f"measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a.src, "-filter_complex", fc + f";[a]{ln},aresample=48000[ao]",
                "-map", "[v]", "-map", "[ao]", "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-g", "30",
                "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k", a.out], check=True)
print("voice in:", j["input_i"], "LUFS -> target", a.lufs)

# ---- 3. remap word times from the source clock to the cut clock (words outside the ranges are dropped) ----
def remap(t):
    acc = 0.0
    for s, e in KEEP:
        if s - 0.05 <= t <= e + 0.05:
            return round(acc + min(max(t, s), e) - s, 3)
        acc += e - s
    return None

out = []
for w in json.load(open(a.words)):
    s, e = remap(w["start"]), remap(w["end"])
    if s is None or e is None:
        continue
    out.append({"id": f"w{len(out)}", "text": w["text"], "start": s, "end": max(e, s + 0.08)})
json.dump(out, open("assets/words-cut.json", "w"), indent=1)
dur = sum(e - s for s, e in KEEP)
print(len(out), "words; cut length", round(dur, 3), "s")
print(" ".join(f"{w['text']}@{w['start']}" for w in out))
