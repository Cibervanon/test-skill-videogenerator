import React from "react";
import { useCurrentFrame } from "remotion";
import { Character } from "../characters/Character";
import { cast } from "../characters/cast";
import generated from "../data/generated_assets.json";
import { clamp, easeInOutCubic, lerp, settle, smoothstep } from "../engine/math";
import type { GeneratedExpression } from "../generated/types";

export type ActorSpec = {
  id: string;
  preset: "idle" | "walkIn" | "closeup" | "dig" | "reach" | "turn" | "call";
  x: number;
  y: number;
  scale: number;
  facing: 1 | -1;
  from?: number;
  to?: number;
  start?: number;
  end?: number;
  hold?: "none" | "shovel" | "lantern" | "rope" | "bell";
  armR?: number;
  phase?: number;
  /** Reusable generated expression id, with or without the `expression:` prefix. */
  expression?: string;
  /** Seconds-ish offset so two actors do not perform in lockstep. */
  offset?: number;
};

/** Blink curve: 5-frame close, every ~3.2s, phase-shifted per actor. */
const blinkAt = (frame: number, offset: number) => {
  const cycle = 96;
  const local = (frame + offset) % cycle;
  if (local < 4) return local / 4;
  if (local < 8) return 1 - (local - 4) / 4;
  return 0;
};

/**
 * Performance presets. Motion is expressed as intent (walk, dig, hold) and
 * resolved per frame, so a shot can be re-timed without re-animating.
 */
type Acting = {
  gait: number;
  phase: number;
  blink: number;
  mouth: number;
  headTilt: number;
  lean: number;
  breath: number;
  armL: number;
  armR: number;
  brow: number;
  x?: number;
  yaw: number;
  elbowL?: number;
  elbowR?: number;
  handL: "open" | "point" | "fist";
  handR: "open" | "point" | "fist";
};

