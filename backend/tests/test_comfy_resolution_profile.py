"""Optional higher-resolution ComfyUI generation must be explicit and bounded.

Tests cover trusted local graph config only; no live checkpoint/VRAM claim.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from auto_tool_video.providers import Comfy, load_workflow
from auto_tool_video.store import DomainError


@pytest.fixture
def config(monkeypatch):
    root = Path(__file__).resolve().parents[2]
    monkeypatch.setenv("COMFY_WORKFLOW_PATH", str(root / "config/comfy-sdxl-api.example.json"))
    return load_workflow()


def test_default_model_generation_preserves_existing_resolution(config):
    source = copy.deepcopy(config)
    portrait = Comfy.graph(config, "safe", "no text", 9, "portrait")
    landscape = Comfy.graph(config, "safe", "no text", 9, "landscape")
    assert (portrait["5"]["inputs"]["width"], portrait["5"]["inputs"]["height"]) == (768, 1344)
    assert (landscape["5"]["inputs"]["width"], landscape["5"]["inputs"]["height"]) == (1344, 768)
    assert config == source


def test_trusted_high_detail_profile_requests_more_source_pixels(config):
    source = copy.deepcopy(config)
    config["resolution_profile"] = "high_detail"
    portrait = Comfy.graph(config, "safe", "no text", 9, "portrait")
    landscape = Comfy.graph(config, "safe", "no text", 9, "landscape")
    assert (portrait["5"]["inputs"]["width"], portrait["5"]["inputs"]["height"]) == (1024, 1792)
    assert (landscape["5"]["inputs"]["width"], landscape["5"]["inputs"]["height"]) == (1792, 1024)
    assert portrait["3"]["inputs"]["seed"] == 9
    assert portrait["9"] == source["workflow"]["9"]
    assert config["workflow"] == source["workflow"]


@pytest.mark.parametrize("profile", ["huge", "", "1024x1792", None, 5, {}, []])
def test_unknown_or_unbounded_resolution_profile_fails_closed(
    tmp_path, monkeypatch, config, profile
):
    config["resolution_profile"] = profile
    path = tmp_path / "test-workflow.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    monkeypatch.setenv("COMFY_WORKFLOW_PATH", str(path))
    with pytest.raises(DomainError) as error:
        load_workflow()
    assert error.value.code == "PROVIDER_CONFIG_ERROR"


def test_high_detail_config_is_loaded_from_trusted_local_workflow(tmp_path, monkeypatch, config):
    config["resolution_profile"] = "high_detail"
    path = tmp_path / "test-workflow.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    monkeypatch.setenv("COMFY_WORKFLOW_PATH", str(path))
    loaded = load_workflow()
    assert loaded["resolution_profile"] == "high_detail"
    assert loaded["sha256"]
