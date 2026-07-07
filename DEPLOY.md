# Deploying the Story Video plugin to the team

Two ways to get the plugin onto teammates' machines. Start with **A** (self-install); use **B** only if A is blocked or you want it pushed automatically.

---

## A. Each teammate self-installs (no admin needed)

Send teammates these steps (also in the [README](README.md)):

1. Open the **Claude desktop app** → **Code** tab.
2. Click **+** next to the prompt → **Plugins** → **Manage plugins → Add marketplace**.
3. Enter: `sapphire10-k/Story_Video_Plugin`
4. Install the **story-video** plugin from the **fordham-video** marketplace.
5. Quit (⌘Q) and reopen the app.
6. Verify: ask *"make a short story video"*, or check `/plugin`-style plugin list shows **story-video** with no errors.

If a teammate sees **"not allowed by organization policy,"** the org has plugin
installs locked (`strictKnownMarketplaces`) → use route B.

---

## B. Push it org-wide (needs the Director / org owner)

The **Director** (org owner, not just admin) does one of:

- **Admin console:** `https://claude.ai/admin-settings/claude-code` → add the marketplace
  + enabled plugin to managed settings, **or**
- **Managed settings file** — deploy [`deploy/managed-settings.json`](deploy/managed-settings.json)
  to each Mac at `/Library/Application Support/ClaudeCode/managed-settings.json`
  (by hand or via MDM — Jamf/Kandji). It auto-registers the marketplace **and**
  auto-enables the plugin, so teammates do nothing.

---

## Credentials each teammate needs (once)

Works on **macOS, Windows, and Linux**. Credentials resolve from env var → macOS
Keychain → secrets file.

**macOS** — Keychain:
```bash
security add-generic-password -U -a "$USER" -s ELEVENLABS_API_KEY -w   # paste when prompted
security add-generic-password -U -a "$USER" -s MAGNIFIC_API_KEY   -w
```

**Windows / Linux** — create `~/.claude/remotion/secrets.json`
(template: [`scripts/secrets.example.json`](plugins/story-video/scripts/secrets.example.json)):
```json
{ "ELEVENLABS_API_KEY": "sk-...", "MAGNIFIC_API_KEY": "..." }
```
(Or set env vars — Windows: `setx ELEVENLABS_API_KEY "..."`.)

**Brand voices registry** (all OSes) — copy
[`scripts/voices.example.json`](plugins/story-video/scripts/voices.example.json)
to `~/.claude/remotion/voices.json` and fill in the ids, then render with
`--voice manisha` / `--voice director`.

---

## ⚠️ Brand-voice access decision

Our two cloned brand voices (`manisha`, `director`) live in **one ElevenLabs
account** and can only be synthesized with **that account's API key**. A teammate
using their *own* ElevenLabs key cannot render them. Pick one:

| Option | How | Trade-off |
|--------|-----|-----------|
| **Shared brand account** (recommended) | One ElevenLabs account holds both clones; put its API key in each person's Keychain | One subscription; simplest; everyone can render both voices |
| **ElevenLabs voice-sharing** | Share each clone to teammates' own ElevenLabs accounts | ToS-clean, but each needs their own paid account |
| **Share the one API key** | Give teammates the account's key | Simplest, but against ElevenLabs' "don't share keys" guidance |

For general (non-brand) narration, **Magnific** works for everyone with no voice
sharing needed — only our custom clones require the decision above.
