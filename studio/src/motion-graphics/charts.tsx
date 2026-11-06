import React from "react";
import { useCurrentFrame } from "remotion";
import { clamp, easeOutCubic, lerp } from "../engine/math";
import { useStyle } from "../engine/styles";
import type { Box } from "./spec";
import { OverlayFrame, Provenance, type OverlayRenderProps } from "./Frame";

/**
 * Data graphics.
 *
 * Rules baked into the components:
 *  - every number is labelled with its unit and its provenance;
 *  - the animation is a reveal, never a value that counts up from nowhere;
 *  - a chart with no data renders an explicit "sin datos" plate instead of an
 *    empty frame, so a missing payload is visible in the render.
 *
 * Type and bar sizes derive from the resolved box, not from a constant: the
 * same component is a 300 px compact card in mode B and a 700 px focus panel in
 * mode D/E, and it must fill the box it was given without becoming a stamp in
 * the middle of an empty plate.
 */

const tone = (style: ReturnType<typeof useStyle>, t: string | undefined) =>
  t === "accentAlt" ? style.palette.accentAlt : t === "warn" ? style.palette.warn : style.palette.accent;

/** Scale factor: 1.0 ≈ a 380 px-tall compact box. */
const scaleFor = (box: Box) => clamp((box.h * 1920) / 380, 0.85, 1.7);

const Empty: React.FC<{ text?: string }> = ({ text = "sin datos" }) => {
  const style = useStyle();
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        width: "100%",
        height: "100%",
        border: `2px dashed ${style.palette.line}`,
        borderRadius: style.ui.radius,
        color: style.palette.muted,
        fontFamily: style.type.ui,
        fontSize: style.type.labelSize * 0.8,
        letterSpacing: 1.2,
        textTransform: "uppercase",
      }}
    >
      {text}
    </div>
  );
};

const Heading: React.FC<{ title?: string; caption?: string; scale?: number }> = ({ title, caption, scale = 1 }) => {
  const style = useStyle();
  if (!title && !caption) return null;
  return (
    <div style={{ marginBottom: 10 * scale }}>
      {title ? (
        <div
          style={{
            fontFamily: style.type.ui,
            fontWeight: 800,
            fontSize: style.type.labelSize * scale,
            color: style.palette.text,
            letterSpacing: 0.3,
            lineHeight: 1.12,
          }}
        >
          {title}
        </div>
      ) : null}
      {caption ? (
        <div style={{ fontFamily: style.type.ui, fontSize: style.type.microSize * scale, color: style.palette.muted, marginTop: 2 }}>{caption}</div>
      ) : null}
    </div>
  );
};

export const BarChart: React.FC<OverlayRenderProps> = ({ spec, box, frames }) => {
  const style = useStyle();
  const frame = useCurrentFrame();
  const data = spec.data?.series ?? [];
  if (!data.length) {
    return (
      <OverlayFrame spec={spec} box={box} p={0} frames={1}>
        <Empty />
      </OverlayFrame>
    );
  }
  const s = scaleFor(box);
  const px = box.h * 1920;
  const barH = clamp(18, px * 0.14, 62);
  const max = Math.max(...data.map((d) => Math.abs(d.value)), Number.EPSILON);
  const local = easeOutCubic(clamp((frame - (spec.from ?? 0.06) * frames) / 24));
  return (
    <div style={{ display: "flex", flexDirection: "column", justifyContent: "center", gap: 12 * s, width: "100%", height: "100%" }}>
      <Heading title={spec.data?.title} caption={spec.data?.caption} scale={s} />
      {data.map((row, i) => {
        const grow = clamp(local * 1.6 - i * 0.12);
        return (
          <div key={row.label} style={{ display: "flex", alignItems: "center", gap: 12 * s }}>
            <div
              style={{
                width: "36%",
                fontFamily: style.type.ui,
                fontSize: style.type.microSize * s,
                color: style.palette.text,
                textAlign: "right",
                opacity: 0.92,
              }}
            >
              {row.label}
            </div>
            <div style={{ position: "relative", flex: 1, height: barH }}>
              <div
                style={{
                  position: "absolute",
                  inset: 0,
                  borderRadius: style.graphics.barShape === "rounded" ? barH / 2 : 0,
                  background: "rgba(255,255,255,0.08)",
                }}
              />
              <div
                style={{
                  position: "absolute",
                  left: 0,
                  top: 0,
                  bottom: 0,
                  width: `${(Math.abs(row.value) / max) * 100 * grow}%`,
                  borderRadius: style.graphics.barShape === "rounded" ? barH / 2 : 0,
                  background: tone(style, row.tone),
                  opacity: style.graphics.fillOpacity,
                }}
              />
            </div>
            <div
              style={{
                width: "16%",
                fontFamily: style.type.mono,
                fontSize: style.type.microSize * s,
                color: style.palette.text,
                fontVariantNumeric: "tabular-nums",
              }}
            >
              {row.value.toLocaleString("es-ES")}
              {spec.data?.unit ? ` ${spec.data.unit}` : ""}
            </div>
          </div>
        );
      })}
      <Provenance spec={spec} align="right" />
    </div>
  );
};

