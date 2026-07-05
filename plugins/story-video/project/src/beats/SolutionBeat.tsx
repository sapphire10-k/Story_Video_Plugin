import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import type { Beat } from "../types";
import { COLORS, FONT_FAMILY } from "../theme";
import { Backdrop, Eyebrow, RevealText } from "../components/primitives";

/** Solution: a checklist whose rows spring in one after another. */
export const SolutionBeat: React.FC<{ beat: Beat; accent: string }> = ({ beat, accent }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const bullets = beat.bullets ?? [];

  return (
    <AbsoluteFill>
      <Backdrop accent={accent} align="top" />
      <AbsoluteFill style={{ justifyContent: "center", padding: "0 110px" }}>
        <div style={{ display: "flex", flexDirection: "column", gap: 48 }}>
          <Eyebrow accent={accent}>{beat.eyebrow ?? "The Solution"}</Eyebrow>
          {beat.title ? <RevealText text={beat.title} size={72} weight={800} delay={2} /> : null}
          <div style={{ display: "flex", flexDirection: "column", gap: 26, marginTop: 8 }}>
            {bullets.map((b, i) => {
              const s = spring({
                frame: frame - 22 - i * 8,
                fps,
                config: { damping: 16, stiffness: 110 },
              });
              return (
                <div
                  key={`${b}-${i}`}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 26,
                    opacity: s,
                    transform: `translateX(${interpolate(s, [0, 1], [-40, 0])}px)`,
                  }}
                >
                  <div
                    style={{
                      width: 56,
                      height: 56,
                      borderRadius: 16,
                      backgroundColor: accent,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      flexShrink: 0,
                      transform: `scale(${interpolate(s, [0, 1], [0.4, 1])})`,
                    }}
                  >
                    <svg width={30} height={30} viewBox="0 0 24 24" fill="none">
                      <path
                        d="M5 13l4 4L19 7"
                        stroke={COLORS.bg}
                        strokeWidth={3.5}
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeDasharray={30}
                        strokeDashoffset={interpolate(s, [0, 1], [30, 0])}
                      />
                    </svg>
                  </div>
                  <span
                    style={{
                      fontFamily: FONT_FAMILY,
                      fontSize: 46,
                      fontWeight: 600,
                      color: COLORS.white,
                    }}
                  >
                    {b}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
