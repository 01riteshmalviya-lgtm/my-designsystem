"""Synthesize the intro score: 128 BPM, 8 bars, one musical idea per section (royalty-free: generated here).

    python3 audio/make_music.py  ->  audio/music.wav   (8 bars + a 1 s tail for the final hit)

Arrangement follows the picture: bar 1 sparse (no kick), drums from bar 2, arp from bar 5,
riser into bar 7, a stab on every beat of bar 7, impacts on bar 8's one and on the hand-off (beat 32).
"""
import os
import wave

import numpy as np
from scipy.signal import butter, sosfilt

SR = 48000
BPM = 128
BEAT = 60 / BPM
BARS = 8
END = BARS * 4 * BEAT          # 15.0 s
TOTAL = END + 1.0              # hold on the cover
N = int(round(TOTAL * SR))
rng = np.random.default_rng(11)
HERE = os.path.dirname(os.path.abspath(__file__))


def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def sos(kind, f, order=2):
    return butter(order, f, btype=kind, fs=SR, output="sos")


def T(sec):
    return np.arange(int(sec * SR)) / SR


def place(buf, x, t, gain=1.0):
    i = int(round(t * SR))
    if i < 0:
        x, i = x[-i:], 0
    j = min(len(buf), i + len(x))
    if j > i:
        buf[i:j] += gain * x[: j - i]


def kick(punch=1.0):
    t = T(0.5)
    f = 44 + 120 * np.exp(-t * 30)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 6.5)
    click = sosfilt(sos("highpass", 2000), rng.standard_normal(len(t))) * np.exp(-t * 280) * 0.3
    return np.tanh(1.8 * punch * (body + click)) * 0.9


def clap():
    t = T(0.3)
    n = sosfilt(sos("bandpass", [900, 3500]), rng.standard_normal(len(t)))
    e = sum((t >= o) * np.exp(-np.clip(t - o, 0, None) * (170 if k < 2 else 20)) for k, o in enumerate([0, .01, .021]))
    return n * e * 0.4


def hat(open_=False):
    t = T(0.18 if open_ else 0.05)
    return sosfilt(sos("highpass", 8000, 4), rng.standard_normal(len(t))) * np.exp(-t * (24 if open_ else 100)) * 0.2


def bass(note, dur):
    t = T(dur)
    f = midi(note)
    x = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(4 * np.pi * f * t + 0.3)
    e = np.minimum(1, t / 0.004) * np.exp(-t * 2.5) * np.clip((dur - t) / 0.012, 0, 1)
    return np.tanh(1.6 * x * e) * 0.45


def saw_voice(f, t, det=(-0.08, 0, 0.08)):
    return sum(2 * ((f * 2 ** (d / 12) * t + rng.uniform()) % 1) - 1 for d in det) / len(det)


def pad(notes, dur, cutoff=1600):
    t = T(dur)
    x = sum(saw_voice(midi(n), t) for n in notes) / len(notes)
    x = sosfilt(sos("lowpass", cutoff), x)
    return x * np.minimum(1, t / 0.2) * np.clip((dur - t) / 0.25, 0, 1) * 0.32


def stab(notes, dur=0.32, cutoff=3200):
    t = T(dur)
    x = sum(saw_voice(midi(n), t) for n in notes) / len(notes)
    x = sosfilt(sos("lowpass", cutoff), x)
    return x * np.minimum(1, t / 0.002) * np.exp(-t * 9) * 0.55


def pluck(note, dur=0.3):
    t = T(dur)
    f = midi(note)
    x = sum(np.sin(2 * np.pi * f * k * t) / k ** 1.5 * np.exp(-t * (7 + 6 * k)) for k in range(1, 7))
    return x * np.minimum(1, t / 0.002) * 0.17


def sub_boom(dur=1.6):
    t = T(dur)
    f = 32 + 60 * np.exp(-t * 6)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.2) * 0.9


def crash(dur=1.8):
    t = T(dur)
    x = sosfilt(sos("highpass", 4000, 2), rng.standard_normal(len(t)))
    return x * np.exp(-t * 2.6) * 0.18


