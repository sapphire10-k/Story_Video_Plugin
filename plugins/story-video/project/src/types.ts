/** The seven narrative beat types StoryVideo can render. */
export type BeatType =
  | "hook"
  | "problem"
  | "stat"
  | "insight"
  | "solution"
  | "cta"
  | "logo";

/**
 * A single beat in the story. `durationInFrames` is the *base* duration — it is
 * used directly when there is no voiceover, and as the proportional weight when
 * beat durations are redistributed to match an audio track (unless `fixed`).
 */
export type Beat = {
  type: BeatType;

  /** Base / weight duration in frames. Must be >= 1. */
  durationInFrames: number;

  /**
   * When true this beat keeps its exact `durationInFrames` and is excluded from
   * voiceover redistribution. Useful for logo stings or legally-required cards.
   */
  fixed?: boolean;

  /** Optional per-beat accent override (defaults to the beat type's accent). */
  accent?: string;

  // ---- Content fields (all optional; each beat type uses what it needs) ----
  /** Small label above the title (e.g. "THE PROBLEM"). */
  eyebrow?: string;
  title?: string;
  subtitle?: string;
  body?: string;

  /** stat: the headline figure, e.g. "87", "$1.2M", "3.4x". */
  value?: string;
  /** stat: optional trailing unit rendered smaller, e.g. "%". */
  unit?: string;
  /** stat: caption beneath the figure. */
  label?: string;

  /** solution: staggered checklist items. */
  bullets?: string[];

  /** cta: button / action label. */
  cta?: string;

  /** logo: brand wordmark text and tagline. */
  brand?: string;
  tagline?: string;
};

export type Voiceover = {
  /**
   * Audio location. A bare path (e.g. "voiceover.mp3") is resolved with
   * staticFile() against the Remotion public dir; absolute URLs / data URIs are
   * used verbatim.
   */
  src: string;
  /** Linear gain 0..1. */
  volume?: number;
  /** Trim this many seconds off the start of the audio file. */
  startFromSeconds?: number;
  /**
   * Known audio length in seconds. When present it drives beat redistribution
   * directly; otherwise it is measured from the file with @remotion/media-utils.
   */
  durationInSeconds?: number;
};

export type StoryVideoProps = {
  beats: Beat[];
  voiceover?: Voiceover;
  /** Transition overlap in frames. Defaults to DEFAULT_TRANSITION_FRAMES. */
  transitionDurationInFrames?: number;

  /**
   * Injected by calculateStoryMetadata — the per-beat durations after voiceover
   * redistribution. The component recomputes these if absent (e.g. in tests).
   */
  resolvedDurations?: number[];
};
