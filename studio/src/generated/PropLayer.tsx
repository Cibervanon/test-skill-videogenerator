import React from "react";
import type { GeneratedProp, PropPlacement, SvgElement } from "./types";

/**
 * Reusable generated props, placed in scene coordinates. Props are not added to
 * the character's closed hold enum: they compose with any actor and background.
 */
const propElement = (el: SvgElement, index: number) => {
  const common = {
    opacity: el.opacity,
    stroke: el.stroke,
    strokeWidth: el.strokeWidth,
    strokeLinecap: el.strokeLinecap,
  };
  switch (el.kind) {
    case "rect":
      return <rect key={index} x={el.x} y={el.y} width={el.w} height={el.h} rx={el.rx} fill={el.fill} {...common} />;
    case "circle":
      return <circle key={index} cx={el.cx} cy={el.cy} r={el.r} fill={el.fill} {...common} />;
    case "ellipse":
      return <ellipse key={index} cx={el.cx} cy={el.cy} rx={el.rx} ry={el.ry} fill={el.fill} {...common} />;
    case "path":
      return <path key={index} d={el.d} fill={el.fill ?? "none"} {...common} />;
    case "polygon":
      return <polygon key={index} points={(el.points ?? []).map((p) => p.join(",")).join(" ")} fill={el.fill} {...common} />;
    case "line":
      return (
        <line key={index} x1={el.x1} y1={el.y1} x2={el.x2} y2={el.y2} {...common} />
      );
    default:
      return null;
  }
};

export const PropGlyph: React.FC<{ spec: GeneratedProp; placement: PropPlacement }> = ({ spec, placement }) => {
  const pivot = spec.pivot ?? [100, 400];
  const scale = placement.scale ?? 1;
  return (
    <g
      transform={`translate(${placement.x} ${placement.y}) rotate(${placement.rotation ?? 0}) scale(${scale}) translate(${-pivot[0]} ${-pivot[1]})`}
      opacity={placement.opacity ?? 1}
    >
      {spec.elements.map((el, i) => propElement(el, i))}
    </g>
  );
};

export const PropLayer: React.FC<{
  props: PropPlacement[];
  specs: Record<string, GeneratedProp>;
  layer: "back" | "front";
}> = ({ props, specs, layer }) => (
  <svg
    viewBox="0 0 1080 1920"
    preserveAspectRatio="xMidYMid slice"
    style={{ position: "absolute", inset: 0, width: "100%", height: "100%", overflow: "visible" }}
  >
    {props
      .filter((prop) => (prop.layer ?? "back") === layer)
      .map((prop) => {
        const key = prop.id.replace(/^prop:/, "");
        const spec = specs[key];
        if (!spec) throw new Error(`Unknown generated prop "${prop.id}" — regenerate the asset registry`);
        return <PropGlyph key={prop.id} spec={spec} placement={prop} />;
      })}
  </svg>
);
