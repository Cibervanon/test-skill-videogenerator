# Audiovisual direction (0.9.0 → 0.10.5)

The engine already had a camera, acting presets, a procedural score, a storyboard
and a QA pipeline. What it did not have was an edit decision: why this shot, at
this scale, with this movement, cut here, sounding like this. This layer adds
that decision without adding a second renderer.

## 1. Audit: what existed and what was missing

| System | Before | Reused / extended |
|---|---|---|
| Shot manifest | scene, camera, actors, line, transition frames | **extended** with `beat`, `scale`, `cameraMotive`, `transitionMotive`, `sound` |
| Camera | 9 transform moves (`CameraRig.tsx`) | **extended** with `trackLeft`, `trackRight`, `reframe`, `handheld` and a per-shot `cameraIntensity`; all old moves kept |
| Acting | 7 intent presets (`Actors.tsx`) | **extended** with `point`, `react` and compound `sequence` phases; the plan chooses who acts, listens and reacts |
| Audio | scene-derived bell/footsteps/dig | **extended**: a shot can declare timed cues, including intentional silence |
| Score | deterministic `audio_gen` + NumPy envelope duck | reused; demo mixed at `music_gain=0.20` after measuring competition |
| Narrator / voice | Kokoro, cached takes, `voicecheck` | reused unchanged; the eight original lines are preserved |
| Asset library | `library.compose` validates sets/characters/cameras | reused; the director manifest still fails on an unknown id |
| Storyboard / preproduction | `project.write_preproduction` | reused; corrected to sum per-boundary transitions, not every boundary |
| Technical QA | `qa.py` | reused; delivery voice and audio-duration gates remain |
| Creative QA | `avqa.py` | **extended** with beat order, beat framing, axis continuity, static intent, shot purpose and speech density |
| Evaluation | measured vs subjective dimensions | **extended** with a measured `montage` dimension from `av_audit.json` |
| Feedback | `feedback.py` scopes and categories | reused; no second memory system |

There was no beat structure, no shot-scale vocabulary, no stated camera motive,
no explicit transition motive and no creative audit. These are the gaps this
iteration fills.

## 2. Architecture

```
projects/<id>/spec.json       authored beat sheet (story decisions)
        │
        ▼
av_director.plan()            validates beats, fills scale/camera defaults,
        │                     requires motifs, converts transitions and sounds
        ▼
library.compose()             resolves every scene/character/camera asset by id
        │
        ▼
manifest.json                 the same schema the existing renderer consumes
        │
        ├── CameraRig + Actors + sets + captions  → Remotion render
        ├── audio_gen.spec_from_project()         → score + declared cues
        └── avqa.audit()                          → creative QA (structural)
                                                     │
                                                     ▼
                                             evaluate.scorecard()
                                             measured `montage` dimension
```

The planner is deterministic and does not write prose or invent shots. A beat
sheet may omit a scale or camera; the planner uses the function's default. It
does not omit a camera motive: an unmotivated move is a plan error, and a
dissolve without a motive is rejected.

### Beat vocabulary

`hook`, `setup`, `development`, `insert`, `escalation`, `reaction`, `reveal`,
`close`. Not every film needs every function; the audit only requires the
functions the author declared to be coherent, and warns when hook or close is
absent.

### Shot-scale vocabulary

`wide`, `full`, `medium`, `close`, `detail`. The renderer still receives actor
scale, position and camera transform; `scale` is the directorial label and the
QA unit. This is honest: the current camera is a 2.5D transform rig, not a lens
model with focal length.

## 3. Demo: `projects/av_direccion`

Same story, same eight narration lines and same assets as `ui_direccion`, with
two wordless shots that create reaction and pause. No generated footage and no
new set.

