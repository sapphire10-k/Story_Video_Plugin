import type { Beat } from "./types";

/** A complete 7-beat demo story exercising every layout. Durations in frames @30fps. */
export const sampleBeats: Beat[] = [
  {
    type: "hook",
    durationInFrames: 90,
    eyebrow: "For growing teams",
    title: "Your workflow is leaking hours.",
    subtitle: "And you probably can't see where.",
  },
  {
    type: "problem",
    durationInFrames: 105,
    eyebrow: "The Problem",
    title: "Context switching kills momentum",
    body: "The average knowledge worker jumps between 9 apps an hour, losing focus every single time.",
  },
  {
    type: "stat",
    durationInFrames: 90,
    value: "23",
    unit: "min",
    label: "to fully refocus after a single interruption",
  },
  {
    type: "insight",
    durationInFrames: 105,
    eyebrow: "The Insight",
    body: "The problem was never the tools. It was the space between them.",
    subtitle: "Product research, 2026",
  },
  {
    type: "solution",
    durationInFrames: 120,
    eyebrow: "The Solution",
    title: "One surface for everything",
    bullets: [
      "Unified inbox across every app",
      "AI that drafts before you ask",
      "Zero context lost between tasks",
    ],
  },
  {
    type: "cta",
    durationInFrames: 90,
    title: "Get your hours back.",
    subtitle: "Start free — no card required.",
    cta: "Try it now",
  },
  {
    // A fixed logo sting: excluded from voiceover redistribution.
    type: "logo",
    durationInFrames: 75,
    fixed: true,
    brand: "Fordham",
    tagline: "Focus, restored",
  },
];
