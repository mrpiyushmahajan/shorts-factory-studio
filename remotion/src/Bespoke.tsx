import React from 'react';
import {
  useCurrentFrame,
  useVideoConfig,
  Sequence,
  interpolate,
  spring,
  Easing,
} from 'remotion';

type Segment = {displayText: string; durationS: number; imagePath: string | null};

const CX = 540;
const CY = 780; // middle band center

const glow = (c: string, s = 24) => `drop-shadow(0 0 ${s}px ${c})`;

// ---- reusable particle burst ----
const Burst: React.FC<{frame: number; at: number; accent: string; n?: number; r?: number}> = ({
  frame,
  at,
  accent,
  n = 16,
  r = 300,
}) => {
  const t = frame - at;
  if (t < 0 || t > 40) return null;
  const p = interpolate(t, [0, 40], [0, 1], {extrapolateRight: 'clamp'});
  return (
    <g opacity={1 - p}>
      {Array.from({length: n}).map((_, i) => {
        const a = (i / n) * Math.PI * 2;
        const d = r * Easing.out(Easing.cubic)(p);
        return (
          <circle
            key={i}
            cx={CX + Math.cos(a) * d}
            cy={CY + Math.sin(a) * d}
            r={9 * (1 - p) + 3}
            fill={accent}
            style={{filter: glow(accent, 14)}}
          />
        );
      })}
    </g>
  );
};

// ---- an isometric cube (the poop) ----
const Cube: React.FC<{cx: number; cy: number; s: number; accent: string; op?: number}> = ({
  cx,
  cy,
  s,
  accent,
  op = 1,
}) => {
  const top = `${cx},${cy - s} ${cx + s},${cy - s / 2} ${cx},${cy} ${cx - s},${cy - s / 2}`;
  const left = `${cx - s},${cy - s / 2} ${cx},${cy} ${cx},${cy + s} ${cx - s},${cy + s / 2}`;
  const right = `${cx + s},${cy - s / 2} ${cx},${cy} ${cx},${cy + s} ${cx + s},${cy + s / 2}`;
  return (
    <g opacity={op} style={{filter: glow(accent, 18)}}>
      <polygon points={top} fill={accent} opacity={0.95} />
      <polygon points={left} fill={accent} opacity={0.55} />
      <polygon points={right} fill={accent} opacity={0.35} />
    </g>
  );
};

const Frame: React.FC<{children: React.ReactNode}> = ({children}) => (
  <svg
    width={1080}
    height={1920}
    viewBox="0 0 1080 1920"
    style={{position: 'absolute', inset: 0}}
  >
    {children}
  </svg>
);

const BespokeOverlay: React.FC<{
  segments: Segment[];
  skin: {bg: string; accent: string};
}> = ({segments, skin}) => {
  const {fps} = useVideoConfig();
  const accent = skin.accent;
  const starts: number[] = [];
  let acc = 0;
  for (const s of segments) {
    starts.push(Math.round(acc * fps));
    acc += s.durationS;
  }
  const durs = segments.map((s) => Math.round(s.durationS * fps));

  return (
    <>
      {/* SEG 0 — the question: pulsing "?" over three tumbling mystery cubes */}
      <Sequence from={starts[0]} durationInFrames={durs[0]}>
        <Seg0 accent={accent} />
      </Sequence>

      {/* SEG 1 — REVEAL: huge counter to 100 dice + burst */}
      <Sequence from={starts[1]} durationInFrames={durs[1]}>
        <Seg1 accent={accent} />
      </Sequence>

      {/* SEG 2 — intestine squeezes round -> cube */}
      <Sequence from={starts[2]} durationInFrames={durs[2]}>
        <Seg2 accent={accent} />
      </Sequence>

      {/* SEG 3 — stacking wall of cubes with turf arrow */}
      <Sequence from={starts[3]} durationInFrames={durs[3]}>
        <Seg3 accent={accent} />
      </Sequence>

      {/* SEG 4 — would you build a wall? slamming brick + ? */}
      <Sequence from={starts[4]} durationInFrames={durs[4]}>
        <Seg4 accent={accent} />
      </Sequence>
    </>
  );
};

const Seg0: React.FC<{accent: string}> = ({accent}) => {
  const f = useCurrentFrame();
  const pulse = 1 + 0.12 * Math.sin(f / 5);
  return (
    <Frame>
      {[0, 1, 2].map((i) => {
        const a = f / 18 + (i * Math.PI * 2) / 3;
        return (
          <g key={i} opacity={0.5}>
            <Cube cx={CX + Math.cos(a) * 200} cy={CY + Math.sin(a) * 120} s={38} accent={accent} />
          </g>
        );
      })}
      <text
        x={CX}
        y={CY + 70}
        textAnchor="middle"
        fontSize={260}
        fontWeight={900}
        fontFamily="Arial Black, sans-serif"
        fill={accent}
        opacity={0.9}
        style={{filter: glow(accent, 30)}}
        transform={`translate(${CX} ${CY}) scale(${pulse}) translate(${-CX} ${-CY})`}
      >
        ?
      </text>
    </Frame>
  );
};

