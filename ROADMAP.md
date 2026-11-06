# Roadmap

Ordered by what the evidence says is weak, not by what is fashionable. Each
item names the gate that would prove it done.

## Done — 0.10.1: story recovery and narration consistency

| Item | Why | Done when | State |
|---|---|---|---|
| `--manifest` actually selects the film | the flag was accepted but Remotion read the active file | render/storyboard activate the requested manifest and restore the previous bytes | corrected 10-shot film rendered through `studio.py render --manifest` |
| Narration has one role | visible characters were stealing the narrator's lines | `narration: true` resolves every non-dialogue line to `narrator`; `dialogue: true` is the explicit exception | 8/8 lines `ef_dora`; `voicecheck` OK |
| Audio covers the spoken text | a short stem could pass on picture duration alone | stem/mix are checked against the last spoken line; `assemble` rejects short audio | 31.183 s stem, last line 30.188 s, 30.933 s mix; `qa.audio_duration` PASS |
| Catalogue preserves the story | scene keys were lowercased and narration was dropped | compose maps renderer scene names and keeps top-level narration | 10 shots, no `Unknown scene`, no voice switching |
| Proportion audit | identity was structural only | head/body ratio measured against the rig, with a calibrated band | elder 0.541 · young 0.518 · widow 0.529; 0 problems |
| Render progress | a slow provider render looked identical to a hung one | Remotion output streams to `logs/render.log` | fixed + test; one full provider render, two-render gate still open |

## Done — 0.10.0: shared asset system

| Item | Why | Done when | State |
|---|---|---|---|
| One catalogue for forged assets | an asset generator cannot become a parallel library | schema-2 entries merge into `assets/catalog.json`; `validate` passes | 38 assets, 0 problems |
| Versioned creation | a variation must not overwrite an approved asset | changed requests write `vN+1`; old files remain readable | `set:laboratorio` v1 day → v2 night |
| Preview + validation before registration | a file in a folder is not a renderable asset | every forged asset has an SVG preview and structural validation | 5 forged types, all previews present |
| Renderer integration | an asset must be usable without editing the engine | generated set/prop/expression/graphic render through existing components | two Remotion stills, visual check |
| Reuse proof | the system must mix new and old assets | proof project uses generated + existing set/character | `set:doorway`, `character:elder` reused |
| Persistent references | examples must survive sessions | purpose/tag selection with provenance/licence checks | 3 seeded references, validation OK |

## Done — 0.9.0: audiovisual direction

| Item | Why | Done when | State |
|---|---|---|---|
| Beat sheet → shot plan | the edit had no hook, reaction, pause or close decision | `studio.py av` writes the same manifest with `beat`, `scale`, motives and sounds | 10 shots, 30.933 s, 0 structural failures |
| Shot-scale vocabulary | every setup was carried by actor scale alone | declared `wide/full/medium/close/detail`; QA detects identical-scale runs | 4 scales, longest run 1 |
| Motivated camera | moves existed but nothing said why | every non-static move carries a motive; dissolves need one too | 9/9 moves, 2/2 dissolves |
| Camera vocabulary extended | tracking and reframing were missing | `trackLeft`, `trackRight`, `reframe` render through the existing rig | `trackRight` used in S09 |
| Sound follows action | score had fixed scene effects | per-shot timed cues, including intentional silence | 15 events, 9/10 shots |
| Creative QA without fake scoring | technical QA cannot judge an edit | `avqa` reports structure, failures and human-pending dimensions | 13 checks pass; narrative/acting/rhythm pending |
| Before/after gate | adding features is not a visual improvement | `avqa --baseline` writes deltas against the previous manifest | action 2→5, reaction 0→1, scale run 3→1 |
| Rendered delivery | the plan must survive the actual MP4 | assemble + QA + inspect + evaluation on `av_direccion` | 927 frames, 17.5 MB, QA 11/11, inspect 0/10, 10 measured PASSes |

## Done — 0.8.0: identity and narration

| Item | Why | Done when | State |
|---|---|---|---|
| Canonical identity actually rendered | `height` and silhouette were data the rig ignored | identity height applied to rig + overlay anchors | `identity_sheet.png`: one identity, seven poses; young 8 % shorter |
| Identity audit as a gate | a shot cannot be allowed to invent a variant | `studio.py identity` + tests fail on overrides | 3 canonical characters, 0 problems, 0 overrides |
| Real narration verified in the delivery | an audio track that exists is not a voice you can hear | take/stem/mix RMS per line + muxed MP4 | `voicecheck` OK, 8 lines, 58 words, 23.34 s of speech |
| No doubled voice at dissolves | overlapping shot windows summed two takes | each line ends at the next start | S01/S02 and S03/S04 trimmed with a 20 ms fade |

## Done — 0.7.0: UI as direction

