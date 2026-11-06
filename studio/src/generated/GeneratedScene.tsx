import React from "react";
import { useCurrentFrame } from "remotion";
import type { GeneratedSet, SvgElement } from "./types";

/**
 * Renders a forged background from its layer spec. This is not a second engine:
 * it draws inside the same 1080x1920 SVG space as the hand-authored scenes, and
 * the same CameraRig / FilmFinish / actor stack wraps it.
 */
const prefixed = (value: string | undefined, prefix: string) =>
  (value ?? "").replace(/url\(#([^)]+)\)/g, (_match, id: string) => `url(#${prefix}-${id})`);

const element = (el: SvgElement, index: number, prefix: string, frame: number) => {
  const motion = el.motion;
  const drift = motion
    ? {
        x: motion.type === "drift" ? Math.sin(frame / (22 / Math.max(0.1, motion.speed))) * motion.amplitude : 0,
        y: motion.type === "float" ? Math.sin(frame / (18 / Math.max(0.1, motion.speed))) * motion.amplitude : 0,
      }
    : { x: 0, y: 0 };
  const transform = drift.x || drift.y ? `translate(${drift.x.toFixed(2)} ${drift.y.toFixed(2)})` : undefined;
  const common = {
    opacity: el.opacity,
    stroke: prefixed(el.stroke, prefix) || undefined,
    strokeWidth: el.strokeWidth,
    strokeLinecap: el.strokeLinecap,
  };
  const fill = prefixed(el.fill, prefix);
  let shape: React.ReactNode = null;
  switch (el.kind) {
    case "rect":
      shape = <rect x={el.x} y={el.y} width={el.w} height={el.h} rx={el.rx} fill={fill} {...common} />;
      break;
    case "circle":
      shape = <circle cx={el.cx} cy={el.cy} r={el.r} fill={fill} {...common} />;
      break;
    case "ellipse":
      shape = <ellipse cx={el.cx} cy={el.cy} rx={el.rx} ry={el.ry} fill={fill} {...common} />;
      break;
    case "path":
      shape = <path d={el.d} fill={fill || "none"} {...common} />;
      break;
    case "polygon":
      shape = <polygon points={(el.points ?? []).map((p) => p.join(",")).join(" ")} fill={fill} {...common} />;
      break;
    case "line":
      shape = <line x1={el.x1} y1={el.y1} x2={el.x2} y2={el.y2} {...common} />;
      break;
  }
  return (
    <g key={`${el.kind}-${index}`} transform={transform}>
      {shape}
    </g>
  );
};

export const GeneratedScene: React.FC<{ spec: GeneratedSet; progress: number }> = ({ spec, progress }) => {
  const frame = useCurrentFrame();
  const prefix = `gen-${(spec.subject ?? "set").replace(/[^a-z0-9]/gi, "")}`;
  return (
    <svg
      viewBox={(spec.viewBox ?? [0, 0, 1080, 1920]).join(" ")}
      preserveAspectRatio="xMidYMid slice"
      style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }}
    >
      <defs>
        {(spec.gradients ?? []).map((gradient) => (
          <linearGradient
            key={gradient.id}
            id={`${prefix}-${gradient.id}`}
            x1={gradient.x1 ?? 0}
            y1={gradient.y1 ?? 0}
            x2={gradient.x2 ?? 0}
            y2={gradient.y2 ?? 1}
          >
            {gradient.stops.map(([offset, color], i) => (
              <stop key={i} offset={`${offset * 100}%`} stopColor={color} />
            ))}
          </linearGradient>
        ))}
      </defs>
      <rect width="1080" height="1920" fill={spec.background ?? "#08060d"} />
      {(spec.layers ?? []).map((layer) => {
        const shift = (progress - 0.5) * (layer.depth ?? 0) * 42;
        return (
          <g
            key={layer.id}
            opacity={layer.opacity ?? 1}
            transform={`translate(${shift.toFixed(2)} ${(shift * 0.12).toFixed(2)})`}
            style={{ mixBlendMode: (layer.blend as React.CSSProperties["mixBlendMode"]) ?? "normal" }}
          >
            {layer.elements.map((el, i) => element(el, i, prefix, frame))}
          </g>
        );
      })}
    </svg>
  );
};
