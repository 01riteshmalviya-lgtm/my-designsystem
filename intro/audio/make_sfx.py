"""Synthesize the intro's sound design (royalty-free: generated here) -> audio/sfx/<name>.wav

mix.py places each file so its measured peak lands on its cue.
"""
import os
import wave

import numpy as np
from scipy.signal import butter, sosfilt

SR = 48000
DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sfx")
rng = np.random.default_rng(5)


def T(sec):
    return np.arange(int(sec * SR)) / SR


def bp(x, lo, hi):
    return sosfilt(butter(2, [lo, min(hi, 23000)], btype="bandpass", fs=SR, output="sos"), x)


def tone(f, sec, decay, f_end=None):
    t = T(sec)
    ff = np.full_like(t, f) if f_end is None else f * (f_end / f) ** (t / sec)
    return np.sin(2 * np.pi * np.cumsum(ff) / SR) * np.exp(-t * decay)


def noise(sec, lo, hi, decay):
    t = T(sec)
    return bp(rng.standard_normal(len(t)), lo, hi) * np.exp(-t * decay)


def mix(*xs):
    n = max(len(x) for x in xs)
    return sum(np.pad(x, (0, n - len(x))) for x in xs)


def sweep(sec, f0, f1, shape=2.0, rise=True):
    """band-passed noise whose centre glides f0 -> f1; loudest at the end when rise=True"""
    t = T(sec)
    x = rng.standard_normal(len(t))
    out = np.zeros_like(x)
    steps = 20
    seg = len(t) // steps
    for k in range(steps):
        fc = f0 * (f1 / f0) ** (k / (steps - 1))
        a, b = k * seg, (k + 1) * seg if k < steps - 1 else len(t)
        out[a:b] = bp(x, fc * 0.6, fc * 1.6)[a:b]
    env = (t / sec) ** shape if rise else (1 - t / sec) ** shape
    return out * env


S = {
    "blip": mix(tone(1320, 0.18, 22) * 0.4, tone(2640, 0.1, 40) * 0.12),
    "key": mix(noise(0.018, 1800, 5500, 280) * 0.5, tone(330, 0.025, 170) * 0.3),
    "slam": mix(tone(150, 0.35, 11, 45) * 0.9, noise(0.06, 200, 3000, 60) * 0.5, noise(0.015, 3000, 9000, 300) * 0.35),
    "whoosh": mix(sweep(0.32, 300, 4500, 1.6), np.zeros(int(0.05 * SR))) * 0.5,
    "swish": sweep(0.22, 2500, 9000, 1.2) * 0.35,
    "swell": sweep(0.6, 200, 6000, 2.6) * 0.45,
    "stretch": mix(tone(180, 0.45, 5, 420) * 0.35, sweep(0.4, 400, 2500, 1.5) * 0.2),
    "drop": mix(tone(900, 0.16, 18, 300) * 0.35, tone(120, 0.18, 25) * 0.5),
    "split": mix(*[np.pad(tone(1800 + 200 * k, 0.04, 120) * 0.22, (int(k * 0.012 * SR), 0)) for k in range(5)]),
    "lock": mix(noise(0.01, 2000, 7000, 500) * 0.5, tone(700, 0.08, 50) * 0.4,
                np.pad(mix(noise(0.01, 2000, 7000, 500) * 0.4, tone(1050, 0.08, 50) * 0.3), (int(0.06 * SR), 0))),
    "sparkle": mix(*[np.pad(tone(2000 + 220 * k, 0.12, 40) * 0.16, (int(k * 0.016 * SR), 0)) for k in range(12)]),
    "ticks": mix(*[np.pad(tone(2600, 0.02, 300) * 0.2, (int(k * 0.03 * SR), 0)) for k in range(14)]),
    "burst": mix(tone(110, 0.6, 7, 40) * 0.8, noise(0.4, 3000, 12000, 9) * 0.25,
                 *[np.pad(tone(2400 + 300 * k, 0.08, 60) * 0.08, (int(k * 0.02 * SR), 0)) for k in range(10)]),
    "pop": tone(420, 0.12, 30, 900) * 0.5,
}
for i, f in enumerate([523, 587, 659, 784, 880]):        # pills: a rising pentatonic
    S[f"pop{i}"] = mix(tone(f, 0.14, 26, f * 1.5) * 0.45, noise(0.008, 2000, 6000, 600) * 0.3)
S["sweep"] = sweep(0.5, 300, 5000, 1.0, rise=False) * 0.3

os.makedirs(DIR, exist_ok=True)
for name, x in S.items():
    x = np.concatenate([np.zeros(48), x])                 # 1 ms lead-in so the peak is never sample 0
    x = x * np.minimum(1, np.arange(len(x))[::-1] / (0.004 * SR))
    with wave.open(os.path.join(DIR, f"{name}.wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype("<i2").tobytes())
print(f"{len(S)} sounds -> {DIR}")
