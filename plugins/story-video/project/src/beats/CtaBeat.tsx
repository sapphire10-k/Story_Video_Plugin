import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import type { Beat } from "../types";
import { COLORS, FONT_FAMILY } from "../theme";
import { Backdrop, RevealText } from "../components/primitives";

/** CTA: centered ask with a gently pulsing action button. */
export const CtaBeat: React.FC<{ beat: Beat; accent: string }> = ({ beat, accent }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const btn = spring({ frame: frame - 20, fps, config: { damping: 12, stiffness: 100 } });
  // Continuous subtle pulse driven by interpolate over a looped phase.
  const pulse = 1 + 0.03 * Math.sin((frame / fps) * Math.PI * 2 * 0.9);

  return (
    <AbsoluteFill>
      <Backdrop accent={accent} />
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", padding: 110 }}>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 54 }}>
          <RevealText
            text={beat.title ?? ""}
            size={84}
            align="center"
            weight={900}
            delay={2}
            stagger={3}
          />
          {beat.subtitle ? (
            <div
              style={{
                fontFamily: FONT_FAMILY,
                fontSize: 38,
                color: COLORS.muted,
                textAlign: "center",
                maxWidth: 720,
                lineHeight: 1.35,
                opacity: interpolate(frame, [14, 28], [0, 1], { extrapolateRight: "clamp" }),
              }}
            >
              {beat.subtitle}
            </div>
          ) : null}
          {beat.cta ? (
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 20,
                padding: "34px 66px",
                borderRadius: 999,
                backgroundColor: accent,
                boxShadow: `0 24px 70px ${accent}55`,
                opacity: btn,
                transform: `scale(${interpolate(btn, [0, 1], [0.6, 1]) * pulse})`,
              }}
            >
              <span
                style={{
                  fontFamily: FONT_FAMILY,
                  fontSize: 46,
                  fontWeight: 800,
                  color: COLORS.bg,
                  letterSpacing: 0.5,
                }}
              >
                {beat.cta}
              </span>
              <svg width={40} height={40} viewBox="0 0 24 24" fill="none">
                <path
                  d="M5 12h14M13 6l6 6-6 6"
                  stroke={COLORS.bg}
                  strokeWidth={3}
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </div>
          ) : null}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