export const DonutChart: React.FC<OverlayRenderProps> = ({ spec, box, frames }) => {
  const style = useStyle();
  const frame = useCurrentFrame();
  const segments = spec.data?.segments ?? [];
  const total = segments.reduce((sum, s) => sum + Math.max(0, s.value), 0);
  if (!segments.length || total <= 0) {
    return (
      <OverlayFrame spec={spec} box={box} p={0} frames={1}>
        <Empty />
      </OverlayFrame>
    );
  }
  const s = scaleFor(box);
  const donut = clamp(Math.min(box.h * 1920 * 0.72, box.w * 1080 * 0.34), 120, 300);
  const local = clamp((frame - (spec.from ?? 0.06) * frames) / 26);
  const R = 74;
  const C = 2 * Math.PI * R;
  let offset = 0;
  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 22 * s, height: "100%" }}>
      <svg viewBox="0 0 200 200" style={{ width: donut, height: donut, flex: "0 0 auto" }}>
        <circle cx={100} cy={100} r={R} fill="none" stroke="rgba(255,255,255,0.12)" strokeWidth={26} />
        {segments.map((seg) => {
          const frac = Math.max(0, seg.value) / total;
          const dash = C * frac * local;
          const el = (
            <circle
              key={seg.label}
              cx={100}
              cy={100}
              r={R}
              fill="none"
              stroke={tone(style, seg.tone)}
              strokeWidth={26}
              strokeDasharray={`${dash} ${C}`}
              strokeDashoffset={-offset * C * local}
              transform="rotate(-90 100 100)"
              strokeLinecap="butt"
            />
          );
          offset += frac;
          return el;
        })}
        {spec.data?.center ? (
          <text x={100} y={108} textAnchor="middle" fontFamily={style.type.ui} fontSize={26} fontWeight={800} fill={style.palette.text}>
            {spec.data.center}
          </text>
        ) : null}
      </svg>
      <div style={{ display: "flex", flexDirection: "column", gap: 8 * s, maxWidth: "52%" }}>
        <Heading title={spec.data?.title} scale={s} />
        {segments.map((seg) => (
          <div key={seg.label} style={{ display: "flex", alignItems: "center", gap: 8 * s }}>
            <span style={{ width: 12 * s, height: 12 * s, borderRadius: 3, background: tone(style, seg.tone), display: "inline-block" }} />
            <span style={{ fontFamily: style.type.ui, fontSize: style.type.microSize * s, color: style.palette.text }}>
              {seg.label} · {Math.round((seg.value / total) * 100)}%
            </span>
          </div>
        ))}
        <Provenance spec={spec} />
      </div>
    </div>
  );
};

