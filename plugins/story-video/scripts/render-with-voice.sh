#!/usr/bin/env bash
#
# render-with-voice.sh — generate an ElevenLabs voiceover, merge it into the
# StoryVideo props, and render the final MP4.
#
# Usage:
#   ./render-with-voice.sh --script "Narration text" --slug my-clip [--props base.json] [--speed 1.0]
#
# Output:
#   ~/03-OUTPUTS/video/YYYY-MM-DD-StoryVideo-<slug>.mp4
#
# Paths auto-resolve relative to this plugin. Override any with env vars:
#   REMOTION_DIR, PUBLIC_DIR, VOICEOVER_GEN, OUTPUT_DIR
#
set -euo pipefail

# --------------------------------------------------------------------------- #
# Configuration — self-locating so it works from any machine / plugin install
# --------------------------------------------------------------------------- #
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# When invoked by a Claude Code skill, CLAUDE_PLUGIN_ROOT points at the plugin;
# otherwise fall back to this script's parent (scripts/ -> plugin root).
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"

REMOTION_DIR="${REMOTION_DIR:-$PLUGIN_ROOT/project}"
VOICEOVER_GEN="${VOICEOVER_GEN:-$SCRIPT_DIR/generate-voiceover.py}"
PUBLIC_DIR="${PUBLIC_DIR:-$HOME/.claude/remotion/public}"
OUTPUT_DIR="${OUTPUT_DIR:-$HOME/03-OUTPUTS/video}"
COMPOSITION="StoryVideo"

# Keep the generator's output dir in sync with what the render reads.
export REMOTION_PUBLIC_DIR="$PUBLIC_DIR"

# --------------------------------------------------------------------------- #
# Temp-file bookkeeping + cleanup
# --------------------------------------------------------------------------- #
TMP_FILES=()
cleanup() {
  for f in "${TMP_FILES[@]:-}"; do
    [[ -n "$f" && -e "$f" ]] && rm -f "$f"
  done
}
trap cleanup EXIT

die() { echo "error: $*" >&2; exit 1; }

usage() {
  sed -n '2,18p' "$0" | sed 's/^# \{0,1\}//'
}

# --------------------------------------------------------------------------- #
# Parse arguments
# --------------------------------------------------------------------------- #
SCRIPT_TEXT=""
SLUG=""
PROPS_PATH=""
SPEED=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --script)   SCRIPT_TEXT="${2:-}"; shift 2 ;;
    --script=*) SCRIPT_TEXT="${1#*=}"; shift ;;
    --slug)     SLUG="${2:-}"; shift 2 ;;
    --slug=*)   SLUG="${1#*=}"; shift ;;
    --props)    PROPS_PATH="${2:-}"; shift 2 ;;
    --props=*)  PROPS_PATH="${1#*=}"; shift ;;
    --speed)    SPEED="${2:-}"; shift 2 ;;
    --speed=*)  SPEED="${1#*=}"; shift ;;
    -h|--help)  usage; exit 0 ;;
    *)          die "unknown argument: $1" ;;
  esac
done

[[ -n "$SCRIPT_TEXT" ]] || die "--script is required"
[[ -n "$SLUG" ]]        || die "--slug is required"

# Sanitize slug: spaces -> dashes, keep [A-Za-z0-9._-] only.
SLUG_CLEAN="$(printf '%s' "$SLUG" | tr ' ' '-' | tr -cd 'A-Za-z0-9._-')"
[[ -n "$SLUG_CLEAN" ]] || die "--slug is empty after sanitization"

# Preconditions.
command -v python3 >/dev/null 2>&1 || die "python3 not found"
command -v npx >/dev/null 2>&1     || die "npx not found"
[[ -f "$VOICEOVER_GEN" ]]          || die "voiceover generator not found: $VOICEOVER_GEN"
[[ -d "$REMOTION_DIR" ]]           || die "remotion project not found: $REMOTION_DIR"

