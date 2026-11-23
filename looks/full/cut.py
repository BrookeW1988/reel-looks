#!/usr/bin/env python3
"""Rough cut + accurate word timings for one style reel. Reads reel.json, writes assets/seg<N>.mp4 + assets/words-cut.json.

    $PY cut.py            # the skill's venv has mlx_whisper (Apple silicon)

WHY each step:
- keep spans are SOURCE seconds picked at real pauses (silencedetect / RMS envelope), never mid-word. House rule: no trim
  that saves < 0.15 s (a 1-2 frame jump for nothing).
- every segment is levelled to the voice target (-14 LUFS, two-pass loudnorm) BEFORE it meets the others, because two
  takes from two rooms arrive 10+ dB apart (a studio-mic take vs an iPhone take in another room).
- shift_px slides the take DOWN so the hook and cards sit above your head. The empty strip at the top is your
  own wall: the top 60 px of the frame, stretched and blurred.
- word times come from mlx_whisper (large-v3-turbo, word_timestamps) run on the FINISHED cut (so no remapping error),
  then snapped to the audio envelope: whisper puts some starts up to ~0.4 s early, inside the pause before the word.
  (whisper.cpp drifted up to ~1 s on the demo take.) The heard line is printed: proofread it, it becomes the captions.
- `--skip-cut` reuses the assets/seg*.mp4 already made and only redoes the words.
"""
import json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(open(os.path.join(HERE, next((a for a in sys.argv[1:] if a.endswith(".json")), "reel.json"))))
SPEED = CFG.get("speed", 1.3)
LUFS = CFG.get("voice_lufs", -14)
MODEL = os.environ.get("WHISPER_MODEL", "mlx-community/whisper-large-v3-turbo")
# The Python running this file does the transcribing (each skill runs templates with its own Python). Override with WHISPER_PYTHON.
WHISPER_PY = os.environ.get("WHISPER_PYTHON") or sys.executable
# Peak limiter at -3 dBFS after loudnorm. WHY: on the demo take linear loudnorm can't hold -1.5 dBTP, AAC then decodes
# to +1.5 dBFS overs, and HyperFrames' delivery check turns the WHOLE mix down 0.7 dB (render warning audio_lowered).
LIMIT = "alimiter=limit=0.708:level=false:attack=5:release=50"
A = lambda p: os.path.join(HERE, p)


def ffprobe_dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                                capture_output=True, text=True).stdout.strip())


def graph(seg):
    """ffmpeg filter graph: trim + concat the keep spans, frame to 1080x1920, slide down, speed up."""
    keep, shift = seg["keep"], seg.get("shift_px", 0)
    parts = []
    for i, (a, b) in enumerate(keep):
        parts.append(f"[0:v]trim={a}:{b},setpts=PTS-STARTPTS[v{i}];"
                     f"[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS,afade=t=in:d=0.012,"
                     f"afade=t=out:st={b - a - 0.012:.3f}:d=0.012[a{i}];")
    n = len(keep)
    fc = "".join(parts) + "".join(f"[v{i}][a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[vc][ac];"
    flip = "hflip," if seg.get("hflip") else ""
    fc += f"[vc]{flip}scale=1080:1920:flags=lanczos,setsar=1[vs];"
    if shift > 0:
        # top strip = your own wall (top 60 px of the frame), stretched to the gap and softened so it reads as room
        fc += (f"[vs]split[vm][vt];[vt]crop=1080:60:0:0,scale=1080:{shift},gblur=sigma=14[top];"
               f"[vm]crop=1080:{1920 - shift}:0:0[main];[top][main]vstack,setsar=1[vf];")
    else:
        fc += "[vs]null[vf];"
    fc += f"[vf]setpts=PTS/{SPEED},fps=30[vo];[ac]atempo={SPEED}[at]"
    return fc


def cut(i, seg):
    src, out = A(os.path.expanduser(seg["src"])), A(f"assets/seg{i}.mp4")   # src may start with ~/
    if "--skip-cut" in sys.argv and os.path.exists(out):
        return out
    fc = graph(seg)
    # pass 1: measure loudness of the finished segment audio
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", src, "-filter_complex",
                        fc + f";[at]loudnorm=I={LUFS}:TP=-1.5:LRA=11:print_format=json[ao]",
                        "-map", "[vo]", "-map", "[ao]", "-f", "null", "-"], capture_output=True, text=True)
    if "input_i" not in r.stderr:
        sys.exit(r.stderr[-2000:])
    m = json.loads(r.stderr[r.stderr.rfind("{"):r.stderr.rfind("}") + 1])
    ln = (f"loudnorm=I={LUFS}:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-filter_complex", fc + f";[at]{ln},aresample=48000,{LIMIT}[ao]",
                    "-map", "[vo]", "-map", "[ao]", "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-g", "30",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", out], check=True)
    print(f"seg{i}: {seg['src']} keep {seg['keep']} -> {ffprobe_dur(out):.3f} s (input {m['input_i']} LUFS)")
    return out


def whisper(path):
    import mlx_whisper
    r = mlx_whisper.transcribe(path, path_or_hf_repo=MODEL, word_timestamps=True, language="en")
    return [{"text": w["word"].strip(), "start": w["start"], "end": w["end"]} for s in r["segments"] for w in s["words"]]


def envelope(path):
    """10 ms RMS envelope in dBFS of a file's audio (16 kHz mono)."""
    import numpy as np
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", "16000", "-"],
                         capture_output=True).stdout
    x = np.frombuffer(raw, np.float32)
    n = 160
    e = np.array([np.sqrt(np.mean(x[i:i + n] ** 2)) + 1e-9 for i in range(0, len(x) - n, n)])
    return 20 * np.log10(e)


