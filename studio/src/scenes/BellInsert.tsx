import React from "react";
import { useCurrentFrame } from "remotion";
import { Particles } from "../engine/Snow";
import { DustMotes, Glow, LightShaft, SoftBlurDefs } from "../engine/atmosphere";
import { MaterialDefs } from "../engine/texture";

const MAT = {
  stone: "#2c3050",
  stoneLight: "#3a4066",
  mortar: "#1c2038",
  wood: "#4a3a2c",
  woodLight: "#5e4a36",
  woodLine: "#241a14",
  roof: "#2a2a3e",
  roofLight: "#38384f",
  roofLine: "#1a1a28",
  snow: "#cdd8ee",
  snowLine: "#8f9dc4",
  snowAccent: "#ffffff",
  carpet: "#3a2a3e",
  carpetLine: "#241a28",
  carpetAccent: "#8a5a4a",
  wall: "#333a5c",
  wallLine: "#22284a",
  wallAccent: "#4a5478",
  frost: "#cfe0ff",
  ink: "#141020",
};

/** The belfry: stone wall, louvred opening, timber headstock, bronze bell. */
export const BellInsert: React.FC<{ progress: number }> = ({ progress }) => {
  const frame = useCurrentFrame();
  const sway = Math.sin(frame / 52) * 1.1 + progress * 1.4;
  const flicker = 0.9 + Math.sin(frame / 9) * 0.05;

  return (
    <>
      <svg viewBox="0 0 1080 1920" preserveAspectRatio="xMidYMid slice" style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }}>
        <defs>
          <linearGradient id="bell-ambient" x1="0" y1="0" x2="0.4" y2="1">
            <stop offset="0%" stopColor="#0b1024" />
            <stop offset="55%" stopColor="#1b2344" />
            <stop offset="100%" stopColor="#2b2f4e" />
          </linearGradient>
          <linearGradient id="bell-bronze" x1="0.1" y1="0" x2="0.9" y2="1">
            <stop offset="0%" stopColor="#f0d79b" />
            <stop offset="26%" stopColor="#c99a4c" />
            <stop offset="62%" stopColor="#9a6a2c" />
            <stop offset="100%" stopColor="#5e3d1a" />
          </linearGradient>
          <linearGradient id="bell-verdigris" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#6f9a86" stopOpacity="0" />
            <stop offset="60%" stopColor="#6f9a86" stopOpacity="0.35" />
            <stop offset="100%" stopColor="#4a6f60" stopOpacity="0.5" />
          </linearGradient>
          <radialGradient id="bell-key">
            <stop offset="0%" stopColor="#ffd79a" stopOpacity="0.3" />
            <stop offset="60%" stopColor="#ffbf7a" stopOpacity="0.08" />
            <stop offset="100%" stopColor="#ffbf7a" stopOpacity="0" />
          </radialGradient>
          <filter id="softBlur" x="-40%" y="-40%" width="180%" height="180%">
            <feGaussianBlur stdDeviation={8} />
          </filter>
          <MaterialDefs prefix="bell" palette={MAT} />
          <SoftBlurDefs id="bell-soft" />
          <clipPath id="bell-clip">
            <path d="M -220 62 C -152 24 -130 -70 -122 -166 C -114 -250 -84 -302 -46 -320 C -22 -332 22 -332 46 -320 C 84 -302 114 -250 122 -166 C 130 -70 152 24 220 62 C 118 110 -118 110 -220 62 Z" />
          </clipPath>
        </defs>

        {/* belfry wall */}
        <rect width="1080" height="1920" fill="url(#bell-ambient)" />
        <rect x={-20} y={0} width={1120} height={1920} fill="url(#bell-stone)" opacity={0.55} />
        {/* stone arch opening, out of focus: the source of the cold light */}
        <g opacity={0.9}>
          <path d="M 180 1920 L 180 520 Q 540 300 900 520 L 900 1920 Z" fill="#0d1730" />
          <path d="M 180 520 Q 540 300 900 520" stroke="#46507a" strokeWidth={14} fill="none" opacity={0.6} />
          {/* louvres: thick slats with a dark gap between them. Thin lines read
              as scan lines; slats read as a belfry. */}
          {new Array(8).fill(0).map((_, i) => (
            <g key={i}>
              <rect x={236} y={566 + i * 76} width={608} height={44} fill="#101a34" opacity={0.95} />
              <rect x={240} y={578 + i * 76} width={600} height={20} fill="#33405f" />
              <rect x={240} y={578 + i * 76} width={600} height={3} fill="#9fb8e8" opacity={0.4} />
              <rect x={240} y={598 + i * 76} width={600} height={4} fill="#070c1c" opacity={0.7} />
            </g>
          ))}
          {/* stone arch rim around the opening */}
          <path d="M 168 620 Q 540 288 912 620" stroke="#39405f" strokeWidth={40} fill="none" opacity={0.9} />
          <path d="M 168 620 Q 540 288 912 620" stroke="#4a5478" strokeWidth={6} fill="none" opacity={0.45} />
        </g>
        <LightShaft id="bell-shaft" d="M 240 560 L 840 560 L 640 1500 L 180 1500 Z" color="#9fb8e8" opacity={0.14} blur={30} />

        {/* timber headstock with iron straps */}
        <g>
          <rect x={-20} y={430} width={1120} height={96} fill="url(#bell-plank)" stroke="#1a1210" strokeWidth={5} />
          <rect x={-20} y={430} width={1120} height={16} fill="#6a5238" opacity={0.5} />
          {[120, 420, 660, 900].map((x, i) => (
            <g key={i}>
              <rect x={x} y={424} width={26} height={108} rx={4} fill="#2a2320" stroke="#141010" strokeWidth={3} />
              <circle cx={x + 13} cy={452} r={4} fill="#6a6258" />
              <circle cx={x + 13} cy={504} r={4} fill="#6a6258" />
            </g>
          ))}
          {/* hanger + bell */}
          <rect x={-26} y={526} width={52} height={54} rx={6} fill="url(#bell-plank)" stroke="#1a1210" strokeWidth={4} />
          <g transform={`translate(540 900) rotate(${sway})`}>
            <circle cx={0} cy={-180} r={470} fill="url(#bell-key)" opacity={flicker} />
            <path d="M 0 -300 v 20" stroke="#2a1f18" strokeWidth={14} />
            <circle cx={0} cy={-278} r={22} fill="#2a1f18" />
            {/* bell body */}
            <path
              d="M -220 62 C -152 24 -130 -70 -122 -166 C -114 -250 -84 -302 -46 -320 C -22 -332 22 -332 46 -320 C 84 -302 114 -250 122 -166 C 130 -70 152 24 220 62 C 118 110 -118 110 -220 62 Z"
              fill="url(#bell-bronze)"
              stroke="#2a1a10"
              strokeWidth={7}
            />
            <path
              d="M -220 62 C -152 24 -130 -70 -122 -166 C -114 -250 -84 -302 -46 -320 C -22 -332 22 -332 46 -320 C 84 -302 114 -250 122 -166 C 130 -70 152 24 220 62 C 118 110 -118 110 -220 62 Z"
              fill="url(#bell-verdigris)"
              opacity={0.8}
            />
            {/* rim light from the louvres + a darker heel, so the bronze turns */}
            <path
              d="M -178 44 C -142 12 -128 -80 -120 -164 C -112 -248 -82 -300 -44 -318"
              stroke="#ffe6b8"
              strokeWidth={9}
              fill="none"
              opacity={0.45}
              strokeLinecap="round"
            />
            <path
              d="M 152 26 C 130 4 124 -46 120 -96"
              stroke="#3a240f"
              strokeWidth={16}
              fill="none"
              opacity={0.3}
              strokeLinecap="round"
            />
            {/* engraved bands, clipped so they cannot float off the bell */}
            <g clipPath="url(#bell-clip)">
              <path d="M -176 -104 q 176 58 352 0" stroke="#f4dfa6" strokeWidth={7} fill="none" opacity={0.5} />
              <path d="M -192 -62 q 192 60 384 0" stroke="#52351a" strokeWidth={8} fill="none" opacity={0.65} />
              <path d="M -208 -20 q 208 62 416 0" stroke="#e0c184" strokeWidth={4} fill="none" opacity={0.3} />
              {[0, 1, 2, 3, 4, 5, 6, 7].map((i) => (
                <circle key={i} cx={-140 + i * 40} cy={-40 + Math.abs(3.5 - i) * 5} r={3.4} fill="#f4dfa6" opacity={0.35} />
              ))}
            </g>
            <ellipse cx={0} cy={64} rx={220} ry={46} fill="#3a2612" stroke="#2a1a10" strokeWidth={6} />
            <ellipse cx={0} cy={58} rx={192} ry={31} fill="#150e08" />
            <ellipse cx={0} cy={58} rx={192} ry={31} fill="#5a3d1c" opacity={0.35} />
            {/* clapper */}
            <g transform={`translate(${Math.sin(frame / 52) * 12} 78)`}>
              <path d="M 0 0 L 0 84" stroke="#3a2a1c" strokeWidth={12} />
              <ellipse cx={0} cy={106} rx={44} ry={50} fill="#8a6132" stroke="#2a1a10" strokeWidth={6} />
              <ellipse cx={-14} cy={92} rx={12} ry={16} fill="#d8b071" opacity={0.45} />
            </g>
            {/* frost / patina specks */}
            {[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11].map((i) => (
              <circle key={i} cx={-170 + i * 30} cy={-292 + (i % 6) * 46} r={2.2} fill="#fff2d0" opacity={0.4} />
            ))}
          </g>
        </g>

        {/* pulley + rope, twisted, going out of the top of frame */}
        <circle cx={540} cy={470} r={26} fill="#3a2a1c" stroke="#141010" strokeWidth={4} />
        <circle cx={540} cy={470} r={9} fill="#6a6258" />
        <path d="M 540 470 q -26 -150 -8 -290" stroke="#c9ac86" strokeWidth={13} fill="none" />
        <path d="M 540 470 q -26 -150 -8 -290" stroke="#8a7150" strokeWidth={3} fill="none" strokeDasharray="7 9" opacity={0.8} />
        <path d="M 540 470 q -6 -150 4 -290" stroke="#e6d2b0" strokeWidth={3} fill="none" opacity={0.35} />

        {/* foreground: blurred rope edge + dust in the shaft */}
        <g filter="url(#softBlur)" opacity={0.5}>
          <path d="M 60 1920 q 60 -220 30 -420" stroke="#1a1420" strokeWidth={40} fill="none" />
        </g>
        <DustMotes count={44} seed={21} frame={frame} area={{ x: 220, y: 520, w: 620, h: 900 }} color="#ffe3ae" />
        <Glow id="bell-rimlight" cx={540} cy={760} r={300} color="#ffd79a" opacity={0.14} />
      </svg>
      <Particles count={18} seed="bellSnow2" size={[2, 5]} speed={[0.3, 0.8]} opacity={0.3} />
    </>
  );
};
