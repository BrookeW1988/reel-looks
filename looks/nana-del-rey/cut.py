#!/usr/bin/env python3
"""Rough cut for the "inspired by Nana DelRey" look (see SPEC.md).

WHY these cuts: her look holds shots 4-5 s and cuts only at sentence ends, at normal speed. So the demo is one
continuous 13.6 s run plus ONE plain jump cut at a sentence end, no speed-up, no punch-in.
Cut points sit in measured silence (20 ms RMS envelope, see SPEC.md "Cut"), not on whisper's word edges,
which can run ~0.2 s early at segment starts.

    python3 cut.py            -> assets/cut.mp4 + assets/words-cut.json
Needs ffmpeg and work/words-source.json (mlx_whisper large-v3-turbo word timings for the whole take, source clock,
a list of {"text", "start", "end"}). Make it with the skill's venv:
    $PY -c 'import json,sys,mlx_whisper; r=mlx_whisper.transcribe(sys.argv[1], path_or_hf_repo="mlx-community/whisper-large-v3-turbo", word_timestamps=True); json.dump([{"text": w["word"].strip(), "start": round(w["start"], 3), "end": round(w["end"], 3)} for s in r["segments"] for w in s["words"] if w["word"].strip()], open(sys.argv[2], "w"), indent=1)' ~/Movies/Edits-inbox/your-take.mov work/words-source.json
"""
import json, os, re, subprocess

SRC = os.path.expanduser("~/Movies/Edits-inbox/your-take.mov")   # your SDR take (convert iPhone HDR first)
# Example values from the demo take: replace with your own kept ranges (source seconds).
KEEP = [(20.84, 34.46), (50.76, 55.70)]          # source seconds
# whisper start -> measured onset, for words whisper starts early, e.g. {20.68: 20.92}. Example: empty.
ONSET_FIX = {}
VOICE_LUFS, VOICE_TP = -14.2, -1.5               # voice target; the bed 14 dB under adds ~+0.2 dB -> ~-14.0 total

def run(args):
    return subprocess.run(args, check=True, capture_output=True, text=True)

os.makedirs("work", exist_ok=True); os.makedirs("assets", exist_ok=True)   # neither ships with the template

# ---- 1. picture + sound cut (12 ms audio fades at each edit so there is no click) ----
parts = []
for i, (a, b) in enumerate(KEEP):
    parts.append(f"[0:v]trim={a}:{b},setpts=PTS-STARTPTS[v{i}];"
                 f"[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS,afade=t=in:d=0.012,afade=t=out:st={b-a-0.012:.3f}:d=0.012[a{i}];")
n = len(KEEP)
fc = "".join(parts) + "".join(f"[v{i}][a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[v][a]"
run(["ffmpeg", "-v", "error", "-y", "-i", SRC, "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
     "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-g", "30", "-pix_fmt", "yuv420p",
     "-c:a", "pcm_s16le", "work/cut-raw.mov"])

# ---- 2. voice to -14.2 LUFS, two-pass linear loudnorm (measure, then apply exactly) ----
m = run(["ffmpeg", "-hide_banner", "-i", "work/cut-raw.mov", "-af",
         f"loudnorm=I={VOICE_LUFS}:TP={VOICE_TP}:LRA=11:print_format=json", "-f", "null", "-"]).stderr
j = json.loads(re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", m, re.S).group(0))
af = (f"loudnorm=I={VOICE_LUFS}:TP={VOICE_TP}:LRA=11:linear=true:measured_I={j['input_i']}:"
      f"measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:"
      f"offset={j['target_offset']},aresample=48000")
run(["ffmpeg", "-v", "error", "-y", "-i", "work/cut-raw.mov", "-af", af, "-c:v", "copy",
     "-c:a", "aac", "-b:a", "256k", "assets/cut.mp4"])

# ---- 3. word times, source clock -> cut clock ----
def remap(t):
    acc = 0.0
    for a, b in KEEP:
        if a - 0.05 <= t <= b + 0.05:
            return round(acc + min(max(t, a), b) - a, 3)
        acc += b - a
    return None

words = json.load(open("work/words-source.json"))
out = []
for w in words:
    s = ONSET_FIX.get(w["start"], w["start"])
    if not any(a - 0.05 <= s <= b for a, b in KEEP):
        continue
    cs, ce = remap(s), remap(w["end"])
    # whisper splits "hyper-focus" style words: keep them joined
    if w["text"].startswith("-") and out:
        out[-1]["text"] += w["text"]; out[-1]["end"] = ce; continue
    out.append({"id": f"w{len(out)}", "text": w["text"], "start": cs, "end": max(ce, cs + 0.08)})
json.dump(out, open("assets/words-cut.json", "w"), indent=1)
dur = float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", "assets/cut.mp4"]).stdout)
print(f"{len(out)} words, cut {dur:.3f} s, last word ends {out[-1]['end']}")
print(" ".join(f"{w['text']}@{w['start']}" for w in out))
