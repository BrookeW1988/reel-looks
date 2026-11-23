#!/usr/bin/env python3
"""Rough cut for POV micro-skit. WHY: the style is setup -> reaction, cut on the reaction, nothing after. The demo
take opened on 0.5 s of nothing and ended with a reach for the phone at 5.0 s; the 0.55 s tight-lipped "did I nail
it?" smile (4.45-5.0 s) was the reaction, played at half speed so it lands. Output: assets/cut.mp4 +
assets/words-cut.json + assets/beats.json. Run inside this folder:
    $PY cut.py
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_shared"))
import reeltools as rt

C = json.load(open("config.json"))
os.makedirs("assets", exist_ok=True)   # why: the template ships without media
rt.cut(os.path.expanduser(C["take"]), C["keep"], "assets/cut.mp4")
words = rt.transcribe("assets/cut.mp4")
json.dump(words, open("assets/words-cut.json", "w"), indent=1)
# where the reaction starts on the cut clock = the length of every keep range before the last one
react = sum((k[1] - k[0]) / (k[2] if len(k) > 2 else 1) for k in C["keep"][:-1])
json.dump({"reaction_start": round(react, 3), "duration": rt.duration("assets/cut.mp4")}, open("assets/beats.json", "w"))
print(len(words), "words; reaction at", round(react, 3), "cut", rt.duration("assets/cut.mp4"))
print(" ".join(f"{w['text']}@{w['start']}-{w['end']}" for w in words))
