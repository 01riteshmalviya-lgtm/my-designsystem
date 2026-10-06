# One Shape

A 14-second, 1440×1440 loop at 120 BPM over 7 bars. One element morphs through 13 UI states and a cursor drives every change.

**Watch:** `out/one-shape.mp4` · **Beat grid (one frame per beat):** `out/beat-grid.png`

Button → loader → check → dynamic island → player (play/pause morph) → scrub → volume slider (rubber-band past max) → toggle → liquid tabs → chart that draws itself (+ hover tooltip) → ⌘K → type to filter → click → toast → button.

## How it works

- `index.html` is the whole piece. `seek(t)` recomputes every style from `t`: no CSS transitions, no timers, nothing carried between frames. Open it through any static server; `?play` previews it live, `?t=6.2&hud` freezes a frame.
- **Springs** are closed-form damped step responses. A value that changes target many times is the sum of one spring per change. Looping tracks also sum the previous loop's springs, so the value *and its velocity* match across the seam: the last frame flows into the first.
- **The puck** is one inner element. It goes progress fill → volume fill → toggle knob → tab indicator → ⌘K highlight → toast icon. Its two edges ride different springs, so the leading edge stretches ahead of the trailing one.
- **Drags** are direct manipulation: while the cursor is held, the value comes from its position. On release it springs back from wherever it was, e.g. the volume's rubber-band stretch.
- **Text swaps** use separate enter/exit timing (a quick exit, then a delayed enter with a short blur), so nothing overlaps mid-morph.

## Pipeline

```bash
python3 audio/make_music.py      # stand-in 120 BPM loop (or drop a track at audio/song.mp3|wav)
python3 audio/analyze.py         # numpy: onset flux -> tempo (autocorr) -> phase (comb) -> downbeat (chroma novelty) -> out/beats.json
python3 audio/make_sfx.py        # UI sounds -> audio/sfx/*.wav (swap any for a Mixkit SFX of the same name)
node render.mjs cues             # sound cues straight from the page timeline -> out/cues.json
python3 audio/mix.py             # song from its downbeat + each sound placed by its measured peak -> out/soundtrack.wav
node render.mjs beats --hud      # one still per beat + contact sheet, to check before the full render
node render.mjs full             # 4 subframes/frame (180° shutter) -> ffmpeg tmix -> 60 fps H.264 + AAC
```

Needs Node with Playwright, ffmpeg, Python with numpy + scipy.

## Using a real Mixkit track

The music is generated (royalty-free) because the build sandbox couldn't reach mixkit.co. Save a ~120 BPM Mixkit track as `audio/song.mp3`, then re-run `analyze.py → mix.py → render.mjs full`. The analysis picks the loudest 7-bar run that starts on a downbeat, and the page timeline follows the measured beat period.

Font: [Geist](https://vercel.com/font) (SIL OFL, `fonts/OFL.txt`).
