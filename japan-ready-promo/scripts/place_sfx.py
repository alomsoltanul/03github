"""Write the SFX <audio> cues into index.html, timed from the voice's word timings.

Re-run after scripts/make_voice.py so every sound stays on its word.
    python3 scripts/place_sfx.py
"""

import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cap_js = open(os.path.join(ROOT, "assets/data/captions.js"), encoding="utf-8").read()
CAP = json.loads(cap_js[cap_js.index("{") : cap_js.rindex("}") + 1])
L = {l["id"]: l for l in CAP["lines"]}
clean = lambda w: re.sub(r"[^a-z0-9']", "", w.lower())


def W(lid, w):
    return next(x for x in L[lid]["words"] if clean(x["w"]) == clean(w))


DUR = {"whoosh": 0.57, "whoosh-short": 0.57, "whoosh-cinematic": 3.0, "pop": 0.6, "click-soft": 0.37, "click": 0.37, "sparkle": 1.6,
       "chime": 2.0, "typing": 1.0, "impact-bass-1": 1.6, "cabin-chime": 2.3, "station-chime": 2.4, "plane-pass": 6.5,
       "train-ambience": 5.6, "split-flap": 1.4}
EXT = {k: ("wav" if k in ("cabin-chime", "station-chime", "plane-pass", "train-ambience", "split-flap") else "mp3") for k in DUR}

cues = []
c = lambda t, name, vol: cues.append((round(t, 3), name, vol))

# 1 · globe
c(0.05, "whoosh-cinematic", 0.3)
c(L["L01"]["start"] + 0.05, "pop", 0.45)
c(W("L02", "Japan")["s"] - 0.9, "whoosh-short", 0.3)
c(W("L02", "Japan")["s"] + 0.95, "pop", 0.45)
c(5.75, "whoosh", 0.3)
# 2 · reasons
for lid, w in (("L03", "work"), ("L04", "degree"), ("L05", "trip")):
    c(W(lid, w)["s"] - 0.05, "pop", 0.4)
c(12.3, "whoosh-short", 0.3)
# 3 · flight
c(12.95, "cabin-chime", 0.4)
c(13.2, "plane-pass", 0.5)
c(19.5, "whoosh", 0.35)
# 4 · arrival
c(20.15, "impact-bass-1", 0.25)
c(20.45, "split-flap", 0.45)
t9 = W("L09", "everything")["s"]
for i in range(0, 10, 2):
    c(t9 + i * 0.17, "click-soft", 0.32)
# 5 · everyday
c(L["J01"]["start"] - 0.75, "station-chime", 0.42)
c(25.0, "train-ambience", 0.38)
segB = L["L11"]["start"] - 0.25
c(segB, "whoosh-short", 0.32)
c(segB + 0.4, "typing", 0.22)
c(segB + 1.7, "click", 0.45)
segC = L["L12"]["start"] - 0.2
c(segC, "whoosh-short", 0.32)
c(L["J02"]["start"] - 0.05, "pop", 0.38)
c(L["J02"]["start"] + 1.4, "pop", 0.22)
# 6 · ticket → language
c(38.65, "whoosh-short", 0.32)
c(W("L14", "language")["s"] - 0.2, "sparkle", 0.28)
# 7 · product
c(44.7, "impact-bass-1", 0.22)
c(44.75, "sparkle", 0.25)
h, n1 = W("L15", "hiragana")["s"], W("L15", "N1.")["s"]
for i in range(6):
    c(h + (n1 - h) * i / 5, "click-soft", 0.26)
for lid in ("L16", "L17", "L18"):
    c(L[lid]["start"] - 0.3, "whoosh-short", 0.28)
for i in range(4):
    c(L["L17"]["start"] - 0.3 + 0.75 + i * 0.62, "click-soft", 0.22)
c(W("L17", "forget")["s"], "whoosh-short", 0.22)
c(W("L18", "listening")["s"], "click", 0.3)
for i in range(4):
    c(W("L18", "mock")["s"] - 0.2 + 0.5 + i, "click-soft", 0.16)
# 8 · goals
for lid in ("L19", "L20", "L21"):
    c(L[lid]["start"] - 0.3, "whoosh-short", 0.28)
    c(L[lid]["start"], "pop", 0.35)
# 9 · close
c(79.95, "whoosh-cinematic", 0.28)
c(W("L22", "start")["s"] - 0.2, "sparkle", 0.28)
c(L["J03"]["start"] - 0.1, "chime", 0.3)

tags = []
track_free = {}
for i, (t, name, vol) in enumerate(sorted(cues)):
    d = DUR[name]
    tr = 30
    while track_free.get(tr, 0) > t:
        tr += 1
    track_free[tr] = t + d + 0.01
    tags.append(f'      <audio id="sfx-{i + 1:02d}" src="assets/sfx/{name}.{EXT[name]}" data-start="{t}" data-duration="{d}" data-track-index="{tr}" data-volume="{vol}"></audio>')

p = os.path.join(ROOT, "index.html")
s = open(p, encoding="utf-8").read()
s = re.sub(r"(<!-- SFX_START -->\n).*?(\s*<!-- SFX_END -->)", lambda m: m.group(1) + "\n".join(tags) + m.group(2), s, flags=re.S)
open(p, "w", encoding="utf-8").write(s)
print(len(tags), "sfx cues placed")
