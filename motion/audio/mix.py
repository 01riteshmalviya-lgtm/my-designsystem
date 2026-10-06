"""Build out/soundtrack.wav: the song from its measured downbeat + every UI sound placed by its measured peak.

    python3 audio/mix.py      (needs out/beats.json from analyze.py and out/cues.json from `node render.mjs cues`)
"""
import json
import os
import subprocess

import numpy as np

SR = 48000
FPS = 60
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
OUT = os.path.join(ROOT, "out")


def load(path, ch):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", str(ch), "-ar", str(SR), "-f", "f32le", "-"],
                         check=True, capture_output=True).stdout
    return np.frombuffer(raw, dtype="<f4").astype(np.float64).reshape(-1, ch)


def peak_index(x):
    """sample index of the loudest point of the 1 ms RMS envelope"""
    k = SR // 1000
    env = np.sqrt(np.convolve(x ** 2, np.ones(k) / k, mode="same"))
    return int(np.argmax(env))


beats = json.load(open(os.path.join(OUT, "beats.json")))
cues = json.load(open(os.path.join(OUT, "cues.json")))["cues"]
frames = round(beats["loop_seconds"] * FPS)
N = round(frames / FPS * SR)

song = load(os.path.join(ROOT, beats["source"]), 2)
start = int(round(beats["start"] * SR))
if beats.get("circular"):
    music = np.take(song, (np.arange(N) + start) % len(song), axis=0, mode="wrap")
else:
    music = song[max(start, 0):max(start, 0) + N]
    music = np.pad(music, ((0, N - len(music)), (0, 0)))
    fade = int(0.01 * SR)
    music[:fade] *= np.linspace(0, 1, fade)[:, None]
    music[-fade:] *= np.linspace(1, 0, fade)[:, None]

sfx = np.zeros(N)
cache, report = {}, []
for c in cues:
    if c["s"] not in cache:
        x = load(os.path.join(HERE, "sfx", f"{c['s']}.wav"), 1)[:, 0]
        cache[c["s"]] = (x, peak_index(x))
    x, pk = cache[c["s"]]
    at = int(round(c["t"] * SR)) - pk          # the peak lands exactly on the cue
    idx = (np.arange(len(x)) + at) % N          # wrap: tails past the end ring into the start (seamless loop)
    np.add.at(sfx, idx, x * c.get("g", 1.0))
    report.append(f"{c['t']:7.3f}s  {c['s']:<8} peak +{1000 * pk / SR:5.1f}ms")

mix = music * 0.82 + sfx[:, None] * 0.9
mix = np.tanh(mix * 1.05) / np.tanh(1.05)
mix *= 10 ** (-1 / 20) / max(1e-9, np.abs(mix).max())

import wave
with wave.open(os.path.join(OUT, "soundtrack.wav"), "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mix * 32767).astype("<i2").tobytes())
print("\n".join(report))
print(f"{len(cues)} cues, {N / SR:.3f}s ({frames} frames) -> out/soundtrack.wav")
