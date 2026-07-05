import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { COLORS, FONT_FAMILY } from "../theme";

/** Full-frame branded background with a soft radial accent glow. */
export const Backdrop: React.FC<{ accent: string; align?: "top" | "center" }> = ({
  accent,
  align = "center",
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  // Very slow drift so long beats never feel static.
  const drift = interpolate(frame, [0, durationInFrames], [0, 1], {
    extrapolateRight: "clamp",
  });
  const gx = align === "top" ? 30 : 22 + drift * 12;
  const gy = align === "top" ? 18 : 30 + drift * 10;
  return (
    <AbsoluteFill style={{ backgroundColor: COLORS.bg }}>
      <AbsoluteFill
        style={{
          background: `radial-gradient(circle at ${gx}% ${gy}%, ${accent}2E 0%, transparent 45%),
             radial-gradient(circle at ${90 - gx}% ${100 - gy}%, ${COLORS.navy}55 0%, transparent 55%)`,
        }}
      />
    </AbsoluteFill>
  );
};

/** Small uppercase eyebrow label with a leading accent tick. */
export const Eyebrow: React.FC<{
  children: React.ReactNode;
  accent: string;
  delay?: number;
}> = ({ children, accent, delay = 0 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame: frame - delay, fps, config: { damping: 200 } });
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 16,
        opacity: s,
        transform: `translateX(${interpolate(s, [0, 1], [-30, 0])}px)`,
      }}
    >
      <div style={{ width: 44, height: 4, borderRadius: 2, backgroundColor: accent }} />
      <span
        style={{
          fontFamily: FONT_FAMILY,
          color: accent,
          fontSize: 30,
          fontWeight: 700,
          letterSpacing: 6,
          textTransform: "uppercase",
        }}
      >
        {children}
      </span>
    </div>
  );
};

/**
 * Word-by-word rising reveal for headline text. Each word springs up and fades
 * in, staggered, giving titles a lively kinetic-typography feel.
 */
export const RevealText: React.FC<{
  text: string;
  size: number;
  color?: string;
  weight?: number;
  delay?: number;
  stagger?: number;
  lineHeight?: number;
  align?: "left" | "center";
}> = ({
  text,
  size,
  color = COLORS.white,
  weight = 800,
  delay = 0,
  stagger = 3,
  lineHeight = 1.05,
  align = "left",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const words = text.split(" ");
  return (
    <div
      style={{
        display: "flex",
        flexWrap: "wrap",
        gap: `0 ${size * 0.26}px`,
        justifyContent: align === "center" ? "center" : "flex-start",
        textAlign: align,
      }}
    >
      {words.map((w, i) => {
        const s = spring({
          frame: frame - delay - i * stagger,
          fps,
          config: { damping: 200, stiffness: 120 },
        });
        return (
          <span
            key={`${w}-${i}`}
            style={{
              fontFamily: FONT_FAMILY,
              fontSize: size,
              fontWeight: weight,
              color,
              lineHeight,
              letterSpacing: -1,
              display: "inline-block",
              opacity: s,
              transform: `translateY(${interpolate(s, [0, 1], [size * 0.6, 0])}px)`,
            }}
          >
            {w}
          </span>
        );
      })}
    </div>
  );
};

/**
 * Animated number readout. Parses a leading numeric part out of `value`
 * (keeping any prefix like "$" and suffix like "M") and counts up to it.
 */
export const NumberTicker: React.FC<{
  value: string;
  size: number;
  color: string;
  durationFrames?: number;
}> = ({ value, size, color, durationFrames = 40 }) => {
  const frame = useCurrentFrame();
  const match = value.match(/^([^\d-]*)(-?[\d.,]+)(.*)$/);
  const { fps } = useVideoConfig();
  const progress = spring({ frame, fps, config: { damping: 200 }, durationInFrames: durationFrames });

  let display = value;
  if (match) {
    const [, prefix, num, suffix] = match;
    const decimals = num.includes(".") ? num.split(".")[1].length : 0;
    const target = parseFloat(num.replace(/,/g, ""));
    const current = interpolate(progress, [0, 1], [0, target]);
    const grouped = current.toLocaleString("en-US", {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    });
    display = `${prefix}${grouped}${suffix}`;
  }

  return (
    <span
      style={{
        fontFamily: FONT_FAMILY,
        fontSize: size,
        fontWeight: 900,
        color,
        letterSpacing: -4,
        lineHeight: 1,
        fontVariantNumeric: "tabular-nums",
      }}
    >
      {display}
    </span>
  );
};

/** Circular progress ring used by the stat beat. */
export const ProgressRing: React.FC<{
  size: number;
  stroke: number;
  accent: string;
  progressToFrames?: number;
}> = ({ size, stroke, accent, progressToFrames = 45 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = spring({ frame, fps, config: { damping: 200 }, durationInFrames: progressToFrames });
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const dash = interpolate(p, [0, 1], [c, c * 0.12]);
  return (
    <svg width={size} height={size} style={{ transform: "rotate(-90deg)" }}>
      <circle cx={size / 2} cy={size / 2} r={r} stroke={COLORS.line} strokeWidth={stroke} fill="none" />
      <circle
        cx={size / 2}
        cy={size / 2}
        r={r}
        stroke={accent}
        strokeWidth={stroke}
        strokeLinecap="round"
        fill="none"
        strokeDasharray={c}
        strokeDashoffset={dash}
      />
    </svg>
  );
};
