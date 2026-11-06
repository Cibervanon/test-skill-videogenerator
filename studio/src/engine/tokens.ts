/**
 * Style tokens extracted from the reference corpus (see references/measurements.json).
 * Nothing here is invented: the palettes come from k-means runs over the three
 * reference videos, the timings from the measured shot list.
 */

export type Palette = {
  id: string;
  skyTop: string;
  skyBottom: string;
  ground: string;
  groundShadow: string;
  structure: string;
  structureLight: string;
  structureDark: string;
  accentWarm: string;
  accentCool: string;
  haze: string;
};

export const ink = "#241a2b";
export const inkSoft = "rgba(36,26,43,0.55)";
export const skin = "#f7f0e2";
export const blush = "#e9a18e";
export const coatRed = "#b8423f";
export const coatTeal = "#2f6f63";
export const coatOchre = "#c8892f";

export const palettes: Record<string, Palette> = {
  // Night town: measured dominant blues (#1d2a52 / #2c3a6b) + warm window pools.
  nightTown: {
    id: "nightTown",
    skyTop: "#101733",
    skyBottom: "#3b3f74",
    ground: "#c9d3e8",
    groundShadow: "#8f9dc4",
    structure: "#2b3360",
    structureLight: "#3d4778",
    structureDark: "#171c3b",
    accentWarm: "#ffb765",
    accentCool: "#8fb3e8",
    haze: "#5a5f96",
  },
  // Candle-lit interior: measured crimson/plum with amber key light.
  interior: {
    id: "interior",
    skyTop: "#2a1b25",
    skyBottom: "#4a2b34",
    ground: "#6d4636",
    groundShadow: "#3d2620",
    structure: "#4b2c33",
    structureLight: "#6b3d3f",
    structureDark: "#241319",
    accentWarm: "#ffc07a",
    accentCool: "#7f8fc4",
    haze: "#7a4a4a",
  },
  // Dawn field: measured peach sky, cream snow, cold pine silhouettes.
  dawnField: {
    id: "dawnField",
    skyTop: "#e8896a",
    skyBottom: "#ffd9a8",
    ground: "#f3e2cf",
    groundShadow: "#cbb29c",
    structure: "#5d4b46",
    structureLight: "#7d655c",
    structureDark: "#33262a",
    accentWarm: "#fff0c4",
    accentCool: "#9fb6c9",
    haze: "#f0b48f",
  },
};

/** Measured rhythm of the reference corpus: long takes, slow moves, few cuts. */
export const rhythm = {
  medianShotSeconds: 6.4,
  meanShotSeconds: 8.1,
  maxShotSeconds: 21.0,
  cutsPerMinuteSoft: 6.6,
  /** Word-chunk size used by the burned-in captions (2-3 words per beat). */
  captionWordsPerChunk: 3,
  captionY: 0.885,
};

export const typography = {
  captionFamily:
    '"Nunito", "Trebuchet MS", "Segoe UI", system-ui, -apple-system, sans-serif',
  captionSize: 52,
  captionStroke: 7,
  captionShadow: "0 6px 18px rgba(10,6,16,0.65)",
  titleFamily: '"Georgia", "Times New Roman", serif',
};
