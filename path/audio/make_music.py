"""Synthesize the score for "The Path": 112 BPM, 10 bars, bright and warm (royalty-free: generated here).

    python3 audio/make_music.py -> audio/music.wav  (10 bars + 1 s tail on the final chord)

Bar 1: keys + marimba only (hello). Bar 2 on: soft kick, snaps on 2 and 4, shaker 16ths, bass.
Each stop gets a 4-note marimba motif; bar 9 (next chapter) lifts; bar 10 resolves and rings out.
"""
import os
import wave

import numpy as np
from scipy.signal import butter, sosfilt

SR = 48000
BPM = 112
BEAT = 60 / BPM
BARS = 10
END = BARS * 4 * BEAT
TOTAL = END + 1.0
N = int(round(TOTAL * SR))
rng = np.random.default_rng(21)
HERE = os.path.dirname(os.path.abspath(__file__))


def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def sos(kind, f, order=2):
    return butter(order, f, btype=kind, fs=SR, output="sos")


def T(sec):
    return np.arange(int(sec * SR)) / SR


def place(buf, x, t, g=1.0):
    i = int(round(t * SR)); j = min(len(buf), i + len(x))
    if j > i:
        buf[i:j] += g * x[: j - i]


def kick():
    t = T(0.4)
    f = 48 + 90 * np.exp(-t * 28)
    return np.tanh(1.4 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 8)) * 0.8


def snap():
    t = T(0.18)
    n = sosfilt(sos("bandpass", [1500, 5000]), rng.standard_normal(len(t)))
    return n * (np.exp(-t * 60) + 0.6 * (t > 0.008) * np.exp(-np.clip(t - 0.008, 0, None) * 90)) * 0.35


def shaker(acc=1.0):
    t = T(0.07)
    n = sosfilt(sos("bandpass", [5000, 11000]), rng.standard_normal(len(t)))
    return n * np.minimum(1, t / 0.01) * np.exp(-t * 55) * 0.12 * acc


def keys(notes, dur):
    """Rhodes-ish: FM bell on a sine, gentle tremolo"""
    t = T(dur)
    x = np.zeros_like(t)
    for n in notes:
        f = midi(n)
        mod = np.sin(2 * np.pi * f * 1.0 * t) * 1.2 * np.exp(-t * 3)
        x += np.sin(2 * np.pi * f * t + mod)
    x *= (1 + 0.12 * np.sin(2 * np.pi * 5 * t)) / len(notes)
    return x * np.minimum(1, t / 0.006) * np.exp(-t * 0.9) * np.clip((dur - t) / 0.08, 0, 1) * 0.35


def marimba(note, dur=0.35):
    t = T(dur)
    f = midi(note)
    x = np.sin(2 * np.pi * f * t) * np.exp(-t * 9) + 0.35 * np.sin(2 * np.pi * f * 4 * t) * np.exp(-t * 30)
    return x * np.minimum(1, t / 0.002) * 0.3


def bass(note, dur):
    t = T(dur)
    f = midi(note)
    x = np.sin(2 * np.pi * f * t) + 0.2 * np.sin(4 * np.pi * f * t)
    return x * np.minimum(1, t / 0.005) * np.exp(-t * 2) * np.clip((dur - t) / 0.02, 0, 1) * 0.42


# C major, bright: C G Am F | C G F G | Am F G | C (resolve)
CH = [(48, [64, 67, 72]), (43, [62, 67, 71]), (45, [64, 69, 72]), (41, [65, 69, 72]), (48, [64, 67, 72]),
      (43, [62, 67, 71]), (41, [65, 69, 72]), (43, [62, 67, 71]), (45, [64, 69, 72, 76]), (48, [64, 67, 72, 76])]
MOTIF = [[0, 2, 1, 2], [2, 1, 0, 1], [0, 1, 2, 3], [2, 0, 1, 2]]

drums, bed = np.zeros(N), np.zeros(N)
for bar in range(BARS):
    t0 = bar * 4 * BEAT
    root, tones = CH[bar]
    last = bar == BARS - 1
    place(bed, keys(tones, (4 * BEAT + 0.1) if not last else 4 * BEAT + 1.0), t0, 1.0)
    mot = MOTIF[bar % 4]
    for k in range(4):
        n = tones[mot[k] % len(tones)] + 12
        place(bed, marimba(n), t0 + k * BEAT + (BEAT / 2 if k % 2 else 0) * 0, 0.9)
        if bar >= 1 and not last:
            place(bed, marimba(tones[(mot[k] + 1) % len(tones)] + 12, 0.25), t0 + k * BEAT + BEAT * 0.75, 0.45)
    if bar == 0:
        continue
    for b in range(4):
        tb = t0 + b * BEAT
        if not (last and b > 0):
            place(drums, kick(), tb)
        if b in (1, 3) and not last:
            place(drums, snap(), tb)
        if not last:
            for s in range(4):
                place(drums, shaker(1.0 if s == 2 else 0.55), tb + s * BEAT / 4)
            place(bed, bass(root, BEAT * 0.45), tb + BEAT / 2)
    if last:
        place(bed, bass(root, 1.6), t0, 1.0)

mix = drums + bed
t = np.arange(N) / SR
duck = np.where((t >= 4 * BEAT) & (t < END - 4 * BEAT), 1 - 0.3 * np.exp(-((t % BEAT) / BEAT) * 8), 1.0)
mix = drums + bed * duck
mix = sosfilt(sos("highpass", 30), mix)
mix = np.tanh(mix * 1.2)
mix[-int(0.3 * SR):] *= np.linspace(1, 0, int(0.3 * SR))
mix *= 10 ** (-1 / 20) / np.max(np.abs(mix))
st = np.stack([mix, mix], 1)
with wave.open(os.path.join(HERE, "music.wav"), "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((st * 32767).astype("<i2").tobytes())
print(f"wrote audio/music.wav  {TOTAL:.2f}s  {BPM} BPM  {BARS} bars + tail")