# First run on a new machine: install the Remotion project's dependencies.
if [[ ! -d "$REMOTION_DIR/node_modules" ]]; then
  echo "› First run — installing Remotion dependencies (one-off, ~1 min)…" >&2
  (cd "$REMOTION_DIR" && npm install) >&2 || die "npm install failed in $REMOTION_DIR"
fi

if [[ -n "$PROPS_PATH" ]]; then
  [[ -f "$PROPS_PATH" ]] || die "--props file not found: $PROPS_PATH"
fi

# --------------------------------------------------------------------------- #
# 1. Generate the voiceover
# --------------------------------------------------------------------------- #
echo "› Generating voiceover (${#SCRIPT_TEXT} chars)…" >&2
gen_args=(--script "$SCRIPT_TEXT" --output "${SLUG_CLEAN}.mp3")
[[ -n "$SPEED" ]] && gen_args+=(--speed "$SPEED")

VO_JSON="$(python3 "$VOICEOVER_GEN" "${gen_args[@]}")" \
  || die "voiceover generation failed"

# --------------------------------------------------------------------------- #
# 2. Parse the generator's JSON (audio file + duration)
# --------------------------------------------------------------------------- #
read -r AUDIO_FILE DURATION <<EOF
$(printf '%s' "$VO_JSON" | python3 -c '
import sys, json
d = json.load(sys.stdin)
print(d["file"], d["duration_secs"])
')
EOF
[[ -n "$AUDIO_FILE" && -n "$DURATION" ]] || die "could not parse voiceover JSON: $VO_JSON"
echo "› Voiceover: $AUDIO_FILE  (${DURATION}s)" >&2

# --------------------------------------------------------------------------- #
# 3. Merge voiceover metadata into the props JSON (written to /tmp)
# --------------------------------------------------------------------------- #
MERGED_PROPS="$(mktemp /tmp/storyvideo-props.XXXXXX.json)"
TMP_FILES+=("$MERGED_PROPS")

BASE_PROPS="${PROPS_PATH:-}" \
AUDIO_FILE="$AUDIO_FILE" \
DURATION="$DURATION" \
python3 - "$MERGED_PROPS" <<'PY'
import json, os, sys

out_path = sys.argv[1]
base_path = os.environ.get("BASE_PROPS") or ""

props = {}
if base_path:
    with open(base_path) as fh:
        props = json.load(fh)
    if not isinstance(props, dict):
        sys.exit("base props JSON must be an object")

vo = dict(props.get("voiceover") or {})
vo["src"] = os.environ["AUDIO_FILE"]
vo["durationInSeconds"] = float(os.environ["DURATION"])
vo.setdefault("volume", 1)
props["voiceover"] = vo

with open(out_path, "w") as fh:
    json.dump(props, fh, indent=2)
PY

# --------------------------------------------------------------------------- #
# 4. Render
# --------------------------------------------------------------------------- #
DATE="$(date +%F)"  # YYYY-MM-DD
OUTPUT="$OUTPUT_DIR/${DATE}-StoryVideo-${SLUG_CLEAN}.mp4"
mkdir -p "$OUTPUT_DIR"

echo "› Rendering $COMPOSITION → $OUTPUT" >&2
(
  cd "$REMOTION_DIR"
  npx remotion render "$COMPOSITION" "$OUTPUT" \
    --props="$MERGED_PROPS" \
    --public-dir="$PUBLIC_DIR" \
    --log=error
) || die "remotion render failed"

[[ -f "$OUTPUT" ]] || die "render reported success but output is missing: $OUTPUT"

# --------------------------------------------------------------------------- #
# 5. Report
# --------------------------------------------------------------------------- #
SIZE="$(du -h "$OUTPUT" | cut -f1 | tr -d '[:space:]')"
echo >&2
echo "✓ Done" >&2
echo "  file:     $OUTPUT" >&2
echo "  size:     $SIZE" >&2
echo "  duration: ${DURATION}s" >&2

# Machine-readable summary on stdout.
printf '{"output":"%s","size":"%s","duration_secs":%s}\n' "$OUTPUT" "$SIZE" "$DURATION"
