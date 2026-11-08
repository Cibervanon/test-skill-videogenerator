# Final quality report

Output: `C:\Users\W10\Videos\SKILLS\projects\av_ultima_medida\output\final_video.mp4`
Result: **PASS**

| check | pass | value | detail |
|---|---|---|---|
| readable | ✅ | `mov,mp4,m4a,3gp,3g2,mj2` | ffprobe parsed the file |
| has_video | ✅ | `{'codec': 'h264', 'width': 1080, 'height': 1920, 'fps': 30.0, 'fps_avg': 30.0, 'pix_fmt': 'yuvj420p', 'frames': 672, 'aspect': 0.5625, 'orientation': 'vertical'}` | video stream present |
| has_audio | ✅ | `{'codec': 'aac', 'channels': 2, 'sample_rate': 48000, 'bitrate': 191340, 'duration': 22.4, 'streams': 1}` | audio stream present |
| duration | ✅ | `22.4` | delta 0.000s (tolerance 0.25s) |
| format | ✅ | `{'codec': 'h264', 'width': 1080, 'height': 1920, 'fps': 30.0, 'fps_avg': 30.0, 'pix_fmt': 'yuvj420p', 'frames': 672, 'aspect': 0.5625, 'orientation': 'vertical'}` | to spec |
| motion | ✅ | `4.034` | min 1.0 — guards against a slideshow of stills |
| black_frames | ✅ | `0.0` | max 0.02 — a black render must never pass |
| freeze | ✅ | `0.1042` | static-frame budget |
| audio_duration | ✅ | `22.4` | audio covers the picture; delta 0.000s |
| loudness | ✅ | `-17.0` | acceptable band -22.0..-11.0 dB (mean volume, not LUFS) |
| voice_in_delivery | ✅ | `0.9267` | voice present after removing the bed (signal correlation, not intelligibility); gain 2.105 |
| audio_activity | ✅ | `0.101` | the soundtrack is not near-silence |
| caption_plan | ✅ | `0.893` | computed from the cue plan (shot lines), not from OCR of the render |

## Motion by shot

| shot | start | seconds | mean energy | moving | low motion |
|---|---:|---:|---:|---:|---|
| S01 | 0.0 | 3.5 | 2.981 | 0.667 | no |
| S02 | 3.5 | 4.8 | 2.383 | 0.556 | no |
| S03 | 8.3 | 3.6 | 3.133 | 0.667 | no |
| S04 | 11.9 | 2.4 | 2.742 | 0.5 | no |
| S05 | 14.3 | 4.0 | 2.878 | 0.714 | no |
| S06 | 18.3 | 4.1 | 3.133 | 0.714 | no |

Low-motion shots: `[]`. A low reading is a diagnostic; a declared insert or held reaction is allowed to be quiet.

> heuristic gates calibrated on this engine's renders; not an aesthetic judgement
