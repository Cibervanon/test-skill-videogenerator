import React from "react";
import { AbsoluteFill } from "remotion";
import { Character } from "../characters/Character";
import { cast } from "../characters/cast";

/**
 * The cast sheet: every character on the one rig, each in the acting state it
 * actually uses, so proportions, palette and props can be compared at a glance.
 * Render it after touching the rig or a costume:
 *   npx remotion still src/index.ts CastSheet out/cast.png
 *
 * Idea from the external repository's `CastSheet.tsx` (MIT); this layout,
 * palette and the states below are specific to this cast.
 */

const LABEL: React.CSSProperties = {
  fontFamily: "Inter, Segoe UI, sans-serif",
  letterSpacing: 2,
};

type State = {
  id: string;
  state: string;
  armL: number;
  armR: number;
  brow: number;
  headTilt: number;
  lean: number;
  hold: "none" | "shovel" | "lantern" | "rope" | "bell";
};

const STATES: State[] = [
  { id: "elder", state: "HOLDING THE LANTERN", armL: 10, armR: -34, brow: -0.4, headTilt: 3, lean: 0, hold: "lantern" },
  { id: "young", state: "DIGGING", armL: 14, armR: -30, brow: 0.2, headTilt: 11, lean: 7, hold: "shovel" },
  { id: "widow", state: "WITHHELD", armL: 6, armR: -8, brow: -0.7, headTilt: -4, lean: -2, hold: "none" },
];

export const CastSheet: React.FC = () => (
  <AbsoluteFill style={{ backgroundColor: "#0e0c16" }}>
    <svg width={1400} height={860} viewBox="0 0 1400 860">
      <defs>
        <linearGradient id="cast-bg" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#1a1626" />
          <stop offset="100%" stopColor="#0d0b14" />
        </linearGradient>
      </defs>
      <rect width={1400} height={860} fill="url(#cast-bg)" />
      <text x={70} y={70} style={{ ...LABEL, fontSize: 26, fill: "#f6efe3" }}>
        AI CINEMATIC STUDIO · CAST SHEET · ONE RIG, ONE IDENTITY PER CHARACTER
      </text>
      <text x={70} y={104} style={{ ...LABEL, fontSize: 16, fill: "#a79fb8" }}>
        identity is data (cast.json), not a redraw per shot
      </text>

      {STATES.map((s, i) => {
        const x = 250 + i * 380;
        return (
          <g key={s.id} transform={`translate(${x} 0)`}>
            <rect x={-170} y={140} width={340} height={520} rx={18} fill="#171320" stroke="#2c2536" strokeWidth={2} />
            <Character
              spec={cast[s.id]}
              x={0}
              y={470}
              scale={0.95}
              facing={1}
              phase={0.6}
              armL={s.armL}
              armR={s.armR}
              brow={s.brow}
              headTilt={s.headTilt}
              lean={s.lean}
              hold={s.hold}
            />
            <text x={0} y={700} textAnchor="middle" style={{ ...LABEL, fontSize: 20, fill: "#f6efe3" }}>
              {cast[s.id].name.toUpperCase()}
            </text>
            <text x={0} y={728} textAnchor="middle" style={{ ...LABEL, fontSize: 14, fill: "#ffb15a" }}>
              {s.state}
            </text>
            <text x={0} y={754} textAnchor="middle" style={{ ...LABEL, fontSize: 12, fill: "#7d7590" }}>
              {cast[s.id].hatStyle} · r{cast[s.id].headRadius} · {cast[s.id].coat}
            </text>
          </g>
        );
      })}
    </svg>
  </AbsoluteFill>
);
