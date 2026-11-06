import React from "react";
import { useCurrentFrame } from "remotion";
import { Particles } from "../engine/Snow";
import { prng, hashString } from "../engine/math";

/**
 * Close-up background: out-of-focus night, bokeh lamps, cold haze.
 * The actor is rendered by the shot on top of this plate.
 */
export const FaceCloseup: React.FC<{ progress: number }> = ({ progress }) => {
  const frame = useCurrentFrame();
  const rnd = prng(hashString("bokeh"));
  const lights = new Array(14).fill(0).map(() => ({
    x: 40 + rnd() * 1000,
    y: 200 + rnd() * 1200,
    r: 24 + rnd() * 78,
    warm: rnd() > 0.35,
    a: 0.08 + rnd() * 0.18,
    ph: rnd() * 7,
  }));

  return (
    <>
      <svg viewBox="0 0 1080 1920" preserveAspectRatio="xMidYMid slice" style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }}>
        <defs>
          <linearGradient id="cuBg" x1="0" y1="0" x2="0.3" y2="1">
            <stop offset="0%" stopColor="#101633" />
            <stop offset="55%" stopColor="#232a52" />
            <stop offset="100%" stopColor="#3b2f45" />
          </linearGradient>
          <radialGradient id="cuKey" cx="0.3" cy="0.28" r="0.7">
            <stop offset="0%" stopColor="#ffd08a" stopOpacity="0.35" />
            <stop offset="100%" stopColor="#ffd08a" stopOpacity="0" />
          </radialGradient>
        </defs>
        <rect width="1080" height="1920" fill="url(#cuBg)" />
        {lights.map((l, i) => (
          <g key={i} opacity={l.a * (0.8 + 0.2 * Math.sin(frame / 26 + l.ph))}>
            <circle cx={l.x + progress * -16 * (i % 3)} cy={l.y} r={l.r} fill={l.warm ? "#ffc07a" : "#a9c2f0"} />
            <circle cx={l.x + progress * -16 * (i % 3)} cy={l.y} r={l.r * 1.7} fill={l.warm ? "#ffc07a" : "#a9c2f0"} opacity={0.35} />
          </g>
        ))}
        <rect width="1080" height="1920" fill="url(#cuKey)" />
        {/* soft architectural hint: window mullion out of focus */}
        <path d="M 120 0 L 120 1920 M 960 0 L 960 1920 M 0 260 L 1080 260" stroke="#0c1128" strokeWidth={46} opacity={0.35} filter="blur(6px)" />
      </svg>
      <div style={{ position: "absolute", inset: 0, backdropFilter: "blur(1.2px)" }} />
      <Particles count={26} seed="closeSnow" size={[3, 9]} speed={[0.3, 0.9]} opacity={0.35} />
    </>
  );
};
