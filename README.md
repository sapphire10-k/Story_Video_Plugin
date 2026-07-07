# Fordham Video — Claude Code plugin

A Claude Code plugin that renders branded **1080×1080 story videos** with Remotion, with an optional AI voiceover whose length drives the on-screen beat timing. Ships the `video` skill, the Remotion project, and the render scripts together.

This repo is a **plugin marketplace** (`fordham-video`) containing one plugin (`story-video`). Voiceovers can be generated via **Magnific** (Freepik) or **ElevenLabs**.

---

## Install

### Desktop app (what most of us use)

The `/plugin` **chat** command only exists in the terminal CLI — in the desktop app, use the UI:

1. Open the **Claude desktop app** → **Code** tab.
2. Click the **+** button next to the prompt box → **Plugins**.
3. **Manage plugins → Add marketplace**, and enter the repo:
   `sapphire10-k/Story_Video_Plugin`
4. The **fordham-video** marketplace appears → **install** the **story-video** plugin.
5. Fully quit (⌘Q) and reopen the app if it doesn't appear immediately.

### Terminal CLI (if you use `claude` in a terminal instead)

```
/plugin marketplace add sapphire10-k/Story_Video_Plugin
/plugin install story-video@fordham-video
/reload-plugins
```

### Verify + invoke

Plugin skills are **namespaced**: this one is **`/story-video:video`** (not `/video`).
You usually don't type it — just ask in plain English (*"make a 15-second story
video hooking on our new product"*) and it triggers automatically.

---

## Making it available to the whole team

Because the marketplace is a **public GitHub repo**, there are two routes:

### A. Each teammate self-installs (no admin needed)
Follow the **Desktop app** steps above. This works unless your org has locked
plugins down (see the caveat below).

### B. Admin pushes it org-wide (nobody has to install manually)
This requires **org owner** rights (your Director), not just admin:

- **Admin console** (Teams/Enterprise): the Director opens
  `https://claude.ai/admin-settings/claude-code` and adds managed settings so the
  marketplace + plugin deploy to everyone automatically, or
- **Managed settings file** (deployable via MDM — Jamf/Kandji — or by hand) at
  `/Library/Application Support/ClaudeCode/managed-settings.json` on each Mac:

```json
{
  "extraKnownMarketplaces": {
    "fordham-video": {
      "source": { "source": "github", "repo": "sapphire10-k/Story_Video_Plugin" }
    }
  },
  "enabledPlugins": { "story-video@fordham-video": true }
}
```
`enabledPlugins` auto-enables it after install, so teammates do nothing.

### Roles & the blocker to check
- A regular **admin cannot** push a plugin org-wide — only the **owner/Director** can (admin console or the managed file).
- If a teammate tries to add the marketplace and sees *"not allowed by organization policy"*, your org has **`strictKnownMarketplaces`** set. The Director must **allowlist** `sapphire10-k/Story_Video_Plugin` in the admin console before anyone can self-install.

**Short version for your situation:** ask each teammate to self-install (route A) first. If they hit the policy error, the Director needs to either allowlist the repo or deploy it org-wide (route B).

---

> **Tip:** the manual terminal commands below assume the default install path
> (`~/.claude/plugins/marketplaces/fordham-video/...`). It can vary — the reliable
> way is to just **ask Claude** to run setup/tests, since the skill resolves the
> plugin location automatically via `${CLAUDE_PLUGIN_ROOT}`.

## One-time setup per machine

### 1. Node dependencies — automatic
The first voiceover render runs `npm install` for you (~1 min, one-off). For a
**silent** render, pre-install:
```bash
cd ~/.claude/plugins/marketplaces/fordham-video/plugins/story-video/project && npm install
```

### 2. Voiceover credentials (cross-platform)

**Easiest — run the setup helper** (interactive, works on every OS; hides your
keys as you type and writes the config files for you):
```bash
python3 "<plugin>/scripts/setup.py"      # macOS / Linux
python  "<plugin>\scripts\setup.py"      # Windows
```
It prompts for your ElevenLabs / Magnific API keys and your brand voice names +
ids, then writes `~/.claude/remotion/secrets.json` and `voices.json`. Re-run any
time to add or change entries. (Or just ask Claude to "run the video setup".)

**Manual alternative.** The generator **auto-selects Magnific** if a
`MAGNIFIC_API_KEY` is available, otherwise ElevenLabs. Credentials resolve from
**env var → macOS Keychain → secrets file**, so this works on macOS, Windows,
and Linux.

**macOS — Keychain (secure):**
```bash
security add-generic-password -U -a "$USER" -s ELEVENLABS_API_KEY -w   # paste when prompted
security add-generic-password -U -a "$USER" -s MAGNIFIC_API_KEY   -w
```