def riser(dur):
    t = T(dur)
    x = rng.standard_normal(len(t))
    out = np.zeros_like(x)
    seg = len(t) // 24
    for k in range(24):  # stepped band-pass sweep
        a, b = k * seg, (k + 1) * seg if k < 23 else len(t)
        fc = 300 * (12000 / 300) ** (k / 23)
        out[a:b] = sosfilt(sos("bandpass", [fc * 0.7, min(fc * 1.4, 20000)]), x)[a:b]
    return out * (t / dur) ** 2.2 * 0.22


# D minor: Dm Bb F C | Dm Bb Gm A | (bar 8) Dm
CH = [(38, [62, 65, 69]), (34, [62, 65, 70]), (41, [60, 65, 69]), (36, [60, 64, 67]),
      (38, [62, 65, 69]), (34, [62, 65, 70]), (43, [62, 67, 70]), (45, [61, 64, 69])]
FIN = (38, [62, 65, 69, 74])
ARP = [0, 1, 2, 1, 2, 0, 1, 2]

drums = np.zeros(N)
bed = np.zeros(N)
fx = np.zeros(N)

for bar in range(BARS):
    t0 = bar * 4 * BEAT
    root, tones = CH[bar] if bar < 7 else FIN
    if bar == 0:
        place(bed, pad(tones, 4 * BEAT + 0.2, 900), t0, 0.9)
        for b in range(4):
            place(bed, pluck(tones[b % 3] + 12), t0 + b * BEAT, 1.2)
        place(fx, riser(BEAT * 1.0), t0 + 3 * BEAT, 0.8)        # into the iris
        continue
    if bar == 6:                                                  # kinetic type: a stab on every beat
        for b in range(4):
            tb = t0 + b * BEAT
            place(drums, kick(1.15), tb)
            place(bed, stab([n + 12 for n in tones] + [tones[0]]), tb, 1.0)
            place(bed, bass(root, BEAT * 0.9), tb, 0.9)
            place(drums, hat(), tb + BEAT / 2, 0.8)
        place(drums, clap(), t0 + 3.5 * BEAT, 0.9)
        continue
    for b in range(4):
        tb = t0 + b * BEAT
        place(drums, kick(), tb)
        place(drums, hat(b == 3), tb + BEAT / 2, 0.9)
        place(drums, hat(), tb + BEAT * 0.75, 0.35)
        if b in (1, 3):
            place(drums, clap(), tb)
        place(bed, bass(root, BEAT * 0.42), tb + BEAT / 2)
    place(bed, pad(tones, 4 * BEAT + 0.2), t0, 0.8)
    if bar >= 4:                                                  # systems/depth: 8th-note arp
        for k in range(8):
            place(bed, pluck(tones[ARP[k]] + 12), t0 + k * BEAT / 2, 0.8)
    if bar == 5:
        place(fx, riser(BEAT * 2), t0 + 2 * BEAT, 1.0)            # warp into the kinetic bar

# bar 8 impact and the hand-off hit
for at, g in ((7 * 4 * BEAT, 1.0), (31 * BEAT, 1.25)):
    place(fx, sub_boom(), at, g)
    place(fx, crash(), at, g)
    place(fx, stab([n + 12 for n in FIN[1]] + [FIN[0] + 12], 1.2, 2400), at, 0.8 * g)
# everything but the final hit stops at the hand-off
cut = int(round(31 * BEAT * SR))
fade = np.ones(N)
fade[cut:] = np.exp(-np.arange(N - cut) / (0.05 * SR))
drums *= fade
bed *= fade

# sidechain the bed to the kick grid (from bar 2), keep the final hit ringing
t = np.arange(N) / SR
duck = np.where((t >= 4 * BEAT) & (t < 31 * BEAT), 1 - 0.5 * np.exp(-((t % BEAT) / BEAT) * 9), 1.0)
bed = bed * duck

mix = drums + bed + fx
mix = sosfilt(sos("highpass", 25), mix)
mix = np.tanh(mix * 1.3)
mix[-int(0.25 * SR):] *= np.linspace(1, 0, int(0.25 * SR))
mix *= 10 ** (-1 / 20) / np.max(np.abs(mix))
st = np.stack([mix, mix], 1)
with wave.open(os.path.join(HERE, "music.wav"), "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((st * 32767).astype("<i2").tobytes())
print(f"wrote audio/music.wav  {TOTAL:.2f}s  {BPM} BPM  {BARS} bars + tail")
