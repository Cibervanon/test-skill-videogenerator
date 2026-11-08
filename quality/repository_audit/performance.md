# Performance report

No optimization was implemented in this pass, so no speedup is claimed. The
numbers below are the baseline the next iteration must beat.

## Environment

| Item | Value |
|---|---|
| OS | Windows 11 |
| Python | 3.14.7 |
| Node | 24.21.0 |
| Remotion | 4.0.540 |
| FFmpeg | 9.0.2 |
| Output | 1080×1920, 30 fps, H.264/AAC |

## Measured baseline

| Workload | Measurement | Derived rate |
|---|---|---|
| Full test suite (174 tests) | 68.06 s | 2.56 tests/s |
| 10 storyboard stills at `--scale 0.35` | 54 s (includes one Remotion bundle + 10 stills) | 5.4 s/still |
| 60-frame render slice | 94.29 s / 96.9 s in two runs | **≈0.63 fps / 38 frames/min** |
| Full film render, 927 frames (recorded in the previous session) | 1464.45 s | **0.63 fps / 38 frames/min** |
| QA on the 30.933 s delivery | completed within the verification command; not separately timed | — |

## Contradiction found and corrected

`LIMITATIONS.md` claimed “roughly 500 frames/min” and “a 34 s film takes ~8–10
minutes”. The recorded provider render is 927 frames in 1464.45 s → **38
frames/min**, i.e. 24 min 24 s for 31 s of film. The documentation now reports
the measured figure. The 500 frames/min number may have described a cheaper
composition or a different machine; it is not supported by this render.

## Determinism cost

The short gate runs 30 frames twice. The decoded frames differ by 0.39/255 on
average (PSNR 53.12 dB, SSIM 0.99696) while the audio mix is byte-identical.
The difference comes from Chrome re-rasterising the SVG `feTurbulence` grain
filter, not from application randomness: every particle and grain offset uses a
seeded PRNG. The gate is therefore structural (PSNR/SSIM), not MD5.

## Likely bottlenecks (not yet profiled)

1. **Per-frame SVG grain.** `FilmFinish` uses `feTurbulence` over the full
   1080×1920 frame. Filters are re-rasterised every frame; this is the first
   candidate for a profile and a cached noise plate. It is also the source of
   the sub-pixel difference between renders.
2. **Deep SVG scene graphs.** Five hand-built sets plus atmosphere layers,
   parallax groups and actors are composited per frame.
3. **Concurrency.** `config/render.concurrency` is 4. No sweep has been run to
   find the CPU/memory optimum; Chrome instances compete for the same cores.
4. **Remotion bundle startup.** The 54 s for 10 stills includes one bundle
   startup; its share is not separated.
5. **No partial re-render.** Any change re-renders all 927 frames; there is no
   shot-level cache.

## Next measurements, in order

1. Profile one 90-frame shot with Remotion's own timing output and Chrome
   tracing; separate grain/filter cost from scene graph cost.
2. Sweep concurrency 2/4/6 on the same shot; record wall time and peak RAM.
3. Measure a cached-grain variant against the current one with a frame diff to
   prove the look is preserved.
4. Only then change the renderer, and re-run the full 174-test suite plus QA.

No performance change should be accepted without a before/after wall-time
measurement and a visual diff.
