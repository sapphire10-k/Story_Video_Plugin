# Fordham Video — Claude Code plugin

A Claude Code plugin that renders branded **1080×1080 story videos** with Remotion, with an optional AI voiceover whose length drives the on-screen beat timing. Ships the `video` skill, the Remotion project, and the render scripts together.

This repo is a **plugin marketplace** containing one plugin (`story-video`).

## Install (each team member)

In Claude Code:

```
/plugin marketplace add <git-url-of-this-repo>
/plugin install story-video@fordham-video
```

Then, once per machine:

```bash
# 1. Install the Remotion project's dependencies
cd "$(claude plugin path story-video)/project" 2>/dev/null || \
  cd ~/.claude/plugins/*/plugins/story-video/project    # fallback if the helper isn't available
npm install

# 2. (Voiceovers only) add ElevenLabs credentials to the macOS Keychain
security add-generic-password -a "$USER" -s ELEVENLABS_API_KEY  -w <your-api-key>
security add-generic-password -a "$USER" -s ELEVENLABS_VOICE_ID -w <your-voice-id>
```

> The exact plugin install path varies; the skill itself uses `${CLAUDE_PLUGIN_ROOT}`
> which Claude Code resolves automatically, so once installed you can just ask
> Claude to "render a story video" and it will find everything.

## Requirements

- macOS (credentials are read from the Keychain via `security`)
- Node.js + npm (for Remotion)
- Python 3 (stdlib only — no pip packages)
- An ElevenLabs account (only for voiceovers)

## What's inside

```
.claude-plugin/marketplace.json        # marketplace definition
plugins/story-video/
  .claude-plugin/plugin.json           # plugin manifest
  skills/video/SKILL.md                # the "video" skill (auto-loaded)
  scripts/
    generate-voiceover.py              # ElevenLabs TTS -> MP3 + duration (stdlib only)
    render-with-voice.sh               # voiceover + timing-sync + render wrapper
  project/                             # the Remotion project (run npm install here)
    src/... package.json ...
```

## Usage

Once installed, ask Claude things like:

- "Render a story video hooking on our Q3 launch, with a voiceover."
- "Make a silent 5-beat StoryVideo from these bullet points."

Or run the wrapper directly:

```bash
plugins/story-video/scripts/render-with-voice.sh \
  --script "Your workflow is leaking hours. Here's how to get them back." \
  --slug workflow-hook
```

Output lands in `~/03-OUTPUTS/video/YYYY-MM-DD-StoryVideo-<slug>.mp4`.

## Updating the plugin

Bump `version` in both `.claude-plugin/marketplace.json` and
`plugins/story-video/.claude-plugin/plugin.json`, commit, and push. Team members
run `/plugin marketplace update fordham-video` then reinstall/upgrade.
