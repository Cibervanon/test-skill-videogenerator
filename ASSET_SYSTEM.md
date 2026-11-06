# ASSET SYSTEM — shared library, forge and render integration

Status: **implemented and exercised by a real still render**. No video was
generated for this delivery. The proof is
`projects/asset_forge/preview/contact_sheet.jpg`, built from two Remotion stills
of the same composition.

The system creates, versions, previews, validates and reuses assets without a
second catalogue and without a second renderer:

```
prompt → forge → assets/registry.json (metadata + versions)
                  ├─ assets/generated/<type>/<id>/vN/asset.json
                  ├─ assets/generated/<type>/<id>/vN/preview.svg
                  └─ studio/src/data/generated_assets.json (active render data)
                                ↓
                       assets/catalog.json (derived, one catalogue)
                                ↓
                 library.compose → projects/<id>/manifest.json
                                ↓
             Remotion: GeneratedScene / PropLayer / Actors / OverlayLayer
```

## 1. Audit (what existed before this layer)

| Area | Existing implementation | Reused |
|---|---|---|
| Catalogue | `scripts/acs/library.py`, `assets/catalog.json` derived from sources | extended, not replaced |
| Hand-written extras | `assets/registry.json` merge path already existed but was empty | created, now schema 2 |
| Characters | `studio/src/data/cast.json`, `Character.tsx`, `Actors.tsx` | merged generated identities; same rig |
| Sets | five TSX scenes in `studio/src/scenes/` | untouched; generated sets use the same SVG space |
| Props | `hold` is a closed union in `Character.tsx` | generated props compose in the scene, not in the hand enum |
| UI / graphics | 13 overlay types in `studio/src/motion-graphics/` | generated graphics resolve to that renderer |
| Camera | `CameraRig.tsx` | unchanged |
| Composition | `Demo.tsx` had a hardcoded five-scene map | added generated-set fallback; same composition |
| Catalogue search | id/name/description/tag only | added style, scene, character, usage, compatibility, similarity |
| Validation | ids, files, dependencies, licence | added schema-2 fields, previews, versions, provenance, renderability |
| Previews | none for assets | SVG previews per generated asset |
| References | visual references were not persistent | `assets/references.json` + `scripts/acs/references.py` |
| Licences | licence field only | provenance, source, date, restrictions, reference validation |

What could break and was protected: manifests without the new fields still
render; canonical cast entries always win over generated ones; unknown ids still
abort composition; no existing scene, rig, camera or overlay file was replaced.

## 2. One catalogue, one renderer

There is still exactly one searchable asset catalogue: `assets/catalog.json`.
It is rebuilt from:

- canonical cast, scene components, engine modules, voices, SFX, cameras and
  transitions;
- `assets/registry.json`, which now includes schema-2 forged assets.

`studio/src/data/generated_assets.json` is **render data**, not a catalogue. It
contains the active version of generated sets, characters, expressions, props and
graphics. `GeneratedScene`, `PropLayer`, `Actors` and the existing
`OverlayLayer` read it. No second render engine exists.

## 3. Asset record

Every schema-2 registry entry carries:

`id`, `name`, `type`, `category`, `description`, `style`, `resolution`,
`aspect`, `transparent`, `path`, `preview`, `version`, `versions`,
`dependencies`, `tags`, `usage`, `character`, `scene`, `config`, `license`,
`provenance`, `compatibility`, `status`, `validated`, `created`, `layers`,
`signature`, `references`.

`versions` is append-only. A new request with the same spec returns the existing
asset (duplicate), a changed spec creates `vN+1`, and older version directories
remain. `assets show --version N` reads an archived version.

## 4. Representations

- **Flat background**: set spec with a single `background` layer; used when the
  request asks for a flat/simple plate.
- **Layered background**: `background → midground → foreground → lighting →
  atmosphere`, with shared coordinates and palette.
- **Variation**: a night/warm request can recolour the previous set geometry
  instead of inventing a new location.
- **Character**: identity fields accepted by the existing procedural rig
  (`coat`, `coatDark`, `hat`, `hatBand`, `height`, `headRadius`, hat/hair/facial
  hair), plus descriptive palette, silhouette and wardrobe metadata.
- **Expression**: values for `brow`, `mouth`, `headTilt`, `yaw`, `blink`; applied
  over an acting preset and never allowed to change identity.
- **Prop**: SVG primitives with a pivot, placed in scene coordinates and
  composited in `back` or `front` of actors.
- **Motion graphic / UI**: an overlay spec consumed by the existing
  `OverlayLayer`; numeric graphics require a source or `illustrative: true`.

## 5. Workflow for another user or agent

```bash
# 1. Search before creating.
python scripts/studio.py assets search --query laboratorio
python scripts/studio.py assets similar --id set:laboratorio
python scripts/studio.py assets references --purpose lighting

# 2. Create from a request.
python scripts/studio.py assets generate \
  --prompt "Genera un fondo de laboratorio" \
  --id laboratorio \
  --reference ref:cinematic-warm-cool

# 3. A variation keeps the location and changes atmosphere.
python scripts/studio.py assets generate \
  --prompt "Genera un fondo nocturno basado en el laboratorio existente" \
  --id laboratorio

# 4. A character can carry a reusable expression.
python scripts/studio.py assets generate \
  --prompt "Genera un personaje de científico con expresión de sorpresa" \
  --id cientifico

# 5. Props and graphics are independent reusable assets.
python scripts/studio.py assets generate \
  --prompt "Genera una lámpara compatible con el escenario del laboratorio" \
  --id lampara_laboratorio
python scripts/studio.py assets generate \
  --prompt "Genera un gráfico animado de comparación" \
  --id comparacion

# 6. Validate and inspect.
python scripts/studio.py assets validate
python scripts/studio.py assets preview --id set:laboratorio
python scripts/studio.py assets versions --id set:laboratorio

# 7. Compose a project through the catalogue and render a still.
python scripts/studio.py compose \
  --spec projects/asset_forge/spec.json --project projects/asset_forge
```

