import React from 'react';
import {Composition, getInputProps} from 'remotion';
import {Short, ShortProps, defaultProps} from './Short';

const FPS = 30;

export const RemotionRoot: React.FC = () => {
  const inputProps = getInputProps() as unknown as ShortProps;
  const props = inputProps?.segments?.length ? inputProps : defaultProps;

  const totalSeconds = props.segments.reduce(
    (acc, s) => acc + Math.max(s.durationS, 1),
    0
  );

  return (
    <Composition
      id="Short"
      component={Short}
      durationInFrames={Math.round(totalSeconds * FPS)}
      fps={FPS}
      width={1080}
      height={1920}
      defaultProps={props}
      calculateMetadata={({props}) => {
        const secs = props.segments.reduce(
          (acc: number, s: any) => acc + Math.max(s.durationS, 1),
          0
        );
        return {durationInFrames: Math.round(secs * FPS)};
      }}
    />
  );
};
