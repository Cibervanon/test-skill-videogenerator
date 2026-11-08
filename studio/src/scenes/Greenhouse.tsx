import React from "react";
import { useCurrentFrame } from "remotion";
import { ParallaxGroup } from "../engine/CameraRig";
import { CastShadow, DustMotes, Glow, LightShaft, SoftBlurDefs } from "../engine/atmosphere";
import { MaterialDefs } from "../engine/texture";

const MAT = {
  wall: "#315247",
  wallLight: "#47695b",
  wallLine: "#1d352e",
  floor: "#4b4035",
  floorLine: "#2c241d",
  frame: "#d7c7a7",
  frameDark: "#8e795c",
  glass: "#8eb9ad",
  leaf: "#4d7a4c",
  leafDark: "#2f5535",
  leafDry: "#8e7948",
  pot: "#a96343",
  potDark: "#713d2c",
  water: "#75b8c4",
  metal: "#aab7b1",
  metalDark: "#5f726c",
  flower: "#f2d38c",
  ink: "#1d2822",
  sun: "#ffd49a",
  sky: "#334d5b",
};

type PlantState = "dry" | "bloom";

const Plant: React.FC<{ x: number; y: number; state: PlantState; frame: number }> = ({ x, y, state, frame }) => {
  const bloom = state === "bloom";
  const sway = Math.sin(frame / 44) * 1.4;
  const leaves = [
    { x: -34, y: -118, angle: -42, scale: 0.9 },
    { x: -10, y: -150, angle: -18, scale: 1.05 },
    { x: 20, y: -142, angle: 18, scale: 1.0 },
    { x: 42, y: -110, angle: 44, scale: 0.84 },
  ];
  return (
    <g transform={`translate(${x} ${y})`}>
      <CastShadow cx={0} cy={6} rx={82} ry={13} opacity={0.28} />
      <path d={`M -54 0 L -42 -74 L 42 -74 L 54 0 Z`} fill={MAT.pot} stroke={MAT.ink} strokeWidth={4} />
      <path d="M -42 -74 L 42 -74 L 42 -84 L -42 -84 Z" fill={MAT.potDark} stroke={MAT.ink} strokeWidth={3} />
      <path d="M -28 -66 Q 0 -54 28 -66" stroke="#d58c64" strokeWidth={3} fill="none" opacity={0.55} />
      {leaves.map((leaf, i) => {
        const angle = bloom ? leaf.angle : leaf.angle * 0.42 + (i % 2 ? 22 : -22);
        const cy = bloom ? leaf.y : leaf.y + 22;
        return (
          <g key={i} transform={`translate(${leaf.x} ${cy}) rotate(${angle + sway})`}>
            <path
              d={`M 0 0 C ${-38 * leaf.scale} ${-12 * leaf.scale} ${-60 * leaf.scale} ${-46 * leaf.scale} ${-42 * leaf.scale} ${-68 * leaf.scale} C ${-8 * leaf.scale} ${-48 * leaf.scale} ${9 * leaf.scale} ${-22 * leaf.scale} 0 0 Z`}
              fill={bloom ? MAT.leaf : MAT.leafDry}
              stroke={MAT.ink}
              strokeWidth={2.5}
            />
            <path d={`M 0 0 Q ${-28 * leaf.scale} ${-26 * leaf.scale} ${-42 * leaf.scale} ${-54 * leaf.scale}`} stroke={bloom ? MAT.leafDark : "#6f5f37"} strokeWidth={2} fill="none" opacity={0.7} />
          </g>
        );
      })}
      <path d="M 0 -74 Q -6 -112 0 -146" stroke={bloom ? MAT.leafDark : "#7b683c"} strokeWidth={5} fill="none" strokeLinecap="round" />
      {bloom ? (
        <g transform={`translate(0 -164) rotate(${sway})`}>
          {[0, 60, 120, 180, 240, 300].map((angle) => (
            <ellipse key={angle} cx={0} cy={-16} rx={8} ry={18} fill={MAT.flower} stroke={MAT.ink} strokeWidth={2} transform={`rotate(${angle})`} />
          ))}
          <circle cx={0} cy={0} r={9} fill="#d98d4f" stroke={MAT.ink} strokeWidth={2.5} />
        </g>
      ) : (
        <path d="M -7 -146 Q 0 -160 8 -146" stroke="#7b683c" strokeWidth={3} fill="none" strokeLinecap="round" />
      )}
    </g>
  );
};

