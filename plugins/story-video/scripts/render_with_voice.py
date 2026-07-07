#!/usr/bin/env python3
"""Cross-platform orchestrator: voiceover -> merged props -> Remotion render.

Runs on macOS, Windows, and Linux (pure stdlib). Generates a voiceover via
generate-voiceover.py, merges it into the StoryVideo props, renders the MP4, and
writes it to ~/03-OUTPUTS/video/YYYY-MM-DD-StoryVideo-<slug>.mp4.

Usage:
    python render_with_voice.py --script "Narration" --slug my-clip \
        [--props base.json] [--speed 1.0] [--provider elevenlabs|magnific] \
        [--voice <name>] [--voice-id <id>]

Paths auto-resolve relative to this script / the plugin. Override with env vars:
    REMOTION_DIR, REMOTION_PUBLIC_DIR, OUTPUT_DIR, VOICEOVER_GEN
"""

import argparse
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
# When launched by a Claude Code skill, CLAUDE_PLUGIN_ROOT points at the plugin;
# otherwise fall back to this script's parent (scripts/ -> plugin root).
PLUGIN_ROOT = os.environ.get("CLAUDE_PLUGIN_ROOT") or os.path.dirname(HERE)

def _find_remotion_dir() -> str:
    """Locate the Remotion project (the dir with package.json).

    Works for the plugin layout (scripts/ + project/ siblings) and the dev
    layout (this script sitting in the project root itself).
    """
    if os.environ.get("REMOTION_DIR"):
        return os.environ["REMOTION_DIR"]
    for cand in (os.path.join(PLUGIN_ROOT, "project"), HERE, os.path.join(HERE, "project")):
        if os.path.isfile(os.path.join(cand, "package.json")):
            return cand
    return os.path.join(PLUGIN_ROOT, "project")  # default; validated in main()


REMOTION_DIR = _find_remotion_dir()
PUBLIC_DIR = os.path.expanduser(
    os.environ.get("REMOTION_PUBLIC_DIR", "~/.claude/remotion/public")
)
OUTPUT_DIR = os.path.expanduser(os.environ.get("OUTPUT_DIR", "~/03-OUTPUTS/video"))
VOICEOVER_GEN = os.environ.get("VOICEOVER_GEN") or os.path.join(HERE, "generate-voiceover.py")
COMPOSITION = "StoryVideo"


def die(message: str) -> "None":
    print(f"error: {message}", file=sys.stderr)
    sys.exit(1)


def run_node_tool(args: list, **kwargs) -> subprocess.CompletedProcess:
    """Run an npm/npx tool cross-platform (.cmd shims on Windows need the shell)."""
    exe = shutil.which(args[0])
    if exe is None:
        die(f"'{args[0]}' not found on PATH (is Node.js installed?)")
    cmd = [exe] + args[1:]
    if os.name == "nt":  # Windows: run .cmd/.bat via the shell
        return subprocess.run(subprocess.list2cmdline(cmd), shell=True, **kwargs)
    return subprocess.run(cmd, **kwargs)


def human_size(n: int) -> str:
    size = float(n)
    for unit in ("B", "K", "M", "G"):
        if size < 1024 or unit == "G":
            return f"{size:.0f}{unit}" if unit == "B" else f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}G"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate a voiceover and render StoryVideo.")
    p.add_argument("--script", required=True, help="Narration text.")
    p.add_argument("--slug", required=True, help="Filename slug.")
    p.add_argument("--props", default=None, help="Optional base props JSON to merge into.")
    p.add_argument("--speed", default=None, help="Speaking speed 0.7-1.2.")
    p.add_argument("--provider", default=None, choices=["auto", "magnific", "elevenlabs"])
    p.add_argument("--voice", default=None, help="Named voice from the registry.")
    p.add_argument("--voice-id", default=None, help="Explicit ElevenLabs voice id.")
    return p.parse_args()


