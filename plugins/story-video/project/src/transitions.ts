import {
  linearTiming,
  springTiming,
  type TransitionPresentation,
  type TransitionTiming,
} from "@remotion/transitions";
import { fade } from "@remotion/transitions/fade";
import { slide } from "@remotion/transitions/slide";
import { wipe } from "@remotion/transitions/wipe";
import { flip } from "@remotion/transitions/flip";
import { clockWipe } from "@remotion/transitions/clock-wipe";
import type { BeatType } from "./types";

interface Dims {
  width: number;
  height: number;
}

/**
 * Pick a transition *presentation* for entering a beat of `toType`. Keyed by the
 * destination beat so each kind of moment arrives in a characteristic way, with
 * an index-based fallback that guarantees variety on repeated types.
 */
function presentationFor(
  toType: BeatType,
  index: number,
  { width, height }: Dims
): TransitionPresentation<Record<string, unknown>> {
  const byType: Partial<Record<BeatType, () => TransitionPresentation<any>>> = {
    hook: () => fade(),
    problem: () => slide({ direction: "from-right" }),
    stat: () => clockWipe({ width, height }),
    insight: () => wipe({ direction: "from-bottom-right" }),
    solution: () => slide({ direction: "from-bottom" }),
    cta: () => flip({ direction: "from-left" }),
    logo: () => fade(),
  };

  const fallbacks: Array<() => TransitionPresentation<any>> = [
    () => fade(),
    () => slide({ direction: "from-right" }),
    () => wipe({ direction: "from-left" }),
    () => flip({ direction: "from-bottom" }),
    () => clockWipe({ width, height }),
  ];

  const make = byType[toType] ?? fallbacks[index % fallbacks.length];
  return make();
}

/** Alternate spring/linear timing so the cadence of cuts stays varied. */
function timingFor(index: number, durationInFrames: number): TransitionTiming {
  return index % 2 === 0
    ? springTiming({ config: { damping: 200 }, durationInFrames })
    : linearTiming({ durationInFrames });
}

export function getTransition(
  toType: BeatType,
  index: number,
  durationInFrames: number,
  dims: Dims
): { presentation: TransitionPresentation<Record<string, unknown>>; timing: TransitionTiming } {
  return {
    presentation: presentationFor(toType, index, dims),
    timing: timingFor(index, durationInFrames),
  };
}
