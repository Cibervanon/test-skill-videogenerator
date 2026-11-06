/**
 * Overlay specification shared by motion graphics and character UI.
 *
 * Every overlay is data: a type, a placement, a time window and its payload.
 * Nothing here reads the DOM or the wall clock, so a given manifest always
 * renders the same frames.
 *
 * The *UI director* (scripts/acs/ui_director.py) decides the mode, the box and
 * the window, and writes them here; the renderer draws that decision.
 */

export type ActorAnchor = { actor: string; at?: "head" | "chest" | "feet" };

/** A 0..1 box. The director resolves semantic anchors to one of these. */
export type Box = { x: number; y: number; w: number; h: number };

export type Placement = { kind: "screen"; box?: Box } | ({ kind: "actor"; offset?: { x?: number; y?: number } } & ActorAnchor);

/** Presentation modes: how the shot hosts its information. */
export type PresentationMode = "A" | "B" | "C" | "D" | "E" | "F";

export type SemanticAnchor =
  | "top-left"
  | "top-right"
  | "top-center"
  | "mid-left"
  | "mid-right"
  | "center"
  | "bottom-left"
  | "bottom-right"
  | "bottom-center"
  | "above-character"
  | "beside-character";

/** The decision record the director attaches to a shot. */
export type ShotPresentation = {
  mode: PresentationMode;
  reason?: string;
  scrim?: number;
  independent?: boolean;
  bridge?: boolean;
};

/** The audit trail of one overlay. */
export type OverlayDecision = {
  intent?: string;
  mode?: PresentationMode;
  anchor?: string;
  reading_seconds?: number;
  window_seconds?: number;
  reason?: string;
};

export type OverlayType =
  | "label"
  | "callout"
  | "badge"
  | "panel"
  | "hud"
  | "highlight"
  | "arrow"
  | "counter"
  | "bar"
  | "donut"
  | "line"
  | "ranking"
  | "process";

export type SeriesPoint = { label: string; value: number; tone?: "accent" | "accentAlt" | "warn" };

export type OverlayData = {
  title?: string;
  caption?: string;
  unit?: string;
  decimals?: number;
  value?: number;
  from?: number;
  series?: SeriesPoint[];
  points?: number[];
  labels?: string[];
  rows?: SeriesPoint[];
  steps?: { label: string; detail?: string }[];
  segments?: SeriesPoint[];
  center?: string;
  name?: string;
  role?: string;
  status?: string;
  tone?: "accent" | "accentAlt" | "warn";
};

export type OverlaySpec = {
  id: string;
  type: OverlayType;
  placement: Placement;
  /** Semantic placement requested from the director ("auto" lets it choose). */
  anchor?: SemanticAnchor | "auto";
  /** Fractions of the shot duration (0..1). Defaults: 0.06 → 0.94. */
  from?: number;
  to?: number;
  /** Optional explicit box, overrides the default size of the type. */
  box?: Box;
  data?: OverlayData;
  /** Where the numbers come from. Required for numeric overlays. */
  source?: string;
  /** Explicit marker for a schematic value that is not a real measurement. */
  illustrative?: boolean;
  /** Force a different motion than the style default. */
  animation?: "rise" | "fade" | "wipe" | "pop";
  /** Keep the element inside the 6% safe area. Default true. */
  safe?: boolean;
  /** "bridge" asks the director for mode F (UI as the transition). */
  ui_role?: "bridge" | "required" | "optional";
  /** Written by the director: why this element exists. */
  ui?: OverlayDecision;
};

export const DEFAULT_WINDOW = { from: 0.06, to: 0.94 };

/** Default box (normalised) for each overlay type, chosen to respect 9:16. */
export const DEFAULT_BOX: Record<OverlayType, Box> = {
  label: { x: 0.08, y: 0.3, w: 0.6, h: 0.09 },
  callout: { x: 0.55, y: 0.62, w: 0.37, h: 0.13 },
  badge: { x: 0.08, y: 0.1, w: 0.42, h: 0.06 },
  panel: { x: 0.08, y: 0.55, w: 0.84, h: 0.24 },
  hud: { x: 0.06, y: 0.08, w: 0.88, h: 0.1 },
  highlight: { x: 0.42, y: 0.5, w: 0.32, h: 0.2 },
  arrow: { x: 0.2, y: 0.55, w: 0.5, h: 0.2 },
  counter: { x: 0.08, y: 0.62, w: 0.5, h: 0.16 },
  bar: { x: 0.08, y: 0.54, w: 0.84, h: 0.26 },
  donut: { x: 0.1, y: 0.54, w: 0.8, h: 0.26 },
  line: { x: 0.08, y: 0.54, w: 0.84, h: 0.26 },
  ranking: { x: 0.08, y: 0.46, w: 0.84, h: 0.34 },
  process: { x: 0.08, y: 0.62, w: 0.84, h: 0.2 },
};

/** Overlays that carry numbers and therefore need a source. */
export const NUMERIC_TYPES: OverlayType[] = ["counter", "bar", "donut", "line", "ranking"];

export const isNumeric = (spec: OverlaySpec) => NUMERIC_TYPES.includes(spec.type);
