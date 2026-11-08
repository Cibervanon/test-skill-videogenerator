# Roadmap

Ordered by what the evidence says is weak, not by what is fashionable. Each
item names the gate that would prove it done.

## Done — 0.10.6: carried character state and a new story

| Item | Why | Done when | State |
|---|---|---|---|
| Carried actor state | the next shot reset position, facing and held prop | `carry` inherits the previous exit and refuses a scene change | 5 carried states in `av_ultima_medida`; `avqa.character_continuity` passes |
| Teleport guard | a same-scene jump looked like drift | a >260 px move fails without `continuityMotive` | planner tests reject an unmotivated 378 px jump |
| New workshop set | another winter/bell story would not prove range | a non-snow interior with a new object and dawn light renders | `Workshop.tsx`; S01–S06; no bell or snow |
| New story structure | the old premise could be repeated with new labels | hook, objective, obstacle, reaction, escalation and close differ | **La última medida**; 6 shots / 22.4 s |
| Rendered proof | continuity must survive the MP4, not only the manifest | render, QA, inspect and frame strip | **672 frames**; QA **13/13**; inspect **0/6**; `continuity_issues: []` |
| Current regression suite | new state code must not break the delivery | full suite + `tsc` | **184 passed**; `tsc` exit 0 |

## Done — 0.10.5: compound action and per-shot motion

| Item | Why | Done when | State |
|---|---|---|---|
| Compound action sequences | a preset per shot cannot show a beginning, a change and an end | existing presets can be ordered inside one shot with normalized windows | `ActorSpec.sequence`; S02 walk→turn, S03 turn→reach; **2 sequences / 4 phases** |
| Action completion audit | a sequence can end mid-walk and still render | `avqa` rejects invalid windows/overlaps and a last `walkIn` | `action_completion` passes; 3 new tests |
| Per-shot motion evidence | a global mean hides one dead shot | every shot is measured independently | `qa.shot_motion`; min **2,438**, **no low-motion shots** |
| Rendered proof | the action must survive the MP4 | assemble + QA + inspect + frames | **613 frames / 500,47 s**; QA **13/13**; inspect **0/6** |
| Current regression suite | new code must not break the delivery | full suite + `tsc` | **184 passed**; `tsc` exit 0 |

## Done — 0.10.4: direction continuity, interaction and a shorter demo

| Item | Why | Done when | State |
|---|---|---|---|
| Camera intensity + `handheld` | a vocabulary of moves is not a vocabulary of pressure | every move can be authored at 0.35–1.35 without changing the rig | manifest `cameraIntensity`; `handheld` deterministic; `static` audited for a motive |
| Interaction presets | reach/turn did not cover pointing or a wordless reaction | the rig has explicit `point` and `react` performances | 5/6 shots with action in the demo; `tsc` 0 |
| Narrative continuity audit | beats existed but order, framing and screen direction were unchecked | `avqa` fails a late hook, a close that is not last, a reaction in wide, an axis flip, an unmotivated static shot or a shot with no purpose | demo passes 20/20 structural checks; 13 AV tests |
| Length-independent before/after | a 6-shot demo cannot be compared to a 10-shot story on raw counts | comparison reports action/actor/camera/scale rates per shot | action per shot **0.50 → 0.833**; two actors **0.30 → 0.667**; camera variety **0.80 → 1.00** |
| Mix edge fades | a hard WAV start/end clicks after AAC | 80 ms in / 120 ms out on mix and ducked bed | implemented in `mixdown`; audio tests green |
| Shorter direction demo | the full 31 s film is expensive to iterate | 6 shots, 20.4 s, hook → setup → development → reaction → escalation → close | `projects/av_direccion_demo/`; structural QA clean; render and delivery QA recorded separately |

## Done — 0.10.3: audio integrity, manifest lock, determinism slice

| Item | Why | Done when | State |
|---|---|---|---|
| Narration actually in the delivery | the mix graph dropped the voice while QA passed | measure the MP4 against the voice stem, not only against non-silence | `voice_in_delivery` **0.9209**; QA **13/13**; MP4 re-assembled |
| Deterministic mixer | the FFmpeg sidechain/amix graph was unreliable and clipped | one mixer with a measured voice envelope and a limiter | NumPy mixer; peak **0.844**; mix-vs-voice **0.8985**; 3 windows within 3 dB |
| Concurrent render safety | two renders could swap `project.json` | one process holds a lock, the other fails fast | `ManifestBusy` in 5 s; lock test passes |
| Reproducibility gate | a full double render costs 48 min | two short renders through the same path compare structurally | 30 frames × 2: PSNR **53.12 dB**, SSIM **0.99696**; mix SHA identical; full render still open |
| No silent soundtrack fallback | `score.wav` could be muxed after a correct mix existed | `assemble` prefers `mix.wav` | soundtrack selection test passes |

