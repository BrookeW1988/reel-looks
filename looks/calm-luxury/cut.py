#!/usr/bin/env python3
"""Rough cut for the Calm luxury look (see SPEC.md for why every number is what it is).

WHY these choices:
- Calm comes from stillness, not slow cutting: so NO speed-up (1.0x; the demo speaker's natural ~170 words a minute
  matches Jess's measured 162-172) and NO jump cuts inside a sentence. In the demo the first range is one unbroken
  13.6 s "process hold"; then ONE hard cut to the closing line.
- Cut points sit inside measured silences (RMS envelope, 40 ms windows) and are frame-aligned to 30 fps, so no word
  is clipped and the voice starts on frame 1.
- REFRAME is a static crop for the whole reel (never animated, so it is not a zoom): scale 1.12 anchored to the
  bottom edge lifted the demo chin from y~1400 to y~1338 and put a dark top, not neck, under the caption line.

Usage:  python3 cut.py            (needs ffmpeg; writes assets/cut.mp4 + assets/words-cut.json + assets/cut-points.json)
Member version: change SRC, KEEP and REFRAME; WORDS is word-level JSON on the SOURCE clock
([{"text","start","end"}]). Make it first with the skill's venv:
    $PY -c 'import json,sys,mlx_whisper; r=mlx_whisper.transcribe(sys.argv[1], path_or_hf_repo="mlx-community/whisper-large-v3-turbo", word_timestamps=True); json.dump([{"text": w["word"].strip(), "start": round(w["start"], 3), "end": round(w["end"], 3)} for s in r["segments"] for w in s["words"] if w["word"].strip()], open(sys.argv[2], "w"), indent=1)' ~/Movies/Edits-inbox/your-take.mov assets/words-source.json
"""
import json, os, subprocess

SRC = os.path.expanduser("~/Movies/Edits-inbox/your-take.mov")   # your SDR take, filmed locked off
WORDS = "assets/words-source.json"
FPS = 30
# Source seconds (frame-aligned). Example values from the demo: A = one long hold, B = the closing line.
KEEP = [(626 / FPS, 1034 / FPS), (1530 / FPS, 1654 / FPS)]
REFRAME = 1.12           # 1.0 = no crop. Static, bottom-anchored, centred horizontally.
EDGE_FADE = 0.012        # 12 ms audio fades at each edit, so the cuts don't click

os.makedirs("assets", exist_ok=True)
parts = []
for i, (a, b) in enumerate(KEEP):
    parts.append(f"[0:v]trim={a:.4f}:{b:.4f},setpts=PTS-STARTPTS[v{i}];"
                 f"[0:a]atrim={a:.4f}:{b:.4f},asetpts=PTS-STARTPTS,afade=t=in:d={EDGE_FADE},"
                 f"afade=t=out:st={b - a - EDGE_FADE:.4f}:d={EDGE_FADE}[a{i}];")
n = len(KEEP)
cw, ch = round(1080 / REFRAME / 2) * 2, round(1920 / REFRAME / 2) * 2
fc = ("".join(parts) + "".join(f"[v{i}][a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[vc][a];"
      f"[vc]crop={cw}:{ch}:{(1080 - cw) // 2}:{1920 - ch},scale=1080:1920:flags=lanczos,setsar=1[v]")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", SRC, "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
                "-r", str(FPS), "-c:v", "libx264", "-crf", "16", "-preset", "slow", "-g", "30", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "192k", "assets/cut.mp4"], check=True)


def remap(t):
    """Source clock -> cut clock. Returns None for words outside the kept ranges."""
    acc = 0.0
    for a, b in KEEP:
        if a - 0.05 <= t <= b + 0.05:
            return round(acc + min(max(t, a), b) - a, 3)
        acc += b - a
    return None


out = []
for w in json.load(open(WORDS)):
    s, e = remap(w["start"]), remap(w["end"])
    if s is None or e is None:
        continue
    out.append({"id": f"w{len(out)}", "text": w["text"], "start": s, "end": max(e, s + 0.08)})
json.dump(out, open("assets/words-cut.json", "w"), indent=1)
# hard cuts inside cut.mp4 (cut clock), so build.py can swap a caption ON the cut rather than just before it
edges, acc = [], 0.0
for a, b in KEEP[:-1]:
    acc += b - a
    edges.append(round(acc, 4))
json.dump(edges, open("assets/cut-points.json", "w"))
total = sum(b - a for a, b in KEEP)
print(f"cut {total:.3f} s, hard cuts at {edges}, {len(out)} words, last ends {out[-1]['end']}")
print(" ".join(f"{w['text']}@{w['start']}" for w in out))
