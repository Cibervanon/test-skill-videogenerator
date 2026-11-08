# Comparison — `av_ultima_medida` vs `av_direccion_demo`

This is an evidence-based comparison, not a blind audience test. Objective
values come from the two `quality/evaluation.md` reports; the visual check comes
from the rendered frame strips. Narrative, acting, rhythm and style remain human
dimensions and are not scored automatically.

## What changed

| Dimension | `av_direccion_demo` | `av_ultima_medida` | Reading |
|---|---|---|---|
| Story | bell / winter village / field | snapped tape / tailor's workshop / skipped stitch | new premise, object and resolution |
| Hook | establishing bell insert | snapped tape on the worktable | new visual anomaly, no bell |
| Structure | hook → setup → development → reaction → escalation → close | hook → setup → escalation → reaction → reveal → close | beat order changed; `development`/`escalation` are not in the same place |
| Location | 4 sets (`bellInsert`, `doorway`, `fieldDawn`, `townNight`) | 1 set (`workshop`) | deliberate spatial continuity; lower location variety |
| Cast | `elder`, `young` | `elder`, `young` | reused rig and cast, not a new character system |
| Action coverage | 5/6 shots, 2 sequences / 4 phases | 4/6 shots, 3 sequences / 6 phases | fewer action shots; more phased action inside the shots that have it |
| Carried states | not audited in that delivery | **5** | new state ledger is exercised |
| Duration / frames | 20.433 s / 612 frames | 22.4 s / 672 frames | slightly longer, still six shots |
| Motion | 8.858 | 4.034 | lower global motion; S04 is a held reaction, so this is not a like-for-like quality score |
| Captions | 0.883 | 0.893 | comparable cue coverage |
| Sound | −17.2 dB | −17.0 dB | comparable mean level |
| Empty-scene max | 0.504 | 0.524 | both below the 0.55 failure threshold |
| Scene continuity | declared per shot | `continuity_issues: []`, 5 inherited states | the new delivery makes continuity auditable |

## Visual check

- `av_ultima_medida/quality/continuity_strip.jpg` was opened.
- S01 shows the tailor, worktable, snapped tape and dawn window.
- S02–S03 keep the same workshop and the tailor/apprentice blocking; the
  apprentice turns and reaches while the carried position is preserved.
- S04 is a close-up of the tailor in the same room, not a new location.
- S05–S06 retain the blocking; the coat and the skipped stitch remain the
  narrative object. No snow, bell, village or cemetery appears.
- `av_direccion_demo/quality/action_sequence.jpg` and its storyboard were used
  only as the previous-delivery reference, not as a template for the new story.

## Improvements supported by evidence

1. Same-scene continuity is now a first-class, checked state instead of a
   per-shot declaration (`carry`, ledger, `character_continuity`).
2. A teleport without a motive is rejected at plan time (260 px guard).
3. The new story changes premise, hook, set, object, beat order and resolution;
   it is not the old winter/bell sequence with renamed labels.
4. The render contains five inherited states with no reported continuity issue,
   and the selected-frame strip is consistent with that claim.

## Regressions and remaining gaps

- **Location variety decreased:** four sets became one. This is intentional for
  continuity, but it is a real trade-off, not an improvement in every dimension.
- **Action coverage decreased:** 5/6 action shots became 4/6. The new film has
  more phases (6) and sequences (3), but fewer shots carry a movement action.
- **Global motion decreased:** 8.858 → 4.034. Part of this is the deliberate
  held close-up; it is not evidence that the new film is better animated.
- **Narrative, acting, rhythm and style are still unscored.** `evaluate` leaves
  4 human dimensions pending. The story is structurally complete, but this
  document does not claim it is more entertaining.
- **No full-film human review, no blind comparison, no audience measurement.**
  The frame strip proves selected-frame consistency, not the experience of the
  whole 22.4 s film.

## Next evidence to collect

- Watch the full MP4 with sound and mark hook strength, clarity of the objective,
  reaction legibility, and whether the close resolves the skipped stitch.
- Add a second non-workshop story that reuses no scene and no beat order, to test
  diversity beyond the current single-set proof.
- Add a transition model before carrying state across a scene change; today the
  planner correctly refuses it instead of inventing a teleport.
