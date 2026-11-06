import React from "react";
import { useCurrentFrame } from "remotion";
import { Particles } from "../engine/Snow";
import { ParallaxGroup } from "../engine/CameraRig";
import { prng, hashString } from "../engine/math";
import { CastShadow, FogBand, Glow, LightShaft, LightVeil, SoftBlurDefs } from "../engine/atmosphere";
import { MaterialDefs } from "../engine/texture";

const MAT = {
  stone: "#3a3f66",
  stoneLight: "#4a5079",
  mortar: "#252a4a",
  wood: "#4a3a38",
  woodLight: "#5c4844",
  woodLine: "#2a1f22",
  roof: "#2a3155",
  roofLight: "#353d66",
  roofLine: "#1a1f3c",
  snow: "#dbe3f4",
  snowLine: "#9aa8cf",
  snowAccent: "#ffffff",
  carpet: "#3a2b40",
  carpetLine: "#241a2c",
  carpetAccent: "#8a5a4a",
  wall: "#2c3054",
  wallLine: "#20244a",
  wallAccent: "#4a4f78",
  frost: "#cfe0ff",
  ink: "#0d1024",
};

/** Timber-framed house: stone base, plank walls, shingled roof, lit windows. */
const House: React.FC<{
  x: number;
  y: number;
  w: number;
  h: number;
  flip?: boolean;
  lit?: [boolean, boolean];
  sign?: boolean;
  chimney?: boolean;
  frame: number;
  prefix: string;
}> = ({ x, y, w, h, flip = false, lit = [true, false], sign = false, chimney = true, frame, prefix }) => {
  const roofH = w * 0.42;
  const smoke = 0.5 + 0.5 * Math.sin(frame / 30);
  return (
    <g transform={`translate(${x} ${y}) scale(${flip ? -1 : 1} 1)`}>
      {/* stone base */}
      <rect x={0} y={-h * 0.22} width={w} height={h * 0.22} fill={`url(#${prefix}-stone)`} stroke={MAT.ink} strokeWidth={2.6} />
      {/* plank wall */}
      <rect x={0} y={-h} width={w} height={h * 0.79} fill={`url(#${prefix}-plank)`} stroke={MAT.ink} strokeWidth={3} />
      {/* timber frame */}
      {/* corner posts, sill and a mid rail: the X-bracing of the first pass
          read as scribbles across the windows */}
      <g stroke="#2a1c1e" strokeWidth={7} strokeLinecap="square" opacity={0.8}>
        <path d={`M 0 ${-h} L 0 ${-h * 0.2}`} />
        <path d={`M ${w} ${-h} L ${w} ${-h * 0.2}`} />
        <path d={`M -4 ${-h * 0.63} L ${w + 4} ${-h * 0.63}`} />
        <path d={`M ${w * 0.05} ${-h * 0.2} L ${w * 0.18} ${-h * 0.56}`} />
        <path d={`M ${w * 0.95} ${-h * 0.2} L ${w * 0.82} ${-h * 0.56}`} />
      </g>
      {/* roof */}
      <path d={`M ${-14} ${-h} L ${w / 2} ${-h - roofH} L ${w + 14} ${-h} Z`} fill={`url(#${prefix}-shingle)`} stroke={MAT.ink} strokeWidth={3} />
      <path d={`M ${-6} ${-h - 4} L ${w / 2} ${-h - roofH * 0.92} L ${w + 6} ${-h - 4}`} stroke="#e9effb" strokeWidth={8} fill="none" strokeLinecap="round" opacity={0.95} />
      {/* icicles */}
      {[0.16, 0.3, 0.52, 0.68, 0.84].map((t, i) => (
        <path key={i} d={`M ${w * t} ${-h + 2} l 5 ${12 + (i % 3) * 8} l 5 ${-(12 + (i % 3) * 8)} z`} fill="#dce8fb" opacity={0.8} />
      ))}
      {/* chimney + smoke */}
      {chimney ? (
        <g>
          <rect x={w * 0.72} y={-h - roofH * 0.72} width={18} height={roofH * 0.62} fill="#4a3a44" stroke={MAT.ink} strokeWidth={2.4} />
          <rect x={w * 0.72} y={-h - roofH * 0.74} width={18} height={5} fill="#e9effb" />
          <path
            d={`M ${w * 0.72 + 9} ${-h - roofH * 0.78} q ${-10 - smoke * 8} -22 ${6 - smoke * 10} -46 q ${16 + smoke * 6} -20 ${2} -44`}
            stroke="#c9d3e8"
            strokeWidth={7 - smoke * 2}
            fill="none"
            opacity={0.16 + smoke * 0.1}
            strokeLinecap="round"
          />
        </g>
      ) : null}
      {/* windows */}
      {[0.16, 0.58].map((t, i) => (
        <g key={i} transform={`translate(${w * t} ${-h * 0.72})`}>
          <rect x={-2} y={-2} width={w * 0.24 + 4} height={h * 0.2 + 4} fill="#1a1e3a" stroke={MAT.ink} strokeWidth={3} />
          <rect x={0} y={0} width={w * 0.24} height={h * 0.2} fill={lit[i] ? "#ffc179" : "#2c3258"} opacity={lit[i] ? 0.95 : 1} />
          <path d={`M ${w * 0.12} 0 L ${w * 0.12} ${h * 0.2} M 0 ${h * 0.1} L ${w * 0.24} ${h * 0.1}`} stroke="#1a1e3a" strokeWidth={3} />
          {lit[i] ? <rect x={0} y={0} width={w * 0.24} height={h * 0.2} fill="url(#town-window)" opacity={0.7} /> : null}
          {/* snow on the sill */}
          <rect x={-4} y={h * 0.2} width={w * 0.24 + 8} height={5} rx={2.5} fill="#e9effb" opacity={0.9} />
          {lit[i] ? <LightShaft id={`${prefix}-shaft${i}-${Math.round(x)}`} d={`M ${0} ${0} L ${w * 0.24} ${0} L ${w * 0.24 + 40} ${h * 0.9} L ${-70} ${h * 0.9} Z`} color="#ffc179" opacity={0.1} blur={22} /> : null}
        </g>
      ))}
      {/* door */}
      <g transform={`translate(${w * 0.38} ${-h * 0.32})`}>
        <rect width={w * 0.2} height={h * 0.32} fill="#332423" stroke={MAT.ink} strokeWidth={3} />
        <rect x={w * 0.03} y={h * 0.03} width={w * 0.14} height={h * 0.11} fill="none" stroke="#5a3f38" strokeWidth={2} />
        <circle cx={w * 0.16} cy={h * 0.2} r={2.6} fill="#d3a55f" />
        <rect y={-6} width={w * 0.2} height={8} rx={3} fill="#e9effb" opacity={0.85} />
      </g>
      {/* hanging shop sign */}
      {sign ? (
        <g transform={`translate(${w * 0.86} ${-h * 0.9})`}>
          <path d="M 0 0 L 26 0 M 26 0 L 26 26" stroke="#2a1c1e" strokeWidth={5} fill="none" />
          <rect x={10} y={26} width={46} height={34} rx={4} fill="#6b4a34" stroke={MAT.ink} strokeWidth={3} transform={`rotate(${Math.sin(frame / 50) * 2} 33 43)`} />
          <circle cx={33} cy={43} r={9} fill="none" stroke="#d9b071" strokeWidth={3} transform={`rotate(${Math.sin(frame / 50) * 2} 33 43)`} />
        </g>
      ) : null}
    </g>
  );
};

