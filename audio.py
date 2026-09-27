#!/usr/bin/env python3
"""EXP Brand Anthem — 120 BPM, 7 bars, 14.0 s, composed in numpy.

Royalty-free by construction: every sample is synthesized here.
The mix starts on a downbeat and loops (bar 7 hands off to bar 1).
Every UI sound is placed at the exact event time used by index.html.
"""
import numpy as np

SR = 44100
DUR = 14.0
BEAT = 0.5
N = int(SR * DUR)
t_axis = np.arange(N) / SR

L = np.zeros(N)
R = np.zeros(N)


def put(sig, t0, gain=1.0, pan=0.0):
    """Mix a mono snippet into the stereo master at time t0. pan in [-1, 1]."""
    i0 = int(t0 * SR)
    if i0 >= N:
        return
    n = min(len(sig), N - i0)
    gl = gain * min(1.0, 1.0 - pan)
    gr = gain * min(1.0, 1.0 + pan)
    L[i0:i0 + n] += sig[:n] * gl
    R[i0:i0 + n] += sig[:n] * gr


def env(n, a, d, curve=5.0):
    """Attack-decay envelope, exponential decay."""
    x = np.arange(n) / SR
    e = np.minimum(x / max(a, 1e-4), 1.0) * np.exp(-np.maximum(x - a, 0) * curve / max(d, 1e-3))
    return e


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


rng = np.random.default_rng(7)

# ---------------------------------------------------------------- drums
def kick(dur=0.30, punch=1.0):
    n = int(dur * SR)
    x = np.arange(n) / SR
    freq = 44 + 120 * np.exp(-x * 34)
    phase = 2 * np.pi * np.cumsum(freq) / SR
    body = np.sin(phase) * np.exp(-x * 13)
    click = highpass(rng.standard_normal(int(0.004 * SR)), 2500) * 0.7
    out = body * punch
    out[:len(click)] += click * punch
    return np.tanh(out * 1.6) * 0.9


def hat(dur=0.06, tone=7000):
    n = int(dur * SR)
    return highpass(rng.standard_normal(n), tone) * env(n, 0.001, 0.018, 6) * 1.4


def clap(dur=0.25):
    n = int(dur * SR)
    out = np.zeros(n)
    for k, dt in enumerate([0.0, 0.011, 0.021, 0.033]):
        i = int(dt * SR)
        m = n - i
        out[i:] += bandpass(rng.standard_normal(m), 900, 4200) * env(m, 0.001, 0.09, 6) * (0.7 if k < 3 else 1.0)
    return out * 0.8


# ---------------------------------------------------------------- tonal
def note_hz(name):
    NAMES = {'A': 0, 'B': 2, 'C': 3, 'D': 5, 'E': 7, 'F': 8, 'G': 10}
    letter, octv = name[0], int(name[-1])
    semis = NAMES[letter] + (1 if '#' in name else 0)
    return 55.0 * (2 ** (octv - 1)) * (2 ** (semis / 12))


def sub_note(f, dur):
    n = int(dur * SR)
    x = np.arange(n) / SR
    sig = np.sin(2 * np.pi * f * x) + 0.18 * np.sin(2 * np.pi * 2 * f * x)
    e = np.minimum(x / 0.012, 1) * np.minimum((dur - x) / 0.06, 1).clip(0, 1)
    return np.tanh(sig * 1.3) * e * 0.8


def pad_chord(freqs, dur, bright=900):
    n = int(dur * SR)
    x = np.arange(n) / SR
    sig = np.zeros(n)
    for f in freqs:
        for h, a in [(1, 1.0), (2, 0.35), (3, 0.16), (4, 0.07)]:
            det = 1 + 0.0015 * np.sin(2 * np.pi * 0.31 * x + f)
            sig += a * np.sin(2 * np.pi * f * h * det * x + f)
    sig = lowpass(sig / len(freqs), bright)
    e = np.minimum(x / 0.25, 1) * np.minimum((dur - x) / 0.4, 1).clip(0, 1)
    return sig * e * 0.5


