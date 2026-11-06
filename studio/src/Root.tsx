import React from "react";
import { Composition } from "remotion";
import project from "./data/project.json";
import assetForgeProject from "../../projects/asset_forge/manifest.json";
import { CinematicDemo, CinematicProject, totalFrames, type DemoProject } from "./composition/Demo";
import { CastSheet } from "./composition/CastSheet";
import { IdentitySheet } from "./composition/IdentitySheet";

const proofProject = assetForgeProject as unknown as DemoProject;
const AssetForgeDemo: React.FC = () => <CinematicProject project={proofProject} />;

export const RemotionRoot: React.FC = () => (
  <>
    <Composition
      id="CinematicDemo"
      component={CinematicDemo}
      durationInFrames={totalFrames()}
      fps={project.format.fps}
      width={project.format.width}
      height={project.format.height}
    />
    <Composition
      id="AssetForgeDemo"
      component={AssetForgeDemo}
      durationInFrames={totalFrames(proofProject)}
      fps={proofProject.format.fps}
      width={proofProject.format.width}
      height={proofProject.format.height}
    />
    <Composition id="CastSheet" component={CastSheet} durationInFrames={1} fps={30} width={1400} height={860} />
    <Composition id="IdentitySheet" component={IdentitySheet} durationInFrames={1} fps={30} width={2100} height={1300} />
  </>
);
