---
name: video
description: Render branded story videos with Remotion. Use when the user wants to create, render, or produce a video, social clip, animated explainer, or narrated video from a script or set of "beats". Covers the StoryVideo composition, its props schema, voiceover generation, and the render commands.
---

# Video rendering (Remotion)

Produce square, branded story videos from a list of narrative **beats**, optionally with an AI voiceover whose length drives the on-screen timing.

`${CLAUDE_PLUGIN_ROOT}` is set by Claude Code to this plugin's install directory — use it to locate the bundled project and scripts.

## Paths

| What | Where |
|------|-------|
| Remotion project (run renders here) | `${CLAUDE_PLUGIN_ROOT}/project` |
| Voiceover generator | `${CLAUDE_PLUGIN_ROOT}/scripts/generate-voiceover.py` |
| One-shot render+voice wrapper | `${CLAUDE_PLUGIN_ROOT}/scripts/render-with-voice.sh` |
| Voiceover audio (public dir) | `~/.claude/remotion/public/` |
| **Final video output** | `~/03-OUTPUTS/video/` |

**Naming convention (always):** `YYYY-MM-DD-<Composition>-<slug>.mp4`
e.g. `2026-07-05-StoryVideo-q3-launch.mp4`. `render-with-voice.sh` applies this automatically; match it by hand for direct renders.

## First-time setup (once per machine)

Node dependencies install **automatically** on the first voiceover render (the
wrapper runs `npm install` if `project/node_modules` is missing). For a silent
direct render, install them manually once: `cd "${CLAUDE_PLUGIN_ROOT}/project" && npm install`.

For **voiceovers**, add credentials to the Keychain (once per person). The
generator supports two providers and **auto-selects Magnific** when a
`MAGNIFIC_API_KEY` is present, otherwise ElevenLabs.

**Magnific (preferred for the team — one subscription, ElevenLabs voices):**
```bash
security add-generic-password -a "$USER" -s MAGNIFIC_API_KEY  -w <your-magnific-api-key>
security add-generic-password -a "$USER" -s MAGNIFIC_VOICE_ID -w <elevenlabs-voice-id>
```

**ElevenLabs direct (alternative):**
```bash
security add-generic-password -a "$USER" -s ELEVENLABS_API_KEY  -w <your-api-key>
security add-generic-password -a "$USER" -s ELEVENLABS_VOICE_ID -w <your-voice-id>
```

- `*_VOICE_ID` is an **ElevenLabs voice id** in both cases. For a consistent brand
  voice, everyone uses the **same** id — pick a *premade* voice (premade ids are
  identical across accounts; a cloned voice is tied to its owning account).
- If only `ELEVENLABS_VOICE_ID` is set, Magnific reuses it.
- Force a provider with `--provider magnific|elevenlabs` (or `VOICE_PROVIDER=` env).

---

## Compositions

### StoryVideo
- **Dimensions:** 1080×1080 (square), 30fps
- **Duration:** dynamic — set by `calculateMetadata`, never hardcoded.
  - No voiceover → sum of beat `durationInFrames` minus transition overlaps.
  - Voiceover → the *visible* timeline is stretched/compressed to match the audio exactly.
- **Use cases:** Instagram/LinkedIn feed posts, product hooks, stat drops, mini case studies, launch teasers, narrated explainers. Anything short (≈10–40s) and vertical-feed-friendly.

There is currently **one** composition (`StoryVideo`). Add new ones under `project/src/` and register them in `project/src/Root.tsx`; document them here when you do.

---

## Props schema

`StoryVideoProps` (pass as a JSON object via `--props`):

| Field | Type | Notes |
|-------|------|-------|
| `beats` | `Beat[]` | **Required.** The story, in order. |
| `voiceover` | `Voiceover?` | Omit for silent videos. |
| `transitionDurationInFrames` | `number?` | Transition overlap. Default `16`. |

> Do **not** set `resolvedDurations` — it is injected internally by `calculateMetadata`.

### Beat

Every beat has:

| Field | Type | Notes |
|-------|------|-------|
| `type` | `"hook" \| "problem" \| "stat" \| "insight" \| "solution" \| "cta" \| "logo"` | Required. |
| `durationInFrames` | `number` | Required. Base duration; also the **proportional weight** when a voiceover redistributes timing. |
| `fixed` | `boolean?` | If `true`, keeps its exact duration and is **excluded** from voiceover redistribution (use for logo stings). |
| `accent` | `string?` | Hex override for the beat's accent color. |

Content fields (each type uses the ones marked ✓):

