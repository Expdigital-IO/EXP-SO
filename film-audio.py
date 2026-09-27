#!/usr/bin/env python3
"""EXP Brand Film soundtrack — 16.0 s, 120 BPM, 8 bars, corporate house.

Royalty-free by construction (pure numpy synthesis). Arrangement follows
the film: intro groove (Act I branding), arp lift (Act II marketing),
snare-roll build into the blast, half-time piano hits under the manifesto,
V-i cadence resolving on the endcard. Every UI sound sits on its cut.
"""
import wave

import numpy as np

SR = 44100
DUR = 16.0
BPM = 120
BEAT = 60 / BPM
BAR = 4 * BEAT
N = int(SR * DUR)
rng = np.random.default_rng(2026)

BUS = {k: np.zeros((2, N)) for k in ('drums', 'music', 'fx', 'send')}


def put(bus, sig, t0, gain=1.0, pan=0.0, send=0.0):
    i0 = int(round(t0 * SR))
    if i0 >= N:
        return
    if i0 < 0:
        sig = sig[-i0:]
        i0 = 0
    n = min(len(sig), N - i0)
    gl, gr = gain * min(1, 1 - pan), gain * min(1, 1 + pan)
    BUS[bus][0, i0:i0 + n] += sig[:n] * gl
    BUS[bus][1, i0:i0 + n] += sig[:n] * gr
    if send:
        BUS['send'][0, i0:i0 + n] += sig[:n] * gl * send
        BUS['send'][1, i0:i0 + n] += sig[:n] * gr * send


def tt(dur):
    return np.arange(int(dur * SR)) / SR


def lowpass(sig, fc, order=4):
    S = np.fft.rfft(sig)
    f = np.fft.rfftfreq(len(sig), 1 / SR)
    return np.fft.irfft(S / (1 + (f / fc) ** order), len(sig))


def highpass(sig, fc, order=4):
    S = np.fft.rfft(sig)
    f = np.fft.rfftfreq(len(sig), 1 / SR)
    r = (f / fc) ** order
    return np.fft.irfft(S * r / (1 + r), len(sig))


def bandpass(sig, lo, hi):
    return highpass(lowpass(sig, hi), lo)


NOTES = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}


def hz(name):
    """'A2', 'F#3', 'Bb3' -> frequency (A4 = 440)."""
    semis = NOTES[name[0]] + (1 if '#' in name else -1 if 'b' in name[1:-1] else 0)
    octave = int(name[-1])
    return 440.0 * 2 ** ((semis - 9) / 12 + (octave - 4))


# ============================ instruments ============================
def kick(punch=1.0):
    x = tt(0.42)
    f = 46 + 150 * np.exp(-x * 38)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * 9.5)
    click = np.zeros_like(x)
    k = int(0.005 * SR)
    click[:k] = highpass(rng.standard_normal(k), 3000) * np.linspace(1, 0, k)
    return np.tanh((body + 0.6 * click) * 1.9 * punch) * 0.92


def clap():
    x = tt(0.3)
    out = np.zeros_like(x)
    for k, dt in enumerate((0.0, 0.009, 0.018, 0.028)):
        i = int(dt * SR)
        m = len(x) - i
        out[i:] += bandpass(rng.standard_normal(m), 1100, 5200) * np.exp(-x[:m] * (38 if k < 3 else 16))
    return out * 0.7


def snap():
    x = tt(0.08)
    return highpass(rng.standard_normal(len(x)), 2500) * np.exp(-x * 90) * 0.8


def hat(open_=False):
    x = tt(0.22 if open_ else 0.05)
    n = highpass(rng.standard_normal(len(x)), 7200)
    return n * np.exp(-x * (16 if open_ else 95)) * (0.55 if open_ else 0.9)


def shaker():
    x = tt(0.07)
    return bandpass(rng.standard_normal(len(x)), 4500, 11000) * np.sin(np.pi * np.minimum(x / 0.07, 1)) ** 2 * 0.6


def snare():
    x = tt(0.16)
    body = np.sin(2 * np.pi * 190 * x) * np.exp(-x * 28)
    noise = bandpass(rng.standard_normal(len(x)), 1500, 7000) * np.exp(-x * 22)
    return (0.5 * body + noise) * 0.8


