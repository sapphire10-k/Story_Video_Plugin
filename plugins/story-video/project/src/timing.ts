import type { Beat } from "./types";

/**
 * Round a list of floats to integers so that the entries selected by
 * `adjustable` sum (together with the fixed entries) to exactly `targetSum`.
 *
 * Fixed entries are rounded independently and never touched again; the rounding
 * remainder is absorbed by the adjustable entries using a largest-remainder
 * distribution, so no frames are lost or invented.
 */
function roundToTarget(
  values: number[],
  adjustable: boolean[],
  targetSum: number
): number[] {
  const floored = values.map((v) => Math.max(1, Math.floor(v)));
  let diff = targetSum - floored.reduce((a, b) => a + b, 0);

  // Indices we're allowed to nudge, ordered by descending fractional part.
  const order = values
    .map((v, i) => ({ i, frac: v - Math.floor(v) }))
    .filter(({ i }) => adjustable[i])
    .sort((a, b) => b.frac - a.frac)
    .map(({ i }) => i);

  if (order.length === 0) return floored;

  // Add frames to the highest-fraction entries first.
  let k = 0;
  while (diff > 0) {
    floored[order[k % order.length]] += 1;
    diff--;
    k++;
  }
  // Remove frames (targetSum smaller than floor sum) without going below 1.
  k = 0;
  let guard = 0;
  while (diff < 0 && guard < order.length * 10000) {
    const idx = order[k % order.length];
    if (floored[idx] > 1) {
      floored[idx] -= 1;
      diff++;
    }
    k++;
    guard++;
  }
  return floored;
}

/**
 * Resolve the concrete per-beat *sequence* durations so they sum to
 * `targetSeqSum` frames.
 *
 * Fixed beats keep their base durations; the remaining ("flex") beats are scaled
 * proportionally to absorb whatever is left. Pass `targetSeqSum = sum(base)` to
 * leave everything untouched (no voiceover), or `audioFrames + totalOverlap` to
 * make the *visible* timeline match an audio track once transition overlaps are
 * subtracted (see {@link compositionDuration}).
 */
/**
 * Structural minimum length for each beat's sequence. A transition overlaps the
 * beat from each adjacent side and two transitions cannot overlap each other, so
 * interior beats need 2x the transition and edge beats 1x. Remotion rejects any
 * sequence shorter than an adjacent transition.
 */
function beatMinimums(n: number, transitionFrames: number): number[] {
  return Array.from({ length: n }, (_, i) => {
    const sides = (i > 0 ? 1 : 0) + (i < n - 1 ? 1 : 0);
    return Math.max(1, sides * transitionFrames);
  });
}

export function resolveDurations(
  beats: Beat[],
  targetSeqSum: number,
  transitionFrames = 0
): number[] {
  const n = beats.length;
  if (n === 0) return [];

  const base = beats.map((b) => Math.max(1, Math.round(b.durationInFrames)));
  const isFlex = beats.map((b) => !b.fixed);
  const minDur = beatMinimums(n, transitionFrames);

  const fixedSum = base.reduce((s, v, i) => (isFlex[i] ? s : s + v), 0);
  const flexBaseSum = base.reduce((s, v, i) => (isFlex[i] ? s + v : s), 0);
  const flexCount = isFlex.filter(Boolean).length;

  let resolved: number[];
  if (flexCount === 0 || flexBaseSum === 0) {
    // Nothing to scale (all beats fixed, or no flex weight): use base durations.
    resolved = base;
  } else {
    // Frames left for the flexible beats after honoring the fixed ones. Guard so
    // each flex beat can still get at least 1 frame even for tiny targets.
    const available = Math.max(flexCount, targetSeqSum - fixedSum);
    const scale = available / flexBaseSum;
    const scaled = base.map((v, i) => (isFlex[i] ? v * scale : v));
    resolved = roundToTarget(scaled, isFlex, fixedSum + available);
  }

  // Enforce the structural minimum. This only binds when the target is very
  // short (e.g. a brief voiceover); otherwise it's a no-op and the exact
  // audio-length match is preserved. When it binds, the visible timeline is the
  // shortest length that still fits every beat + its transitions.
  return resolved.map((v, i) => Math.max(v, minDur[i]));
}

/** Total base sequence length of the beats (their authored durations). */
export function baseSeqSum(beats: Beat[]): number {
  return beats.reduce((s, b) => s + Math.max(1, Math.round(b.durationInFrames)), 0);
}

/** Total frames of transition overlap for `n` beats at `transitionFrames` each. */
export function totalOverlap(n: number, transitionFrames: number): number {
  return Math.max(0, n - 1) * transitionFrames;
}

/** Visible composition length once transition overlaps are subtracted. */
export function compositionDuration(
  resolved: number[],
  transitionFrames: number
): number {
  return Math.max(
    1,
    resolved.reduce((a, b) => a + b, 0) - totalOverlap(resolved.length, transitionFrames)
  );
}
