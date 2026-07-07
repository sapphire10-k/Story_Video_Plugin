# Fordham Video — Claude Code plugin

A Claude Code plugin that renders branded **1080×1080 story videos** with Remotion, with an optional AI voiceover whose length drives the on-screen beat timing. Ships the `video` skill, the Remotion project, and the render scripts together.

This repo is a **plugin marketplace** (`fordham-video`) containing one plugin (`story-video`).

---

## Install (each team member)

**In Claude Code**, run these two slash commands:

```
/plugin marketplace add sapphire10-k/Story_Video_Plugin
/plugin install story-video@fordham-video
```

> `sapphire10-k/Story_Video_Plugin` is the GitHub repo. `fordham-video` is the
> marketplace name and `story-video` is the plugin name (both defined in the
> manifests). If Claude Code doesn't pick up the plugin immediately, run
> `/reload-plugins` (or restart the session).

### Verify it loaded

- Run `/plugin` → open the **Errors** tab; it should be empty.
- Type `/story-video:` — the `video` skill should appear in the menu.

Plugin skills are **namespaced**, so this skill is invoked as **`/story-video:video`**
(not `/video`). You usually don't need to type it — just ask Claude in plain
English (e.g. *"make a 15-second story video hooking on our new product"*) and it
will trigger the skill automatically.

---

## One-time setup per machine

### 1. Node dependencies — automatic
The first time you render **with a voiceover**, the wrapper runs `npm install`
for you (~1 minute, one-off). For a **silent** render you can pre-install:
```bash
# find the installed plugin, then install deps:
cd ~/.claude/plugins/marketplaces/fordham-video/plugins/story-video/project
npm install
```

### 2. ElevenLabs credentials — only for voiceovers
Add **your own** ElevenLabs API key + a voice ID to the macOS Keychain:
```bash
security add-generic-password -a "$USER" -s ELEVENLABS_API_KEY  -w <your-api-key>
security add-generic-password -a "$USER" -s ELEVENLABS_VOICE_ID -w <your-voice-id>
```
For a **consistent brand voice** across the team, everyone should use the **same
`ELEVENLABS_VOICE_ID`** — choose a shared *premade* voice from the ElevenLabs
voice library (premade IDs are the same on every account; a cloned voice is tied
to the one account that created it).

---

## Test it (2-minute smoke test)

Ask Claude: **"Render a 10-second test story video with a voiceover, slug `hello-team`."**

Or run the wrapper directly from a terminal:
```bash
~/.claude/plugins/marketplaces/fordham-video/plugins/story-video/scripts/render-with-voice.sh \
  --script "This is our team video pipeline. If you can hear me, it works." \
  --slug hello-team
```

**Expected:** a JSON line like
```json
{"output":"/Users/<you>/03-OUTPUTS/video/YYYY-MM-DD-StoryVideo-hello-team.mp4","size":"~2M","duration_secs":9.x}
```
and an MP4 at `~/03-OUTPUTS/video/YYYY-MM-DD-StoryVideo-hello-team.mp4` (1080×1080,
duration matching the voiceover). Open it to confirm audio + visuals.

**Silent test (no ElevenLabs needed):**
```bash
cd ~/.claude/plugins/marketplaces/fordham-video/plugins/story-video/project
npx remotion render StoryVideo /tmp/test.mp4 --scale=0.5 --log=error
```

---

## Requirements

- **macOS** (credentials are read from the Keychain via `security`)
- **Node.js + npm** (for Remotion)
- **Python 3** (stdlib only — no pip packages)
- An **ElevenLabs** account (only for voiceovers — see the team billing note below)

---

## Team ElevenLabs setup (cost-effective)

Programmatic API access works on any paid ElevenLabs tier, and their ToS says
**not to share one account's API key**. So the cheapest compliant setup for 3
people is **one subscription each**, sized to volume:

- Light use → **3 × Starter ≈ $18/mo total** (30k credits each).
- More volume / higher quality → **3 × Creator ≈ $66/mo total** (121k credits each).
- A shared **Scale** plan (3 seats, shared pool) is **$299/mo** — only worth it at
  very high combined volume or if you need shared-workspace admin.

Each person puts *their own* key in the Keychain (step 2 above) but uses the
**same premade `ELEVENLABS_VOICE_ID`** for a consistent brand voice.

---

## What's inside

```
.claude-plugin/marketplace.json        # marketplace definition (name: fordham-video)
plugins/story-video/
  .claude-plugin/plugin.json           # plugin manifest (name: story-video)
  skills/video/SKILL.md                # the "video" skill (auto-loaded, /story-video:video)
  scripts/
    generate-voiceover.py              # ElevenLabs TTS -> MP3 + duration (stdlib only)
    render-with-voice.sh               # voiceover + timing-sync + render (auto-installs deps)
  project/                             # the Remotion project
    src/... package.json ...
```

Output always lands in `~/03-OUTPUTS/video/YYYY-MM-DD-StoryVideo-<slug>.mp4`.

## Updating the plugin

Bump `version` in both `.claude-plugin/marketplace.json` and
`plugins/story-video/.claude-plugin/plugin.json`, commit, and push. Team members
run `/plugin marketplace update fordham-video`, then `/reload-plugins`.