The agent must: interpret the request, search existing assets, identify an
existing set/character to reuse, choose reuse vs variation vs creation, generate,
validate, preview, register, and confirm that `compose` resolves it. It must not
edit the engine when a compatible asset is enough.

### Request vocabulary

| Request | Asset |
|---|---|
| “fondo de laboratorio” | `set:laboratorio` |
| “fondo nocturno basado en…” | new version of the same `set:` id |
| “personaje de científico” | `character:cientifico` |
| “personaje con expresión de sorpresa” | character + `expression:*` |
| “lámpara compatible con el escenario” | `prop:*` |
| “gráfico animado de comparación” | `graphic:*` with an existing overlay type |
| “interfaz/panel” | `ui:*` with an existing overlay type |

## 6. References

`assets/references.json` stores visual, character, background, composition,
lighting, movement and style references. Each record has an id, purpose, source
path, licence, provenance, tags, applicability and notes. `references.select`
returns only the relevant subset; the whole library is never attached to a
request.

Adding a reference requires a real source path and a known licence:

```bash
python scripts/studio.py assets reference \
  --name "Night key light" --purpose lighting \
  --path "projects/av_direccion/quality/after_contact.jpg" \
  --reference-license original \
  --tags night,warm,cool --applies-to set,lighting
```

Existing records are never overwritten; a revision gets a new id. References are
metadata, not renderable assets, because they are not composed by Remotion.

## 7. Previews and validation

Generated assets get an SVG preview next to their version:

- set: full scene and its layers;
- character: identity portrait and palette;
- expression: face preview with the chosen values;
- prop: scale/pivot preview;
- graphic: static chart/callout preview.

`schema-2` validation fails on: missing required metadata, missing preview,
missing provenance fields, unordered/duplicate versions, latest pointer not the
highest version, missing archived file, unsupported engine, non-validated status,
non-renderable generated set, missing/unspecified licence, missing dependency, or
a dependency of a forbidden type. Invalid specs are rejected **before** the
registry write.

## 8. Render integration

- `GeneratedScene` renders the active set inside the same 1080×1920 camera stack.
- `PropLayer` renders props before/after the actor layer.
- `cast.ts` merges generated identities; canonical identities win.
- `Actors.tsx` applies a generated expression over the selected performance
  preset and fails loudly on an unknown expression.
- `library.compose` resolves `set:`, `character:`, `expression:`, `prop:` and
  `graphic:` ids and aborts on unknown ones.
- `Root.tsx` adds `AssetForgeDemo`; it uses the same `CinematicProject` as the
  active `CinematicDemo`, not a copy of the engine.

The proof project uses one generated set, one generated character, one generated
expression, one generated prop, one generated graphic, and the existing
`set:doorway` + `character:elder`. It renders as stills at
`projects/asset_forge/preview/A01_generated.png` and
`A02_existing.png`.

## 9. Licences and provenance

Forged assets default to `CC0-1.0` and record:

- origin: `generated-locally`;
- author: `asset_forge / local deterministic primitives`;
- source: generated locally from a prompt, no external model/image/asset;
- date;
- restrictions: no external model or reference asset was used.

A reference or externally supplied asset with unknown provenance/licence is
rejected. The forge spends no credits and makes no network call.

## 10. Tests and evidence

- `tests/test_assets.py` covers generation, validation, previews, versions,
  duplicate detection, search, similarity, composition, expressions/props/graphics,
  cast merging, references and the real proof stills.
- Full suite: **148 passed**.
- `cd studio && npx tsc --noEmit`: exit 0.
- `python scripts/studio.py assets validate`: 38 assets checked, OK.
- Remotion stills: two frames of `AssetForgeDemo`, inspected visually. A01 shows
  the generated night laboratory, scientist, surprised expression, lamp and
  comparison graphic. A02 shows the existing doorway and elder.

No MP4 was rendered for this request.

## 11. Known limits

- The forge is a **local deterministic primitive composer**, not a diffusion/
  image model. It creates renderable vector assets, not photoreal images.
- The set grammar is currently laboratory-led; other subjects are mapped onto
  the same room grammar. New grammars belong in `_set_spec`, not in a second
  renderer.
- Generated characters use the one existing body rig. They can change identity
  data, palette, hat/hair and expressions, not anatomy.
- Generic props use a small primitive vocabulary (lamp archetype and a generic
  object). The `hold` prop enum remains for hand-authored actor props.
- Generated assets are fixed to 1080×1920 / 9:16; other formats are rejected
  explicitly until a format pass exists.
- Previews are SVG, not rendered PNG/MP4; the proof stills are the pixel evidence.
- Reference selection is tag/purpose based, not visual embedding search.
- `assets/catalog.json` remains derived. Do not hand-edit it; edit the source or
  `assets/registry.json` and rebuild.