def pluck(f, dur=0.22, bright=2400):
    n = int(dur * SR)
    x = np.arange(n) / SR
    sig = np.sin(2 * np.pi * f * x) + 0.4 * np.sin(2 * np.pi * 2 * f * x + 0.7)
    sig = lowpass(sig, bright)
    return sig * env(n, 0.002, 0.09, 7)


# ---------------------------------------------------------------- UI sounds
def ui_click(hz=1900, dur=0.05, sharp=0.9):
    n = int(dur * SR)
    x = np.arange(n) / SR
    tick = np.sin(2 * np.pi * hz * x) * np.exp(-x * 220)
    th = highpass(rng.standard_normal(n), 3200) * np.exp(-x * 500) * sharp
    return (tick + th * 0.5) * 0.9


def ui_pop():
    n = int(0.14 * SR)
    x = np.arange(n) / SR
    f = 340 + 620 * (1 - np.exp(-x * 40))
    sig = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * 26)
    return sig * 0.9


def ui_whoosh(dur=0.28, lo=500, hi=3200, updown=True):
    n = int(dur * SR)
    x = np.arange(n) / SR
    noise = rng.standard_normal(n)
    sig = bandpass(noise, lo, hi)
    e = np.sin(np.pi * np.minimum(x / dur, 1)) ** 2
    return sig * e * 0.8


def ui_thock(hz=150):
    n = int(0.11 * SR)
    x = np.arange(n) / SR
    body = np.sin(2 * np.pi * hz * x) * np.exp(-x * 46)
    tick = highpass(rng.standard_normal(n), 2600) * np.exp(-x * 420)
    return np.tanh(body * 2.2 + tick * 0.5) * 0.95


def ui_chime(freqs, dur=0.7):
    n = int(dur * SR)
    x = np.arange(n) / SR
    sig = np.zeros(n)
    for i, f in enumerate(freqs):
        d = 0.06 * i
        m = x > d
        sig[m] += (np.sin(2 * np.pi * f * (x[m] - d)) + 0.3 * np.sin(2 * np.pi * 2.01 * f * (x[m] - d))) \
                  * np.exp(-(x[m] - d) * 7)
    return sig * 0.55


def ui_stretch(dur=0.38, f0=210, f1=560):
    n = int(dur * SR)
    x = np.arange(n) / SR
    f = f0 + (f1 - f0) * (x / dur) ** 1.6
    sig = np.sin(2 * np.pi * np.cumsum(f) / SR)
    sig += 0.3 * np.sin(2 * np.pi * np.cumsum(f * 1.502) / SR)
    e = np.minimum(x / 0.05, 1) * np.minimum((dur - x) / 0.05, 1).clip(0, 1)
    return lowpass(sig, 1800) * e * 0.55


# ================================================================ arrangement
A1, A2 = note_hz('A1'), note_hz('A2')
F1 = note_hz('F1')
AM9 = [note_hz('A2'), note_hz('C3'), note_hz('E3'), note_hz('G3'), note_hz('B3')]
FM9 = [note_hz('F2'), note_hz('A2'), note_hz('C3'), note_hz('E3'), note_hz('G3')]

# --- drums ---
for b in range(28):
    tb = b * BEAT
    bar = b // 4
    put(kick(punch=1.0 if bar not in (0,) else 0.85), tb, 0.9)
    put(hat(), tb + 0.25, 0.30 if bar >= 1 else 0.20, pan=0.35)
    if bar >= 3:
        put(hat(dur=0.03, tone=9000), tb + 0.375, 0.12, pan=-0.4)   # 16th ghost
for b in range(28):
    if b % 4 in (1, 3) and b >= 4 and b < 26:                        # claps on 2 & 4, bars 2-6
        put(clap(), b * BEAT, 0.5, pan=-0.1)