const Can: React.FC<{ x: number; y: number; scale?: number }> = ({ x, y, scale = 1 }) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <path d="M -28 0 Q -34 -32 -22 -40 L 22 -40 Q 34 -32 28 0 Z" fill={MAT.metal} stroke={MAT.ink} strokeWidth={3} />
    <path d="M -28 -8 Q 0 4 28 -8" stroke={MAT.metalDark} strokeWidth={3} fill="none" opacity={0.7} />
    <path d="M 28 0 L 44 -34 L 50 -30 L 35 2" fill={MAT.metalDark} stroke={MAT.ink} strokeWidth={2.5} />
    <path d="M 22 -22 Q 38 -58 52 -42 Q 46 -29 30 -24" fill="none" stroke={MAT.ink} strokeWidth={4} />
    <path d="M -24 -3 Q 0 6 24 -3 L 22 2 Q 0 9 -22 2 Z" fill={MAT.water} opacity={0.8} />
    <circle cx={-13} cy={-14} r={3} fill={MAT.ink} opacity={0.55} />
  </g>
);

const Faucet: React.FC = () => (
  <g transform="translate(58 -2)">
    <rect x={0} y={-6} width={26} height={12} rx={4} fill={MAT.metalDark} stroke={MAT.ink} strokeWidth={3} />
    <path d="M 24 -2 L 44 4 L 44 12 L 24 8 Z" fill={MAT.metal} stroke={MAT.ink} strokeWidth={3} />
    <path d="M 8 -6 L 8 -30" stroke={MAT.metalDark} strokeWidth={4} strokeLinecap="round" />
    <path d="M -5 -30 L 21 -30" stroke={MAT.metal} strokeWidth={6} strokeLinecap="round" />
    <circle cx={8} cy={-30} r={8} fill={MAT.metalDark} stroke={MAT.ink} strokeWidth={2.5} />
    <path d="M 0 -30 L 16 -30" stroke="#d7c7a7" strokeWidth={2} opacity={0.7} />
  </g>
);

const HangingPlanter: React.FC<{ x: number; y: number; scale?: number; flip?: boolean }> = ({ x, y, scale = 1, flip = false }) => (
  <g transform={`translate(${x} ${y}) scale(${flip ? -scale : scale} ${scale})`}>
    <path d="M 0 -52 L 0 24" stroke={MAT.frameDark} strokeWidth={3} />
    <path d="M -20 24 Q 0 38 20 24 L 26 62 L -26 62 Z" fill={MAT.pot} stroke={MAT.ink} strokeWidth={3} />
    <path d="M -24 62 Q 0 72 24 62" stroke="#d58c64" strokeWidth={3} fill="none" opacity={0.55} />
    {[-1, 1].map((side) => (
      <g key={side} transform={`rotate(${side * 24})`}>
        <path d="M 0 38 C -28 12 -62 22 -72 52 C -42 60 -16 54 0 38 Z" fill={MAT.leaf} stroke={MAT.ink} strokeWidth={2.4} />
        <path d="M 0 38 C -18 54 -38 78 -34 104 C -12 84 -2 62 0 38 Z" fill={MAT.leafDark} stroke={MAT.ink} strokeWidth={2.2} opacity={0.95} />
      </g>
    ))}
  </g>
);

