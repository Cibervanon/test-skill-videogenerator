# External repositories audit

Audited 2026-11-04, licences read at source. **No dependency was added** in this
cycle: the goal is a decision with evidence, not an installation.

| Repo | Licence | OSI | Latest | Maintained | Decision |
|---|---|---|---|---|---|
| [remotion-dev/remotion](https://github.com/remotion-dev/remotion) | Remotion License (custom, source-available) | **no** | 4.0.540 (2026-11-02) | very active | **keep** (already the engine), compliance note |
| [d3/d3](https://github.com/d3/d3) | ISC | yes | 7.9.2 (2026-11-03) | active | **adapt the maths, not the dependency** |
| [airbnb/lottie-web](https://github.com/airbnb/lottie-web) | MIT | yes | 5.13.0 (2024-11-19) | dormant (~2 years) | **discard** |
| [rive-app/rive-react](https://github.com/rive-app/rive-react) | MIT | yes | 4.38.0 (2026-10-27) | very active | **discard for now** |
| [shreefentsar/remotion-video-toolkit](https://github.com/shreefentsar/remotion-video-toolkit) | none in repo (registries claim MIT/MIT-0, contradicting each other) | unverifiable | no tags | 4 commits, last 2026-01-29 | **discard as a dependency** |

## Remotion — compliance is the finding

The licence is **not** open source: free for individuals, non-profits and
for-profit companies with **up to three employees**; a paid Company License is
required otherwise. It also forbids reselling a derivative of Remotion itself.
Technical fit is excellent (React 19 supported since 4.0, offline bundling via
`@remotion/bundler`), but anyone shipping this skill commercially above that
headcount must license it. This is recorded, not worked around.

## D3 — the useful part is the maths

D3's scales, interpolators and shape generators are pure functions, which is
exactly the model this renderer needs (frame in, geometry out). The charts here
are five primitives over plain SVG; adding `d3` would pull a metapackage to
compute scale and path strings already written in ~40 lines each.

**Decision:** keep the hand-written primitives. If the chart vocabulary grows to
layouts (stacked areas, force diagrams, geographic projections), adopt
`d3-scale` + `d3-shape` only, never `d3-selection`/`d3-transition` — those touch
the DOM and run their own timers, which breaks frame determinism.

## Lottie — clean licence, wrong shape

MIT and deterministic *if* you drive it with `goToAndStop(frame, true)` and
clone the JSON when repeaters are present. But the repository has had no commit
since November 2024, and adopting it means authoring animation JSON in another
tool for effects this engine already draws procedurally. No gap it fills.

## Rive — MIT, but it fights the frame model

React 19 is explicitly supported and it is actively maintained. The problem is
architectural: Rive is a stateful real-time runtime with a WASM binary; hitting
exact frames requires bypassing state machines, driving animation time manually
and ensuring WASM init finished before the frame renders. That is a harness, not
an import, and it buys vector cut-out animation this project can already build
with its own rig.

## remotion-video-toolkit — not a library

The repository contains `SKILL.md` and a `rules/` folder of Markdown. No
`package.json`, no source, no build, no releases, and **no LICENSE file**;
third-party registries disagree on the licence. It cannot be bundled, and its
guidance targets an older Remotion/React baseline. Nothing to adopt.

## What was reused instead

Ideas, not code: the storyboard-before-render discipline (already in
`scripts/acs/storyboard.py`), loudness two-pass assembly, and the "one manifest,
one composition" constraint that this cycle extended to overlays and styles.

## Verification

Licence and release facts above come from the repositories, their raw
`LICENSE` files and the GitHub releases/commits APIs, read on 2026-11-04. The
determinism judgements for Rive and Lottie are architectural, not benchmarked
here, and are stated as such.