# --- sub bass: enters on the PLAY click (t=3.0, beat 6), leaves at 13.0 ---
BASSLINE = {  # bar -> pattern of (offset beats, note, len beats)
    1: [(2, A1, 0.45), (3, A1, 0.45), (3.5, A1, 0.4)],
    2: [(0, A1, 0.45), (1, A1, 0.4), (1.75, A2, 0.2), (2, A1, 0.45), (3, A1, 0.4), (3.5, A1, 0.45)],
    3: [(0, F1, 0.45), (1, F1, 0.4), (1.75, F1 * 2, 0.2), (2, F1, 0.45), (3, F1, 0.4), (3.5, A1, 0.45)],
    4: [(0, A1, 0.45), (1, A1, 0.4), (1.75, A2, 0.2), (2, A1, 0.45), (3, A1, 0.4), (3.5, A1, 0.45)],
    5: [(0, F1, 0.45), (1, F1, 0.4), (1.75, F1 * 2, 0.2), (2, F1, 0.45), (3, F1, 0.4), (3.5, A1, 0.45)],
    6: [(0, A1, 0.45), (1, A1, 0.4), (2, A1, 0.45)],
}
for bar, pat in BASSLINE.items():
    for off, f, ln in pat:
        put(sub_note(f, ln * BEAT * 2), (bar * 4 + off) * BEAT, 0.62)

# --- pads: ghost from start, open after play ---
CHORDS = {0: (AM9, 500), 1: (AM9, 700), 2: (FM9, 1100), 3: (AM9, 1200),
          4: (FM9, 1400), 5: (AM9, 1200), 6: (AM9, 700)}
for bar, (ch, br) in CHORDS.items():
    g = 0.30 if bar == 0 else (0.42 if bar >= 2 else 0.36)
    if bar == 6:
        g = 0.30
    put(pad_chord(ch, 2.05, bright=br), bar * 2.0, g, pan=0.08 if bar % 2 else -0.08)

