import React from "react";
import { ink, skin, blush } from "../engine/tokens";
import { RIG } from "./geometry";

export type CharacterSpec = {
  id: string;
  name: string;
  coat: string;
  coatDark: string;
  hat: string;
  hatBand: string;
  height: number;
  headRadius: number;
  hatStyle: "beanie" | "cap" | "scarf" | "bald";
  hairStyle: "none" | "curls" | "side";
  facialHair: "none" | "moustache" | "beard";
  voice: string;
  role: string;
};

export type RigProps = {
  spec: CharacterSpec;
  x: number;
  y: number;
  scale?: number;
  facing?: 1 | -1;
  gait?: number;
  phase?: number;
  armL?: number;
  armR?: number;
  headTilt?: number;
  blink?: number;
  mouth?: number;
  lean?: number;
  breath?: number;
  hold?: "none" | "shovel" | "lantern" | "rope" | "bell";
  shadow?: boolean;
  opacity?: number;
  /** -1 sad/concerned .. +1 angry; 0 neutral. Drives brow angle. */
  brow?: number;
  /** Explicit elbow bend override, degrees (positive bends outward). */
  elbowL?: number;
  elbowR?: number;
  /** Hand shape at the end of each forearm. */
  handL?: "open" | "point" | "fist";
  handR?: "open" | "point" | "fist";
  /** -1 looks screen-left, 0 front, +1 screen-right: shifts the features, not the head. */
  yaw?: number;
};

/**
 * Procedural character rig.
 *
 * Two changes over the first version, both aimed at the "wooden doll" read:
 *  - the coat is now volume-shaded with a gradient + occlusion under the head,
 *    so the torso stops looking like a flat cut-out;
 *  - arms are two segments with a driven elbow, and the head leads the body
 *    slightly during a walk (secondary motion), which removes the stiff
 *    single-piece feel without adding a physics system.
 */
