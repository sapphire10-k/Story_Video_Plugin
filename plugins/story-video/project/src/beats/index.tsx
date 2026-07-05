import React from "react";
import type { Beat, BeatType } from "../types";
import { BEAT_ACCENTS } from "../theme";
import { HookBeat } from "./HookBeat";
import { ProblemBeat } from "./ProblemBeat";
import { StatBeat } from "./StatBeat";
import { InsightBeat } from "./InsightBeat";
import { SolutionBeat } from "./SolutionBeat";
import { CtaBeat } from "./CtaBeat";
import { LogoBeat } from "./LogoBeat";

const REGISTRY: Record<
  BeatType,
  React.FC<{ beat: Beat; accent: string }>
> = {
  hook: HookBeat,
  problem: ProblemBeat,
  stat: StatBeat,
  insight: InsightBeat,
  solution: SolutionBeat,
  cta: CtaBeat,
  logo: LogoBeat,
};

/** Render a single beat by dispatching on its type. */
export const BeatRenderer: React.FC<{ beat: Beat }> = ({ beat }) => {
  const Component = REGISTRY[beat.type];
  const accent = beat.accent ?? BEAT_ACCENTS[beat.type];
  return <Component beat={beat} accent={accent} />;
};
