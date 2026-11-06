import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { clamp, easeOutCubic } from "../engine/math";
import { useStyle } from "../engine/styles";
import { Provenance, type OverlayRenderProps } from "./Frame";

/**
 * Information layer: callouts, labels, panels, HUD, badges, arrows, highlights.
 *
 * The distinction from charts is intent: charts quantify, these *point*. Every
 * element is backed by a plate or a stroke, so text never sits directly on an
 * unknown background (the inspector measures that contrast on the render).
 */

const plate = (style: ReturnType<typeof useStyle>) => ({
  background: style.palette.surface,
  border: `${style.ui.stroke}px solid ${style.palette.line}`,
  borderRadius: style.ui.radius,
  backdropFilter: style.ui.backdropBlur ? `blur(${style.ui.backdropBlur}px)` : undefined,
  boxShadow: "0 18px 40px rgba(0,0,0,0.42)",
});

export const Panel: React.FC<OverlayRenderProps> = ({ spec }) => {
  const style = useStyle();
  const rows = spec.data?.series ?? spec.data?.rows ?? [];
  return (
    <div style={{ ...plate(style), width: "100%", height: "100%", padding: 22, boxSizing: "border-box", display: "flex", flexDirection: "column" }}>
      <div style={{ fontFamily: style.type.ui, fontWeight: 800, fontSize: style.type.labelSize, color: style.palette.text }}>{spec.data?.title}</div>
      {spec.data?.caption ? (
        <div style={{ fontFamily: style.type.ui, fontSize: style.type.microSize, color: style.palette.muted, marginTop: 4 }}>{spec.data.caption}</div>
      ) : null}
      <div style={{ marginTop: 12, display: "flex", flexDirection: "column", gap: 8 }}>
        {rows.map((row) => (
          <div key={row.label} style={{ display: "flex", justifyContent: "space-between", borderTop: `1px solid ${style.palette.line}`, paddingTop: 7 }}>
            <span style={{ fontFamily: style.type.ui, fontSize: style.type.microSize, color: style.palette.text }}>{row.label}</span>
            <span style={{ fontFamily: style.type.mono, fontSize: style.type.microSize, color: style.palette.accent }}>
              {row.value}
              {spec.data?.unit ? ` ${spec.data.unit}` : ""}
            </span>
          </div>
        ))}
      </div>
      <div style={{ marginTop: "auto" }}>
        <Provenance spec={spec} />
      </div>
    </div>
  );
};

export const Badge: React.FC<OverlayRenderProps> = ({ spec }) => {
  const style = useStyle();
  return (
    <div style={{ display: "inline-flex", alignItems: "center", gap: 10, ...plate(style), borderRadius: 999, padding: "9px 18px" }}>
      <span style={{ width: 11, height: 11, borderRadius: 6, background: style.palette.accent, boxShadow: `0 0 12px ${style.palette.accent}` }} />
      <span style={{ fontFamily: style.type.ui, fontSize: style.type.microSize, letterSpacing: 1.6, textTransform: "uppercase", color: style.palette.text }}>
        {spec.data?.title ?? spec.data?.name ?? ""}
      </span>
    </div>
  );
};

export const Callout: React.FC<OverlayRenderProps> = ({ spec }) => {
  const style = useStyle();
  const frame = useCurrentFrame();
  const pulse = 0.55 + 0.45 * Math.sin(frame / 9);
  return (
    <div style={{ position: "relative", width: "100%", height: "100%" }}>
      <div style={{ ...plate(style), padding: "14px 18px", width: "100%", height: "100%", boxSizing: "border-box", display: "flex", flexDirection: "column", justifyContent: "center" }}>
        {spec.data?.title ? (
          <div style={{ fontFamily: style.type.ui, fontWeight: 800, fontSize: style.type.labelSize * 0.94, color: style.palette.text }}>{spec.data.title}</div>
        ) : null}
        {spec.data?.caption ? (
          <div style={{ fontFamily: style.type.ui, fontSize: style.type.microSize, color: style.palette.muted, marginTop: 4, lineHeight: 1.25 }}>{spec.data.caption}</div>
        ) : null}
      </div>
      {/* leader: a short stem plus a dot, so the card is visibly attached to a subject */}
      <div style={{ position: "absolute", left: "50%", bottom: -34, width: 2, height: 34, background: style.palette.line }} />
      <div style={{ position: "absolute", left: "50%", bottom: -42, width: 11, height: 11, marginLeft: -5, borderRadius: 6, background: style.palette.accent, opacity: pulse }} />
    </div>
  );
};

export const Arrow: React.FC<OverlayRenderProps> = ({ spec, box }) => {
  const style = useStyle();
  const frame = useCurrentFrame();
  const local = clamp((frame - (spec.from ?? 0.06) * 100) / 26);
  const W = 600;
  const H = Math.max(120, box.h * 1920);
  const d = `M 20 ${H - 30} Q ${W * 0.45} ${H * 0.12} ${W - 40} ${H * 0.3}`;
  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" height="100%" style={{ overflow: "visible" }}>
      <defs>
        <marker id={`head-${spec.id}`} markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto">
          <path d="M 0 0 L 12 6 L 0 12 z" fill={style.palette.accent} />
        </marker>
      </defs>
      <path
        d={d}
        fill="none"
        stroke={style.palette.accent}
        strokeWidth={4.5}
        strokeLinecap="round"
        strokeDasharray={900}
        strokeDashoffset={900 * (1 - easeOutCubic(local))}
        markerEnd={`url(#head-${spec.id})`}
      />
    </svg>
  );
};

