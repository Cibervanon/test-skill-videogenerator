import React from "react";

/**
 * Procedural material patterns.
 *
 * Every set in the reference is *surfaced*: stone reads as blocks, wood as
 * planks, roofs as shingles, fabric as pattern. Flat fills are what make a set
 * look like a diagram instead of an illustration, so these patterns are the
 * single highest-leverage change available to a code-only renderer.
 *
 * All patterns are pure SVG `<pattern>` definitions with a caller-supplied id
 * prefix, because the same scene can be mounted twice during a crossfade and
 * duplicate ids would silently resolve to the first definition.
 */

type P = { id: string; base: string; line: string; accent?: string };

export const StonePattern: React.FC<P & { unit?: number }> = ({ id, base, line, accent, unit = 46 }) => (
  <pattern id={id} patternUnits="userSpaceOnUse" width={unit * 2} height={unit}>
    <rect width={unit * 2} height={unit} fill={base} />
    {[0, 1].map((row) =>
      [0, 1, 2].map((col) => {
        const w = unit * 0.92;
        const h = unit * 0.86;
        const x = col * unit - (row % 2 ? unit * 0.5 : 0);
        const y = row * unit + unit * 0.07;
        return (
          <g key={`${row}-${col}`}>
            <rect x={x} y={y} width={w} height={h} fill={accent ?? base} opacity={0.55 + ((row + col) % 3) * 0.12} rx={2} />
            <rect x={x} y={y} width={w} height={h} fill="none" stroke={line} strokeWidth={1.6} opacity={0.55} rx={2} />
          </g>
        );
      })
    )}
  </pattern>
);

export const PlankPattern: React.FC<P & { unit?: number; vertical?: boolean }> = ({
  id,
  base,
  line,
  accent,
  unit = 26,
  vertical = true,
}) => (
  <pattern
    id={id}
    patternUnits="userSpaceOnUse"
    width={vertical ? unit : unit * 3}
    height={vertical ? unit * 3 : unit}
    patternTransform={vertical ? undefined : "rotate(0)"}
  >
    <rect width={vertical ? unit : unit * 3} height={vertical ? unit * 3 : unit} fill={base} />
    {(vertical ? [0, 1, 2, 3] : [0, 1, 2, 3]).map((i) => (
      <g key={i}>
        <rect
          x={vertical ? i * unit : 0}
          y={vertical ? 0 : i * unit}
          width={vertical ? unit - 1 : unit * 3}
          height={vertical ? unit * 3 : unit - 1}
          fill={accent ?? base}
          opacity={0.25 + (i % 3) * 0.14}
        />
        <line
          x1={vertical ? i * unit : 0}
          y1={vertical ? 0 : i * unit}
          x2={vertical ? i * unit : unit * 3}
          y2={vertical ? unit * 3 : i * unit}
          stroke={line}
          strokeWidth={1.4}
          opacity={0.45}
        />
      </g>
    ))}
    {/* grain: a few long, low-contrast curves */}
    <path d={`M 4 8 q ${unit * 0.5} 6 ${unit - 6} -2`} stroke={line} strokeWidth={1} fill="none" opacity={0.16} />
    <path d={`M 2 ${unit * 1.6} q ${unit * 0.6} -5 ${unit - 4} 3`} stroke={line} strokeWidth={1} fill="none" opacity={0.12} />
  </pattern>
);

export const ShinglePattern: React.FC<P & { unit?: number }> = ({ id, base, line, accent, unit = 22 }) => (
  <pattern id={id} patternUnits="userSpaceOnUse" width={unit} height={unit}>
    <rect width={unit} height={unit} fill={base} />
    {[0, 1].map((row) => (
      <g key={row}>
        <path
          d={`M 0 ${row * (unit / 2) + 2} q ${unit / 4} ${unit / 2.4} ${unit / 2} 0 q ${unit / 4} ${unit / 2.4} ${unit / 2} 0`}
          fill={accent ?? base}
          stroke={line}
          strokeWidth={1.2}
          opacity={0.85}
        />
      </g>
    ))}
  </pattern>
);

export const SnowPattern: React.FC<P & { unit?: number }> = ({ id, base, line, accent, unit = 40 }) => (
  <pattern id={id} patternUnits="userSpaceOnUse" width={unit} height={unit}>
    <rect width={unit} height={unit} fill={base} />
    <circle cx={unit * 0.2} cy={unit * 0.3} r={1.4} fill={line} opacity={0.22} />
    <circle cx={unit * 0.62} cy={unit * 0.18} r={1} fill={line} opacity={0.18} />
    <circle cx={unit * 0.8} cy={unit * 0.66} r={1.6} fill={line} opacity={0.16} />
    <circle cx={unit * 0.36} cy={unit * 0.78} r={1.1} fill={line} opacity={0.2} />
    <path d={`M ${unit * 0.05} ${unit * 0.55} q ${unit * 0.18} -3 ${unit * 0.3} 0`} stroke={accent ?? line} strokeWidth={1.4} fill="none" opacity={0.18} />
    <path d={`M ${unit * 0.55} ${unit * 0.9} q ${unit * 0.2} -3 ${unit * 0.34} 0`} stroke={accent ?? line} strokeWidth={1.2} fill="none" opacity={0.14} />
  </pattern>
);

