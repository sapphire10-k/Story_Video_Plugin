# StoryVideo

A [Remotion](https://remotion.dev) composition for beat-driven, square (1080×1080) social story videos at 30fps. Feed it an array of narrative **beats** and, optionally, a **voiceover** — beat timing redistributes automatically to match the audio.

## Quick start

```bash
npm install
npm run dev      # open Remotion Studio
npm run render   # render out/story.mp4
```

## Props (`StoryVideoProps`)

| Prop | Type | Notes |
|------|------|-------|
| `beats` | `Beat[]` | Required. The story, in order. |
| `voiceover` | `Voiceover?` | `{ src, volume?, startFromSeconds? }`. When set, plays continuously and drives beat timing. |
| `transitionDurationInFrames` | `number?` | Overlap per transition. Default `16`. |

### Beats

Seven visually distinct beat types, each with its own layout, animation, and accent color:

| Type | Layout | Key fields |
|------|--------|-----------|
| `hook` | Centered headline, scales in | `title`, `subtitle`, `eyebrow` |
| `problem` | Left-aligned, underline draws in | `title`, `body`, `eyebrow` |
| `stat` | Counting figure in a progress ring | `value`, `unit`, `label` |
| `insight` | Editorial pull-quote | `body`, `subtitle` (attribution) |
| `solution` | Staggered animated checklist | `title`, `bullets[]` |
| `cta` | Pulsing action button | `title`, `subtitle`, `cta` |
| `logo` | Mark draws in + wordmark | `brand`, `tagline` |

Every beat has:
- `durationInFrames` — base duration (also the proportional weight during redistribution).
- `fixed?` — when `true`, the beat keeps its exact duration and is **excluded** from voiceover redistribution (e.g. logo stings).
- `accent?` — override the beat type's default accent.

See [`src/sampleBeats.ts`](src/sampleBeats.ts) for a complete example.

## Voiceover timing

`calculateStoryMetadata` (in [`src/StoryVideo.tsx`](src/StoryVideo.tsx)) sets the composition duration dynamically:

- **No voiceover** → authored `durationInFrames` are used exactly.
- **Voiceover** → audio length is measured with `@remotion/media-utils`; the *flexible* (non-`fixed`) beats scale proportionally so the visible timeline matches the audio precisely, while `fixed` beats are preserved. Transition overlaps are accounted for so the on-screen total equals the audio length to the frame.

The redistribution/rounding logic lives in [`src/timing.ts`](src/timing.ts) and preserves the exact frame total via largest-remainder rounding.

To use a voiceover, drop an audio file in `public/` and set the default prop in [`src/Root.tsx`](src/Root.tsx):

```ts
import { staticFile } from "remotion";
// ...
defaultProps={{
  beats: sampleBeats,
  voiceover: { src: staticFile("voiceover.mp3"), volume: 1 },
}}
```

## Transitions

Transitions between beats use [`@remotion/transitions`](https://remotion.dev/docs/transitions) (`fade`, `slide`, `wipe`, `flip`, `clockWipe`) with alternating spring/linear timing, keyed by the destination beat type for variety. See [`src/transitions.ts`](src/transitions.ts).

## Design tokens

Brand colors and font live in [`src/theme.ts`](src/theme.ts): navy `#003087`, blue `#00A3E0`, dark bg `#0A0F1E`, Inter with a system fallback stack.
