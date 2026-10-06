"""Sound design for "The Path" (royalty-free: generated here) -> audio/sfx/<name>.wav

Playful and soft: pops, slaps, hops, coin clinks, a hotel bell, a monster chomp.
mix.py places each file so its measured peak lands on its cue.
"""
import os
import wave

import numpy as np
from scipy.signal import butter, sosfilt

SR = 48000
DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sfx")
rng = np.random.default_rng(8)


def T(sec):
    return np.arange(int(sec * SR)) / SR


def bp(x, lo, hi):
    return sosfilt(butter(2, [lo, min(hi, 23000)], btype="bandpass", fs=SR, output="sos"), x)


def tone(f, sec, decay, f_end=None, harm=()):
    t = T(sec)
    ff = np.full_like(t, f) if f_end is None else f * (f_end / f) ** (t / sec)
    ph = 2 * np.pi * np.cumsum(ff) / SR
    x = np.sin(ph) + sum(a * np.sin(k * ph) for k, a in harm)
    return x * np.exp(-t * decay) * np.minimum(1, t / 0.002)


def noise(sec, lo, hi, decay):
    t = T(sec)
    return bp(rng.standard_normal(len(t)), lo, hi) * np.exp(-t * decay)


def mix(*xs):
    n = max(len(x) for x in xs)
    return sum(np.pad(x, (0, n - len(x))) for x in xs)


def at(x, sec):
    return np.pad(x, (int(sec * SR), 0))


def sweep(sec, f0, f1, shape=2.0, rise=True):
    t = T(sec)
    x, out, steps = rng.standard_normal(len(t)), np.zeros(len(t)), 18
    seg = len(t) // steps
    for k in range(steps):
        fc = f0 * (f1 / f0) ** (k / (steps - 1))
        a, b = k * seg, (k + 1) * seg if k < steps - 1 else len(t)
        out[a:b] = bp(x, fc * 0.6, fc * 1.6)[a:b]
    return out * ((t / sec) ** shape if rise else (1 - t / sec) ** shape)


S = {
    "pop": mix(tone(520, 0.12, 30, 980), noise(0.006, 2000, 7000, 700) * 0.3) * 0.5,
    "slap": mix(noise(0.05, 400, 4000, 70) * 0.7, tone(160, 0.12, 30) * 0.5),
    "tick": tone(2400, 0.03, 160) * 0.3,
    "rise": mix(tone(260, 0.22, 10, 520) * 0.35, sweep(0.18, 800, 3000, 1.5) * 0.15),
    "whoosh": sweep(0.3, 400, 5000, 1.5) * 0.4,
    "swish": sweep(0.2, 2500, 9000, 1.2) * 0.3,
    "swell": sweep(0.55, 200, 5000, 2.4) * 0.35,
    "hop": tone(330, 0.09, 24, 660) * 0.3,
    "counter": mix(*[at(tone(1800 + 40 * k, 0.025, 200) * 0.18, k * 0.024) for k in range(22)]),
    "card": mix(sweep(0.14, 1500, 6000, 1.0) * 0.25, at(tone(880, 0.06, 60) * 0.25, 0.12)),
    "drip": mix(*[at(tone(900 + 120 * k, 0.07, 40, 1500 + 120 * k) * 0.22, k * 0.04) for k in range(5)]),
    "chomp": mix(tone(110, 0.25, 14, 70) * 0.8, noise(0.08, 300, 2500, 40) * 0.6, at(noise(0.04, 300, 2500, 60) * 0.5, 0.09)),
    "flick": tone(1200, 0.05, 70, 1800) * 0.25,
    "coin": mix(tone(2093, 0.4, 9, harm=((2.76, 0.4), (5.4, 0.2))) * 0.25, at(tone(2637, 0.35, 10, harm=((2.76, 0.3),)) * 0.2, 0.05)),
    "stamps": mix(*[at(mix(noise(0.02, 300, 3000, 150) * 0.4, tone(220, 0.04, 70) * 0.3), k * 0.0214) for k in range(20)]) * 0.6,
    "snap": mix(noise(0.008, 2500, 9000, 600) * 0.5, tone(1400, 0.04, 90) * 0.3),
    "drop": mix(tone(800, 0.14, 20, 300) * 0.35, at(tone(140, 0.12, 30) * 0.5, 0.1)),
    "ding": mix(tone(1567, 1.2, 3.5, harm=((2.0, 0.3), (3.01, 0.15), (4.2, 0.08))) * 0.35, noise(0.004, 3000, 9000, 900) * 0.4),
    "shimmer": mix(*[at(tone(1046 * 2 ** (k / 12 * 2.4), 0.5, 6) * 0.08, k * 0.035) for k in range(12)]),
}
for i, f in enumerate([523, 587, 659, 784, 880]):
    S[f"pop{i}"] = mix(tone(f, 0.14, 26, f * 1.6), noise(0.006, 2000, 7000, 700) * 0.3) * 0.45

os.makedirs(DIR, exist_ok=True)
for name, x in S.items():
    x = np.concatenate([np.zeros(48), x])
    x = x * np.minimum(1, np.arange(len(x))[::-1] / (0.004 * SR))
    with wave.open(os.path.join(DIR, f"{name}.wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype("<i2").tobytes())
print(f"{len(S)} sounds -> {DIR}")
