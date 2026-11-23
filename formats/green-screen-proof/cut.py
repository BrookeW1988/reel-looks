#!/usr/bin/env python3
"""Rough cut for Green-screen proof. WHY: the style runs 1.1-1.3x with pauses out; keep one argument from the take,
minus any list signpost ("Number three is ...") that makes no sense once the reel starts mid-list.
Output: assets/cut.mp4 + assets/words-cut.json (accurate word times) + assets/voice.wav.
    $PY cut.py
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_shared"))
import reeltools as rt

C = json.load(open("config.json"))
os.makedirs("assets", exist_ok=True)   # a fresh copy of the template may not have it yet
rt.cut(os.path.expanduser(C["take"]), C["keep"], "assets/cut.mp4", speed=C["speed"])
words = rt.transcribe("assets/cut.mp4")
json.dump(words, open("assets/words-cut.json", "w"), indent=1)
print(len(words), "words; cut", rt.duration("assets/cut.mp4"), "s")
print(" ".join(f"{w['text']}@{w['start']}" for w in words))

# The picture behind her is a web page, not this footage, so the voice plays from its own file.
rt.run(["ffmpeg", "-v", "error", "-y", "-i", "assets/cut.mp4", "-vn", "-c:a", "pcm_s16le", "-ar", "48000", "assets/voice.wav"])
