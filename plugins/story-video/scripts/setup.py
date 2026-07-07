#!/usr/bin/env python3
"""Interactive setup for Story Video credentials and brand voices.

Cross-platform (macOS / Windows / Linux). Writes two local files:
  ~/.claude/remotion/secrets.json   API keys (kept private, chmod 600 on Unix)
  ~/.claude/remotion/voices.json    named brand voices -> ElevenLabs voice ids

Re-run any time to add or change entries — existing values are preserved unless
you type a new one over them. Nothing is committed or sent anywhere.

Usage:
    python setup.py        (Windows)
    python3 setup.py       (macOS / Linux)
"""

import getpass
import json
import os
import stat
import sys

BASE = os.path.expanduser(os.environ.get("REMOTION_HOME", "~/.claude/remotion"))
SECRETS = os.path.join(BASE, "secrets.json")
VOICES = os.path.join(BASE, "voices.json")


def load(path: str) -> dict:
    try:
        with open(path) as fh:
            data = json.load(fh)
        return {k: v for k, v in data.items() if not k.startswith("_")} if isinstance(data, dict) else {}
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def save(path: str, data: dict, private: bool = False) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        json.dump(data, fh, indent=2)
        fh.write("\n")
    if private and os.name == "posix":
        try:
            os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)  # 0600
        except OSError:
            pass


def ask(label: str) -> str:
    try:
        return input(label).strip()
    except EOFError:
        return ""


def ask_secret(label: str) -> str:
    try:
        return getpass.getpass(label).strip()
    except EOFError:
        return ""


def main() -> int:
    print("Story Video - setup")
    print("=" * 30)
    print(f"Config folder: {BASE}\n")

    # --- API keys -----------------------------------------------------------
    secrets = load(SECRETS)
    print("API keys (press Enter to keep the current value / skip):")
    for name, human in (
        ("ELEVENLABS_API_KEY", "ElevenLabs API key"),
        ("MAGNIFIC_API_KEY", "Magnific API key"),
    ):
        marker = " [already set]" if secrets.get(name) else ""
        value = ask_secret(f"  {human}{marker}: ")
        if value:
            secrets[name] = value
    secrets = {k: v for k, v in secrets.items() if v}
    save(SECRETS, secrets, private=True)

    # --- Brand voices -------------------------------------------------------
    voices = load(VOICES)
    print("\nBrand voices — map a name to an ElevenLabs voice id.")
    if voices:
        print("  currently defined:", ", ".join(sorted(voices)))
    print("  Enter a blank name when you're finished.")
    while True:
        name = ask("  voice name (e.g. director): ")
        if not name:
            break
        vid = ask(f"    ElevenLabs voice id for '{name}': ")
        if vid:
            voices[name] = vid
        else:
            print("    (skipped — no id entered)")
    save(VOICES, voices)

    # --- Summary ------------------------------------------------------------
    print("\nDone.")
    print(f"  secrets: {SECRETS}  ({', '.join(sorted(secrets)) or 'none set'})")
    print(f"  voices:  {VOICES}  ({', '.join(sorted(voices)) or 'none set'})")
    print("\nNext: ask Claude to \"make a story video in the <name> voice\", or run:")
    print("  python render_with_voice.py --provider elevenlabs --voice <name> \\")
    print("      --script \"Your narration\" --slug my-clip")
    return 0


if __name__ == "__main__":
    sys.exit(main())
