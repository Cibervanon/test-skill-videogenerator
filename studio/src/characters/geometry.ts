/**
 * Rig geometry shared by the renderer and the overlay layout.
 *
 * These numbers define where the head, shoulders and feet actually are. The
 * character component and the label placement both read this object, so a
 * change to the rig cannot leave labels floating next to the wrong body part.
 */
export const RIG = {
  bodyTop: -226,
  shoulderY: -200,
  hem: -56,
  footY: 6,
  /** Head radius factor used for the head centre. */
  headOffset: 0.94,
  headRadius: 46,
} as const;
