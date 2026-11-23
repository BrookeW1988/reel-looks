#!/usr/bin/env python3
"""Clip prep for Yes... but split. WHY: both halves play together for the whole reel, so both clips are cut to the
same length (in the demo the YES clip is slowed to 0.7x so its 3.95 s stretch matches the BUT clip's 5.64 s; slightly
dreamy suits "the dream"). Sound is dropped: the style is text labels + trending audio the member adds in Edits.
    $PY cut.py
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_shared"))
import reeltools as rt

C = json.load(open("config.json"))
for side in ("yes", "but"):
    c = C[side]
    rt.cut(os.path.expanduser(c["src"]),   # config paths may start with ~
            [c["keep"]], f"assets/{side}.mp4", speed=c["speed"], audio=False)
    print(side, rt.duration(f"assets/{side}.mp4"), "s")
