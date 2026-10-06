"""Synthesize the UI sounds (royalty-free: generated here) -> audio/sfx/<name>.wav

Swap any file for a Mixkit SFX of the same name; mix.py aligns each by its measured peak.
"""
import os
import wave

import numpy as np
from scipy.signal import butter, sosfilt

SR = 48000
HERE = os.path.dirname(os.path.abspath(__file__))
DIR = os.path.join(HERE, "sfx")
rng = np.random.default_rng(3)


def T(sec):
    return np.arange(int(sec * SR)) / SR


def bp(x, lo, hi):
    return sosfilt(butter(2, [lo, hi], btype="bandpass", fs=SR, output="sos"), x)


def tone(f, sec, decay, f_end=None):
    t = T(sec)
    f = np.full_like(t, f) if f_end is None else f * (f_end / f) ** (t / sec)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * decay)


def noise(sec, lo, hi, decay):
    t = T(sec)
    return bp(rng.standard_normal(len(t)), lo, hi) * np.exp(-t * decay)


def pre(x, ms=1.0):
    """short silent lead-in so the measured peak is never sample 0"""
    return np.concatenate([np.zeros(int(ms * SR / 1000)), x])


def mix(*xs):
    n = max(len(x) for x in xs)
    return sum(np.pad(x, (0, n - len(x))) for x in xs)


S = {
    "click": mix(noise(0.012, 2500, 7000, 420) * 0.6, tone(1750, 0.05, 140) * 0.5, tone(420, 0.04, 110) * 0.35),
    "grab": mix(noise(0.01, 1200, 4000, 500) * 0.35, tone(900, 0.05, 120) * 0.4),
    "release": mix(noise(0.008, 2000, 6000, 600) * 0.3, tone(1300, 0.04, 150) * 0.35),
    "detent": tone(2600, 0.02, 330) * 0.28,
    "limit": mix(tone(1400, 0.05, 120) * 0.4, tone(700, 0.08, 70) * 0.4, noise(0.01, 1500, 5000, 500) * 0.3),
    "toggle": mix(tone(640, 0.09, 55, 520) * 0.55, noise(0.015, 1800, 6000, 350) * 0.45, tone(1900, 0.03, 200) * 0.25),
    "tick": mix(tone(2200, 0.025, 260) * 0.35, noise(0.006, 3000, 8000, 900) * 0.25),
    "key": mix(noise(0.02, 1800, 5200, 260) * 0.55, tone(310, 0.03, 160) * 0.35),
    "pop": tone(480, 0.09, 45, 920) * 0.5,
}
# success: two-note bell (E6 -> A6)
bell = lambda f: sum(tone(f * k, 0.6, 7 + 4 * k) / k ** 1.4 for k in (1, 2, 3))
S["success"] = mix(bell(1318.5) * 0.32, np.pad(bell(1760.0) * 0.28, (int(0.08 * SR), 0)))
# swell: airy rise into the morph, peak at the end so the peak lands on the beat
t = T(0.32)
sw = rng.standard_normal(len(t))
sw = bp(sw, 500, 3500) * (t / t[-1]) ** 3
S["swell"] = np.concatenate([sw, sw[-1] * np.exp(-T(0.08) * 60)]) * 0.18

os.makedirs(DIR, exist_ok=True)
for name, x in S.items():
    x = pre(x)
    x = x * np.minimum(1, np.arange(len(x))[::-1] / (0.004 * SR))  # declick tail
    with wave.open(os.path.join(DIR, f"{name}.wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype("<i2").tobytes())
print(f"{len(S)} sounds -> {DIR}")