| Field | hook | problem | stat | insight | solution | cta | logo |
|-------|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| `eyebrow` (small label) | ✓ | ✓ | | ✓ | ✓ | | |
| `title` | ✓ | ✓ | | | ✓ | ✓ | |
| `subtitle` | ✓ | | | ✓ (attribution) | | ✓ | |
| `body` | | ✓ | | ✓ (the quote) | | | |
| `value` (big figure) | | | ✓ | | | | |
| `unit` (e.g. `%`, `min`) | | | ✓ | | | | |
| `label` (caption) | | | ✓ | | | | |
| `bullets` `string[]` | | | | | ✓ | | |
| `cta` (button text) | | | | | | ✓ | |
| `brand` / `tagline` | | | | | | | ✓ |

### Voiceover

| Field | Type | Notes |
|-------|------|-------|
| `src` | `string` | Bare filename (e.g. `"vo.mp3"`) resolved via `staticFile()` against the public dir; or an absolute URL / data URI. |
| `volume` | `number?` | Linear gain 0–1. Default `1`. |
| `startFromSeconds` | `number?` | Trim seconds off the start. |
| `durationInSeconds` | `number?` | Known length; drives redistribution directly. `render-with-voice.sh` fills this in from the generator. |

### Example props JSON

```json
{
  "beats": [
    { "type": "hook", "durationInFrames": 90, "eyebrow": "For growing teams", "title": "Your workflow is leaking hours.", "subtitle": "And you can't see where." },
    { "type": "stat", "durationInFrames": 90, "value": "23", "unit": "min", "label": "to refocus after one interruption" },
    { "type": "solution", "durationInFrames": 120, "eyebrow": "The fix", "title": "One surface for everything", "bullets": ["Unified inbox across every app", "AI that drafts before you ask"] },
    { "type": "cta", "durationInFrames": 90, "title": "Get your hours back.", "cta": "Try it now" },
    { "type": "logo", "durationInFrames": 75, "fixed": true, "brand": "Fordham", "tagline": "Focus, restored" }
  ],
  "transitionDurationInFrames": 16
}
```

---

## Rendering

### Option A — with voiceover (preferred for narrated videos)

`render-with-voice.sh` generates the voiceover (ElevenLabs TTS), syncs beat timing to the audio length, renders, and writes to the output dir with the correct filename.

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/render-with-voice.sh" \
  --script "Your workflow is leaking hours. Here's how to get them back." \
  --slug workflow-hook \
  [--props /path/to/base-props.json] \
  [--speed 1.0]
```

- `--script` — narration text (also the audio timing driver).
- `--slug` — filename slug (sanitized to `[A-Za-z0-9._-]`).
- `--props` — optional base props (your `beats`). The script merges the voiceover into it. If omitted, the composition's default beats are used.
- `--speed` — 0.7–1.2 (optional).

It prints a JSON summary and reports size + duration. Temp files are auto-cleaned.

### Option B — direct render (silent, or you already have audio)

```bash
cd "${CLAUDE_PLUGIN_ROOT}/project"
npx remotion render StoryVideo \
  ~/03-OUTPUTS/video/$(date +%F)-StoryVideo-<slug>.mp4 \
  --props=/path/to/props.json \
  --log=error
```

If your `props.json` references a voiceover file in `~/.claude/remotion/public/`, add:
`--public-dir="$HOME/.claude/remotion/public"`.

Fast-iteration tip: add `--scale=0.5` while checking visuals.

### When to use which

| Situation | Use |
|-----------|-----|
| You have narration text and want spoken audio | **`render-with-voice.sh`** |
| Timing should follow the voiceover | **`render-with-voice.sh`** |
| Silent video (music added later, or no audio) | **Direct render** |
| You already have a finished audio file | **Direct render** (put it in the public dir, reference it in props) |
| Rapid visual iteration (avoid TTS cost/latency) | **Direct render**, add audio on the final pass |

---

## Writing the copy — keep it TIGHT

On-screen text is read in ~2 seconds. Be ruthless.

- **Headlines / titles: max 8 words.**
- **Bullets: max 12 words each**, 3 bullets max per `solution` beat.
- `eyebrow`: 1–4 words, it's a label not a sentence.
- `stat.value`: just the number + short `unit` (`87` + `%`). Put context in `label`.
- `insight.body`: one sentence, ≤ ~14 words — it's a pull-quote.
- `cta`: 2–3 words on the button (`Try it now`, `Get the guide`).
- Cut filler ("really", "just", "in order to"). Prefer verbs over adjectives.
- The **voiceover** carries detail; the **screen** carries the punchline. Don't duplicate long sentences on screen — summarize them.

If the user's copy is too long, tighten it and show them the trimmed version before rendering.
