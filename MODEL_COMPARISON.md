# MODEL COMPARISON

**Status: NO VERIFICADO.** Nothing in this table was executed here — no keys, no
GPU, and the brief forbids spending. Values are what public sources report, kept
so a later HYBRID/PREMIUM phase knows what to evaluate first. Verify prices,
licences and limits with each provider before enabling an adapter.

Versions change monthly; treat the version numbers as "as reported in late 2026".

## Video generation

| Option | Access | Reported strengths | Reported limits | Cost (reported) | Verified here |
|---|---|---|---|---|---|
| **Wan 2.2** | open weights (self-host) | strongest open video-only quality at high VRAM | ~65–80 GB VRAM at 720p; ~5 s clips | GPU time only (~$0.35/h class rental) | ❌ |
| **LTX-2.x** | open weights + hosted | runs on ~24 GB, longer clips, audio track | quality below the largest models at high motion | GPU time / hosted per-second | ❌ |
| **HunyuanVideo 1.x** | open weights | strong motion, active ecosystem | heavy VRAM, slow | GPU time | ❌ |
| **CogVideoX-1.5** | open weights | lighter, easier to run | older, weaker temporal consistency | GPU time | ❌ |
| **ComfyUI** (orchestrator) | local app | graph workflows, reproducible JSON | not a model; needs the models + GPU | free | ❌ |
| **Runway** | hosted API | strong camera control and editing tools | per-second billing, clip length caps | per second | ❌ |
| **Kling** | hosted API | motion realism, image-to-video | queue times, per-second cost | per second | ❌ |
| **Veo** | hosted API | high fidelity, prompt adherence | availability/region limits, cost | per second | ❌ |
| **Sora** | hosted | long-form coherence | limited access, cost | per second | ❌ |
| **Luma / Hailuo** | hosted API | fast iteration, decent i2v | consistency across shots | per second | ❌ |

**Implication for this repo:** a clip-level adapter would only be worth it where
code cannot reach — photoreal humans, real performance, complex hand contact.
Everything else in the demo (sets, characters, camera, captions, sound) is
cheaper and more consistent in code.

## Image generation

| Option | Access | Reported strengths | Limits | Verified here |
|---|---|---|---|---|
| FLUX.1 family | open weights / hosted | prompt adherence, text rendering, ControlNet ecosystem | licence varies per variant; VRAM | ❌ |
| Stable Diffusion XL | open weights | huge ecosystem (LoRA, ControlNet, IP-Adapter) | older base quality | ❌ |
| IP-Adapter / ControlNet / depth | adapters | character and pose consistency | needs a base model + GPU | ❌ |

## Voice / audio

| Option | Access | Reported strengths | Limits | Verified here |
|---|---|---|---|---|
| ElevenLabs | hosted API | expressive TTS, voice design, cloning with consent | per-character billing, licensing terms | ❌ |
| Piper | local (open) | fast, offline, permissive licences vary by voice | flatter prosody | ❌ |
| XTTS / Coqui | local (open) | cloning, multilingual | licence and maintenance status must be checked | ❌ |
| Whisper / faster-whisper | local | transcription + word timings | **not installed here** (no filter, no package) | ❌ |
| Procedural synthesis (this repo) | local | free, deterministic, licence-free | not speech; music/ambience only | ✅ |

## Speech-to-text

| Option | Access | Notes | Verified here |
|---|---|---|---|
| faster-whisper / whisper.cpp | local | would produce `transcript.json` with word timings | ❌ not installed |
| hosted ASR APIs | hosted | per-minute billing | ❌ |

## What this means for the pipeline

1. **LOCAL** (default, shipped): vector sets + rig + procedural score + FFmpeg.
2. **HYBRID** (interface ready, adapters unimplemented): add a *photo/plate*
   provider for backgrounds and a *TTS* provider for narration. Code keeps the
   animation, camera and edit.
3. **PREMIUM**: add a video model for hero shots only, keep everything else
   procedural; cost is bounded per shot by `budget_usd`.

Rule that does not change with the mode: **no external call without explicit
authorisation and a budget, and no adapter that fakes its output.**
