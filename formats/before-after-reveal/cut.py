#!/usr/bin/env python3
"""Media prep for the Before-and-after reveal (the demo: the same take before and after an HDR -> SDR fix).

WHY: the "before" must be the REAL washed-out file, and the "after" the REAL converted file, cut to the same clock.
The voice runs from the after file's audio (same take, same sound) with a gap where the process montage plays
(the format's montage carries tactile sounds, not speech). For a member: point BEFORE/AFTER at your two clips,
set VOICE_KEEP and GAP, optionally SCRIPT, then run (inside this folder)
    $PY cut.py
    $PY build.py

Writes: assets/before.mp4, assets/after.mp4 (1080x1920, 30 fps, keyframe every 30 frames, no audio),
assets/voice.wav (-14 LUFS), assets/words-cut.json (cut clock), assets/scope-before.png + scope-after.png + scope-stats.json
(real vectorscopes + saturation numbers of one frame of each file, for the process montage), cut.json (the clock numbers build.py reads).
"""
import json, os, subprocess, sys

# ---- per take. The numbers below are example values for the demo take; Claude sets these per take. ----
BEFORE = os.path.expanduser("~/Movies/Edits-inbox/your-before.mov")   # the real "before" clip, untouched
AFTER = os.path.expanduser("~/Movies/Edits-inbox/your-after.mov")     # the real "after" clip (the voice comes from here)
START = 0.90            # source second the reel opens on (on the demo: 0.75 s looking at camera before the first word)
VOICE_KEEP = [(0.90, 4.86), (4.95, 9.90)]   # [setup line] | [payoff line + the hold], source seconds in AFTER
GAP = 2.60              # process montage length, inserted between the two voice parts
SCOPE_AT = 3.0          # source second used for the colour scopes (same frame in both files)
LUFS = -14.0
# The proofread spoken line, word for word (it replaces whisper's spelling by position). Leave it empty to use the
# words as whisper heard them. Use \u00a0 to keep two words as one caption word (e.g. a two-word brand name).
SCRIPT = ""
# word-start snaps on the cut clock where whisper drifts after a silence: {word index: start second}, measured on a
# 30 ms RMS envelope of voice.wav. Empty until you've checked the printed timings.
SNAP = {}
# the Python running this file does the transcribing (each skill runs templates with its own Python). Override with WHISPER_PYTHON.
WHISPER_PY = os.environ.get("WHISPER_PYTHON") or sys.executable

def run(cmd):
    subprocess.run(cmd, check=True)

def video(src, out):
    # Chrome can't show 10-bit HLG HEVC reliably. The plain 8-bit decode keeps the washed look the raw file has in
    # any editor that skips the HDR tone map, which is exactly the "before" a member sees.
    run(["ffmpeg", "-v", "error", "-y", "-i", src, "-map", "0:v:0", "-vf", "scale=1080:1920:flags=lanczos,fps=30,format=yuv420p",
         "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
         "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-g", "30", "-an", out])