**Windows / Linux — secrets file** `~/.claude/remotion/secrets.json`
(template: `plugins/story-video/scripts/secrets.example.json`):
```json
{ "ELEVENLABS_API_KEY": "sk-...", "MAGNIFIC_API_KEY": "..." }
```
Or env vars — Windows: `setx ELEVENLABS_API_KEY "..."`.

- The **voice id** is an ElevenLabs voice id (not a secret) — set per render via
  the voices registry (`~/.claude/remotion/voices.json`, `--voice <name>`).
- Force a provider: `--provider magnific|elevenlabs`, or `VOICE_PROVIDER=` env.

---

## Test it (2-minute smoke test)

Ask Claude: **"Render a 10-second test story video with a voiceover, slug `hello-team`."**

Or run the wrapper directly (cross-platform — use `python3` on mac/Linux, `python` on Windows):
```bash
python3 ~/.claude/plugins/marketplaces/fordham-video/plugins/story-video/scripts/render_with_voice.py \
  --script "This is our team video pipeline. If you can hear me, it works." \
  --slug hello-team
```
(macOS/Linux also have a `render-with-voice.sh` shim that calls the same script.)

**Expected:** a JSON line like
```json
{"output":"/Users/<you>/03-OUTPUTS/video/YYYY-MM-DD-StoryVideo-hello-team.mp4","size":"~2M","duration_secs":9.x}
```
and an MP4 at `~/03-OUTPUTS/video/YYYY-MM-DD-StoryVideo-hello-team.mp4` (1080×1080).

**Silent test (no voiceover credentials needed):**
```bash
cd ~/.claude/plugins/marketplaces/fordham-video/plugins/story-video/project
npx remotion render StoryVideo /tmp/test.mp4 --scale=0.5 --log=error
```

---

## Requirements

- **macOS, Windows, or Linux** (credentials via env var / macOS Keychain / secrets file)
- **Node.js + npm** (Remotion)
- **Python 3** (stdlib only — no pip packages)
- A **Magnific** or **ElevenLabs** account (only for voiceovers)

### Voiceover cost notes
- **Magnific:** if the team already has a Magnific subscription, its voiceover API
  (ElevenLabs Turbo v2.5) draws on those credits — no separate ElevenLabs seats.
- **ElevenLabs direct:** their ToS says don't share one key; cheapest compliant is
  one subscription each — **3 × Starter ≈ $18/mo** (light use) or **3 × Creator ≈ $66/mo**.

---

## What's inside

```
.claude-plugin/marketplace.json        # marketplace definition (name: fordham-video)
plugins/story-video/
  .claude-plugin/plugin.json           # plugin manifest (name: story-video)
  skills/video/SKILL.md                # the "video" skill (auto-loaded, /story-video:video)
  scripts/
    generate-voiceover.py              # Magnific OR ElevenLabs TTS -> audio + duration (stdlib only)
    render-with-voice.sh               # voiceover + timing-sync + render (auto-installs deps)
  project/                             # the Remotion project
    src/... package.json ...
```

Output always lands in `~/03-OUTPUTS/video/YYYY-MM-DD-StoryVideo-<slug>.mp4`.

## Updating to a new version

The marketplace tracks the repo's `main` branch, so a new push is picked up once
the marketplace catalog is refreshed. Custom marketplaces do **not** auto-update
by default, so already-installed teammates must refresh + reinstall:

**Desktop app (macOS/Windows):**
1. **+** next to the prompt → **Plugins** → **Manage plugins** → **Marketplaces** tab.
2. Select **fordham-video** and refresh it (or toggle **Enable auto-update**).
3. **Installed** tab → **story-video** → **Uninstall**, then **Discover**/reinstall it.
   (There's no dedicated "Update" button yet; reinstall is the documented path.)
4. Run `/reload-plugins` in chat, or fully quit (⌘Q) and reopen.

**Terminal CLI:**
```
/plugin marketplace update fordham-video
/plugin uninstall story-video@fordham-video
/plugin install story-video@fordham-video
/reload-plugins
```

**Web client (claude.ai/code):** plugin *management* isn't available in the web UI.
Cloud/web sessions load plugins from the **repo's** `.claude/settings.json`, so add
this there (see [deploy/managed-settings.json](deploy/managed-settings.json) for the
same content), commit, and push — cloud sessions then auto-install the latest at startup:
```json
{
  "extraKnownMarketplaces": {
    "fordham-video": { "source": { "source": "github", "repo": "sapphire10-k/Story_Video_Plugin" } }
  },
  "enabledPlugins": { "story-video@fordham-video": true }
}
```

### Publishing a new version (maintainer)
Bump `version` in both `.claude-plugin/marketplace.json` and
`plugins/story-video/.claude-plugin/plugin.json`, commit, and push `main`.
