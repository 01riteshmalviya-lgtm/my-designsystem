"""Synthesize a seamless 7-bar, 120 BPM minimal house loop (royalty-free: generated here).

Stand-in for a Mixkit track while mixkit.co is blocked by the sandbox network
policy. Drop a real track at audio/song.wav (or .mp3) and analyze.py will use it
instead.

    python3 audio/make_music.py  ->  audio/music.wav
"""
import os
import wave

import numpy as np
from scipy.signal import butter, sosfilt

SR = 48000
BPM = 120
BEAT = 60 / BPM
BARS = 7
LOOP = BARS * 4 * BEAT  # 14.0 s
N = int(round(LOOP * SR))
TAIL = 3 * SR

rng = np.random.default_rng(7)
HERE = os.path.dirname(os.path.abspath(__file__))


def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def sos(kind, f, order=2):
    return butter(order, f, btype=kind, fs=SR, output="sos")


def place(buf, x, t, gain=1.0):
    i = int(round(t * SR))
    j = min(len(buf), i + len(x))
    if j > i:
        buf[i:j] += gain * x[: j - i]


# ---------------------------------------------------------------- voices
def kick():
    n = int(0.45 * SR)
    t = np.arange(n) / SR
    f = 46 + 110 * np.exp(-t * 32)
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-t * 7.5)
    click = sosfilt(sos("highpass", 1800), rng.standard_normal(n)) * np.exp(-t * 300) * 0.25
    return np.tanh(1.6 * (body + click)) * 0.9


def hat(open_=False):
    n = int((0.16 if open_ else 0.05) * SR)
    t = np.arange(n) / SR
    x = sosfilt(sos("highpass", 7500, 4), rng.standard_normal(n))
    return x * np.exp(-t * (28 if open_ else 95)) * 0.22


def clap():
    n = int(0.3 * SR)
    t = np.arange(n) / SR
    noise = sosfilt(sos("bandpass", [900, 3200], 2), rng.standard_normal(n))
    e = np.zeros(n)
    for k, off in enumerate([0.0, 0.011, 0.022]):
        e += (t >= off) * np.exp(-np.clip(t - off, 0, None) * (160 if k < 2 else 22))
    return noise * e * 0.38


def bass(note, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = midi(note)
    x = np.sin(2 * np.pi * f * t) + 0.25 * np.sin(4 * np.pi * f * t)
    e = np.minimum(1, t / 0.004) * np.exp(-t * 3.0) * np.minimum(1, (dur - t) / 0.01).clip(0)
    return np.tanh(1.4 * x * e) * 0.42


def pluck(note, dur=0.32):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = midi(note)
    x = sum(np.sin(2 * np.pi * f * k * t) / k ** 1.6 * np.exp(-t * (6 + 5 * k)) for k in range(1, 7))
    return x * np.minimum(1, t / 0.002) * 0.16


def pad(notes, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for note in notes:
        f = midi(note)
        for det in (-0.09, 0.0, 0.08):
            ff = f * 2 ** (det / 12)
            ph = rng.uniform(0, 1)
            x += 2 * ((ff * t + ph) % 1.0) - 1  # saw
    x = sosfilt(sos("lowpass", 1400, 2), x) / (len(notes) * 3)
    e = np.minimum(1, t / 0.25) * np.minimum(1, (dur - t) / 0.3).clip(0)
    return x * e * 0.35


# ---------------------------------------------------------------- arrangement
# A minor: Am7 Fmaj7 C G | Am7 Fmaj7 Gsus-G  (7 bars, resolves back to bar 1)
CHORDS = [
    (45, [57, 60, 64, 67]),  # Am7
    (41, [57, 60, 64, 65]),  # Fmaj7
    (48, [55, 60, 64, 67]),  # C
    (43, [55, 59, 62, 67]),  # G
    (45, [57, 60, 64, 67]),  # Am7
    (41, [57, 60, 64, 65]),  # Fmaj7
    (43, [55, 60, 62, 67]),  # Gsus4 -> G (bar 7)
]
ARP = [0, 2, 1, 3, 2, 1, 3, 2]  # indices into chord tones, 8ths

L = N + TAIL
drums = np.zeros(L)
music = np.zeros(L)
K, H, HO, C = kick(), hat(), hat(True), clap()

for bar in range(BARS):
    root, tones = CHORDS[bar]
    t0 = bar * 4 * BEAT
    for b in range(4):
        tb = t0 + b * BEAT
        place(drums, K, tb)
        place(drums, HO if b == 3 else H, tb + BEAT / 2, 0.9)
        place(drums, H, tb + BEAT * 0.75, 0.35)
        if b in (1, 3):
            place(drums, C, tb)
        # offbeat bass, octave pop on the last 16th of the bar
        place(music, bass(root, BEAT * 0.45), tb + BEAT / 2)
    place(music, bass(root + 12, BEAT * 0.2), t0 + 3.75 * BEAT, 0.6)
    place(music, pad(tones, 4 * BEAT + 0.3), t0)
    for k in range(8):
        note = tones[ARP[k]] + 12
        place(music, pluck(note), t0 + k * BEAT / 2, 0.8 if k % 2 else 1.0)

# sidechain pump on the musical bed, keyed from the kick grid
t = np.arange(L) / SR
phase = (t % BEAT) / BEAT
duck = 1 - 0.55 * np.exp(-phase * 9)
music *= duck

mix = drums + music
# fold the tail back onto the start so the loop point is seamless
loop = mix[:N].copy()
loop[: L - N] += mix[N:]

# gentle bus: highpass rumble, soft clip, normalise to -1 dBFS
loop = sosfilt(sos("highpass", 28), loop)
loop = np.tanh(loop * 1.2)
loop *= 10 ** (-1 / 20) / np.max(np.abs(loop))

stereo = np.stack([loop, loop], axis=1)
out = os.path.join(HERE, "music.wav")
with wave.open(out, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((stereo * 32767).astype("<i2").tobytes())
print(f"wrote {out}  {LOOP:.2f}s  {BPM} BPM  {BARS} bars")