export const Highlight: React.FC<OverlayRenderProps> = ({ spec, box }) => {
  const style = useStyle();
  const frame = useCurrentFrame();
  const local = easeOutCubic(clamp((frame - (spec.from ?? 0.06) * 100) / 18));
  const corner = 26;
  const stroke = style.palette.accent;
  return (
    <svg viewBox={`0 0 ${box.w * 1080} ${box.h * 1920}`} width="100%" height="100%" preserveAspectRatio="none" style={{ overflow: "visible" }}>
      <rect
        x={2}
        y={2}
        width={box.w * 1080 - 4}
        height={box.h * 1920 - 4}
        fill="none"
        stroke={stroke}
        strokeWidth={3}
        strokeDasharray={`${corner} 14`}
        opacity={0.35 + 0.4 * local}
        rx={style.ui.radius}
      />
      {[
        [0, 0, 1, 1],
        [box.w * 1080, 0, -1, 1],
        [0, box.h * 1920, 1, -1],
        [box.w * 1080, box.h * 1920, -1, -1],
      ].map(([cx, cy, sx, sy], i) => (
        <g key={i} stroke={stroke} strokeWidth={6} strokeLinecap="square" opacity={local}>
          <line x1={cx} y1={cy} x2={cx + 34 * sx} y2={cy} />
          <line x1={cx} y1={cy} x2={cx} y2={cy + 34 * sy} />
        </g>
      ))}
      <rect x={2} y={2} width={box.w * 1080 - 4} height={box.h * 1920 - 4} fill={stroke} opacity={0.06 * (1 - local)} />
    </svg>
  );
};

export const Hud: React.FC<OverlayRenderProps> = ({ spec, box, p }) => {
  const style = useStyle();
  const { fps } = useVideoConfig();
  const seconds = p * box.h * 0 + p; // shot progress kept explicit below
  const items = spec.data?.labels ?? [];
  return (
    <div style={{ width: "100%", display: "flex", justifyContent: "space-between", alignItems: "center", fontFamily: style.type.mono }}>
      <div style={{ display: "flex", gap: 18, alignItems: "center" }}>
        <span style={{ width: 9, height: 9, borderRadius: 5, background: style.palette.warn, opacity: 0.9 }} />
        <span style={{ fontSize: style.type.microSize, letterSpacing: 2, color: style.palette.text, textTransform: "uppercase" }}>
          {spec.data?.title ?? "registro"}
        </span>
      </div>
      <div style={{ display: "flex", gap: 16, fontSize: style.type.microSize * 0.9, color: style.palette.muted, letterSpacing: 1.2 }}>
        {items.map((item) => (
          <span key={item}>{item}</span>
        ))}
        <span style={{ color: style.palette.accent }}>
          {fps}fps · {(seconds * 100).toFixed(0).padStart(3, "0")}%
        </span>
      </div>
    </div>
  );
};

/**
 * Character label. It is placed by the layout module (never arbitrary
 * coordinates), so it follows the body across framings and keeps clear of the
 * face; the leader makes the attachment visible when the label sits beside the
 * head instead of above it.
 */
export const LabelTag: React.FC<OverlayRenderProps & { above?: boolean }> = ({ spec, above = true }) => {
  const style = useStyle();
  const tone = spec.data?.tone === "warn" ? style.palette.warn : spec.data?.tone === "accentAlt" ? style.palette.accentAlt : style.palette.accent;
  return (
    <div style={{ position: "relative", width: "100%" }}>
      <div
        style={{
          ...plate(style),
          display: "inline-flex",
          flexDirection: "column",
          padding: "10px 16px 11px",
          borderLeft: `5px solid ${tone}`,
          borderRadius: style.ui.labelStyle === "bubble" ? 22 : style.ui.radius,
          maxWidth: "100%",
        }}
      >
        <span style={{ fontFamily: style.type.ui, fontWeight: 800, fontSize: style.type.labelSize, color: style.palette.text, letterSpacing: 0.2, lineHeight: 1.1 }}>
          {spec.data?.name ?? ""}
        </span>
        {spec.data?.role ? (
          <span style={{ fontFamily: style.type.ui, fontSize: style.type.microSize * 0.95, color: style.palette.muted, marginTop: 2 }}>{spec.data.role}</span>
        ) : null}
        {spec.data?.status ? (
          <span style={{ fontFamily: style.type.mono, fontSize: style.type.microSize * 0.8, color: tone, marginTop: 4, letterSpacing: 1, textTransform: "uppercase" }}>
            {spec.data.status}
          </span>
        ) : null}
      </div>
      {style.ui.labelStyle === "leader" ? (
        <>
          <div style={{ position: "absolute", left: 26, [above ? "top" : "bottom"]: -22, width: 2, height: 22, background: tone, opacity: 0.85 }} />
          <div style={{ position: "absolute", left: 21.5, [above ? "top" : "bottom"]: -27, width: 11, height: 11, borderRadius: 6, background: tone }} />
        </>
      ) : null}
    </div>
  );
};
