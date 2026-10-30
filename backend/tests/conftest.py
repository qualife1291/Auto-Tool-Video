import io
import math
import struct
import wave

import pytest
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

from auto_tool_video.api import create_app


@pytest.fixture
def client(tmp_path):
    app = create_app(tmp_path)
    with TestClient(
        app, base_url="http://localhost", headers={"X-Studio-Client": "local"}
    ) as client:
        yield client


@pytest.fixture
def image_bytes():
    image = Image.new("RGB", (1000, 800), "white")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(
        (160, 180, 840, 600), radius=50, fill="#d8eab4", outline="#254d3d", width=12
    )
    draw.ellipse((420, 50, 580, 210), fill="#e8b587", outline="#202922", width=6)
    stream = io.BytesIO()
    image.save(stream, "PNG")
    return stream.getvalue()


@pytest.fixture
def audio_bytes():
    stream = io.BytesIO()
    with wave.open(stream, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(48000)
        samples = [
            struct.pack("<h", round(3000 * math.sin(i / 48000 * math.tau * 220)))
            for i in range(24000)
        ]
        audio.writeframes(b"".join(samples))
    return stream.getvalue()


def create_story(client, lines="Nước đi vào không khí.\nBay hơi không cần sôi.\nChọn nơi thoáng."):
    response = client.post("/api/projects", json={"title": "Nước đi đâu?", "narration": lines})
    assert response.status_code == 201
    project = response.json()
    split = client.post(f"/api/projects/{project['id']}/split", json={"revision": 0})
    assert split.status_code == 200
    return split.json()


def attach(client, project, scene, content, name="ảnh.png"):
    result = client.post(
        f"/api/projects/{project['id']}/scenes/{scene['id']}/assets",
        data={"revision": project["revision"]},
        files={"file": (name, content)},
    )
    assert result.status_code == 200, result.text
    return result.json()


def save(client, project):
    payload = {
        key: project[key]
        for key in ("title", "profile", "platform", "narration", "aspect", "revision", "scenes")
    }
    if "brief" in project:
        payload["brief"] = project["brief"]
    return client.put(f"/api/projects/{project['id']}", json=payload)
