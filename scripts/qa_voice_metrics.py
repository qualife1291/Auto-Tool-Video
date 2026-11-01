"""Transparent measurements of synthetic QA voice WAVs, never speech approval.

Vietnamese whitespace-separated units are not necessarily lexical words.
Measured duration includes leading/trailing silence in the processed PCM file.
"""

from __future__ import annotations

import math
import sys
import wave
from array import array
from pathlib import Path

# 40-ms RMS windows distinguish pauses from the frequent zero crossings in speech.
WINDOW_SECONDS = 0.04
QUIET_DBFS = -45.0
NEAR_FULL_SCALE = 32760


def measure_voice_wav(path: Path, narration: str) -> dict:
    """Measure decoded mono PCM16 waveform without inferring intelligibility."""
    with wave.open(str(path), "rb") as wav:
        if (
            wav.getnchannels() != 1
            or wav.getsampwidth() != 2
            or wav.getcomptype() != "NONE"
        ):
            raise ValueError("Source voice not uncompressed mono PCM16")
        rate = wav.getframerate()
        count = wav.getnframes()
        if rate <= 0 or count <= 0:
            raise ValueError("Source voice WAV has no audio frames")
        window_frames = max(1, round(rate * WINDOW_SECONDS))
        quiet_windows = 0
        total_windows = 0
        elapsed_frames = 0
        first_active_frame = None
        last_active_end_frame = None
        current_quiet_frames = 0
        longest_quiet_frames = 0
        peak = 0
        near_full_scale = 0
        quiet_threshold = 32768 * 10 ** (QUIET_DBFS / 20)
        while block := wav.readframes(window_frames):
            samples = array("h")
            samples.frombytes(block)
            if sys.byteorder != "little":
                samples.byteswap()
            if not samples:
                break
            energy = 0
            for sample in samples:
                amplitude = abs(sample)
                peak = max(peak, amplitude)
                if amplitude >= NEAR_FULL_SCALE:
                    near_full_scale += 1
                energy += sample * sample
            block_frames = len(samples)
            if math.sqrt(energy / block_frames) < quiet_threshold:
                quiet_windows += 1
                current_quiet_frames += block_frames
                longest_quiet_frames = max(longest_quiet_frames, current_quiet_frames)
            else:
                if first_active_frame is None:
                    first_active_frame = elapsed_frames
                last_active_end_frame = elapsed_frames + block_frames
                current_quiet_frames = 0
            elapsed_frames += block_frames
            total_windows += 1

    duration = count / rate
    # Window-level activity detects speech-sized audio regions, not words.
    # Keep internal pauses inside the span; exclude only quiet padding outside.
    if first_active_frame is None:
        leading_quiet_frames = count
        trailing_quiet_frames = count
        speech_span_frames = 0
    else:
        leading_quiet_frames = first_active_frame
        trailing_quiet_frames = count - last_active_end_frame
        speech_span_frames = last_active_end_frame - first_active_frame
    units = len(narration.split())
    warnings = []
    if quiet_windows == total_windows:
        warnings.append("ALL_WINDOWS_QUIET")
    if near_full_scale:
        warnings.append("NEAR_FULL_SCALE_SAMPLES")
    return {
        "duration": duration,
        "space_delimited_units": units,
        "units_per_minute": round(60 * units / duration, 1),
        "speech_span_seconds": round(speech_span_frames / rate, 3),
        "speech_span_units_per_minute": (
            round(60 * units * rate / speech_span_frames, 1)
            if speech_span_frames
            else None
        ),
        "speech_span_basis": (
            "space-delimited text units / first-to-last nonquiet 40ms PCM window; "
            "includes pauses between sounds; NOT lexical WPM or validated pronunciation"
        ),
        "leading_quiet_seconds": round(leading_quiet_frames / rate, 3),
        "trailing_quiet_seconds": round(trailing_quiet_frames / rate, 3),
        "longest_quiet_seconds": round(longest_quiet_frames / rate, 3),
        "pace_basis": "space-delimited Vietnamese text units / full processed WAV duration; not words",
        "quiet_window_fraction": round(quiet_windows / total_windows, 3),
        "quiet_window_ms": round(1000 * window_frames / rate, 2),
        "quiet_threshold_dbfs": QUIET_DBFS,
        "peak_dbfs": round(20 * math.log10(peak / 32768), 1) if peak else None,
        "near_full_scale_samples": near_full_scale,
        "audio_warnings": warnings,
        "voice_review": "NOT RUN",
    }