export const HatchPattern: React.FC<P & { unit?: number; angle?: number }> = ({ id, base, line, unit = 14, angle = 28 }) => (
  <pattern id={id} patternUnits="userSpaceOnUse" width={unit} height={unit} patternTransform={`rotate(${angle})`}>
    <rect width={unit} height={unit} fill={base} fillOpacity={0} />
    <line x1={0} y1={0} x2={0} y2={unit} stroke={line} strokeWidth={1} opacity={0.16} />
  </pattern>
);

export const CarpetPattern: React.FC<P & { unit?: number }> = ({ id, base, line, accent, unit = 64 }) => (
  <pattern id={id} patternUnits="userSpaceOnUse" width={unit} height={unit}>
    <rect width={unit} height={unit} fill={base} />
    <path d={`M ${unit / 2} 8 L ${unit - 8} ${unit / 2} L ${unit / 2} ${unit - 8} L 8 ${unit / 2} Z`} fill="none" stroke={accent ?? line} strokeWidth={2} opacity={0.55} />
    <path d={`M ${unit / 2} ${unit * 0.28} L ${unit * 0.72} ${unit / 2} L ${unit / 2} ${unit * 0.72} L ${unit * 0.28} ${unit / 2} Z`} fill={accent ?? line} opacity={0.22} />
    <circle cx={unit / 2} cy={unit / 2} r={2.4} fill={line} opacity={0.5} />
    <circle cx={2} cy={2} r={1.6} fill={line} opacity={0.35} />
    <circle cx={unit - 2} cy={unit - 2} r={1.6} fill={line} opacity={0.35} />
  </pattern>
);

export const WallpaperPattern: React.FC<P & { unit?: number }> = ({ id, base, line, accent, unit = 72 }) => (
  <pattern id={id} patternUnits="userSpaceOnUse" width={unit} height={unit}>
    <rect width={unit} height={unit} fill={base} />
    <path
      d={`M ${unit / 2} ${unit * 0.18} q ${unit * 0.14} ${unit * 0.16} 0 ${unit * 0.3} q ${-unit * 0.14} ${unit * 0.14} 0 ${unit * 0.3}`}
      stroke={line}
      strokeWidth={2}
      fill="none"
      opacity={0.4}
    />
    <circle cx={unit / 2} cy={unit * 0.16} r={3} fill={accent ?? line} opacity={0.4} />
    <circle cx={0} cy={unit / 2} r={2} fill={line} opacity={0.25} />
    <circle cx={unit} cy={unit / 2} r={2} fill={line} opacity={0.25} />
  </pattern>
);

export const FrostPattern: React.FC<P & { unit?: number }> = ({ id, base, line, unit = 30 }) => (
  <pattern id={id} patternUnits="userSpaceOnUse" width={unit} height={unit}>
    <rect width={unit} height={unit} fill={base} />
    {[0, 1, 2].map((i) => (
      <path
        key={i}
        d={`M ${i * 10 + 2} ${unit} l ${4 + i} ${-unit * 0.5} M ${i * 10 + 6} ${unit} l ${-2} ${-unit * 0.3}`}
        stroke={line}
        strokeWidth={1.1}
        opacity={0.35}
      />
    ))}
  </pattern>
);

/**
 * Collects the material patterns of a scene, prefixed so ids never collide.
 * Returns a fragment, not a nested <defs>: pattern definitions are inert until
 * referenced, and nesting <defs> inside <defs> is legal but poorly supported.
 */
export const MaterialDefs: React.FC<{ prefix: string; palette: Record<string, string> }> = ({ prefix, palette }) => (
  <>
    <StonePattern id={`${prefix}-stone`} base={palette.stone} line={palette.mortar} accent={palette.stoneLight} />
    <PlankPattern id={`${prefix}-plank`} base={palette.wood} line={palette.woodLine} accent={palette.woodLight} />
    <ShinglePattern id={`${prefix}-shingle`} base={palette.roof} line={palette.roofLine} accent={palette.roofLight} />
    <SnowPattern id={`${prefix}-snow`} base={palette.snow} line={palette.snowLine} accent={palette.snowAccent} />
    <HatchPattern id={`${prefix}-hatch`} base={palette.snow} line={palette.ink} />
    <CarpetPattern id={`${prefix}-carpet`} base={palette.carpet} line={palette.carpetLine} accent={palette.carpetAccent} />
    <WallpaperPattern id={`${prefix}-wallpaper`} base={palette.wall} line={palette.wallLine} accent={palette.wallAccent} />
    <FrostPattern id={`${prefix}-frost`} base="transparent" line={palette.frost} />
  </>
);
