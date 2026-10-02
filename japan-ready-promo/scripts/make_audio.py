"""Synthesize the story SFX and a calm music bed that ducks under the voice.

All sounds are generated here (seeded, royalty-free). Bundled HyperFrames SFX
(Pixabay licence) cover the generic UI sounds; see assets/sfx/CREDITS.md.

    python3 scripts/make_audio.py      # needs assets/audio/vo.wav first
"""

import os

import numpy as np
import pyloudnorm as pyln
import soundfile as sf
from scipy.signal import butter, fftconvolve, lfilter

SR = 48000
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rng = np.random.default_rng(2026)


def save(name, x, peak=0.8):
    x = x / (np.max(np.abs(x)) + 1e-9) * peak
    sf.write(os.path.join(ROOT, "assets", "sfx", name), np.stack([x, x], 1).astype(np.float32), SR, subtype="PCM_16")


def tone(f, dur, decay=4.0, harm=(1, 0.35, 0.12)):
    t = np.arange(int(SR * dur)) / SR
    s = sum(a * np.sin(2 * np.pi * f * (i + 1) * t) for i, a in enumerate(harm))
    return s * np.exp(-t * decay) * np.minimum(1, t / 0.004)


def bp(x, lo, hi, order=2):
    b, a = butter(order, [lo / (SR / 2), hi / (SR / 2)], "band")
    return lfilter(b, a, x)


def lp(x, hi, order=2):
    b, a = butter(order, hi / (SR / 2), "low")
    return lfilter(b, a, x)


def verb(x, secs=1.2, amt=0.25):
    n = int(SR * secs)
    t = np.arange(n) / SR
    ir = rng.standard_normal(n) * np.exp(-t * 5)
    ir[0] = 1 / amt
    return fftconvolve(x, ir)[: len(x) + n] * amt


# cabin "ding-dong" (generic two-tone)
x = np.zeros(int(SR * 2.4))
a, b = tone(784, 1.6, 3.2), tone(622, 1.8, 2.8)
x[: len(a)] += a
x[int(SR * 0.42) : int(SR * 0.42) + len(b)] += b
save("cabin-chime.wav", verb(x, 1.0, 0.2), 0.7)

# station chime (generic ascending three-note, not a real railway melody)
x = np.zeros(int(SR * 2.4))
for i, f in enumerate([659, 784, 988]):
    s = tone(f, 1.4, 3.5, (1, 0.5, 0.2))
    x[int(SR * 0.22 * i) : int(SR * 0.22 * i) + len(s)] += s
save("station-chime.wav", bp(verb(x, 1.2, 0.3), 300, 5000), 0.7)

# plane pass: low jet rumble swelling and fading over ~6.5s
n = int(SR * 6.5)
t = np.arange(n) / SR
noise = rng.standard_normal(n)
rumble = lp(noise, 380) * 1.0 + bp(noise, 600, 2600) * 0.25
env = np.sin(np.pi * np.clip(t / 6.5, 0, 1)) ** 1.6
save("plane-pass.wav", rumble * env, 0.75)

# train interior: rumble + rail clacks every ~0.9s (pairs)
n = int(SR * 5.6)
t = np.arange(n) / SR
x = lp(rng.standard_normal(n), 220) * 0.9 + bp(rng.standard_normal(n), 300, 900) * 0.2
for k in np.arange(0.3, 5.5, 0.92):
    for d in (0.0, 0.11):
        i = int((k + d) * SR)
        c = bp(rng.standard_normal(int(SR * 0.05)), 900, 3500) * np.exp(-np.arange(int(SR * 0.05)) / (SR * 0.008))
        x[i : i + len(c)] += c * 2.5
env = np.minimum(1, t / 0.6) * np.minimum(1, (5.6 - t) / 0.8)
save("train-ambience.wav", x * env, 0.6)

# split-flap clatter (~1.3s of fast irregular flaps)
n = int(SR * 1.4)
x = np.zeros(n)
pos = 0.0
while pos < 1.25:
    i = int(pos * SR)
    L = int(SR * 0.018)
    c = bp(rng.standard_normal(L), 1200, 6000) * np.exp(-np.arange(L) / (SR * 0.004))
    x[i : i + L] += c * (0.6 + 0.4 * rng.random())
    pos += 0.022 + 0.03 * rng.random()
save("split-flap.wav", x, 0.6)

# --- music bed: calm, koto-like plucks in D yo scale over warm pads, ducked under the voice
vo, vsr = sf.read(os.path.join(ROOT, "assets", "audio", "vo.wav"))
vo = vo.mean(1) if vo.ndim > 1 else vo
DUR = len(vo) / vsr
N = int(SR * DUR)
L = np.zeros(N)
R = np.zeros(N)