def snap(words, env):
    """whisper puts some starts up to ~0.4 s early (inside the pause before the word). Push a start that sits in
    silence (< -40 dBFS) forward to the first frame of sound, and pull an end that sits in silence back."""
    db = lambda t: env[min(len(env) - 1, max(0, int(t * 100)))]
    for w in words:
        t = w["start"]
        while db(t) < -40 and t < w["end"] - 0.05:
            t += 0.01
        w["start"] = round(t, 3)
        t = w["end"]
        while db(t) < -40 and t > w["start"] + 0.08:
            t -= 0.01
        w["end"] = round(t, 3)
    return words


def tidy(words):
    """Join whisper's split hyphen words ('hyper' + '-focus'), then apply the reel's spelling fixes."""
    out = []
    for w in words:
        if out and w["text"].startswith("-"):
            out[-1] = {**out[-1], "text": out[-1]["text"] + w["text"], "end": w["end"]}
        else:
            out.append(dict(w))
    fixes = CFG.get("word_fixes", {})
    bare = lambda t: re.sub(r"[^\w'-]", "", t)
    final, k = [], 0
    while k < len(out):
        w, done = out[k], False
        for key, rep in fixes.items():          # phrase keys ("Right Mode") match across consecutive words
            n = len(key.split())
            run = out[k:k + n]
            if len(run) == n and " ".join(bare(x["text"]).lower() for x in run) == key.lower():
                reps = rep.split()
                t0, t1 = run[0]["start"], run[-1]["end"]
                tail = run[-1]["text"][len(bare(run[-1]["text"])):]      # keep the trailing punctuation
                span = (t1 - t0) / len(reps)
                for j, r in enumerate(reps):
                    final.append({**run[0], "text": r + (tail if j == len(reps) - 1 else ""),
                                  "start": round(t0 + j * span, 3), "end": round(t0 + (j + 1) * span, 3)})
                k += n
                done = True
                break
        if not done:
            final.append(w)
            k += 1
    return final


os.makedirs(A("assets"), exist_ok=True)   # why: the template ships without media, so assets/ may not exist yet
segs, words, clock = [], [], 0.0
for i, seg in enumerate(CFG["segments"]):
    out = cut(i, seg)
    dur = ffprobe_dur(out)
    # word times = whisper on the FINISHED cut (no remapping error), snapped to the audio envelope
    heard = snap(whisper(out), envelope(out))
    for w in heard:
        words.append({"text": w["text"], "start": round(clock + w["start"], 3),
                      "end": round(clock + max(w["end"], w["start"] + 0.08), 3), "seg": i})
    segs.append({"file": f"assets/seg{i}.mp4", "start": round(clock, 3), "duration": round(dur, 3)})
    print("  heard: " + " ".join(w["text"] for w in heard) + "\n  (proofread this line: it becomes the captions)")
    clock += dur

words = tidy(words)
for k, w in enumerate(words):
    w["id"] = f"w{k}"
json.dump({"segments": segs, "duration": round(clock, 3), "words": words}, open(A("assets/words-cut.json"), "w"), indent=1)
print(f"{len(words)} words, reel {clock:.3f} s")
print(" ".join(f"{k}:{w['text']}@{w['start']}" for k, w in enumerate(words)))
