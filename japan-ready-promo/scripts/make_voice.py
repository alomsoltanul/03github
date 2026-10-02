"""Build the voiceover + word-level caption timings for the promo.

English narration: Kokoro-82M (af_heart) via kokoro-onnx, with phoneme overrides
for words espeak gets wrong (Shikhi, hiragana). Japanese lines: Kokoro Japanese
voices, phonemized with misaki + pyopenjtalk.

Word timings come from the model's own duration predictor. The stock ONNX file
does not expose it, so scripts/patch_kokoro.py adds a `duration` output first.

    KOKORO_DIR=/path/to/models python3 scripts/make_voice.py
writes assets/audio/vo.wav and assets/data/captions.js
"""

import json
import os
import re

import numpy as np
import pyloudnorm as pyln
import soundfile as sf
from kokoro_onnx import Kokoro
from scipy.signal import butter, fftconvolve, lfilter, resample_poly

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
KDIR = os.environ.get("KOKORO_DIR", ".")
SR_OUT = 48000

cfg = json.load(open(os.path.join(HERE, "vo_script.json"), encoding="utf-8"))
k = Kokoro(os.path.join(KDIR, "kokoro-v1.0-timed.onnx"), os.path.join(KDIR, "voices-v1.0.bin"))
assert k.has_timings, "run scripts/patch_kokoro.py first (model needs a duration output)"

_ja = None


def ja_phonemes(text):
    global _ja
    if _ja is None:
        from misaki import ja

        _ja = ja.JAG2P(version="pyopenjtalk")
    ps, _ = _ja(text)
    # misaki appends a same-length pitch-accent annotation; keep only the phonemes
    return ps[: len(ps) // 2]


def en_phonemes(text):
    ps = k.tokenizer.phonemize(text, "en-us")
    for a, b in cfg["phoneme_overrides"].items():
        ps = ps.replace(a, b)
    return ps


def groups_from_timings(timings):
    """Split phoneme timings into spoken words at space tokens."""
    words, cur = [], []
    for t in timings:
        if t.phoneme == " ":
            if cur:
                words.append(cur)
            cur = []
        else:
            cur.append(t)
    if cur:
        words.append(cur)
    out = []
    for g in words:
        spoken = [t for t in g if re.search(r"[^\s.,!?;:—–\-…]", t.phoneme)]
        if spoken:
            out.append((spoken[0].start, spoken[-1].end))
    return out


def groups_from_text(text):
    """Phoneme words (space separated, punctuation-only tokens dropped) for a text."""
    return [g for g in en_phonemes(text).split() if re.search(r"[^.,!?;:—–\-…]", g)]


def pa_effect(x, sr):
    """Station PA: band-limited, slightly boxy, short reverb tail."""
    b, a = butter(2, [350 / (sr / 2), 3600 / (sr / 2)], "band")
    y = lfilter(b, a, x) * 1.6
    n = int(sr * 0.5)
    t = np.arange(n) / sr
    rng = np.random.default_rng(3)
    ir = rng.standard_normal(n) * np.exp(-t * 9)
    ir[0] = 1.0
    y = fftconvolve(y, ir)[: len(x) + n] * 0.6
    return np.tanh(y * 1.2)


timeline = []
pieces = []
t = cfg["lead_in"]
for line in cfg["lines"]:
    lang = line.get("lang", "en")
    t += line.get("pre", 0.0)
    if lang == "en":
        ps = en_phonemes(line["text"])
        audio, sr, timings = k.create_timed(ps, voice=cfg["en_voice"], speed=cfg["en_speed"], is_phonemes=True)
    else:
        ps = ja_phonemes(line["text"])
        audio, sr, timings = k.create_timed(ps, voice=line["voice"], speed=0.95, is_phonemes=True)
    audio = np.asarray(audio, dtype=np.float64)
    if line.get("effect") == "pa":
        audio = pa_effect(audio, sr)

    entry = {"id": line["id"], "lang": lang, "text": line["text"], "start": round(t, 3), "end": round(t + len(audio) / sr, 3)}
    if lang == "en":
        text_words = line["text"].split()
        spoken = groups_from_timings(timings)
        # cumulative phoneme-word count of each prefix: handles "N4," -> "en four"
        # and context merges like "on the" -> one group
        cum = [len(groups_from_text(" ".join(text_words[: i + 1]))) for i in range(len(text_words))]
        if cum[-1] != len(spoken):
            print(f"  ! {line['id']}: {cum[-1]} groups expected, {len(spoken)} spoken; scaling")
            cum = [round(c * len(spoken) / cum[-1]) for c in cum]
        words, prev = [], 0
        for i, w in enumerate(text_words):
            lo, hi = prev, max(cum[i], prev)
            if hi > lo:
                s, e = spoken[lo][0], spoken[hi - 1][1]
            else:  # merged into the previous group: share its end
                s = e = spoken[max(0, lo - 1)][1]
            words.append({"w": w, "s": round(t + s, 3), "e": round(t + e, 3)})
            prev = hi
        entry["words"] = words
    else:
        spoken = groups_from_timings(timings)
        s0, e0 = (spoken[0][0], spoken[-1][1]) if spoken else (0, len(audio) / sr)
        entry["speech"] = [round(t + s0, 3), round(t + e0, 3)]
        entry["en"] = line.get("en", "")
    timeline.append(entry)
    pieces.append((t, audio, sr))
    print(f"{line['id']} {t:6.2f}–{t + len(audio) / sr:6.2f}  {line['text']}")
    t += len(audio) / sr + line.get("pause", 0.4)

total = t + cfg["tail"]
out = np.zeros(int(total * SR_OUT) + SR_OUT)
for start, audio, sr in pieces:
    a = resample_poly(audio, SR_OUT, sr)
    i = int(start * SR_OUT)
    out[i : i + len(a)] += a
out = out[: int(total * SR_OUT)]

meter = pyln.Meter(SR_OUT)
gain = 10 ** ((-16.0 - meter.integrated_loudness(out)) / 20)
out = out * gain
peak = np.max(np.abs(out))
if peak > 0.89:
    out *= 0.89 / peak

sf.write(os.path.join(ROOT, "assets", "audio", "vo.wav"), np.stack([out, out], axis=1).astype(np.float32), SR_OUT, subtype="PCM_16")
data = {"duration": round(total, 3), "lines": timeline}
with open(os.path.join(ROOT, "assets", "data", "captions.js"), "w", encoding="utf-8") as f:
    f.write("window.CAPTIONS = " + json.dumps(data, ensure_ascii=False, indent=1) + ";\n")
print(f"total {total:.2f}s  ->  assets/audio/vo.wav, assets/data/captions.js")
