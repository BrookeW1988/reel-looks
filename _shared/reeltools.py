"""Shared helpers for the style-reel generators (pov-skit, green-screen-proof, timestamp-vlog, yes-but-split).

WHY one shared file: every format needs the same three chores - cut a take, get accurate word times, and place a
sound so its loudest moment lands one frame after the picture. Keeping them here means a fix lands in all four.
Run everything with the skill's venv python (its setup script installs mlx-whisper, numpy and pillow):
    $PY cut.py
"""
import json, math, os, struct, subprocess, sys

FPS = 30
FRAME = 1 / FPS
WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "mlx-community/whisper-large-v3-turbo")
# The Python running this file does the transcribing (each skill runs templates with its own Python). Override with WHISPER_PYTHON.
WHISPER_PY = os.environ.get("WHISPER_PYTHON") or sys.executable

# ASR fixes applied to every caption word (why: whisper mishears brand and tool names).
# Add words your transcript mishears here, lower-case key -> how it should read on screen.
FIXES = {"chatgpt": "ChatGPT", "chatgpt's": "ChatGPT's"}  # one word per key: fixes are matched word by word


def run(cmd):
    subprocess.run(cmd, check=True)


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                         capture_output=True, text=True, check=True).stdout
    return float(out.strip())


def cut(src, keep, out, speed=1.0, loudnorm=True, audio=True, vf_extra=None, size=(1080, 1920)):
    """Concatenate the KEEP ranges (source seconds) of one take, speed it up, level the voice to -14 LUFS.

    Each piece gets a 12 ms audio fade at both ends so the joins don't click."""
    w, h = size
    parts = []
    # a keep range may carry its own speed as a third value, e.g. [4.45, 5.0, 0.5] = that bit at half speed
    for i, k in enumerate(keep):
        a, b = k[0], k[1]
        sp = (k[2] if len(k) > 2 else 1.0) * speed
        v = f"[0:v]trim={a}:{b},setpts=(PTS-STARTPTS)/{sp},scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},fps={FPS}"
        if vf_extra:
            v += "," + vf_extra
        parts.append(v + f"[v{i}];")
        if audio:
            parts.append(f"[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS,atempo={sp},afade=t=in:d=0.012,"
                         f"areverse,afade=t=in:d=0.012,areverse[a{i}];")
    n = len(keep)
    if audio:
        fc = "".join(parts) + "".join(f"[v{i}][a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[v][a];"
        fc += "[a]" + ("loudnorm=I=-14:TP=-1.5:LRA=11," if loudnorm else "") + "aresample=48000[ao]"
        maps = ["-map", "[v]", "-map", "[ao]", "-c:a", "aac", "-b:a", "192k"]
    else:
        fc = "".join(parts) + "".join(f"[v{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0[v]"
        maps = ["-map", "[v]", "-an"]
    run(["ffmpeg", "-v", "error", "-y", "-i", src, "-filter_complex", fc, *maps,
         "-c:v", "libx264", "-crf", "17", "-preset", "medium", "-g", str(FPS), "-pix_fmt", "yuv420p",
         "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", out])


def envelope(path, start=0.0, end=None, hop=0.02):
    """RMS level (dBFS) every `hop` seconds, mono. Used to snap whisper's word edges to real speech."""
    cmd = ["ffmpeg", "-v", "error", "-ss", str(start)] + (["-to", str(end)] if end else []) + \
          ["-i", path, "-vn", "-ac", "1", "-ar", "8000", "-f", "f32le", "-"]
    d = subprocess.run(cmd, capture_output=True, check=True).stdout
    n = len(d) // 4
    a = struct.unpack(f"{n}f", d)
    step = int(8000 * hop)
    env = []
    for i in range(0, n, step):
        w = a[i:i + step]
        r = math.sqrt(sum(x * x for x in w) / max(1, len(w))) + 1e-9
        env.append((start + i / 8000, 20 * math.log10(r)))
    return env


def transcribe(path):
    """Word timings with mlx_whisper large-v3-turbo, then edges snapped to the audio envelope:
    a word's start moves forward past leading silence (< -38 dBFS) - whisper tends to start words early."""
    import mlx_whisper
    r = mlx_whisper.transcribe(path, path_or_hf_repo=WHISPER_MODEL, word_timestamps=True, language="en")
    words = []
    for s in r["segments"]:
        for w in s["words"]:
            t = w["word"].strip()
            if not t:
                continue
            if t.startswith("-") and words:      # whisper splits "hyper-focus" into "hyper" + "-focus": join them
                words[-1]["text"] += t; words[-1]["end"] = round(w["end"], 3)
                continue
            words.append({"text": t, "start": round(w["start"], 3), "end": round(w["end"], 3)})
    env = envelope(path)
    for w in words:
        t = w["start"]
        # walk forward while it's silent, but never past the middle of the word
        mid = (w["start"] + w["end"]) / 2
        for (tt, db) in env:
            if tt < t:
                continue
            if tt > mid or db > -38:
                break
            w["start"] = round(tt, 3)
    for i, w in enumerate(words):
        w["id"] = f"w{i}"
        w["end"] = max(w["end"], w["start"] + 0.08)
        core = w["text"].rstrip(".,!?")
        if core.lower() in FIXES:
            w["text"] = FIXES[core.lower()] + w["text"][len(core):]
    return words


def sfx_peak(path):
    """Seconds from the file's start to its loudest 10 ms window (the 'hit')."""
    env = envelope(path, hop=0.01)
    return max(env, key=lambda x: x[1])[0]


def sfx_start(picture_t, path):
    """Start time so the sound's peak lands ONE FRAME after its picture moment (light first, then sound)."""
    return round(picture_t + FRAME - sfx_peak(path), 3)


def measure(path):
    """Integrated loudness + true peak of a rendered file (ffmpeg ebur128)."""
    out = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    summ = out[out.rfind("Summary:"):]
    i = float(summ.split("I:")[1].split("LUFS")[0])
    tp = float(summ.split("Peak:")[1].split("dBFS")[0])
    return {"integrated_lufs": i, "true_peak_dbtp": tp}


def momentary_at(path, t, win=0.4):
    """Short-window loudness (LUFS) of a file around time t - used to compare a sound hit with the voice."""
    out = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-ss", str(max(0, t - win / 2)), "-t", str(win), "-i", path,
                          "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
    summ = out[out.rfind("Summary:"):]
    return float(summ.split("I:")[1].split("LUFS")[0])


def grade(selector, adjust, out_txt, details=None, html_file="index.html"):
    """Apply a colour grade with `hyperframes media-treatment` (the HyperFrames rule: never CSS filters on footage),
    then save the resulting data-color-grading attribute to out_txt so build.py can re-insert it on every rebuild."""
    import re
    patch = {"adjust": adjust}
    if details:
        patch["details"] = details
    run(["npx", "--yes", "hyperframes@0.9.83", "media-treatment", "--file", html_file, "--selector", selector,
         "--grading", json.dumps(patch), "--apply", "--json"])
    src = open(html_file).read()
    el_id = selector.lstrip("#")
    m = re.search(r'<(?:video|img)[^>]*id="' + re.escape(el_id) + r'"[^>]*>', src, re.S)
    attr = re.search(r'data-color-grading="[^"]*"', m.group(0)).group(0)
    open(out_txt, "w").write(attr)
    return attr


def write_overlays(html_text):
    """The graphics-only page lives in its own tiny project, overlays/, so the main project keeps exactly one root
    composition (two roots make HyperFrames play audio twice). overlays/assets is a link to ../assets, so the same
    asset paths work. Render it with: npx hyperframes render overlays --format mov -o renders/<slug>-overlays.mov"""
    os.makedirs("overlays", exist_ok=True)
    if not os.path.lexists("overlays/assets"):
        os.symlink("../assets", "overlays/assets")
    for f in ("hyperframes.json", "package.json"):
        if os.path.exists(f) and not os.path.exists(f"overlays/{f}"):
            open(f"overlays/{f}", "w").write(open(f).read())
    if os.path.exists("overlays.html"):
        os.remove("overlays.html")
    open("overlays/index.html", "w").write(html_text)