/** The bell post: braced timber frame, bronze bell, lantern, snow caps. */
const BellPost: React.FC<{ frame: number; prefix: string }> = ({ frame, prefix }) => {
  const swing = Math.sin(frame / 90) * 0.8;
  return (
    <g transform="translate(560 1330)">
      {/* stone plinth + post */}
      <rect x={-34} y={-24} width={68} height={26} rx={4} fill={`url(#${prefix}-stone)`} stroke={MAT.ink} strokeWidth={3} />
      <rect x={-15} y={-470} width={30} height={450} fill={`url(#${prefix}-plank)`} stroke={MAT.ink} strokeWidth={4} />
      <rect x={-15} y={-470} width={8} height={450} fill="#5c4844" opacity={0.5} />
      {/* gable roof over the bell, shingled and snow-capped */}
      <path d="M -196 -500 L 0 -596 L 196 -500 Z" fill={`url(#${prefix}-shingle)`} stroke={MAT.ink} strokeWidth={4} />
      <path d="M -188 -502 L 0 -588 L 188 -502" stroke="#e9effb" strokeWidth={9} fill="none" strokeLinecap="round" opacity={0.95} />
      <path d="M 0 -596 L 0 -612" stroke={MAT.ink} strokeWidth={5} />
      {/* braces that actually meet the beam */}
      <path d="M -14 -336 L -156 -484 M 14 -336 L 156 -484" stroke="#3a2a2a" strokeWidth={13} strokeLinecap="round" />
      {/* crossbeam */}
      <rect x={-170} y={-506} width={340} height={24} rx={5} fill={`url(#${prefix}-plank)`} stroke={MAT.ink} strokeWidth={4} />
      {/* hanger + yoke + bell */}
      <rect x={-7} y={-486} width={14} height={28} fill="#3a2a24" stroke={MAT.ink} strokeWidth={3} />
      <g transform={`rotate(${swing})`}>
        <rect x={-54} y={-464} width={108} height={18} rx={6} fill="#4a3a2c" stroke={MAT.ink} strokeWidth={3} />
        <rect x={-16} y={-448} width={32} height={22} rx={5} fill="#54402f" stroke={MAT.ink} strokeWidth={3} />
        {/* bell */}
        <g transform="translate(0 -418)">
          <path
            d="M -44 46 C -30 18 -26 -8 -24 -30 C -22 -52 -14 -64 -6 -68 C -2 -70 2 -70 6 -68 C 14 -64 22 -52 24 -30 C 26 -8 30 18 44 46 C 24 56 -24 56 -44 46 Z"
            fill="url(#town-bronze)"
            stroke="#2a1a10"
            strokeWidth={3.6}
          />
          <path d="M -36 20 q 36 12 72 0" stroke="#f0d092" strokeWidth={3} fill="none" opacity={0.55} />
          <ellipse cx={0} cy={48} rx={44} ry={9} fill="#3a2612" stroke="#2a1a10" strokeWidth={3} />
          <path d="M 0 50 L 0 70" stroke="#3a2a1c" strokeWidth={5} />
          <circle cx={0} cy={76} r={8} fill="#8a6132" stroke="#2a1a10" strokeWidth={2.6} />
        </g>
      </g>
      {/* rope */}
      <path d="M 6 -452 q 12 120 -6 236" stroke="#cbb59a" strokeWidth={5} fill="none" opacity={0.85} />
      <path d="M 6 -452 q 12 120 -6 236" stroke="#8a7150" strokeWidth={1.6} fill="none" strokeDasharray="5 8" opacity={0.6} />
      {/* lantern on a bracket */}
      <g transform="translate(0 -250)">
        <path d="M 15 0 L 46 0" stroke="#2a1c1e" strokeWidth={6} />
        <path d="M 40 0 L 40 10" stroke="#2a1c1e" strokeWidth={4} />
        <g transform="translate(40 10)">
          <path d="M -12 0 h 24 l 5 26 h -34 z" fill="#f7c977" stroke={MAT.ink} strokeWidth={3} />
          <path d="M -12 0 h 24" stroke="#8a5a2a" strokeWidth={4} />
          <ellipse cx={0} cy={13} rx={8} ry={9} fill="#fff3c9" />
        </g>
        <Glow id={`${prefix}-lantern-glow`} cx={40} cy={22} r={130} color="#ffb765" opacity={0.35} />
      </g>
      <ellipse cx={0} cy={4} rx={52} ry={12} fill="rgba(20,14,30,0.4)" filter="url(#softBlur)" />
    </g>
  );
};