const Seg1: React.FC<{accent: string}> = ({accent}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const land = Math.round(1.4 * fps);
  const count = Math.round(interpolate(f, [0, land], [0, 100], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}));
  const sp = spring({frame: f - land, fps, config: {damping: 8, stiffness: 120}});
  const sc = f < land ? 1 : 1 + 0.3 * (1 - Math.min(1, sp));
  return (
    <Frame>
      <circle cx={CX} cy={CY} r={330} fill="none" stroke={accent} strokeWidth={4} opacity={0.25} />
      <Burst frame={f} at={land} accent={accent} r={360} />
      <text
        x={CX}
        y={CY + 90}
        textAnchor="middle"
        fontSize={300}
        fontWeight={900}
        fontFamily="Arial Black, sans-serif"
        fill={accent}
        style={{filter: glow(accent, f >= land ? 40 : 16)}}
        transform={`translate(${CX} ${CY}) scale(${sc}) translate(${-CX} ${-CY})`}
      >
        {count}
      </text>
      <text x={CX} y={CY + 210} textAnchor="middle" fontSize={70} fontWeight={800} fontFamily="Arial, sans-serif" fill={accent} opacity={0.85}>
        CUBES / DAY
      </text>
    </Frame>
  );
};

const Seg2: React.FC<{accent: string}> = ({accent}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  // morph round -> cube via corner radius
  const p = interpolate(f, [0, 1.6 * fps], [1, 0], {extrapolateRight: 'clamp'});
  const squeeze = 1 - 0.15 * Math.sin(f / 4);
  const rad = 130 * p + 8;
  return (
    <Frame>
      {/* intestine tube */}
      <path
        d={`M 120 ${CY} Q ${CX} ${CY - 160 * squeeze}, 960 ${CY}`}
        fill="none"
        stroke={accent}
        strokeWidth={26}
        opacity={0.35}
        strokeLinecap="round"
        style={{filter: glow(accent, 12)}}
      />
      <g transform={`translate(${CX} ${CY}) scale(${squeeze} ${2 - squeeze})`}>
        <rect x={-140} y={-140} width={280} height={280} rx={rad} ry={rad} fill={accent} opacity={0.9} style={{filter: glow(accent, 26)}} />
      </g>
      {/* squeeze arrows */}
      {[-1, 1].map((d) => (
        <polygon
          key={d}
          points={`${CX + d * 250},${CY - 40} ${CX + d * 180},${CY} ${CX + d * 250},${CY + 40}`}
          fill={accent}
          opacity={0.7 + 0.3 * Math.abs(Math.sin(f / 4))}
        />
      ))}
    </Frame>
  );
};

const Seg3: React.FC<{accent: string}> = ({accent}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const cubes = [
    [CX - 90, CY + 120],
    [CX + 90, CY + 120],
    [CX, CY + 10],
    [CX - 90, CY - 100],
    [CX + 90, CY - 100],
  ];
  return (
    <Frame>
      {cubes.map(([x, y], i) => {
        const t = spring({frame: f - i * 6, fps, config: {damping: 10, stiffness: 90}});
        const dy = (1 - t) * -400;
        return (
          <g key={i} transform={`translate(0 ${dy})`} opacity={t}>
            <Cube cx={x} cy={y} s={78} accent={accent} />
          </g>
        );
      })}
      {/* self-drawing turf arrow */}
      {(() => {
        const dr = interpolate(f, [fps * 1.2, fps * 2.2], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
        const len = 260;
        return (
          <g opacity={0.9} style={{filter: glow(accent, 14)}}>
            <line x1={CX + 200} y1={CY + 220} x2={CX + 200} y2={CY + 220 - len * dr} stroke={accent} strokeWidth={12} strokeLinecap="round" />
            {dr > 0.9 && (
              <polygon points={`${CX + 200},${CY - 60} ${CX + 170},${CY - 10} ${CX + 230},${CY - 10}`} fill={accent} />
            )}
          </g>
        );
      })()}
    </Frame>
  );
};

const Seg4: React.FC<{accent: string}> = ({accent}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = spring({frame: f, fps, config: {damping: 7, stiffness: 140}});
  const sc = 0.3 + 0.7 * t;
  const wobble = 1 + 0.06 * Math.sin(f / 3);
  return (
    <Frame>
      <g transform={`translate(${CX} ${CY}) scale(${sc * wobble}) translate(${-CX} ${-CY})`} opacity={t}>
        {[0, 1].map((r) =>
          [0, 1, 2].map((c) => (
            <Cube key={`${r}-${c}`} cx={CX - 130 + c * 130} cy={CY - 60 + r * 120} s={62} accent={accent} />
          ))
        )}
      </g>
      <text
        x={CX}
        y={CY + 300}
        textAnchor="middle"
        fontSize={150}
        fontWeight={900}
        fontFamily="Arial Black, sans-serif"
        fill={accent}
        opacity={0.9 * t}
        style={{filter: glow(accent, 28)}}
      >
        WALL?
      </text>
    </Frame>
  );
};

export default BespokeOverlay;