const WallShelf: React.FC = () => (
  <g transform="translate(584 1012)">
    <rect width={396} height={12} rx={3} fill="#9b704e" stroke={MAT.ink} strokeWidth={3} />
    <path d="M 32 12 L 20 58 M 364 12 L 376 58" stroke={MAT.frameDark} strokeWidth={5} />
    {[0, 1, 2, 3, 4].map((i) => (
      <g key={i} transform={`translate(${44 + i * 68} -2)`}>
        <rect x={-15} y={-34 - (i % 2) * 12} width={30} height={34 + (i % 2) * 12} rx={4} fill={i % 2 ? "#718b72" : "#b26b50"} stroke={MAT.ink} strokeWidth={2.5} />
        <path d={`M -11 ${-26 - (i % 2) * 12} L 11 ${-26 - (i % 2) * 12}`} stroke="#ead6a9" strokeWidth={2} opacity={0.6} />
        <rect x={-18} y={-42 - (i % 2) * 12} width={36} height={8} rx={2} fill="#5d4130" stroke={MAT.ink} strokeWidth={2} />
      </g>
    ))}
  </g>
);

const HoseReel: React.FC = () => (
  <g transform="translate(968 1134)">
    <circle r={46} fill="#4a443a" stroke={MAT.ink} strokeWidth={4} />
    <circle r={31} fill="#81745c" stroke={MAT.ink} strokeWidth={3} />
    <circle r={8} fill="#d8c9a4" stroke={MAT.ink} strokeWidth={2.5} />
    {[0, 1, 2].map((i) => (
      <circle key={i} r={18 + i * 8} fill="none" stroke="#3e625a" strokeWidth={4} opacity={0.8} />
    ))}
    <path d="M 34 34 Q 80 26 82 78 Q 84 104 54 108" stroke="#3e625a" strokeWidth={7} fill="none" strokeLinecap="round" />
    <path d="M 50 108 L 60 116" stroke={MAT.metalDark} strokeWidth={7} strokeLinecap="round" />
  </g>
);

const HangingVine: React.FC<{ x: number; y: number; scale?: number }> = ({ x, y, scale = 1 }) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <path d="M 0 0 C -18 70 18 132 -4 202 C -20 260 8 322 -8 392" stroke="#3c6648" strokeWidth={5} fill="none" strokeLinecap="round" />
    {[0, 1, 2, 3, 4, 5].map((i) => {
      const side = i % 2 ? 1 : -1;
      const top = 38 + i * 62;
      return (
        <g key={i} transform={`translate(${side * (8 + (i % 3) * 7)} ${top}) rotate(${side * 34})`}>
          <path d="M 0 0 C 6 -34 28 -46 48 -50 C 38 -22 20 -6 0 0 Z" fill={i % 2 ? MAT.leaf : MAT.leafDark} stroke={MAT.ink} strokeWidth={2} />
          <path d="M 0 0 Q 22 -18 46 -48" stroke="#789467" strokeWidth={1.8} fill="none" opacity={0.65} />
        </g>
      );
    })}
  </g>
);

const WallTrellis: React.FC = () => (
  <g transform="translate(494 900)" opacity={0.9}>
    <path d="M 0 0 L 0 470 M 64 0 L 64 470 M 128 0 L 128 470 M 192 0 L 192 470" stroke={MAT.frameDark} strokeWidth={6} />
    <path d="M 0 44 L 192 44 M 0 168 L 192 168 M 0 292 L 192 292 M 0 416 L 192 416" stroke={MAT.frameDark} strokeWidth={5} />
    <path d="M 12 444 C 54 388 34 330 78 280 C 118 234 98 158 152 112" stroke="#3c6648" strokeWidth={5} fill="none" />
    {[0, 1, 2, 3, 4].map((i) => (
      <path key={i} d={`M ${78 + (i % 2) * 24} ${272 - i * 42} q ${i % 2 ? 42 : -42} -22 ${i % 2 ? 74 : -74} -8`} stroke={MAT.leaf} strokeWidth={7} fill="none" strokeLinecap="round" />
    ))}
  </g>
);