export const LineChart: React.FC<OverlayRenderProps> = ({ spec, box, frames }) => {
  const style = useStyle();
  const frame = useCurrentFrame();
  const points = spec.data?.points ?? [];
  if (points.length < 2) {
    return (
      <OverlayFrame spec={spec} box={box} p={0} frames={1}>
        <Empty />
      </OverlayFrame>
    );
  }
  const s = scaleFor(box);
  const W = 560;
  const H = 240;
  const pad = 14;
  const min = Math.min(...points);
  const max = Math.max(...points);
  const span = Math.max(1e-6, max - min);
  const xy = points.map((v, i) => ({
    x: pad + (i / (points.length - 1)) * (W - pad * 2),
    y: pad + (1 - (v - min) / span) * (H - pad * 2),
  }));
  const path = xy.map((pt, i) => `${i === 0 ? "M" : "L"}${pt.x.toFixed(1)} ${pt.y.toFixed(1)}`).join(" ");
  const local = clamp((frame - (spec.from ?? 0.06) * frames) / 30);
  const len = 1400;
  return (
    <div style={{ width: "100%", height: "100%", display: "flex", flexDirection: "column", justifyContent: "center" }}>
      <Heading title={spec.data?.title} caption={spec.data?.caption} scale={s} />
      <svg viewBox={`0 0 ${W} ${H}`} style={{ width: "100%", height: "auto", overflow: "visible" }}>
        {style.graphics.grid
          ? [0.25, 0.5, 0.75].map((g) => <line key={g} x1={0} x2={W} y1={H * g} y2={H * g} stroke="rgba(255,255,255,0.14)" strokeWidth={1} />)
          : null}
        {style.graphics.area ? (
          <path d={`${path} L${xy[xy.length - 1].x} ${H} L${xy[0].x} ${H} Z`} fill={style.palette.accent} opacity={0.16 * local} />
        ) : null}
        <path d={path} fill="none" stroke={style.palette.accent} strokeWidth={style.graphics.strokeWidth} strokeDasharray={len} strokeDashoffset={len * (1 - local)} strokeLinejoin="round" />
        {xy.map((pt, i) => (
          <circle key={i} cx={pt.x} cy={pt.y} r={4.5} fill={style.palette.paper} stroke={style.palette.accent} strokeWidth={2} opacity={local} />
        ))}
        <text x={pad} y={H - 2} fill={style.palette.muted} fontFamily={style.type.mono} fontSize={20 * s}>
          {min}
          {spec.data?.unit ? ` ${spec.data.unit}` : ""}
        </text>
        <text x={W - pad} y={H - 2} textAnchor="end" fill={style.palette.muted} fontFamily={style.type.mono} fontSize={20 * s}>
          {max}
          {spec.data?.unit ? ` ${spec.data.unit}` : ""}
        </text>
      </svg>
      <Provenance spec={spec} align="right" />
    </div>
  );
};

export const Counter: React.FC<OverlayRenderProps> = ({ spec, box, frames }) => {
  const style = useStyle();
  const frame = useCurrentFrame();
  const target = Number(spec.data?.value ?? 0);
  const start = Number(spec.data?.from ?? 0);
  const local = easeOutCubic(clamp((frame - (spec.from ?? 0.06) * frames) / 28));
  const value = lerp(start, target, local);
  const decimals = spec.data?.decimals ?? 0;
  const px = box.h * 1920;
  const numberSize = clamp(px * 0.62, 34, 210);
  return (
    <div style={{ width: "100%", display: "flex", flexDirection: "column", justifyContent: "center" }}>
      {spec.data?.title ? (
        <div
          style={{
            fontFamily: style.type.ui,
            fontSize: clamp(style.type.microSize * (px / 300), 16, 40),
            letterSpacing: 1.4,
            textTransform: "uppercase",
            color: style.palette.muted,
          }}
        >
          {spec.data.title}
        </div>
      ) : null}
      <div
        style={{
          fontFamily: style.type.ui,
          fontWeight: 900,
          fontSize: numberSize,
          lineHeight: 1,
          color: style.palette.text,
          fontVariantNumeric: "tabular-nums",
          textShadow: "0 6px 24px rgba(0,0,0,0.45)",
        }}
      >
        {value.toLocaleString("es-ES", { minimumFractionDigits: decimals, maximumFractionDigits: decimals })}
        {spec.data?.unit ? <span style={{ fontSize: "0.42em", marginLeft: 10, color: style.palette.accent }}>{spec.data.unit}</span> : null}
      </div>
      {spec.data?.caption ? (
        <div style={{ fontFamily: style.type.ui, fontSize: style.type.microSize, color: style.palette.text, opacity: 0.86, marginTop: 6 }}>
          {spec.data.caption}
        </div>
      ) : null}
      <Provenance spec={spec} />
    </div>
  );
};

