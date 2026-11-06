# Reference style analysis

Corpus: `Ejemplos/Video/` (3 shorts) + `Ejemplos/Frames/` (20 contact sheets,
1 per second of each short). Analysis produced by `scripts/analyze_reference.py`;
raw data in `references/measurements.json` and
`projects/demo_001/analysis/<video>/`.

Status labels: **[measured]** = produced by FFmpeg/FFprobe on the file.
**[observed]** = read from the frame sheets / decoded frames.
**[interpretation]** = my reading, not a measurement.

---

## 1. Technical baseline

| | Ancient Jar | Job Nobody Wants | Perfect Railroads |
|---|---|---|---|
| duration | 64.90 s | 60.56 s | 65.22 s |
| resolution | 608×1080 | 608×1080 | 608×1080 |
| fps | 30 | 30 | 30 |
| video codec | AV1 | AV1 | AV1 |
| audio | AAC 44.1 kHz stereo | AAC 44.1 kHz stereo | AAC 44.1 kHz stereo |
| mean / peak level | −16.8 / −2.2 dB | −16.9 / −2.1 dB | −16.8 / −2.3 dB |
| detected changes (scene > 0.10) | 9 | 9 | 12 |
| hard cuts (scene > 0.30) | 1 | 0 | 1 |
| mean shot (detector) | 9.27 s | 10.09 s | 8.15 s |
| longest detected take | 20.63 s | 30.89 s | 20.53 s |
| mean motion energy | 24.3 | 29.6 | 30.4 |
| frames with horizontal pan | 39.7 % | 66.3 % | 67.7 % |

**[measured]** Detected shot boundaries:

- *Ancient Jar*: 0 · 3.07 · 5.23 · 6.10 · 18.97 · 39.60 · 46.80 · 64.90
- *Job Nobody Wants*: 0 · 0.97 · 2.13 · 25.07 · 29.07 · 29.67 · 60.56
- *Perfect Railroads*: 0 · 3.73 · 9.87 · 30.40 · 44.03 · 50.67 · 57.73 · 64.23 · 65.22

**[interpretation]** The detector finds far fewer boundaries than the frame
sheets show setups, and almost no hard cuts. The transitions are therefore
mostly gradual (dissolves / continuous camera moves that carry the cut), not
hard editorial cuts. Consequence for production: pacing comes from *within-take
change*, not from cutting faster.

---

## 2. Palette

**[measured]** dominant k-means clusters (k=6, 1 fps):

- *Ancient Jar*: `#58454a` `#8c654f` `#b08c77` `#e4c1a7` `#312637` `#4358a2`
- *Job Nobody Wants*: `#9ba174` `#6b89b9` `#d9d7d8` `#1f43ac` `#262945` `#755550`
- *Perfect Railroads*: `#956b6c` `#2e2c50` `#6e322e` `#cec3c3` `#dd7638` `#5e88ce`

**[interpretation]** Two families recur: (a) cold blue field + warm object, and
(b) desaturated earth + one saturated accent (red, orange). Saturation is spent
locally — one object carries the colour, the frame does not.

---

## 3. Image

**[observed]**

- Line: constant-weight dark ink outline on characters and props; backgrounds
  are often outline-free, which keeps focus on the figures.
- Shading: flat local colour + a lighter rim on the key side + soft gradients in
  skies and light pools. No hard cel shadows.
- Texture: visible paper/brush grain across the whole frame, stronger in large
  flat areas (walls, snow, sky).
- Depth: 3–5 planes per frame. Foreground occluders (snow bank, doorframe,
  out-of-focus branch) appear frequently; backgrounds hold many small props.
- Composition: subject at 1/3 line or centred; horizon low (≈ 60–70 % height) or
  absent in close shots; captions in the bottom fifth.

**[interpretation]** The "production value" is art direction density: small
props, light pools, layered silhouettes. Character complexity is deliberately
low, which is exactly why a procedural rig can approximate the style.

---

## 4. Sound

**[measured]** Mean −16.8 dBFS, peak −2.2 dBFS, no long silent gaps
(`silencedetect` at −35 dB/0.35 s returns nothing). RMS blocks sit at −19…−14 dB,
i.e. a continuous, compressed bed rather than sparse dialogue with silence.

**[interpretation]** Narration over music/ambience, mixed loud and continuous.
The LOCAL engine mirrors this with a continuous bed, not with silence between
lines.

---

## 5. Motion

**[measured]** 39.7–67.7 % of sampled frame pairs contain a horizontal shift;
median |pan| 1 px per sample at 72×128 resolution (small, steady drift).
Motion energy 24–30 (mean absolute luma difference, 0–255 scale).

**[observed]** Characters animate as layered cut-outs: head bob, arm swing,
blink; ambient snow/flame/water moves independently; camera drifts slowly.

**[interpretation]** No shot is fully static. This is the single easiest quality
signal to reproduce and the one most often lost in AI slide-show output.

---

## 6. What the demo reproduces

| Feature | Status in the demo |
|---|---|
| vertical 9:16, 30 fps | yes, 1080×1920 |
| silhouette-first characters with dot eyes + rim light | yes |
| 3 depth planes + foreground occluder | yes (snow bank, doorframe) |
| warm/cool split + motivated light pools | yes |
| slow camera moves, one per shot | yes (`panLeft`, `dollyIn`, `pushInSlow`, `panRight`, `tiltUp`) |
| continuous ambient motion (snow, dust, bokeh, flicker) | yes |
| 2–3 word lowercase captions low in frame | yes |
| grain + vignette + halation | yes |
| painted brush texture at reference density | **no** — grain only |
| dozens of background props per frame | **partial** — 8–20 per set |
| hand-drawn line quality variance | **no** — constant stroke |
| character cloth/hair physics | **partial** — rigid rig |

---

## 7. Note on the creator reference

The brief mentions Rickclips as a quality bar. The corpus supplied here is
treated as the concrete reference: the analysis above describes **these files**
only. No character, script, voice, name or asset from them is reused; the demo
story ("The Bell That Broke") is original, and the borrowed elements are formal
(shot rhythm, framing, caption treatment, painted-vector look).
