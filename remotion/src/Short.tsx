import React from 'react';
import {
  AbsoluteFill, Audio, Img, Video, Sequence,
  interpolate, spring, staticFile,
  useCurrentFrame, useVideoConfig,
} from 'remotion';
import BespokeOverlay from './Bespoke';

const resolveSrc = (p: string) =>
  p.startsWith('http') || p.startsWith('/') ? p : staticFile(p);

export type Word = {text: string; start: number; end: number};

export type Segment = {
  displayText: string;
  durationS: number;
  imagePath: string | null;
  imagePaths?: string[];
  videoPaths?: string[];    // real AnimateDiff video clips
};

export type ShortProps = {
  segments: Segment[];
  audioPath: string | null;
  skin: {bg: string; accent: string};
  badge: string;
  words: Word[];
  followCta?: string;
};

export const defaultProps: ShortProps = {
  segments: [
    {displayText: 'Sample fact', durationS: 4, imagePath: null},
    {displayText: 'Mind blown', durationS: 4, imagePath: null},
  ],
  audioPath: null,
  skin: {bg: '#0b1220', accent: '#FFD23F'},
  badge: 'DID YOU KNOW?',
  words: [],
  followCta: 'FOLLOW FOR DAILY FACTS',
};

// ── Karaoke captions ─────────────────────────────────────────────────────────
const KaraokeCaptions: React.FC<{words: Word[]; accent: string}> = ({words, accent}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  if (!words.length) return null;

  const pages: {words: Word[]; startF: number; endF: number}[] = [];
  for (let i = 0; i < words.length; i += 3) {
    const chunk = words.slice(i, i + 3);
    pages.push({
      words: chunk,
      startF: chunk[0].start * fps,
      endF: (words[i + 3]?.start ?? chunk[chunk.length - 1].end + 0.4) * fps,
    });
  }

  let page = null as (typeof pages)[0] | null;
  for (let i = pages.length - 1; i >= 0; i--) {
    if (frame >= pages[i].startF) { page = pages[i]; break; }
  }
  if (!page || frame > page.endF + fps * 0.5) return null;

  const pop = spring({frame: frame - page.startF, fps, config: {damping: 12, stiffness: 200}});

  return (
    <div style={{
      position: 'absolute', bottom: 200, left: 0, right: 0,
      display: 'flex', justifyContent: 'center', gap: 22,
      transform: `scale(${0.9 + 0.1 * pop})`, zIndex: 20,
    }}>
      {page.words.map((w, wi) => {
        const active = frame >= w.start * fps && frame < w.end * fps + 3;
        return (
          <span key={wi} style={{
            fontFamily: 'Arial Black, sans-serif', fontSize: 72, fontWeight: 900,
            textTransform: 'uppercase',
            color: active ? accent : '#fff',
            textShadow: '0 4px 20px rgba(0,0,0,0.95), 0 2px 4px rgba(0,0,0,0.9)',
            WebkitTextStroke: '2px rgba(0,0,0,0.65)',
            transform: active ? 'scale(1.12)' : 'scale(1)',
            display: 'inline-block', margin: '0 12px',
          }}>
            {w.text}
          </span>
        );
      })}
    </div>
  );
};

// ── Shot: AnimateDiff video clip OR still + Ken Burns ────────────────────────
const ShotView: React.FC<{
  src: string;
  isVideo: boolean;
  styleIdx: number;
  shotFrames: number;
}> = ({src, isVideo, styleIdx, shotFrames}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / Math.max(shotFrames, 1);
  const punch = spring({frame, fps, config: {damping: 16, stiffness: 180}});
  const flash = interpolate(frame, [0, 3], [0.55, 0], {extrapolateRight: 'clamp'});

  let scale = 1.1, x = 0, y = 0, rot = 0;
  if (styleIdx === 0) {
    scale = interpolate(t, [0, 1], [1.35, 1.12]) * (0.96 + 0.04 * punch);
    rot = interpolate(t, [0, 1], [-1.5, 0]);
  } else if (styleIdx === 1) {
    scale = interpolate(t, [0, 1], [1.12, 1.3]);
    x = interpolate(t, [0, 1], [40, -40]);
  } else if (styleIdx === 2) {
    scale = interpolate(t, [0, 1], [1.25, 1.1]);
    y = interpolate(t, [0, 1], [-50, 40]);
  } else {
    scale = interpolate(t, [0, 1], [1.32, 1.15]);
    x = interpolate(t, [0, 1], [-35, 30]);
    y = interpolate(t, [0, 1], [30, -25]);
  }

  return (
    <AbsoluteFill style={{overflow: 'hidden'}}>
      {isVideo ? (
        <Video
          src={resolveSrc(src)}
          style={{width: '100%', height: '100%', objectFit: 'cover'}}
          playbackRate={1.0}
          muted
        />
      ) : (
        <Img
          src={resolveSrc(src)}
          style={{
            width: '100%', height: '100%', objectFit: 'cover',
            transform: `scale(${scale}) translate(${x}px, ${y}px) rotate(${rot}deg)`,
          }}
        />
      )}
      <AbsoluteFill style={{backgroundColor: 'white', opacity: flash}} />
    </AbsoluteFill>
  );
};

