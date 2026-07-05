import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import type { Beat } from "../types";
import { COLORS, FONT_FAMILY } from "../theme";
import { Backdrop, Eyebrow, RevealText } from "../components/primitives";

/** Hook: dramatic centered headline that scales in from the depths. */
export const HookBeat: React.FC<{ beat: Beat; accent: string }> = ({ beat, accent }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const pop = spring({ frame, fps, config: { damping: 12, mass: 0.8, stiffness: 90 } });
  const scale = interpolate(pop, [0, 1], [0.7, 1]);

  return (
    <AbsoluteFill>
      <Backdrop accent={accent} />
      <AbsoluteFill
        style={{
          justifyContent: "center",
          alignItems: "center",
          padding: 110,
          transform: `scale(${scale})`,
        }}
      >
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 46 }}>
          {beat.eyebrow ? <Eyebrow accent={accent}>{beat.eyebrow}</Eyebrow> : null}
          <RevealText
            text={beat.title ?? ""}
            size={104}
            align="center"
            weight={900}
            delay={4}
            stagger={4}
          />
          {beat.subtitle ? (
            <div
              style={{
                fontFamily: FONT_FAMILY,
                fontSize: 40,
                color: COLORS.muted,
                textAlign: "center",
                maxWidth: 760,
                lineHeight: 1.3,
                opacity: interpolate(frame, [16, 30], [0, 1], { extrapolateRight: "clamp" }),
              }}
            >
              {beat.subtitle}
            </div>
          ) : null}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