export const TownNight: React.FC<{ progress: number }> = ({ progress }) => {
  const frame = useCurrentFrame();
  const rnd = prng(hashString("town-v2"));
  const stars = new Array(70).fill(0).map(() => ({
    x: rnd() * 1080,
    y: rnd() * 660,
    r: 0.8 + rnd() * 2,
    a: 0.2 + rnd() * 0.7,
    tw: rnd() * 6,
  }));
  const flicker = 0.9 + Math.sin(frame / 6.5) * 0.05 + Math.sin(frame / 2.3) * 0.03;

  return (
    <>
      <svg viewBox="0 0 1080 1920" preserveAspectRatio="xMidYMid slice" style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }}>
        <defs>
          <linearGradient id="town-sky" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#0b1128" />
            <stop offset="48%" stopColor="#1d2650" />
            <stop offset="78%" stopColor="#39406e" />
            <stop offset="100%" stopColor="#4a4a72" />
          </linearGradient>
          <radialGradient id="town-moon">
            <stop offset="0%" stopColor="#f4f8ff" stopOpacity="0.95" />
            <stop offset="40%" stopColor="#cfdcff" stopOpacity="0.25" />
            <stop offset="100%" stopColor="#cfdcff" stopOpacity="0" />
          </radialGradient>
          <linearGradient id="town-bronze" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#e0bd78" />
            <stop offset="45%" stopColor="#b8893f" />
            <stop offset="100%" stopColor="#7a5222" />
          </linearGradient>
          <linearGradient id="town-window" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#fff0c0" stopOpacity="0.9" />
            <stop offset="100%" stopColor="#ff9a4a" stopOpacity="0.2" />
          </linearGradient>
          <radialGradient id="town-pool">
            <stop offset="0%" stopColor="#ffcf8a" stopOpacity="0.5" />
            <stop offset="55%" stopColor="#ffb765" stopOpacity="0.14" />
            <stop offset="100%" stopColor="#ffb765" stopOpacity="0" />
          </radialGradient>
          <linearGradient id="town-snowground" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#e7edfb" />
            <stop offset="42%" stopColor="#cfd8ee" />
            <stop offset="100%" stopColor="#a4b0d2" />
          </linearGradient>
          <filter id="town-blur" x="-30%" y="-30%" width="160%" height="160%">
            <feGaussianBlur stdDeviation={10} />
          </filter>
          <filter id="softBlur" x="-40%" y="-40%" width="180%" height="180%">
            <feGaussianBlur stdDeviation={9} />
          </filter>
          <MaterialDefs prefix="town" palette={MAT} />
          <SoftBlurDefs id="town-soft" />
        </defs>

        {/* SKY */}
        <rect width="1080" height="1920" fill="url(#town-sky)" />
        {stars.map((s, i) => (
          <circle key={i} cx={s.x} cy={s.y} r={s.r} fill="#eaf0ff" opacity={s.a * (0.55 + 0.45 * Math.sin(frame / 30 + s.tw))} />
        ))}
        {/* thin night clouds: organic, low-contrast, they give the sky a surface */}
        <g opacity={0.14} fill="#8f9dc4" filter="url(#town-blur)">
          <path d="M -40 320 q 180 -46 360 -8 q 170 34 340 -14 q 90 -22 200 4 l 0 62 q -220 34 -430 6 q -240 -30 -470 12 z" />
          <path d="M 120 470 q 200 -30 380 4 q 160 30 320 -6 l 0 46 q -220 32 -420 4 q -180 -26 -280 6 z" opacity={0.6} />
        </g>
        <circle cx={840} cy={300} r={260} fill="url(#town-moon)" />
        <circle cx={840} cy={300} r={58} fill="#f3f7ff" />
        <circle cx={818} cy={284} r={11} fill="#dde6f8" opacity={0.55} />
        <circle cx={858} cy={318} r={7} fill="#dde6f8" opacity={0.45} />

        {/* FAR: ridge, church spire, distant houses */}
        <ParallaxGroup depth={0.1} progress={progress}>
          <path d="M 0 1050 Q 200 986 380 1026 Q 560 1066 720 1004 Q 880 944 1080 1002 L 1080 1120 L 0 1120 Z" fill="#1b2246" />
          {/* church */}
          <g transform="translate(300 1030)" fill="#161c3c">
            <rect x={-40} y={-90} width={80} height={90} />
            <path d="M -40 -90 L 0 -190 L 40 -90 Z" />
            <path d="M -4 -190 L -4 -232 M -18 -214 L 12 -214" stroke="#161c3c" strokeWidth={7} />
            <rect x={-10} y={-70} width={20} height={26} fill="#ffc179" opacity={0.55} />
          </g>
          {[110, 190, 620, 700, 780, 880, 960].map((x, i) => (
            <path key={i} d={`M ${x} 1050 l 18 ${-52 - (i % 3) * 18} l 18 ${52 + (i % 3) * 18} z`} fill="#1a2144" opacity={0.9} />
          ))}
        </ParallaxGroup>

        {/* MID: the two house rows */}
        <ParallaxGroup depth={0.26} progress={progress}>
          <g>
            <House x={-60} y={1268} w={260} h={250} frame={frame} prefix="town" lit={[true, false]} sign />
            <House x={210} y={1282} w={210} h={214} frame={frame} prefix="town" lit={[false, true]} flip />
            <House x={640} y={1270} w={250} h={244} frame={frame} prefix="town" lit={[true, true]} />
            <House x={880} y={1292} w={220} h={206} frame={frame} prefix="town" lit={[false, false]} flip />
          </g>
        </ParallaxGroup>

        {/* GROUND */}
        <path d="M 0 1276 Q 280 1244 560 1268 Q 820 1292 1080 1262 L 1080 1920 L 0 1920 Z" fill="url(#town-snowground)" />
        <rect y={1280} width={1080} height={640} fill="url(#town-snow)" opacity={0.55} />
        {/* wind-carved drifts: brushy contour lines, not flat ellipses */}
        <g stroke="#f5f9ff" fill="none" opacity={0.55} strokeLinecap="round">
          <path d="M 40 1450 q 180 -26 330 6 q 140 30 300 -4" strokeWidth={7} />
          <path d="M 300 1540 q 200 -22 380 4 q 120 18 260 -8" strokeWidth={5} />
          <path d="M -20 1660 q 240 -30 480 0 q 260 30 620 -10" strokeWidth={8} />
          <path d="M 120 1760 q 300 -24 560 2" strokeWidth={5} />
        </g>
        <g stroke="#a9b6d8" fill="none" opacity={0.28} strokeWidth={3}>
          <path d="M 0 1500 q 260 -18 520 8" />
          <path d="M 420 1610 q 260 -16 520 6" />
        </g>

        {/* cast shadows of the houses, stretching towards camera */}
        <g opacity={0.5} filter="url(#town-blur)">
          <CastShadow cx={150} cy={1380} rx={210} ry={40} rotate={-8} opacity={0.28} />
          <CastShadow cx={540} cy={1420} rx={180} ry={34} rotate={6} opacity={0.24} />
          <CastShadow cx={930} cy={1390} rx={200} ry={38} rotate={10} opacity={0.26} />
        </g>

        {/* window light pools on the snow */}
        <ellipse cx={120} cy={1420} rx={230} ry={86} fill="url(#town-pool)" opacity={0.75 * flicker} />
        <ellipse cx={300} cy={1470} rx={180} ry={60} fill="url(#town-pool)" opacity={0.5 * flicker} />
        <ellipse cx={980} cy={1440} rx={210} ry={78} fill="url(#town-pool)" opacity={0.85 * flicker} />
        <ellipse cx={700} cy={1520} rx={160} ry={54} fill="url(#town-pool)" opacity={0.45} />

        {/* near row: low stone wall with snow cap, barrels, sledge */}
        <ParallaxGroup depth={0.46} progress={progress}>
          <g transform="translate(0 1440)">
            <rect x={-20} y={0} width={300} height={90} fill="url(#town-stone)" stroke={MAT.ink} strokeWidth={3} />
            <path d="M -20 0 q 150 -22 300 0 l 0 16 q -150 -18 -300 0 z" fill="#e9effb" />
          </g>
          <g transform="translate(830 1470)">
            <ellipse cx={0} cy={70} rx={130} ry={20} fill="rgba(20,14,30,0.3)" filter="url(#softBlur)" />
            <g>
              <ellipse cx={0} cy={54} rx={46} ry={12} fill="#2a1d1a" />
              <path d="M -46 54 L -40 6 q 40 -12 80 0 l 6 48 z" fill="#6b4a34" stroke={MAT.ink} strokeWidth={3} />
              <ellipse cx={0} cy={6} rx={40} ry={10} fill="#7d5a40" stroke={MAT.ink} strokeWidth={3} />
              <path d="M -40 6 q 40 -10 80 0" stroke="#c8a882" strokeWidth={3} fill="none" opacity={0.6} />
            </g>
            <g transform="translate(90 22)">
              <rect x={0} y={0} width={54} height={44} rx={4} fill="#5c4536" stroke={MAT.ink} strokeWidth={3} />
              <path d="M 0 12 L 54 12 M 27 0 L 27 44" stroke="#3a2a22" strokeWidth={3} />
              <rect x={0} y={0} width={54} height={7} rx={3} fill="#e9effb" />
            </g>
          </g>
        </ParallaxGroup>

        {/* mid-ground props: a sledge and a bucket, placed to break the empty
            snow between the figures and the right-hand house */}
        <g transform="translate(872 1580)" opacity={0.95}>
          <ellipse cx={10} cy={58} rx={120} ry={16} fill="rgba(20,14,30,0.28)" filter="url(#softBlur)" />
          <path d="M -70 40 L 62 40 L 46 58 L -56 58 Z" fill="#5c4536" stroke={MAT.ink} strokeWidth={3} />
          <path d="M -66 40 q 64 -46 128 -4" stroke="#8a6a4a" strokeWidth={7} fill="none" />
          <path d="M -66 40 q 64 -46 128 -4" stroke="#c8a882" strokeWidth={2} fill="none" opacity={0.5} />
          <path d="M -70 40 L -74 -6 M 62 40 L 66 -2" stroke="#3a2a22" strokeWidth={6} />
        </g>
        <g transform="translate(966 1546)">
          <path d="M -16 46 L -12 8 L 12 8 L 16 46 Z" fill="#4a3a34" stroke={MAT.ink} strokeWidth={3} />
          <ellipse cx={0} cy={8} rx={13} ry={4} fill="#2a1f1c" />
          <path d="M -13 8 q 13 -22 26 0" stroke="#3a2a22" strokeWidth={3} fill="none" />
        </g>

        {/* THE BELL */}
        <ParallaxGroup depth={0.36} progress={progress}>
          <BellPost frame={frame} prefix="town" />
        </ParallaxGroup>

        {/* footprints leading in */}
        <g opacity={0.3} fill="#8f9dc4">
          {[0, 1, 2, 3, 4, 5, 6, 7].map((i) => (
            <ellipse key={i} cx={250 + i * 34} cy={1650 + i * 22} rx={10} ry={5} transform={`rotate(${-14 + i} ${250 + i * 34} ${1650 + i * 22})`} />
          ))}
        </g>

        {/* FOREGROUND: snowbank + blurred branch (occluder that creates depth) */}
        <path d="M -20 1806 Q 240 1738 520 1802 Q 800 1866 1100 1786 L 1100 1920 L -20 1920 Z" fill="#e8eefb" />
        <path d="M -20 1806 Q 240 1738 520 1802 Q 800 1866 1100 1786" stroke="#ffffff" strokeWidth={7} fill="none" opacity={0.6} />
        <rect y={1806} width={1080} height={120} fill="url(#town-snow)" opacity={0.5} />
        <g filter="url(#town-blur)" opacity={0.55}>
          <path d="M -40 120 q 120 40 180 120 q 60 80 40 190" stroke="#101733" strokeWidth={26} fill="none" strokeLinecap="round" />
          <path d="M 60 190 q 70 6 120 44" stroke="#101733" strokeWidth={16} fill="none" strokeLinecap="round" />
        </g>

        {/* CONTRAST PASS: the square's mid-tones sink, the moon and the lantern
            keep their pools. The set only: actors are drawn on their own layer. */}
        <LightVeil id="town-veil" lights={[[790, 250, 330], [600, 1075, 190]]} opacity={0.34} />

        <FogBand id="town-fog" y={1480} height={300} color="#9fb0d8" opacity={0.22} />
      </svg>

      <Particles count={110} seed="townSnow2" size={[2, 7]} speed={[0.5, 1.7]} opacity={0.85} />
      <Particles count={20} seed="townBokeh" size={[14, 22]} speed={[0.2, 0.5]} opacity={0.1} />
    </>
  );
};
