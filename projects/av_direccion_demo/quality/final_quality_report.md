# Final quality report

Output: `C:\Users\W10\Videos\SKILLS\projects\av_direccion_demo\output\final_video.mp4`
Result: **PASS**

| check | pass | value | detail |
|---|---|---|---|
| readable | ✅ | `mov,mp4,m4a,3gp,3g2,mj2` | ffprobe parsed the file |
| has_video | ✅ | `{'codec': 'h264', 'width': 1080, 'height': 1920, 'fps': 30.0, 'fps_avg': 30.0, 'pix_fmt': 'yuvj420p', 'frames': 612, 'aspect': 0.5625, 'orientation': 'vertical'}` | video stream present |
| has_audio | ✅ | `{'codec': 'aac', 'channels': 2, 'sample_rate': 48000, 'bitrate': 192084, 'duration': 20.433, 'streams': 1}` | audio stream present |
| duration | ✅ | `20.433` | delta 0.003s (tolerance 0.25s) |
| format | ✅ | `{'codec': 'h264', 'width': 1080, 'height': 1920, 'fps': 30.0, 'fps_avg': 30.0, 'pix_fmt': 'yuvj420p', 'frames': 612, 'aspect': 0.5625, 'orientation': 'vertical'}` | to spec |
| motion | ✅ | `8.858` | min 1.0 — guards against a slideshow of stills |
| black_frames | ✅ | `0.0` | max 0.02 — a black render must never pass |
| freeze | ✅ | `0.0489` | static-frame budget |
| audio_duration | ✅ | `20.433` | audio covers the picture; delta 0.000s |
| loudness | ✅ | `-17.2` | acceptable band -22.0..-11.0 dB (mean volume, not LUFS) |
| voice_in_delivery | ✅ | `0.9273` | voice present after removing the bed (signal correlation, not intelligibility); gain 2.0707 |
| audio_activity | ✅ | `0.173` | the soundtrack is not near-silence |
| caption_plan | ✅ | `0.883` | computed from the cue plan (shot lines), not from OCR of the render |

## Motion by shot

| shot | start | seconds | mean energy | moving | low motion |
|---|---:|---:|---:|---:|---|
| S01 | 0.0 | 3.167 | 2.438 | 0.8 | no |
| S02 | 3.167 | 3.8 | 4.334 | 0.571 | no |
| S03 | 6.967 | 3.8 | 4.337 | 0.857 | no |
| S04 | 10.767 | 2.4 | 2.743 | 0.5 | no |
| S05 | 13.167 | 3.467 | 4.284 | 0.833 | no |
| S06 | 16.633 | 3.8 | 7.356 | 0.857 | no |

Low-motion shots: `[]`. A low reading is a diagnostic; a declared insert or held reaction is allowed to be quiet.

> heuristic gates calibrated on this engine's renders; not an aesthetic judgement