def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def koto(m, dur=2.4, bright=0.45):
    f = midi(m)
    n = int(SR * dur)
    p = max(2, int(SR / f))
    xx = np.zeros(n)
    xx[:p] = np.convolve(rng.uniform(-1, 1, p), np.ones(3) / 3, mode="same")
    damp = 0.996 - (1 - bright) * 0.004
    aa = np.zeros(p + 2)
    aa[0], aa[p], aa[p + 1] = 1.0, -damp / 2, -damp / 2
    out = lfilter([1.0], aa, xx)
    return out * np.exp(-np.arange(n) / (SR * dur * 0.5)) * 0.5


def pad(notes, dur, g):
    n = int(SR * dur)
    tt = np.arange(n) / SR
    s = np.zeros(n)
    for m in notes:
        for det in (-0.07, 0.0, 0.06):
            s += 2 * ((tt * midi(m + det)) % 1.0) - 1
    s = lp(s, 1400)
    att = min(1.2, dur / 3)
    return s * np.minimum(1, tt / att) * np.minimum(1, (dur - tt) / min(1.0, dur / 3)) * g / len(notes)


def add(sig, t0, pan=0.0, g=1.0):
    i = int(t0 * SR)
    if i >= N:
        return
    s = sig[: N - i] * g
    L[i : i + len(s)] += s * np.cos((pan + 1) * np.pi / 4)
    R[i : i + len(s)] += s * np.sin((pan + 1) * np.pi / 4)


YO = [0, 2, 5, 7, 9]
deg = lambda d, base=62: base + 12 * (d // 5) + YO[d % 5]
BAR = 60 / 84 * 4
chords = [[50, 57, 62, 64], [55, 62, 67, 69], [47, 54, 62, 66], [57, 62, 64, 69]]
t = 0.0
i = 0
while t < DUR:
    add(pad(chords[i % 4], BAR + 0.6, 0.11), t)
    add(pad([chords[i % 4][0] - 12], BAR + 0.4, 0.06), t)
    i += 1
    t += BAR
pattern = [0, 2, 4, 2, 5, 4, 2, 1]
beat = 60 / 84
k = 0
t = 0.0
while t < DUR - 2:
    if k % 2 == 0 or (k % 8) in (3, 7):
        add(koto(deg(pattern[k % 8] + (5 if (k // 16) % 2 else 0), 62), 2.2), t, -0.25 if k % 2 else 0.25, 0.32)
    k += 1
    t += beat / 2
# soft pulse on the downbeats from the reveal onward
for tb in np.arange(44.6, DUR - 3, beat):
    n = int(SR * 0.3)
    tt = np.arange(n) / SR
    add(np.sin(2 * np.pi * (52 + 40 * np.exp(-tt * 30)) * tt) * np.exp(-tt * 12) * 0.35, tb)

mix = np.stack([L, R], 1)
mix = fftconvolve(mix, np.stack([rng.standard_normal(int(SR * 1.5)) * np.exp(-np.arange(int(SR * 1.5)) / (SR * 0.35))] * 2, 1), axes=0)[:N] * 0.012 + mix

# sidechain: duck the music while she speaks
env = np.abs(np.interp(np.arange(N) / SR, np.arange(len(vo)) / vsr, vo))
win = int(SR * 0.08)
env = np.convolve(env, np.ones(win) / win, mode="same")
env = env / (env.max() + 1e-9)
gate = (env > 0.04).astype(float)
att, rel = int(SR * 0.12), int(SR * 0.6)
g = np.zeros(N)
cur = 0.0
for j in range(0, N, 480):  # 10 ms control rate
    target = gate[j]
    cur += (target - cur) * (480 / att if target > cur else 480 / rel)
    g[j : j + 480] = cur
duck = 1 - 0.55 * np.clip(g, 0, 1)
mix *= duck[:, None]
fade = np.ones(N)
fade[: int(SR * 1.2)] = np.linspace(0, 1, int(SR * 1.2))
fade[-int(SR * 2.5) :] = np.linspace(1, 0, int(SR * 2.5))
mix *= fade[:, None]
meter = pyln.Meter(SR)
mix *= 10 ** ((-27.0 - meter.integrated_loudness(mix)) / 20)
mix /= max(1.0, np.max(np.abs(mix)) / 0.8)
sf.write(os.path.join(ROOT, "assets", "audio", "bgm.wav"), mix.astype(np.float32), SR, subtype="PCM_16")
print("wrote sfx + bgm", round(DUR, 2), "s")
