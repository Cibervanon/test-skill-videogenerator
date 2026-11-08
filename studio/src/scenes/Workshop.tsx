import React from "react";
import { useCurrentFrame } from "remotion";
import { ParallaxGroup } from "../engine/CameraRig";
import { CastShadow, DustMotes, Glow, LightShaft, SoftBlurDefs } from "../engine/atmosphere";
import { MaterialDefs } from "../engine/texture";

const MAT = {
  wall: "#5d4034",
  wallLight: "#7a5643",
  wallLine: "#3a261f",
  floor: "#4a3026",
  floorLine: "#2c1b16",
  wood: "#6b4632",
  woodLight: "#956646",
  woodLine: "#38221a",
  brass: "#c79a55",
  brassDark: "#7d5a2c",
  fabric: "#315b58",
  fabricLight: "#4b817a",
  paper: "#d8c5a2",
  ink: "#211612",
  dawn: "#f3b37b",
  sky: "#2d3b5c",
};

const Spool: React.FC<{ x: number; y: number; color: string; h?: number }> = ({ x, y, color, h = 34 }) => (
  <g transform={`translate(${x} ${y})`}>
    <rect x={-7} y={-h} width={14} height={h} rx={3} fill={color} stroke={MAT.ink} strokeWidth={2} />
    <rect x={-10} y={-h - 4} width={20} height={5} rx={2} fill={MAT.woodLight} stroke={MAT.ink} strokeWidth={1.6} />
    <rect x={-10} y={-2} width={20} height={5} rx={2} fill={MAT.woodLight} stroke={MAT.ink} strokeWidth={1.6} />
    <path d={`M -3 ${-h + 6} L 4 ${-h + 6}`} stroke="#ffffff" strokeWidth={1.5} opacity={0.35} />
  </g>
);

const Scissors: React.FC<{ x: number; y: number; rotate: number }> = ({ x, y, rotate }) => (
  <g transform={`translate(${x} ${y}) rotate(${rotate})`}>
    <path d="M -28 0 L 28 0" stroke={MAT.ink} strokeWidth={3} strokeLinecap="round" />
    <path d="M -28 0 L -44 -10 M -28 0 L -44 10" stroke={MAT.brassDark} strokeWidth={4} strokeLinecap="round" />
    <path d="M 28 0 L 44 -10 M 28 0 L 44 10" stroke={MAT.brassDark} strokeWidth={4} strokeLinecap="round" />
    <circle cx={0} cy={0} r={4.5} fill={MAT.brass} stroke={MAT.ink} strokeWidth={2} />
  </g>
);

