# The Path — intro, redesigned

22 seconds at 1920×1440 (4:3, same as the deck) and 112 BPM, shot as **one continuous camera move**. A little orange character (you) hops along a stepping-stone trail through one illustrated world per chapter. At the end the world contracts into the Cover slide's photo panel, the photo opens from where you're sitting on the real trail, and the last second holds on the Cover.

**Watch:** `out/the-path.mp4` · **One frame per beat:** `out/beat-grid.png`

## Palette (from the reference swatches)
| Role | Color |
|---|---|
| Ink (replaces black) | Dark Cherry `#3F151D` |
| Paper | Vanilla Cream `#F8F1DC`, Milk Foam `#F9F7EF` |
| Hello · OYO | Vivid Orange `#F16A02` |
| How I Design | Ice Water `#D7EFFD` |
| Saathi | Berry Bubblegum `#FEBFDA` |
| Good Monster | Fresh Lime `#E3FA85` |
| Fideo | Citrus Zest `#DAE24E` |
| Airtel | Raspberry Shot `#B91C44` |
| Next Chapter | a Dark Cherry world, which sets up the black Cover |

Type: Anton (condensed display, as in the swatches) for headlines and the arched badge text, Bricolage Grotesque for labels, Inter for the hand-off (the deck's font).
Icons: one 24-unit grid with a 2-unit round stroke, always drawn at 84px, so every icon has the same weight.
Stickers: pill and circle shapes with a 5px cherry outline and a hard 9px cherry offset shadow. No gradients, no glows.

## Stops (one bar each)
| Bar | Stop | Illustration |
|---|---|---|
| 1 | Hello | the character pops in; RITESH rises letter by letter; Product Designer sticker; 12+ years badge |
| 2 | Who I Am | Consumer + Enterprise; five domain islands with icons (EdTech, FinTech, Hospitality, AI, SaaS) |
| 3 | How I Design | three signposts spring up from the ground, one per beat |
| 4 | Saathi | job cards stack into a phone, users count up to 1M+, +25% sticker, a team of 6 |
| 5 | Good Monster | leads drip into a funnel, a monster chomps it, +30% badge, NYC skyline |
| 6 | Fideo | coins arc from ₹ to $, 20 businesses stamp in |
| 7 | Airtel | UI components fly in and snap onto a phone grid; ~40% |
| 8 | OYO | pins drop on NL, CH, DK with hotels; the bell rings; +1.22% |
| 9 | Next Chapter | three overlapping circles from the deck's last slide |
| 10 | Hand-off | the world contracts into the photo panel; the character hops in and becomes you |

## How it works
- `index.html` is the whole piece. `seek(t)` recomputes everything from time: camera, parallax confetti, wobbling blobs, the trail reveal, every item's spring pop, the character's hops and squash, counters, coins and the monster's mouth. `?play` previews it live and `?t=8` freezes a frame.
- Every illustration piece is an item with a beat and a kind (pop, rise, slap, drop). Items that make a sound register a cue on their own beat, so the sound design is generated from the timeline.
- Render: 4 subframes per frame blended with ffmpeg `tmix` at 60 fps. Audio: a synthesized score plus sound effects, each placed by its measured peak.

```bash
python3 audio/make_music.py && python3 audio/analyze.py && python3 audio/make_sfx.py
node render.mjs cues && python3 audio/mix.py
node render.mjs beats      # contact sheet, one frame per beat
node render.mjs full       # -> out/the-path.mp4
node render.mjs cover      # last frame vs the Figma cover
```

Fonts are SIL OFL (licenses in `fonts/`). The photo comes from the Figma cover, which only exports at 343×768, so it's upscaled.
