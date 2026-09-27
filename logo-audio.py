#!/usr/bin/env python3
"""EXP Logo Reel soundtrack — 120 BPM, 24 beats, 12.0 s, composed in numpy.

Royalty-free by construction. Punchier than the UI-morph track: every scene
cut lands on a hit; whooshes, shutter clicks and impact booms mark the montage.
"""
import numpy as np
import wave

SR = 44100
DUR = 13.5
BEAT = 0.5
N = int(SR * DUR)

L = np.zeros(N)
R = np.zeros(N)
KL = np.zeros(N)   # kicks/booms live outside the sidechain
KR = np.zeros(N)
rng = np.random.default_rng(11)


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
    S = np.fft.rfft(sig)
    f = np.fft.rfftfreq(len(sig), 1 / SR)
    S *= 1 / (1 + (f / fc) ** 4)
    return np.fft.irfft(S, len(sig))


def highpass(sig, fc):
    S = np.fft.rfft(sig)
    f = np.fft.rfftfreq(len(sig), 1 / SR)
    S *= (f / fc) ** 4 / (1 + (f / fc) ** 4)
    return np.fft.irfft(S, len(sig))


def bandpass(sig, lo, hi):
    return highpass(lowpass(sig, hi), lo)


def kick(dur=0.32, punch=1.0):
    n = int(dur * SR)
    x = np.arange(n) / SR
    freq = 42 + 130 * np.exp(-x * 36)
    body = np.sin(2 * np.pi * np.cumsum(freq) / SR) * np.exp(-x * 12)
    click = highpass(rng.standard_normal(int(0.004 * SR)), 2800) * 0.8
    out = body * punch
    out[:len(click)] += click * punch
    return np.tanh(out * 1.7) * 0.92


def hat(dur=0.05, tone=7500):
    n = int(dur * SR)
    return highpass(rng.standard_normal(n), tone) * env(n, 0.001, 0.016, 6) * 1.3


def clap(dur=0.22):
    n = int(dur * SR)
    out = np.zeros(n)
    for k, dt in enumerate([0.0, 0.010, 0.019, 0.030]):
        i = int(dt * SR)
        m = n - i
        out[i:] += bandpass(rng.standard_normal(m), 1000, 4500) * env(m, 0.001, 0.08, 6) * (0.7 if k < 3 else 1.0)
    return out * 0.85


def boom(dur=0.7, f0=55):
    """Impact boom for big cuts."""
    n = int(dur * SR)
    x = np.arange(n) / SR
    freq = f0 * (1 + 0.6 * np.exp(-x * 20))
    body = np.sin(2 * np.pi * np.cumsum(freq) / SR) * np.exp(-x * 6)
    th = lowpass(rng.standard_normal(n), 300) * np.exp(-x * 14) * 0.6
    return np.tanh((body + th) * 1.8) * 0.95


def whoosh(dur=0.3, lo=500, hi=4000):
    n = int(dur * SR)
    x = np.arange(n) / SR
    sig = bandpass(rng.standard_normal(n), lo, hi)
    e = np.sin(np.pi * np.minimum(x / dur, 1)) ** 2
    return sig * e * 0.8


def shutter():
    """Camera-shutter double click for the white hard cuts."""
    n = int(0.09 * SR)
    x = np.arange(n) / SR
    c1 = highpass(rng.standard_normal(n), 3000) * np.exp(-x * 300)
    c2 = np.zeros(n)
    i = int(0.035 * SR)
    c2[i:] = highpass(rng.standard_normal(n - i), 2200) * np.exp(-x[:n - i] * 260) * 0.8
    return (c1 + c2) * 0.9


def tick(hz=2400, dur=0.05):
    n = int(dur * SR)
    x = np.arange(n) / SR
    return (np.sin(2 * np.pi * hz * x) * np.exp(-x * 200) +
            highpass(rng.standard_normal(n), 3600) * np.exp(-x * 420) * 0.4)


def riser(dur=1.0):
    n = int(dur * SR)
    x = np.arange(n) / SR
    sig = bandpass(rng.standard_normal(n), 700, 7000)
    return sig * (x / dur) ** 2.4 * 0.55


def sub_note(f, dur):
    n = int(dur * SR)
    x = np.arange(n) / SR
    sig = np.sin(2 * np.pi * f * x) + 0.15 * np.sin(2 * np.pi * 2 * f * x)
    e = np.minimum(x / 0.01, 1) * np.minimum((dur - x) / 0.05, 1).clip(0, 1)
    return np.tanh(sig * 1.4) * e * 0.8


def chime(freqs, dur=0.7):
    n = int(dur * SR)
    x = np.arange(n) / SR
    sig = np.zeros(n)
    for i, f in enumerate(freqs):
        d = 0.05 * i
        m = x > d
        sig[m] += (np.sin(2 * np.pi * f * (x[m] - d)) + 0.3 * np.sin(2 * np.pi * 2.01 * f * (x[m] - d))) * np.exp(-(x[m] - d) * 7)
    return sig * 0.5


