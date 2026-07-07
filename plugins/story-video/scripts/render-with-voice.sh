#!/usr/bin/env bash
# Thin shim -> the cross-platform Python orchestrator (render_with_voice.py).
# Kept for macOS/Linux muscle memory; Windows users call render_with_voice.py directly.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$DIR/render_with_voice.py" "$@"