def ep(f, dur, vel=1.0):
    """FM electric piano: decaying modulation index + bell tine."""
    x = tt(dur + 0.35)
    idx = 1.1 * np.exp(-x * 5.5) + 0.22
    car = np.sin(2 * np.pi * f * x + idx * np.sin(2 * np.pi * f * x))
    tine = 0.16 * np.sin(2 * np.pi * f * 7.02 * x) * np.exp(-x * 16)
    env = np.minimum(x / 0.004, 1) * np.exp(-x * 1.7)
    rel = np.clip((dur + 0.35 - x) / 0.35, 0, 1)
    trem = 1 + 0.06 * np.sin(2 * np.pi * 5.2 * x)
    return (car + tine) * env * rel * trem * vel


def pad(freqs, dur):
    x = tt(dur)
    sig = np.zeros_like(x)
    for f in freqs:
        for det in (-0.006, 0.0, 0.0065):
            ph = 2 * np.pi * f * (1 + det) * x
            sig += np.tanh(np.sin(ph) * 2.5) * 0.33
    sig = lowpass(sig / len(freqs), 1300)
    env = np.minimum(x / 0.35, 1) * np.clip((dur - x) / 0.4, 0, 1)
    return sig * env * 0.5


def bass_pluck(f, dur=0.24):
    x = tt(dur)
    saw = sum(((-1) ** (k + 1)) * np.sin(2 * np.pi * k * f * x) / k for k in range(1, 12))
    tone = lowpass(saw, 950) * np.exp(-x * 7.5)
    sub = np.sin(2 * np.pi * f * x) * np.exp(-x * 4)
    rel = np.clip((dur - x) / 0.03, 0, 1)
    return np.tanh((1.0 * tone + 0.7 * sub) * 1.4) * rel * 0.75


def sub_long(f, dur):
    x = tt(dur)
    return np.sin(2 * np.pi * f * x) * np.minimum(x / 0.01, 1) * np.clip((dur - x) / 0.2, 0, 1) * 0.8


def pluck(f, dur=0.22):
    x = tt(dur)
    sig = np.sin(2 * np.pi * f * x) + 0.35 * np.sin(4 * np.pi * f * x + 0.5) + 0.12 * np.sin(6 * np.pi * f * x)
    return lowpass(sig, 3200) * np.exp(-x * 13) * 0.6


def boom(dur=1.0, f0=46):
    x = tt(dur)
    body = np.sin(2 * np.pi * np.cumsum(f0 * (1 + 0.7 * np.exp(-x * 18))) / SR) * np.exp(-x * 5)
    rum = lowpass(rng.standard_normal(len(x)), 260) * np.exp(-x * 9) * 0.7
    return np.tanh((body + rum) * 1.9) * 0.95


def crash(dur=1.6):
    x = tt(dur)
    return highpass(rng.standard_normal(len(x)), 5200) * np.exp(-x * 3.2) * 0.85


def whoosh(dur=0.3, lo=500, hi=4500):
    x = tt(dur)
    return bandpass(rng.standard_normal(len(x)), lo, hi) * np.sin(np.pi * np.minimum(x / dur, 1)) ** 2 * 0.8


def riser(dur=1.0):
    x = tt(dur)
    noise = bandpass(rng.standard_normal(len(x)), 800, 9000) * (x / dur) ** 2.3
    tone = np.sin(2 * np.pi * np.cumsum(220 + 900 * (x / dur) ** 2) / SR) * (x / dur) ** 2 * 0.25
    return (noise * 0.5 + tone) * 0.9


def reverse_crash(dur=1.0):
    return crash(dur)[::-1] * 0.8


def tick(hz_=2600, dur=0.04, g=1.0):
    x = tt(dur)
    return (np.sin(2 * np.pi * hz_ * x) * np.exp(-x * 190) +
            highpass(rng.standard_normal(len(x)), 3600) * np.exp(-x * 400) * 0.4) * g


def ping(f1=1318.5, f2=1760.0):
    """two-tone notification ding"""
    x = tt(0.5)
    a = np.sin(2 * np.pi * f1 * x) * np.exp(-x * 9)
    b = np.zeros_like(x)
    k = int(0.075 * SR)
    b[k:] = np.sin(2 * np.pi * f2 * x[:-k]) * np.exp(-x[:-k] * 7)
    return (a + b) * 0.45


def thump():
    x = tt(0.35)
    f = 70 + 90 * np.exp(-x * 25)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * 11) * 0.9


def shutter():
    x = tt(0.09)
    c1 = highpass(rng.standard_normal(len(x)), 3000) * np.exp(-x * 300)
    c2 = np.zeros_like(x)
    k = int(0.034 * SR)
    c2[k:] = highpass(rng.standard_normal(len(x) - k), 2200) * np.exp(-x[:-k] * 260) * 0.8
    return (c1 + c2) * 0.9


