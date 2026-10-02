"""Synthesize the original music bed for the Japanese Shikhi promo.

Fully deterministic (seeded) and royalty-free: every sound is generated here.
Koto-like plucks use Karplus-Strong; the bright sections sit in the Japanese
"yo" pentatonic scale, the night/exam section switches to the darker "in" scale.
Section boundaries match the scene timings in index.html.

    python3 scripts/make_bgm.py            # writes assets/audio/bgm.wav
"""

import os
import numpy as np
from scipy.signal import fftconvolve, butter, lfilter
from scipy.io import wavfile

SR = 44100
DUR = 53.0
BPM = 100.0
BEAT = 60.0 / BPM
N = int(SR * DUR)
rng = np.random.default_rng(1284)

L = np.zeros(N)
R = np.zeros(N)


def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12)


# D yo scale (D E G A B) and D in scale (D Eb G A Bb), as MIDI degrees across octaves
YO = [0, 2, 5, 7, 9]
IN = [0, 1, 5, 7, 8]


def deg(scale, d, base=62):
    o, i = divmod(d, len(scale))
    return base + 12 * o + scale[i]


def add(sig, t, pan=0.0, gain=1.0):
    i = int(t * SR)
    if i >= N or i + len(sig) <= 0:
        return
    s = sig[: max(0, N - i)] * gain
    lg = np.cos((pan + 1) * np.pi / 4)
    rg = np.sin((pan + 1) * np.pi / 4)
    L[i : i + len(s)] += s * lg
    R[i : i + len(s)] += s * rg


def koto(m, dur=1.6, bright=0.5):
    f = midi(m)
    n = int(SR * dur)
    p = max(2, int(SR / f))
    exc = rng.uniform(-1, 1, p)
    # soften the excitation for a plucked-silk tone
    exc = np.convolve(exc, np.ones(3) / 3, mode="same")
    x = np.zeros(n)
    x[:p] = exc
    damp = 0.996 - (1 - bright) * 0.004
    # Karplus-Strong as an IIR filter: y[k] = x[k] + damp/2 * (y[k-p] + y[k-p-1])
    a = np.zeros(p + 2)
    a[0] = 1.0
    a[p] = -damp * 0.5
    a[p + 1] = -damp * 0.5
    out = lfilter([1.0], a, x)
    env = np.minimum(1, np.arange(n) / (0.002 * SR)) * np.exp(-np.arange(n) / (SR * dur * 0.45))
    return out * env * 0.5


def sine_bass(m, dur):
    n = int(SR * dur)
    t = np.arange(n) / SR
    f = midi(m)
    s = np.sin(2 * np.pi * f * t) + 0.25 * np.sin(4 * np.pi * f * t)
    env = np.minimum(1, t / 0.01) * np.exp(-t / (dur * 0.6))
    return np.tanh(1.6 * s * env) * 0.42


def kick():
    n = int(SR * 0.32)
    t = np.arange(n) / SR
    f = 46 + 90 * np.exp(-t * 28)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t * 11) * 0.95


def hat(dec=40.0, g=0.18):
    n = int(SR * 0.09)
    t = np.arange(n) / SR
    x = rng.uniform(-1, 1, n)
    b, a = butter(2, 7000 / (SR / 2), "high")
    return lfilter(b, a, x) * np.exp(-t * dec) * g


def clap():
    n = int(SR * 0.22)
    t = np.arange(n) / SR
    x = rng.uniform(-1, 1, n)
    b, a = butter(2, [900 / (SR / 2), 3200 / (SR / 2)], "band")
    env = np.exp(-t * 18) * (1 + 0.6 * (np.sin(2 * np.pi * 90 * t) > 0) * (t < 0.03))
    return lfilter(b, a, x) * env * 0.5


def pad(notes, dur, g=0.06, cutoff=1800):
    n = int(SR * dur)
    t = np.arange(n) / SR
    s = np.zeros(n)
    for m in notes:
        for det in (-0.08, 0.0, 0.07):
            f = midi(m + det)
            s += 2 * ((t * f) % 1.0) - 1
    b, a = butter(2, cutoff / (SR / 2), "low")
    s = lfilter(b, a, s)
    att = min(0.6, dur / 3)
    env = np.minimum(1, t / att) * np.minimum(1, (dur - t) / min(0.5, dur / 3))
    return s * env * g / len(notes)


