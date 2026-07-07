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
| One-shot render+voice wrapper (cross-platform) | `${CLAUDE_PLUGIN_ROOT}/scripts/render_with_voice.py` (run with `python`/`python3`; `.sh` shim on mac/Linux) |
| Voiceover audio (public dir) | `~/.claude/remotion/public/` |
| **Final video output** | `~/03-OUTPUTS/video/` |

**Naming convention (always):** `YYYY-MM-DD-<Composition>-<slug>.mp4`
e.g. `2026-07-05-StoryVideo-q3-launch.mp4`. `render-with-voice.sh` applies this automatically; match it by hand for direct renders.

## First-time setup (once per machine)

Node dependencies install **automatically** on the first voiceover render (the
wrapper runs `npm install` if `project/node_modules` is missing). For a silent
direct render, install them manually once: `cd "${CLAUDE_PLUGIN_ROOT}/project" && npm install`.

For **voiceovers**, provide credentials. The generator **auto-selects Magnific**
when a `MAGNIFIC_API_KEY` is available, otherwise ElevenLabs. Credentials resolve
**cross-platform** in this order: environment variable → macOS Keychain → secrets
file. So it runs on macOS, Windows, and Linux:

**macOS — Keychain (most secure):**
```bash
security add-generic-password -U -a "$USER" -s ELEVENLABS_API_KEY -w   # paste when prompted
security add-generic-password -U -a "$USER" -s MAGNIFIC_API_KEY   -w
```

**Windows / Linux — secrets file** at `~/.claude/remotion/secrets.json`
(see `scripts/secrets.example.json`):
```json
{ "ELEVENLABS_API_KEY": "sk-...", "MAGNIFIC_API_KEY": "..." }
```
…or environment variables (Windows: `setx ELEVENLABS_API_KEY "..."`).

- The **voice id** is an ElevenLabs voice id (not a secret) — set it per render
  via the voices registry (below) rather than storing a credential.
- Force a provider with `--provider magnific|elevenlabs` (or `VOICE_PROVIDER=` env).
- **Custom / cloned voices** (made in your own ElevenLabs account) only work via
  **ElevenLabs-direct** — Magnific can't reach private voices. Use `--provider
  elevenlabs` for those. Magnific is for **premade / shared-library** voices.

### Named brand voices (registry)

Voice ids aren't secrets, so brand voices live in a **local** JSON registry
(`~/.claude/remotion/voices.json`, not committed) mapping names → ElevenLabs voice ids:
```json
{ "manisha": "LAzZ…", "director": "jS55…" }
```
Select one per render — no Keychain juggling:
```bash
./render-with-voice.sh --provider elevenlabs --voice director --script "…" --slug board-update
```
- `--voice <name>` resolves from the registry; `--voice-id <id>` passes a raw id;
  with neither, the Keychain default (`ELEVENLABS_VOICE_ID`) is used.
- When the user names a person ("in the director's voice"), map it to `--voice <name>`.
- See `scripts/voices.example.json` for the format; each teammate keeps their own
  `~/.claude/remotion/voices.json`.

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

`render_with_voice.py` (cross-platform: macOS/Windows/Linux) generates the
voiceover, syncs beat timing to the audio length, renders, and writes to the
output dir with the correct filename. **Invoke it with Python** so it works on
every OS:

```bash
# macOS / Linux
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/render_with_voice.py" \
  --provider elevenlabs --voice director \
  --script "Your workflow is leaking hours." --slug workflow-hook \
  [--props /path/to/base-props.json] [--speed 1.0]
```
```powershell
# Windows (PowerShell / CMD)
python "%CLAUDE_PLUGIN_ROOT%\scripts\render_with_voice.py" --provider elevenlabs --voice director --script "..." --slug workflow-hook
```

- `--script` — narration text (also the audio timing driver).
- `--slug` — filename slug (sanitized to `[A-Za-z0-9._-]`).
- `--voice` / `--voice-id` — pick a brand voice; `--provider` forces magnific|elevenlabs.
- `--props` — optional base props (your `beats`); the voiceover is merged in. If omitted, the default beats are used.
- `--speed` — 0.7–1.2 (optional).

A `render-with-voice.sh` shim exists for macOS/Linux muscle memory (it just calls
the Python script). It prints a JSON summary; temp files are auto-cleaned.

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
