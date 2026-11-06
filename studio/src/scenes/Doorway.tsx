import React from "react";
import { useCurrentFrame } from "remotion";
import { Particles } from "../engine/Snow";
import { ParallaxGroup } from "../engine/CameraRig";
import { DustMotes, CastShadow, Cone, FogBand, Glow, LightShaft, LightVeil, SoftBlurDefs } from "../engine/atmosphere";
import { MaterialDefs } from "../engine/texture";
import { makeRoom } from "../engine/perspective";

const MAT = {
  stone: "#4a3f44",
  stoneLight: "#5a4c50",
  mortar: "#2c2328",
  wood: "#5b3b30",
  woodLight: "#7a5140",
  woodLine: "#33201c",
  roof: "#3a2a2a",
  roofLight: "#4a3535",
  roofLine: "#241718",
  snow: "#d7dfee",
  snowLine: "#9aa8c4",
  snowAccent: "#ffffff",
  carpet: "#7a2f34",
  carpetLine: "#5a1f24",
  carpetAccent: "#c9a25f",
  wall: "#8a5a3f",
  wallLine: "#5e3928",
  wallAccent: "#a87a52",
  frost: "#cfe0ff",
  ink: "#1a1218",
};

/** A jar on a shelf: three primitives, but they read as a lived-in room. */
const Jar: React.FC<{ x: number; y: number; h: number; c: string }> = ({ x, y, h, c }) => (
  <g transform={`translate(${x} ${y})`}>
    <path d={`M -9 0 q -3 ${-h * 0.6} 0 ${-h} l 18 0 q 3 ${h * 0.4} 0 ${h} z`} fill={c} stroke={MAT.ink} strokeWidth={2.4} />
    <rect x={-7} y={-h - 4} width={14} height={5} rx={2} fill="#3a2a22" />
    <path d={`M -5 ${-h * 0.5} q 5 4 10 0`} stroke="#ffffff" strokeWidth={2} fill="none" opacity={0.3} />
  </g>
);

// The back wall is INSET from the door opening: that inset is what gives the
// side walls, ceiling and floor somewhere to converge to. When the back wall
// filled the opening the room still read as a flat panel.
const ROOM = makeRoom({ x: 540, y: 800 }, { x0: 296, x1: 784, y0: 556, y1: 1236 }, 3.1);

