import json
import wave
from uuid import uuid4

import numpy as np
import pytest
from conftest import attach, create_story, save
from PIL import Image

from auto_tool_video.domain import ExportInput, Scene
from auto_tool_video.jobs import enqueue
from auto_tool_video.layout import boxes, fitted_image, image_transform
from auto_tool_video.render import ScenePainter, narration_track, render_job, transition_visual
from auto_tool_video.timing import frames_for, scene_timeline, silence_report


def test_cover_fills_edges_without_distortion_and_focal_controls_the_crop():
    source = Image.new("RGB", (300, 100), "red")
    source.paste("blue", (150, 0, 300, 100))
    left = fitted_image(source, (100, 200), "cover", (0, 0.5))
    right = fitted_image(source, (100, 200), "cover", (1, 0.5))
    assert left.getpixel((0, 100)) == (255, 0, 0)
    assert right.getpixel((99, 100)) == (0, 0, 255)
    matrix = image_transform(source.size, (100, 200), "cover", (0.5, 0.5))
    assert matrix[0] == matrix[4] == 0.5
    contain = fitted_image(source, (100, 200), "contain", (0.5, 0.5))
    assert contain.getpixel((0, 0)) == (255, 248, 235)


def test_subpixel_motion_changes_continuously_before_any_integer_resize_step():
    a = image_transform((1600, 1400), (1080, 1920), "cover", (0.5, 0.5), 1.00001)
    b = image_transform((1600, 1400), (1080, 1920), "cover", (0.5, 0.5), 1.00002)
    assert 0 < abs(a[0] - b[0]) < 0.001
    assert a[2] != b[2]


@pytest.mark.parametrize("size", [(360, 640), (640, 360)])
def test_full_frame_is_edge_to_edge_and_title_is_drawn_after_visual(tmp_path, size):
    path = tmp_path / "source.png"
    Image.new("RGB", (400, 400), "#55ADBE").save(path)
    scene = Scene(title="Nước đã đi đâu?", narration="Bay hơi.", style="motion").model_dump()
    painter = ScenePainter(path, scene, *size, True)
    try:
        raw = painter.frame(0.4, overlays=False)
        composed = raw.copy()
        painter.draw_overlays(composed, 0.4)
        assert raw.getpixel((0, 0)) == (85, 173, 190)
        assert raw.getpixel((size[0] - 1, size[1] - 1)) == (85, 173, 190)
        assert np.any(np.asarray(raw) != np.asarray(composed))
        assert boxes(*size, "full_frame")["image"] == (0, 0, *size)
    finally:
        painter.close()


def test_pen_lift_does_not_draw_a_false_line_between_disconnected_strokes(tmp_path):
    path = tmp_path / "source.png"
    Image.new("RGB", (400, 400), "white").save(path)
    painter = ScenePainter(
        path, {"title": "Nét vẽ", "narration": "", "duration": 2}, 360, 640, False
    )
    try:
        painter.segments = [
            ((10, 20), (30, 20), 20, True),
            ((30, 20), (100, 20), 44.5, False),
            ((100, 20), (120, 20), 64.5, True),
        ]
        painter.total_length = 64.5
        painter.cursor = 0
        painter.mask = Image.new("L", painter.image.size, 0)
        _, pen = painter.visual_frame(0.65 * 32 / 64.5)
        assert not painter.pen_down and 30 < pen[0] < 100
        assert painter.mask.getpixel((20, 20)) == 255
        assert painter.mask.getpixel((60, 20)) == 0
    finally:
        painter.close()


def test_dissolve_blends_visuals_only_and_does_not_modify_the_input():
    first, second = Image.new("RGB", (100, 100), "blue"), Image.new("RGB", (100, 100), "red")
    mixed = transition_visual(first, second, 0, 90, True)
    assert mixed.getpixel((40, 40)) == (51, 0, 204)
    assert second.getpixel((40, 40)) == (255, 0, 0)
    assert transition_visual(first, second, 5, 90, True) is second
    assert transition_visual(first, second, 0, 90, False) is second


def test_real_clip_frame_clock_does_not_skip_a_frame_mid_scene(tmp_path):
    class Capture:
        def __init__(self):
            self.index = 0

        def read(self):
            self.index += 1
            return True, np.full((20, 20, 3), self.index, dtype=np.uint8)

        def release(self):
            pass

    path = tmp_path / "source.png"
    Image.new("RGB", (20, 20), "white").save(path)
    scene = {"title": "Clock", "narration": "", "duration": 1, "style": "motion"}
    painter = ScenePainter(path, scene, 360, 640, False)
    capture = Capture()
    painter.capture = capture
    painter.clip_index = 0
    painter.clip_fps = 30
    try:
        for i in range(30):
            painter.frame(i / 29)
            assert painter.clip_index == i
    finally:
        painter.close()


def test_frame_grid_and_variable_timeline_are_sample_exact():
    assert frames_for(3.166667) == 95
    result = scene_timeline([{"duration": 3.166667}, {"duration": 2.5}, {"duration": 1.2}])
    assert result[1]["start"] == 95 / 30
    assert result[2]["start"] == 170 / 30


