# ASSETS — the persistent library

Every reusable thing has a stable id and lives in one catalogue. A new video
*reuses* assets instead of redrawing them. The catalogue is still
`assets/catalog.json`, derived from the real render sources plus
`assets/registry.json`; there is no parallel asset catalogue.

```bash
python scripts/studio.py assets            # list everything
python scripts/studio.py assets search --query keeper
python scripts/studio.py assets search --type set --style cinematic
python scripts/studio.py assets search --scene laboratorio
python scripts/studio.py assets search --usage prop
python scripts/studio.py assets show --id character:elder
python scripts/studio.py assets similar --id set:laboratorio
python scripts/studio.py assets validate   # ids, files, previews, versions, deps, licences
python scripts/studio.py assets reuse      # what the current manifest reuses
python scripts/studio.py assets rebuild    # regenerate assets/catalog.json
```

## Create assets from a request

```bash
python scripts/studio.py assets generate \
  --prompt "Genera un fondo de laboratorio" --id laboratorio

python scripts/studio.py assets generate \
  --prompt "Genera un fondo nocturno basado en el laboratorio existente" \
  --id laboratorio

python scripts/studio.py assets generate \
  --prompt "Genera un personaje de científico con expresión de sorpresa" \
  --id cientifico

python scripts/studio.py assets generate \
  --prompt "Genera una lámpara compatible con el escenario del laboratorio" \
  --id lampara_laboratorio

python scripts/studio.py assets generate \
  --prompt "Genera un gráfico animado de comparación" --id comparacion
```

The generator writes a version directory, a preview and a registry entry, then
rebuilds the catalogue. It never calls the network and never spends credits.

## Ids

| Type | Example | Source of truth |
|---|---|---|
| `character:<key>` | `character:elder` | `studio/src/data/cast.json` + generated cast |
| `rig:default` | `rig:default` | `studio/src/characters/Character.tsx` |
| `set:<scene>` | `set:doorway` | `studio/src/scenes/Doorway.tsx` or generated set |
| `prop:<key>` | `prop:lampara_laboratorio` | generated prop spec |
| `expression:<key>` | `expression:surprise_cientifico` | generated expression spec |
| `graphic:<key>` | `graphic:comparacion` | generated overlay spec |
| `ui:<key>` | `ui:panel` | generated overlay spec |
| `engine:<module>` | `engine:atmosphere` | `studio/src/engine/*.tsx` |
| `voice:<key>` | `voice:narrator` | `config/voices.json` |
| `sfx:<event>` | `sfx:bell` | the events `audio_gen` actually synthesises |
| `camera:<move>` | `camera:panleft` | `studio/src/engine/CameraRig.tsx` |
| `transition:<kind>` | `transition:cut` | `studio/src/composition/Demo.tsx` |

## What an entry records

`id`, `name`, `type`, `category`, `path`, `description`, `version`,
`dependencies`, `config`, `license`, `created`, `validated`, `tags`.

Schema-2 forged assets additionally record: `style`, `resolution`, `aspect`,
`transparent`, `preview`, `versions`, `usage`, `character`, `scene`, `layers`,
`provenance`, `compatibility`, `status`, `signature`, `references`.

Canonical assets use file mtime as their version because they are edited in
place. Forged assets use append-only numeric versions: a changed request writes
`vN+1`; the old directory and preview stay available through
`assets show --id ... --version N`.

## Validation

`validate` fails on: duplicate ids, missing files, unknown dependencies, a
dependency of a type that is not allowed (a set cannot depend on a voice), a
missing/unspecified licence, and for schema-2 assets: missing metadata, preview,
provenance, ordered versions, archived version file, unsupported engine,
non-validated status, or a non-renderable generated set.

## Previews

Every forged asset has an SVG preview next to its spec:

```
assets/generated/set/laboratorio/v2/asset.json
assets/generated/set/laboratorio/v2/preview.svg
```

`assets preview --id set:laboratorio` prints the active preview path.

## References

`assets/references.json` is a persistent, metadata-only reference library.
`assets references` lists it; adding a record requires a real source path and a
known licence:

```bash
python scripts/studio.py assets reference \
  --name "Night key light" --purpose lighting \
  --path "projects/av_direccion/quality/after_contact.jpg" \
  --reference-license original --tags night,warm,cool \
  --applies-to set,lighting
```

References are selected by purpose/tags (`scripts/acs/references.py`), not all
attached to every request. They are not renderable assets.

## Reuse rules

1. `assets search` and `assets similar` before creating anything.
2. If a character exists, reuse its rig and identity, never redraw.
3. If a set exists, reuse it or create a **version** of it; do not invent a new
   location for a lighting/time-of-day change.
4. Props and graphics are independent assets; do not add a second character just
   to hold a prop.
5. A change that must not break older projects becomes a version, not an
   overwrite.
6. Unknown ids abort `compose`; they never render blank.

`projects/<id>/manifest.json` is the manifest as it was used, so an old film can
be reproduced after the active project moves on.

## Deliberately not stored

Final renders, frames and WAVs are outputs, not assets: they are large and
regenerable. The library stores **editable, programmatic** sources.

See `ASSET_SYSTEM.md` for the audit, architecture, full workflow and limits.
