#!/usr/bin/env python3
"""EXP Logo Sting soundtrack — 3.6 s, 150 BPM, hits on every reference cut."""
import numpy as np
import wave

SR = 44100
DUR = 3.6
N = int(SR * DUR)
L = np.zeros(N)
R = np.zeros(N)
KL = np.zeros(N)
KR = np.zeros(N)
rng = np.random.default_rng(23)


def put(sig, t0, gain=1.0, pan=0.0, drums=False):
    i0 = int(t0 * SR)
    if i0 >= N or i0 < 0:
        return
    n = min(len(sig), N - i0)
    (KL if drums else L)[i0:i0 + n] += sig[:n] * gain * min(1, 1 - pan)
    (KR if drums else R)[i0:i0 + n] += sig[:n] * gain * min(1, 1 + pan)


def env(n, a, d, curve=5.0):
    x = np.arange(n) / SR
    return np.minimum(x / max(a, 1e-4), 1.0) * np.exp(-np.maximum(x - a, 0) * curve / max(d, 1e-3))


def lowpass(sig, fc):
    S = np.fft.rfft(sig); f = np.fft.rfftfreq(len(sig), 1 / SR)
    return np.fft.irfft(S / (1 + (f / fc) ** 4), len(sig))


def highpass(sig, fc):
    S = np.fft.rfft(sig); f = np.fft.rfftfreq(len(sig), 1 / SR)
    return np.fft.irfft(S * (f / fc) ** 4 / (1 + (f / fc) ** 4), len(sig))


def bandpass(sig, lo, hi):
    return highpass(lowpass(sig, hi), lo)


def kick(dur=0.3):
    n = int(dur * SR); x = np.arange(n) / SR
    body = np.sin(2 * np.pi * np.cumsum(44 + 130 * np.exp(-x * 36)) / SR) * np.exp(-x * 12)
    click = highpass(rng.standard_normal(int(0.004 * SR)), 2800) * 0.8
    out = body.copy(); out[:len(click)] += click
    return np.tanh(out * 1.7) * 0.92


def hat(dur=0.05, tone=7500):
    n = int(dur * SR)
    return highpass(rng.standard_normal(n), tone) * env(n, 0.001, 0.016, 6) * 1.3


def boom(dur=0.7, f0=50):
    n = int(dur * SR); x = np.arange(n) / SR
    body = np.sin(2 * np.pi * np.cumsum(f0 * (1 + 0.6 * np.exp(-x * 20))) / SR) * np.exp(-x * 6)
    th = lowpass(rng.standard_normal(n), 300) * np.exp(-x * 14) * 0.6
    return np.tanh((body + th) * 1.8) * 0.95


def whoosh(dur=0.16, lo=600, hi=4200):
    n = int(dur * SR); x = np.arange(n) / SR
    return bandpass(rng.standard_normal(n), lo, hi) * np.sin(np.pi * np.minimum(x / dur, 1)) ** 2 * 0.8


def tickk(hz=2400, dur=0.05):
    n = int(dur * SR); x = np.arange(n) / SR
    return np.sin(2 * np.pi * hz * x) * np.exp(-x * 200) + highpass(rng.standard_normal(n), 3600) * np.exp(-x * 420) * 0.4


def sub_note(f, dur):
    n = int(dur * SR); x = np.arange(n) / SR
    e = np.minimum(x / 0.01, 1) * np.minimum((dur - x) / 0.05, 1).clip(0, 1)
    return np.tanh((np.sin(2 * np.pi * f * x) + 0.15 * np.sin(4 * np.pi * f * x)) * 1.4) * e * 0.8


def chime(freqs, dur=0.8):
    n = int(dur * SR); x = np.arange(n) / SR
    sig = np.zeros(n)
    for i, f in enumerate(freqs):
        d = 0.05 * i; m = x > d
        sig[m] += (np.sin(2 * np.pi * f * (x[m] - d)) + 0.3 * np.sin(2 * np.pi * 2.01 * f * (x[m] - d))) * np.exp(-(x[m] - d) * 6)
    return sig * 0.5


def riser(dur=0.5):
    n = int(dur * SR); x = np.arange(n) / SR
    return bandpass(rng.standard_normal(n), 700, 7000) * (x / dur) ** 2.2 * 0.5


BEAT = 0.4  # 150 BPM
A1 = 55.0
for b in range(9):
    tb = b * BEAT
    if tb < 3.25:
        put(kick(), tb, 0.95, drums=True)
    put(hat(), tb + 0.2, 0.3, pan=0.3)
    put(hat(dur=0.03, tone=9200), tb + 0.3, 0.12, pan=-0.35)
for tb in (0.8, 1.6, 2.4):
    n = int(0.2 * SR)
    put(bandpass(rng.standard_normal(n), 1000, 4500) * env(n, 0.001, 0.08, 6), tb, 0.45, pan=-0.1)
for k in range(8):
    put(sub_note(A1, 0.3), k * 0.4 + 0.2, 0.5)

CUT_TIMES = [0.37, 0.60, 0.87, 1.07, 1.23, 1.40, 1.60, 1.90, 2.10, 2.30, 2.53, 2.73]
for i, tc in enumerate(CUT_TIMES):
    put(whoosh(), tc, 0.42, pan=(-1) ** i * 0.2)
    put(tickk(2200 + (i % 4) * 250), tc, 0.3)
put(boom(0.7), 0.0, 0.65, drums=True)
put(riser(0.45), 2.52, 0.5)
put(boom(0.9, 46), 2.945, 0.95, drums=True)              # closing macro hit
n = int(1.0 * SR); x = np.arange(n) / SR
put(highpass(rng.standard_normal(n), 4200) * np.exp(-x * 5) * 0.9, 2.97, 0.3)
put(chime([440, 554, 659], 0.6), 3.0, 0.5)
put(sub_note(A1, 0.55), 2.97, 0.5)

duck = np.ones(N)
for b in range(9):
    i0 = int(b * BEAT * SR); n = int(0.22 * SR)
    x = np.arange(min(n, N - i0)) / SR
    duck[i0:i0 + len(x)] *= 1 - 0.42 * np.exp(-x * 14)
L *= duck; R *= duck
L += KL; R += KR

mix = np.stack([L, R])
mix = np.tanh(mix * 1.3)
mix *= 0.97 / np.max(np.abs(mix))
nf = int(0.012 * SR)
fade = np.linspace(0, 1, nf)
mix[:, :nf] = mix[:, :nf] * fade + mix[:, -nf:] * (1 - fade)
mix[:, -nf:] *= np.linspace(1, 0, nf)
out = (mix.T * 32767).astype(np.int16)
with wave.open('/tmp/exp-sting.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(out.tobytes())
print('wrote /tmp/exp-sting.wav')
