# Motion graphics and visual UI

One module, `studio/src/motion-graphics/`, rendered by the same Remotion
composition as the scenes. No second renderer, no separate timeline: an overlay
is a field in a shot of the manifest.

## Model

```json
{
  "id": "G1",
  "type": "bar",
  "placement": { "kind": "screen", "box": { "x": 0.07, "y": 0.55, "w": 0.86, "h": 0.24 } },
  "from": 0.16,
  "to": 0.9,
  "source": "inventario municipal, 2026",
  "data": {
    "title": "lo que contó el aprendiz",
    "unit": "días",
    "series": [ { "label": "oídos", "value": 9 }, { "label": "no oídos", "value": 0, "tone": "warn" } ]
  }
}
```

- `from` / `to` are **fractions of the shot**, so retiming a shot keeps the
  graphic in the same relative beat.
- `placement.kind = "actor"` anchors a label to a body (`actor`, `at`:
  `head` | `chest` | `feet`); `"screen"` places a normalised box in frame space.
- `illustrative: true` is required when a number has no source; the renderer
  prints **ilustrativo** under it. `scripts/acs/overlays.py` rejects a numeric
  overlay with neither source nor that flag.

## Types

| Group | Types | Notes |
|---|---|---|
| Character UI | `label`, `badge` | label carries name, role, status and a leader |
| Information | `callout`, `panel`, `hud`, `highlight`, `arrow` | screen space, plated for contrast |
| Data | `bar`, `donut`, `line`, `counter`, `ranking`, `process` | a chart without payload renders a visible `sin datos` plate |

## Placement rules (`layout.ts`)

1. A label is placed **above the head**, then beside the body on the side it
   faces away from, then below the feet.
2. Every candidate is clamped to a **6% safe area**.
3. The head circle is never covered: the validator checks the resolved box
   against the face circle and fails the shot if they intersect.
4. The **caption band (0.855–0.94)** is reserved for subtitles; a panel or chart
   that reaches it is a validation error, not a warning.
5. Actor-anchored overlays render **inside** the camera transform, so they stay
   glued to the body through a dolly or pan. Panels and charts render **outside**
   it, so a camera move never skews the data a viewer is reading.
6. Two overlays whose windows intersect and whose boxes overlap raise a warning.

The Python validator mirrors this geometry; `tests/test_overlays.py` parses
`SAFE` and `RIG` out of the TypeScript and fails if the two drift.

## Style integration

Overlays read the active style (`engine/styles.tsx`): palette, type scale,
radius, plate treatment, label style (leader / caption / tag / plain / bubble),
chart shading and grid. A style change never requires touching an overlay.

## Adding a type

1. Implement the component in `charts.tsx` or `annotations.tsx`.
2. Register it in `OverlayLayer.tsx` (`COMPONENTS`).
3. Add it to `TYPES`, `DEFAULT_BOX` and, if it carries numbers, `NUMERIC_TYPES`
   in `scripts/acs/overlays.py`.
4. Run `tsc --noEmit` and `python -m unittest tests.test_overlays` — the test
   asserts that every validated type has a renderer.

## What it is not

No 3D charts, no data loading at render time, no fabricated statistics, no
automatic layout solver beyond the anchor rules, and no animation library: every
motion is a pure function of the frame.
