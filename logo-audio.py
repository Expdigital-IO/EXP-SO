#!/usr/bin/env python3
"""EXP Logo Reel soundtrack — 120 BPM, 24 beats, 12.0 s, composed in numpy.

Royalty-free by construction. Punchier than the UI-morph track: every scene
cut lands on a hit; whooshes, shutter clicks and impact booms mark the montage.
"""
import numpy as np
import wave

SR = 44100
DUR = 12.0
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
for b in range(24):
    tb = b * BEAT
    put(kick(punch=1.0), tb, 0.95, drums=True)
    put(hat(), tb + 0.25, 0.30, pan=0.35)
    if b >= 2:
        put(hat(dur=0.03, tone=9500), tb + 0.375, 0.13, pan=-0.4)
    if b % 4 in (1, 3):
        put(clap(), tb, 0.5, pan=-0.08)

SUBP = {0: A1, 1: A1, 2: F1, 3: A1, 4: F1, 5: A1}   # per bar
for bar, f in SUBP.items():
    for off in (0, 0.75, 1.5, 2.5, 3.0, 3.75):
        put(sub_note(f if off < 3 else A1, 0.32), bar * 2 + off * BEAT, 0.55)

# ---------------- scene-cut hits ----------------
CUTS = [0, 1, 2, 2.25, 2.5, 3, 4, 5, 6, 7, 8, 9, 10, 10.5, 11]  # seconds
put(boom(0.8), 0.0, 0.7, drums=True)                      # opening
put(whoosh(0.35, 400, 3200), 0.02, 0.5)
put(whoosh(0.3, 500, 3600), 1.0, 0.5)         # waves
put(shutter(), 2.0, 0.85)                     # white cut 1
put(shutter(), 2.25, 0.7)                     # white cut 2
put(boom(0.6, 60), 2.478, 0.6, drums=True)                  # black-on-orange
put(whoosh(0.3, 600, 4200), 3.0, 0.5)         # lockup wipe
put(tick(2600, 0.04), 3.35, 0.5, 0.2)
put(chime([440, 660], 0.4), 4.0, 0.35)        # instagram pop
for k in range(6):                            # follower count ticks
    put(tick(3000 + k * 90, 0.03), 4.15 + k * 0.11, 0.16, 0.25)
put(whoosh(0.28, 500, 3600), 5.0, 0.5)        # app store
for k in range(5):                            # star pops
    put(tick(2000 + k * 180, 0.05), 5.125 + k * 0.045 * 2, 0.3, -0.2 + k * 0.1)
put(whoosh(0.3, 400, 3000), 6.0, 0.5)         # type blueprint
put(boom(0.7, 50), 6.972, 0.65, drums=True)                 # totem
put(whoosh(0.3, 500, 3600), 8.0, 0.5)         # browser
put(tick(2400, 0.05), 8.45, 0.4)              # cta pop
put(whoosh(0.4, 600, 5000), 9.0, 0.55)        # tapes sweep in
put(chime([523, 784], 0.35), 10.0, 0.3)       # peach
put(boom(0.6, 48), 10.478, 0.7, drums=True)                 # macro bass drop
put(riser(0.95), 10.05, 0.4)                  # riser into the outro
put(boom(0.9, 55), 10.975, 0.75, drums=True)                # final lockup hit
put(chime([440, 554, 659], 0.9), 11.02, 0.5)  # brand chime
put(whoosh(0.3, 400, 2800), 11.85, 0.35)      # tail into the loop cut

# ---------------- sidechain ----------------
duck = np.ones(N)
for b in range(24):
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
for b in range(24):
    c = int(b * BEAT * SR / hop)
    win = onset[max(0, c - 8):c + 9]
    if len(win):
        errs.append((np.argmax(win) + max(0, c - 8) - c) * hop / SR * 1000)
errs = np.array(errs)
print(f'beat-grid: mean |err| {np.mean(np.abs(errs)):.1f} ms, max {np.max(np.abs(errs)):.1f} ms')
assert np.max(np.abs(errs)) < 40
print('grid OK')
