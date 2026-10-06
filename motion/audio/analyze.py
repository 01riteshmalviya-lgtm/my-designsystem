"""Measure the beat grid of the song with numpy and pick the downbeat to start on.

    python3 audio/analyze.py [song]   ->  out/beats.json

Uses audio/song.* if present (a real Mixkit track), else audio/music.wav.
Steps: spectral-flux onset envelope -> tempo by autocorrelation -> beat phase
by comb sum -> per-beat peak refinement + linear fit -> downbeat by harmonic
(chroma) novelty, since chords change on the one.
"""
import glob
import json
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "out")
SR = 48000
HOP = 256
WIN = 2048
LOOP_BEATS = 28  # 7 bars


def load(path):
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
        check=True, capture_output=True,
    ).stdout
    return np.frombuffer(raw, dtype="<f4").astype(np.float64)


def stft_mag(x):
    w = np.hanning(WIN)
    pad = np.concatenate([np.zeros(WIN // 2), x, np.zeros(WIN)])
    n = 1 + (len(pad) - WIN) // HOP
    idx = np.arange(WIN)[None, :] + HOP * np.arange(n)[:, None]
    return np.abs(np.fft.rfft(pad[idx] * w, axis=1))


def onset_env(mag):
    lm = np.log1p(100 * mag)
    flux = np.maximum(0, np.diff(lm, axis=0, prepend=lm[:1])).sum(axis=1)
    k = int(0.4 * SR / HOP)
    flux = flux - np.convolve(flux, np.ones(k) / k, mode="same")
    flux = np.maximum(flux, 0)
    return flux / (flux.max() + 1e-12)


def tempo(env, lo=80, hi=170, prior=120):
    fps = SR / HOP
    e = env - env.mean()
    ac = np.correlate(e, e, mode="full")[len(e) - 1:]
    lags = np.arange(int(fps * 60 / hi), int(fps * 60 / lo) + 1)
    bpms = 60 * fps / lags
    weight = np.exp(-0.5 * (np.log2(bpms / prior) / 0.6) ** 2)
    score = ac[lags] * weight
    i = int(np.argmax(score))
    # parabolic refinement of the lag
    if 0 < i < len(lags) - 1:
        a, b, c = ac[lags[i - 1]], ac[lags[i]], ac[lags[i + 1]]
        d = 0.5 * (a - c) / (a - 2 * b + c + 1e-12)
    else:
        d = 0.0
    return (lags[i] + d) / fps  # period in seconds


def interp(env, t):
    f = t * SR / HOP
    return np.interp(f, np.arange(len(env)), env, left=0, right=0)


def main():
    cands = sorted(glob.glob(os.path.join(HERE, "song.*")))
    path = sys.argv[1] if len(sys.argv) > 1 else (cands[0] if cands else os.path.join(HERE, "music.wav"))
    x = load(path)
    dur = len(x) / SR
    mag = stft_mag(x)
    env = onset_env(mag)
    period = tempo(env)

    # phase: comb over the whole file
    phases = np.linspace(0, period, 400, endpoint=False)
    nb = int(dur / period)
    scores = [interp(env, p + period * np.arange(nb)).sum() for p in phases]
    phase = phases[int(np.argmax(scores))]
    # half-beat ambiguity (offbeat bass/hats): the beat is where the low band hits
    freqs = np.fft.rfftfreq(WIN, 1 / SR)
    low = onset_env(mag[:, freqs < 150])
    if interp(low, (phase + period / 2) % period + period * np.arange(nb - 1)).sum() > \
            interp(low, phase + period * np.arange(nb - 1)).sum():
        phase = (phase + period / 2) % period
    if phase > period - 0.03:  # a beat sitting right on t=0
        phase -= period
    nb = int((dur - phase) / period + 0.5)

    # refine each beat to its measured onset peak, then least-squares the grid
    grid = phase + period * np.arange(nb)
    fps = SR / HOP
    # fine onset curve at 0.5 ms: rise of log energy in 2 ms windows (STFT frames are too coarse)
    h = SR // 2000
    e2 = np.log1p(1e4 * np.convolve(x ** 2, np.ones(4 * h) / (4 * h), mode="same")[::h])
    rise = np.maximum(0, np.diff(e2, prepend=e2[0]))
    meas = []
    for t in grid:
        a, b = int((t - 0.03) * 2000), int((t + 0.03) * 2000) + 1
        a = max(a, 0)
        if b <= a or b > len(rise):
            meas.append(t)
            continue
        meas.append((a + int(np.argmax(rise[a:b]))) / 2000)
    meas = np.array(meas)
    A = np.stack([np.ones(nb), np.arange(nb)], axis=1)
    (off, per), *_ = np.linalg.lstsq(A, meas, rcond=None)
    beats = off + per * np.arange(nb)
    jitter = np.abs(meas - beats)

    # downbeat: harmonic novelty between consecutive beats (chroma), averaged per bar phase
    band = (freqs > 55) & (freqs < 2000)
    pc = np.round(12 * np.log2(freqs[band] / 440.0)).astype(int) % 12
    chroma_frames = np.zeros((mag.shape[0], 12))
    for c in range(12):
        chroma_frames[:, c] = mag[:, band][:, pc == c].sum(axis=1)
    bch = []
    for i in range(nb):
        a = int(beats[i] * fps)
        b = int((beats[i] + per) * fps)
        v = chroma_frames[max(a, 0):max(b, a + 1)].mean(axis=0)
        bch.append(v / (np.linalg.norm(v) + 1e-12))
    bch = np.array(bch)
    nov = np.r_[0, 1 - (bch[1:] * bch[:-1]).sum(axis=1)]
    if nb >= LOOP_BEATS:  # treat as circular when the file is exactly one loop
        nov[0] = 1 - bch[0] @ bch[-1]
    dscore = [nov[p::4].mean() for p in range(4)]
    dphase = int(np.argmax(dscore))

    # start: the downbeat whose following 7 bars are loudest (earliest on ties)
    rms = np.sqrt(np.convolve(x ** 2, np.ones(SR // 10) / (SR // 10), mode="same"))
    loop_len = LOOP_BEATS * per
    starts = [beats[i] for i in range(dphase, nb, 4) if beats[i] + loop_len <= dur + per * 0.5]
    if not starts:
        starts = [beats[dphase]]
    energy = [rms[int(max(s, 0) * SR):int(min(s + loop_len, dur) * SR)].mean() for s in starts]
    best = int(np.argmax(np.round(np.array(energy) / max(energy), 2)))
    start = max(float(starts[best]), 0.0)
    circular = abs(dur - loop_len) < per / 4
    if circular:  # the file is one seamless loop: take the downbeat nearest 0, wrapping
        bar = 4 * per
        start = float(beats[dphase] - bar * np.round(beats[dphase] / bar))

    res = {
        "source": os.path.relpath(path, os.path.join(HERE, "..")),
        "duration": round(dur, 4),
        "bpm": round(60 / per, 3),
        "period": per,
        "first_beat": float(beats[0]),
        "downbeat_phase": dphase,
        "start": start,
        "circular": bool(circular),
        "loop_seconds": loop_len,
        "beat_jitter_ms": {"mean": round(1000 * jitter.mean(), 2), "max": round(1000 * jitter.max(), 2)},
        "downbeat_scores": [round(float(s), 4) for s in dscore],
        "beats": [round(float(b), 5) for b in beats],
    }
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "beats.json"), "w") as f:
        json.dump(res, f, indent=1)
    print(f"{res['source']}: {res['bpm']} BPM, start on downbeat at {start:.4f}s, "
          f"jitter mean {res['beat_jitter_ms']['mean']}ms max {res['beat_jitter_ms']['max']}ms, "
          f"downbeat scores {res['downbeat_scores']} -> phase {dphase}")


if __name__ == "__main__":
    main()
