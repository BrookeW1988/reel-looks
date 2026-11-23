"""Stand-in for mlx_whisper, used only when the real one isn't installed.

WHY this exists: the templates were written with `mlx_whisper` (fast on Apple silicon, installed by the
instagram-edits skill). The Claude Video Editor runs on Macs AND Linux with faster-whisper instead. Rather than
change every template, the Video Editor puts this folder on PYTHONPATH when `import mlx_whisper` would fail, so
`mlx_whisper.transcribe(...)` keeps working and returns the same shape:
    {"text": "...", "segments": [{"start", "end", "text", "words": [{"word", "start", "end"}]}]}

The model: faster-whisper doesn't read mlx model names, so `path_or_hf_repo` is ignored and this uses
REEL_LOOKS_WHISPER_MODEL (default "small.en", the same model the Video Editor transcribes with). Set it to
"large-v3-turbo" for the model the templates were measured with (bigger download, slower on a CPU).
"""
import os
import subprocess
import tempfile
import wave

_models = {}


def _model(name):
    # one model per process: loading it is the slow part
    if name not in _models:
        from faster_whisper import WhisperModel
        _models[name] = WhisperModel(name, device="auto", compute_type="int8")
    return _models[name]


def transcribe(path, path_or_hf_repo=None, word_timestamps=True, language=None, **_ignored):
    import numpy as np
    name = os.environ.get("REEL_LOOKS_WHISPER_MODEL", "small.en")
    if name.endswith(".en") and language not in (None, "en"):
        name = name[:-3]                      # an English-only model can't do other languages
    # decode with ffmpeg first: faster-whisper's own file reader breaks with some versions of its audio library
    wav = os.path.join(tempfile.mkdtemp(), "speech16k.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.expanduser(path), "-vn", "-ac", "1", "-ar", "16000", wav],
                   check=True)
    with wave.open(wav) as wf:
        samples = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
    it, _info = _model(name).transcribe(samples, language=language, word_timestamps=True,
                                        condition_on_previous_text=False, vad_filter=False)
    segments = []
    for seg in it:
        segments.append({"start": seg.start, "end": seg.end, "text": seg.text,
                         "words": [{"word": w.word, "start": w.start, "end": w.end} for w in (seg.words or [])]})
    return {"text": "".join(s["text"] for s in segments), "segments": segments}
