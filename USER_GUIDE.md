# USER GUIDE

## The normal workflow

1. **Give me the reference video and one sentence of intent.**
   Example: *"same rhythm and framing, original characters, winter town, 35 s"*.
2. I analyse the file (duration, cuts, palette, motion, loudness) — I do not ask
   you for anything the file already answers.
3. I write the preproduction: script, shot list with camera intent, character
   and environment bibles, continuity check.
4. I build and render the film in LOCAL mode (no credits, no keys).
5. I run the quality gates and hand you the MP4 plus the reports.

## What you can ask for

| Request | What changes |
|---|---|
| "recreate the structure with original characters" | new script + cast, same rhythm |
| "keep the look, change the story" | same palettes/sets, new lines and blocking |
| "more cinematic" | longer takes, slower moves, more foreground layering |
| "improve the motion" | more secondary action, longer holds, particles |
| "change the format" | `format.width/height` + scene viewBox + caption size |
| "shorter / exact duration" | shot `seconds` in `project.json`; audio follows automatically |

## Where things live

- **Story / shots / captions:** `studio/src/data/project.json`
- **Characters:** `studio/src/data/cast.json`
- **Look (palettes, caption rhythm):** `studio/src/engine/tokens.ts`
- **Sets:** `studio/src/scenes/*.tsx`
- **Film output:** `projects/<id>/output/final_video.mp4`

## Editing one shot

```jsonc
{
  "id": "S03",
  "scene": "faceCloseup",
  "camera": "pushInSlow",   // see VISUAL_STYLE_GUIDE.md §5
  "seconds": 6,
  "line": "he had rung it once before. it did not end well.",
  "actors": [{ "id": "elder", "preset": "closeup", "x": 540, "y": 2010, "scale": 5.3, "facing": 1 }]
}
```

`scale` is relative to frame height: `1.0` ≈ 310 px tall in a 1920 frame, so a
close-up is ~5, a wide ~1.5. Do not nudge it per frame; change the shot.

## Re-rendering

```bash
# everything after the picture is already rendered
python scripts/studio.py assemble --project projects/demo_001
python scripts/studio.py qa       --project projects/demo_001

# only the picture
python scripts/studio.py render   --project projects/demo_001
```

## Reviewing the result

`projects/demo_001/quality/final_quality_report.md` lists every gate with the
measured value. A failed gate means the cut is not accepted — fix the cause, do
not lower the threshold (thresholds live in `config/studio.config.json` and are
documented as heuristics calibrated on this engine).

## Resuming

Every stage reads and writes files, so a crashed run resumes where it stopped:

```bash
python scripts/studio.py produce --project projects/demo_001 --reference "Ejemplos/Video/x.mp4"
```

## Cost

In LOCAL mode the cost is exactly **0**. `status` prints `spent_usd: 0`.
HYBRID/PREMIUM require an explicit `authorize_spend` and a budget; every call is
logged in `projects/<id>/logs/generation_history.jsonl`.

## Common mistakes

- Editing `cast.ts` instead of `cast.json` (the JSON is the source of truth).
- Putting a `<div>` inside an `<svg>` (it is silently dropped — use `ParallaxGroup`).
- Setting a character `scale` to fix framing instead of moving the camera.
- Expecting photoreal output from LOCAL mode: it is painted-vector animation.