def test_pacing_measures_long_silence_including_end_of_file_and_silent_is_explicit():
    log = "silence_start: 1.1\nsilence_end: 2.1 | silence_duration: 1\nsilence_start: 3.5"
    measured = silence_report(log, 4)
    assert measured["silence_seconds"] == pytest.approx(1.5)
    assert measured["longest_interval_seconds"] == pytest.approx(1)
    assert silence_report(log, 4, True)["status"] == "not_applicable"


@pytest.mark.parametrize("silent", [False, True])
def test_export_qc_reports_long_narration_gaps_but_respects_intentional_silence(
    client, image_bytes, audio_bytes, silent
):
    project = create_story(client, "Có lời đọc ngắn và một khoảng giữ hình quá dài.")
    project = attach(client, project, project["scenes"][0], image_bytes)
    project = attach(client, project, project["scenes"][0], audio_bytes, "voice.wav")
    project["scenes"][0]["duration"] = 2
    project = save(client, project).json()
    store = client.app.state.store
    job = enqueue(
        store,
        project["id"],
        ExportInput(
            revision=project["revision"],
            kind="preview",
            silent=silent,
            idempotency_key=str(uuid4()),
        ),
    )
    render_job(store, store.claim())
    qc = store.get("jobs", job["id"])["quality_report"]
    assert qc["technical"]["status"] == "passed"
    gaps = [f for f in qc["signals"]["findings"] if f["kind"] == "long_silence"]
    if silent:
        assert qc["pacing"]["status"] == "not_applicable" and not gaps
    else:
        assert qc["pacing"]["longest_interval_seconds"] >= 1.4
        assert gaps and 0.4 < gaps[0]["timestamp"] < 0.6
    assert qc["gate"]["status"] == "pending_review"


def test_audio_pcm_has_no_aac_padding_at_scene_boundaries(
    client, image_bytes, audio_bytes, tmp_path
):
    project = create_story(client, "Cảnh một.\nCảnh hai.")
    for scene in project["scenes"]:
        project = attach(client, project, scene, audio_bytes, "voice.wav")
    for scene in project["scenes"]:
        scene["duration"] = 1
    project = save(client, project).json()
    output = tmp_path / "narration.wav"
    count = narration_track(
        client.app.state.store, {"snapshot": project, "options": {"silent": False}}, output
    )
    with wave.open(str(output), "rb") as stream:
        assert stream.getframerate() == 48000 and stream.getnframes() == count == 96000


def test_fit_audio_shortens_holds_without_cutting_voice_and_rejects_stale(client, audio_bytes):
    project = create_story(client, "Nước không biến mất.")
    project = attach(client, project, project["scenes"][0], audio_bytes, "voice.wav")
    project["scenes"][0]["duration"] = 8
    project = save(client, project).json()
    path = f"/api/projects/{project['id']}/fit-audio"
    fitted = client.post(path, json={"revision": project["revision"], "pause_after": 0.12})
    assert fitted.status_code == 200 and fitted.json()["scenes"][0]["duration"] == 1
    assert client.post(path, json={"revision": project["revision"]}).status_code == 409
    project = fitted.json()
    project["scenes"][0]["narration"] = "Lời mới."
    project = save(client, project).json()
    assert client.post(path, json={"revision": project["revision"]}).status_code == 400


def test_legacy_save_preserves_board_fit_and_transition_when_fields_are_missing(client):
    project = create_story(client)
    store = client.app.state.store
    with store.connect() as conn:
        for scene in project["scenes"]:
            for key in [
                "layout",
                "visual_fit",
                "focal_x",
                "focal_y",
                "transition",
                "draw_fraction",
            ]:
                scene.pop(key)
        conn.execute("UPDATE projects SET data=? WHERE id=?", (json.dumps(project), project["id"]))
    response = save(client, project)
    assert response.status_code == 200
    scene = response.json()["scenes"][0]
    assert (scene["layout"], scene["visual_fit"], scene["transition"]) == (
        "board",
        "contain",
        "cut",
    )


@pytest.mark.parametrize(
    "patch",
    [
        {"focal_x": -1},
        {"focal_y": "NaN"},
        {"draw_fraction": 1},
        {"visual_fit": "stretch"},
        {"layout": "html"},
    ],
)
def test_invalid_composition_fields_are_rejected(client, patch):
    project = create_story(client)
    project["scenes"][0].update(patch)
    assert save(client, project).status_code == 422


def test_new_split_and_ai_scenes_default_to_noncropping_fit():
    from auto_tool_video.domain import Scene, split_script

    # Newly authored scenes should never lose half the subject in a portrait
    # output just because a user imports a landscape photo or diagram.
    assert split_script("Vì sao nước bay hơi?")[0].visual_fit == "contain"
    # Legacy persisted snapshots continue to deserialize their old default.
    assert Scene(title="Cũ", narration="Giữ nguyên").visual_fit == "cover"
    # Explicit creator intent takes precedence, including old snapshots.
    assert Scene(title="Đã chọn", visual_fit="cover").visual_fit == "cover"