def chime(freqs, dur=1.2):
    x = tt(dur)
    sig = np.zeros_like(x)
    for i, f in enumerate(freqs):
        d = 0.045 * i
        m = x > d
        y = x[m] - d
        sig[m] += (np.sin(2 * np.pi * f * y) + 0.28 * np.sin(2 * np.pi * 2.01 * f * y)) * np.exp(-y * 4.5)
    return sig * 0.45


# ============================ harmony ============================
CH = {
    'Am9':   ['A2', 'E3', 'G3', 'B3', 'C4'],
    'Fmaj9': ['F2', 'C3', 'E3', 'G3', 'A3'],
    'Cmaj9': ['C3', 'E3', 'G3', 'B3', 'D4'],
    'G69':   ['G2', 'D3', 'E3', 'A3', 'B3'],
    'Dm9':   ['D3', 'F3', 'A3', 'C4', 'E4'],
    'E7sus': ['E2', 'B2', 'D3', 'A3', 'B3'],
    'E7':    ['E2', 'B2', 'D3', 'G#3', 'B3'],
}
ROOT = {'Am9': 'A1', 'Fmaj9': 'F1', 'Cmaj9': 'C2', 'G69': 'G1', 'Dm9': 'D2', 'E7sus': 'E1', 'E7': 'E1'}
PROG = ['Am9', 'Fmaj9', 'Cmaj9', 'G69', 'Am9', 'Fmaj9', 'Dm9', 'Am9']      # bar 7 is the manifesto
KICKS = []


def chord(name, t0, dur, vel=1.0, send=0.35, lp=None):
    sig_l = np.zeros(int((dur + 0.4) * SR))
    sig_r = np.zeros_like(sig_l)
    for i, n in enumerate(CH[name]):
        s = ep(hz(n), dur, vel * (0.9 if i == 0 else 0.7))
        pan = (-0.35, 0.3, -0.15, 0.4, -0.3)[i % 5]
        sig_l[:len(s)] += s * min(1, 1 - pan)
        sig_r[:len(s)] += s * min(1, 1 + pan)
    if lp:
        sig_l, sig_r = lowpass(sig_l, lp), lowpass(sig_r, lp)
    i0 = int(t0 * SR)
    n = min(len(sig_l), N - i0)
    BUS['music'][0, i0:i0 + n] += sig_l[:n] * 0.55
    BUS['music'][1, i0:i0 + n] += sig_r[:n] * 0.55
    BUS['send'][0, i0:i0 + n] += sig_l[:n] * 0.55 * send
    BUS['send'][1, i0:i0 + n] += sig_r[:n] * 0.55 * send


STAB = [(0.0, 0.85), (1.5, 0.45), (2.75, 0.4), (3.5, 0.45)]   # beat offset, length in beats

for bar, name in enumerate(PROG):
    tb = bar * BAR
    if bar == 6:
        continue                                               # manifesto bar handled below
    lp = 900 if bar == 0 else None
    for off, ln in STAB:
        chord(name, tb + off * BEAT, ln * BEAT, vel=1.0 if off == 0 else 0.8, lp=lp)
    put('music', pad([hz(n) for n in CH[name][1:4]], BAR), tb, 0.34, send=0.3)
    if bar not in (0,):
        for k in range(4):                                     # offbeat house bass
            f = hz(ROOT[name])
            put('music', bass_pluck(f * (2 if k == 3 and bar % 2 else 1)), tb + (k + 0.5) * BEAT, 0.62)
        put('music', bass_pluck(hz(ROOT[name]), 0.2), tb, 0.35)

# arp lift across Act II (bars 4-6) and a lighter one on the endcard
for bar in (3, 4, 5, 7):
    name = PROG[bar]
    tones = [hz(n) * 2 for n in CH[name][1:]]
    for s16 in range(16):
        f = tones[(s16 * 3) % len(tones)] * (2 if s16 % 8 == 7 else 1)
        g = (0.22 if bar != 7 else 0.14) * (1.0 if s16 % 4 == 0 else 0.7)
        put('music', pluck(f), bar * BAR + s16 * BEAT / 4, g, pan=0.45 if s16 % 2 else -0.45, send=0.4)

