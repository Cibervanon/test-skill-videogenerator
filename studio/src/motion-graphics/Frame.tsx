import React from "react";
import { useCurrentFrame } from "remotion";
import { clamp, easeOutCubic } from "../engine/math";
import { useStyle } from "../engine/styles";
import type { Box, OverlaySpec } from "./spec";

/**
 * Overlay timing and entrance/exit.
 *
 * The window is expressed in fractions of the shot so a retimed shot keeps its
 * graphics in the same relative place. Everything is a pure function of the
 * frame: no springs that depend on prior frames, no wall clock.
 */
export const useWindow = (spec: OverlaySpec, frames: number) => {
  const from = spec.from ?? 0.06;
  const to = spec.to ?? 0.94;
  return { start: Math.round(frames * from), end: Math.round(frames * to) };
};

export type OverlayRenderProps = {
  spec: OverlaySpec;
  box: Box;
  /** 0..1 progress inside the shot, already provided by the caller. */
  p: number;
  frames: number;
};

export const OverlayFrame: React.FC<OverlayRenderProps & { children: React.ReactNode }> = ({ spec, box, frames, children }) => {
  const frame = useCurrentFrame();
  const style = useStyle();
  const { start, end } = useWindow(spec, frames);
  const kind = spec.animation ?? style.motion.kind;
  const inFrames = Math.max(1, Math.round(style.motion.enterFrames));
  const outFrames = Math.max(1, Math.round(style.motion.exitFrames));

  if (frame < start || frame > end) return null;

  const enter = easeOutCubic(clamp((frame - start) / inFrames));
  // A bridge card must survive until the cut, otherwise the transition drops
  // to the scene for its last frames and the dissolve reads as a mistake.
  const exit = spec.ui?.mode === "F" ? 1 : clamp((end - frame) / outFrames);
  const opacity = Math.min(enter, exit);

  const rise = style.motion.rise;
  const transform =
    kind === "rise"
      ? `translateY(${(1 - enter) * rise - (1 - exit) * rise * 0.4}px)`
      : kind === "pop"
        ? `scale(${0.92 + enter * 0.08 + (1 - exit) * 0.03})`
        : "none";

  return (
    <div
      style={{
        position: "absolute",
        left: `${box.x * 100}%`,
        top: `${box.y * 100}%`,
        width: `${box.w * 100}%`,
        height: `${box.h * 100}%`,
        opacity,
        transform,
        transformOrigin: "50% 100%",
        clipPath: kind === "wipe" ? `inset(0 ${(1 - enter) * 100}% 0 0)` : undefined,
        pointerEvents: "none",
      }}
    >
      {children}
    </div>
  );
};

/** Small "ilustrativo" marker: a schematic value must never read as a measurement. */
export const Provenance: React.FC<{ spec: OverlaySpec; align?: "left" | "right" }> = ({ spec, align = "left" }) => {
  const style = useStyle();
  const label = spec.illustrative ? "ilustrativo" : spec.source ? `fuente: ${spec.source}` : "";
  if (!label) return null;
  return (
    <div
      style={{
        fontFamily: style.type.ui,
        fontSize: style.type.microSize * 0.82,
        letterSpacing: 0.6,
        textTransform: "uppercase",
        color: style.palette.muted,
        textAlign: align,
        marginTop: 4,
      }}
    >
      {label}
    </div>
  );
};
