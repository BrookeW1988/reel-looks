#!/usr/bin/env python3
"""Measures every sound effect against your voice, from the composition itself (no listening needed).

    $PY measure.py                     # before render: rebuilds each effect from index.html's <audio> tags
    $PY measure.py renders/<slug>.mp4  # after render: also integrated loudness + true peak of the finished file

For each effect: its loudest momentary loudness (EBU R128 M, 400 ms window) on its own, against the voice's
momentary loudness over the same window (the speech under it), and against the voice's integrated loudness.
Target (SPEC.md): effects sit 6-10 dB under the voice. Picture-to-peak alignment is set in build.py (peak + 1 frame).
"""
import html, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
A = lambda p: os.path.join(HERE, p)
CUT = json.load(open(A("assets/words-cut.json")))
DUR = CUT["duration"]
page = open(A("index.html")).read()


def momentary(args):
    """List of (t, M LUFS) every 100 ms for the audio made by these ffmpeg input args/filter."""
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats"] + args + ["-f", "null", "-"], capture_output=True, text=True)
    return [(float(t), float(m)) for t, m in re.findall(r"t:\s*([\d.]+)\s+TARGET.*?M:\s*(-?[\d.]+|-inf)", r.stderr)
            if m != "-inf"] if "TARGET" in r.stderr else \
           [(float(t), float(m)) for t, m in re.findall(r"t:\s*([\d.]+).*?M:\s*(-?[\d.]+)", r.stderr)]


def integrated(args):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats"] + args + ["-f", "null", "-"], capture_output=True, text=True)
    i = re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr)
    tp = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", r.stderr)
    return (float(i[-1]) if i else None), (float(tp[-1]) if tp else None)


# the voice on the reel clock: the segments in order
segs = CUT["segments"]
vin = []
for s in segs:
    vin += ["-i", A(s["file"])]
vf = "".join(f"[{k}:a]" for k in range(len(segs))) + f"concat=n={len(segs)}:v=0:a=1,ebur128=peak=true"
voice_args = vin + ["-filter_complex", vf]
voice_m = momentary(voice_args)
voice_i, voice_tp = integrated(voice_args)
print(f"voice: integrated {voice_i} LUFS, true peak {voice_tp} dBTP")

rows = []
for tag in re.findall(r"<audio [^>]*>", page):
    a = dict(re.findall(r'([\w-]+)="([^"]*)"', tag))
    start, dur, vol = float(a["data-start"]), float(a["data-duration"]), float(a.get("data-volume", 1))
    fo = float(a.get("data-fade-out", 0))
    f = (f"[0:a]atrim=0:{dur},afade=t=out:st={max(0, dur - fo)}:d={fo},volume={vol},"
         f"adelay={int(start * 1000)}:all=1,apad=whole_dur={DUR},ebur128=peak=true")
    m = momentary(["-i", A(html.unescape(a["src"])), "-filter_complex", f])
    if not m:
        continue
    t_pk, m_pk = max(m, key=lambda x: x[1])
    under = [v for t, v in voice_m if abs(t - t_pk) <= 0.2]
    v_here = max(under) if under else None
    rows.append((a["id"], start, t_pk, m_pk, v_here))
    gap_here = f"{v_here - m_pk:5.1f} dB under the voice there" if v_here is not None else "no voice there"
    print(f"{a['id']:<22} vol {vol:<5} starts {start:6.2f}s  peak M {m_pk:6.1f} LUFS at {t_pk:5.2f}s  "
          f"{voice_i - m_pk:5.1f} dB under voice integrated, {gap_here}")

for f in sys.argv[1:]:
    i, tp = integrated(["-i", f, "-af", "ebur128=peak=true"])
    print(f"\nrender {f}: integrated {i} LUFS, true peak {tp} dBTP")
    if f.endswith(".mov"):
        # the overlay MOV has no voice: its audio is the effects stem AS RENDERED. Check each effect's real level.
        stem = momentary(["-i", f, "-af", "ebur128"])
        for rid, start, t_pk, m_pk, v_here in rows:
            near = [v for t, v in stem if abs(t - t_pk) <= 0.25]
            if near:
                print(f"  rendered {rid:<20} peak M {max(near):6.1f} LUFS (predicted {m_pk:.1f}), "
                      f"{voice_i - max(near):4.1f} dB under the voice")
os.makedirs(A("renders"), exist_ok=True)
json.dump({"voice_integrated": voice_i, "voice_true_peak": voice_tp,
           "effects": [dict(zip(("id", "start", "peak_t", "peak_M", "voice_M_there"), r)) for r in rows]},
          open(A("renders/audio-measure.json"), "w"), indent=1)