| Shot | Beat | Scale | Camera | Action / information | Sound |
|---|---|---|---|---|---|
| S01 | hook | detail | tiltUp | the silent bell, before the keeper | bell |
| S02 | setup | close | pushInSlow | three winters on the keeper's face | footstep |
| S03 | development | wide | panRight | apprentice crosses the square with the rope | footsteps |
| S04 | insert | detail | static | rope reaches the bell; deliberate pause | silence |
| S05 | development | medium | drift | keeper and apprentice in one two-shot | footstep |
| S06 | reaction | close | dollyIn | the keeper's wordless answer | footstep |
| S07 | reveal | medium | dollyIn | the mechanism, with the rope already in hand | footstep |
| S08 | reveal | close | pushInSlow | "the third one nobody looked at" is the apprentice | footstep |
| S09 | escalation | medium | trackRight | he points to the missing rope | footsteps |
| S10 | close | wide | dollyOut | graveyard at first light; consequence, not explanation | digging |

The original lines are kept in order:

1. Aquella noche, el guardián no tocó la campana.
2. El pueblo llevaba tres inviernos sin oírla.
3. El aprendiz subió al campanario con una cuerda.
4. Comparó lo que el pueblo creía con lo que vio.
5. El mecanismo tenía tres pasos.
6. El tercero era el que nadie miraba.
7. El aprendiz señaló la cuerda que faltaba.
8. Desde entonces, el silencio tuvo fecha.

Wordless shots are S04 (the pause after the rope arrives) and S06 (the keeper's
reaction). They are not missing narration; removing the line is the edit decision.

## 4. Creative QA, measured

`scripts/acs/avqa.py` audits the edit plan; it does not inspect taste.

| Check | Result |
|---|---|
| hook / setup / escalation / reaction / close declared | pass |
| hook length | 3.4 s |
| shot scales | 4 distinct; longest run 1 |
| camera intents | 8 distinct |
| non-static camera moves with a motive | 9/9 |
| moving-shot share | 0.9 (one deliberate static shot) |
| dissolves with a motive | 2/2 |
| shots with sound | 9/10; 15 timed events |
| shots with an acting preset | 5/10 |
| reaction shots | 1 |
| repeated narration lines | none |
| duration | 30.933 s |

Structural failures: **none**. Human review remains required for narrative,
acting, rhythm and style; those dimensions stay `pending` in `evaluate`.

S04 is a declared `insert`/`detail` shot, so composition QA records its 60.3%
flat-tile ratio separately (`declared_insert_max`) instead of treating a
contemplative bell plate as an empty scene. The exemption is limited to that
explicit declaration; it does not lower the global empty-scene threshold.

The `montage` dimension only appears as measured when `quality/av_audit.json`
exists. A legacy project without beat fields is not retroactively declared
failed; its beat checks are `pending`, while derived scale/camera metrics are
still reported.

## 5. Before / after

`  python scripts/studio.py avqa --project projects/av_direccion \
  --manifest projects/av_direccion/manifest.json \
  --baseline projects/ui_direccion/manifest.json
# shorter, interaction-led direction demo:
# python scripts/studio.py av --project projects/av_direccion_demo \
#   --spec projects/av_direccion_demo/spec.json`

writes `projects/av_direccion/quality/before_after.md`.

| Metric | ui_direccion | av_direccion |
|---|---|---|
| shots | 8 | 10 |
| duration | 27.4 s | 30.933 s |
| average shot | 3.42 s | 3.09 s |
| distinct scales | 4 | 4 |
| longest scale run | 3 | 1 |
| distinct cameras | 7 | 8 |
| moving share | 0.875 | 0.9 |
| action shots | 2 | 5 |
| reaction shots | 0 | 1 |
| shots with audio | 7 | 9 |
| audio events | 7 | 15 |
| two-actor shots | 2 | 3 |

Structural failures fell from `scale_run, camera_motivation, action_coverage` to
none. This is evidence about the edit, not proof that the rendered film is
better; the rendered QA and the human review are separate.

### Rendered check

