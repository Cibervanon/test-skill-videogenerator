import React from "react";
import { useVideoConfig } from "remotion";
import type { ActorSpec } from "../composition/Actors";
import { BarChart, Counter, DonutChart, LineChart, Process, Ranking } from "./charts";
import { Arrow, Badge, Callout, Highlight, Hud, LabelTag, Panel } from "./annotations";
import { OverlayFrame } from "./Frame";
import { BridgeCard } from "./modes";
import { resolveBox } from "./layout";
import type { OverlaySpec, PresentationMode } from "./spec";

/**
 * One dispatcher for every overlay. A manifest drives it; an unknown type is a
 * loud error, never an empty frame that reaches the render.
 */
const COMPONENTS: Record<string, React.FC<{ spec: OverlaySpec; box: { x: number; y: number; w: number; h: number }; p: number; frames: number }>> = {
  label: LabelTag,
  callout: Callout,
  badge: Badge,
  panel: Panel,
  hud: Hud,
  highlight: Highlight,
  arrow: Arrow,
  counter: Counter,
  bar: BarChart,
  donut: DonutChart,
  line: LineChart,
  ranking: Ranking,
  process: Process,
};

export const OverlayLayer: React.FC<{
  overlays: OverlaySpec[];
  actors: ActorSpec[];
  frames: number;
  p: number;
  /** "actor" renders inside the camera transform so labels stay glued to bodies. */
  layer: "actor" | "screen";
  /** The director's mode for the shot: F replaces the component with the bridge card. */
  mode?: PresentationMode;
}> = ({ overlays, actors, frames, p, layer, mode = "B" }) => {
  const { width, height } = useVideoConfig();
  const frameSize = { width, height };
  if (mode === "E" && layer === "actor") return null;
  const visible = overlays.filter((o) => (layer === "actor" ? o.placement.kind === "actor" : o.placement.kind === "screen"));
  return (
    <>
      {visible.map((spec) => {
        const Component = mode === "F" ? BridgeCard : COMPONENTS[spec.type];
        if (!Component) throw new Error(`Unknown overlay type "${spec.type}" — add it to motion-graphics/OverlayLayer.tsx`);
        const { box } = resolveBox(spec, actors, frameSize);
        return (
          <OverlayFrame key={spec.id} spec={spec} box={box} p={p} frames={frames}>
            <Component spec={spec} box={box} p={p} frames={frames} />
          </OverlayFrame>
        );
      })}
    </>
  );
};
