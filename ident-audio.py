#!/usr/bin/env python3
"""EXP Ident soundtrack — 5.0 s, 120 BPM, cinema dive/blast transitions."""
import numpy as np
import wave

SR = 44100
DUR = 5.0
N = int(SR * DUR)
L = np.zeros(N)
R = np.zeros(N)
KL = np.zeros(N)
KR = np.zeros(N)
rng = np.random.default_rng(31)


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


BEAT = 0.5  # 120 BPM
A1 = 55.0
for b in range(10):
    tb = b * BEAT
    if b != 9:
        put(kick(), tb, 0.95, drums=True)
    put(hat(), tb + 0.25, 0.3, pan=0.3)
    put(hat(dur=0.03, tone=9200), tb + 0.375, 0.12, pan=-0.35)
for tb in (0.5, 1.5, 2.5, 3.5):
    n = int(0.2 * SR)
    put(bandpass(rng.standard_normal(n), 1000, 4500) * env(n, 0.001, 0.08, 6), tb, 0.45, pan=-0.1)
for k in range(9):
    put(sub_note(A1, 0.32), k * 0.5 + 0.25, 0.5)
# marquee shaker
for k in range(8):
    put(hat(dur=0.03, tone=8200), 2.5 + k * 0.125, 0.10, pan=(-1) ** k * 0.3)

put(boom(0.7), 0.0, 0.65, drums=True)                    # opening
put(whoosh(0.2, 500, 3600), 0.02, 0.45)
n = int(0.09 * SR); x = np.arange(n) / SR
sh1 = highpass(rng.standard_normal(n), 3000) * np.exp(-x * 300)
put(sh1, 0.45, 0.8)                                      # shutter (white)
put(boom(0.5, 60), 0.678, 0.55, drums=True)              # billboard
put(chime([440, 660], 0.35), 1.0, 0.35)                  # instagram
for k in range(4):
    put(tickk(3000 + k * 90, 0.03), 1.08 + k * 0.1, 0.15, 0.25)
put(riser(0.34), 1.42, 0.6)                              # DIVE riser into the logo
put(boom(0.6, 52), 1.732, 0.7, drums=True)               # portal thud
put(whoosh(0.25, 300, 2200), 1.75, 0.5)                  # pull-out air
put(whoosh(0.3, 600, 5000), 2.5, 0.55)                   # marquee wall
put(riser(0.32), 3.24, 0.6)                              # riser into the blast
put(boom(0.9, 46), 3.522, 0.95, drums=True)              # THE BOOM
n = int(1.0 * SR); x = np.arange(n) / SR
put(highpass(rng.standard_normal(n), 4200) * np.exp(-x * 5) * 0.9, 3.55, 0.3)
put(sub_note(A1, 0.6), 3.55, 0.5)
put(chime([440, 554, 659], 0.9), 3.62, 0.5)              # brand chime
put(whoosh(0.25, 400, 2800), 4.75, 0.32)                 # tail into the loop

duck = np.ones(N)
for b in range(10):
    i0 = int(b * BEAT * SR); n = int(0.24 * SR)
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
with wave.open('/tmp/exp-ident.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(out.tobytes())
print('wrote /tmp/exp-ident.wav')
