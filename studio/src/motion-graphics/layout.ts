import type { ActorSpec } from "../composition/Actors";
import { cast } from "../characters/cast";
import { RIG } from "../characters/geometry";
import type { Box, OverlaySpec } from "./spec";
import { DEFAULT_BOX } from "./spec";

export type Frame = { width: number; height: number };
export type ActorAnchorBox = {
  head: { x: number; y: number; r: number };
  chest: { x: number; y: number };
  feet: { x: number; y: number };
  facing: 1 | -1;
  top: number;
  bottom: number;
};

/** Safe area: 6% margin, the same band the captions respect. */
export const SAFE = 0.06;

/**
 * Resolve an actor's body geometry in stage coordinates (1080x1920, the rig's
 * own viewBox). The maths mirrors Character.tsx exactly: the rig is drawn from
 * a body top of -226 and a head centre at -226 - H*0.94, then scaled.
 */
export const actorAnchor = (actor: ActorSpec, headRadius: number = RIG.headRadius, height = 1): ActorAnchorBox => {
  const h = headRadius;
  const headCY = RIG.bodyTop - h * RIG.headOffset;
  const x = actor.x;
  const y = actor.y;
  const s = actor.scale * height;
  return {
    head: { x: x, y: y + headCY * s, r: h * s },
    chest: { x: x, y: y + (RIG.bodyTop + 60) * s },
    feet: { x: x, y: y + RIG.footY * s },
    facing: actor.facing,
    top: y + (headCY - h) * s,
    bottom: y + RIG.footY * s,
  };
};

const clampBox = (box: Box, safe: boolean): Box => {
  const mx = safe ? SAFE : 0;
  const w = Math.min(box.w, 1 - mx * 2);
  const h = Math.min(box.h, 1 - mx * 2);
  return {
    w,
    h,
    x: Math.min(1 - mx - w, Math.max(mx, box.x)),
    y: Math.min(1 - mx - h, Math.max(mx, box.y)),
  };
};

/**
 * Place a box next to an actor without covering the face.
 *
 * Order of preference: above the head, beside the body on the side the actor
 * faces away from, then below the feet. Every candidate is clamped to the safe
 * area; if none fits, the first one wins and the inspector reports the squeeze
 * instead of the layout silently stacking a label on the eyes.
 */
export const placeNearActor = (
  anchor: ActorAnchorBox,
  size: { w: number; h: number },
  frame: Frame,
  at: "head" | "chest" | "feet" = "head",
): Box => {
  const gap = 28;
  const wPx = size.w * frame.width;
  const hPx = size.h * frame.height;
  const above = { x: anchor.head.x / frame.width - size.w / 2, y: (anchor.top - gap - hPx) / frame.height, w: size.w, h: size.h };
  const below = { x: anchor.head.x / frame.width - size.w / 2, y: (anchor.bottom + gap) / frame.height, w: size.w, h: size.h };
  const sideX = anchor.facing === 1 ? anchor.head.x + anchor.head.r + gap : anchor.head.x - anchor.head.r - gap - wPx;
  const side = { x: sideX / frame.width, y: (anchor.head.y - hPx * 0.5) / frame.height, w: size.w, h: size.h };
  const candidates = at === "feet" ? [below, side, above] : [above, side, below];
  for (const candidate of candidates) {
    const inside =
      candidate.x >= SAFE && candidate.y >= SAFE && candidate.x + candidate.w <= 1 - SAFE && candidate.y + candidate.h <= 1 - SAFE;
    if (inside) return candidate;
  }
  return clampBox(candidates[0], true);
};

/** Resolve the final box of an overlay given the shot cast and the frame size. */
export const resolveBox = (
  spec: OverlaySpec,
  actors: ActorSpec[],
  frame: Frame,
): { box: Box; anchor?: ActorAnchorBox } => {
  const size = spec.box ?? DEFAULT_BOX[spec.type];
  const placement = spec.placement;
  if (placement.kind === "actor") {
    const actor = actors.find((a) => a.id === placement.actor);
    if (!actor) return { box: clampBox(size, spec.safe !== false) };
    const identity = cast[actor.id];
    const anchor = actorAnchor(actor, identity?.headRadius ?? RIG.headRadius, identity?.height ?? 1);
    const box = placeNearActor(anchor, { w: size.w, h: size.h }, frame, placement.at ?? "head");
    const dx = placement.offset?.x ?? 0;
    const dy = placement.offset?.y ?? 0;
    return {
      box: clampBox({ ...box, x: box.x + dx, y: box.y + dy }, spec.safe !== false),
      anchor,
    };
  }
  return { box: clampBox({ ...size, ...(placement.box ?? {}) }, spec.safe !== false) };
};

/** Screen-space rectangle in pixels, for pixel inspection and tests. */
export const toPixels = (box: Box, frame: Frame) => ({
  left: Math.round(box.x * frame.width),
  top: Math.round(box.y * frame.height),
  width: Math.round(box.w * frame.width),
  height: Math.round(box.h * frame.height),
});

/** Do two boxes intersect by more than `pad` (normalised)? */
export const overlaps = (a: Box, b: Box, pad = 0) =>
  a.x + pad < b.x + b.w && b.x + pad < a.x + a.w && a.y + pad < b.y + b.h && b.y + pad < a.y + a.h;
