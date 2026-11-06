import React from "react";
import { AbsoluteFill, useCurrentFrame } from "remotion";
import { prng, hashString } from "./math";

/**
 * Film finish stack: paper grain, warm key / cool fill grade, vignette,
 * halation. Overlay-only by design: it never paints an opaque base, so it can
 * sit on top of a composition without hiding it.
 *
 * The grain is a single static SVG turbulence image that is *displaced* every
 * frame instead of being regenerated, which keeps rendering fast and
 * deterministic.
 */
const grainSvg = (seed: number) =>
  `<svg xmlns="http://www.w3.org/2000/svg" width="360" height="640">
    <filter id="g" x="0" y="0">
      <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="3" seed="${seed}" stitchTiles="stitch"/>
      <feColorMatrix type="saturate" values="0"/>
    </filter>
    <rect width="360" height="640" filter="url(#g)" opacity="0.55"/>
  </svg>`;

const GRAIN_URI = `url("data:image/svg+xml;utf8,${encodeURIComponent(grainSvg(11))}")`;

export const FilmFinish: React.FC<{
  /** 0..1 strength of the grain (references sit around 0.10-0.16). */
  grain?: number;
  vignette?: number;
  warmth?: string;
}> = ({ grain = 0.13, vignette = 0.55, warmth = "rgba(255,178,93,0.05)" }) => {
  const frame = useCurrentFrame();
  const rnd = prng(hashString("grain") + frame);
  const gx = Math.floor(rnd() * 180);
  const gy = Math.floor(rnd() * 320);

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <AbsoluteFill
        style={{
          background: `radial-gradient(120% 80% at 50% 35%, ${warmth} 0%, rgba(20,14,30,0) 58%)`,
          mixBlendMode: "screen",
        }}
      />
      <AbsoluteFill
        style={{
          background: `radial-gradient(135% 95% at 50% 52%, rgba(0,0,0,0) 40%, rgba(8,5,14,${vignette}) 100%)`,
        }}
      />
      <AbsoluteFill
        style={{
          backgroundImage: GRAIN_URI,
          backgroundRepeat: "repeat",
          backgroundPosition: `${gx}px ${gy}px`,
          opacity: grain,
          mixBlendMode: "overlay",
        }}
      />
      <AbsoluteFill
        style={{
          background: "radial-gradient(62% 46% at 50% 32%, rgba(255,196,128,0.10), rgba(0,0,0,0) 72%)",
          mixBlendMode: "screen",
        }}
      />
    </AbsoluteFill>
  );
};
