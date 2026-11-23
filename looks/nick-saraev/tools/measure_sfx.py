#!/usr/bin/env python3
"""Per-file facts for placing and levelling effects, measured the same way the final mix is checked:
spk  = time of the file's absolute sample peak (s)      -> what "peaks 1 frame after the picture" is measured on
mmax = max momentary (400 ms) loudness, LUFS, as PLAYED (a mono file is upmixed to both channels: +3 LU)             -> what "6-10 dB under the voice" is measured on
Appends 'spk' and 'mmax' to each line of assets/sfx/peaks.txt (keeps the hyperframes audio fields)."""
import array, re, subprocess
lines = [l.rstrip("\n") for l in open("assets/sfx/peaks.txt") if l.strip()]
out = []
for l in lines:
    f = l.split()[0]
    l = re.sub(r" spk \S+ mmax \S+$", "", l)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", f"assets/sfx/{f}", "-ac", "1", "-ar", "48000", "-f", "s16le", "-"],
                         capture_output=True).stdout
    a = array.array("h", raw)
    spk = max(range(len(a)), key=lambda i: abs(a[i])) / 48000
    mono = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=channels", "-of", "csv=p=0",
                           f"assets/sfx/{f}"], capture_output=True, text=True).stdout.strip() == "1"
    # pad 1 s of silence so the 400 ms momentary window sees the whole of very short files
    e = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", f"assets/sfx/{f}", "-af", "pan=stereo|c0=c0|c1=c0,apad=pad_dur=1,ebur128" if mono else "apad=pad_dur=1,ebur128",
                        "-f", "null", "-"], capture_output=True, text=True).stderr
    M = [float(m) for m in re.findall(r"M:\s*(-?[\d.]+)", e)]
    out.append(f"{l} spk {spk:.3f} mmax {max(M):.1f}")
    print(out[-1].split()[0], "spk", f"{spk:.3f}", "mmax", max(M))
open("assets/sfx/peaks.txt", "w").write("\n".join(out) + "\n")