const perform = (spec: ActorSpec, frame: number, p: number): Acting => {
  const base: Acting = {
    gait: 0,
    phase: spec.phase ?? 0,
    blink: blinkAt(frame, (spec.id.charCodeAt(0) * 13) % 96),
    mouth: 0.08,
    headTilt: 0,
    lean: 0,
    breath: Math.sin(frame / 26),
    armL: 8,
    armR: spec.armR ?? -8,
    brow: 0,
    yaw: 0,
    handL: "open",
    handR: spec.hold && spec.hold !== "none" ? "fist" : "open",
  };

  switch (spec.preset) {
    case "walkIn": {
      const t = clamp((p - (spec.start ?? 0)) / Math.max(0.001, (spec.end ?? 0.9) - (spec.start ?? 0)));
      const x = lerp(spec.from ?? -200, spec.to ?? 0, easeInOutCubic(t));
      // Acceleration and deceleration are separate beats: a walk that snaps to
      // full gait on frame one reads mechanical. Ramp in over the first 12% and
      // out over the last 14%, then let the body settle when the foot lands.
      const gait = 0.06 + 0.84 * smoothstep(0, 0.12, t) * (1 - smoothstep(0.86, 1, t));
      const landed = t > 0.86 ? settle((t - 0.86) * 40, 2.6, 1.5, 5) : 0;
      return {
        ...base,
        x: spec.x + x,
        gait,
        phase: frame / 6.4,
        lean: 2 * smoothstep(0, 0.12, t) * (1 - smoothstep(0.8, 1, t)),
        headTilt: Math.sin(frame / 44) * 2 + landed,
        brow: t > 0.7 ? 0.12 : 0,
      };
    }
    case "dig": {
      const swing = Math.sin(frame / 7.2);
      // The strike overshoots and rebounds: an arc with a hit at the bottom,
      // not a pendulum. settle() carries the recoil after each impact.
      const hit = Math.max(0, -swing);
      return {
        ...base,
        gait: 0,
        phase: 0,
        armR: -34 + swing * 46 + settle(hit * 6, 4, 2.2, 4),
        armL: 14 - swing * 10,
        lean: 7 + hit * 2,
        headTilt: 11 + Math.sin(frame / 9) * 2 - hit * 1.5,
        breath: Math.sin(frame / 18) * 1.4 + hit * 0.8,
        mouth: 0.2,
        brow: 0.18,
      };
    }
    case "reach": {
      // A reach with the beat structure the old presets lacked: anticipation,
      // travel, overshoot, settle, hold. Pure function of the shot clock.
      const t = clamp(p * 1.35 - 0.1);
      const travel = easeInOutCubic(clamp((t - 0.18) / 0.5));
      const overshoot = t > 0.55 ? settle((t - 0.55) * 26, 9, 1.7, 4) : 0;
      const armR = -18 - travel * 96 - overshoot;
      return {
        ...base,
        gait: 0,
        armR,
        elbowR: -6 - travel * 16,
        handR: "point",
        armL: 6 + travel * 6,
        lean: -3 * travel,
        headTilt: -6 * travel,
        yaw: 0.45 * travel,
        brow: 0.3 * travel,
        mouth: 0.14 + 0.1 * travel,
      };
    }
    case "turn": {
      // Attention: shoulders lead, head turns, then the eyes settle. No head spin.
      const t = clamp(p * 1.2 - 0.05);
      const swing = easeInOutCubic(clamp(t / 0.55));
      const hold = Math.sin((p - 0.55) * 6.2) * 1.1 * (p > 0.55 ? 1 : 0);
      return {
        ...base,
        gait: 0,
        yaw: -0.7 * swing + hold * 0.02,
        headTilt: -5 * swing + hold,
        lean: -1.5 * swing,
        armL: 7 - 3 * swing,
        armR: (spec.armR ?? -8) + 4 * swing,
        brow: -0.25 * swing,
        mouth: 0.1,
      };
    }
    case "call": {
      // Calling out: arm up on an arc, chest lifts, jaw opens, then a recovery.
      const t = clamp(p * 1.3 - 0.08);
      const up = easeInOutCubic(clamp((t - 0.1) / 0.45));
      const impact = t > 0.5 ? settle((t - 0.5) * 24, 7, 1.9, 4) : 0;
      return {
        ...base,
        gait: 0,
        armL: 8 + up * 122 + impact,
        elbowL: -8 - up * 18,
        handL: "open",
        lean: 3 * up,
        headTilt: -8 * up,
        yaw: 0.2 * up,
        brow: 0.45 * up,
        mouth: 0.15 + 0.55 * up * (0.7 + 0.3 * Math.sin(frame / 5)),
        breath: Math.sin(frame / 18) * 1.6,
      };
    }
    case "closeup": {
      return {
        ...base,
        gait: 0,
        headTilt: Math.sin(frame / 62) * 1.6,
        breath: Math.sin(frame / 34) * 1.1,
        mouth: 0.12 + 0.05 * Math.sin(frame / 27),
        armL: 6,
        armR: -6,
        // a held, concerned brow is what makes the close-up read as a thought
        brow: -0.55 + Math.sin(frame / 90) * 0.08,
      };
    }
    case "idle":
    default:
      return {
        ...base,
        gait: 0.05,
        phase: frame / 90,
        headTilt: Math.sin(frame / 50) * 1.8,
        mouth: 0.1,
      };
  }
};

export const Actor: React.FC<{ spec: ActorSpec; progress: number }> = ({ spec, progress }) => {
  const frame = useCurrentFrame();
  const character = cast[spec.id];
  if (!character) {
    // Fail loudly at render time instead of silently drawing nothing.
    throw new Error(`Unknown character id "${spec.id}" — add it to characters/cast.ts`);
  }
  const expressions = (generated as unknown as { expressions?: Record<string, GeneratedExpression> }).expressions ?? {};
  const expression = spec.expression ? expressions[spec.expression.replace(/^expression:/, "")] : undefined;
  if (spec.expression && !expression) {
    throw new Error(`Unknown expression "${spec.expression}" — add it to the generated asset library`);
  }
  const acting = { ...perform(spec, frame, progress), ...(expression?.values ?? {}) };
  return (
    <Character
      spec={character}
      x={acting.x ?? spec.x}
      y={spec.y}
      scale={spec.scale}
      facing={spec.facing}
      gait={acting.gait}
      phase={acting.phase}
      armL={acting.armL}
      armR={acting.armR}
      headTilt={acting.headTilt}
      blink={acting.blink}
      mouth={acting.mouth}
      lean={acting.lean}
      breath={acting.breath}
      brow={acting.brow}
      yaw={acting.yaw}
      elbowL={acting.elbowL}
      elbowR={acting.elbowR}
      handL={acting.handL}
      handR={acting.handR}
      hold={spec.hold ?? "none"}
    />
  );
};
