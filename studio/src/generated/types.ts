import type { OverlaySpec } from "../motion-graphics";

export type SvgElement = {
  kind: "rect" | "circle" | "ellipse" | "path" | "polygon" | "line";
  x?: number;
  y?: number;
  w?: number;
  h?: number;
  cx?: number;
  cy?: number;
  r?: number;
  rx?: number;
  ry?: number;
  d?: string;
  points?: number[][];
  x1?: number;
  y1?: number;
  x2?: number;
  y2?: number;
  fill?: string;
  stroke?: string;
  strokeWidth?: number;
  strokeLinecap?: "butt" | "round" | "square";
  opacity?: number;
  motion?: { type: "float" | "drift"; amplitude: number; speed: number };
};

export type SceneLayer = {
  id: "background" | "midground" | "foreground" | "lighting" | "atmosphere";
  depth?: number;
  opacity?: number;
  blend?: string;
  elements: SvgElement[];
};

export type GeneratedSet = {
  renderer: "generated-set-v1";
  viewBox: [number, number, number, number];
  background?: string;
  gradients?: {
    id: string;
    x1?: number;
    y1?: number;
    x2?: number;
    y2?: number;
    stops: [number, string][];
  }[];
  layers: SceneLayer[];
  subject?: string;
};

export type GeneratedProp = {
  renderer: "generated-prop-v1";
  viewBox: [number, number, number, number];
  pivot?: [number, number];
  elements: SvgElement[];
  subject?: string;
};

export type PropPlacement = {
  id: string;
  x: number;
  y: number;
  scale?: number;
  rotation?: number;
  opacity?: number;
  layer?: "back" | "front";
};

export type GeneratedExpression = {
  name: string;
  values: {
    brow?: number;
    mouth?: number;
    headTilt?: number;
    yaw?: number;
    blink?: number;
  };
  character_ref?: string | null;
};

export type GeneratedGraphic = OverlaySpec;
