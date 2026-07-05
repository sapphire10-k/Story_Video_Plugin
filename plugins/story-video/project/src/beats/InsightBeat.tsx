import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import type { Beat } from "../types";
import { COLORS, FONT_FAMILY } from "../theme";
import { Backdrop, Eyebrow } from "../components/primitives";

/** Insight: editorial pull-quote with an oversized quotation mark. */
export const InsightBeat: React.FC<{ beat: Beat; accent: string }> = ({ beat, accent }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const bar = spring({ frame, fps, config: { damping: 200 } });
  const quote = spring({ frame: frame - 8, fps, config: { damping: 200 } });
  const attribIn = spring({ frame: frame - 28, fps, config: { damping: 200 } });

  return (
    <AbsoluteFill>
      <Backdrop accent={accent} />
      <AbsoluteFill style={{ justifyContent: "center", padding: "0 120px" }}>
        <div style={{ display: "flex", gap: 44 }}>
          <div
            style={{
              width: 10,
              borderRadius: 5,
              backgroundColor: accent,
              transform: `scaleY(${bar})`,
              transformOrigin: "top",
            }}
          />
          <div style={{ display: "flex", flexDirection: "column", gap: 28 }}>
            {beat.eyebrow ? <Eyebrow accent={accent}>{beat.eyebrow}</Eyebrow> : null}
            <div
              style={{
                fontFamily: FONT_FAMILY,
                fontSize: 220,
                lineHeight: 0.7,
                fontWeight: 900,
                color: accent,
                opacity: interpolate(quote, [0, 1], [0, 0.35]),
                height: 100,
              }}
            >
              &ldquo;
            </div>
            <div
              style={{
                fontFamily: FONT_FAMILY,
                fontSize: 68,
                fontWeight: 700,
                color: COLORS.white,
                lineHeight: 1.22,
                maxWidth: 820,
                opacity: quote,
                transform: `translateY(${interpolate(quote, [0, 1], [30, 0])}px)`,
              }}
            >
              {beat.body ?? beat.title}
            </div>
            {beat.subtitle ? (
              <div
                style={{
                  fontFamily: FONT_FAMILY,
                  fontSize: 34,
                  fontWeight: 600,
                  color: accent,
                  opacity: attribIn,
                }}
              >
                — {beat.subtitle}
              </div>
            ) : null}
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