| Item | Why | Done when | State |
|---|---|---|---|
| UI director per shot (A–F) | UI must serve the story, not fill the frame | `studio.py ui` writes modes, boxes and windows with reasons | done in `projects/ui_direccion` |
| Adaptive placement with escalation | a fixed column always covers someone | B → D → E when there is no free zone | 0 body/face overlaps in the new demo |
| Reading-time windows and exits | a card that stays is a card that hides the film | B/C leave before 0.90, QA checks it | 6/6 elements inside their window |
| UI QA + rendered evidence | passing tests is not a composed frame | `uiqa` + `measure_render` over the MP4 | 0 problems, 8/8 shots clean |

## Done — 0.6.0: consolidating the base

| Item | Why | Done when |
|---|---|---|
| Hybrid demo with character + chart + label + UI + narration | prove the modules share one composition | `projects/sistema_demo` renders, QA passes, inspection clean |
| Style tokens on every surface | avoid a second engine per style | all 5 styles render the same manifest; `tsc` + tests green |
| Feedback memory with scopes | stop losing corrections between sessions | records persist in `feedback/records.jsonl`, docs regenerate |
| Inspection + evaluation separation | stop calling metrics "quality" | every dimension declares kind and status in `quality/evaluation.md` |
| Creative direction from a title | generate, don't just assemble | `studio.py direct` writes spec + manifest + board plan |

## Next — quality depth

1. **Human review of the new edit.** The structural audit passes; narrative,
   acting and rhythm are still `pending`. Gate: a completed
   `preproduction/visual_review.json` for `av_direccion_story`, with per-dimension
   evidence, not a global score.
2. **Real lens semantics.** `scale` is a declared unit over a 2.5D transform;
   there is no focal length, depth of field or true parallax. Gate: framing
   derived from a lens/distance model and validated on a close-up and a wide.
3. **Prop and hand continuity.** The plan says who holds what, but the rig uses
   three grips and no IK; a handoff between shots is not tracked. Gate: one prop
   handed between two characters across two shots, audited by position.
4. **Per-frame UI reflow.** The existing caveat remains: a moving camera can
   carry a body under a screen-space card after the box is resolved. Gate: zero
   collisions over every frame of a moving shot.
5. **Per-style asset packs.** Styles currently re-tune tokens; a cartoon style
   with the same vector silhouettes still reads as the same drawing. Gate: one
   set redrawn in two styles, judged side by side by a human review file.
6. **Caption timing in the render.** The SRT is timed from the take; the
   burned-in layer still distributes words by character weight. Gate: frame
   diff between caption reveal and `words.json` under 120 ms. (Still pending;
   the narration check only proves the audio, not the burned-in reveal.)
7. **Real style consistency check.** Palette drift is a proxy. Gate: a
   perceptual distance (CIEDE2000) over a reference frame per shot, with a
   threshold calibrated on accepted renders.
8. **Camera-aware UI reflow.** This is UI work and is deliberately out of this
   iteration; boxes are still resolved once per shot. Gate: per-frame collision
   check over a moving-camera shot, with zero frames in violation.
9. **Composition rules with teeth.** Overlap and safe area are checked; visual
   weight and headroom are not. Gate: a composition report that flags a subject
   pressed against the frame edge.
10. **Regression suite over three accepted renders.** Currently two references
    are registered. Gate: `evaluate.compare` runs on every demo and fails on
    drift.
11. **Per-character body silhouettes.** Identity now carries height, head radius,
    hat and palette, but the torso/limb paths are still one rig. Gate: each
    recurring character has a distinct body outline, judged side by side in
    `IdentitySheet` without changing head or coat.
12. **Word-synced burned-in captions.** The SRT is timed from the take; the
    caption layer still distributes words by character weight, because the
    renderer does not read `words.json`. Gate: reveal times within 120 ms of the
    real word timings on three lines.
13. **Render provider that cannot hang.** `studio.py render` now streams to
    `logs/render.log` and the `--manifest` activation is exception-safe; one full
    24-minute render completed. Priority: high (blocks a reproducible delivery).
    Gate: two consecutive full renders through `studio.py render`, with streaming
    logs and no manual fallback.

## Later — capability, not polish

- **Lip-sync**: Kokoro gives phoneme timings; the rig has a mouth shape but no
  viseme track. Gate: mouth opening correlated with the phoneme track over a
  spoken line.
- **More voices**: three Spanish voices is a casting ceiling. Gate: at least one
  additional register (narration vs dialogue) without cloning.
- **16:9 / 1:1 formats**: the layout maths is normalised, the sets are drawn for
  9:16. Gate: a set that survives a 16:9 crop without empty bands.
- **Word-level caption emphasis**: the data exists in `words.json`; the renderer
  ignores it.

## Explicitly out of scope

- Photoreal humans or footage in LOCAL mode.
- A second video pipeline. Every new module hangs off the same Remotion
  composition and the same manifest.
- Automatic "learning" from prose. Feedback becomes rules only through a
  recorded, validated change.
- Paid provider calls without explicit authorisation and a budget.
