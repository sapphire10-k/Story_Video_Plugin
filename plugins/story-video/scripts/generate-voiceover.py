#!/usr/bin/env python3
"""Generate an ElevenLabs voiceover MP3 for a Remotion StoryVideo.

Reads credentials from the macOS Keychain, calls the ElevenLabs text-to-speech
API, saves the MP3 into the Remotion public/ folder, measures its duration by
parsing MP3 frame headers directly, and prints a JSON summary to stdout.

Standard library only — no pip dependencies.

Example:
    ./generate-voiceover.py \
        --script "Your workflow is leaking hours." \
        --output voiceover.mp3 \
        --speed 1.0
"""

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request

# Keychain service names (looked up with: security find-generic-password -s NAME -w)
KEY_SERVICE = "ELEVENLABS_API_KEY"
VOICE_SERVICE = "ELEVENLABS_VOICE_ID"

MODEL_ID = "eleven_multilingual_v2"
OUTPUT_FORMAT = "mp3_44100_128"  # 44.1kHz / 128kbps
# Where the MP3 is written. Overridable so the render step can keep its
# --public-dir in sync across machines/plugin installs.
PUBLIC_DIR = os.path.expanduser(
    os.environ.get("REMOTION_PUBLIC_DIR", "~/.claude/remotion/public")
)

SPEED_MIN, SPEED_MAX = 0.7, 1.2


