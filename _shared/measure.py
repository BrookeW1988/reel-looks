#!/usr/bin/env python3
"""measure.py <project dir>: MEASURES (not listens to) the rendered reel.
- file specs (size, fps, duration, codecs) of renders/<slug>.mp4 and the overlay MOV (pixel format = alpha or not)
- integrated loudness + true peak of the render
- every sound effect on its own, at its mix volume, as a 400 ms momentary loudness at its hit, compared with the
  voice's integrated loudness (target: 6-10 dB under). Sounds are rebuilt offline from index.html's <audio> tags.
Run with the skill's venv python: $PY measure.py <project dir>"""
import json, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reeltools as rt

P = os.path.abspath(sys.argv[1]); os.chdir(P); S = os.path.basename(P)
out = {"slug": S}
def probe(f):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,codec_name,width,height,r_frame_rate,pix_fmt:format=duration,size",
                        "-of", "json", f], capture_output=True, text=True).stdout
    return json.loads(r)
for f in (f"renders/{S}.mp4", f"renders/{S}-overlays.mov", "renders/poster.jpg"):
    if os.path.exists(f):
        d = probe(f)
        out[f] = {"size_mb": round(int(d["format"].get("size", 0)) / 1e6, 1), "duration": d["format"].get("duration"),
                  "streams": [{k: s.get(k) for k in ("codec_type", "codec_name", "width", "height", "r_frame_rate", "pix_fmt")} for s in d["streams"]]}
    else:
        out[f] = "MISSING"
mp4 = f"renders/{S}.mp4"
if os.path.exists(mp4):
    out["render_loudness"] = rt.measure(mp4)
html = open("index.html").read()
voice = None
for m in re.finditer(r'<(?:audio|video)[^>]*>', html):
    tag = m.group(0)
    if 'data-has-audio="true"' in tag or 'id="voice"' in tag:
        voice = re.search(r'src="([^"]+)"', tag).group(1)
if voice:
    out["voice_integrated_lufs"] = rt.measure(voice)["integrated_lufs"]
sfx = []
for m in re.finditer(r'<audio id="(sfx[^"]*)"[^>]*>', html):
    tag = m.group(0)
    g = lambda a, d=None: (re.search(a + r'="([^"]+)"', tag) or [None, d])[1]
    src, start, dur, vol, ms = g("src"), float(g("data-start")), float(g("data-duration")), float(g("data-volume", 1)), float(g("data-media-start", 0))
    if not src or not os.path.exists(src):
        continue  # why: SFX aren't shipped; a missing file is skipped, not a crash
    tmp = f"/tmp/_sfx_{S}_{m.group(1)}.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(ms), "-t", str(dur), "-i", src, "-af", f"volume={vol},apad=pad_dur=1", "-ar", "48000", tmp], check=True)
    env = rt.envelope(tmp, hop=0.01); pk = max(env, key=lambda x: x[1])[0]
    lufs = rt.momentary_at(tmp, pk, 0.4)
    row = {"id": m.group(1), "hit_at": round(start + pk, 3), "momentary_lufs": round(lufs, 1)}
    if voice:
        row["under_voice_db"] = round(out["voice_integrated_lufs"] - lufs, 1)
    sfx.append(row)
    os.remove(tmp)
out["sfx_offline_estimate"] = sfx


def m_series(path):
    """Momentary (400 ms) loudness every 100 ms, as [(t_end, LUFS)]."""
    txt = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-vn", "-af", "ebur128", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    rows = []
    for line in txt.splitlines():
        if "t:" in line and "M:" in line and line.startswith("[Parsed_ebur128"):
            t = float(line.split("t:")[1].split()[0]); m = float(line.split("M:")[1].split()[0])
            rows.append((t, m))
    return rows


# IN THE RENDER: subtract the voice waveform (aligned by cross-correlation) from the render's audio; what is left is
# the sound effects alone. Then read each one's peak momentary loudness (ebur128, K-weighted) around its hit.
if os.path.exists(mp4):
    import numpy as np, math
    def raw(f):
        return np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", f, "-vn", "-ac", "2", "-ar", "48000", "-f", "f32le", "-"],
                                            capture_output=True, check=True).stdout, np.float32).reshape(-1, 2)
    r = raw(mp4)
    res = r.copy()
    if voice:
        v = raw(voice)[: len(r)]
        a, b = r[96000:240000, 0], v[96000:240000, 0]
        g = float(np.dot(a, b) / (np.dot(b, b) + 1e-12))
        vs = np.zeros_like(r); vs[: len(v)] = v
        res = r - g * vs
        q = res[96000:240000]
        out["voice_subtraction"] = {"gain": round(g, 4), "residue_in_voice_stretch_db": round(10 * math.log10(float(np.mean(q ** 2)) + 1e-12), 1)}
    tmpw = f"/tmp/_resid_{S}.f32"
    res.astype(np.float32).tofile(tmpw)
    def peak_m(t0, t1):
        txt = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-f", "f32le", "-ar", "48000", "-ac", "2", "-i", tmpw,
                              "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
        best = -120.0
        for line in txt.splitlines():
            if line.startswith("[Parsed_ebur128") and "M:" in line and "t:" in line:
                t = float(line.split("t:")[1].split()[0]); m = float(line.split("M:")[1].split()[0])
                if t0 <= t - 0.2 <= t1:
                    best = max(best, m)
        return best
    ref = out.get("voice_integrated_lufs", -14.0)
    meas = []
    for row in sfx:
        m = peak_m(row["hit_at"] - 0.25, row["hit_at"] + 0.25)
        meas.append({"id": row["id"], "hit_at": row["hit_at"], "sfx_only_M": m,
                     ("under_voice_db" if voice else "under_minus14_db"): round(ref - m, 1)})
    out["sfx_in_render"] = meas
    os.remove(tmpw)
print(json.dumps(out, indent=1))
