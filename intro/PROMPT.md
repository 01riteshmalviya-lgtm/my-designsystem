# Intro — prompt

Reference: the "motion reel" screen recording (128 BPM, 8 bars, one section per bar, HUD frame, color-blocked scenes).
Content: Figma "Intro Slides (Master)" → page "01 — Core Story".

```
<inputs>
Ask me for: a royalty-free ~128 BPM track with a clean kick (e.g. Mixkit, free for commercial use) or approval to synthesize one; whether the intro ends by handing off to the Cover slide (default) or loops; the frame: 1920x1440 (4:3, matches the deck, default) or 1920x1080 (16:9).
</inputs>

<content>
From the Figma deck, nothing invented:
Ritesh Malviya · Product Designer · 12+ years · Gurgaon, India · 01riteshmalviya@gmail.com
Consumer + Enterprise · EdTech, FinTech, Hospitality, AI, SaaS
How I design: 01 Designing for scale · 02 Behavior-driven UX · 03 Trust & onboarding
Saathi: Director of Product Design, 1M+ users, +25% job applications, team of 6
Good Monster: Head of Design (New York, remote), +30% new business
Fideo: Founding Designer, core UX & design system, 20+ businesses onboarded
Airtel: Senior Visual Designer, design system, ~40% more UI consistency, 20 designers
OYO: Lead Product Designer, +1.22% booking conversion, international team of 8 (Netherlands, Switzerland, Denmark)
</content>

<direction>
Showreel-grade title sequence in the language of the reference. Full-bleed color fields, one per scene, cut hard on the downbeat. Every scene is one system (a mark, a grid, a field of tiles, a point cloud, a word), never an illustration.
Palette as flat fields only: Signal Orange #FF5A36, Electric Blue #2B3BFF, Acid Lime #DCF53A, Ink #0B0B0C, Cream #F3EEE4.
Type: Archivo variable for the display words (they stretch from condensed wdth 62 to wide wdth 125 at weight 900). Instrument Serif italic for one soft line per lockup. JetBrains Mono, uppercase, tracked, small, for the HUD and captions. Inter only for the final hand-off frame, to match the deck.
A persistent HUD sits over everything: corner brackets; "RITESH MALVIYA  INTRO — 2026" top-left; "0N — SECTION" top-right; timecode HH:MM:SS:FF and "60 FPS" bottom-left; "128 BPM ▢▢▢■ BAR n/8" bottom-right, with one square filling per beat; a hairline progress bar along the bottom. The HUD inverts ink/cream with the background. A faint dot grid on dark scenes.
Motion: springs and expo ease-outs, motion blur on every fast move, something hits on every beat. Scene changes are hard cuts or shape wipes (an iris, a field contracting), never crossfades.
Banned: crossfades, drop shadows, glows, gradients on shapes, elastic or bouncy easing, stock icons, emoji, company logos (set the names in the display type instead), anything that looks like a template.
</direction>

<structure>
128 BPM, 8 bars, 32 beats = 15.0 s = 900 frames at 60 fps. One section per bar, as in the reference.
Bar 1 · 01 IDENTITY (ink): an orange dot inside a thin ring → the ring expands and the dot unfolds into a 12-spoke mark, spokes springing out with a stagger → mono text orbits the mark, writing on clockwise: "RITESH MALVIYA · PRODUCT DESIGNER · 12+ YEARS · GURGAON ·" → the mark spins up, collapses to a point, and a cream iris opens from it.
Bar 2 · 01 IDENTITY (orange): "RITESH" slams in condensed → stretches to wide on the beat, tracking tightening → "product designer" writes on in serif italic under a hairline rule that draws across → the mono meta line types on: "12+ YEARS · CONSUMER + ENTERPRISE".
Bar 3 · 02 WHO I AM (cream): "CONSUMER" in from the left, "ENTERPRISE" in from the right, an orange "+" spins in between → the five domain pills (EdTech, FinTech, Hospitality, AI, SaaS) pop in on eighth notes, each a different palette color → a pin drops on "GURGAON, INDIA".
Bar 4 · 03 HOW I DESIGN (blue), morphing: one cream square → it splits into a 3x3 grid, caption "DESIGNING FOR SCALE" → the cells slide into a path a dot travels along, "BEHAVIOR-DRIVEN UX" → the cells lock into a check, "TRUST & ONBOARDING", then subdivide into the tiles of the next bar.
Bar 5 · 04 SYSTEMS (ink + cream tiles): a field of quarter-arc truchet tiles fills the frame. On each beat a rotation wave ripples out from a new point, with an orange color wave behind it. Mono captions, one per beat: "AIRTEL — DESIGN SYSTEM · 20 DESIGNERS" / "~40% MORE UI CONSISTENCY" / "FIDEO — CORE UX & DESIGN SYSTEM" / "20+ BUSINESSES ONBOARDED". On beat 4 the tiles shrink to points.
Bar 6 · 05 DEPTH (ink): the points become a perspective grid plane (cream, a few orange) → it curls into a globe → points light orange at Gurgaon, New York, Netherlands, Switzerland and Denmark with mono labels, "OYO — INTERNATIONAL TEAM OF 8" → the globe pinches into a torus and flies through the camera into warp streaks.
Bar 7 · 06 KINETIC TYPE: one word per beat, the background flipping color each beat, motion-blurred slams: "1M+" on orange ("USERS · SAATHI") → "25%." cream on ink with an orange period ("MORE JOB APPLICATIONS") → "30%" blue on cream ("NEW BUSINESS · GOOD MONSTER") → "SCALE" as a wall of rows on lime scrolling in alternating directions, then one row slams forward.
Bar 8 · 07 FIN (orange): the 12-spoke mark punches in with a small burst of ink, blue and cream particles → "RITESH MALVIYA" assembles beside it with "product designer" in italic beneath → the meta row types on: "INTRO 2026 · 12+ YEARS · EVERY FRAME WRITTEN IN CODE · 01RITESHMALVIYA@GMAIL.COM" → the orange field contracts to black, the lockup re-sets into the Cover slide's layout and type, and the photo panel slides in from the right. The last frame IS slide 00 / Cover.
</structure>

<build>
1. One HTML file at the chosen size. Every style, canvas pixel and character is computed from time inside seek(t): no CSS transitions, no timers, no state carried between frames.
2. Springs are closed-form step responses. A value that changes target many times is the sum of one spring per change.
3. The display words animate Archivo's real wdth/wght axes with font-variation-settings, never scaleX, so the letterforms stay true.
4. The 3D section is plain JS projection onto a canvas: about 2,000 seeded points, perspective divide, sorted by depth, redrawn every seek. No WebGL, no randomness at render time.
5. Truchet tile orientation is a hash of the tile's (x, y). The waves are functions of distance from the wave origin and time.
6. Particles are seeded and ballistic in closed form (p0 + v·t + ½·g·t²), so they are pure functions of t too.
7. Analyze the song with numpy for the beat grid and start on a downbeat. Time everything in beats. Place every UI sound by its measured peak.
8. Render with Playwright: 4 subframes per frame, blended with ffmpeg tmix for motion blur at 60 fps.
9. Render one frame per beat (32) before the full render and compare it against the reference contact sheet. Fix anything off the grid, cramped or hard to read.
10. Export the last frame and diff it against the Figma Cover slide. They must match.
</build>

<gotchas>
Changing wdth changes the word's width: re-measure and anchor it every frame or it jitters. Never blend subframes across a hard cut: clamp a frame's subframes to the scene that owns that frame, or the cut smears. Keep the HUD out of the motion blur: its text changes per frame, not per subframe. Never put will-change on anything that scales, or the text renders blurry. Canvases are cleared and fully redrawn on every seek. Text that swaps inside a moving container needs its own enter and exit timing or it overlaps. Use the deck's exact font, sizes and positions for the hand-off frame, so the cut into slide 00 is invisible.
</gotchas>

<start>
Ask me for the inputs, then show me the 32-beat grid with what happens on each beat before you write any code.
</start>
```
