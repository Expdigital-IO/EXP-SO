#!/usr/bin/env python3
"""Bipa + EXP Reels — trilha de 15 s a 120 BPM, sintetizada aqui (livre de direitos).

0–6,6 s   pad etéreo + brilhos que acompanham o cometa desenhando as logos, riser
6,94 s    60 ms de silêncio
7,0 s     boom (as logos explodem e voltam), entra o groove
8,35 s    três "swooshes" para as linhas da manchete
9,0–11,5  um "pop" por recurso (um por batida)
12,0 s    virada para o final · 12,55 pop do botão · acorde final com cauda
"""
import wave
import numpy as np

SR = 44100
DUR = 15.0
N = int(SR * DUR)
L = np.zeros(N); R = np.zeros(N)
rng = np.random.default_rng(1124)
BEAT = 0.5


def put(sig, t0, gain=1.0, pan=0.0):
    i0 = int(t0 * SR)
    if i0 >= N or i0 < 0:
        return
    n = min(len(sig), N - i0)
    L[i0:i0 + n] += sig[:n] * gain * min(1, 1 - pan)
    R[i0:i0 + n] += sig[:n] * gain * min(1, 1 + pan)


def filt(sig, lo=None, hi=None):
    S = np.fft.rfft(sig); f = np.fft.rfftfreq(len(sig), 1 / SR)
    if hi: S *= 1 / (1 + (f / hi) ** 4)
    if lo: S *= (f / lo) ** 4 / (1 + (f / lo) ** 4)
    return np.fft.irfft(S, len(sig))


def reverb(sig, secs=2.2, mix=0.35):
    n = int(secs * SR); x = np.arange(n) / SR
    ir = rng.standard_normal(n) * np.exp(-x * 6.9 / secs)
    ir = filt(ir, 200, 7000); ir /= np.sqrt(np.sum(ir ** 2))
    m = len(sig) + n
    wet = np.fft.irfft(np.fft.rfft(sig, m) * np.fft.rfft(ir, m), m)[:len(sig)]
    return sig * (1 - mix) + wet * mix * 1.4


def mtof(m): return 440 * 2 ** ((m - 69) / 12)


def pad_chord(notes, dur, bright=1800):
    n = int(dur * SR); x = np.arange(n) / SR; s = np.zeros(n)
    for m in notes:
        f = mtof(m)
        for det in (-0.12, 0, 0.11):          # supersaw suave
            ph = rng.uniform(0, 1)
            s += (2 * ((x * f * 2 ** (det / 12) + ph) % 1) - 1) * 0.12
    s = filt(s, 120, bright)
    return s * np.minimum(x / 0.8, 1) * np.minimum((dur - x) / 0.6, 1).clip(0, 1)


def ping(f, dur=0.6):
    n = int(dur * SR); x = np.arange(n) / SR
    return (np.sin(2 * np.pi * f * x) + 0.25 * np.sin(2 * np.pi * 3.01 * f * x)) * np.exp(-x * 9) * np.minimum(x / 0.002, 1)


def kick(dur=0.32):
    n = int(dur * SR); x = np.arange(n) / SR
    f = 46 + 120 * np.exp(-x * 32)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * 9)
    click = filt(rng.standard_normal(n), 1500, 6000) * np.exp(-x * 300) * 0.3
    return np.tanh((body + click) * 1.6)


def hat(dur=0.05, lo=7000):
    n = int(dur * SR); x = np.arange(n) / SR
    return filt(rng.standard_normal(n), lo, None) * np.exp(-x * 80)


def boom(dur=2.4):
    n = int(dur * SR); x = np.arange(n) / SR
    f = 34 + 90 * np.exp(-x * 14)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * 2.2)
    noise = filt(rng.standard_normal(n), 60, 3000) * np.exp(-x * 5) * 0.7
    return np.tanh((sub + noise) * 1.5)


def whoosh(dur=0.5, lo=500, hi=6000, rise=True):
    n = int(dur * SR); x = np.arange(n) / SR; u = x / dur
    e = (u ** 2.5 if rise else np.sin(np.pi * u) ** 2)
    sig = filt(rng.standard_normal(n), lo, hi) * e
    return sig * 0.7


def pop(f=1400):
    n = int(0.18 * SR); x = np.arange(n) / SR
    fr = f * (1 + 0.6 * np.exp(-x * 60))
    return np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-x * 26) + filt(rng.standard_normal(n), 4000) * np.exp(-x * 300) * 0.3


def bass(m, dur):
    n = int(dur * SR); x = np.arange(n) / SR; f = mtof(m)
    s = np.tanh(np.sin(2 * np.pi * f * x) * 1.8 + 0.3 * np.sin(4 * np.pi * f * x))
    return s * np.minimum(x / 0.006, 1) * np.exp(-x * 3.5)