# --- arp: rises with the chart draw (bars 5), sparkles bars 3-6 ---
PENTA = ['A3', 'C4', 'D4', 'E4', 'G4', 'A4', 'C5', 'D5', 'E5', 'G5', 'A5']
for bar in range(2, 7):
    for s in range(8):                    # 8th notes
        tt = bar * 2.0 + s * 0.25
        if bar == 4:                      # chart bar: ascending run during the draw (8.0-9.0)
            idx = min(s + 2, len(PENTA) - 1) if tt < 9.0 else 4 + (s % 3)
            g = 0.16
        else:
            if s % 2 == 0:
                continue
            idx = [4, 2, 5, 3][(s // 2) % 4] + (2 if bar >= 5 else 0)
            g = 0.10
        put(pluck(note_hz(PENTA[idx])), tt, g, pan=0.5 if s % 2 else -0.5)

# --- risers into key moments ---
def riser(dur=0.9):
    n = int(dur * SR)
    x = np.arange(n) / SR
    sig = bandpass(rng.standard_normal(n), 600, 6000)
    return sig * (x / dur) ** 2.2 * 0.5

put(riser(0.9), 2.1, 0.35)     # into the play drop (3.0)
put(riser(0.9), 11.1, 0.30)    # into the toast (12.0)
put(riser(0.7), 13.3, 0.22)    # into the loop restart

# --- sidechain duck (pumping pads/sub feel) ---
duck = np.ones(N)
for b in range(28):
    i0 = int(b * BEAT * SR)
    n = int(0.30 * SR)
    x = np.arange(min(n, N - i0)) / SR
    duck[i0:i0 + len(x)] *= 1 - 0.45 * np.exp(-x * 11)
L *= duck
R *= duck

# ================================================================ UI sounds
UI = []  # (time, snippet, gain, pan)
UI.append((0.50, ui_click(2100), 0.75, 0.0))          # button press
UI.append((0.72, ui_click(1500, sharp=0.5), 0.5, 0.0))
UI.append((1.50, ui_pop(), 0.8, 0.0))                 # check pop
UI.append((1.55, ui_chime([note_hz('A4'), note_hz('E5')], 0.45), 0.45, 0.1))
UI.append((2.00, ui_whoosh(0.24, 400, 2600), 0.45, 0.0))    # island
UI.append((2.50, ui_whoosh(0.30, 500, 3400), 0.5, 0.0))     # player opens
UI.append((3.00, ui_click(2100), 0.8, 0.0))           # play
UI.append((4.00, ui_click(1700), 0.6, -0.1))          # grab progress
for k in range(7):                                     # scrub zipper
    UI.append((4.06 + k * 0.1, ui_click(2600 + k * 120, 0.03, 0.25), 0.14, 0.1))
UI.append((4.75, ui_click(1400, sharp=0.5), 0.55, 0.0))     # release
UI.append((5.00, ui_whoosh(0.22, 500, 2800), 0.4, 0.0))     # volume
UI.append((5.48, ui_stretch(), 0.5, 0.1))             # rubber-band stretch
UI.append((5.86, ui_thock(210), 0.55, 0.0))           # snap back
UI.append((6.50, ui_thock(160), 0.9, 0.0))            # toggle ON
UI.append((7.00, ui_whoosh(0.24, 500, 3000), 0.45, 0.0))    # tabs
UI.append((7.50, ui_whoosh(0.18, 900, 4200), 0.4, 0.3))     # liquid slide
UI.append((8.00, ui_whoosh(0.32, 400, 3200), 0.5, 0.0))     # chart opens
UI.append((9.00, ui_click(2300, 0.04, 0.3), 0.35, 0.2))     # tooltip
UI.append((9.50, ui_click(2500, 0.04, 0.3), 0.35, 0.3))     # tooltip 2
UI.append((10.00, ui_whoosh(0.26, 500, 2600), 0.45, 0.0))   # collapse to ⌘K
UI.append((10.50, ui_whoosh(0.24, 600, 3400), 0.45, 0.0))   # palette opens
UI.append((10.75, ui_click(2900, 0.04), 0.5, -0.15))  # key 'l'
UI.append((11.00, ui_click(2600, 0.04), 0.5, 0.15))   # key 'a'
UI.append((11.50, ui_thock(140), 0.8, 0.0))           # enter
UI.append((12.00, ui_chime([note_hz('A4'), note_hz('C5'), note_hz('E5')], 0.8), 0.6, 0.0))  # toast
UI.append((13.00, ui_whoosh(0.24, 400, 2400), 0.4, 0.0))    # back to button

for tt, sig, g, pn in UI:
    put(sig, tt, g, pn)

# ================================================================ master
mix = np.stack([L, R])
mix = np.tanh(mix * 1.25)
mix *= 0.97 / np.max(np.abs(mix))

# seamless loop: 12 ms equal-power crossfade of the edges
nf = int(0.012 * SR)
fade = np.linspace(0, 1, nf)
mix[:, :nf] = mix[:, :nf] * fade + mix[:, -nf:] * (1 - fade)
mix[:, -nf:] *= np.linspace(1, 0, nf)

out = (mix.T * 32767).astype(np.int16)
import wave
with wave.open('/tmp/exp-anthem.wav', 'wb') as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(out.tobytes())
print('wrote /tmp/exp-anthem.wav', out.shape)

# ---- beat-grid validation: onset energy must peak on multiples of 0.5 s ----
mono = mix.mean(axis=0)
hop = 256
frames = len(mono) // hop
e = np.array([np.sqrt(np.mean(mono[i * hop:(i + 1) * hop] ** 2)) for i in range(frames)])
onset = np.maximum(np.diff(e), 0)
errs = []
for b in range(28):
    c = int(b * BEAT * SR / hop)
    win = onset[max(0, c - 8):c + 9]
    if len(win):
        pk = np.argmax(win) + max(0, c - 8)
        errs.append((pk - c) * hop / SR * 1000)
errs = np.array(errs)
print(f'beat-grid: mean |err| {np.mean(np.abs(errs)):.1f} ms, max {np.max(np.abs(errs)):.1f} ms')
assert np.max(np.abs(errs)) < 25, 'beat grid off!'
print('downbeat OK, grid OK')
