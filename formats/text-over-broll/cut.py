#!/usr/bin/env python3
"""B-roll prep for the Text over B-roll template.

WHY: the format is "1-3 steady clips, normal or slightly slowed, same grade". Slowing 30 fps phone footage by
plain frame-stretching stutters, so each clip is slowed with motion interpolation (ffmpeg minterpolate) and cut
to 1080x1920 from the 4K source (crops are 1.2x, so nothing goes soft).
For a member: list her clips in CLIPS (file, in, out, speed, crop) and run `python3 cut.py`, then `python3 build.py`.
Needs ffmpeg (no Python packages).

Writes assets/broll.mp4 (no audio: this format has no voice and no effects; the member adds a song in Edits)
and assets/clips.json (where each clip starts on the reel clock, for the text beats).
"""
import json, os, subprocess

# The member's clips live in her Edits inbox (why ~: the code expands it to her home folder).
FOOT = os.path.expanduser("~/Movies/Edits-inbox/")
# crop = (w, h, x, y) in SOURCE pixels (2160x3840 = iPhone 4K), or None for the full frame.
# Example values: file names, in/out (seconds), speeds and crops only show the shape. 1-3 steady clips, speed 0.5-1.0.
CLIPS = [
    # 1. a calm moment before anything happens, full frame
    {"file": "your-clip-1.mov", "in": 0.00, "out": 1.00, "speed": 0.50, "crop": None},
    # 2. a second clip, 1.2x crop anchored to the top: a tighter frame than clip 1, so the cut reads as a step in,
    #    not a jump
    {"file": "your-clip-2.mov", "in": 0.10, "out": 1.50, "speed": 0.60, "crop": (1800, 3200, 180, 0)},
    # 3. the last clip (outside, sky, ends on a smile in the demo). 1.2x crop anchored to the top keeps a head
    #    below the text
    {"file": "your-clip-3.mov", "in": 1.60, "out": 3.90, "speed": 0.55, "crop": (1800, 3200, 180, 0)},
]
FPS = 30

def main():
    # each clip is encoded on its own and MEASURED (minterpolate drops a few tail frames, so durations can't be
    # computed from in/out/speed), then the clips are joined without re-encoding
    parts, out, t = [], [], 0.0
    for i, c in enumerate(CLIPS):
        crop = f"crop={c['crop'][0]}:{c['crop'][1]}:{c['crop'][2]}:{c['crop'][3]}," if c["crop"] else ""
        vf = (f"trim={c['in']}:{c['out']},setpts=(PTS-STARTPTS)/{c['speed']},{crop}scale=1080:1920:flags=lanczos,"
              f"format=yuv420p,minterpolate=fps={FPS}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,setsar=1")
        part = f"assets/clip-{i + 1}.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", FOOT + c["file"], "-map", "0:v:0", "-vf", vf, "-r", str(FPS),
                        "-c:v", "libx264", "-crf", "15", "-preset", "slow", "-g", str(FPS), "-pix_fmt", "yuv420p",
                        "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-an", part], check=True)
        frames = int(subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries",
                                     "stream=nb_read_frames", "-of", "csv=p=0", part], capture_output=True, text=True).stdout)
        d = round(frames / FPS, 3)
        out.append({"file": c["file"], "start": round(t, 3), "duration": d})
        t += d
        parts.append(part)
    open("assets/concat.txt", "w").write("".join(f"file '{os.path.basename(p)}'\n" for p in parts))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", "assets/concat.txt", "-c", "copy",
                    "assets/broll.mp4"], check=True)
    for p in parts + ["assets/concat.txt"]:
        os.remove(p)
    json.dump(out, open("assets/clips.json", "w"), indent=1)
    print(json.dumps(out))

if __name__ == "__main__":
    main()
