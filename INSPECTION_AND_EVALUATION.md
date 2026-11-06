# Visual inspection and evaluation

Two modules, deliberately separate:

- `scripts/acs/inspect.py` measures the render and the manifest geometry;
- `scripts/acs/evaluate.py` builds a scorecard where each dimension declares its
  evidence kind and whether it is measured or pending.

There is **no global quality score**. Averaging a caption contrast with a
judgement about acting produces a number that means nothing.

## Pixel and geometry checks

| Signal | How it is measured | Threshold | Honest limit |
|---|---|---|---|
| `empty_ratio` | share of 12×21 tiles with luma std < 6 | flag > 62%, or > 50% with detail < 5; E/F excluded | a night sky is legitimately flat; the second condition protects it |
| `edge_density` | mean of a Sobel-style edge filter | used with emptiness | grain inflates it slightly |
| `subject_score` | peak tile edge energy / median tile | < 1.55 | proxy for "something is there", not saliency |
| caption contrast | max local p95−p5 across 12×4 cells of the caption band | < 70 with edges < 5 | no OCR: measures contrast, not legibility of the words |
| `palette_shift` | dominant colours vs the style palette, weighted mean distance | > 0.30 | RGB distance, not perceptual (CIEDE2000 pending) |
| `depth_bands` | edge energy in three horizontal thirds | < 2 bands | proxy for depth, not a depth map |
| overlays | boxes resolved from the manifest | any error fails; warnings listed | geometric, does not see pixels |
| cuts | manifest boundaries vs detected scene changes | ±0.35 s | planned for the video pass |

Every metric is labelled in `kind_map` as `automatic (pixels)`,
`geometry (manifest)` or `automatic (video)`.

## Evaluation dimensions

Measured automatically: composition (emptiness/subject/depth on scene shots
A–D; E/F are graphic plates), ui composition (mode, placement, timing),
legibility, consistency (palette drift), overlays, motion, technical, sound,
captions. From QA: format, duration, black frames, freeze, loudness, audio
activity. The scorecard and the inspector apply the same E/F exemption, so one
cannot fail what the other accepts.

Stay **pending** until a human writes `preproduction/visual_review.json`:
narrative, acting, rhythm, style integrity. A pending dimension has `value:
null`; it is never filled with a zero.

## Human review file

```json
{
  "narrative": { "score": 4, "note": "el cierre resuelve el gancho", "reviewer": "autor" },
  "acting":    { "score": 3, "note": "el gesto de S04 llega tarde" }
}
```

`evaluate` reads it and flips those dimensions to `reviewed`, keeping the kind
`subjective`.

## Regression references

`references/regression/index.json` stores, per accepted render: id, date,
relative path, sha256, bytes, the measured metrics and the per-shot inspection.
`evaluate.snapshot()` writes one; `evaluate.compare()` diffs a new run against it
and fails on a metric delta beyond 25% (or 0.05 absolute).

This compares **measurements**, not taste: it catches "the render got emptier,
flatter or off-palette", not "the story got worse".

## Honest conclusion

The tooling makes a claim fail loudly. It cannot tell you a shot is beautiful,
and it does not try: the aesthetic dimensions stay explicitly empty until a
person looks at the frames.
