import React from "react";
import { AbsoluteFill, Audio, staticFile, type CalculateMetadataFunction } from "remotion";
import { TransitionSeries } from "@remotion/transitions";
import { getAudioDurationInSeconds } from "@remotion/media-utils";
import type { StoryVideoProps } from "./types";
import { COLORS, DEFAULT_TRANSITION_FRAMES, FPS, HEIGHT, WIDTH } from "./theme";
import { baseSeqSum, compositionDuration, resolveDurations, totalOverlap } from "./timing";
import { BeatRenderer } from "./beats";
import { getTransition } from "./transitions";

/** Resolve a bare public path via staticFile(); pass URLs/data URIs through. */
const resolveSrc = (src: string): string =>
  /^([a-z]+:)?\/\//i.test(src) || src.startsWith("data:") ? src : staticFile(src);

/**
 * Computes the composition's real duration and, when a voiceover is supplied,
 * redistributes flexible beat durations to fill the audio. The resolved
 * durations are threaded back into props so the component renders deterministically.
 */
export const calculateStoryMetadata: CalculateMetadataFunction<StoryVideoProps> = async ({
  props,
}) => {
  const transitionFrames = props.transitionDurationInFrames ?? DEFAULT_TRANSITION_FRAMES;
  const overlap = totalOverlap(props.beats.length, transitionFrames);

  // Without a voiceover, keep authored durations exactly (sequences = base sum).
  let targetSeqSum = baseSeqSum(props.beats);

  if (props.voiceover?.src) {
    // We want the *visible* timeline (sequences minus overlaps) to equal the
    // audio, so the sequences must sum to audioFrames + overlap. Prefer a
    // caller-supplied duration; fall back to measuring the file.
    const seconds =
      props.voiceover.durationInSeconds ??
      (await getAudioDurationInSeconds(resolveSrc(props.voiceover.src)));
    const audioFrames = Math.max(1, Math.round(seconds * FPS));
    targetSeqSum = audioFrames + overlap;
  }

  const resolvedDurations = resolveDurations(props.beats, targetSeqSum, transitionFrames);
  const durationInFrames = compositionDuration(resolvedDurations, transitionFrames);

  return {
    durationInFrames,
    fps: FPS,
    width: WIDTH,
    height: HEIGHT,
    props: { ...props, resolvedDurations, transitionDurationInFrames: transitionFrames },
  };
};

export const StoryVideo: React.FC<StoryVideoProps> = ({
  beats,
  voiceover,
  transitionDurationInFrames = DEFAULT_TRANSITION_FRAMES,
  resolvedDurations,
}) => {
  // Fall back to computing durations locally (e.g. Studio preview before
  // calculateMetadata has run, or unit tests rendering the component directly).
  const durations =
    resolvedDurations && resolvedDurations.length === beats.length
      ? resolvedDurations
      : resolveDurations(beats, baseSeqSum(beats), transitionDurationInFrames);

  const dims = { width: WIDTH, height: HEIGHT };

  return (
    <AbsoluteFill style={{ backgroundColor: COLORS.bg }}>
      {voiceover?.src ? (
        <Audio
          src={resolveSrc(voiceover.src)}
          volume={voiceover.volume ?? 1}
          startFrom={
            voiceover.startFromSeconds
              ? Math.round(voiceover.startFromSeconds * FPS)
              : undefined
          }
        />
      ) : null}

      <TransitionSeries>
        {beats.flatMap((beat, i) => {
          const seq = (
            <TransitionSeries.Sequence
              key={`beat-${i}`}
              durationInFrames={durations[i]}
            >
              <BeatRenderer beat={beat} />
            </TransitionSeries.Sequence>
          );

          if (i === 0) return [seq];

          const { presentation, timing } = getTransition(
            beat.type,
            i,
            transitionDurationInFrames,
            dims
          );

          return [
            <TransitionSeries.Transition
              key={`trans-${i}`}
              presentation={presentation}
              timing={timing}
            />,
            seq,
          ];
        })}
      </TransitionSeries>
    </AbsoluteFill>
  );
};