# ---------------------------- drums ----------------------------
for b in range(32):
    tb = b * BEAT
    bar = b // 4
    in_build_drop = 22 <= b <= 23                              # kick drops for the last beat pair of the build
    manifesto = 24 <= b <= 27
    if not in_build_drop and not manifesto and b != 31:
        put('drums', kick(), tb, 0.82)
        KICKS.append(tb)
    if b % 4 in (1, 3) and not manifesto and b < 22 or (b in (29, 31)):
        put('drums', clap(), tb, 0.55, pan=-0.05, send=0.35)
        put('drums', snap(), tb + 0.004, 0.25, pan=0.2)
    # hats: 8ths in bar 1, swung 16ths after
    for s in range(4):
        if bar == 0 and s % 2:
            continue
        if manifesto and s % 2:
            continue
        sw = 0.018 if s % 2 else 0.0
        vel = (1.0, 0.45, 0.7, 0.45)[s]
        put('drums', hat(), tb + s * BEAT / 4 + sw, 0.22 * vel, pan=0.28)
    if 2 <= bar <= 5 or bar == 7:
        put('drums', hat(open_=True), tb + BEAT / 2, 0.2, pan=-0.25, send=0.15)
    if 3 <= bar <= 5:
        put('drums', shaker(), tb + BEAT * 0.75, 0.16, pan=0.5)

# build (bar 6, 10-12 s): snare roll accelerating into the blast
t = 10.5
step = BEAT / 4
while t < 11.98:
    prog = (t - 10.5) / 1.5
    put('drums', snare(), t, 0.12 + 0.45 * prog ** 1.5, pan=0.1, send=0.2)
    t += step if t < 11.5 else step / 2
put('fx', riser(1.3), 10.7, 0.7, send=0.25)
put('fx', reverse_crash(1.0), 11.0, 0.5, send=0.2)

# ---------------------------- manifesto bar (12-14 s) ----------------------------
put('drums', boom(1.1, 44), 11.975, 1.35)
put('drums', crash(1.8), 12.0, 0.45, send=0.3)
chord('Dm9', 12.0, 0.7, 1.0, send=0.5)
put('music', sub_long(hz('D2'), 0.7), 12.0, 0.6)
chord('Dm9', 12.75, 0.6, 1.1, send=0.5)                         # "VOCÊ TRAZ O NEGÓCIO."
put('drums', kick(1.1), 12.75, 0.9)
KICKS.append(12.75)
put('music', sub_long(hz('D2'), 0.7), 12.75, 0.6)
chord('E7sus', 13.5, 0.22, 1.0, send=0.5)                       # "A EXP TRAZ A ESTRUTURA."
chord('E7', 13.72, 0.5, 1.05, send=0.5)
put('drums', kick(1.1), 13.5, 0.9)
KICKS.append(13.5)
put('music', sub_long(hz('E2'), 0.7), 13.5, 0.6)
for k in range(8):
    put('drums', hat(), 12.0 + k * BEAT / 2 + 0.25, 0.1, pan=0.3)
put('fx', riser(0.45), 13.8, 0.35)

# ---------------------------- UI / cut sound design ----------------------------
put('fx', boom(0.7, 52), 0.0, 0.45)
put('fx', whoosh(0.3, 400, 3400), 0.02, 0.4)
put('fx', shutter(), 0.5, 0.75)
put('fx', tick(2200), 0.75, 0.35)
put('fx', thump(), 1.0, 0.55)                                   # chapter 01
put('fx', whoosh(0.35, 300, 2600), 1.0, 0.35)
put('fx', whoosh(0.3, 600, 5200), 1.75, 0.4)                    # palette columns rise
put('fx', whoosh(0.22, 900, 6000), 2.55, 0.35)                  # orange column swallows frame
for k in range(4):
    put('fx', tick(1800 + k * 300, 0.035), 2.75 + k * 0.09, 0.22)   # weight steps
put('fx', whoosh(0.28, 500, 3800), 3.5, 0.35)                   # billboard
put('fx', whoosh(0.25, 1500, 8000), 4.0, 0.3, pan=-0.3)         # cards slide in
put('fx', whoosh(0.25, 1500, 8000), 4.08, 0.3, pan=0.3)
put('fx', chime([659.25, 987.77], 0.5), 4.75, 0.3)              # instagram
put('fx', riser(0.48), 5.02, 0.55)                              # the dive
put('fx', thump(), 5.5, 0.6)
put('fx', whoosh(0.3, 250, 2000), 5.5, 0.4)
put('fx', thump(), 6.25, 0.55)                                  # chapter 02
put('fx', whoosh(0.35, 300, 2600), 6.25, 0.35)
put('fx', whoosh(0.3, 500, 4000), 7.0, 0.35)                    # dashboard
for k in range(8):
    put('fx', tick(2800 + k * 60, 0.03), 7.15 + k * 0.085, 0.12, pan=0.2)