# ---------------- Ato 1: desenho (0–6,94)
# Dmaj9 → Bm11 → Gmaj9 (claro, "abertura")
put(reverb(pad_chord([50, 57, 62, 66, 69, 76], 3.4, 1400)), 0.0, 0.55)
put(reverb(pad_chord([47, 54, 62, 66, 69, 73], 2.0, 2000)), 3.2, 0.5)
put(reverb(pad_chord([43, 50, 59, 62, 66, 69], 1.9, 2600)), 5.05, 0.5)
# brilhos do cometa: densidade cresce com o desenho
SCALE = [74, 76, 78, 81, 83, 85, 86, 88, 90, 93]
tt = 0.15
while tt < 6.8:
    m = SCALE[int(rng.integers(0, len(SCALE)))]
    put(reverb(ping(mtof(m), 0.7), 1.6, 0.5), tt, 0.10 + 0.05 * tt / 6.8, pan=float(rng.uniform(-0.7, 0.7)))
    tt += 0.25 - 0.17 * (tt / 6.8)
# "voo" do cometa (ar filtrado que abre)
n = int(6.9 * SR); x = np.arange(n) / SR
air = filt(rng.standard_normal(n), 900, 5000) * (0.05 + 0.10 * (x / 6.9) ** 2)
put(air, 0.0, 0.6)
put(whoosh(1.2, 600, 9000), 5.74, 0.55)           # riser final
# silêncio 6,94–7,0
cut0, cut1 = int(6.94 * SR), int(7.0 * SR)
L[cut0:cut1] *= np.linspace(1, 0, cut1 - cut0); R[cut0:cut1] *= np.linspace(1, 0, cut1 - cut0)
L[cut1:] = 0; R[cut1:] = 0
# reaplica o que começa depois de 7 s
# ---------------- Ato 2: hit + groove (7–12)
put(reverb(boom(), 2.8, 0.3), 7.0, 1.0)
put(reverb(pad_chord([50, 57, 62, 66, 69, 74, 78], 1.6, 5000), 2.5, 0.45), 7.0, 0.55)
n = int(1.2 * SR); x = np.arange(n) / SR
put(filt(rng.standard_normal(n), 5000) * np.exp(-x * 4) * 0.5, 7.0, 0.5)   # chuva de brilho
PROG = [(50, 7.5), (50, 8.5), (47, 9.0), (47, 10.0), (43, 10.5), (45, 11.5)]
for b in range(int((12.0 - 7.5) / BEAT)):
    tb = 7.5 + b * BEAT
    put(kick(), tb, 0.85)
    put(hat(), tb + 0.25, 0.22, pan=0.25)
    put(hat(0.03, 9000), tb + 0.375, 0.08, pan=-0.3)
    root = 50 if tb < 9.0 else 47 if tb < 10.5 else 43 if tb < 11.5 else 45
    put(bass(root - 12 + 12, 0.24), tb + 0.25, 0.32)
# acordes em stab no contratempo
CH = {50: [62, 66, 69, 73], 47: [62, 66, 69, 71], 43: [59, 62, 66, 69], 45: [61, 64, 69, 71]}
for b in range(9):
    tb = 7.5 + b * BEAT
    root = 50 if tb < 9.0 else 47 if tb < 10.5 else 43 if tb < 11.5 else 45
    st = sum(ping(mtof(m), 0.35) for m in CH[root]) * 0.35
    put(reverb(st, 1.2, 0.35), tb + 0.25, 0.25, pan=0.15 * (-1) ** b)
for i, t0 in enumerate((8.35, 8.5, 8.65)):
    put(whoosh(0.28, 1200, 8000, rise=False), t0 - 0.05, 0.35, pan=(-0.3, 0, 0.3)[i])
for i in range(6):
    put(pop(1250 + 140 * i), 9.0 + i * 0.5, 0.42)
# ---------------- Ato 3: final (12–15)
put(whoosh(0.45, 400, 7000), 11.6, 0.5)
put(kick(0.5), 12.05, 0.7)
put(reverb(pad_chord([50, 57, 62, 66, 69, 73, 76], 3.0, 3000), 3.0, 0.45), 12.05, 0.6)
put(reverb(pop(900), 1.5, 0.4), 12.55, 0.55)
for i, m in enumerate([74, 78, 81, 86]):
    put(reverb(ping(mtof(m), 1.2), 2.5, 0.5), 12.9 + i * 0.12, 0.16, pan=-0.3 + 0.2 * i)
put(bass(38, 1.8), 12.05, 0.35)

# sidechain leve no pad pelo kick do groove
duck = np.ones(N)
for b in range(9):
    i0 = int((7.5 + b * BEAT) * SR); n = int(0.25 * SR); x = np.arange(n) / SR
    duck[i0:i0 + n] *= 1 - 0.3 * np.exp(-x * 12)
mix = np.stack([L * duck, R * duck])
mix = np.tanh(mix * 1.2)
mix *= 0.93 / np.max(np.abs(mix))
fo = int(0.6 * SR); mix[:, -fo:] *= np.linspace(1, 0, fo) ** 1.5
fi = int(0.02 * SR); mix[:, :fi] *= np.linspace(0, 1, fi)
out = (mix.T * 32767).astype(np.int16)
with wave.open('/tmp/bipa-reel.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(out.tobytes())
print('wrote /tmp/bipa-reel.wav')
