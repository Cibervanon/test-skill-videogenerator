import React from "react";
import { AbsoluteFill } from "remotion";
import { Character } from "../characters/Character";
import { cast } from "../characters/cast";

/**
 * Identity sheet: the same canonical identity in seven acting states.
 *
 * It exists to make drift visible before a render: if a pose changes the head
 * size, the coat, the hat or the silhouette, it is on this sheet. Pose, camera
 * and expression are expected to differ; identity is not.
 */

type Pose = {
  label: string;
  yaw?: number;
  headTilt?: number;
  gait?: number;
  phase?: number;
  mouth?: number;
  brow?: number;
  armR?: number;
  elbowR?: number;
  handR?: "open" | "point" | "fist";
  lean?: number;
};

const POSES: Pose[] = [
  { label: "NEUTRA · FRONTAL" },
  { label: "TRES CUARTOS", yaw: 0.6, headTilt: -2 },
  { label: "PERFIL", yaw: 1, headTilt: -3 },
  { label: "CAMINAR", gait: 0.8, phase: 1.2 },
  { label: "HABLAR", mouth: 0.55, brow: 0.1 },
  { label: "SORPRESA", brow: 0.9, mouth: 0.45, headTilt: -4 },
  { label: "ACCIÓN", armR: -100, elbowR: -18, handR: "point", lean: 4, brow: 0.3 },
];

const ROWS = ["elder", "young"] as const;
const W = 2100;
const H = 1300;

export const IdentitySheet: React.FC = () => (
  <AbsoluteFill style={{ backgroundColor: "#0e0c16" }}>
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`}>
      <defs>
        <linearGradient id="id-bg" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#1a1626" />
          <stop offset="100%" stopColor="#0d0b14" />
        </linearGradient>
      </defs>
      <rect width={W} height={H} fill="url(#id-bg)" />
      <text x={70} y={70} fill="#f6efe3" fontFamily="Inter, Segoe UI, sans-serif" fontSize={30} letterSpacing={3}>
        AI CINEMATIC STUDIO · IDENTITY SHEET · ONE IDENTITY, SEVEN POSES
      </text>
      <text x={70} y={106} fill="#a79fb8" fontFamily="Inter, Segoe UI, sans-serif" fontSize={17} letterSpacing={2}>
        pose, yaw and expression may change · head size, coat, hat and silhouette may not
      </text>

      {ROWS.map((key, row) => {
        const character = cast[key];
        const baseY = 520 + row * 610;
        return (
          <g key={key}>
            <text
              x={70}
              y={baseY - 330}
              fill="#ffb15a"
              fontFamily="Inter, Segoe UI, sans-serif"
              fontSize={20}
              letterSpacing={3}
            >
              {character.name.toUpperCase()} · h{character.height} · r{character.headRadius} · {character.coat}
            </text>
            {POSES.map((pose, i) => {
              const x = 190 + i * 280;
              return (
                <g key={pose.label} transform={`translate(${x} ${baseY})`}>
                  <line x1={-110} y1={-250} x2={110} y2={-250} stroke="#2c2536" strokeWidth={1} />
                  <Character
                    spec={character}
                    x={0}
                    y={0}
                    scale={0.9}
                    facing={1}
                    yaw={pose.yaw ?? 0}
                    headTilt={pose.headTilt ?? 0}
                    gait={pose.gait ?? 0}
                    phase={pose.phase ?? 0}
                    mouth={pose.mouth ?? 0.1}
                    brow={pose.brow ?? 0}
                    armR={pose.armR ?? -8}
                    elbowR={pose.elbowR}
                    handR={pose.handR ?? "open"}
                    lean={pose.lean ?? 0}
                  />
                  <text
                    x={0}
                    y={70}
                    textAnchor="middle"
                    fill="#cfc7db"
                    fontFamily="Inter, Segoe UI, sans-serif"
                    fontSize={15}
                    letterSpacing={2}
                  >
                    {pose.label}
                  </text>
                </g>
              );
            })}
          </g>
        );
      })}
    </svg>
  </AbsoluteFill>
);