// ── One segment ──────────────────────────────────────────────────────────────
const SegmentScene: React.FC<{
  seg: Segment;
  skin: ShortProps['skin'];
  badge: string;
  isFirst: boolean;
  isLast: boolean;
  index: number;
  followCta: string;
}> = ({seg, skin, badge, isFirst, isLast, index, followCta}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const segFrames = Math.round(seg.durationS * fps);
  const appear = spring({frame, fps, config: {damping: 14, stiffness: 120}});

  const videoPaths = seg.videoPaths && seg.videoPaths.length > 0 ? seg.videoPaths : [];
  const imagePaths = seg.imagePaths && seg.imagePaths.length > 0
    ? seg.imagePaths
    : (seg.imagePath ? [seg.imagePath] : []);
  const shots = videoPaths.length > 0 ? videoPaths : imagePaths;
  const isVideoShots = videoPaths.length > 0;
  const shotFrames = shots.length ? Math.ceil(segFrames / shots.length) : segFrames;

  return (
    <AbsoluteFill style={{backgroundColor: skin.bg}}>
      {shots.length ? (
        shots.map((shot, si) => (
          <Sequence key={si} from={si * shotFrames} durationInFrames={shotFrames}>
            <ShotView src={shot} isVideo={isVideoShots}
              styleIdx={(index + si) % 4} shotFrames={shotFrames} />
          </Sequence>
        ))
      ) : (
        <AbsoluteFill style={{
          background: `radial-gradient(circle at 50% 35%, ${skin.bg} 0%, #000 100%)`,
        }} />
      )}

      <AbsoluteFill style={{
        background: 'linear-gradient(180deg,rgba(0,0,0,0.35) 0%,rgba(0,0,0,0) 30%,rgba(0,0,0,0) 55%,rgba(0,0,0,0.75) 100%)',
      }} />
      <AbsoluteFill style={{
        background: 'radial-gradient(ellipse at center,rgba(0,0,0,0) 55%,rgba(0,0,0,0.45) 100%)',
      }} />

      {isFirst && (
        <div style={{position:'absolute',top:300,width:'100%',display:'flex',justifyContent:'center',padding:'0 50px'}}>
          <div style={{
            fontFamily:'Arial Black,sans-serif',
            fontSize: seg.displayText.length > 30 ? 68 : 84,
            fontWeight:900, color:'#fff', textAlign:'center',
            textTransform:'uppercase', lineHeight:1.12,
            textShadow:'0 4px 24px rgba(0,0,0,0.95)',
            WebkitTextStroke:'2.5px rgba(0,0,0,0.7)',
          }}>
            {seg.displayText}
          </div>
        </div>
      )}

      {isFirst && (
        <div style={{position:'absolute',top:110,width:'100%',display:'flex',justifyContent:'center',opacity:appear}}>
          <div style={{
            backgroundColor:skin.accent, color:'#000',
            fontFamily:'Arial Black,sans-serif', fontSize:42, fontWeight:900,
            padding:'14px 36px', borderRadius:40, letterSpacing:2,
          }}>
            {badge}
          </div>
        </div>
      )}

      {isLast && frame > segFrames * 0.5 && (
        <div style={{
          position:'absolute', bottom:90, width:'100%',
          display:'flex', justifyContent:'center',
          opacity: interpolate(frame,[segFrames*0.5,segFrames*0.65],[0,1],{extrapolateRight:'clamp'}),
          transform:`scale(${1+0.04*Math.sin((frame/fps)*Math.PI*3)})`,
        }}>
          <div style={{
            backgroundColor:skin.accent, color:'#000',
            fontFamily:'Arial Black,sans-serif', fontSize:44, fontWeight:900,
            padding:'16px 40px', borderRadius:50,
          }}>
            ↑ {followCta}
          </div>
        </div>
      )}
    </AbsoluteFill>
  );
};

const ProgressBar: React.FC<{accent: string}> = ({accent}) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  return (
    <div style={{
      position:'absolute', bottom:0, left:0, height:12,
      width:`${(frame/durationInFrames)*100}%`,
      backgroundColor:accent, zIndex:30,
    }} />
  );
};

export const Short: React.FC<ShortProps> = ({segments, audioPath, skin, badge, words, followCta='FOLLOW'}) => {
  const {fps} = useVideoConfig();
  let from = 0;
  return (
    <AbsoluteFill style={{backgroundColor: skin.bg}}>
      {segments.map((seg, i) => {
        const segFrames = Math.round(Math.max(seg.durationS, 1) * fps);
        const el = (
          <Sequence key={i} from={from} durationInFrames={segFrames}>
            <SegmentScene seg={seg} skin={skin} badge={badge}
              isFirst={i===0} isLast={i===segments.length-1}
              index={i} followCta={followCta} />
          </Sequence>
        );
        from += segFrames;
        return el;
      })}
      <BespokeOverlay segments={segments} skin={skin} />
      <KaraokeCaptions words={words ?? []} accent={skin.accent} />
      <ProgressBar accent={skin.accent} />
      {audioPath ? <Audio src={resolveSrc(audioPath)} /> : null}
    </AbsoluteFill>
  );
};