The final MP4 is 30.933 s, 927 frames, 1080×1920, H.264/AAC, 17.5 MB. Technical
QA passes 11/11: motion 10.246 (baseline 9.923), freeze 0.069 (baseline 0.161),
black frames 0, loudness −12.7 dB, audio activity 0.195, caption plan 0.874.
The caption drop from 1.0 is the two declared wordless shots, not a missing
caption. `inspect` flags 0/10 shots; `evaluate` has 10 measured dimensions, no
failures and four human-pending dimensions.

The contact sheets `quality/before_contact.jpg` and `quality/after_contact.jpg`
were sampled from both MP4s. The after sheet shows the added reaction in the
doorway, the pause on the bell, the two-shot explanation, the town close-up of
the overlooked apprentice and the dawn close. The style remains flat vector
animation: more setups and motivated cuts, not more visual detail.

## 6. Audio

The score and foley remain procedural. Explicit cues are offsets inside the
shot; `audio_gen` converts them to the global timeline. A declared empty list
means silence for that shot and suppresses the old scene-derived effects.

The default mix (`music_gain=0.45`) left 40 windows within 3 dB of the voice;
the corrected `music_gain=0.20` mix now leaves **3**.
At `0.28` it fell to 15; at `0.20` to 4, with the music still present and the
envelope ducking breathing in the gaps. The delivered mix uses 0.20. This is a measured
mix decision, not a claim that the music is good.

## 7. Reproduce

```bash
python scripts/studio.py av --project projects/av_direccion \
  --spec projects/av_direccion/spec.json --write-active
python scripts/studio.py preproduction --project projects/av_direccion \
  --manifest projects/av_direccion/manifest.json
python scripts/studio.py voice --project projects/av_direccion \
  --manifest projects/av_direccion/manifest.json --provider kokoro
python scripts/studio.py audio --project projects/av_direccion \
  --manifest projects/av_direccion/manifest.json
python scripts/studio.py mixdown --project projects/av_direccion \
  --music-gain 0.20 --voice-gain 1.0
  python scripts/studio.py avqa --project projects/av_direccion \
  --manifest projects/av_direccion/manifest.json \
  --baseline projects/ui_direccion/manifest.json
# shorter, interaction-led direction demo:
# python scripts/studio.py av --project projects/av_direccion_demo \
#   --spec projects/av_direccion_demo/spec.json
cd studio && npx remotion render src/index.ts CinematicDemo \
  ../projects/av_direccion/output/picture_silent.mp4 --concurrency=4
cd .. && python scripts/studio.py assemble --project projects/av_direccion \
  --audio projects/av_direccion/generation/audio/mix.wav
python scripts/studio.py qa --project projects/av_direccion \
  --manifest projects/av_direccion/manifest.json
```

## 8. Camera as intention, not decoration (0.10.4)

A move now carries an intensity as well as a motive:

```jsonc
{
  "camera": "trackRight",
  "cameraIntensity": 0.8,
  "cameraMotive": "move with the rope hand so the climb is an action"
}
```

The director fills a beat-specific default (hook 0.9, setup 0.7, reaction 0.85,
close 0.75, insert/static 0). The renderer multiplies translation, rotation and
the scale delta by that value, so the same vocabulary can whisper or push. The
new `handheld` move is a low-amplitude, deterministic operator drift, not random
noise; `static` remains a legitimate choice and is audited for a motive.

Acting gained two presets that make interaction readable:

- `point` — eyes arrive first, then the arm; the hand settles instead of
  snapping. It is slower than `reach`, so it can carry a line.
- `react` — a small recoil, held brow and catching breath for a wordless
  reaction close-up.

These are still preset curves, not IK or mocap. They coordinate with the shot,
the camera and the sound cue; they do not simulate physical contact.

## 9. Creative QA: what is now measured

`avqa` still refuses to score taste. It now checks decisions that were previously
only prose:

| Check | What it catches |
|---|---|
| `beat_order` | a hook that arrives late or a close that is not last |
| `beat_framing` | a reaction in extreme wide, a close in detail, a reveal with no face/object scale |
| `axis_continuity` | the same two actors reversing screen direction between shots in one scene |
| `static_intent` | an unmotivated tripod shot, or a film that is mostly static |
| `shot_purpose` | a shot with no line, action, insert or reaction |
| `speech_density` | narration delivered faster than the ear can follow |
| `camera_intensity` | an intensity outside 0.35..1.35 (static may use 0) |
| `action_completion` | a compound sequence with an invalid window or a last `walkIn` |
| `shot_motion` | a per-shot motion reading; low readings are diagnostic, not automatic failures |

Before/after comparison also reports length-independent rates: action per shot,
two-actor shots per shot, camera and scale variety per shot, and audio events per
second. Raw counts alone would penalise a shorter demo for being shorter.

## 10. Compound actions and per-shot motion (0.10.5)

A shot can now carry an action score instead of one frozen preset:

```jsonc
"sequence": [
  {"preset": "walkIn", "start": 0.02, "end": 0.62, "from": 180, "to": -20, "x": 760},
  {"preset": "turn",   "start": 0.66, "end": 1.00, "x": 740}
]
```

The phase windows are normalized shot time. Each phase is evaluated on its own
local clock through the existing `perform` function; adjacent phases cross-fade
over ±4% of the shot. This is how S02 completes **walk → stop → turn** and S03
completes **turn → reach** without resetting the character at a phase edge.

The planner rejects unknown presets, empty scores, invalid windows and overlaps.
It warns about pose gaps, a sequence that starts late and a sequence that ends
mid-walk; `avqa` makes the last case a structural failure (`action_completion`).

QA now also writes `shot_motion`: every visible shot is decoded separately, and
reports mean motion, moving ratio, pan/tilt and a `low_motion` diagnostic. On the
current demo: **min 2,438**, mean **4,249**, **0 low-motion shots**; S04 remains a
quiet declared reaction, not a missing animation.

## 10.6 Carried state and the new story

`carry` is resolved in the planner, not in the renderer. The ledger records
entry/exit `x`, `facing`, `hold`, preset, scene and shift; `manifest.continuity`
is the same resolved evidence consumed by `avqa`. Five states are inherited in
`av_ultima_medida`, with no scene change and no unmotivated shift. The teleport
guard fails a same-scene move over 260 px unless the shot declares
`continuityMotive`.

The new film uses `workshop` for all six shots. This trades location variety for
spatial continuity: the camera changes scale and angle, but the tailor and the
apprentice keep their blocking. S04 is a deliberate wordless close-up; S05
returns to the wide workshop with a motive. `quality/continuity_strip.jpg` was
opened and reviewed; it is not a substitute for a full human pass.

## 11. Limits

- **Scale is a declared unit, not a lens.** The camera is a transform rig; there
  is no focal length, depth of field or true 3D parallax.
- **The planner does not understand prose.** It validates and completes an
  authored beat sheet; it does not decide the story by itself.
- **The audit cannot see the frame.** It measures structure; composition,
  legibility and consistency still come from `inspect`/`evaluate` and human eyes.
  S04's detail insert is measured but exempt from the empty-scene failure by its
  declared `insert`/`detail` beat; that is a domain rule, not a universal pass.
- **Acting is still preset-based.** The plan coordinates who acts and when; a
  sequence blends preset parameters, but the rig has no IK, cloth, contact or
  visemes.
- **Carried state is planned, not simulated.** `carry` inherits x/facing/hold at
  plan time and refuses a scene change; the renderer still receives ordinary
  actor fields and does not own a body across `<Sequence>` boundaries. The
  `workshop` story proves five inherited states, not physical persistence.
- **A single set is a deliberate trade.** `av_ultima_medida` stays in the
  workshop for all six shots; that strengthens blocking continuity and reduces
  location variety compared with the four-set direction demo.
- **Continuity is asserted by ids and positions, not tracked in 3D.** A prop can
  change hands if an explicit sequence/blocking says so; there is no contact
  solver and no pixel-level drift check.
- **Human review is pending.** Narrative, performance, rhythm and style have no
  score here.