# ---------------- groove: kick 4/4, hats, claps, driving sub ----------------
A1, E1, F1 = 55.0, 41.2, 43.65
for b in range(27):
    tb = b * BEAT
    if b != 26:                                     # last beat breathes before the loop
        put(kick(punch=1.0), tb, 0.95, drums=True)
    put(hat(), tb + 0.25, 0.30 if b < 26 else 0.16, pan=0.35)
    if b >= 2:
        put(hat(dur=0.03, tone=9500), tb + 0.375, 0.13, pan=-0.4)
    if b % 4 in (1, 3) and b < 25:
        put(clap(), tb, 0.5, pan=-0.08)

SUBP = {0: A1, 1: A1, 2: F1, 3: A1, 4: F1, 5: A1, 6: A1}   # per bar
for bar, f in SUBP.items():
    for off in (0, 0.75, 1.5, 2.5, 3.0, 3.75):
        if bar * 2 + off * BEAT < 13.2:
            put(sub_note(f if off < 3 else A1, 0.32), bar * 2 + off * BEAT, 0.55)
# marquee section shaker (8.5-11.0): rolling 16ths
for k in range(20):
    put(hat(dur=0.03, tone=8200), 8.5 + k * 0.125, 0.10, pan=(-1) ** k * 0.3)

# ---------------- scene-cut hits ----------------
CUTS = [0, 1, 2, 2.25, 2.5, 3, 4, 5, 6, 7, 8, 9, 10, 10.5, 11]  # seconds
put(boom(0.8), 0.0, 0.7, drums=True)                       # opening
put(whoosh(0.35, 400, 3200), 0.02, 0.5)
put(whoosh(0.3, 500, 3600), 0.75, 0.5)                      # waves
put(shutter(), 1.5, 0.85)                                   # white cut
put(shutter(), 1.75, 0.7)                                   # negative cut
put(boom(0.6, 60), 1.978, 0.6, drums=True)                  # on-color
put(whoosh(0.3, 600, 4200), 2.5, 0.5)                       # lockup wipe
put(tick(2600, 0.04), 2.85, 0.5, 0.2)
put(chime([440, 660], 0.4), 3.5, 0.35)                      # instagram
for k in range(6):
    put(tick(3000 + k * 90, 0.03), 3.65 + k * 0.11, 0.16, 0.25)
put(whoosh(0.28, 500, 3600), 4.5, 0.5)                      # app store
for k in range(5):
    put(tick(2000 + k * 180, 0.05), 4.62 + k * 0.09, 0.3, -0.2 + k * 0.1)
put(whoosh(0.3, 400, 3000), 5.5, 0.5)                       # type blueprint
put(boom(0.7, 50), 6.472, 0.65, drums=True)                 # phone
put(whoosh(0.3, 500, 3600), 7.5, 0.5)                       # browser
put(tick(2400, 0.05), 7.95, 0.4)
put(whoosh(0.4, 600, 5000), 8.5, 0.55)                      # marquee wall
put(riser(1.1), 9.9, 0.55)                                  # riser into the blast
def crash(dur=1.2):
    n = int(dur * SR)
    x = np.arange(n) / SR
    return highpass(rng.standard_normal(n), 4200) * np.exp(-x * 4.5) * 0.9
put(boom(1.0, 46), 10.972, 0.95, drums=True)                # THE BOOM
put(crash(), 11.0, 0.32)
put(sub_note(A1, 0.8), 11.0, 0.5)
put(boom(0.8, 55), 11.475, 0.7, drums=True)                 # final lockup hit
put(chime([440, 554, 659], 1.0), 11.52, 0.5)                # brand chime
put(whoosh(0.3, 400, 2800), 13.05, 0.35)                    # tail into the loop

# ---------------- sidechain ----------------
duck = np.ones(N)
for b in range(27):
    i0 = int(b * BEAT * SR)
    n = int(0.28 * SR)
    x = np.arange(min(n, N - i0)) / SR
    duck[i0:i0 + len(x)] *= 1 - 0.42 * np.exp(-x * 12)
L *= duck
R *= duck
L += KL
R += KR

# ---------------- master ----------------
mix = np.stack([L, R])
mix = np.tanh(mix * 1.3)
mix *= 0.97 / np.max(np.abs(mix))
nf = int(0.012 * SR)
fade = np.linspace(0, 1, nf)
mix[:, :nf] = mix[:, :nf] * fade + mix[:, -nf:] * (1 - fade)
mix[:, -nf:] *= np.linspace(1, 0, nf)

out = (mix.T * 32767).astype(np.int16)
with wave.open('/tmp/exp-reel.wav', 'wb') as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(out.tobytes())
print('wrote /tmp/exp-reel.wav')

# beat-grid validation
mono = mix.mean(axis=0)
hop = 256
e = np.array([np.sqrt(np.mean(mono[i * hop:(i + 1) * hop] ** 2)) for i in range(len(mono) // hop)])
onset = np.maximum(np.diff(e), 0)
errs = []
for b in range(26):
    c = int(b * BEAT * SR / hop)
    win = onset[max(0, c - 8):c + 9]
    if len(win):
        errs.append((np.argmax(win) + max(0, c - 8) - c) * hop / SR * 1000)
errs = np.array(errs)
print(f'beat-grid: mean |err| {np.mean(np.abs(errs)):.1f} ms, max {np.max(np.abs(errs)):.1f} ms')
assert np.max(np.abs(errs)) < 40
print('grid OK')
