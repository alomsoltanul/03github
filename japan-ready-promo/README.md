# Japanese Shikhi — "Ready for Japan" (16:9)

An 88-second landscape motion-graphics film with map animations, a female voiceover and
kinetic captions. It follows a student in Dhaka who has decided to go to Japan for work,
study or travel, and shows where the language becomes the real hurdle. Japanese Shikhi
comes in quietly in the second half.

Final render: `renders/japanese-shikhi-ready-for-japan-16x9.mp4` (1920×1080, 30 fps, −16 LUFS).

## Script

| Time | Voice | Picture |
| --- | --- | --- |
| 0:00 | This is Dhaka. And you've made up your mind. Japan is next. | Globe turns to Bangladesh, pin on Dhaka (ঢাকা), Japan lights up, route draws |
| 0:06 | Maybe it's work. Maybe it's a degree. Or a trip you've been saving up for. | Japan map: 仕事 Work (Tokyo), 留学 Study (Kyoto), 旅行 Travel (Hokkaido) |
| 0:13 | Getting there is the easy part. Almost five thousand kilometers. A few hours in the air. | Plane flies the Dhaka → Tokyo great circle; counter lands on 4,880 km |
| 0:20 | Then you land. And everything around you is in Japanese. | Split-flap arrivals board (ダッカ / 到着), station signs with no English |
| 0:25 | 「次は、新宿です。」 The announcement on the train. | Yamanote LED: 渋谷 → 原宿 → 代々木 → 新宿 |
| 0:30 | The form at the city office. | 住民異動届 (residence form) |
| 0:32 | The first question in your job interview. 「自己紹介をお願いします。」 | Interview: "Please introduce yourself." |
| 0:38 | A ticket gets you to Japan. The language is what lets you live there. | Boarding pass DAC → TYO, then 日本語 with 住む / 働く / 学ぶ |
| 0:44 | Japanese Shikhi teaches Japanese in Bangla, from your first hiragana to JLPT N1. | Logo, বাংলায় JLPT জাপানি ভাষা শিক্ষা, あ → N5 … N1 ladder |
| 0:51 | Every grammar point is explained in Bangla. | 〜ています card with a Bangla explanation and example |
| 0:55 | New words come back for review just before you'd forget them. | Spaced-review memory curve, 勉強 → পড়াশোনা flash card |
| 0:59 | And when you're ready, there's listening practice and timed mock exams. | 聴解 waveform, 模試 countdown |
| 1:04 | Going for work? Japan's skilled worker visa asks for N4, or an equivalent test. | 特定技能 panel, N4 highlighted |
| 1:10 | Going to study? Many universities that teach in Japanese expect N2. | 留学 panel, N2 highlighted |
| 1:16 | Travelling? Even the basics make each day easier. | 旅行 panel, N5 highlighted |
| 1:20 | Wherever you're headed, start here. In Bangla. 「日本で会いましょう。」 | Globe with the full route, logo, "See you in Japan.", japaneseshikhi.com |

Facts used: the Dhaka–Tokyo great-circle distance is computed from coordinates (4,880 km).
Specified Skilled Worker (i) applicants show Japanese ability with JLPT N4 or the JFT-Basic
test; some sectors add their own test. "N2 for many universities" and "N5 basics for travel"
are general guidance, not official requirements.

## Voice

- English narration: Kokoro-82M, voice `af_heart` (Apache-2.0 model, runs locally, no account).
  espeak mispronounces two words, so `scripts/vo_script.json` overrides their phonemes:
  *Shikhi* → "shee-khee", *hiragana* → "hee-ra-gaa-na".
- Japanese lines: Kokoro `jf_alpha` (announcement, closing line) and `jm_kumo` (interviewer),
  phonemized with misaki + pyopenjtalk. The announcement gets a station-PA filter.
- Word timings for the captions come from the model's own duration predictor
  (`scripts/patch_kokoro.py` exposes it as an ONNX output), so every caption word lands on
  the spoken word.

## Sound

- `scripts/make_audio.py` synthesizes the story sounds (cabin chime, a generic station chime,
  plane pass, train interior, split-flap clatter) and an original music bed in the Japanese
  yo scale that ducks about 5 dB whenever the narrator speaks.
- Generic UI sounds (whooshes, pops, clicks, sparkle, typing) are the Pixabay SFX bundled with
  HyperFrames (`assets/sfx/CREDITS.md`).
- `scripts/place_sfx.py` writes every SFX cue into `index.html` from the word timings.

To use your own SFX, drop files into `assets/sfx/` and change the names in `scripts/place_sfx.py`.

## Rebuild

```bash
pip install kokoro-onnx soundfile onnx misaki pyopenjtalk-plus pyloudnorm scipy numpy
# models: kokoro-v1.0.onnx + voices-v1.0.bin from github.com/thewh1teagle/kokoro-onnx releases
python3 scripts/patch_kokoro.py /path/to/kokoro-v1.0.onnx
KOKORO_DIR=/path/to python3 scripts/make_voice.py   # vo.wav + captions.js
python3 scripts/make_audio.py                        # sfx + ducked music
python3 scripts/place_sfx.py                         # sfx cues → index.html
npx hyperframes check
npx hyperframes render -o renders/japanese-shikhi-ready-for-japan-16x9.mp4 --fps 30 --quality high
# the HyperFrames mix lands around -20 LUFS; master it to -16 LUFS:
ffmpeg -i in.mp4 -c:v copy -af loudnorm=I=-16:TP=-1.5:LRA=11 -c:a aac -b:a 192k out.mp4
```

Edit the narration in `scripts/vo_script.json`; scene timings read the voice's own word
timings (`JS.word(...)` in `assets/js/helpers.js`), so scenes follow the voice when it changes.
Map data: Natural Earth via `world-atlas` (public domain), drawn with d3-geo.
