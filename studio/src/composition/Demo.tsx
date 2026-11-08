import React, { useMemo } from "react";
import { AbsoluteFill, Sequence, useCurrentFrame } from "remotion";
import activeProject from "../data/project.json";
import { CameraRig } from "../engine/CameraRig";
import { FilmFinish } from "../engine/FilmFinish";
import { buildCues, Captions, type TimedCaptionCue } from "../engine/Subtitles";
import { clamp } from "../engine/math";
import { StyleProvider } from "../engine/styles";
import { ExplainerBackdrop, OverlayLayer, Scrim } from "../motion-graphics";
import type { OverlaySpec, ShotPresentation } from "../motion-graphics";
import { Actor, type ActorSpec } from "./Actors";
import { TownNight } from "../scenes/TownNight";
import { Doorway } from "../scenes/Doorway";
import { FaceCloseup } from "../scenes/FaceCloseup";
import { FieldDawn } from "../scenes/FieldDawn";
import { BellInsert } from "../scenes/BellInsert";
import { Workshop } from "../scenes/Workshop";
import { Greenhouse } from "../scenes/Greenhouse";
import { GeneratedScene } from "../generated/GeneratedScene";
import { PropLayer } from "../generated/PropLayer";
import generated from "../data/generated_assets.json";
import type { GeneratedProp, GeneratedSet, PropPlacement } from "../generated/types";

type Shot = {
  id: string;
  scene: string;
  camera: string;
  cameraIntensity?: number;
  seconds: number;
  line?: string;
  transitionIn?: number;
  /** Word-timed cues from the take (shot-local seconds); falls back if absent. */
  captions?: TimedCaptionCue[];
  overlays?: OverlaySpec[];
  props?: PropPlacement[];
  offsetX?: number;
  offsetY?: number;
  zoom?: number;
  state?: "table" | "held" | "pour" | "bloom";
  actors?: ActorSpec[];
  presentation?: ShotPresentation;
};

export type DemoProject = {
  id?: string;
  title?: string;
  style?: string;
  format: { width: number; height: number; fps: number; aspect: string };
  transitionFrames?: number;
  shots: Shot[];
};

const active = activeProject as unknown as DemoProject;

const envs: Record<string, React.FC<{ progress: number; state?: "table" | "held" | "pour" | "bloom" | "left" }>> = {
  townNight: TownNight,
  doorway: Doorway,
  faceCloseup: FaceCloseup,
  fieldDawn: FieldDawn,
  bellInsert: BellInsert,
  workshop: Workshop,
  greenhouse: Greenhouse,
};

const generatedSets = (generated as unknown as { sets?: Record<string, GeneratedSet> }).sets ?? {};
const generatedProps = (generated as unknown as { props?: Record<string, GeneratedProp> }).props ?? {};

export const fps = active.format.fps;
export const shotFrames = (seconds: number, atFps: number = fps) => Math.round(seconds * atFps);

/**
 * Transition rule: a dissolve between two framings of the SAME subject at very
 * different scales produces a double exposure, so each boundary declares its own
 * transition:
 *   - cut      → subject continues, framing changes hard (0 frames of overlap)
 *   - dissolve → different setup, different subject or location
 */
const transitionIn = (shot: Shot, project: DemoProject): number => shot.transitionIn ?? project.transitionFrames ?? 0;

export const shotTimeline = (project: DemoProject = active) => {
  const shots = project.shots;
  let cursor = 0;
  return shots.map((shot, i) => {
    const frames = shotFrames(shot.seconds, project.format.fps);
    const entry = { shot, from: cursor, frames, transIn: transitionIn(shot, project) };
    const nextTrans = i + 1 < shots.length ? transitionIn(shots[i + 1], project) : 0;
    cursor += frames - nextTrans;
    return entry;
  });
};

export const totalFrames = (project: DemoProject = active) => {
  const timeline = shotTimeline(project);
  const last = timeline[timeline.length - 1];
  return last ? last.from + last.frames : 1;
};

