import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { easeInOutCubic, easeOutCubic, clamp } from "./math";

export type CameraMove =
  | "static"
  | "drift"
  | "dollyIn"
  | "dollyOut"
  | "panLeft"
  | "panRight"
  | "tiltUp"
  | "craneDown"
  | "pushInSlow"
  | "trackLeft"
  | "trackRight"
  | "reframe";

type Transform = { scale: number; x: number; y: number; rotate: number };

/**
 * Camera vocabulary. Each move is a *narrative* intent expressed as a
 * transform curve, never a random wobble:
 *  - dollyIn / pushInSlow : building realisation, intimacy
 *  - dollyOut             : loneliness, reveal of context
 *  - panLeft / panRight   : following a walk, scanning a space
 *  - trackLeft / trackRight: following a subject without losing the space
 *  - reframe              : moving the subject inside a held composition
 *  - tiltUp / craneDown   : scale, arrival
 *  - drift                : hold with life, never a frozen frame
 */
const transformFor = (move: CameraMove, p: number, frame: number): Transform => {
  const hand = Math.sin(frame / 47) * 3.2 + Math.sin(frame / 23 + 1.7) * 1.4;
  switch (move) {
    case "dollyIn":
      return { scale: 1.02 + easeInOutCubic(p) * 0.14, x: 0, y: -easeInOutCubic(p) * 1.2, rotate: 0 };
    case "pushInSlow":
      return { scale: 1.0 + easeOutCubic(p) * 0.18, x: 0, y: -easeOutCubic(p) * 2.2, rotate: -0.2 };
    case "dollyOut":
      return { scale: 1.18 - easeInOutCubic(p) * 0.15, x: 0, y: easeInOutCubic(p) * 0.8, rotate: 0 };
    // The pan must never outrun the scale: translate happens after scale, so a
    // 7% shift against a 1.1x zoom (5% of overscan per side) left a 2% black
    // strip on the trailing edge in the first v3 render.
    case "panLeft":
      return { scale: 1.16, x: easeInOutCubic(p) * 5.5, y: 0.4, rotate: 0 };
    case "panRight":
      return { scale: 1.16, x: -easeInOutCubic(p) * 5.5, y: 0.4, rotate: 0 };
    case "trackLeft":
      return { scale: 1.2, x: easeInOutCubic(p) * 7, y: 0.6, rotate: 0 };
    case "trackRight":
      return { scale: 1.2, x: -easeInOutCubic(p) * 7, y: 0.6, rotate: 0 };
    case "reframe":
      return { scale: 1.12, x: (easeInOutCubic(p) - 0.5) * 5.5, y: 0.4, rotate: 0 };
    case "tiltUp":
      return { scale: 1.06, x: 0, y: easeInOutCubic(p) * 3, rotate: 0 };
    case "craneDown":
      return { scale: 1.08 + p * 0.04, x: 0, y: -2 + easeInOutCubic(p) * 2.4, rotate: 0 };
    case "drift":
      return { scale: 1.03, x: hand * 0.06, y: hand * 0.045, rotate: 0 };
    case "static":
    default:
      return { scale: 1, x: 0, y: 0, rotate: 0 };
  }
};

export const CameraRig: React.FC<{
  move: CameraMove;
  /** 0..1 progress override; defaults to shot progress. */
  progress?: number;
  /** Extra vertical framing offset in % of frame height. */
  offsetY?: number;
  children: React.ReactNode;
}> = ({ move, progress, offsetY = 0, children }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const p = clamp(progress ?? frame / Math.max(1, durationInFrames - 1));
  const t = transformFor(move, p, frame);

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        overflow: "hidden",
        transform: `translate3d(${t.x}%, ${t.y + offsetY}%, 0) scale(${t.scale}) rotate(${t.rotate}deg)`,
        transformOrigin: "50% 52%",
        willChange: "transform",
      }}
    >
      {children}
    </div>
  );
};

/**
 * SVG parallax group. Must be a `<g>`, not a `<div>`: inside an `<svg>` element
 * an HTML wrapper is silently dropped by the browser, which is exactly how the
 * first version of this engine lost every background layer.
 */
export const ParallaxGroup: React.FC<{
  depth: number;
  progress: number;
  children: React.ReactNode;
}> = ({ depth, progress, children }) => {
  const shiftX = (progress - 0.5) * depth * 90;
  const shiftY = shiftX * 0.18;
  const scale = 1 + depth * 0.06;
  return (
    <g
      transform={`translate(${shiftX.toFixed(2)} ${shiftY.toFixed(2)}) translate(540 960) scale(${scale.toFixed(4)}) translate(-540 -960)`}
    >
      {children}
    </g>
  );
};
