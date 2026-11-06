# Visual system audit

What the renderer actually produces, measured on the code and on the accepted
renders. This is an audit of a stylised 2.5D engine, not of a 3D or photographic
pipeline.

## 1. What is real

| Layer | Implementation | Notes |
|---|---|---|
| Sets | 5 SVG scene components with parallax groups | town at night, threshold, close-up plate, dawn graveyard, bell insert |
| Characters | procedural SVG rig, two-segment arms, brows, blink, breath | `headRadius` per identity, geometry shared with label layout |
| Camera | 9 named intents as transform curves | dolly, pan, tilt, crane, drift, push-in |
| Light | gradient + occlusion + rim light baked per shape | no light objects, no shadows cast by a light direction |
| Materials | procedural ashlar, planks, shingles, snow, frost | `engine/texture.tsx` |
| Atmosphere | cast shadows, shafts, fog, dust, glows, veil | `engine/atmosphere.tsx` |
| Finish | grain, vignette, warm/cool grade, halation | `engine/FilmFinish.tsx` |
| Typography | captions only (until this cycle) | display/UI/mono tokens now exist in `styles.json` |
| Information | **new**: 13 overlay types + character labels | `motion-graphics/` |

## 2. Rhythm and palette

From `references/measurements.json` (three reference videos, k-means palettes):
median shot 6.4 s, mean 8.1 s, longest 21 s, ~6.6 cuts/min. The engine's demos
sit inside that band; `demo_003` is 29.2 s with six shots.

Palettes are measured, not invented: night town `#1d2a52`/`#2c3a6b` with warm
window pools, dawn field peach and cream, interior crimson/plum. They live in
`engine/tokens.ts` and now also in the style tokens.

## 3. What was missing before this cycle

- **No information layer.** A shot could hold a character and a caption, and
  nothing else: no label, no chart, no callout, no panel.
- **No style system.** One look; a new look meant editing the scene components.
- **No feedback memory.** Corrections lived in the chat.
- **No self-inspection.** QA measured motion, black frames, loudness and caption
  coverage — nothing about emptiness, legibility or palette drift.
- **No direction.** Manifests were hand-written; nothing turned a title into a
  plan.

## 4. What is still weak

1. **One drawing language.** Every style shares the same silhouettes. Token
   changes move palette, type, density and motion, not shape. Calling the
   cartoon style a different *art style* would be dishonest.
2. **Depth is authored, not simulated.** Parallax is a per-layer shift; there is
   no occlusion solving, no depth of field beyond a blur plate in one set.
3. **Lighting is painted.** A character does not react to the light of the set;
   rim light is a fixed stroke.
4. **Acting is a curve library.** Presets read as intentional motion at 1.5-2×
   scale, not as performance at close-up scale.
5. **Captions are typographic, not timed to the take in the render.** The SRT is
   correct; the burned-in layer is not driven by `words.json` yet.
6. **Composition feedback is geometric.** Overlap, safe area, face and caption
   band are checked. Visual weight, headroom and eyeline are not.

## 5. Verification used in this cycle

- `python -m unittest discover -s tests` — engine-adjacent Python behaviour.
- `tsc --noEmit` — overlay/style types compile against the real composition.
- Storyboard stills at 0.4 scale, inspected by `scripts/acs/inspect.py`
  (tile flatness, edge energy, local caption contrast, palette drift, depth
  bands) plus a manifest-geometry pass.
- A human review file is the only way to fill the aesthetic dimensions; until it
  exists, `evaluate` reports them as `pending`.

## 6. Honest conclusion

The engine is a strong **stylised narrative renderer** with a real information
layer now attached. It is not a general animation system, and the style system
is a token system. The next quality jump is not more overlay types: it is
per-style assets and caption timing from the actual voice.