export const Doorway: React.FC<{ progress: number }> = ({ progress }) => {
  const frame = useCurrentFrame();
  const flicker = 0.92 + Math.sin(frame / 5.2) * 0.05 + Math.sin(frame / 1.9) * 0.02;
  const swing = Math.sin(frame / 70) * 1.2;

  return (
    <>
      <svg viewBox="0 0 1080 1920" preserveAspectRatio="xMidYMid slice" style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }}>
        <defs>
          <linearGradient id="door-night" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#0e1530" />
            <stop offset="70%" stopColor="#26305a" />
            <stop offset="100%" stopColor="#3a3f66" />
          </linearGradient>
          <linearGradient id="door-warm" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#ffd79a" />
            <stop offset="55%" stopColor="#f0a75f" />
            <stop offset="100%" stopColor="#b96f42" />
          </linearGradient>
          <radialGradient id="door-lamp">
            <stop offset="0%" stopColor="#fff6d8" stopOpacity="0.95" />
            <stop offset="35%" stopColor="#ffd08a" stopOpacity="0.5" />
            <stop offset="100%" stopColor="#ffb765" stopOpacity="0" />
          </radialGradient>
          <linearGradient id="door-spill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#ffcf8a" stopOpacity="0.6" />
            <stop offset="60%" stopColor="#ffb765" stopOpacity="0.2" />
            <stop offset="100%" stopColor="#ffb765" stopOpacity="0" />
          </linearGradient>
          <filter id="softBlur" x="-40%" y="-40%" width="180%" height="180%">
            <feGaussianBlur stdDeviation={8} />
          </filter>
          <MaterialDefs prefix="door" palette={MAT} />
          <SoftBlurDefs id="door-soft" />
          <clipPath id="door-interior">
            <rect x={212} y={498} width={656} height={1012} />
          </clipPath>
        </defs>

        <rect width="1080" height="1920" fill="url(#door-night)" />

        {/* EXTERIOR WALL: planks + stone footing + small frosted window */}
        <ParallaxGroup depth={0.16} progress={progress}>
          <rect x={0} y={600} width={1080} height={900} fill="url(#door-plank)" opacity={0.9} />
          <rect x={0} y={600} width={1080} height={60} fill="#3a2a2c" stroke={MAT.ink} strokeWidth={3} />
          <rect x={0} y={1400} width={1080} height={100} fill="url(#door-stone)" stroke={MAT.ink} strokeWidth={3} />
          {/* small window with frost, outside the door frame */}
          <g transform="translate(70 760)">
            <rect width={110} height={150} fill="#1a2240" stroke={MAT.ink} strokeWidth={5} />
            <rect x={5} y={5} width={100} height={140} fill="#2b3a6b" />
            <rect x={5} y={5} width={100} height={140} fill="url(#door-frost)" opacity={0.5} />
            <path d="M 55 5 L 55 145 M 5 75 L 105 75" stroke={MAT.ink} strokeWidth={5} />
            <rect x={-6} y={150} width={122} height={8} rx={4} fill="#e9effb" />
          </g>
          {/* hanging lantern on the wall */}
          <g transform="translate(940 720)">
            <path d="M 0 0 L 0 24 M -22 24 L 22 24" stroke="#2a1c1e" strokeWidth={4} />
            <path d="M -16 30 h 32 l 6 34 h -44 z" fill="#f7c977" stroke={MAT.ink} strokeWidth={3} />
            <ellipse cx={0} cy={48} rx={10} ry={11} fill="#fff3c9" />
            <Glow id="door-lantern" cx={0} cy={48} r={150} color="#ffb765" opacity={0.34} />
          </g>
        </ParallaxGroup>

        {/* DOOR FRAME */}
        <rect x={182} y={468} width={716} height={1046} rx={6} fill="#2a1c22" stroke="#120c12" strokeWidth={7} />
        <rect x={196} y={482} width={688} height={1030} fill="#1c1218" />
        {/* threshold */}
        <rect x={196} y={1480} width={688} height={34} fill="url(#door-stone)" stroke={MAT.ink} strokeWidth={4} />
        <rect x={196} y={1476} width={688} height={8} rx={4} fill="#e9effb" opacity={0.85} />

        {/* INTERIOR (through the opening) */}
        <g clipPath="url(#door-interior)">
          {/* THE ROOM IS A PERSPECTIVE BOX, not a lit rectangle: side walls,
              ceiling and floor converge on one vanishing point, so depth is
              geometry rather than a gradient. Maths ported from the external
              repo's one-point room (MIT). */}
          <polygon points={ROOM.Q([[0, 0, 0], [0, 1, 0], [0, 1, 1], [0, 0, 1]])} fill="#6b4530" />
          <polygon points={ROOM.Q([[1, 0, 0], [1, 1, 0], [1, 1, 1], [1, 0, 1]])} fill="#5c3a29" />
          <polygon points={ROOM.Q([[0, 0, 0], [1, 0, 0], [1, 0, 1], [0, 0, 1]])} fill="#4a2b21" />
          <polygon points={ROOM.Q([[0, 1, 0], [1, 1, 0], [1, 1, 1], [0, 1, 1]])} fill="#3d2820" />
          {/* ceiling beams run to the same vanishing point as the boards */}
          {[0.2, 0.5, 0.8].map((u, i) => (
            <line
              key={`beam${i}`}
              x1={ROOM.P(u, 0, 0).x}
              y1={ROOM.P(u, 0, 0).y}
              x2={ROOM.P(u, 0, 1).x}
              y2={ROOM.P(u, 0, 1).y}
              stroke="#33201c"
              strokeWidth={3}
              opacity={0.65}
            />
          ))}
          {/* back wall + wainscot, inset inside the opening */}
          <rect x={296} y={556} width={488} height={680} fill="url(#door-wallpaper)" opacity={0.9} />
          <rect x={296} y={1080} width={488} height={156} fill="url(#door-plank)" />
          <rect x={296} y={1072} width={488} height={14} fill="#5e3928" />
          <path d="M 296 556 L 784 556" stroke="#2c1b14" strokeWidth={6} opacity={0.75} />
          {/* floor boards running to the vanishing point */}
          {[0.08, 0.22, 0.36, 0.5, 0.64, 0.78, 0.92].map((u, i) => (
            <line
              key={`plank${i}`}
              x1={ROOM.P(u, 1, 0).x}
              y1={ROOM.P(u, 1, 0).y}
              x2={ROOM.P(u, 1, 1).x}
              y2={ROOM.P(u, 1, 1).y}
              stroke="#2c1b14"
              strokeWidth={2}
              opacity={0.5}
            />
          ))}
          {/* the rug is laid in room coordinates, so it lies on the floor */}
          <polygon
            points={ROOM.Q([[0.04, 1, 0.02], [0.96, 1, 0.02], [0.96, 1, 0.92], [0.04, 1, 0.92]])}
            fill="url(#door-carpet)"
            stroke="#3a1618"
            strokeWidth={5}
            opacity={0.95}
          />
          <polygon
            points={ROOM.Q([[0.09, 1, 0.1], [0.91, 1, 0.1], [0.91, 1, 0.84], [0.09, 1, 0.84]])}
            fill="none"
            stroke="#c9a25f"
            strokeWidth={4}
            opacity={0.45}
          />
          {/* window light falling across the boards */}
          <polygon
            points={ROOM.Q([[0.1, 1, 0.18], [0.38, 1, 0.18], [0.5, 1, 0.96], [0.16, 1, 0.96]])}
            fill="#ffe3ae"
            opacity={0.12}
          />
          {/* hanging lamp */}
          <g transform={`translate(540 690) rotate(${swing})`}>
            <path d="M 0 -134 L 0 -58" stroke="#3a2a1e" strokeWidth={4} />
            <path d="M -62 -58 L 62 -58 L 34 -14 L -34 -14 Z" fill="#f7d79a" stroke="#5a3a22" strokeWidth={4} />
            <ellipse cx={0} cy={-10} rx={26} ry={7} fill="#fff2c9" />
            <Glow id="door-lampglow" cx={0} cy={-10} r={210} color="#ffd08a" opacity={0.4} />
            <LightShaft id="door-shaft" d="M -34 -14 L 34 -14 L 150 700 L -150 700 Z" color="#ffd08a" opacity={0.1} blur={26} />
          </g>
          {/* shelf with jars */}
          <g transform="translate(668 1000)">
            <rect x={-6} y={0} width={110} height={12} fill="#5e3928" stroke={MAT.ink} strokeWidth={3} />
            <Jar x={20} y={0} h={44} c="#8fae7a" />
            <Jar x={54} y={0} h={34} c="#c98a5a" />
            <Jar x={88} y={0} h={52} c="#7a8fae" />
          </g>
          {/* coat on a hook */}
          <g transform="translate(408 880)">
            <path d="M 0 0 q 26 40 8 96 q -20 10 -34 -4 q 12 -52 -4 -92 z" fill="#4a3a5a" stroke={MAT.ink} strokeWidth={3} />
            <path d="M -4 -6 q 4 -14 14 -14 q 10 0 12 12" stroke={MAT.ink} strokeWidth={4} fill="none" />
            <path d="M 0 96 q -4 30 6 60" stroke="#4a3a5a" strokeWidth={10} fill="none" strokeLinecap="round" />
          </g>
          {/* picture frame */}
          <g transform="translate(612 776)">
            <rect width={96} height={78} fill="#6b4a34" stroke={MAT.ink} strokeWidth={5} />
            <rect x={9} y={9} width={78} height={60} fill="#c9a25f" opacity={0.45} />
            <path d="M 9 60 L 38 34 L 56 50 L 70 40 L 87 60 Z" fill="#5a6b8a" opacity={0.6} />
          </g>
          {/* chair, table edge, bowl */}
          <g transform="translate(430 1392)" opacity={0.92}>
            <rect x={-52} y={-74} width={104} height={14} rx={5} fill="#5c3226" stroke={MAT.ink} strokeWidth={3} />
            <rect x={-44} y={-74} width={12} height={120} fill="#5c3226" />
            <rect x={30} y={-74} width={12} height={120} fill="#5c3226" />
            <rect x={-56} y={-64} width={20} height={54} rx={6} fill="#5c3226" />
            <path d="M -56 -10 L -36 -10" stroke={MAT.ink} strokeWidth={3} />
          </g>
          <g transform="translate(600 1330)">
            <rect x={-20} y={-8} width={190} height={16} rx={4} fill="#6b4a34" stroke={MAT.ink} strokeWidth={3} />
            <ellipse cx={60} cy={-20} rx={34} ry={14} fill="#c9a25f" stroke={MAT.ink} strokeWidth={3} />
            <ellipse cx={60} cy={-24} rx={26} ry={9} fill="#7a5a3a" />
            <path d="M -14 -8 l -6 70 M 170 -8 l 6 70" stroke="#4a3026" strokeWidth={9} />
          </g>
        </g>

        {/* door leaf, open towards us */}
        <g>
          <rect x={212} y={498} width={150} height={1012} fill="url(#door-plank)" stroke="#22151a" strokeWidth={5} />
          <rect x={232} y={540} width={110} height={420} rx={4} fill="none" stroke="#6d4736" strokeWidth={4} />
          <rect x={232} y={990} width={110} height={420} rx={4} fill="none" stroke="#6d4736" strokeWidth={4} />
          <circle cx={332} cy={1010} r={9} fill="#d3a55f" stroke="#7a5520" strokeWidth={2} />
          <path d="M 212 498 L 212 1510" stroke="#1a1014" strokeWidth={5} />
        </g>

        {/* frost + icicles on the lintel */}
        {[210, 268, 330, 402, 470, 545, 612, 690, 760, 830].map((x, i) => (
          <path key={i} d={`M ${x} 1508 l 6 ${16 + (i % 3) * 14} l 6 ${-(16 + (i % 3) * 14)} z`} fill="#dfe9f8" opacity={0.75} />
        ))}

        {/* CONTRAST PASS: mid-tones sink, the lamp and the doorway stay bright.
            Drawn on the set only, so the characters keep full brightness. */}
        <LightVeil id="door-veil" lights={[[540, 700, 330], [540, 1240, 290], [940, 790, 150]]} opacity={0.5} />
        <Cone id="door-cone" d="M 494 700 L 586 700 L 700 1300 L 380 1300 Z" opacity={0.22} />

        {/* LIGHT SPILL onto the snow + snow surface */}
        <path d="M 212 1510 L 868 1510 L 1030 1920 L 60 1920 Z" fill="url(#door-spill)" opacity={0.85 * flicker} />
        <path d="M 0 1496 Q 300 1458 540 1482 Q 800 1508 1080 1472 L 1080 1920 L 0 1920 Z" fill="#cfd8ea" />
        <rect y={1500} width={1080} height={420} fill="url(#door-snow)" opacity={0.55} />
        <path d="M 0 1496 Q 300 1458 540 1482 Q 800 1508 1080 1472" stroke="#eef4ff" strokeWidth={7} fill="none" opacity={0.75} />
        <ellipse cx={540} cy={1560} rx={330} ry={78} fill="#ffcf8a" opacity={0.2 * flicker} />
        {/* the keeper's footprints in the snow */}
        <g opacity={0.32} fill="#8f9dc4">
          {[0, 1, 2, 3].map((i) => (
            <ellipse key={i} cx={420 - i * 60} cy={1620 + i * 40} rx={12} ry={6} transform={`rotate(${-18 + i * 4} ${420 - i * 60} ${1620 + i * 40})`} />
          ))}
        </g>
        <CastShadow cx={540} cy={1580} rx={220} ry={40} opacity={0.18} />
        <FogBand id="door-fog" y={1600} height={260} color="#9fb0d8" opacity={0.16} />
        <DustMotes count={26} seed={9} frame={frame} area={{ x: 240, y: 900, w: 600, h: 600 }} color="#ffe6b8" />
      </svg>
      <Particles count={54} seed="doorSnow2" size={[2, 6]} speed={[0.4, 1.2]} opacity={0.55} />
    </>
  );
};