export const Character: React.FC<RigProps> = ({
  spec,
  x,
  y,
  scale = 1,
  facing = 1,
  gait = 0,
  phase = 0,
  armL = 8,
  armR = -8,
  headTilt = 0,
  blink = 0,
  mouth = 0.12,
  lean = 0,
  breath = 0,
  hold = "none",
  shadow = true,
  opacity = 1,
  brow = 0,
  elbowL,
  elbowR,
  handL = "open",
  handR = "open",
  yaw = 0,
}) => {
  const H = spec.headRadius;
  // `height` is identity data (cast.json), not framing: shot scale decides how
  // big the character is on screen, height decides how tall they are next to
  // each other. Without it every character was the same body with another coat.
  const identity = spec.height ?? 1;
  const bodyTop = RIG.bodyTop;
  const shoulderY = RIG.shoulderY;
  const hem = RIG.hem;
  const headCY = bodyTop - H * 0.94;
  const legSwing = Math.sin(phase) * 22 * gait;
  const bob = Math.abs(Math.sin(phase)) * 3.4 * gait - breath * 1.4;
  const armSwing = Math.sin(phase + Math.PI) * 20 * gait;
  const headLead = Math.sin(phase - 0.7) * 2.2 * gait;
  const sway = Math.sin(phase + 0.4) * 1.6 * gait;

  const uid = `c${Math.round(x)}${Math.round(y)}${spec.id.replace(/[^a-z0-9]/gi, "")}`;

  const hand = (kind: "open" | "point" | "fist", side: 1 | -1) =>
    kind === "point" ? (
      // a fist with the index finger out: the one gesture the old rig could not do
      <g>
        <path d="M -9 -6 q -4 11 0 18 q 8 5 16 0 q 5 -7 1 -18 z" fill={skin} stroke={ink} strokeWidth={2.6} strokeLinejoin="round" />
        <rect x={-3} y={-16} width={6.5} height={16} rx={3.2} fill={skin} stroke={ink} strokeWidth={2.2} />
        <ellipse cx={side * -8} cy={2} rx={3.6} ry={6} fill={skin} stroke={ink} strokeWidth={2} />
      </g>
    ) : kind === "fist" ? (
      <g>
        <ellipse cx={0} cy={2} rx={9} ry={10} fill={skin} stroke={ink} strokeWidth={2.8} />
        <path d="M -6 4 q 6 3 12 0" stroke={ink} strokeWidth={1.6} fill="none" opacity={0.4} />
      </g>
    ) : (
      // an open mitten: palm plus a thumb, so the hand has a readable side
      <g>
        <ellipse cx={0} cy={3} rx={9.5} ry={11.5} fill={skin} stroke={ink} strokeWidth={2.8} />
        <ellipse cx={side * -8} cy={-2} rx={4} ry={6.8} transform={`rotate(${side * -24} ${side * -8} -2)`} fill={skin} stroke={ink} strokeWidth={2.2} />
        <path d="M -4 8 q 4 3 8 0" stroke={ink} strokeWidth={1.4} fill="none" opacity={0.35} />
      </g>
    );

  const arm = (angle: number, side: 1 | -1, withProp: React.ReactNode = null, kind: "open" | "point" | "fist" = "open", elbowOverride?: number) => {
    const elbow = elbowOverride ?? Math.max(-26, Math.min(26, -angle * 0.55 - 6 + gait * 8));
    return (
      <g transform={`rotate(${angle})`}>
        {/* upper arm */}
        <path d="M 0 0 C 3 18 5 30 6 38" stroke={`url(#${uid}-arm)`} strokeWidth={17} strokeLinecap="round" fill="none" />
        <path d="M 0 0 C 3 18 5 30 6 38" stroke={ink} strokeWidth={1.5} strokeLinecap="round" fill="none" opacity={0.18} />
        {/* forearm, bending at the elbow: the joint the first rig was missing */}
        <g transform={`translate(6 38) rotate(${elbow * side})`}>
          <path d="M 0 0 C 1 12 1 22 0 30" stroke={`url(#${uid}-arm)`} strokeWidth={15} strokeLinecap="round" fill="none" />
          <g transform="translate(0 34)">
            {hand(kind, side)}
            {withProp}
          </g>
        </g>
      </g>
    );
  };

  return (
    <g
      transform={`translate(${x} ${y}) scale(${scale * facing * identity} ${scale * identity}) translate(0 ${bob}) skewX(${sway}) rotate(${lean})`}
      opacity={opacity}
    >
      <defs>
        <linearGradient id={`${uid}-coat`} x1="0" y1="0" x2="1" y2="0.2">
          <stop offset="0%" stopColor={spec.coatDark} />
          <stop offset="26%" stopColor={spec.coat} />
          <stop offset="62%" stopColor={spec.coat} />
          <stop offset="100%" stopColor={spec.coatDark} />
        </linearGradient>
        <linearGradient id={`${uid}-arm`} x1="0" y1="0" x2="1" y2="0.4">
          <stop offset="0%" stopColor={spec.coat} />
          <stop offset="100%" stopColor={spec.coatDark} />
        </linearGradient>
        <radialGradient id={`${uid}-face`} cx="0.38" cy="0.32" r="0.78">
          <stop offset="0%" stopColor="#fffaf0" />
          <stop offset="72%" stopColor={skin} />
          <stop offset="100%" stopColor="#e6d8c2" />
        </radialGradient>
      </defs>

      {shadow ? <ellipse cx={0} cy={6} rx={56} ry={11} fill="rgba(12,8,20,0.4)" filter="url(#softBlur)" /> : null}

      {/* legs + boots */}
      <g>
        <g transform={`rotate(${legSwing} -18 ${hem})`}>
          <rect x={-26} y={hem} width={18} height={50} rx={8} fill={spec.coatDark} stroke={ink} strokeWidth={2.4} />
          <path d={`M -30 -6 q 4 -8 14 -8 q 10 0 12 8 q 1 7 -8 7 l -14 0 q -6 0 -4 -7 z`} fill="#2a1f28" stroke={ink} strokeWidth={2.2} />
        </g>
        <g transform={`rotate(${-legSwing} 18 ${hem})`}>
          <rect x={8} y={hem} width={18} height={50} rx={8} fill={spec.coatDark} stroke={ink} strokeWidth={2.4} />
          <path d={`M 4 -6 q 4 -8 14 -8 q 10 0 12 8 q 1 7 -8 7 l -14 0 q -6 0 -4 -7 z`} fill="#2a1f28" stroke={ink} strokeWidth={2.2} />
        </g>
      </g>

      {/* torso */}
      <g>
        <path
          d={`M 0 ${bodyTop}
              C 30 ${bodyTop} 44 ${bodyTop + 14} 47 ${bodyTop + 34}
              C 52 ${-152} 56 ${-108} 57 ${-88}
              C 58 ${-68} 50 ${hem} 38 ${hem}
              L -38 ${hem}
              C -50 ${hem} -58 ${-68} -57 ${-88}
              C -56 ${-108} -52 ${-152} -47 ${bodyTop + 34}
              C -44 ${bodyTop + 14} -30 ${bodyTop} 0 ${bodyTop} Z`}
          fill={`url(#${uid}-coat)`}
          stroke={ink}
          strokeWidth={3.4}
        />
        {/* occlusion under the chin + hem shadow: grounds the figure */}
        <path d={`M -34 ${bodyTop + 8} q 34 22 68 0 q -8 26 -34 26 q -26 0 -34 -26 z`} fill="#000" opacity={0.16} />
        <path d={`M -50 ${hem - 10} q 50 14 100 0 l 0 12 q -50 14 -100 0 z`} fill="#000" opacity={0.13} />
        {/* rim light on the key side */}
        <path
          d={`M -25 ${bodyTop + 6} C -47 ${bodyTop + 20} -51 ${-186} -49 ${-150} C -47 ${-116} -45 ${-84} -41 ${hem - 8}`}
          stroke="rgba(255,255,255,0.26)"
          strokeWidth={6}
          strokeLinecap="round"
          fill="none"
        />
        <path d={`M -26 ${bodyTop + 4} L 0 ${bodyTop + 30} L 26 ${bodyTop + 4}`} stroke={spec.coatDark} strokeWidth={6} fill="none" strokeLinejoin="round" strokeLinecap="round" />
        <path d={`M 1 ${bodyTop + 32} L 1 ${hem + 8}`} stroke="rgba(0,0,0,0.15)" strokeWidth={2} />
        {[0, 1, 2].map((i) => (
          <circle key={i} cx={1} cy={bodyTop + 76 + i * 27} r={2.4} fill={spec.coatDark} opacity={0.85} />
        ))}
        <g transform={`translate(-42 ${shoulderY})`}>{arm(armL + armSwing, -1, null, handL, elbowL)}</g>
        <g transform={`translate(42 ${shoulderY})`}>
          {arm(
            armR - armSwing,
            1,
            hold === "shovel" ? (
              <g transform="rotate(30)">
                <rect x={-3} y={-98} width={6} height={150} rx={3} fill="#8a6a4a" stroke={ink} strokeWidth={2.2} />
                <rect x={-3} y={-98} width={2} height={150} fill="#c8a882" opacity={0.6} />
                <path d="M -17 42 q 17 -13 34 0 l -7 30 q -10 8 -20 0 z" fill="#b9b2a6" stroke={ink} strokeWidth={2.4} />
                <path d="M -11 50 q 11 -7 22 0" stroke="#8f887c" strokeWidth={2} fill="none" opacity={0.7} />
              </g>
            ) : hold === "lantern" ? (
              <g transform="translate(0 8)">
                <path d="M 0 -12 v 8" stroke={ink} strokeWidth={3} />
                <path d="M -15 0 h 30 l 7 32 h -44 z" fill="#f7c977" stroke={ink} strokeWidth={3} />
                <ellipse cx={0} cy={16} rx={11} ry={12} fill="#fff3c9" />
                <path d="M -15 0 h 30" stroke="#8a5a2a" strokeWidth={4} />
              </g>
            ) : null,
            handR,
            elbowR
          )}
        </g>
      </g>

      <rect x={-10} y={bodyTop - 12} width={20} height={22} rx={7} fill={spec.coatDark} stroke={ink} strokeWidth={2.4} />

      {/* head */}
      <g transform={`translate(0 ${headCY})`}>
        <g transform={`rotate(${headTilt + headLead})`}>
          <circle cx={0} cy={0} r={H} fill={`url(#${uid}-face)`} stroke={ink} strokeWidth={4} />
          {/* jaw occlusion so the head has volume instead of being a flat disc */}
          <path d={`M ${-H * 0.86} ${H * 0.36} A ${H} ${H} 0 0 0 ${H * 0.86} ${H * 0.36}`} stroke="#000" strokeWidth={7} fill="none" opacity={0.07} />
          <ellipse cx={-H * 0.58} cy={H * 0.26} rx={H * 0.2} ry={H * 0.12} fill={blush} opacity={0.38} />
          <ellipse cx={H * 0.58} cy={H * 0.26} rx={H * 0.2} ry={H * 0.12} fill={blush} opacity={0.38} />

          {/* the face slides with yaw; the head silhouette and hat do not, so a
              turn reads as attention without a 3D head */}
          <g transform={`translate(${yaw * H * 0.12} 0)`}>
          {/* brows: the cheapest expression control on the rig */}
          <path
            d={`M ${-H * 0.46} ${-H * 0.24 + brow * H * 0.05} q ${H * 0.14} ${-H * 0.06 - brow * H * 0.04} ${H * 0.26} 0`}
            stroke={ink}
            strokeWidth={3.4}
            fill="none"
            strokeLinecap="round"
            opacity={0.85}
          />
          <path
            d={`M ${H * 0.2} ${-H * 0.24 + brow * H * 0.05} q ${H * 0.14} ${-H * 0.06 - brow * H * 0.04} ${H * 0.26} 0`}
            stroke={ink}
            strokeWidth={3.4}
            fill="none"
            strokeLinecap="round"
            opacity={0.85}
          />

          <ellipse cx={-H * 0.34} cy={-H * 0.06} rx={H * 0.085} ry={Math.max(0.6, H * 0.105 * (1 - blink))} fill={ink} />
          <ellipse cx={H * 0.34} cy={-H * 0.06} rx={H * 0.085} ry={Math.max(0.6, H * 0.105 * (1 - blink))} fill={ink} />

          <ellipse cx={0} cy={H * 0.22} rx={H * 0.1} ry={H * 0.065} fill="none" stroke={ink} strokeWidth={2.2} />

          <path
            d={`M ${-H * 0.19} ${H * 0.44} Q 0 ${H * (0.44 + 0.22 * mouth)} ${H * 0.19} ${H * 0.44}`}
            fill={mouth > 0.4 ? ink : "none"}
            stroke={ink}
            strokeWidth={2.8}
            strokeLinecap="round"
          />
          </g>

          {spec.facialHair === "moustache" ? (
            <path d={`M ${-H * 0.24} ${H * 0.33} Q 0 ${H * 0.24} ${H * 0.24} ${H * 0.33}`} stroke={ink} strokeWidth={5} fill="none" strokeLinecap="round" />
          ) : null}
          {spec.facialHair === "beard" ? (
            <path
              d={`M ${-H * 0.4} ${H * 0.58} Q 0 ${H * 1.12} ${H * 0.4} ${H * 0.58} Q 0 ${H * 0.74} ${-H * 0.4} ${H * 0.58} Z`}
              fill={spec.coatDark}
              stroke={ink}
              strokeWidth={2.6}
              opacity={0.92}
            />
          ) : null}

          {/* hair peeking from under the headwear */}
          {spec.hatStyle !== "bald" ? (
            <g fill={spec.hairStyle === "curls" ? spec.coatDark : "#3a2c2c"} opacity={0.9}>
              <path d={`M ${-H * 0.98} ${-H * 0.16} q ${-H * 0.04} ${H * 0.2} ${H * 0.08} ${H * 0.3}`} stroke={spec.coatDark} strokeWidth={H * 0.1} fill="none" strokeLinecap="round" />
              <path d={`M ${H * 0.98} ${-H * 0.16} q ${H * 0.04} ${H * 0.2} ${-H * 0.08} ${H * 0.3}`} stroke={spec.coatDark} strokeWidth={H * 0.1} fill="none" strokeLinecap="round" />
            </g>
          ) : null}

          {spec.hatStyle === "beanie" ? (
            <g>
              <path
                d={`M ${-H * 1.01} ${-H * 0.24} A ${H * 1.01} ${H * 1.01} 0 0 1 ${H * 1.01} ${-H * 0.24} Z`}
                fill={spec.hat}
                stroke={ink}
                strokeWidth={3.8}
              />
              <path
                d={`M ${-H * 0.9} ${-H * 0.52} A ${H * 0.9} ${H * 0.9} 0 0 1 ${H * 0.55} ${-H * 0.78}`}
                stroke="rgba(255,255,255,0.45)"
                strokeWidth={5}
                fill="none"
                strokeLinecap="round"
              />
              {/* The band sits on the brim, above the brows. At -0.36H..-0.10H
                  it covered the eye line, so the face lost its strongest
                  identity cue exactly when the shot got close. */}
              <rect
                x={-H * 1.04}
                y={-H * 0.52}
                width={H * 2.08}
                height={H * 0.25}
                rx={H * 0.12}
                fill={spec.hatBand}
                stroke={ink}
                strokeWidth={3.2}
              />
            </g>
          ) : null}
          {spec.hatStyle === "cap" ? (
            <g>
              <path d={`M ${-H * 0.98} ${-H * 0.28} Q 0 ${-H * 1.3} ${H * 0.98} ${-H * 0.28} Z`} fill={spec.hat} stroke={ink} strokeWidth={3.8} />
              <path
                d={`M ${H * 0.2} ${-H * 0.42} Q ${H * 1.42} ${-H * 0.44} ${H * 1.2} ${-H * 0.16} Q ${H * 0.6} ${-H * 0.24} ${H * 0.2} ${-H * 0.32} Z`}
                fill={spec.hatBand}
                stroke={ink}
                strokeWidth={2.8}
              />
            </g>
          ) : null}
          {spec.hatStyle === "scarf" ? (
            <g>
              <path d={`M ${-H * 0.98} ${-H * 0.16} Q 0 ${-H * 0.62} ${H * 0.98} ${-H * 0.16}`} stroke={spec.hat} strokeWidth={H * 0.22} fill="none" strokeLinecap="round" />
              <path d={`M ${H * 0.62} ${-H * 0.06} q ${H * 0.46} ${H * 0.36} ${H * 0.3} ${H * 0.92}`} stroke={spec.hat} strokeWidth={H * 0.16} fill="none" strokeLinecap="round" />
            </g>
          ) : null}
          {spec.hatStyle === "bald" && spec.hairStyle === "curls" ? (
            <g fill={spec.coatDark} stroke={ink} strokeWidth={2.6}>
              <circle cx={-H * 0.66} cy={-H * 0.52} r={H * 0.28} />
              <circle cx={0} cy={-H * 0.8} r={H * 0.32} />
              <circle cx={H * 0.66} cy={-H * 0.52} r={H * 0.28} />
            </g>
          ) : null}
          {spec.hatStyle === "bald" && spec.hairStyle === "side" ? (
            <path
              d={`M ${-H * 0.98} ${-H * 0.4} Q ${-H * 0.2} ${-H * 1.14} ${H * 0.8} ${-H * 0.48} Q ${H * 0.2} ${-H * 0.76} ${-H * 0.98} ${-H * 0.4}`}
              fill={spec.coatDark}
              stroke={ink}
              strokeWidth={2.8}
            />
          ) : null}
        </g>
      </g>

      {hold === "rope" ? (
        <g transform={`translate(-42 ${shoulderY})`}>
          <path d="M 3 72 q -18 70 10 110" stroke="#cbb59a" strokeWidth={4} fill="none" strokeLinecap="round" />
        </g>
      ) : null}
    </g>
  );
};
