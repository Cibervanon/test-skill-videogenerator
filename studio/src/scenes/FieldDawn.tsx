import React from "react";
import { useCurrentFrame } from "remotion";
import { ParallaxGroup } from "../engine/CameraRig";
import { Particles } from "../engine/Snow";
import { prng, hashString } from "../engine/math";
import { CastShadow, FogBand, Glow, LightShaft, SoftBlurDefs } from "../engine/atmosphere";
import { MaterialDefs } from "../engine/texture";

const MAT = {
  stone: "#a89a93",
  stoneLight: "#bcaea6",
  mortar: "#6f615c",
  wood: "#6b5348",
  woodLight: "#87695a",
  woodLine: "#3b2a28",
  roof: "#6d5548",
  roofLight: "#84695a",
  roofLine: "#3b2a28",
  snow: "#f3e4d4",
  snowLine: "#cdb6a4",
  snowAccent: "#fffaf2",
  carpet: "#8a4a44",
  carpetLine: "#6a3530",
  carpetAccent: "#c9a25f",
  wall: "#b5a396",
  wallLine: "#7d6a60",
  wallAccent: "#c9b6a6",
  frost: "#e6f0ff",
  ink: "#3a2b2c",
};

type StoneKind = "round" | "cross" | "obelisk" | "slab";

/**
 * A headstone. The first pass drew a rectangle plus a bar, which read as a fence
 * post; these are single continuous silhouettes with an inset border, a carving
 * block and a snow cap, so the shape identifies the object at thumbnail size.
 */
