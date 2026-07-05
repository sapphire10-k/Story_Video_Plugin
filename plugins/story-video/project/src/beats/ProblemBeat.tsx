import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import type { Beat } from "../types";
import { COLORS, FONT_FAMILY } from "../theme";
import { Backdrop, Eyebrow, RevealText } from "../components/primitives";

/** Problem: left-aligned, tense. A drawn underline strikes through the title. */
export const ProblemBeat: React.FC<{ beat: Beat; accent: string }> = ({ beat, accent }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const underline = spring({ frame: frame - 18, fps, config: { damping: 200 } });
  const bodyIn = spring({ frame: frame - 26, fps, config: { damping: 200 } });

  return (
    <AbsoluteFill>
      <Backdrop accent={accent} align="top" />
      <AbsoluteFill style={{ justifyContent: "center", padding: "0 110px" }}>
        <div style={{ display: "flex", flexDirection: "column", gap: 40, alignItems: "flex-start" }}>
          <Eyebrow accent={accent}>{beat.eyebrow ?? "The Problem"}</Eyebrow>
          <div style={{ position: "relative", paddingBottom: 22 }}>
            <RevealText text={beat.title ?? ""} size={88} weight={800} delay={2} stagger={3} />
            <div
              style={{
                position: "absolute",
                bottom: 0,
                left: 0,
                height: 8,
                borderRadius: 4,
                width: `${interpolate(underline, [0, 1], [0, 100])}%`,
                backgroundColor: accent,
              }}
            />
          </div>
          {beat.body ? (
            <div
              style={{
                fontFamily: FONT_FAMILY,
                fontSize: 40,
                color: COLORS.muted,
                lineHeight: 1.4,
                maxWidth: 820,
                opacity: bodyIn,
                transform: `translateY(${interpolate(bodyIn, [0, 1], [24, 0])}px)`,
              }}
            >
              {beat.body}
            </div>
          ) : null}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
