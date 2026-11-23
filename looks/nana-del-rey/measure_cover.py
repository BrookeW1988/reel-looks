#!/usr/bin/env python3
"""How much of each hero word does the speaker's head cover? (target 30-55%, SPEC.md "Giant words behind the head")

WHY pixels, not geometry: heads move, and estimates from letter widths were wrong both ways on earlier reels.
It snapshots each hero moment twice, with and without the cut-out, counts text-coloured pixels in the hero line's
band, and reports 1 - visible/total. Run after build.py; it rebuilds index.html normally at the end.
    python3 measure_cover.py
"""
import json, subprocess, sys
import numpy as np
from PIL import Image

C = json.load(open("reel.json"))
WORDS = json.load(open(C["words"]))
TARGETS = {"butter": (0xF8, 0xF4, 0x9C), "lilac": (0xE4, 0xC8, 0xEC), "white": (0xFC, 0xF8, 0xFC)}

def snap(times, out, debug):
    subprocess.run([sys.executable, "build.py"] + (["--debug-no-cutout"] if debug else []), check=True, capture_output=True)
    subprocess.run(["npx", "--yes", "hyperframes@0.9.83", "snapshot", "--at", ",".join(f"{t:.2f}" for t in times),
                    "--no-end", "-o", out], capture_output=True)

def text_mask(img, colours):
    a = np.asarray(img.convert("RGB")).astype(int)
    m = np.zeros(a.shape[:2], bool)
    for c in colours:
        m |= (np.abs(a - np.array(TARGETS[c])).sum(axis=2) < 30)
    return m

# hero moments: the hero line is fully on from its last word to the stack's end
import re
page = open("index.html").read()          # stack on/off times as built
def stack_end(sid):
    m = re.search(rf'id="stack-{sid}"[^>]*data-start="([\d.]+)"[^>]*data-duration="([\d.]+)"', page)
    return float(m.group(1)) + float(m.group(2))
plan = []
for st in C["stacks"]:
    hero = next(l for l in st["lines"] if l.get("hero"))
    first = hero["text"].split()[-1].lower()
    t_on = next(w["start"] for w in WORDS if w["text"].lower().strip(".,") == first and w["start"] > 0)
    colours = {st.get("hero_colour", "butter")} | ({"lilac"} if st.get("lilac") else set())
    plan.append((st["id"], [t_on + 0.12, t_on + 0.40, stack_end(st["id"]) - 0.15], st["baseline_y"], colours))
times = [t for _, ts, _, _ in plan for t in ts]
snap(times, "work/cover-with", False)
snap(times, "work/cover-without", True)
subprocess.run([sys.executable, "build.py"], check=True, capture_output=True)   # leave the real build in place

def fname(d, t):
    import glob
    return next(p for p in glob.glob(f"{d}/frame-*-at-*.png") if p.endswith(f"at-{float(f'{t:.2f}'):g}s.png"))

for sid, ts, base, colours in plan:
    for t in ts:
        band = slice(base - 200, base + 60)                       # hero glyphs (incl. descenders) sit in baseline-200 .. baseline+60
        a = text_mask(Image.open(fname("work/cover-with", t)), colours)[band].sum()
        b = text_mask(Image.open(fname("work/cover-without", t)), colours)[band].sum()
        msg = f"{sid:10} t={t:5.2f} baseline={base}: hero line covered {100 * (1 - a / max(b, 1)):4.0f}%"
        if "lilac" in colours:   # the payoff word on its own: it must stay readable
            la = text_mask(Image.open(fname("work/cover-with", t)), {"lilac"})[band].sum()
            lb = text_mask(Image.open(fname("work/cover-without", t)), {"lilac"})[band].sum()
            msg += f" | lilac word covered {100 * (1 - la / max(lb, 1)):4.0f}%"
        print(msg)
