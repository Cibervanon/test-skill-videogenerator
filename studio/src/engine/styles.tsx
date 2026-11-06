import React from "react";
import data from "../data/styles.json";

/**
 * Style system.
 *
 * A style is a token set, never a second engine: the same scenes, rig, camera
 * and subtitle stack render in every style. `styles.json` is the single source
 * of truth and is also read by the Python side (inspection + director), so a
 * style cannot exist in one place and be missing in the other.
 */

export type StyleId = "cinematic" | "editorial" | "infographic" | "minimal" | "cartoon";

export type Style = {
  id: StyleId;
  name: string;
  use_when: string;
  palette: Record<
    "ink" | "paper" | "text" | "muted" | "accent" | "accentAlt" | "warn" | "surface" | "surfaceStrong" | "line",
    string
  >;
  type: {
    display: string;
    ui: string;
    mono: string;
    titleSize: number;
    labelSize: number;
    microSize: number;
    tracking: number;
  };
  ui: {
    density: "low" | "medium" | "high";
    radius: number;
    panel: "glass" | "paper" | "line";
    stroke: number;
    maxPanels: number;
    labelStyle: "leader" | "caption" | "tag" | "plain" | "bubble";
    backdropBlur: number;
  };
  graphics: {
    shade: "solid" | "flat";
    barShape: "rounded" | "square";
    grid: boolean;
    fillOpacity: number;
    strokeWidth: number;
    area: boolean;
  };
  camera: { energy: number };
  motion: { enterFrames: number; exitFrames: number; rise: number; kind: "rise" | "wipe" | "fade" | "pop" };
  transition: { defaultFrames: number };
};

type StyleFile = { default: string; styles: Record<string, Style> };
const file = data as unknown as StyleFile;

export const styles = file.styles;
export const styleIds = Object.keys(file.styles) as StyleId[];

export const getStyle = (id?: string | null): Style =>
  (id && file.styles[id]) || file.styles[file.default] || file.styles.cinematic;

const StyleContext = React.createContext<Style>(getStyle(null));

export const StyleProvider: React.FC<{ id?: string | null; children: React.ReactNode }> = ({ id, children }) => (
  <StyleContext.Provider value={getStyle(id)}>{children}</StyleContext.Provider>
);

export const useStyle = (): Style => React.useContext(StyleContext);