put('fx', whoosh(0.25, 500, 4000), 8.25, 0.35)                  # funnel
for k in range(4):
    put('fx', tick(1600 + k * 250, 0.04), 8.25 + k * 0.05, 0.25)
put('fx', whoosh(0.3, 500, 4000), 9.0, 0.35)                    # ads
for k, tn in enumerate((9.18, 9.40, 9.62)):
    put('fx', ping(1318.5 * (1 + 0.06 * k), 1760.0 * (1 + 0.06 * k)), tn, 0.4, pan=0.15, send=0.25)
put('fx', tick(1200, 0.06), 9.28, 0.3)                          # heart pop
for k in range(14):                                             # typing
    put('fx', tick(3400 + (k % 3) * 200, 0.025), 10.02 + k * 0.022, 0.13, pan=(-1) ** k * 0.15)
put('fx', whoosh(0.2, 800, 5000), 10.28, 0.3)
put('fx', ping(1567.98, 2093.0), 10.45, 0.32, send=0.2)         # #1 badge
put('fx', whoosh(0.4, 600, 5500), 10.75, 0.45)                  # marquee wall
put('fx', chime([440.0, 554.37, 659.25, 880.0], 1.6), 14.25, 0.5, send=0.4)   # endcard
put('fx', tick(900, 0.07), 14.67, 0.4)                          # CTA pop
put('fx', whoosh(0.3, 3000, 12000), 15.2, 0.12)                 # shine
put('fx', whoosh(0.3, 400, 2600), 15.7, 0.25)                   # tail into the loop

# ============================ mix ============================
duck = np.ones(N)
for tk in KICKS:
    i0 = int(tk * SR)
    x = np.arange(min(int(0.3 * SR), N - i0)) / SR
    duck[i0:i0 + len(x)] *= 1 - 0.5 * np.exp(-x * 12)
BUS['music'] *= duck

# convolution reverb (stereo, decorrelated tails)
irl = int(1.9 * SR)
x = np.arange(irl) / SR
irs = []
for ch in range(2):
    ir = rng.standard_normal(irl) * np.exp(-x / 0.42)
    ir = lowpass(ir, 5200)
    ir[:int(0.022 * SR)] = 0
    irs.append(ir / np.sqrt(np.sum(ir ** 2)))
wet = np.zeros((2, N))
L = N + irl
for ch in range(2):
    sp = np.fft.rfft(BUS['send'][ch], L) * np.fft.rfft(irs[ch], L)
    wet[ch] = np.fft.irfft(sp, L)[:N]
wet = highpass(wet[0], 180)[None, :], highpass(wet[1], 180)[None, :]
wet = np.vstack(wet) * 0.55

mix = BUS['drums'] + BUS['music'] + BUS['fx'] * 0.9 + wet
# drop gap: near-silence on the solid-orange seal, then the boom lands on the cut
tg = np.arange(N) / SR
gate = 1 - 0.88 * np.clip((tg - 11.90) / 0.02, 0, 1) * np.clip((11.975 - tg) / 0.008, 0, 1)
mix *= gate[None, :]
mix = np.tanh(mix * 1.15)
mix *= 0.95 / np.max(np.abs(mix))

nf = int(0.015 * SR)                                            # seamless loop seam
fade = np.linspace(0, 1, nf)
mix[:, :nf] = mix[:, :nf] * fade + mix[:, -nf:] * (1 - fade)
mix[:, -nf:] *= fade[::-1]

out = (mix.T * 32767).astype(np.int16)
with wave.open('/tmp/exp-film.wav', 'wb') as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(out.tobytes())
print('wrote /tmp/exp-film.wav', out.shape)

# beat-grid validation on every kick: measure the audible attack above 1.5 kHz
# (a 5.8 ms RMS window would otherwise read each cycle of a 55 Hz bass note as an onset)
mono = highpass(mix.mean(axis=0), 1500)
hop = 256
e = np.sqrt(np.convolve(mono ** 2, np.ones(hop) / hop, mode='same'))[::hop]
onset = np.maximum(np.diff(e), 0)
errs = []
for tk in KICKS:
    c = int(tk * SR / hop)
    win = onset[max(0, c - 8):c + 9]
    errs.append((np.argmax(win) + max(0, c - 8) - c) * hop / SR * 1000)
errs = np.abs(np.array(errs))
print(f'kick grid: {len(errs)} kicks, mean |err| {errs.mean():.1f} ms, max {errs.max():.1f} ms')
assert errs.max() < 30, 'beat grid off'
print('grid OK')