export const Workshop: React.FC<{ progress: number }> = ({ progress }) => {
  const frame = useCurrentFrame();
  const flicker = 0.92 + Math.sin(frame / 5.4) * 0.05 + Math.sin(frame / 2.1) * 0.02;

  return (
    <svg
      viewBox="0 0 1080 1920"
      preserveAspectRatio="xMidYMid slice"
      style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }}
    >
      <defs>
        <linearGradient id="shop-wall" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#3d2b26" />
          <stop offset="48%" stopColor={MAT.wall} />
          <stop offset="100%" stopColor="#4a3028" />
        </linearGradient>
        <linearGradient id="shop-floor" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={MAT.floor} />
          <stop offset="100%" stopColor="#241511" />
        </linearGradient>
        <linearGradient id="shop-sky" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={MAT.sky} />
          <stop offset="48%" stopColor="#6c6374" />
          <stop offset="78%" stopColor="#d18b6d" />
          <stop offset="100%" stopColor="#ffd3a0" />
        </linearGradient>
        <linearGradient id="shop-wood" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={MAT.woodLight} />
          <stop offset="55%" stopColor={MAT.wood} />
          <stop offset="100%" stopColor="#4b2e21" />
        </linearGradient>
        <linearGradient id="shop-cloth" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor={MAT.fabricLight} />
          <stop offset="54%" stopColor={MAT.fabric} />
          <stop offset="100%" stopColor="#1e3b3a" />
        </linearGradient>
        <linearGradient id="shop-light" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#ffe1ac" stopOpacity="0.85" />
          <stop offset="100%" stopColor="#ffd08a" stopOpacity="0" />
        </linearGradient>
        <radialGradient id="shop-lamp">
          <stop offset="0%" stopColor="#fff4d0" stopOpacity="0.95" />
          <stop offset="38%" stopColor="#ffd08a" stopOpacity="0.5" />
          <stop offset="100%" stopColor="#ffb765" stopOpacity="0" />
        </radialGradient>
        <filter id="shop-soft" x="-40%" y="-40%" width="180%" height="180%">
          <feGaussianBlur stdDeviation={8} />
        </filter>
        <MaterialDefs prefix="shop" palette={MAT} />
        <SoftBlurDefs id="shop-blur" />
      </defs>

      <rect width="1080" height="1920" fill="url(#shop-wall)" />

      {/* back wall panelling */}
      <ParallaxGroup depth={0.12} progress={progress}>
        {[0, 1, 2, 3, 4, 5].map((i) => (
          <rect key={`panel-${i}`} x={-20 + i * 190} y={0} width={186} height={1370} fill="none" stroke={MAT.wallLine} strokeWidth={4} opacity={0.35} />
        ))}
        <path d="M 0 1110 L 1080 1110" stroke={MAT.wallLine} strokeWidth={9} opacity={0.75} />
        <path d="M 0 1118 L 1080 1118" stroke="#9b7458" strokeWidth={3} opacity={0.4} />

        {/* the window to the street: dawn, no snow */}
        <g transform="translate(92 322)">
          <rect x={-16} y={-16} width={344} height={550} fill="#2a1b19" stroke={MAT.ink} strokeWidth={6} />
          <rect width={312} height={518} fill="url(#shop-sky)" />
          <rect y={330} width={312} height={188} fill="#7b5f5d" opacity={0.75} />
          {[0, 1, 2, 3].map((i) => (
            <path key={`roof-${i}`} d={`M ${20 + i * 78} 330 l 30 -52 l 32 52 z`} fill="#3b2f38" opacity={0.85} />
          ))}
          <path d="M 0 354 Q 96 338 178 350 Q 252 360 312 346 L 312 390 L 0 390 Z" fill="#4a3436" opacity={0.9} />
          <circle cx={246} cy={164} r={34} fill="#ffd7a3" opacity={0.9} />
          <circle cx={246} cy={164} r={72} fill="#ffcf9a" opacity={0.15} />
          <path d="M 104 0 L 104 518 M 208 0 L 208 518 M 0 180 L 312 180 M 0 350 L 312 350" stroke={MAT.ink} strokeWidth={7} />
          <path d="M 0 0 L 312 0 L 312 518 L 0 518 Z" fill="none" stroke="#251715" strokeWidth={10} />
          <rect x={-20} y={530} width={352} height={12} rx={4} fill={MAT.woodLight} stroke={MAT.ink} strokeWidth={3} />
          <GLight />
        </g>

        {/* shelf of thread and folded cloth */}
        <g transform="translate(636 590)">
          <rect x={-18} y={0} width={360} height={14} fill={MAT.woodLight} stroke={MAT.ink} strokeWidth={3} />
          <rect x={-18} y={178} width={360} height={14} fill={MAT.woodLight} stroke={MAT.ink} strokeWidth={3} />
          {[
            [0, "#b9543e"],
            [42, "#d0a34f"],
            [84, "#4f8073"],
            [126, "#6a648e"],
            [168, "#b86d4a"],
            [210, "#516d91"],
            [252, "#8c6b4a"],
          ].map(([x, color], i) => (
            <Spool key={i} x={Number(x)} y={0} color={String(color)} h={26 + (i % 3) * 7} />
          ))}
          <g transform="translate(24 178)">
            <rect width={118} height={54} rx={3} fill="#7b5a3f" stroke={MAT.ink} strokeWidth={3} />
            <rect y={10} width={118} height={9} fill="#a78257" opacity={0.7} />
            <rect y={30} width={118} height={9} fill="#a78257" opacity={0.5} />
          </g>
          <g transform="translate(176 178)">
            <rect width={118} height={42} rx={3} fill="#4d6a61" stroke={MAT.ink} strokeWidth={3} />
            <path d="M 0 18 L 118 18" stroke="#8cb0a2" strokeWidth={3} opacity={0.45} />
          </g>
        </g>

        {/* hanging work lamp */}
        <g transform={`translate(796 210) rotate(${Math.sin(frame / 70) * 1.1})`}>
          <path d="M 0 0 L 0 118" stroke={MAT.ink} strokeWidth={5} />
          <path d="M -66 118 L 66 118 L 38 184 L -38 184 Z" fill="#d6a765" stroke="#2c1a14" strokeWidth={5} />
          <ellipse cx={0} cy={180} rx={28} ry={7} fill="#fff4cf" />
          <Glow id="shop-lampglow" cx={0} cy={180} r={270} color="#ffd08a" opacity={0.36 * flicker} />
          <LightShaft id="shop-lamp-shaft" d="M -38 180 L 38 180 L 180 740 L -180 740 Z" color="#ffd08a" opacity={0.09} blur={28} />
        </g>
      </ParallaxGroup>

      {/* floor */}
      <path d="M 0 1120 L 1080 1120 L 1080 1920 L 0 1920 Z" fill="url(#shop-floor)" />
      <g opacity={0.45} stroke={MAT.floorLine} strokeWidth={3}>
        {[0, 1, 2, 3, 4, 5, 6].map((i) => (
          <path key={i} d={`M ${-80 + i * 190} 1120 L ${110 + i * 190} 1920`} />
        ))}
        <path d="M 0 1320 L 1080 1320" />
        <path d="M 0 1570 L 1080 1570" />
      </g>

      {/* dress form: the coat is the object of the story */}
      <g transform="translate(812 1060)">
        <CastShadow cx={0} cy={410} rx={110} ry={24} opacity={0.25} />
        <rect x={-6} y={178} width={12} height={220} fill="#3c2a20" stroke={MAT.ink} strokeWidth={3} />
        <path d="M -46 404 L 46 404 L 30 424 L -30 424 Z" fill="#3c2a20" stroke={MAT.ink} strokeWidth={3} />
        <path d="M -54 166 Q -82 236 -60 316 L 0 336 L 60 316 Q 82 236 54 166 Z" fill="url(#shop-cloth)" stroke={MAT.ink} strokeWidth={4} />
        <path d="M -52 188 Q 0 210 52 188" stroke="#91b8a8" strokeWidth={3} fill="none" opacity={0.45} />
        <path d="M -4 336 L -4 404 M 0 168 L 0 208" stroke={MAT.ink} strokeWidth={3} opacity={0.75} />
        <path d="M -54 166 Q 0 146 54 166 L 62 194 Q 0 174 -62 194 Z" fill="#233e3d" stroke={MAT.ink} strokeWidth={3} />
        {/* the skipped stitch the tailor points to in S05 */}
        <path d="M -24 292 Q 0 280 24 292 Q 42 302 54 286" stroke="#d8785e" strokeWidth={3} fill="none" strokeDasharray="7 5" />
        <path d="M 54 286 Q 64 300 60 318" stroke="#d8785e" strokeWidth={2.4} fill="none" />
        {/* measuring tape around the neck */}
        <path d="M -34 176 Q 0 212 34 176 Q 18 154 0 154 Q -18 154 -34 176 Z" fill="none" stroke="#e6c88e" strokeWidth={5} opacity={0.85} />
      </g>

      {/* worktable, right foreground */}
      <g transform="translate(520 1460)">
        <CastShadow cx={250} cy={230} rx={300} ry={38} opacity={0.28} />
        <rect x={0} y={62} width={560} height={30} rx={5} fill="url(#shop-wood)" stroke={MAT.ink} strokeWidth={4} />
        <rect x={24} y={92} width={20} height={210} fill="#543525" stroke={MAT.ink} strokeWidth={3} />
        <rect x={516} y={92} width={20} height={210} fill="#543525" stroke={MAT.ink} strokeWidth={3} />
        <rect x={44} y={148} width={470} height={12} fill="#3c251c" opacity={0.8} />
        {/* pattern paper */}
        <g transform="translate(78 34) rotate(-4)">
          <rect width={190} height={130} rx={2} fill={MAT.paper} stroke={MAT.ink} strokeWidth={3} />
          <path d="M 18 26 L 168 26 M 18 44 L 128 44 M 18 62 L 154 62" stroke={MAT.wood} strokeWidth={3} opacity={0.55} />
          <path d="M 18 92 Q 56 64 92 90 Q 118 106 166 82" stroke={MAT.fabric} strokeWidth={3} fill="none" opacity={0.6} />
        </g>
        <Scissors x={338} y={34} rotate={-12} />
        {/* the snapped measuring tape: the hook must be visible, not only spoken */}
        <g transform="translate(252 24) rotate(6)">
          <path d="M 0 18 Q 34 2 68 16 Q 102 30 134 10" stroke="#e7c98d" strokeWidth={9} fill="none" strokeLinecap="round" />
          <path d="M 138 10 L 166 2 M 142 16 L 174 14 M 146 22 L 166 30" stroke="#c89a57" strokeWidth={2} opacity={0.8} />
          <path d="M 0 18 L -18 12 M 2 24 L -16 26" stroke="#c89a57" strokeWidth={2} opacity={0.7} />
          {[20, 44, 68, 92, 116].map((x) => (
            <path key={x} d={`M ${x} 10 L ${x} 22`} stroke="#8a6434" strokeWidth={1.8} opacity={0.7} />
          ))}
        </g>
        <g transform="translate(250 16)">
          <rect x={-22} y={-20} width={44} height={36} rx={4} fill="#2f4b47" stroke={MAT.ink} strokeWidth={3} />
          <path d="M -22 -10 L 0 -10 L 0 16" stroke={MAT.brass} strokeWidth={3} fill="none" />
          <circle cx={12} cy={-2} r={6} fill={MAT.brass} stroke={MAT.ink} strokeWidth={2} />
        </g>
        <rect x={92} y={18} width={52} height={12} rx={2} fill="#d7b67d" stroke={MAT.ink} strokeWidth={2} />
        <path d="M 100 24 Q 132 52 164 24" stroke="#e8c98d" strokeWidth={3} fill="none" opacity={0.8} />
      </g>

      {/* foreground chair and basket, kept low so they do not block faces */}
      <g transform="translate(84 1500)">
        <rect x={0} y={80} width={126} height={18} rx={4} fill="#5c3b2a" stroke={MAT.ink} strokeWidth={3} />
        <rect x={10} y={98} width={12} height={150} fill="#3e281e" />
        <rect x={104} y={98} width={12} height={150} fill="#3e281e" />
        <rect x={0} y={-72} width={18} height={160} rx={4} fill="#5c3b2a" stroke={MAT.ink} strokeWidth={3} />
      </g>
      <g transform="translate(330 1750)">
        <ellipse cx={0} cy={54} rx={85} ry={16} fill="#2d1d17" opacity={0.55} />
        <path d="M -70 0 Q -82 64 -52 78 L 52 78 Q 82 64 70 0 Z" fill="#6f4d37" stroke={MAT.ink} strokeWidth={4} />
        <path d="M -66 14 Q 0 42 66 14" stroke="#a57a53" strokeWidth={3} fill="none" opacity={0.5} />
      </g>

      {/* dawn light through the window and a little dust in it */}
      <polygon points="120,850 420,910 700,1560 160,1500" fill="url(#shop-light)" opacity={0.16} />
      <LightShaft id="shop-window-shaft" d="M 108 850 L 402 850 L 620 1500 L 170 1500 Z" color="#ffd7a3" opacity={0.12} blur={26} />
      <DustMotes count={30} seed={17} frame={frame} area={{ x: 140, y: 880, w: 500, h: 650 }} color="#ffe6b8" />
      <rect y={1840} width="1080" height={80} fill="#1c100d" opacity={0.55} />
      <rect width="1080" height="1920" fill="none" stroke="#1b100d" strokeWidth={18} opacity={0.35} />
    </svg>
  );
};

/** Small helper so the window's interior glow has a stable id and no text. */
const GLight: React.FC = () => <Glow id="shop-windowglow" cx={156} cy={258} r={300} color="#ffcf9a" opacity={0.16} />;
