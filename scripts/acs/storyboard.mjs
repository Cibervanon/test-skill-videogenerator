// Storyboard stills: one still per shot at its key frame, bundled once.
// Adapted from the MIT-licensed what-if-animation `scripts/stills.mjs`.
//
//   node scripts/acs/storyboard.mjs <frames.json> <outDir> [--scale 0.45]
//
// frames.json: { "entry": "src/index.ts", "composition": "CinematicDemo",
//                "frames": [ { "id": "S01", "frame": 132 }, ... ] }
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";

const require = createRequire(path.resolve("package.json"));
const { bundle } = require("@remotion/bundler");
const { renderStill, selectComposition } = require("@remotion/renderer");

const [specPath, outDir, ...rest] = process.argv.slice(2);
const scaleAt = rest.indexOf("--scale");
const scale = scaleAt >= 0 ? Number(rest[scaleAt + 1]) : 0.45;
const spec = JSON.parse(fs.readFileSync(path.resolve(specPath), "utf8"));

fs.mkdirSync(path.resolve(outDir), { recursive: true });
const serveUrl = await bundle({ entryPoint: path.resolve(spec.entry || "src/index.ts") });
const composition = await selectComposition({ serveUrl, id: spec.composition || "CinematicDemo" });

for (const shot of spec.frames) {
  const output = path.join(path.resolve(outDir), `${shot.id}.png`);
  await renderStill({
    serveUrl,
    composition,
    frame: Math.min(shot.frame, composition.durationInFrames - 1),
    output,
    overwrite: true,
    scale,
  });
  process.stdout.write(`${shot.id} `);
}
console.log("\ndone");