def noise_riser(dur, g=0.18):
    n = int(SR * dur)
    t = np.arange(n) / SR
    x = rng.uniform(-1, 1, n)
    out = np.zeros(n)
    # sweep a one-pole lowpass upward
    y = 0.0
    for k in range(n):
        c = 0.02 + 0.6 * (t[k] / dur) ** 2
        y += c * (x[k] - y)
        out[k] = y
    return out * (t / dur) ** 2 * g


# --- harmony: D yo progression, one chord per bar ------------------------------
BAR = BEAT * 4
CHORDS_YO = [(50, [62, 64, 69]), (55, [62, 67, 69]), (47, [62, 64, 71]), (57, [62, 64, 69])]
CHORDS_IN = [(50, [62, 63, 69]), (46, [62, 65, 70])]


def chord_at(t, night=False):
    seq = CHORDS_IN if night else CHORDS_YO
    return seq[int(t // BAR) % len(seq)]


def groove(t0, t1, kick_on=True, clap_on=False, hats=True, bass=True, arp=True, arp_bright=0.55, density=2, night=False, hat_g=0.18):
    """Lay down beats from t0 to t1 on the global beat grid."""
    first = int(np.ceil(t0 / (BEAT / 2) - 1e-6))
    last = int(np.floor((t1 - 1e-6) / (BEAT / 2)))
    scale = IN if night else YO
    for k in range(first, last + 1):
        t = k * BEAT / 2
        on_beat = k % 2 == 0
        beat_in_bar = (k // 2) % 4
        root, _ = chord_at(t, night)
        if kick_on and on_beat and beat_in_bar in (0, 2):
            add(kick(), t, 0, 0.7)
        if kick_on and not on_beat and beat_in_bar == 3 and density > 2:
            add(kick(), t, 0, 0.55)
        if clap_on and on_beat and beat_in_bar in (1, 3):
            add(clap(), t, 0.1, 0.8)
        if hats and not on_beat:
            add(hat(g=hat_g), t, 0.35, 1.0)
        if bass and on_beat and beat_in_bar in (0, 2):
            add(sine_bass(root - 12 if root > 52 else root, BEAT * 1.6), t, 0, 1.0)
        if arp and (density >= 2 or on_beat):
            pattern = [0, 2, 4, 3, 5, 4, 2, 3]
            d = pattern[k % len(pattern)] + (1 if (k // 8) % 2 else 0)
            add(koto(deg(scale, d, 62), 1.2, arp_bright), t, -0.3 if k % 2 else 0.3, 1.0)


def melody(t0, notes, step=BEAT / 2, base=74, scale=YO, g=0.75, dur=1.8, bright=0.6):
    g *= 1.7
    for i, d in enumerate(notes):
        if d is None:
            continue
        add(koto(deg(scale, d, base), dur, bright), t0 + i * step, 0.15, g)


def pads(t0, t1, night=False, g=0.06, cutoff=1800):
    t = t0
    while t < t1 - 0.05:
        nxt = min(t1, (np.floor(t / BAR) + 1) * BAR)
        _, notes = chord_at(t, night)
        add(pad(notes, nxt - t + 0.3, g, cutoff), t, 0, 1.0)
        t = nxt


# --- arrangement (times match the scene cuts in index.html) ---------------------
# A 0.0–3.0 hook
groove(0.0, 3.0, density=3, clap_on=False)
pads(0.0, 3.0)
melody(0.0, [0, 2, 4, None, 3, 2, 4, 5, None, 4], base=74)

# B 3.0–4.6 "LYING." — the band stops, one low drone
add(pad([38, 45, 50], 1.6, 0.2, 900), 3.0, 0, 1.0)

# C 4.6–10.0 the ball: light & playful, then the melt
groove(4.6, 6.6, kick_on=False, bass=True, density=2, arp_bright=0.5, hat_g=0.14)
melody(4.7, [2, None, 4, None, 5, 4, None, 2], base=74)
melody(6.6, [5, 4, 3, 2, 1, 0], step=0.17, base=74, dur=1.2)  # descending "deflate"
add(pad([50, 57, 62], 3.4, 0.1, 1200), 6.6, 0, 1.0)
melody(8.0, [0, None, None, -1], step=BEAT, base=74, g=0.5, dur=2.4, bright=0.3)

# D 10.0–19.4 the thieves: bouncy groove, accent on each bite
groove(10.0, 19.4, density=3, clap_on=True)
pads(10.0, 19.4, g=0.045)
for tb in (12.15, 14.15, 16.15, 18.15):
    melody(tb, [7, 5], step=0.09, base=62, g=0.6, dur=0.8)

# E 19.4–24.2 night: "in" scale, no drums, then tension into the tabs
pads(19.4, 24.2, night=True, g=0.13, cutoff=1100)
melody(19.6, [0, None, 2, None, 3, None, 2, 1], step=BEAT / 2, base=62, scale=IN, g=0.7, dur=2.4, bright=0.35)
groove(22.2, 24.2, kick_on=False, bass=False, arp=True, density=2, night=True, arp_bright=0.5, hat_g=0.22)
add(noise_riser(2.0, 0.22), 22.2, 0, 1.0)

# F 24.2–31.6 reveal: full, bright
groove(24.2, 31.6, density=3, clap_on=True, arp_bright=0.65)
pads(24.2, 31.6, g=0.06, cutoff=2400)
melody(24.25, [4, 5, 7, None, 5, 4, 2, None, 4, 5, 7, 9, None, 7], base=74, g=0.7)
melody(29.7, [9, None, 7, 9], step=BEAT / 2, base=74, g=0.7)

# G 31.6–37.0 slipping → reviewed
groove(31.6, 34.0, kick_on=True, clap_on=False, density=2, arp_bright=0.4, hat_g=0.12)
pads(31.6, 34.0, night=True, g=0.05, cutoff=1300)
groove(34.0, 37.0, density=3, clap_on=True, arp_bright=0.6)
melody(36.0, [4, 7, 9], step=0.11, base=74, g=0.75, dur=1.6)

# H 37.0–40.8 morning: warm and light
groove(37.0, 40.8, kick_on=True, clap_on=False, density=2, arp_bright=0.55, hat_g=0.12)
pads(37.0, 40.8, g=0.06, cutoff=2000)
melody(37.05, [2, 4, 5, None, 4, 2, 4, None], base=74)

# I 40.8–42.8 sleep: drums drop, dreamy
pads(40.8, 43.0, g=0.12, cutoff=1500)
melody(41.0, [9, None, 7, None, 5, None, 4], step=BEAT / 2, base=74, g=0.55, dur=2.6, bright=0.4)

# J 42.8–47.8 made with AI: build
groove(43.6, 46.2, kick_on=True, clap_on=False, density=2, hat_g=0.2)
add(noise_riser(2.6, 0.2), 43.6, 0, 1.0)
groove(46.2, 47.8, density=3, clap_on=True, arp_bright=0.7)
pads(43.6, 47.8, g=0.05, cutoff=2200)

# K 47.8–53.0 finale
groove(47.8, 52.0, density=3, clap_on=True, arp_bright=0.65)
pads(47.8, 53.0, g=0.06, cutoff=2400)
melody(47.85, [4, 5, 7, None, 9, 7, 5, None, 4, 5, 7, 9], base=74, g=0.7)
add(kick(), 52.0, 0, 0.9)
for m in (50, 57, 62, 64, 69):
    add(koto(m + 12, 2.6, 0.6), 52.0, 0, 0.55)

# --- space + master -------------------------------------------------------------
ir_len = int(SR * 1.6)
tt = np.arange(ir_len) / SR
irL = rng.standard_normal(ir_len) * np.exp(-tt * 3.2)
irR = rng.standard_normal(ir_len) * np.exp(-tt * 3.2)
irL[0] = irR[0] = 0
wetL = fftconvolve(L, irL)[:N] * 0.018
wetR = fftconvolve(R, irR)[:N] * 0.018
L2, R2 = L + wetL, R + wetR

# gentle glue: soft clip then normalise to -3 dBFS peak
mix = np.stack([L2, R2], axis=1)
# normalise first, then a mild soft-knee limit (no hard distortion)
mix /= np.percentile(np.abs(mix), 99.95) + 1e-9
mix = np.tanh(mix * 1.3) / np.tanh(1.3)
fade = np.ones(N)
fo = int(SR * 0.8)
fade[-fo:] = np.linspace(1, 0, fo)
mix *= fade[:, None]
mix /= np.max(np.abs(mix)) + 1e-9
mix *= 10 ** (-3 / 20)

out = os.path.join(os.path.dirname(__file__), "..", "assets", "audio", "bgm.wav")
wavfile.write(out, SR, (mix * 32767).astype(np.int16))
print("wrote", os.path.normpath(out), f"{DUR:.1f}s")
