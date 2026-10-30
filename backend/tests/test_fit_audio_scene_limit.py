"""C04 P1-B RED regression: Fit Audio must not persist a >20-second scene.

Real imported mono PCM WAV and API/store paths. Synthetic silence is test data only;
it does not certify narration quality or creator audiovisual acceptance.
"""

from __future__ import annotations

import copy
import io
import wave

from conftest import attach, create_story


def _wav(seconds: float) -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(48000)
        output.writeframes(b"\x00\x00" * round(48000 * seconds))
    return buffer.getvalue()


def test_fit_audio_never_persists_scene_over_20_seconds(client):
    """Actual old-code RED: valid 19.65s WAV plus 1s pause exceeds 20s."""
    project = create_story(client, "Áo ướt khô nhờ nước bay hơi.")
    project = attach(client, project, project["scenes"][0], _wav(19.65), "voice.wav")
    audio_id = project["scenes"][0]["audio_id"]
    store = client.app.state.store
    asset_before = copy.deepcopy(store.get("assets", audio_id))
    before = copy.deepcopy(project)

    response = client.post(
        f"/api/projects/{project['id']}/fit-audio",
        json={"revision": project["revision"], "pause_after": 1.0},
    )

    assert response.status_code == 400, response.text
    assert response.json()["code"] == "DURATION_LIMIT"
    assert client.get(f"/api/projects/{project['id']}").json() == before
    assert store.get("assets", audio_id) == asset_before
    assert store.asset_path(asset_before).is_file()
