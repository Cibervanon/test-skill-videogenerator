import React from "react";
import { AbsoluteFill } from "remotion";
import { useStyle } from "../engine/styles";
import { Provenance, type OverlayRenderProps } from "./Frame";

/**
 * Presentation layers for the composition modes.
 *
 * The UI director decides the mode per shot and writes it into the manifest;
 * these components only render that decision. They never choose for themselves
 * whether a scene should be dimmed or replaced.
 */

/** Mode D: the scene stays, but it stops competing with the data. */
export const Scrim: React.FC<{ opacity?: number }> = ({ opacity = 0.58 }) => (
  <AbsoluteFill
    style={{
      background: `radial-gradient(120% 90% at 50% 42%, rgba(6,5,10,${opacity * 0.72}) 0%, rgba(6,5,10,${Math.min(
        0.94,
        opacity + 0.22,
      )}) 78%)`,
    }}
  />
);

/** Mode E: an independent plate. No set, no actors, one idea. */
export const ExplainerBackdrop: React.FC = () => {
  const style = useStyle();
  return (
    <AbsoluteFill style={{ background: `linear-gradient(180deg, ${style.palette.ink} 0%, #0b0912 58%, ${style.palette.ink} 100%)` }}>
      <AbsoluteFill
        style={{
          backgroundImage: `linear-gradient(${style.palette.line} 1px, transparent 1px), linear-gradient(90deg, ${style.palette.line} 1px, transparent 1px)`,
          backgroundSize: "120px 120px",
          opacity: 0.11,
        }}
      />
      <div
        style={{
          position: "absolute",
          left: "6%",
          top: "6%",
          fontFamily: style.type.mono,
          fontSize: style.type.microSize * 0.78,
          letterSpacing: 3.4,
          textTransform: "uppercase",
          color: style.palette.muted,
        }}
      >
        explicación
      </div>
    </AbsoluteFill>
  );
};

/**
 * Mode F: the element becomes the cut. A full-frame card carries the last beat
 * of the shot and dissolves into the next one, so the transition is motivated
 * by the information instead of a decorative wipe.
 */
export const BridgeCard: React.FC<OverlayRenderProps> = ({ spec }) => {
  const style = useStyle();
  const data = spec.data ?? {};
  const value = typeof data.value === "number" ? data.value : undefined;
  // `surfaceStrong` is translucent in the cinematic/ infographic skins; a bridge
  // must hide the shot it is covering, so an opaque plate goes underneath.
  const solid = style.palette.surfaceStrong.startsWith("#") ? style.palette.surfaceStrong : style.palette.ink;
  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        background: solid,
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        padding: "0 9%",
        gap: 12,
        borderTop: `6px solid ${style.palette.accent}`,
      }}
    >
      <div
        style={{
          fontFamily: style.type.ui,
          fontSize: style.type.microSize,
          letterSpacing: 3,
          textTransform: "uppercase",
          color: style.palette.accent,
        }}
      >
        {data.title ?? "transición"}
      </div>
      {value !== undefined ? (
        <div
          style={{
            fontFamily: style.type.display,
            fontWeight: 800,
            fontSize: 190,
            lineHeight: 0.94,
            color: style.palette.text,
            fontVariantNumeric: "tabular-nums",
          }}
        >
          {value.toLocaleString("es-ES")}
          {data.unit ? <span style={{ fontSize: "0.34em", marginLeft: 14, color: style.palette.accent }}>{data.unit}</span> : null}
        </div>
      ) : null}
      {data.caption ? (
        <div style={{ fontFamily: style.type.ui, fontSize: style.type.labelSize * 0.92, color: style.palette.muted, lineHeight: 1.25 }}>
          {data.caption}
        </div>
      ) : null}
      <Provenance spec={spec} />
    </div>
  );
};
