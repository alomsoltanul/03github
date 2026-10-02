# Japanese Shikhi — promo video (HyperFrames)

A 53-second motion-graphics promo for Japanese Shikhi, rebuilt beat-for-beat from the
"Claude Cooked" Tally reference reel and authored with Claude + [HyperFrames](https://hyperframes.heygen.com)
(HTML + GSAP compositions rendered to MP4).

| Output | File | Use |
| --- | --- | --- |
| Master 16:9 (1920×1080) | `renders/japanese-shikhi-promo-16x9.mp4` | Play full-screen on a laptop and film it with your phone (that's how the reference was shot), or post it as-is on YouTube / Facebook. |
| Reel 9:16 (1080×1920) | `renders/japanese-shikhi-promo-reel-9x16.mp4` | Ready to post: the master on a laptop in a purple-lit room, with the "Claude Cooked 凄" caption. |

## Story (same beats and timing as the reference)

| Time | Scene | Reference beat it replaces |
| --- | --- | --- |
| 0–3s | Study-app card counts up to **1,284 words** | Dashboard showing $1,284 |
| 3–4.6s | **LYING. to you.** over a ghost 嘘 (lie) | LYING. to you. |
| 4.6–10s | "It says you know 1,284 words by heart." → "You *actually* remember **412**" — the ball melts, はぁ… | You actually kept $412 |
| 10–11.2s | "where'd the rest go?" question mark made of red balls | same |
| 11.2–19.4s | Four kanji thieves take bites: 忘 Forgetting −386 · 炎 Cramming −274 · 迷 Look-alike kanji −112 (未 ≠ 末) · 耳 Listening −100 | Fees / Ads / Refunds / Shipping |
| 19.4–22.2s | "And you only find out at **11:47** — the night before the exam." 試験前夜 | 11:47 midnight |
| 22.2–24.2s | **14 TABS open.** (grammar PDFs, old flashcard decks, mock-test PDFs…) | 14 TABS open. |
| 24.2–31.6s | Logo + বাংলায় JLPT জাপানি ভাষা শিক্ষা → dashboard (語 文 漢 聴 復 試 nav) → "melted into one number" → **412 words** + 本物 stamp, "The real one." | Tally logo → dashboard → $412.00 REAL |
| 31.6–37s | "When words start slipping," → SRS nudge "12 words are fading" → "One tap." → **Reviewed.** 済 | Ads bleeding → One swipe → Paused. |
| 37–40.8s | 日 sun, 茶 cup, "Every morning, before chai." 7:02 → phone: 火 47-day streak, 12 words due | Every morning, before coffee. |
| 40.8–42.8s | "Fewer tabs. More sleep." 月 moon, 眠 for zzz | Fewer tabs. More sleep. |
| 42.8–47.8s | "Oh, and this whole video?" → editor + `claude ›` prompt → "Made with **AI.**" → "Every single frame." | same |
| 47.8–53s | Comments → **Comment N5** → auto-reply "Sent you the link → japaneseshikhi.com" | Comment PROMPTS |

Kanji stand in for emojis and characters throughout (嘘 忘 炎 迷 耳 本物 済 日 茶 火 月 眠 凄).

## Brand

Colors come from `japanese-shikhi/tailwind.config.ts` and `globals.css`: red `#E63946` (primary),
navy `#1D3557`, sand `#F4A261`, teal `#2A9D8F`, pro purple `#6B21A8`. Fonts: Inter, DM Serif Display
italic accents, Noto Serif JP / Noto Sans JP, Noto Sans Bengali, all bundled in `assets/fonts/` as
subsets of the glyphs used, so the render never depends on the network.

## Audio

- `assets/audio/bgm.wav`: an original music bed synthesized by `scripts/make_bgm.py` (koto-style
  plucks in the Japanese *yo* scale, a darker *in* scale for the night scene, drums that drop and
  return with the scenes). Royalty-free because it is generated from scratch. Swap in a licensed track
  if you prefer: replace the file and keep the `<audio id="bgm">` element.
- `assets/sfx/`: Pixabay sound effects bundled with HyperFrames (see `assets/sfx/CREDITS.md`).

## Edit and re-render

```bash
npm i -g hyperframes            # or use npx hyperframes@0.8.106
npx hyperframes preview         # live Studio preview
npx hyperframes check           # lint + runtime + layout + contrast gate
npx hyperframes render -o renders/japanese-shikhi-promo-16x9.mp4 --fps 30 --quality high

# reel (its own HyperFrames project in reel/): needs the master + its audio next to it
cp renders/japanese-shikhi-promo-16x9.mp4 reel/assets/master.mp4
ffmpeg -y -i reel/assets/master.mp4 -vn -ac 2 -ar 48000 reel/assets/master-audio.wav
cd reel && npx hyperframes render . -o ../renders/japanese-shikhi-promo-reel-9x16.mp4 --fps 30 --quality high && cd ..

# the reel render mixes its single audio track ~6 dB low; put the master's audio back (lossless remux)
ffmpeg -y -i renders/japanese-shikhi-promo-reel-9x16.mp4 -i renders/japanese-shikhi-promo-16x9.mp4 \
  -map 0:v:0 -map 1:a:0 -c copy -movflags +faststart renders/reel-tmp.mp4 \
  && mv renders/reel-tmp.mp4 renders/japanese-shikhi-promo-reel-9x16.mp4
```

The reel caption ("Claude Cooked" + 凄 tile) and the laptop mock-up live in `reel/index.html`.

All copy lives in `compositions/sNN-*.html`. Each scene is a sub-composition with its own GSAP
timeline; the timings in `index.html` place them on the 53s track. The music script regenerates
with `python3 scripts/make_bgm.py` (needs `numpy` and `scipy`).
