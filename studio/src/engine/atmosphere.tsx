import React from "react";

/**
 * Light and grounding primitives. A set without cast shadows floats; a set
 * without a light shaft looks like a diagram. These are the cheapest way to
 * make vector scenery read as a lit photograph of a place.
 */

export const LightShaft: React.FC<{
  id: string;
  /** Quad corners, in viewBox units. */
  d: string;
  color: string;
  opacity?: number;
  blur?: number;
}> = ({ id, d, color, opacity = 0.22, blur = 18 }) => (
  <>
    <defs>
      <linearGradient id={id} x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stopColor={color} stopOpacity={opacity} />
        <stop offset="70%" stopColor={color} stopOpacity={opacity * 0.35} />
        <stop offset="100%" stopColor={color} stopOpacity={0} />
      </linearGradient>
      <filter id={`${id}-blur`} x="-20%" y="-20%" width="140%" height="140%">
        <feGaussianBlur stdDeviation={blur} />
      </filter>
    </defs>
    <path d={d} fill={`url(#${id})`} filter={`url(#${id}-blur)`} style={{ mixBlendMode: "screen" }} />
  </>
);

export const Glow: React.FC<{ id: string; cx: number; cy: number; r: number; color: string; opacity?: number }> = ({
  id,
  cx,
  cy,
  r,
  color,
  opacity = 0.5,
}) => (
  <>
    <defs>
      <radialGradient id={id}>
        <stop offset="0%" stopColor={color} stopOpacity={opacity} />
        <stop offset="45%" stopColor={color} stopOpacity={opacity * 0.35} />
        <stop offset="100%" stopColor={color} stopOpacity={0} />
      </radialGradient>
    </defs>
    <circle cx={cx} cy={cy} r={r} fill={`url(#${id})`} style={{ mixBlendMode: "screen" }} />
  </>
);

export const CastShadow: React.FC<{
  cx: number;
  cy: number;
  rx: number;
  ry: number;
  rotate?: number;
  opacity?: number;
  color?: string;
}> = ({ cx, cy, rx, ry, rotate = 0, opacity = 0.22, color = "#1a1220" }) => (
  <ellipse cx={cx} cy={cy} rx={rx} ry={ry} fill={color} opacity={opacity} transform={`rotate(${rotate} ${cx} ${cy})`} filter="url(#softBlur)" />
);

export const SoftBlurDefs: React.FC<{ id?: string }> = ({ id = "softBlur" }) => (
  <defs>
    <filter id={id} x="-30%" y="-30%" width="160%" height="160%">
      <feGaussianBlur stdDeviation={9} />
    </filter>
  </defs>
);

export const FogBand: React.FC<{
  id: string;
  y: number;
  height: number;
  color: string;
  opacity?: number;
  width?: number;
}> = ({ id, y, height, color, opacity = 0.3, width = 1080 }) => (
  <>
    <defs>
      <linearGradient id={id} x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stopColor={color} stopOpacity={0} />
        <stop offset="45%" stopColor={color} stopOpacity={opacity} />
        <stop offset="100%" stopColor={color} stopOpacity={0} />
      </linearGradient>
    </defs>
    <rect x={0} y={y} width={width} height={height} fill={`url(#${id})`} />
  </>
);

/**
 * The contrast pass, borrowed from the external repository's `LightVeil` (MIT):
 * a dark veil over the whole set with soft holes where the light falls. Mid-tones
 * sink, the pools around lamps and windows glow, and the characters drawn after
 * it keep full brightness. This is what makes a flat SVG room read as lit.
 */
export const LightVeil: React.FC<{
  id: string;
  /** [x, y, radius] of each light, in viewBox units. */
  lights: [number, number, number][];
  opacity?: number;
  color?: string;
}> = ({ id, lights, opacity = 0.42, color = "#07040c" }) => (
  <g>
    <defs>
      <radialGradient id={`${id}-hole`}>
        <stop offset="0%" stopColor="#000" stopOpacity={1} />
        <stop offset="45%" stopColor="#000" stopOpacity={0.72} />
        <stop offset="100%" stopColor="#000" stopOpacity={0} />
      </radialGradient>
      <mask id={`${id}-mask`} maskUnits="userSpaceOnUse" x={-1200} y={-1200} width={4000} height={4000}>
        <rect x={-1200} y={-1200} width={4000} height={4000} fill="#fff" />
        {lights.map(([x, y, r], i) => (
          <circle key={i} cx={x} cy={y} r={r} fill={`url(#${id}-hole)`} />
        ))}
      </mask>
    </defs>
    <rect x={-1200} y={-1200} width={4000} height={4000} fill={color} opacity={opacity} mask={`url(#${id}-mask)`} />
  </g>
);

/** A soft cone of light from a lamp or a window, fading downward. */
export const Cone: React.FC<{ id: string; d: string; color?: string; opacity?: number }> = ({
  id,
  d,
  color = "#ffd7a0",
  opacity = 0.4,
}) => (
  <>
    <defs>
      <linearGradient id={`${id}-cone`} x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stopColor={color} stopOpacity={opacity} />
        <stop offset="100%" stopColor={color} stopOpacity={0} />
      </linearGradient>
    </defs>
    <path d={d} fill={`url(#${id}-cone)`} style={{ mixBlendMode: "screen" }} />
  </>
);

/** Volumetric dust inside a light shaft: seeded dots, deterministic motion. */
export const DustMotes: React.FC<{
  count?: number;
  seed?: number;
  color?: string;
  frame: number;
  area?: { x: number; y: number; w: number; h: number };
}> = ({ count = 40, seed = 3, color = "#ffe6b8", frame, area = { x: 0, y: 0, w: 1080, h: 1920 } }) => {
  let s = seed >>> 0;
  const rnd = () => {
    s = (s * 1664525 + 1013904223) >>> 0;
    return s / 4294967296;
  };
  const motes = new Array(count).fill(0).map((_, i) => {
    const x = area.x + rnd() * area.w;
    const y = area.y + rnd() * area.h;
    const r = 1 + rnd() * 2.6;
    const sp = 0.15 + rnd() * 0.5;
    const ph = rnd() * 6.28;
    return (
      <circle
        key={i}
        cx={x + Math.sin(frame / (34 * sp) + ph) * 10}
        cy={y - ((frame * sp * 0.5) % 260)}
        r={r}
        fill={color}
        opacity={0.12 + 0.2 * Math.abs(Math.sin(frame / 40 + ph))}
      />
    );
  });
  return <g style={{ mixBlendMode: "screen" }}>{motes}</g>;
};
