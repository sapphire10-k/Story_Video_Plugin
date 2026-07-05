import React from "react";
import { Composition } from "remotion";
import { StoryVideo, calculateStoryMetadata } from "./StoryVideo";
import { sampleBeats } from "./sampleBeats";
import { FPS, HEIGHT, WIDTH } from "./theme";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="StoryVideo"
        component={StoryVideo}
        // Placeholder — the real duration is set by calculateMetadata. It must
        // be a positive integer here to satisfy the Studio before metadata runs.
        durationInFrames={600}
        fps={FPS}
        width={WIDTH}
        height={HEIGHT}
        calculateMetadata={calculateStoryMetadata}
        defaultProps={{
          beats: sampleBeats,
          // To test voiceover redistribution, drop an audio file in public/ and set:
          // voiceover: { src: staticFile("voiceover.mp3"), volume: 1 },
        }}
      />
    </>
  );
};
