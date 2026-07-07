#!/usr/bin/env python3
"""Generate a voiceover audio file for a Remotion StoryVideo.

Supports two providers, both using ElevenLabs voices:
  * magnific   — Magnific/Freepik async voiceover API (x-magnific-api-key)
  * elevenlabs — ElevenLabs TTS API directly (xi-api-key)

By default the provider is auto-selected: Magnific if a MAGNIFIC_API_KEY is in
the Keychain, otherwise ElevenLabs. Credentials are read from the macOS Keychain,
the audio is written into the Remotion public/ folder, its duration is measured
by parsing the audio headers directly (no ffprobe), and a JSON summary is printed
to stdout.

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
import time
import urllib.error
import urllib.parse
import urllib.request

# Keychain service names (looked up with: security find-generic-password -s NAME -w)
ELEVENLABS_KEY_SERVICE = "ELEVENLABS_API_KEY"
ELEVENLABS_VOICE_SERVICE = "ELEVENLABS_VOICE_ID"
MAGNIFIC_KEY_SERVICE = "MAGNIFIC_API_KEY"
MAGNIFIC_VOICE_SERVICE = "MAGNIFIC_VOICE_ID"

# ElevenLabs direct
ELEVENLABS_MODEL_ID = "eleven_multilingual_v2"
ELEVENLABS_OUTPUT_FORMAT = "mp3_44100_128"  # 44.1kHz / 128kbps

# Magnific (Freepik) — ElevenLabs Turbo v2.5, async task API
MAGNIFIC_ENDPOINT = "https://api.magnific.com/v1/ai/voiceover/elevenlabs-turbo-v2-5"
MAGNIFIC_POLL_INTERVAL = 2.0     # seconds between status checks
MAGNIFIC_POLL_TIMEOUT = 180.0    # give up after this long

# Where the audio is written. Overridable so the render step can keep its
# --public-dir in sync across machines/plugin installs.
PUBLIC_DIR = os.path.expanduser(
    os.environ.get("REMOTION_PUBLIC_DIR", "~/.claude/remotion/public")
)

SPEED_MIN, SPEED_MAX = 0.7, 1.2


# --------------------------------------------------------------------------- #
# Keychain
# --------------------------------------------------------------------------- #
def keychain_lookup(service: str) -> "str | None":
    """Return the generic-password value for `service`, or None if absent."""
    try:
        result = subprocess.run(
            ["security", "find-generic-password", "-s", service, "-w"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        die("`security` command not found — this script requires macOS.")
    if result.returncode != 0:
        return None
    secret = result.stdout.strip()
    return secret or None


def keychain_secret(service: str) -> str:
    """Return the Keychain value for `service`, or exit with guidance."""
    secret = keychain_lookup(service)
    if not secret:
        die(
            f"Could not read '{service}' from the Keychain. Add it with:\n"
            f"  security add-generic-password -a \"$USER\" -s {service} -w <value>"
        )
    return secret


# --------------------------------------------------------------------------- #
# ElevenLabs (direct) provider
# --------------------------------------------------------------------------- #
def synthesize_elevenlabs(api_key: str, voice_id: str, text: str, speed: float) -> bytes:
    """Call the ElevenLabs TTS API and return raw MP3 bytes (synchronous)."""
    url = (
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        f"?output_format={ELEVENLABS_OUTPUT_FORMAT}"
    )
    payload = json.dumps(
        {
            "text": text,
            "model_id": ELEVENLABS_MODEL_ID,
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
# Magnific (Freepik) provider — async: submit task, poll, download
# --------------------------------------------------------------------------- #
def _magnific_request(method: str, url: str, api_key: str, body: "dict | None" = None) -> dict:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    headers = {"x-magnific-api-key": api_key}
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace").strip()
        die(f"Magnific API error {exc.code} {exc.reason}: {detail}")
    except urllib.error.URLError as exc:
        die(f"Network error calling Magnific: {exc.reason}")


def _download(url: str, api_key: str) -> bytes:
    """Download the generated audio. Retries with the API key if the URL is protected."""
    for headers in ({}, {"x-magnific-api-key": api_key}):
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                return resp.read()
        except urllib.error.HTTPError as exc:
            if exc.code in (401, 403) and not headers:
                continue  # signed URL failed anonymously; retry with auth
            die(f"Failed to download audio ({exc.code} {exc.reason}) from {url}")
        except urllib.error.URLError as exc:
            die(f"Network error downloading audio: {exc.reason}")
    die("Could not download the generated audio (authentication failed).")


def synthesize_magnific(api_key: str, voice_id: str, text: str, speed: float) -> "tuple[bytes, str]":
    """Submit a Magnific voiceover task, poll until done, return (audio_bytes, source_url)."""
    submit = _magnific_request(
        "POST",
        MAGNIFIC_ENDPOINT,
        api_key,
        {
            "text": text,
            "voice_id": voice_id,
            "speed": speed,
            "use_speaker_boost": True,
        },
    )
    task_id = (submit.get("data") or {}).get("task_id")
    if not task_id:
        die(f"Magnific did not return a task_id: {json.dumps(submit)}")

    status_url = f"{MAGNIFIC_ENDPOINT}/{task_id}"
    deadline = time.monotonic() + MAGNIFIC_POLL_TIMEOUT
    while True:
        data = _magnific_request("GET", status_url, api_key).get("data") or {}
        status = data.get("status")
        if status == "COMPLETED":
            generated = data.get("generated") or []
            if not generated:
                die("Magnific task completed but returned no audio URL.")
            url = generated[0]
            return _download(url, api_key), url
        if status == "FAILED":
            die(f"Magnific voiceover task {task_id} failed.")
        if time.monotonic() > deadline:
            die(f"Timed out after {MAGNIFIC_POLL_TIMEOUT:.0f}s waiting for Magnific task {task_id}.")
        time.sleep(MAGNIFIC_POLL_INTERVAL)


# --------------------------------------------------------------------------- #
# Audio format detection + duration
# --------------------------------------------------------------------------- #
def audio_kind(data: bytes, url: str = "") -> str:
    """Best-effort audio container detection: 'mp3', 'wav', or a URL-derived ext."""
    if data[:3] == b"ID3" or (len(data) >= 2 and data[0] == 0xFF and (data[1] & 0xE0) == 0xE0):
        return "mp3"
    if data[:4] == b"RIFF" and data[8:12] == b"WAVE":
        return "wav"
    ext = os.path.splitext(urllib.parse.urlparse(url).path)[1].lower().lstrip(".")
    return ext or "mp3"


def wav_duration_secs(data: bytes) -> float:
    """Duration of a PCM WAV by reading the fmt/data chunks (no dependencies)."""
    if data[:4] != b"RIFF" or data[8:12] != b"WAVE":
        return 0.0
    pos = 12
    byte_rate = 0
    data_size = 0
    n = len(data)
    while pos + 8 <= n:
        chunk_id = data[pos : pos + 4]
        chunk_size = int.from_bytes(data[pos + 4 : pos + 8], "little")
        body = pos + 8
        if chunk_id == b"fmt " and body + 16 <= n:
            byte_rate = int.from_bytes(data[body + 8 : body + 12], "little")
        elif chunk_id == b"data":
            data_size = chunk_size
        pos = body + chunk_size + (chunk_size & 1)  # chunks are word-aligned
    return data_size / byte_rate if byte_rate else 0.0


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


def duration_secs(data: bytes, kind: str) -> float:
    """Dispatch duration measurement on the detected audio kind."""
    if kind == "wav":
        return wav_duration_secs(data)
    return mp3_duration_secs(data)


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


def choose_provider(requested: str) -> str:
    """Resolve 'auto' to a concrete provider based on available credentials."""
    if requested != "auto":
        return requested
    return "magnific" if keychain_lookup(MAGNIFIC_KEY_SERVICE) else "elevenlabs"


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a voiceover (Magnific or ElevenLabs) for Remotion."
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
    parser.add_argument(
        "--provider",
        choices=["auto", "magnific", "elevenlabs"],
        default=os.environ.get("VOICE_PROVIDER", "auto"),
        help="TTS provider. 'auto' uses Magnific if MAGNIFIC_API_KEY is set, else ElevenLabs.",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)

    text = args.script.strip()
    if not text:
        die("--script is empty.")

    # Validate the requested output path early (traversal guard).
    resolve_output(args.output)

    provider = choose_provider(args.provider)

    if provider == "magnific":
        api_key = keychain_secret(MAGNIFIC_KEY_SERVICE)
        # Magnific expects an ElevenLabs voice_id; reuse the ElevenLabs one if a
        # dedicated Magnific voice id isn't set.
        voice_id = keychain_lookup(MAGNIFIC_VOICE_SERVICE) or keychain_lookup(ELEVENLABS_VOICE_SERVICE)
        if not voice_id:
            die(
                "No voice id found. Add one with:\n"
                f"  security add-generic-password -a \"$USER\" -s {MAGNIFIC_VOICE_SERVICE} -w <elevenlabs-voice-id>"
            )
        audio, source_url = synthesize_magnific(api_key, voice_id, text, args.speed)
    else:
        api_key = keychain_secret(ELEVENLABS_KEY_SERVICE)
        voice_id = keychain_secret(ELEVENLABS_VOICE_SERVICE)
        audio = synthesize_elevenlabs(api_key, voice_id, text, args.speed)
        source_url = ""

    if not audio:
        die(f"{provider} returned no audio.")

    # Save with an extension that matches the actual audio (usually .mp3).
    kind = audio_kind(audio, source_url)
    out_rel = args.output
    if os.path.splitext(out_rel)[1].lower().lstrip(".") != kind:
        out_rel = os.path.splitext(out_rel)[0] + "." + kind
    target = resolve_output(out_rel)

    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, "wb") as fh:
        fh.write(audio)

    print(
        json.dumps(
            {
                "file": out_rel,
                "duration_secs": round(duration_secs(audio, kind), 3),
                "chars": len(text),
                "provider": provider,
            }
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
