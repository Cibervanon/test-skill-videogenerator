import React from "react";
import { useCurrentFrame } from "remotion";
import { prng, hashString } from "./math";

/**
 * Snow / dust particles. Positions come from a seeded PRNG so every render of
 * the same frame is identical, and motion is a pure function of the frame.
 */
export const Particles: React.FC<{
  count?: number;
  seed?: string;
  size?: [number, number];
  speed?: [number, number];
  drift?: number;
  opacity?: number;
  color?: string;
  /** 0..1 how far down the particles start within the frame height. */
  area?: number;
}> = ({
  count = 70,
  seed = "snow",
  size = [2, 7],
  speed = [0.4, 1.5],
  drift = 22,
  opacity = 0.85,
  color = "#ffffff",
  area = 1,
}) => {
  const frame = useCurrentFrame();
  const rnd = prng(hashString(seed));
  const items = new Array(count).fill(0).map((_, i) => {
    const x = rnd() * 100;
    const start = rnd() * 100;
    const s = size[0] + rnd() * (size[1] - size[0]);
    const v = speed[0] + rnd() * (speed[1] - speed[0]);
    const sway = (rnd() - 0.5) * drift;
    const alpha = 0.35 + rnd() * 0.65;
    const blur = rnd() > 0.82 ? 2.2 : 0;
    const y = ((start + (frame / 30) * v * 6) % (100 * area)) * (1 / area);
    return (
      <div
        key={i}
        style={{
          position: "absolute",
          left: `${x + Math.sin((frame / 42) * v + i) * (sway / 10)}%`,
          top: `${y}%`,
          width: s,
          height: s,
          borderRadius: "50%",
          background: color,
          opacity: alpha * opacity,
          filter: blur ? `blur(${blur}px)` : undefined,
        }}
      />
    );
  });
  return <div style={{ position: "absolute", inset: 0, overflow: "hidden", pointerEvents: "none" }}>{items}</div>;
};
