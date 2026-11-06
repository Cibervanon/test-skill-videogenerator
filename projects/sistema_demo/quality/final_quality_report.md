# Final quality report

Output: `C:\Users\W10\Videos\SKILLS\projects\sistema_demo\output\final_video.mp4`
Result: **PASS**

| check | pass | value | detail |
|---|---|---|---|
| readable | ✅ | `mov,mp4,m4a,3gp,3g2,mj2` | ffprobe parsed the file |
| has_video | ✅ | `{'codec': 'h264', 'width': 1080, 'height': 1920, 'fps': 30.0, 'fps_avg': 30.0, 'pix_fmt': 'yuvj420p', 'frames': 602, 'aspect': 0.5625, 'orientation': 'vertical'}` | video stream present |
| has_audio | ✅ | `{'codec': 'aac', 'channels': 2, 'sample_rate': 48000, 'bitrate': 190419, 'streams': 1}` | audio stream present |
| duration | ✅ | `20.067` | delta 0.003s (tolerance 0.25s) |
| format | ✅ | `{'codec': 'h264', 'width': 1080, 'height': 1920, 'fps': 30.0, 'fps_avg': 30.0, 'pix_fmt': 'yuvj420p', 'frames': 602, 'aspect': 0.5625, 'orientation': 'vertical'}` | to spec |
| motion | ✅ | `8.769` | min 1.0 — guards against a slideshow of stills |
| black_frames | ✅ | `0.0` | max 0.02 — a black render must never pass |
| freeze | ✅ | `0.0` | static-frame budget |
| loudness | ✅ | `-12.8` | acceptable band -22.0..-11.0 dB (mean volume, not LUFS) |
| audio_activity | ✅ | `0.275` | the soundtrack is not near-silence |
| caption_plan | ✅ | `1.0` | computed from the cue plan (shot lines), not from OCR of the render |

> heuristic gates calibrated on this engine's renders; not an aesthetic judgement