## Done — 0.10.2: repository audit and caption clock

| Item | Why | Done when | State |
|---|---|---|---|
| Caption timing in the render | the SRT was timed, the burned-in layer was not | `shot.captions` from the take clock consumed by `Subtitles.tsx` | 23 cues on 8 shots; **0 ms** reveal error vs the plan (gate 120 ms) |
| Mix sample rate | `voicecheck` assumed 48 kHz | read the rate from the file | 8 kHz fixture test passes; no false silence |
| QA on wordless manifests | a shot without `line` crashed coverage | optional access | regression test passes |
| Performance claim | docs said 500 frames/min | measured render governs | corrected to 38 frames/min (927 frames / 1464.45 s) |
| Audit package | reviews were scattered | evidence in one place | `quality/repository_audit/` (7 documents) |

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
6. **Real style consistency check.** Palette drift is a proxy. Gate: a
   perceptual distance (CIEDE2000) over a reference frame per shot, with a
   threshold calibrated on accepted renders.
7. **Camera-aware UI reflow.** This is UI work and is deliberately out of this
   iteration; boxes are still resolved once per shot. Gate: per-frame collision
   check over a moving-camera shot, with zero frames in violation.
8. **Composition rules with teeth.** Overlap and safe area are checked; visual
   weight and headroom are not. Gate: a composition report that flags a subject
   pressed against the frame edge.
9. **Regression suite over three accepted renders.** Currently two references
    are registered. Gate: `evaluate.compare` runs on every demo and fails on
    drift.
10. **Per-character body silhouettes.** Identity now carries height, head radius,
    hat and palette, but the torso/limb paths are still one rig. Gate: each
    recurring character has a distinct body outline, judged side by side in
    `IdentitySheet` without changing head or coat.
11. **Render provider that cannot hang.** `studio.py render` streams to
    `logs/render.log`, the `--manifest` activation is exception-safe, and a
    fail-fast lock stops a second process from swapping the active manifest. One
    full 24-minute render and two 30-frame structural renders completed. Priority:
    high (blocks a reproducible delivery). Gate: two consecutive **full** renders
    through `studio.py render`, with streaming logs and no manual fallback.

## Staged plan to maximum practical quality

Do not advance a stage because code exists; advance when its gate passes.

### Stage 0 — Stability (current)

- ~~Manifest lock~~ **done**: `manifest_lock` / `ManifestBusy`; the second process
  fails in 5 s and the active bytes are untouched.
- Short reproducibility gate **done**: two 30-frame renders, PSNR **53.12 dB**,
  SSIM **0.99696**, mix SHA identical.
- Two consecutive **full** renders with streaming logs (B-06) **open**: 927 frames
  each, ≈24 min per render.
- Calibrate QA against a third accepted render; keep **178 tests** and `tsc` green.

Gate: no critical regression, reproducible full render, no global-state race.

### Stage 1 — Core output quality (in progress)

- ~~Camera intensity and interaction presets~~ **done**: `cameraIntensity`,
  `handheld`, `point`, `react`.
- ~~Narrative/continuity audit~~ **done**: beat order, beat framing, axis,
  static intent, purpose and speech density.
- ~~Compound action score~~ **done**: `ActorSpec.sequence`, phase validation and
  `action_completion`; S02/S03 each carry two phases.
- ~~Per-shot motion evidence~~ **done**: `qa.shot_motion`; min 2,438, no low-motion
  shots in the current demo.
- Distinct body silhouettes inside the shared rig. **Open.**
- Prop handoff and contact tracked by position, not by preset naming. **Open.**
- Verify caption chunks in rendered pixels (OCR or frame diff), not only in data.
  **Open.**

Gate: human-reviewed identity/pose sheet; audited prop contact; rendered reveal
within 120 ms.

### Stage 2 — Visual quality

- Set density and foreground occluders.
- Per-style drawing packs instead of token-only styles.
- Composition rules for headroom and edge pressure.

Gate: side-by-side human review against the reference corpus; no metric-only
claim of quality.

### Stage 3 — Advanced capabilities

- Lip-sync from Kokoro phonemes.
- Additional voice registers.
- 16:9 / 1:1 format pass.
- Optional generation providers behind the existing spend gate.

Gate: each capability has a real artefact, a test and a documented limit.

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
