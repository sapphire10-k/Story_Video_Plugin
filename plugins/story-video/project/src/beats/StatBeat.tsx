import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import type { Beat } from "../types";
import { COLORS, FONT_FAMILY } from "../theme";
import { Backdrop, NumberTicker, ProgressRing } from "../components/primitives";

/** Stat: a huge counting-up figure inside an animated progress ring. */
export const StatBeat: React.FC<{ beat: Beat; accent: string }> = ({ beat, accent }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const labelIn = spring({ frame: frame - 30, fps, config: { damping: 200 } });

  return (
    <AbsoluteFill>
      <Backdrop accent={accent} />
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", padding: 90 }}>
        <div style={{ position: "relative", display: "flex", justifyContent: "center", alignItems: "center" }}>
          <ProgressRing size={720} stroke={14} accent={accent} />
          <div
            style={{
              position: "absolute",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: 10,
            }}
          >
            <div style={{ display: "flex", alignItems: "flex-start" }}>
              <NumberTicker value={beat.value ?? "0"} size={260} color={COLORS.white} />
              {beat.unit ? (
                <span
                  style={{
                    fontFamily: FONT_FAMILY,
                    fontSize: 96,
                    fontWeight: 800,
                    color: accent,
                    marginTop: 40,
                  }}
                >
                  {beat.unit}
                </span>
              ) : null}
            </div>
            {beat.label ? (
              <div
                style={{
                  fontFamily: FONT_FAMILY,
                  fontSize: 38,
                  fontWeight: 600,
                  color: COLORS.muted,
                  textAlign: "center",
                  maxWidth: 560,
                  lineHeight: 1.3,
                  opacity: labelIn,
                  transform: `translateY(${interpolate(labelIn, [0, 1], [16, 0])}px)`,
                }}
              >
                {beat.label}
              </div>
            ) : null}
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
