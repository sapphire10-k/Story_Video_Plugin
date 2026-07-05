import type { BeatType } from "./types";

/**
 * Brand palette. The three required brand colors plus a small set of
 * supporting tones derived to keep everything cohesive on the dark bg.
 */
export const COLORS = {
  navy: "#003087",
  blue: "#00A3E0",
  bg: "#0A0F1E",
  bgElevated: "#111834",
  white: "#EAF2FF",
  muted: "#8FA3C8",
  line: "rgba(143, 163, 200, 0.18)",
} as const;

/**
 * Each beat type gets its own accent so layouts read as distinct moments
 * while staying anchored to the navy/blue brand.
 */
export const BEAT_ACCENTS: Record<BeatType, string> = {
  hook: "#00A3E0",
  problem: "#FF5C7A",
  stat: "#00E0B8",
  insight: "#FFB84D",
  solution: "#00A3E0",
  cta: "#4D7CFF",
  logo: "#00A3E0",
};

export const FONT_FAMILY =
  "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif";

export const FPS = 30;
export const WIDTH = 1080;
export const HEIGHT = 1080;

/** Default overlap (in frames) for every @remotion/transitions transition. */
export const DEFAULT_TRANSITION_FRAMES = 16;
