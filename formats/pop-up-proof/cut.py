#!/usr/bin/env python3
"""Rough cut + word timings for Pop-up proof. Reads reel.json, writes assets/cut.mp4 + assets/words-cut.json.

    $PY cut.py      # run inside this folder; the venv has mlx_whisper

WHY: takes open on dead air and have slack pauses; the style says "every pause out, 1.1-1.3x". Keep the deliberate
pauses that give a line its rhythm (on the demo, the beat between the two big words). keep spans are SOURCE seconds
picked at real pauses, never mid-word. Words are transcribed on the FINISHED cut (no remapping error) and their starts
snapped to the audio (reeltools.transcribe). The heard line is printed: proofread it, it becomes the captions.
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_shared"))
import reeltools as rt

C = json.load(open("reel.json"))
os.makedirs("assets", exist_ok=True)   # why: the template ships without media
rt.cut(os.path.expanduser(C["take"]), C["keep"], "assets/cut.mp4", speed=C.get("speed", 1.1))
words = rt.transcribe("assets/cut.mp4")
fixes = {k.lower(): v for k, v in C.get("word_fixes", {}).items()}
for w in words:   # your own spelling fixes, on top of reeltools.FIXES
    core = w["text"].rstrip(".,!?")
    if core.lower() in fixes:
        w["text"] = fixes[core.lower()] + w["text"][len(core):]
json.dump(words, open("assets/words-cut.json", "w"), indent=1)
print(len(words), "words; last ends", words[-1]["end"] if words else None)
print(" ".join(f"{w['text']}@{w['start']}" for w in words))
print("(proofread this line: it becomes the captions)")
