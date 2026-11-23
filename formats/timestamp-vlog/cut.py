#!/usr/bin/env python3
"""Clip prep for Timestamp vlog. WHY: the style is 1-3 s clips (final one 3-4 s), no voiceover, so each clip is cut
to its window, made 1080x1920 30 fps with a keyframe every second (so seeking never freezes), and its sound dropped
(the member adds an upbeat track in Edits). Also prints each source's RECORDED time, which is what the chips show.
    $PY cut.py
"""
import json, os, subprocess, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_shared"))
import reeltools as rt

C = json.load(open("config.json"))
for i, c in enumerate(C["clips"]):
    src = os.path.expanduser(c["src"])          # config paths may start with ~
    rt.cut(src, [[c["media_start"], c["media_start"] + c["dur"] + 0.25]], f"assets/clip{i + 1}.mp4", audio=False)
    rec = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format_tags=com.apple.quicktime.creationdate",
                          "-of", "csv=p=0", src], capture_output=True, text=True).stdout.strip()
    print(f"clip{i + 1}: recorded {rec or 'UNKNOWN (no metadata: ask the member, never guess)'} -> chip '{c['when']} · {c['label']}'")
