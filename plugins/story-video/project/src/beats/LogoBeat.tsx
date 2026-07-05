import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import type { Beat } from "../types";
import { COLORS, FONT_FAMILY } from "../theme";
import { Backdrop } from "../components/primitives";

/** Logo: a mark that draws itself in, then the wordmark and tagline settle. */
export const LogoBeat: React.FC<{ beat: Beat; accent: string }> = ({ beat, accent }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const draw = spring({ frame, fps, config: { damping: 200 }, durationInFrames: 40 });
  const mark = spring({ frame: frame - 6, fps, config: { damping: 14, stiffness: 90 } });
  const word = spring({ frame: frame - 22, fps, config: { damping: 200 } });
  const tag = spring({ frame: frame - 32, fps, config: { damping: 200 } });

  const size = 260;
  const r = 110;
  const c = 2 * Math.PI * r;

  return (
    <AbsoluteFill>
      <Backdrop accent={accent} />
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", gap: 50 }}>
        <div
          style={{
            position: "relative",
            width: size,
            height: size,
            transform: `scale(${interpolate(mark, [0, 1], [0.8, 1])})`,
          }}
        >
          <svg width={size} height={size} style={{ transform: "rotate(-90deg)" }}>
            <circle
              cx={size / 2}
              cy={size / 2}
              r={r}
              stroke={accent}
              strokeWidth={12}
              fill="none"
              strokeLinecap="round"
              strokeDasharray={c}
              strokeDashoffset={interpolate(draw, [0, 1], [c, 0])}
            />
          </svg>
          <div
            style={{
              position: "absolute",
              inset: 0,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontFamily: FONT_FAMILY,
              fontSize: 120,
              fontWeight: 900,
              color: COLORS.white,
              opacity: mark,
            }}
          >
            {(beat.brand ?? beat.title ?? "•").trim().charAt(0)}
          </div>
        </div>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 16 }}>
          <div
            style={{
              fontFamily: FONT_FAMILY,
              fontSize: 78,
              fontWeight: 900,
              color: COLORS.white,
              letterSpacing: 2,
              opacity: word,
              transform: `translateY(${interpolate(word, [0, 1], [20, 0])}px)`,
            }}
          >
            {beat.brand ?? beat.title}
          </div>
          {beat.tagline ? (
            <div
              style={{
                fontFamily: FONT_FAMILY,
                fontSize: 34,
                fontWeight: 500,
                color: COLORS.muted,
                letterSpacing: 4,
                textTransform: "uppercase",
                opacity: tag,
              }}
            >
              {beat.tagline}
            </div>
          ) : null}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
