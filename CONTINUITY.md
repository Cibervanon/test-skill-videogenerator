# Character state and continuity (0.10.6)

This is a planning and audit layer on top of the existing actor rig. It does not
simulate a body in 3D and it does not add a second renderer.

## The state record

`av_director.plan` keeps an actor ledger across the shot list. For each actor
that appears in a shot it writes:

```jsonc
"continuity": {
  "entry": {"x": 740.0, "facing": -1, "hold": "rope"},
  "exit":  {"x": 740.0, "facing": -1, "hold": "rope", "preset": "turn"},
  "carried": true,
  "shift": 0.0,
  "scene": "workshop",
  "motive": ""
}
```

The ledger is copied into the manifest as `manifest.continuity.states`, so the
renderer and `avqa` consume the same resolved values. The renderer still receives
ordinary actor fields; `continuity` is evidence, not a new render input.

## `carry`

An actor can declare:

```jsonc
{"id": "young", "preset": "reach", "carry": true, "y": 1740, "scale": 1.28}
```

When `carry` is true, `av_director` inherits `x`, `facing` and `hold` from that
actor's previous exit. If `x` is omitted there is no fallback silently invented:
without a previous state the shot fails.

`carry` is refused across a scene change. A cut to a different set is not a
continuation of stage position. The new scene must declare its own blocking (or
the planner must be extended with a real transition model).

An explicit same-scene move over **260 px** without a `continuityMotive` fails.
This is the teleport guard. A motivated reframing (for example a close-up inside
the same room) is declared explicitly and recorded. Facing flips without a
turn/point/react phase and held-prop changes without an explicit phase are
warnings, not silent passes.

## QA

`avqa.character_continuity` re-reads the resolved ledger and reports:

- the number of carried actor states;
- same-scene shifts over 260 px without a motive;
- a missing ledger as `pending`, never as a pass.

The check is structural. It proves that the manifest does not reset or teleport
an actor without saying so; it does not prove that the rendered pixels match the
ledger. That still needs frame inspection and human review.

## New story: `projects/av_ultima_medida`

The new story is **La última medida**, set in a tailor's workshop at dawn. It is
not the bell/village/cemetery structure:

| Shot | Beat | Action |
|---|---|---|
| S01 | hook | the snapped measuring tape on the worktable |
| S02 | setup | the tailor and the apprentice enter the same workspace |
| S03 | development | the apprentice turns and reaches for the measure (carried from S02) |
| S04 | reaction | wordless close-up of the tailor in the same workshop |
| S05 | escalation | the tailor points to the skipped stitch (workshop restored with a motive) |
| S06 | close | both actors keep their blocking; the coat is finished (carried from S05) |

The set is `studio/src/scenes/Workshop.tsx`; it has a dawn window, thread shelf,
dress form, worktable, the snapped tape and the skipped stitch. It contains no
snow and no bell.

## Rendered evidence (0.10.6)

`projects/av_ultima_medida` resolves **5 carried states** across six shots, with
`continuity_issues: []`. The final render is 672 frames, 1080×1920, 30 fps,
22.4 s, H.264/AAC, 11.989.156 bytes. `avqa` reports 3 sequences / 6 phases,
4/6 action shots and no structural failure; `inspect` marks **0/6** shots.

The frame strip `quality/continuity_strip.jpg` was opened: S01–S03 stay in the
same workshop, S04 is a close-up of the same room, and S05–S06 keep the blocking
without snow, bell or cemetery. This is visual evidence from selected frames, not
a pixel-level drift tracker or a human rating of the whole film.

## Limits

- **No IK or contact.** `hold` is a forearm prop attachment, not a hand lock.
- **No handoff solver.** A prop can change hands only through an explicit
  sequence/blocking declaration; the audit does not infer physical contact.
- **State is resolved at plan time.** The renderer does not own a persistent body
  across `<Sequence>` boundaries; `carry` is deliberately lowered into ordinary
  actor fields.
- **No pixel drift check.** The audit measures the plan. Frame inspection and
  human review remain separate.
- **Narrative, acting, rhythm and style remain human dimensions.**