# --------------------------------------------------------------------------- #
# Keychain
# --------------------------------------------------------------------------- #
def keychain_secret(service: str) -> str:
    """Return the generic-password value stored under `service`."""
    try:
        result = subprocess.run(
            ["security", "find-generic-password", "-s", service, "-w"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        die(f"`security` command not found — this script requires macOS.")

    if result.returncode != 0:
        die(
            f"Could not read '{service}' from the Keychain. Add it with:\n"
            f"  security add-generic-password -a \"$USER\" -s {service} -w <value>"
        )

    secret = result.stdout.strip()
    if not secret:
        die(f"Keychain entry '{service}' is empty.")
    return secret


# --------------------------------------------------------------------------- #
# ElevenLabs TTS
# --------------------------------------------------------------------------- #
def synthesize(api_key: str, voice_id: str, text: str, speed: float) -> bytes:
    """Call the ElevenLabs TTS API and return raw MP3 bytes."""
    url = (
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        f"?output_format={OUTPUT_FORMAT}"
    )
    payload = json.dumps(
        {
            "text": text,
            "model_id": MODEL_ID,
            "voice_settings": {"speed": speed},
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        method="POST",
        headers={
            "xi-api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return resp.read()
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace").strip()
        die(f"ElevenLabs API error {exc.code} {exc.reason}: {body}")
    except urllib.error.URLError as exc:
        die(f"Network error calling ElevenLabs: {exc.reason}")


# --------------------------------------------------------------------------- #
# MP3 duration via frame-header parsing (no ffprobe)
# --------------------------------------------------------------------------- #
# MPEG version index -> label. Bits 20-19 of the header.
_VERSIONS = {0b00: "2.5", 0b10: "2", 0b11: "1"}  # 0b01 reserved
# Layer index -> layer number. Bits 18-17.
_LAYERS = {0b01: 3, 0b10: 2, 0b11: 1}  # 0b00 reserved

# Samples per frame, keyed by (version_group, layer). version_group: 1 or 2/2.5.
_SAMPLES = {
    ("1", 1): 384, ("1", 2): 1152, ("1", 3): 1152,
    ("2", 1): 384, ("2", 2): 1152, ("2", 3): 576,
}

# Sampling rates (Hz) keyed by version, indexed by bits 11-10.
_SAMPLE_RATES = {
    "1": [44100, 48000, 32000],
    "2": [22050, 24000, 16000],
    "2.5": [11025, 12000, 8000],
}

# Bitrate tables in kbps, indexed by bits 15-12 (0=free, 15=bad).
_BITRATES = {
    ("1", 1): [0, 32, 64, 96, 128, 160, 192, 224, 256, 288, 320, 352, 384, 416, 448],
    ("1", 2): [0, 32, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320, 384],
    ("1", 3): [0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320],
    ("2", 1): [0, 32, 48, 56, 64, 80, 96, 112, 128, 144, 160, 176, 192, 224, 256],
    ("2", 2): [0, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160],
    ("2", 3): [0, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160],
}


def _version_group(version: str) -> str:
    """MPEG 2 and 2.5 share the same sample-count / bitrate tables."""
    return "1" if version == "1" else "2"


def _skip_id3v2(data: bytes) -> int:
    """Return the offset past a leading ID3v2 tag, or 0 if none."""
    if len(data) >= 10 and data[:3] == b"ID3":
        # Size is 4 syncsafe bytes (7 bits each), excludes the 10-byte header.
        size = 0
        for b in data[6:10]:
            size = (size << 7) | (b & 0x7F)
        footer = 10 if (data[5] & 0x10) else 0  # extended footer flag
        return 10 + size + footer
    return 0


def _vbr_frame_count(frame: bytes) -> "int | None":
    """If `frame` carries a Xing/Info/VBRI header with a frame count, return it.

    A VBR (or LAME CBR) file's first audio frame is a silent metadata frame that
    declares the total number of audio frames — the authoritative source for
    duration, and what media players trust.
    """
    xing = frame.find(b"Xing")
    if xing < 0:
        xing = frame.find(b"Info")
    if xing >= 0 and xing + 8 <= len(frame):
        flags = int.from_bytes(frame[xing + 4 : xing + 8], "big")
        if flags & 0x0001 and xing + 12 <= len(frame):
            return int.from_bytes(frame[xing + 8 : xing + 12], "big")
        return 0  # header present but no frame-count field
    vbri = frame.find(b"VBRI")
    if vbri >= 0 and vbri + 18 <= len(frame):
        return int.from_bytes(frame[vbri + 14 : vbri + 18], "big")
    return None


def mp3_duration_secs(data: bytes) -> float:
    """Duration in seconds by parsing MPEG audio frame headers (no ffprobe).

    Uses the VBR (Xing/Info/VBRI) frame count when present; otherwise sums the
    duration of every decoded frame. Handles CBR and VBR, skips a leading ID3v2
    tag, and resyncs byte by byte over any non-audio region.
    """
    n = len(data)
    pos = _skip_id3v2(data)
    duration = 0.0
    first_frame = True

    while pos + 4 <= n:
        # Frame sync: 11 set bits (0xFFE).
        if data[pos] != 0xFF or (data[pos + 1] & 0xE0) != 0xE0:
            pos += 1
            continue

        b1, b2 = data[pos + 1], data[pos + 2]
        version = _VERSIONS.get((b1 >> 3) & 0b11)
        layer = _LAYERS.get((b1 >> 1) & 0b11)
        bitrate_idx = (b2 >> 4) & 0b1111
        rate_idx = (b2 >> 2) & 0b11
        padding = (b2 >> 1) & 0b1

        if version is None or layer is None or bitrate_idx in (0, 15) or rate_idx == 3:
            pos += 1  # not a real header; resync
            continue

        vg = _version_group(version)
        bitrate = _BITRATES[(vg, layer)][bitrate_idx] * 1000
        sample_rate = _SAMPLE_RATES[version][rate_idx]
        samples = _SAMPLES[(vg, layer)]

        slot = 4 if layer == 1 else 1
        frame_len = (samples // 8 * bitrate) // sample_rate + padding * slot
        if frame_len <= 0:
            pos += 1
            continue

        if first_frame:
            first_frame = False
            count = _vbr_frame_count(data[pos : pos + frame_len])
            if count:  # authoritative total; return immediately
                return count * samples / sample_rate
            if count == 0:  # metadata frame with no count: don't count it
                pos += frame_len
                continue

        duration += samples / sample_rate
        pos += frame_len

    return duration


# --------------------------------------------------------------------------- #
# Helpers / CLI
# --------------------------------------------------------------------------- #
def die(message: str) -> "None":
    print(message, file=sys.stderr)
    sys.exit(1)


def speed_arg(value: str) -> float:
    try:
        speed = float(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"--speed must be a number, got {value!r}")
    if not (SPEED_MIN <= speed <= SPEED_MAX):
        raise argparse.ArgumentTypeError(
            f"--speed must be between {SPEED_MIN} and {SPEED_MAX} (got {speed})"
        )
    return speed


def resolve_output(rel_path: str) -> str:
    """Resolve `rel_path` inside PUBLIC_DIR, refusing to escape it."""
    if os.path.isabs(rel_path):
        die("--output must be a relative path (it is placed inside public/).")
    base = os.path.realpath(PUBLIC_DIR)
    target = os.path.realpath(os.path.join(base, rel_path))
    if target != base and not target.startswith(base + os.sep):
        die("--output must stay within the public/ directory.")
    return target


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate an ElevenLabs voiceover MP3 for Remotion."
    )
    parser.add_argument("--script", required=True, help="Narration text to speak.")
    parser.add_argument(
        "--output",
        required=True,
        help="Relative path under ~/.claude/remotion/public/ (e.g. voiceover.mp3).",
    )
    parser.add_argument(
        "--speed",
        type=speed_arg,
        default=1.0,
        help=f"Speaking speed, {SPEED_MIN}-{SPEED_MAX}x (default 1.0).",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)

    text = args.script.strip()
    if not text:
        die("--script is empty.")

    target = resolve_output(args.output)

    api_key = keychain_secret(KEY_SERVICE)
    voice_id = keychain_secret(VOICE_SERVICE)

    audio = synthesize(api_key, voice_id, text, args.speed)
    if not audio:
        die("ElevenLabs returned no audio.")

    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, "wb") as fh:
        fh.write(audio)

    duration = mp3_duration_secs(audio)

    print(
        json.dumps(
            {
                "file": args.output,
                "duration_secs": round(duration, 3),
                "chars": len(text),
            }
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
