#!/usr/bin/env python3
"""Word timings for cut.py: mlx_whisper large-v3-turbo with word_timestamps, in SOURCE seconds.

Run with the skill's venv python (it has mlx_whisper; the system python doesn't):
    $PY transcribe.py [--from 19] [--to 57.6]
Reads config.json "footage", writes config.json "whisper_words" (assets/whisper-words.json).
WHY: whisper.cpp drifts up to ~1 s on this kind of take; mlx large-v3-turbo is close, and cut.py then snaps
each word's start to the real onset in the audio.
"""
import argparse, json, os, subprocess, tempfile
import mlx_whisper

os.chdir(os.path.dirname(os.path.abspath(__file__)))
ap = argparse.ArgumentParser()
ap.add_argument("--from", dest="t0", type=float, default=0.0)
ap.add_argument("--to", dest="t1", type=float, default=None)
A = ap.parse_args()
C = json.load(open("config.json"))
wav = os.path.join(tempfile.mkdtemp(), "speech.wav")
os.makedirs("assets", exist_ok=True)
# expanduser: the config holds "~/Movies/Edits-inbox/..." and ffmpeg doesn't expand "~" itself
cmd = ["ffmpeg", "-v", "error", "-y", "-ss", str(A.t0), "-i", os.path.expanduser(C["footage"])]
if A.t1:
    cmd += ["-t", str(A.t1 - A.t0)]
subprocess.run(cmd + ["-vn", "-ac", "1", "-ar", "16000", wav], check=True)
r = mlx_whisper.transcribe(wav, path_or_hf_repo="mlx-community/whisper-large-v3-turbo",
                           word_timestamps=True, language="en")
words = [{"text": w["word"].strip(), "start": round(w["start"] + A.t0, 3), "end": round(w["end"] + A.t0, 3)}
         for s in r["segments"] for w in s["words"]]
json.dump(words, open(C["whisper_words"], "w"), indent=1)
print(" ".join(f"{w['text']}@{w['start']}" for w in words))
