"""Use real eSpeak vi utterances, not sine tones or an approved narrator."""

import json
import shutil
import sys
import wave
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from voice_wav_acceptance import CUES, create_wav_set, sha256, verify_tempo


@pytest.mark.skipif(shutil.which("espeak") is None, reason="eSpeak test engine absent")
def test_twelve_vietnamese_wavs_and_stretched_timeline(tmp_path):
    source = create_wav_set(tmp_path)
    assert len(CUES) == source["cue_count"] == 12
    assert "eSpeak" in source["source"]
    assert "NOT APPROVED" in source["approval"]
    assert len(list((tmp_path / "raw-wav").glob("*.wav"))) == 12
    original_hashes = [entry["sha256"] for entry in source["raw"]]
    for entry in source["raw"]:
        with wave.open(str(tmp_path / entry["file"]), "rb") as wav:
            samples = np.frombuffer(wav.readframes(wav.getnframes()), dtype="<i2")
            assert samples.size > wav.getframerate() // 2
            assert (abs(samples.astype("i4")) > 200).mean() > 0.04
            assert np.std(samples.astype(float)) > 200
    result = verify_tempo(tmp_path)
    assert result["files"] == 12
    assert result["tempo"] == 0.92
    assert 15 < result["total_seconds"] < 60
    assert len(list((tmp_path / "audio-tempo").glob("*.wav"))) == 12
    assert [sha256(tmp_path / entry["file"]) for entry in source["raw"]] == original_hashes
    story = json.loads((tmp_path / "story.json").read_text())
    assert len(story["scenes"]) == 12
    assert all((tmp_path / scene["audio"]).is_file() for scene in story["scenes"])