export const Ranking: React.FC<OverlayRenderProps> = ({ spec, box, frames }) => {
  const style = useStyle();
  const frame = useCurrentFrame();
  const rows = [...(spec.data?.rows ?? [])].sort((a, b) => b.value - a.value);
  if (!rows.length) {
    return (
      <OverlayFrame spec={spec} box={box} p={0} frames={1}>
        <Empty />
      </OverlayFrame>
    );
  }
  const s = scaleFor(box);
  const max = Math.max(...rows.map((r) => r.value), 1);
  const local = clamp((frame - (spec.from ?? 0.06) * frames) / 24);
  return (
    <div style={{ width: "100%", height: "100%", display: "flex", flexDirection: "column", justifyContent: "center" }}>
      <Heading title={spec.data?.title} scale={s} />
      {rows.map((row, i) => (
        <div key={row.label} style={{ display: "flex", alignItems: "center", gap: 12 * s, marginBottom: 10 * s }}>
          <div style={{ width: 34 * s, fontFamily: style.type.mono, fontSize: style.type.labelSize * s, color: style.palette.accent }}>{i + 1}</div>
          <div style={{ flex: 1 }}>
            <div style={{ display: "flex", justifyContent: "space-between", fontFamily: style.type.ui, fontSize: style.type.microSize * s, color: style.palette.text }}>
              <span>{row.label}</span>
              <span style={{ fontFamily: style.type.mono }}>
                {row.value.toLocaleString("es-ES")}
                {spec.data?.unit ? ` ${spec.data.unit}` : ""}
              </span>
            </div>
            <div style={{ height: 8 * s, background: "rgba(255,255,255,0.1)", marginTop: 5 * s, borderRadius: 4 }}>
              <div
                style={{
                  width: `${(row.value / max) * 100 * clamp(local * 1.5 - i * 0.1)}%`,
                  height: "100%",
                  background: tone(style, row.tone ?? (i === 0 ? "accent" : "accentAlt")),
                  borderRadius: 4,
                }}
              />
            </div>
          </div>
        </div>
      ))}
      <Provenance spec={spec} align="right" />
    </div>
  );
};

export const Process: React.FC<OverlayRenderProps> = ({ spec, box, frames }) => {
  const style = useStyle();
  const frame = useCurrentFrame();
  const steps = spec.data?.steps ?? [];
  if (!steps.length) {
    return (
      <OverlayFrame spec={spec} box={box} p={0} frames={1}>
        <Empty />
      </OverlayFrame>
    );
  }
  const s = scaleFor(box);
  const local = clamp((frame - (spec.from ?? 0.06) * frames) / 26);
  return (
    <div style={{ width: "100%", height: "100%", display: "flex", flexDirection: "column", justifyContent: "center" }}>
      <Heading title={spec.data?.title} scale={s} />
      <div style={{ display: "flex", alignItems: "flex-start", gap: 0, marginTop: 8 * s }}>
        {steps.map((step, i) => {
          const on = clamp(local * steps.length * 1.2 - i);
          return (
            <React.Fragment key={step.label}>
              {i > 0 ? (
                <div style={{ flex: 1, height: 3, marginTop: 16 * s, background: `rgba(255,255,255,${0.16 + on * 0.5})` }} />
              ) : null}
              <div style={{ flex: 1, minWidth: 0, textAlign: "center" }}>
                <div
                  style={{
                    width: 34 * s,
                    height: 34 * s,
                    margin: "0 auto",
                    borderRadius: 17 * s,
                    border: `3px solid ${style.palette.accent}`,
                    background: on > 0.5 ? style.palette.accent : "transparent",
                    color: on > 0.5 ? style.palette.ink : style.palette.text,
                    fontFamily: style.type.mono,
                    fontSize: 17 * s,
                    lineHeight: `${28 * s}px`,
                    fontWeight: 700,
                  }}
                >
                  {i + 1}
                </div>
                <div
                  style={{
                    fontFamily: style.type.ui,
                    fontSize: style.type.microSize * s * 1.08,
                    color: style.palette.text,
                    marginTop: 8 * s,
                    opacity: 0.4 + on * 0.6,
                  }}
                >
                  {step.label}
                </div>
                {step.detail ? (
                  <div style={{ fontFamily: style.type.ui, fontSize: style.type.microSize * s * 0.86, color: style.palette.muted, marginTop: 3 * s }}>
                    {step.detail}
                  </div>
                ) : null}
              </div>
            </React.Fragment>
          );
        })}
      </div>
      <Provenance spec={spec} />
    </div>
  );
};