const Headstone: React.FC<{ x: number; y: number; w: number; h: number; kind: StoneKind; tilt: number; seed: number }> = ({
  x,
  y,
  w,
  h,
  kind,
  tilt,
  seed,
}) => {
  const rnd = prng(hashString(`stone2-${seed}`));
  const moss = 0.25 + rnd() * 0.35;
  return (
    <g transform={`translate(${x} ${y}) rotate(${tilt})`}>
      <ellipse cx={0} cy={3} rx={w * 0.95} ry={7} fill="rgba(90,70,64,0.2)" />
      {/* base */}
      <rect x={-w / 2 - 6} y={-8} width={w + 12} height={10} rx={2} fill="#8a7b74" stroke={MAT.ink} strokeWidth={2} />

      {kind === "round" ? (
        <g>
          <path
            d={`M ${-w / 2} 0 L ${-w / 2} ${-h * 0.62} Q 0 ${-h * 1.02} ${w / 2} ${-h * 0.62} L ${w / 2} 0 Z`}
            fill="url(#field-stone)"
            stroke={MAT.ink}
            strokeWidth={3}
          />
          <path
            d={`M ${-w * 0.32} ${-h * 0.5} L ${-w * 0.32} ${-h * 0.1} L ${w * 0.32} ${-h * 0.1} L ${w * 0.32} ${-h * 0.5} Q 0 ${-h * 0.8} ${-w * 0.32} ${-h * 0.5} Z`}
            fill="none"
            stroke="#7d6a60"
            strokeWidth={2.2}
            opacity={0.7}
          />
          <g stroke="#6f5f57" strokeWidth={2.4} strokeLinecap="round" opacity={0.8}>
            <path d={`M ${-w * 0.16} ${-h * 0.4} L ${w * 0.16} ${-h * 0.4}`} />
            <path d={`M ${-w * 0.16} ${-h * 0.3} L ${w * 0.16} ${-h * 0.3}`} />
            <path d={`M ${-w * 0.1} ${-h * 0.2} L ${w * 0.1} ${-h * 0.2}`} />
          </g>
        </g>
      ) : null}

      {/* A thin shaft with a wide arm on top reads as a lollipop at thumbnail
          size. This is a solid slab with the cross carved on its face, the way
          a village mason would actually cut one. */}
      {kind === "cross" ? (
        <g>
          <path
            d={`M ${-w / 2} 0 L ${-w / 2} ${-h * 0.58} Q 0 ${-h * 0.84} ${w / 2} ${-h * 0.58} L ${w / 2} 0 Z`}
            fill="url(#field-stone)"
            stroke={MAT.ink}
            strokeWidth={3}
          />
          <g stroke="#6f5f57" strokeLinecap="round" opacity={0.85}>
            <path d={`M 0 ${-h * 0.12} L 0 ${-h * 0.6}`} strokeWidth={6} />
            <path d={`M ${-w * 0.26} ${-h * 0.44} L ${w * 0.26} ${-h * 0.44}`} strokeWidth={6} />
          </g>
        </g>
      ) : null}

      {kind === "obelisk" ? (
        <g>
          <path
            d={`M ${-w * 0.36} 0 L ${-w * 0.22} ${-h * 0.74} L 0 ${-h} L ${w * 0.22} ${-h * 0.74} L ${w * 0.36} 0 Z`}
            fill="url(#field-stone)"
            stroke={MAT.ink}
            strokeWidth={3}
          />
          <path d={`M ${-w * 0.2} ${-h * 0.28} L ${w * 0.2} ${-h * 0.28}`} stroke="#7d6a60" strokeWidth={3} opacity={0.55} />
        </g>
      ) : null}

      {kind === "slab" ? (
        <g>
          <path
            d={`M ${-w / 2} 0 L ${-w / 2} ${-h * 0.68} Q 0 ${-h * 0.86} ${w / 2} ${-h * 0.68} L ${w / 2} 0 Z`}
            fill="url(#field-stone)"
            stroke={MAT.ink}
            strokeWidth={3}
          />
          <g stroke="#6f5f57" strokeWidth={2.4} strokeLinecap="round" opacity={0.75}>
            <path d={`M ${-w * 0.34} ${-h * 0.48} L ${w * 0.34} ${-h * 0.48}`} />
            <path d={`M ${-w * 0.28} ${-h * 0.36} L ${w * 0.28} ${-h * 0.36}`} />
          </g>
        </g>
      ) : null}

      {/* moss + snow cap, the two cues that read as "old stone in winter" */}
      <g opacity={moss}>
        <path d={`M ${-w * 0.46} 0 q ${w * 0.2} ${-h * 0.12} ${w * 0.44} 0 q ${-w * 0.22} ${h * 0.03} ${-w * 0.44} 0 z`} fill="#7d8a63" />
        <circle cx={-w * 0.26} cy={-h * 0.22} r={2.4} fill="#7d8a63" />
      </g>
      <path
        d={kind === "obelisk" ? `M ${-w * 0.1} ${-h * 0.9} Q 0 ${-h * 0.99} ${w * 0.1} ${-h * 0.9}` : `M ${-w * 0.42} ${-h * 0.64} Q 0 ${-h * 0.82} ${w * 0.42} ${-h * 0.64}`}
        stroke="#fffaf2"
        strokeWidth={6}
        fill="none"
        opacity={0.92}
        strokeLinecap="round"
      />
    </g>
  );
};