def voice():
    (a1, b1), (a2, b2) = VOICE_KEEP
    fc = (f"[0:a:0]atrim={a1}:{b1},asetpts=PTS-STARTPTS,afade=t=out:st={b1-a1-0.02:.3f}:d=0.02[p1];"
          f"[0:a:0]atrim={a2}:{b2},asetpts=PTS-STARTPTS,afade=t=in:d=0.02,afade=t=out:st={b2-a2-0.15:.3f}:d=0.15[p2];"
          f"anullsrc=r=48000:cl=mono,atrim=0:{GAP}[gap];"
          f"[p1]aformat=sample_rates=48000:channel_layouts=mono[q1];[p2]aformat=sample_rates=48000:channel_layouts=mono[q2];"
          f"[q1][gap][q2]concat=n=3:v=0:a=1[a]")
    run(["ffmpeg", "-v", "error", "-y", "-i", AFTER, "-filter_complex", fc, "-map", "[a]", "-c:a", "pcm_s16le",
         "assets/voice-raw.wav"])
    meas = subprocess.run(["ffmpeg", "-hide_banner", "-i", "assets/voice-raw.wav", "-af",
                           f"loudnorm=I={LUFS}:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                          capture_output=True, text=True).stderr
    i = meas.rindex("{"); m = json.loads(meas[i:meas.index("}", i) + 1])
    af = (f"loudnorm=I={LUFS}:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true,"
          "aresample=48000")
    run(["ffmpeg", "-v", "error", "-y", "-i", "assets/voice-raw.wav", "-af", af, "-ac", "2", "-c:a", "pcm_s16le", "assets/voice.wav"])

def scopes():
    """Real vectorscopes (colour spread: the further from the centre, the more colour) of the same frame in both
    files, cropped to the middle of the scope, plus ffmpeg signalstats numbers for the card labels."""
    stats = {}
    for name in ("before", "after"):
        src = f"assets/{name}.mp4"
        run(["ffmpeg", "-v", "error", "-y", "-ss", str(SCOPE_AT), "-i", src, "-frames:v", "1", "-vf",
             "vectorscope=mode=color3:intensity=0.03:envelope=none:graticule=none,crop=128:128:64:64,scale=640:640:flags=bicubic",
             f"assets/scope-{name}.png"])
        out = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(SCOPE_AT), "-i", src, "-frames:v", "1", "-vf",
                              "signalstats,metadata=print:file=-", "-f", "null", "-"], capture_output=True, text=True).stdout
        kv = dict(l.split("=", 1) for l in out.split() if l.startswith("lavfi.signalstats."))
        stats[name] = {k.split(".")[-1]: float(v) for k, v in kv.items() if k.split(".")[-1] in ("SATAVG", "YAVG")}
    return stats

def words():
    code = r'''
import json, mlx_whisper
r = mlx_whisper.transcribe("assets/voice.wav", path_or_hf_repo="mlx-community/whisper-large-v3-turbo",
                           word_timestamps=True, language="en")
print(json.dumps([{"text": w["word"].strip(), "start": w["start"], "end": w["end"]} for s in r["segments"] for w in s["words"]]))
'''
    out = subprocess.run([WHISPER_PY, "-c", code], capture_output=True, text=True, check=True).stdout
    ws = json.loads(out.strip().splitlines()[-1])
    script = SCRIPT.split(" ") if SCRIPT else [w["text"] for w in ws]
    if len(script) != len(ws):
        sys.exit(f"SCRIPT has {len(script)} words, whisper {len(ws)}: " + " ".join(w["text"] for w in ws))
    res = [{"id": f"w{i}", "text": t, "start": round(w["start"], 3), "end": round(max(w["end"], w["start"] + 0.08), 3)}
           for i, (w, t) in enumerate(zip(ws, script))]
    for i, t in SNAP.items():
        res[i]["start"] = t
        res[i]["end"] = max(res[i]["end"], t + 0.12)
    json.dump(res, open("assets/words-cut.json", "w"), indent=1)
    print(" ".join(f"{w['text']}@{w['start']}" for w in res))

if __name__ == "__main__":
    os.makedirs("assets", exist_ok=True)   # why: the template ships without media
    if "--words-only" not in sys.argv:
        video(BEFORE, "assets/before.mp4")
        video(AFTER, "assets/after.mp4")
        voice()
        json.dump(scopes(), open("assets/scope-stats.json", "w"), indent=1)
    words()
    p1 = VOICE_KEEP[0][1] - VOICE_KEEP[0][0]
    json.dump({"start": START, "reveal_media_start": VOICE_KEEP[1][0], "process_at": round(p1, 3),
               "reveal_at": round(p1 + GAP, 3), "duration": round(p1 + GAP + VOICE_KEEP[1][1] - VOICE_KEEP[1][0], 3)},
              open("cut.json", "w"), indent=1)
    print(open("cut.json").read())