const CrateStack: React.FC = () => (
  <g transform="translate(488 1518)">
    <CastShadow cx={0} cy={206} rx={92} ry={18} opacity={0.28} />
    <rect x={-78} y={96} width={156} height={108} rx={5} fill="#7c5b40" stroke={MAT.ink} strokeWidth={4} />
    <rect x={-66} y={0} width={132} height={96} rx={5} fill="#906849" stroke={MAT.ink} strokeWidth={4} />
    <path d="M -66 16 L 66 16 M -66 78 L 66 78 M -78 116 L 78 116 M -78 184 L 78 184" stroke="#4e3625" strokeWidth={5} opacity={0.75} />
    <path d="M -40 38 L 40 38 M -40 58 L 40 58" stroke="#c39568" strokeWidth={4} opacity={0.5} />
    <path d="M -44 136 L 44 136 M -44 160 L 44 160" stroke="#c39568" strokeWidth={4} opacity={0.45} />
  </g>
);

/**
 * The second non-winter interior: a working greenhouse before the day heats up.
 * `state` is the story state of the set, not a new scene: the same glasshouse is
 * dry in the opening, then the plant opens in the close. The watering can is on
 * the bench only while the apprentice has not picked it up.
 */
export const Greenhouse: React.FC<{
  progress: number;
  state?: "table" | "held" | "pour" | "bloom" | "left";
}> = ({ progress, state = "table" }) => {
  const frame = useCurrentFrame();
  const plantState: PlantState = state === "bloom" ? "bloom" : "dry";
  const showTableCan = state === "table" || state === "bloom";
  const dawn = 0.88 + Math.sin(frame / 61) * 0.04;

  return (
    <svg viewBox="0 0 1080 1920" preserveAspectRatio="xMidYMid slice" style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }}>
      <defs>
        <linearGradient id="green-wall" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#263f3c" />
          <stop offset="55%" stopColor={MAT.wall} />
          <stop offset="100%" stopColor="#3f5b4c" />
        </linearGradient>
        <linearGradient id="green-floor" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={MAT.floor} />
          <stop offset="100%" stopColor="#221c16" />
        </linearGradient>
        <linearGradient id="green-sky" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={MAT.sky} />
          <stop offset="55%" stopColor="#6c8b86" />
          <stop offset="100%" stopColor="#f1b987" />
        </linearGradient>
        <linearGradient id="green-wood" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#a77b56" />
          <stop offset="100%" stopColor="#624431" />
        </linearGradient>
        <radialGradient id="green-sun">
          <stop offset="0%" stopColor="#fff3d0" stopOpacity="0.95" />
          <stop offset="45%" stopColor="#ffd19a" stopOpacity="0.42" />
          <stop offset="100%" stopColor="#ffc17d" stopOpacity="0" />
        </radialGradient>
        <linearGradient id="green-light" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#ffe1b4" stopOpacity="0.55" />
          <stop offset="100%" stopColor="#ffd39f" stopOpacity="0" />
        </linearGradient>
        <filter id="green-blur" x="-40%" y="-40%" width="180%" height="180%">
          <feGaussianBlur stdDeviation={14} />
        </filter>
        <MaterialDefs prefix="green" palette={MAT} />
        <SoftBlurDefs id="green-soft" />
      </defs>

      <rect width="1080" height="1920" fill="url(#green-wall)" />
      <path d="M 0 1258 L 1080 1258 L 1080 1920 L 0 1920 Z" fill="url(#green-floor)" />
      <g opacity={0.55} stroke={MAT.floorLine} strokeWidth={4}>
        {[0, 1, 2, 3, 4, 5].map((i) => (
          <path key={i} d={`M ${-100 + i * 240} 1258 L ${40 + i * 240} 1920`} />
        ))}
        <path d="M 0 1450 L 1080 1450" />
        <path d="M 0 1600 L 1080 1600" />
        <path d="M 0 1710 L 1080 1710" />
        <path d="M 0 1830 L 1080 1830" />
      </g>
      <g opacity={0.45} stroke="#83674a" strokeWidth={2.5} fill="none">
        <path d="M 0 1660 Q 280 1648 520 1662 T 1080 1654" />
        <path d="M 0 1760 Q 240 1774 480 1758 T 1080 1768" />
        <path d="M 0 1870 Q 320 1858 640 1872 T 1080 1862" />
      </g>
      <g opacity={0.2} stroke={MAT.wallLine} strokeWidth={3}>
        {[0, 1, 2, 3, 4, 5, 6].map((i) => (
          <path key={i} d={`M ${-40 + i * 190} 0 L ${-40 + i * 190} 1280`} />
        ))}
      </g>

      <ParallaxGroup depth={0.12} progress={progress}>
        {/* glass roof and the first sun of the day */}
        <g transform="translate(0 0)">
          <rect y={0} width={1080} height={1260} fill="#2c4840" opacity={0.55} />
          <g opacity={0.95}>
            {[0, 1, 2, 3, 4, 5, 6].map((i) => (
              <g key={i}>
                <path d={`M ${-80 + i * 200} 0 L ${120 + i * 200} 0 L ${240 + i * 200} 610`} stroke={MAT.frame} strokeWidth={7} opacity={0.62} />
                <path d={`M ${120 + i * 200} 0 L ${180 + i * 200} 610`} stroke={MAT.frameDark} strokeWidth={3} opacity={0.4} />
              </g>
            ))}
            <path d="M 0 610 L 1080 610" stroke={MAT.frame} strokeWidth={9} opacity={0.75} />
            <path d="M 0 630 L 1080 630" stroke={MAT.frameDark} strokeWidth={3} opacity={0.45} />
            <path d="M 0 900 L 1080 900" stroke={MAT.frame} strokeWidth={7} opacity={0.45} />
          </g>
          <circle cx={270} cy={288} r={150} fill="url(#green-sun)" opacity={dawn} />
          <circle cx={270} cy={288} r={42} fill="#ffe4b6" opacity={0.92} />
          {/* distant glasshouse silhouettes, kept low-contrast so the plant owns the foreground */}
          <path d="M 0 610 Q 120 560 220 610 Q 350 548 470 610 Q 610 566 730 610 Q 880 548 1080 606 L 1080 900 L 0 900 Z" fill="#456a5d" opacity={0.48} />
          <path d="M 0 760 Q 160 730 320 760 Q 520 730 720 760 Q 900 730 1080 758 L 1080 900 L 0 900 Z" fill="#315247" opacity={0.65} />
        </g>

        <g transform="translate(0 920)">
          <path d="M 0 0 L 1080 0" stroke={MAT.wallLine} strokeWidth={10} opacity={0.65} />
          <path d="M 0 12 L 1080 12" stroke="#9c7858" strokeWidth={3} opacity={0.4} />
        </g>

        {/* tool shelf, left, with a few readable silhouettes */}
        <g transform="translate(56 760)">
          <rect width={244} height={13} rx={3} fill={MAT.frameDark} stroke={MAT.ink} strokeWidth={3} />
          {[0, 44, 88, 132].map((x, i) => (
            <g key={x} transform={`translate(${x} -2)`}>
              <rect x={0} y={-38 - (i % 2) * 16} width={24} height={38 + (i % 2) * 16} rx={3} fill={i % 2 ? "#b56b50" : "#6b8a6d"} stroke={MAT.ink} strokeWidth={2.5} />
              <path d="M 3 -28 L 20 -28" stroke="#e2cfa7" strokeWidth={2} opacity={0.6} />
            </g>
          ))}
        </g>

        {/* the right-hand wall is not a blank plate: these readable objects also
            keep the hook and the close from becoming a wall with a plant at the edge */}
        <WallTrellis />
        <HangingPlanter x={650} y={760} scale={0.9} />
        <HangingVine x={566} y={800} scale={0.92} />
        <HangingPlanter x={930} y={708} scale={0.78} flip />
        <WallShelf />
        <HoseReel />
        <CrateStack />

        {/* rain barrel: the source of the second act */}
        <g transform="translate(166 1530)">
          <CastShadow cx={0} cy={8} rx={100} ry={18} opacity={0.3} />
          <rect x={-72} y={-24} width={144} height={224} rx={16} fill="#6f523b" stroke={MAT.ink} strokeWidth={4} />
          <path d="M -72 -4 Q 0 12 72 -4 M -72 84 Q 0 100 72 84 M -72 170 Q 0 186 72 170" stroke="#3d2a20" strokeWidth={4} fill="none" opacity={0.65} />
          <ellipse cx={0} cy={-24} rx={72} ry={18} fill="#4b3427" stroke={MAT.ink} strokeWidth={3} />
          <ellipse cx={0} cy={-20} rx={59} ry={12} fill={MAT.water} opacity={0.8} />
          <path d="M 52 20 L 86 42" stroke={MAT.metalDark} strokeWidth={8} strokeLinecap="round" />
          <path d="M 84 42 L 96 46" stroke={MAT.metal} strokeWidth={5} strokeLinecap="round" />
          <Faucet />
        </g>

        {/* workbench and the plant: table height is 210 px above the actors' feet, not chest height */}
        <g transform="translate(610 1530)">
          <CastShadow cx={190} cy={214} rx={240} ry={30} opacity={0.25} />
          <rect width={430} height={28} rx={4} fill="url(#green-wood)" stroke={MAT.ink} strokeWidth={4} />
          <rect x={24} y={28} width={20} height={188} fill="#60402d" stroke={MAT.ink} strokeWidth={3} />
          <rect x={386} y={28} width={20} height={188} fill="#60402d" stroke={MAT.ink} strokeWidth={3} />
          <rect x={44} y={86} width={342} height={11} fill="#422b20" opacity={0.75} />
          <path d="M 54 16 L 376 16" stroke="#d0a77a" strokeWidth={3} opacity={0.55} />
        </g>
        <Plant x={874} y={1530} state={plantState} frame={frame} />
        {showTableCan ? <Can x={690} y={1530} scale={0.92} /> : null}

        {/* foreground pots are below the actors' feet line; they frame without becoming a stool */}
        <g transform="translate(1018 1748)">
          <ellipse cx={0} cy={62} rx={72} ry={14} fill="#211a14" opacity={0.5} />
          <path d="M -46 0 L -34 62 L 34 62 L 46 0 Z" fill="#7c543a" stroke={MAT.ink} strokeWidth={3} />
          <path d="M -34 8 Q 0 24 34 8" stroke="#c08d60" strokeWidth={3} fill="none" opacity={0.55} />
        </g>
      </ParallaxGroup>

      <polygon points="190,610 400,610 640,1500 160,1500" fill="url(#green-light)" opacity={0.14} />
      <LightShaft id="green-window-shaft" d="M 140 620 L 390 620 L 650 1510 L 120 1510 Z" color="#ffd7a4" opacity={0.12} blur={28} />
      <DustMotes count={26} seed={31} frame={frame} area={{ x: 180, y: 700, w: 620, h: 640 }} color="#ffe7bd" />
      <Glow id="green-sun-glow" cx={300} cy={300} r={240} color="#ffe4b5" opacity={0.18} />
      <rect y={1840} width={1080} height={80} fill="#15120e" opacity={0.5} />
      <rect width={1080} height={1920} fill="none" stroke="#12100d" strokeWidth={18} opacity={0.3} />
    </svg>
  );
};