export const FieldDawn: React.FC<{ progress: number }> = ({ progress }) => {
  const frame = useCurrentFrame();
  const rnd = prng(hashString("graves-v3"));

  const stones = new Array(11).fill(0).map((_, i) => ({
    x: 40 + i * 96 + rnd() * 22,
    w: 62 + rnd() * 26,
    h: 96 + rnd() * 50,
    kind: (["round", "cross", "obelisk", "slab", "round", "cross"] as StoneKind[])[i % 6],
    tilt: (rnd() - 0.5) * 7,
    y: 1298 + rnd() * 22,
  }));

  const grass = new Array(18).fill(0).map((_, i) => ({
    x: 120 + (i % 9) * 104 + rnd() * 26,
    y: 1560 + Math.floor(i / 9) * 190 + rnd() * 40,
    h: 20 + rnd() * 26,
    lean: (rnd() - 0.5) * 12,
  }));

  const birds = new Array(6).fill(0).map((_, i) => ({
    x: ((frame * (0.8 + i * 0.1) + i * 220) % 1300) - 120,
    y: 380 + i * 42 + Math.sin(frame / 22 + i) * 9,
    s: 0.6 + i * 0.1,
  }));

  return (
    <>
      <svg viewBox="0 0 1080 1920" preserveAspectRatio="xMidYMid slice" style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }}>
        <defs>
          <linearGradient id="field-sky" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#2f3a66" />
            <stop offset="30%" stopColor="#8f5f72" />
            <stop offset="58%" stopColor="#e08a6e" />
            <stop offset="82%" stopColor="#f7b98a" />
            <stop offset="100%" stopColor="#ffd9a8" />
          </linearGradient>
          <radialGradient id="field-sun">
            <stop offset="0%" stopColor="#fff7dc" stopOpacity="0.95" />
            <stop offset="38%" stopColor="#ffd08a" stopOpacity="0.45" />
            <stop offset="100%" stopColor="#ffb765" stopOpacity="0" />
          </radialGradient>
          <linearGradient id="field-snowground" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#fbeedf" />
            <stop offset="45%" stopColor="#f2dfc9" />
            <stop offset="100%" stopColor="#dcc0a6" />
          </linearGradient>
          <linearGradient id="field-stone" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#c6b8ae" />
            <stop offset="55%" stopColor="#a3948c" />
            <stop offset="100%" stopColor="#82736c" />
          </linearGradient>
          <linearGradient id="field-soil" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#5a3d2c" />
            <stop offset="60%" stopColor="#3d2a1e" />
            <stop offset="100%" stopColor="#241710" />
          </linearGradient>
          <filter id="softBlur" x="-40%" y="-40%" width="180%" height="180%">
            <feGaussianBlur stdDeviation={9} />
          </filter>
          <filter id="field-branch" x="-40%" y="-40%" width="180%" height="180%">
            <feGaussianBlur stdDeviation={14} />
          </filter>
          <MaterialDefs prefix="field" palette={MAT} />
          <SoftBlurDefs id="field-soft" />
        </defs>

        <rect width="1080" height="1920" fill="url(#field-sky)" />
        <g opacity={0.15} fill="#f6c7a8" filter="url(#field-branch)">
          <path d="M -40 380 q 240 -34 460 -4 q 220 30 420 -10 q 140 -26 260 6 l 0 40 q -240 30 -460 4 q -220 -26 -420 8 q -140 22 -260 -4 z" />
          <path d="M 60 540 q 260 -24 480 2 q 200 22 400 -6 l 0 30 q -240 26 -460 2 q -200 -20 -420 6 z" opacity={0.7} />
        </g>
        <circle cx={720} cy={880} r={430} fill="url(#field-sun)" />
        <circle cx={720} cy={880} r={66} fill="#fff2cf" opacity={0.95} />

        {birds.map((b, i) => (
          <path
            key={i}
            d={`M ${b.x} ${b.y} q ${9 * b.s} ${-8 * b.s} ${18 * b.s} 0 q ${9 * b.s} ${-8 * b.s} ${18 * b.s} 0`}
            stroke="#5a3f4a"
            strokeWidth={2.2}
            fill="none"
            opacity={0.5}
          />
        ))}

        <ParallaxGroup depth={0.1} progress={progress}>
          <path d="M 0 1020 Q 180 992 340 1014 Q 540 1040 720 1000 Q 900 962 1080 1006 L 1080 1050 L 0 1050 Z" fill="#8a5f68" opacity={0.55} />
          {[20, 96, 168, 250, 318, 392, 470, 548, 626, 700, 780, 856, 930, 1004, 1060].map((x, i) => {
            const h = 74 + (i % 5) * 20;
            return (
              <g key={i} transform={`translate(${x} 1046)`}>
                <path
                  d={`M 0 ${-h} L ${-h * 0.32} ${-h * 0.32} L ${-h * 0.17} ${-h * 0.34} L ${-h * 0.4} 0 L ${h * 0.4} 0 L ${h * 0.17} ${-h * 0.34} L ${h * 0.32} ${-h * 0.32} Z`}
                  fill="#6a4752"
                  opacity={0.42 + (i % 3) * 0.09}
                />
              </g>
            );
          })}
          <g transform="translate(880 1020)" fill="#5a3f4c" opacity={0.8}>
            <rect x={-56} y={-96} width={112} height={96} />
            <path d="M -56 -96 L 0 -150 L 56 -96 Z" />
            <path d="M -14 -150 L -14 -210 L 14 -210 L 14 -150 Z" />
            <path d="M 0 -210 L 0 -238 M -10 -224 L 10 -224" stroke="#5a3f4c" strokeWidth={5} />
            <rect x={-30} y={-70} width={22} height={32} fill="#f7c98a" opacity={0.5} />
          </g>
        </ParallaxGroup>

        <path d="M 0 1050 Q 300 1026 560 1044 Q 820 1062 1080 1036 L 1080 1920 L 0 1920 Z" fill="url(#field-snowground)" />
        <rect y={1060} width={1080} height={700} fill="url(#field-snow)" opacity={0.6} />
        <g stroke="#fffaf2" fill="none" opacity={0.5} strokeLinecap="round">
          <path d="M 0 1180 q 240 -20 480 4 q 260 24 600 -8" strokeWidth={7} />
          <path d="M 80 1360 q 280 -22 540 2" strokeWidth={5} />
          <path d="M -20 1700 q 260 -26 520 0 q 300 26 600 -12" strokeWidth={8} />
        </g>

        <ParallaxGroup depth={0.26} progress={progress}>
          <g>
            {new Array(15).fill(0).map((_, i) => (
              <g key={i} transform={`translate(${i * 76} 1148)`}>
                <rect x={0} y={0} width={8} height={100} fill={`url(#field-plank)`} stroke={MAT.ink} strokeWidth={2} />
                <rect x={-2} y={-4} width={12} height={6} rx={3} fill="#fffaf2" opacity={0.9} />
                <ellipse cx={4} cy={102} rx={11} ry={4} fill="rgba(90,70,64,0.2)" />
              </g>
            ))}
            <rect x={0} y={34} width={1080} height={5} fill="#6b5348" opacity={0.9} />
            <rect x={0} y={70} width={1080} height={5} fill="#6b5348" opacity={0.9} />
            <rect x={0} y={32} width={1080} height={3} fill="#fffaf2" opacity={0.5} />
          </g>
        </ParallaxGroup>

        <ParallaxGroup depth={0.38} progress={progress}>
          {stones.map((s, i) => (
            <g key={i}>
              <CastShadow cx={s.x - 100} cy={s.y + 4} rx={120} ry={15} rotate={-6} opacity={0.15} />
              <Headstone x={s.x} y={s.y} w={s.w} h={s.h} kind={s.kind} tilt={s.tilt} seed={i} />
            </g>
          ))}
        </ParallaxGroup>

        {/* open grave: layered soil, rim light, board and a planted shovel */}
        <g transform="translate(700 1520)">
          <CastShadow cx={-40} cy={40} rx={290} ry={50} opacity={0.2} />
          <ellipse cx={0} cy={-4} rx={172} ry={46} fill="#6a4a36" />
          <ellipse cx={0} cy={-8} rx={154} ry={38} fill="url(#field-soil)" />
          {/* inner shadow: without it the pit reads as a flat brown lid */}
          <ellipse cx={0} cy={-12} rx={132} ry={28} fill="#1b120c" opacity={0.35} />
          <path d="M -154 -8 Q 0 64 154 -8" stroke="#8a6446" strokeWidth={9} fill="none" opacity={0.8} />
          <path d="M -150 2 Q 0 74 150 2" stroke="#c69a6c" strokeWidth={4} fill="none" opacity={0.45} />
          <path d="M -140 14 q 140 44 280 0" stroke="#7a5a42" strokeWidth={4} fill="none" opacity={0.5} />
          <path d="M -120 -22 q 120 30 240 0" stroke="#2a1c14" strokeWidth={3} fill="none" opacity={0.5} />
          <path d="M -90 34 q 90 26 180 0" stroke="#8f6748" strokeWidth={3} fill="none" opacity={0.4} />
          <path d="M -268 34 q 74 -70 164 -34 q 74 28 142 -10 q 30 46 -6 70 q -142 42 -300 -26 z" fill="#6f4c38" />
          <path d="M -268 34 q 74 -70 164 -34 q 74 28 142 -10" stroke="#8f6748" strokeWidth={4} fill="none" opacity={0.6} />
          <path d="M -264 32 q 74 -66 162 -32 q 74 26 140 -12" stroke="#ffe0bc" strokeWidth={4} fill="none" opacity={0.45} />
          {new Array(12).fill(0).map((_, i) => (
            <ellipse key={i} cx={-196 + i * 38} cy={26 + (i % 3) * 12} rx={8} ry={4.5} fill="#3f2a1e" opacity={0.55} />
          ))}
          <g transform="translate(-190 60) rotate(-6)">
            <rect width={150} height={14} rx={3} fill="#8a6a4a" stroke={MAT.ink} strokeWidth={2.4} />
            <rect width={150} height={5} rx={2} fill="#b08a62" opacity={0.7} />
          </g>
          {/* The apprentice already carries the shovel: a second one planted in
              the mound read as a stray prop, so the pit keeps only the plank. */}
        </g>

        {/* a stone wall segment, mid-ground right: another plane, not another prop */}
        <g transform="translate(880 1460)" opacity={0.95}>
          <rect x={0} y={0} width={240} height={86} fill="url(#field-stone)" stroke={MAT.ink} strokeWidth={3} />
          <path d="M 0 0 q 120 -16 240 0 l 0 14 q -120 -14 -240 0 z" fill="#fffaf2" opacity={0.85} />
          <rect x={0} y={-6} width={240} height={8} fill="#8a7b74" />
        </g>

        <g opacity={0.28} fill="#9a8272">
          {[0, 1, 2, 3, 4, 5].map((i) => (
            <ellipse key={i} cx={300 + i * 52} cy={1660 + i * 34} rx={12} ry={6} transform={`rotate(${-16 + i * 3} ${300 + i * 52} ${1660 + i * 34})`} />
          ))}
        </g>

        <g stroke="#9a7a5c" strokeWidth={3} fill="none" opacity={0.7} strokeLinecap="round">
          {grass.map((g, i) => (
            <g key={i}>
              <path d={`M ${g.x} ${g.y} q ${g.lean} ${-g.h * 0.6} ${g.lean * 1.6} ${-g.h}`} />
              <path d={`M ${g.x + 6} ${g.y} q ${g.lean * 0.6} ${-g.h * 0.4} ${g.lean * 1.1} ${-g.h * 0.7}`} />
            </g>
          ))}
        </g>

        <g filter="url(#field-branch)" opacity={0.6}>
          <path d="M 1120 1180 q -160 60 -230 170 q -60 96 -30 220" stroke="#4a2f2a" strokeWidth={30} fill="none" strokeLinecap="round" />
          <path d="M 980 1330 q -80 20 -130 70" stroke="#4a2f2a" strokeWidth={16} fill="none" strokeLinecap="round" />
        </g>
        <path d="M -20 1830 Q 260 1782 560 1826 Q 820 1866 1100 1810 L 1100 1920 L -20 1920 Z" fill="#f6e7d4" />
        <rect y={1830} width={1080} height={90} fill="url(#field-snow)" opacity={0.45} />

        <FogBand id="field-mist" y={1150} height={260} color="#ffe7cc" opacity={0.22} />
        <LightShaft id="field-sunbeam" d="M 660 880 L 800 880 L 980 1500 L 520 1500 Z" color="#ffd9a8" opacity={0.12} blur={30} />
        <Glow id="field-sunglow" cx={720} cy={880} r={240} color="#ffe6b8" opacity={0.22} />
      </svg>

      <Particles count={34} seed="dawnDust2" size={[1.5, 4]} speed={[0.2, 0.6]} opacity={0.4} color="#fff6e2" area={0.75} />
    </>
  );
};
