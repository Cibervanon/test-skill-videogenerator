# Feedback system

Corrections are data, not chat. They live in `feedback/records.jsonl`, survive
sessions, and are rendered into documents that say exactly how strong each
conclusion is.

**This is not automatic learning.** A record is a note. A fix is a code change. A
rule exists only when a non-local observation has been applied *and* validated
with evidence.

## Record

```json
{
  "id": "FB-0001",
  "date": "2026-11-04",
  "project": "sistema_demo",
  "scene": "S04",
  "component": "projects/sistema_demo/spec.json",
  "problem": "El panel de UI se solapa con la banda de subtítulos",
  "requested": "subirlo por encima de 0.855",
  "category": "ui",
  "severity": "high",
  "scope": "local",
  "evidence": "inspect: S04 P1 overlaps the caption band",
  "solution": "panel y=0.58 h=0.22",
  "status": "validated",
  "validation": "PASS — inspect: 0/4 flagged, overlays OK"
}
```

## Categories

`character_design`, `character_animation`, `acting`, `background`, `composition`,
`camera`, `lighting`, `color`, `typography`, `ui`, `motion_graphics`,
`storytelling`, `editing`, `audio`, `voice`, `consistency`,
`technical_rendering`.

## Scopes

| Scope | Meaning | Can become a rule? |
|---|---|---|
| `local` | one scene/shot | no |
| `project` | this piece | only via validation |
| `character` | one identity | yes, with validation |
| `style` | one style token set | yes, with validation |
| `global` | all pieces | yes, with validation |

Scope is inferred from the wording (`"en esta escena"` → local, `"en todos los
planos"` → global) and can be overridden with `--scope`. A single note about one
scene never becomes a global rule: `STYLE_RULES.md` only lists records with
status `validated` **and** a non-local scope.

## Statuses

`recorded → in_progress → applied → validated` (or `rejected`). `validate`
refuses to run without evidence: a measurement, a still, a render, a test.

## Commands

```bash
python scripts/studio.py feedback add --problem "…" --scene S02 --requested "…"
python scripts/studio.py feedback list
python scripts/studio.py feedback apply --id FB-0003 --solution "…" --component "…"
python scripts/studio.py feedback validate --id FB-0003 --evidence "inspect: …"
python scripts/studio.py feedback report          # regenerates the four docs
python scripts/studio.py feedback case --id R-002 --problem "…" --check qa.ok --threshold true
```

## Generated documents

| File | Content | Rule |
|---|---|---|
| `USER_FEEDBACK.md` | every record with evidence and state | never edited by hand |
| `VISUAL_PREFERENCES.md` | categories seen ≥ 2 times | a pattern is evidence, not a rule |
| `STYLE_RULES.md` | validated, non-local rules only | empty until proven |
| `IMPROVEMENT_LOG.md` | applied changes and their validation | an unvalidated change says "pendiente" |
| `feedback/regression_cases.json` | checks an accepted render must keep passing | added per validated fix |

## Loop for a real correction

1. `feedback add` while the observation is fresh (with the scene and the file).
2. Reproduce it: still, inspection or measurement.
3. Change the smallest component that causes it.
4. `feedback apply` with the concrete change.
5. Re-run the check and `feedback validate` with the number.
6. `feedback report`; if the note was really global, it now appears in
   `STYLE_RULES.md` — otherwise it stays a local fix.
