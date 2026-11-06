/**
 * One-point perspective room maths.
 *
 * Adapted (MIT) from the external repository's `engine/room.tsx`: a point is
 * (u across, v down, w toward camera), u/v on the back wall's box, w = 0 on the
 * back wall and 1 at the near plane. Equal steps in w are equal steps in depth,
 * which is what makes a floor read as a floor instead of a gradient.
 */

export type Pt = { x: number; y: number };
export type V3 = [number, number, number];

export const pts = (list: Pt[]) => list.map((p) => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(" ");

export type Room = ReturnType<typeof makeRoom>;

export const makeRoom = (vp: Pt, back: { x0: number; x1: number; y0: number; y1: number }, depth = 3.4) => {
  const scaleAt = (w: number) => 1 / (1 + (1 / depth - 1) * w);
  const P = (u: number, v: number, w: number): Pt => {
    const k = scaleAt(w);
    return {
      x: vp.x + (back.x0 + (back.x1 - back.x0) * u - vp.x) * k,
      y: vp.y + (back.y0 + (back.y1 - back.y0) * v - vp.y) * k,
    };
  };
  const Q = (corners: V3[]) => pts(corners.map(([u, v, w]) => P(u, v, w)));
  return { vp, back, depth, scaleAt, P, Q };
};

/** A quad in room space: four (u, v, w) corners. */
export const quad = (r: Room, corners: V3[]) => r.Q(corners);

/** A point on the floor (v = 1) at depth w, for standing objects. */
export const onFloor = (r: Room, u: number, w: number): Pt => r.P(u, 1, w);

/** How much a body at depth w shrinks relative to the near plane. */
export const depthScale = (r: Room, w: number) => r.scaleAt(w);
