import { Config } from "@remotion/cli/config";

// LOCAL mode: deterministic, CPU-only rendering. Angle is used because the
// compositions are entirely SVG/CSS (no WebGL), which is the most stable
// option on machines without a dedicated GPU.
Config.setVideoImageFormat("jpeg");
Config.setJpegQuality(95);
Config.setCodec("h264");
Config.setPixelFormat("yuv420p");
Config.setCrf(16);
Config.setConcurrency(4);
Config.setOverwriteOutput(true);