const ShotView: React.FC<{ shot: Shot; index: number; frames: number; transIn: number }> = ({
  shot,
  index,
  frames,
  transIn,
}) => {
  const frame = useCurrentFrame();
  const p = clamp(frame / Math.max(1, frames - 1));
  const Env = envs[shot.scene];
  const generatedSet = generatedSets[shot.scene];
  if (!Env && !generatedSet) {
    throw new Error(`Unknown scene "${shot.scene}" — add it to composition/Demo.tsx or the generated asset library`);
  }

  const cues = useMemo(
    () => buildCues(shot.line ?? "", 0, frames, shot.captions, fps),
    [shot.line, shot.captions, frames],
  );
  const overlays = useMemo(() => (shot.overlays ?? []) as OverlaySpec[], [shot.overlays]);
  const props = useMemo(() => (shot.props ?? []) as PropPlacement[], [shot.props]);
  const actors = (shot.actors ?? []) as ActorSpec[];
  const mode = shot.presentation?.mode ?? (overlays.length ? "B" : "A");
  const opacity = index === 0 || transIn === 0 ? 1 : clamp(frame / transIn);

  return (
    <AbsoluteFill style={{ opacity }}>
      {/* Mode E owns the frame: the set and the cast step out on purpose. */}
      {mode === "E" ? (
        <ExplainerBackdrop />
      ) : (
        <CameraRig move={shot.camera as never} progress={p} offsetX={shot.offsetX ?? 0} offsetY={shot.offsetY ?? 0} zoom={shot.zoom ?? 1} intensity={shot.cameraIntensity ?? 1}>
          {generatedSet ? <GeneratedScene spec={generatedSet} progress={p} /> : Env ? <Env progress={p} state={shot.state} /> : null}
          <PropLayer props={props} specs={generatedProps} layer="back" />
          {/* Actors live in their own SVG layer: a `<g>` outside an `<svg>` is
              ignored by the browser, and a silent missing cast is worse than a
              render error. */}
          <svg
            viewBox="0 0 1080 1920"
            preserveAspectRatio="xMidYMid slice"
            style={{ position: "absolute", inset: 0, width: "100%", height: "100%", overflow: "visible" }}
          >
            {actors.map((actor, i) => (
              <Actor key={`${shot.id}-${actor.id}-${i}`} spec={actor} progress={p} />
            ))}
          </svg>
          <PropLayer props={props} specs={generatedProps} layer="front" />
          {/* Labels follow a body, so they live inside the camera transform. */}
          <OverlayLayer overlays={overlays} actors={actors} frames={frames} p={p} layer="actor" mode={mode} />
        </CameraRig>
      )}
      {/* Mode D keeps the scene visible under a scrim: the data leads. */}
      {mode === "D" ? <Scrim opacity={shot.presentation?.scrim ?? 0.58} /> : null}
      {/* Panels, HUD and charts are screen-space: a camera move must not skew
          the data a viewer is reading. */}
      <OverlayLayer overlays={overlays} actors={actors} frames={frames} p={p} layer="screen" mode={mode} />
      <Captions cues={cues} />
    </AbsoluteFill>
  );
};

export const CinematicProject: React.FC<{ project: DemoProject }> = ({ project }) => {
  const timeline = shotTimeline(project);
  return (
    <StyleProvider id={project.style}>
      <AbsoluteFill style={{ backgroundColor: "#08060d" }}>
        {timeline.map(({ shot, from, frames, transIn }, index) => (
          <Sequence key={shot.id} from={from} durationInFrames={frames} name={`${shot.id} · ${shot.scene}`}>
            <ShotView shot={shot} index={index} frames={frames} transIn={transIn} />
          </Sequence>
        ))}
        <FilmFinish grain={0.14} vignette={0.6} />
      </AbsoluteFill>
    </StyleProvider>
  );
};

export const CinematicDemo: React.FC = () => <CinematicProject project={active} />;
