"""Generate the nine CodeBuddy demo narration clips with Edge TTS.

Install edge-tts into the active virtual environment before running this script.
The script uses only the Python standard library for MP3 duration reporting.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import edge_tts

VOICE = "en-US-JennyNeural"
RATE = "+0%"
NARRATION_LINES = [
    "Meet CodeBuddy, a beginner-friendly helper for exploring GitHub projects and getting debugging hints.",
    "A scripted message says the CodeBuddy repository is loaded, with its README and file list ready to explore.",
    "Ask what the project does, and CodeBuddy explains it in plain language.",
    "Ask how to run it, and you get clear setup steps.",
    "Now a beginner pastes an error message, called a traceback.",
    "Hint level one is a gentle nudge. It names the kind of problem without giving away the fix.",
    "Hint level two points to the file and line to check.",
    "Hint level three explains the cause and shows corrected code.",
    "Thanks for trying the CodeBuddy demo. You can now explore another public repository or paste an error to get hints.",
]


def mp3_duration_seconds(path: Path) -> float:
    """Estimate MP3 playback duration by counting MPEG audio frames."""
    data = path.read_bytes()
    offset = 0
    if data[:3] == b"ID3" and len(data) >= 10:
        tag_size = sum((data[6 + index] & 0x7F) << (7 * (3 - index)) for index in range(4))
        offset = 10 + tag_size + (10 if data[5] & 0x10 else 0)

    mpeg1_layer3_bitrates = (0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320, 0)
    mpeg2_layer3_bitrates = (0, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160, 0)
    base_sample_rates = (44100, 48000, 32000)
    frame_count = 0
    samples_per_frame = 0
    sample_rate = 0

    while offset + 4 <= len(data):
        header = int.from_bytes(data[offset:offset + 4], "big")
        if (header >> 21) != 0x7FF:
            offset += 1
            continue

        version = (header >> 19) & 0b11
        layer = (header >> 17) & 0b11
        bitrate_index = (header >> 12) & 0b1111
        sample_index = (header >> 10) & 0b11
        padding = (header >> 9) & 1
        if version == 0b01 or layer != 0b01 or bitrate_index in (0, 15) or sample_index == 3:
            offset += 1
            continue

        mpeg1 = version == 0b11
        bitrate_table = mpeg1_layer3_bitrates if mpeg1 else mpeg2_layer3_bitrates
        bitrate = bitrate_table[bitrate_index] * 1000
        rate = base_sample_rates[sample_index] // (1 if mpeg1 else 2 if version == 0b10 else 4)
        frame_length = ((144 if mpeg1 else 72) * bitrate // rate) + padding
        if frame_length < 4 or offset + frame_length > len(data):
            break

        frame_count += 1
        samples_per_frame = 1152 if mpeg1 else 576
        sample_rate = rate
        offset += frame_length

    if not frame_count or not sample_rate:
        raise ValueError(f"Could not read MP3 frames in {path.name}")
    return frame_count * samples_per_frame / sample_rate


async def generate() -> None:
    output_dir = Path(__file__).resolve().parents[1] / "static" / "audio"
    output_dir.mkdir(parents=True, exist_ok=True)

    for index, line in enumerate(NARRATION_LINES, start=1):
        output_path = output_dir / f"step_{index:02d}.mp3"
        communicate = edge_tts.Communicate(
            line,
            VOICE,
            rate=RATE,
            connect_timeout=10,
            receive_timeout=20,
        )
        await communicate.save(str(output_path))
        duration = mp3_duration_seconds(output_path)
        print(f"{output_path.name}: {duration:.2f} seconds")


if __name__ == "__main__":
    asyncio.run(generate())
