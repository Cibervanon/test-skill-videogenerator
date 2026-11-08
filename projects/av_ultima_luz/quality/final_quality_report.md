# Final quality report

Output: `C:\Users\W10\Videos\SKILLS\projects\av_ultima_luz\output\final_video.mp4`
Result: **PASS**

| check | pass | value | detail |
|---|---|---|---|
| readable | ✅ | `mov,mp4,m4a,3gp,3g2,mj2` | ffprobe parsed the file |
| has_video | ✅ | `{'codec': 'h264', 'width': 1080, 'height': 1920, 'fps': 30.0, 'fps_avg': 30.0, 'pix_fmt': 'yuvj420p', 'frames': 639, 'aspect': 0.5625, 'orientation': 'vertical'}` | video stream present |
| has_audio | ✅ | `{'codec': 'aac', 'channels': 2, 'sample_rate': 48000, 'bitrate': 191229, 'duration': 21.3, 'streams': 1}` | audio stream present |
| duration | ✅ | `21.3` | delta 0.000s (tolerance 0.25s) |
| format | ✅ | `{'codec': 'h264', 'width': 1080, 'height': 1920, 'fps': 30.0, 'fps_avg': 30.0, 'pix_fmt': 'yuvj420p', 'frames': 639, 'aspect': 0.5625, 'orientation': 'vertical'}` | to spec |
| motion | ✅ | `5.912` | min 1.0 — guards against a slideshow of stills |
| black_frames | ✅ | `0.0` | max 0.02 — a black render must never pass |
| freeze | ✅ | `0.1596` | static-frame budget |
| audio_duration | ✅ | `21.3` | audio covers the picture; delta 0.000s |
| loudness | ✅ | `-13.6` | acceptable band -22.0..-11.0 dB (mean volume, not LUFS) |
| voice_in_delivery | ✅ | `0.7179` | voice present after removing the bed (signal correlation, not intelligibility); gain 1.5771 |
| audio_activity | ✅ | `0.282` | the soundtrack is not near-silence |
| caption_plan | ✅ | `0.873` | computed from the cue plan (shot lines), not from OCR of the render |

## Motion by shot

| shot | start | seconds | mean energy | moving | low motion |
|---|---:|---:|---:|---:|---|
| S01 | 0.0 | 3.6 | 2.576 | 0.667 | no |
| S02 | 3.6 | 4.0 | 4.833 | 0.857 | no |
| S03 | 7.6 | 3.8 | 3.383 | 0.571 | no |
| S04 | 11.4 | 2.7 | 2.038 | 0.25 | no |
| S05 | 14.1 | 3.8 | 3.34 | 0.714 | no |
| S06 | 17.9 | 3.4 | 3.176 | 0.667 | no |

Low-motion shots: `[]`. A low reading is a diagnostic; a declared insert or held reaction is allowed to be quiet.

> heuristic gates calibrated on this engine's renders; not an aesthetic judgement