def main() -> int:
    args = parse_args()

    text = args.script.strip()
    if not text:
        die("--script is empty")

    slug = re.sub(r"[^A-Za-z0-9._-]", "", args.slug.replace(" ", "-"))
    if not slug:
        die("--slug is empty after sanitization")

    if not os.path.isfile(VOICEOVER_GEN):
        die(f"voiceover generator not found: {VOICEOVER_GEN}")
    if not os.path.isdir(REMOTION_DIR):
        die(f"remotion project not found: {REMOTION_DIR}")
    if args.props and not os.path.isfile(args.props):
        die(f"--props file not found: {args.props}")

    # Keep the generator's output dir in sync with what the render reads.
    env = dict(os.environ, REMOTION_PUBLIC_DIR=PUBLIC_DIR)

    # First run on a new machine: install the Remotion project's dependencies.
    if not os.path.isdir(os.path.join(REMOTION_DIR, "node_modules")):
        print("> First run - installing Remotion dependencies (one-off, ~1 min)...", file=sys.stderr)
        r = run_node_tool(["npm", "install"], cwd=REMOTION_DIR)
        if r.returncode != 0:
            die(f"npm install failed in {REMOTION_DIR}")

    # 1. Generate the voiceover.
    print(f"> Generating voiceover ({len(text)} chars)...", file=sys.stderr)
    gen_cmd = [sys.executable, VOICEOVER_GEN, "--script", text, "--output", f"{slug}.mp3"]
    if args.speed:
        gen_cmd += ["--speed", args.speed]
    if args.provider:
        gen_cmd += ["--provider", args.provider]
    if args.voice:
        gen_cmd += ["--voice", args.voice]
    if args.voice_id:
        gen_cmd += ["--voice-id", args.voice_id]
    gen = subprocess.run(gen_cmd, env=env, capture_output=True, text=True)
    if gen.returncode != 0:
        die(f"voiceover generation failed:\n{gen.stderr.strip()}")
    try:
        vo = json.loads(gen.stdout)
        audio_file, duration = vo["file"], vo["duration_secs"]
    except (json.JSONDecodeError, KeyError):
        die(f"could not parse voiceover JSON: {gen.stdout!r}")
    print(f"> Voiceover: {audio_file}  ({duration}s)", file=sys.stderr)

    # 2. Merge voiceover metadata into the props JSON (temp file).
    props = {}
    if args.props:
        with open(args.props) as fh:
            props = json.load(fh)
        if not isinstance(props, dict):
            die("base props JSON must be an object")
    vo_props = dict(props.get("voiceover") or {})
    vo_props["src"] = audio_file
    vo_props["durationInSeconds"] = float(duration)
    vo_props.setdefault("volume", 1)
    props["voiceover"] = vo_props

    fd, merged_path = tempfile.mkstemp(prefix="storyvideo-props-", suffix=".json")
    try:
        with os.fdopen(fd, "w") as fh:
            json.dump(props, fh, indent=2)

        # 3. Render.
        date = datetime.date.today().isoformat()  # YYYY-MM-DD
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        output = os.path.join(OUTPUT_DIR, f"{date}-{COMPOSITION}-{slug}.mp4")
        print(f"> Rendering {COMPOSITION} -> {output}", file=sys.stderr)
        r = run_node_tool(
            ["npx", "remotion", "render", COMPOSITION, output,
             f"--props={merged_path}", f"--public-dir={PUBLIC_DIR}", "--log=error"],
            cwd=REMOTION_DIR,
            env=env,
        )
        if r.returncode != 0 or not os.path.isfile(output):
            die("remotion render failed")
    finally:
        if os.path.exists(merged_path):
            os.remove(merged_path)

    # 4. Report.
    size = human_size(os.path.getsize(output))
    print(f"\n✓ Done\n  file:     {output}\n  size:     {size}\n  duration: {duration}s",
          file=sys.stderr)
    print(json.dumps({"output": output, "size": size, "duration_secs": duration}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
