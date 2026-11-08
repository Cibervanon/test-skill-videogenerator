# Final quality report

Output: `C:\Users\W10\Videos\SKILLS\projects\av_ultima_gota\output\final_video.mp4`
Result: **PASS**

| check | pass | value | detail |
|---|---|---|---|
| readable | ✅ | `mov,mp4,m4a,3gp,3g2,mj2` | ffprobe parsed the file |
| has_video | ✅ | `{'codec': 'h264', 'width': 1080, 'height': 1920, 'fps': 30.0, 'fps_avg': 30.0, 'pix_fmt': 'yuvj420p', 'frames': 789, 'aspect': 0.5625, 'orientation': 'vertical'}` | video stream present |
| has_audio | ✅ | `{'codec': 'aac', 'channels': 2, 'sample_rate': 48000, 'bitrate': 191352, 'duration': 26.3, 'streams': 1}` | audio stream present |
| duration | ✅ | `26.3` | delta 0.000s (tolerance 0.25s) |
| format | ✅ | `{'codec': 'h264', 'width': 1080, 'height': 1920, 'fps': 30.0, 'fps_avg': 30.0, 'pix_fmt': 'yuvj420p', 'frames': 789, 'aspect': 0.5625, 'orientation': 'vertical'}` | to spec |
| motion | ✅ | `5.226` | min 1.0 — guards against a slideshow of stills |
| black_frames | ✅ | `0.0` | max 0.02 — a black render must never pass |
| freeze | ✅ | `0.0152` | static-frame budget |
| audio_duration | ✅ | `26.3` | audio covers the picture; delta 0.000s |
| loudness | ✅ | `-14.1` | acceptable band -22.0..-11.0 dB (mean volume, not LUFS) |
| voice_in_delivery | ✅ | `0.7188` | voice present after removing the bed (signal correlation, not intelligibility); gain 2.1148 |
| audio_activity | ✅ | `0.19` | the soundtrack is not near-silence |
| caption_plan | ✅ | `0.897` | computed from the cue plan (shot lines), not from OCR of the render |

## Motion by shot

| shot | start | seconds | mean energy | moving | low motion |
|---|---:|---:|---:|---:|---|
| S01 | 0.0 | 3.8 | 4.901 | 0.714 | no |
| S02 | 3.8 | 4.0 | 2.544 | 0.571 | no |
| S03 | 7.8 | 4.0 | 3.71 | 0.714 | no |
| S04 | 11.8 | 3.8 | 2.985 | 0.571 | no |
| S05 | 15.6 | 4.2 | 3.522 | 0.714 | no |
| S06 | 19.8 | 2.7 | 2.574 | 0.5 | no |
| S07 | 22.5 | 3.8 | 2.939 | 0.571 | no |

Low-motion shots: `[]`. A low reading is a diagnostic; a declared insert or held reaction is allowed to be quiet.

> heuristic gates calibrated on this engine's renders; not an aesthetic judgement
