# Intro — Ritesh Malviya

A 16-second, 1920×1440 (4:3, same as the deck) title sequence at 128 BPM. It runs 8 bars with one section per bar, then hands off to the deck's **00 / Cover** slide: the final second holds a frame that matches the Figma cover.

**Watch:** `out/intro.mp4` · **One frame per beat:** `out/beat-grid.png` · **Prompt:** `PROMPT.md`

| Bar | Section | Field | What happens |
|---|---|---|---|
| 1 | 01 Identity | ink | dot → 12-spoke mark → orbit text → spin, collapse, iris |
| 2 | 01 Identity | orange | RITESH slams in condensed, stretches wide (Archivo wdth 62→125), serif line, meta |
| 3 | 02 Who I Am | cream | CONSUMER + ENTERPRISE, five domain pills on 8ths, pin on Gurgaon |
| 4 | 03 How I Design | blue | square → 3×3 grid → path a dot walks → check → floods the frame |
| 5 | 04 Systems | ink | truchet field; a rotation + orange heat wave per beat (Airtel, Fideo) |
| 6 | 05 Depth | ink | point plane → globe with cities lit (OYO team) → torus → warp |
| 7 | 06 Kinetic Type | per beat | 1M+ · 25%. · 30% · a wall of SCALE |
| 8 | 07 Fin | orange → black | mark + particle burst, name lockup, then the field contracts into the cover's photo panel |

## How it works
- `index.html` is the whole piece. `seek(t, tf)` recomputes every style, canvas pixel and character from time (`t` moves the picture, `tf` is the frame time for the HUD). `?play` previews live, `?t=7.5` freezes a frame.
- Springs are closed-form step responses, summed per target change. Particles use closed-form drag + gravity. Truchet tile orientation is a hash of (x, y). The 3D section is plain JS projection onto a canvas.
- Motion blur: 4 subframes per frame blended with ffmpeg `tmix`, plus a directional SVG gaussian whose size comes from each slam's velocity. Subframes never straddle a hard cut, so cuts stay sharp.
- The hand-off frame uses the Figma cover's exact layout scaled by 1.875 (Inter, 80px margin, 343px photo panel). `node render.mjs cover` diffs it against `assets/cover-figma.png`.

## Pipeline
```bash
python3 audio/make_music.py   # 128 BPM score, 8 bars + a 1 s tail (or drop a track at audio/song.*)
python3 audio/analyze.py      # numpy beat grid + downbeat -> out/beats.json
python3 audio/make_sfx.py     # sound design -> audio/sfx/*.wav
node render.mjs cues          # cue list straight from the page timeline
python3 audio/mix.py          # music + every sound placed by its measured peak -> out/soundtrack.wav
node render.mjs beats         # one still per beat -> contact sheet (check before the full render)
node render.mjs full          # 960 frames, 4 subframes each, tmix -> out/intro.mp4
node render.mjs cover         # last frame vs the Figma cover
```

Fonts (all SIL OFL, licenses in `fonts/`): Archivo, Instrument Serif, JetBrains Mono, Inter. The photo comes from the Figma cover. Figma only exports it at 343×768, so it's upscaled for the 1920×1440 frame.
