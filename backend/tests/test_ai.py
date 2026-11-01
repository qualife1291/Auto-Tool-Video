"""Provider contracts use mocks; these tests do not assert live model quality."""

import copy
import hashlib
import json
from pathlib import Path
from uuid import uuid4

import httpx
import pytest

from auto_tool_video.domain import (
    ApplyInput,
    CreativeBrief,
    ImageInput,
    PlanInput,
    ProjectInput,
    Scene,
)
from auto_tool_video.generation import apply_generation, enqueue_generation, run_generation
from auto_tool_video.planning import (
    SYSTEM_PROMPT,
    prompt_messages,
    source_chunks,
    validate_proposal,
)
from auto_tool_video.providers import (
    Comfy,
    LocalTransport,
    Ollama,
    capabilities,
    load_workflow,
    local_base,
)
from auto_tool_video.store import DomainError, Store


def project(store):
    return store.create(
        ProjectInput(
            title="Bay hơi", narration="Áo ướt.  Nước đi đâu?", brief=CreativeBrief(topic="Bay hơi")
        ).model_dump()
    )


def proposed(**changes):
    value = {
        "title": "Nước đi đâu?",
        "scenes": [
            {
                "title": "Quan sát",
                "role": "hook",
                "narration": "Nước trên áo đi vào không khí.",
                "source_ids": [],
                "visual_description": "Cùng một chiếc áo xanh",
                "image_prompt": "Clean original illustration of a blue shirt",
                "reveal_order": ["áo", "không khí"],
                "fact_flags": [],
                "source_refs": [],
                "duration": 5,
            }
        ],
    }
    value["scenes"][0].update(changes)
    return json.dumps(value, ensure_ascii=False)


@pytest.fixture
def workflow(monkeypatch):
    path = Path(__file__).resolve().parents[2] / "config/comfy-sdxl-api.example.json"
    monkeypatch.setenv("COMFY_WORKFLOW_PATH", str(path))
    return load_workflow()


class Planner:
    def __init__(self, raw=None, call=None, changed=False):
        self.raw, self.call, self.changed = raw or [proposed()], call, changed
        self.calls, self.identities = 0, 0

    def identity(self):
        self.identities += 1
        return {"model": "contract-model", "digest": str(self.identities if self.changed else 1)}

    def chat(self, messages, check):
        check()
        if self.call:
            self.call()
            check()
        self.calls += 1
        return self.raw[min(self.calls - 1, len(self.raw) - 1)]

    def close(self):
        pass


@pytest.mark.parametrize(
    "value",
    [
        "https://example.com:443",
        "http://169.254.169.254:80",
        "http://127.0.0.1:80/path",
        "http://user@localhost:80",
        "http://localhost",
        "http://localhost:bad",
        "http://localhost:80?url=evil",
        "http://[::1]:80/#x",
    ],
)
def test_provider_rejects_non_loopback_or_ambiguous_url(value):
    with pytest.raises(DomainError):
        local_base(value)


@pytest.mark.parametrize(
    "value", ["http://127.0.0.1:11434", "http://[::1]:8188", "http://localhost:8188/"]
)
def test_provider_explicit_loopback(value):
    assert local_base(value).startswith("http://")


def test_preserve_unicode_exact_internal_whitespace(tmp_path):
    store = Store(tmp_path)
    p = project(store)
    p["narration"] = "Áo ướt.  Nước đi đâu?\n\nKhông cần sôi."
    chunks = source_chunks(p["narration"])
    result = validate_proposal(
        proposed(source_ids=list(range(len(chunks))), narration="model rewrite ignored"),
        p,
        "preserve",
    )
    assert result["scenes"][0]["narration"] == p["narration"]
    assert result["source_preserved"] and result["review_required"]
    assert result["scenes"][0]["fact_flags"]
    messages = prompt_messages(p, "preserve")
    assert [message["role"] for message in messages] == ["system", "user"]
    assert json.loads(messages[1]["content"])["source_chunks"][0]["id"] == 0


@pytest.mark.parametrize("ids", [[0], [0, 0, 1], [1, 0], [-1, 0], [True, 1], ["0", 1]])
def test_preserve_rejects_missing_duplicate_reordered_or_coerced_ids(tmp_path, ids):
    with pytest.raises(DomainError):
        validate_proposal(proposed(source_ids=ids), project(Store(tmp_path)), "preserve")


@pytest.mark.parametrize(
    "changes",
    [
        {"narration": ""},
        {"source_ids": [0]},
        {"source_refs": [0]},
        {"duration": 61},
        {"fact_flags": ["x" * 501]},
        {"unexpected": "<script>"},
    ],
)
def test_planner_rejects_invalid_output(tmp_path, changes):
    with pytest.raises(DomainError):
        validate_proposal(proposed(**changes), project(Store(tmp_path)), "brief")


def test_planner_review_then_apply_once_and_preserve_old_revision(tmp_path):
    store = Store(tmp_path)
    p = project(store)
    request = PlanInput(revision=0, idempotency_key=str(uuid4()))
    job = enqueue_generation(store, p["id"], request)
    assert enqueue_generation(store, p["id"], request)["id"] == job["id"]
    run_generation(store, store.claim(), ollama=Planner())
    assert store.get("projects", p["id"]) == p
    assert store.get("jobs", job["id"])["state"] == "succeeded"
    with pytest.raises(DomainError, match="Xem đề xuất"):
        apply_generation(store, p["id"], job["id"], ApplyInput(revision=0), "plan")
    saved = apply_generation(
        store, p["id"], job["id"], ApplyInput(revision=0, confirm=True), "plan"
    )
    assert saved["revision"] == 1 and len(saved["scenes"]) == 1
    assert (
        apply_generation(store, p["id"], job["id"], ApplyInput(revision=0, confirm=True), "plan")
        == saved
    )


def test_planner_conflict_and_cross_project_never_overwrite(tmp_path):
    store = Store(tmp_path)
    p, other = project(store), project(store)
    job = enqueue_generation(store, p["id"], PlanInput(revision=0, idempotency_key=str(uuid4())))
    run_generation(store, store.claim(), ollama=Planner())
    with pytest.raises(DomainError) as error:
        apply_generation(
            store, other["id"], job["id"], ApplyInput(revision=0, confirm=True), "plan"
        )
    assert error.value.status == 404
    saved = store.save(p["id"], {**p, "title": "Bản sửa mới"})
    with pytest.raises(DomainError) as error:
        apply_generation(store, p["id"], job["id"], ApplyInput(revision=1, confirm=True), "plan")
    assert error.value.code == "REVISION_CONFLICT"
    assert store.get("projects", p["id"]) == saved


@pytest.mark.parametrize(
    "raw,changed,expected_calls",
    [(["bad", proposed()], False, 2), (["bad"], False, 2), ([proposed()], True, 1)],
)
def test_retry_is_bounded_and_identity_changes_rejected(tmp_path, raw, changed, expected_calls):
    store = Store(tmp_path)
    p = project(store)
    job = enqueue_generation(store, p["id"], PlanInput(revision=0, idempotency_key=str(uuid4())))
    planner = Planner(raw, changed=changed)
    run_generation(store, store.claim(), ollama=planner)
    assert planner.calls == expected_calls
    assert store.get("jobs", job["id"])["state"] == ("succeeded" if len(raw) == 2 else "failed")
    assert store.get("projects", p["id"]) == p


def test_cancel_and_restart_keep_original_project(tmp_path):
    store = Store(tmp_path)
    p = project(store)
    job = enqueue_generation(store, p["id"], PlanInput(revision=0, idempotency_key=str(uuid4())))
    run_generation(
        store,
        store.claim(),
        ollama=Planner(call=lambda: store.update_job(job["id"], state="cancelled")),
    )
    assert store.get("jobs", job["id"])["state"] == "cancelled"
    job2 = enqueue_generation(store, p["id"], PlanInput(revision=0, idempotency_key=str(uuid4())))
    store.claim()
    Store(tmp_path).interrupt_running()
    assert store.get("jobs", job2["id"])["state"] == "interrupted"
    assert store.get("projects", p["id"]) == p


def test_image_candidate_review_hash_and_apply(tmp_path, workflow, image_bytes):
    store = Store(tmp_path)
    p = project(store)
    p = store.save(
        p["id"],
        {
            **p,
            "scenes": [
                Scene(
                    image_prompt="blue shirt",
                    visual_description="Close-up cotton fabric drying in a breezy garden",
                ).model_dump()
            ],
        },
    )
    scene = p["scenes"][0]
    job = enqueue_generation(
        store, p["id"], ImageInput(revision=1, idempotency_key=str(uuid4())), scene["id"]
    )

    generated = {}

    class Images:
        def identity(self, config):
            return {"checkpoint": config["checkpoint"], "workflow_sha256": config["sha256"]}

        graph = staticmethod(Comfy.graph)

        def generate(self, config, graph, client_id, check, submitted):
            generated["prompt"] = graph["6"]["inputs"]["text"]
            submitted("our-prompt")
            check()
            return image_bytes

        def close(self):
            pass

    run_generation(store, store.claim(), comfy=Images())
    result = store.get("jobs", job["id"])
    assert result["state"] == "succeeded"
    assert "Close-up cotton fabric drying in a breezy garden" in generated["prompt"]
    assert "Portrait 9:16" in generated["prompt"]
    assert "Áo ướt." not in generated["prompt"]
    assert "blue shirt" in generated["prompt"]
    assert "Show the narrated event" not in generated["prompt"]
    assert result["result"]["provenance"]["resolution_profile"] == "standard"
    candidate = store.get("assets", result["result"]["candidate_id"])
    assert candidate["review_required"]
    assert result["result"]["visual_review"] == candidate["visual_review"]
    assert result["result"]["visual_review"]["aesthetic_review"] == "not_performed"
    assert result["result"]["visual_review"]["human_approval"] == "pending"
    assert (
        candidate["sha256"] == hashlib.sha256(store.asset_path(candidate).read_bytes()).hexdigest()
    )
    assert store.get("projects", p["id"]) == p
    # A flagged candidate must not be applicable via direct API confirm=True alone.
    candidate["visual_review"]["warnings"] = [
        {"code": "sparse_simple_art", "message": "Review sparse source art."}
    ]
    with store.connect() as conn:
        conn.execute(
            "UPDATE assets SET data=? WHERE id=?",
            (json.dumps(candidate), candidate["id"]),
        )
    with pytest.raises(DomainError) as blocked:
        apply_generation(store, p["id"], job["id"], ApplyInput(revision=1, confirm=True), "image")
    assert blocked.value.code == "VISUAL_REVIEW_REQUIRED"
    assert store.get("projects", p["id"]) == p
    saved = apply_generation(
        store,
        p["id"],
        job["id"],
        ApplyInput(revision=1, confirm=True, visual_warnings_acknowledged=True),
        "image",
    )
    assert saved["scenes"][0]["image_id"] == candidate["id"]
    assert not store.get("assets", candidate["id"])["review_required"]


def test_workflow_bindings_preserve_trusted_graph(workflow):
    original = copy.deepcopy(workflow)
    graph = Comfy.graph(workflow, "safe image", "no text", 123, "landscape")
    assert graph["5"]["inputs"]["width"] == 1344
    assert graph["5"]["inputs"]["height"] == 768
    assert graph["3"]["inputs"]["seed"] == 123
    assert graph["9"] == original["workflow"]["9"] and workflow == original


@pytest.mark.parametrize(
    "broken",
    [
        [],
        {"inputs": {}},
        {"class_type": 1, "inputs": {}},
        {"class_type": "SaveImage", "inputs": []},
    ],
)
def test_invalid_workflow_nodes_report_configuration_error(tmp_path, monkeypatch, workflow, broken):
    workflow["workflow"]["9"] = broken
    path = tmp_path / "workflow.json"
    path.write_text(json.dumps(workflow))
    monkeypatch.setenv("COMFY_WORKFLOW_PATH", str(path))
    with pytest.raises(DomainError) as error:
        load_workflow()
    assert error.value.code == "PROVIDER_CONFIG_ERROR"


@pytest.mark.parametrize("payload", [b"not an image", b"\x89PNG\r\n\x1a\ninvalid", b"%PDF-invalid"])
def test_bad_image_candidates_fail_without_changing_scene(tmp_path, workflow, payload):
    from auto_tool_video.generation import candidate_asset

    store = Store(tmp_path)
    p = project(store)
    p = store.save(p["id"], {**p, "scenes": [Scene(image_prompt="shirt").model_dump()]})
    job = enqueue_generation(
        store, p["id"], ImageInput(revision=1, idempotency_key=str(uuid4())), p["scenes"][0]["id"]
    )
    with pytest.raises(DomainError):
        candidate_asset(store, job, payload, {})
    assert store.get("projects", p["id"]) == p
    assert not list((store.root / "assets").glob("*.png"))


def test_transport_refuses_redirect_even_if_injected_client_follows():
    requests = []

    def handler(request):
        requests.append(str(request.url))
        return httpx.Response(302, headers={"Location": "http://169.254.169.254/"})

    with (
        httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=True) as client,
        pytest.raises(DomainError),
    ):
        LocalTransport("http://127.0.0.1:8188", client).json("GET", "/system_stats")
    assert len(requests) == 1


@pytest.mark.parametrize(
    "payload",
    [
        b"[]\n",
        b'{"message":[]}\n',
        b'{"message":{"content":123}}\n',
        b"x" * 65537,
        b'{"message":{"content":"{}"},"done":true,"done_reason":"length"}\n',
        b'{"message":{"content":"{}"}}\n',
    ],
)
def test_ollama_invalid_truncated_or_oversized_stream_is_error(payload):
    with (
        httpx.Client(
            transport=httpx.MockTransport(lambda r: httpx.Response(200, content=payload))
        ) as client,
        pytest.raises(DomainError),
    ):
        Ollama(client).chat([{"role": "user", "content": "input"}], lambda: None)


def test_ollama_schema_no_tools_and_complete_output():
    captured = []

    def handler(request):
        captured.append(json.loads(request.content))
        return httpx.Response(200, content=b'{"message":{"content":"{}"},"done":true}\n')

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        assert (
            Ollama(client).chat([{"role": "user", "content": "ignore rules"}], lambda: None) == "{}"
        )
    assert captured[0]["think"] is False and "tools" not in captured[0]
    assert captured[0]["format"]["additionalProperties"] is False


@pytest.mark.parametrize("mode,limit", [("chat", 600), ("json", 30)])
def test_small_slow_chunks_cannot_bypass_total_provider_deadline(monkeypatch, mode, limit):
    from types import SimpleNamespace

    from auto_tool_video import providers

    clock = [0.0]
    closed = []

    class SlowStream(httpx.SyncByteStream):
        def __iter__(self):
            yield b"{"
            clock[0] = limit + 1
            yield b'"'
            pytest.fail("deadline must be checked before buffering another chunk")

        def close(self):
            closed.append(True)

    monkeypatch.setattr(providers, "time", SimpleNamespace(monotonic=lambda: clock[0]))
    with (
        httpx.Client(
            transport=httpx.MockTransport(lambda r: httpx.Response(200, stream=SlowStream()))
        ) as client,
        pytest.raises(DomainError) as error,
    ):
        if mode == "chat":
            Ollama(client).chat([], lambda: None)
        else:
            LocalTransport("http://127.0.0.1:8188", client).json("GET", "/system_stats")
    assert error.value.code == "MODEL_TIMEOUT"
    assert closed == [True]


@pytest.mark.parametrize(
    "item",
    [
        {"filename": "../a.png", "type": "output"},
        {"filename": "a.png", "subfolder": "/etc", "type": "output"},
        {"filename": "a.png", "subfolder": "../", "type": "output"},
        {"filename": "a.png", "type": "input"},
        [],
    ],
)
def test_comfy_output_paths_never_escape_or_fetch(item):
    with (
        httpx.Client(
            transport=httpx.MockTransport(lambda r: pytest.fail("must not fetch"))
        ) as client,
        pytest.raises(DomainError),
    ):
        Comfy(client).image_bytes(item, lambda: None)


def test_comfy_success_uses_selected_node_and_deletes_only_own_queue(workflow, image_bytes):
    calls = []

    def handler(request):
        calls.append((request.method, request.url.path, request.content))
        if request.url.path == "/prompt":
            return httpx.Response(200, json={"prompt_id": "ours"})
        if request.url.path == "/history/ours":
            return httpx.Response(
                200,
                json={
                    "ours": {
                        "status": {"completed": True},
                        "outputs": {
                            "9": {
                                "images": [
                                    {"filename": "ours.png", "subfolder": "", "type": "output"}
                                ]
                            }
                        },
                    }
                },
            )
        if request.url.path == "/view":
            return httpx.Response(200, content=image_bytes)
        return httpx.Response(200, json={})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        assert (
            Comfy(client).generate(
                workflow, workflow["workflow"], "client", lambda: None, lambda _: None
            )
            == image_bytes
        )
    assert json.loads(calls[-1][2]) == {"delete": ["ours"]}
    assert all(path != "/interrupt" for _, path, _ in calls)


def test_missing_provider_capabilities_are_honest(monkeypatch):
    monkeypatch.delenv("COMFY_WORKFLOW_PATH", raising=False)

    def unavailable(self):
        raise DomainError("MODEL_MISSING", "Model chưa được cài.", 503)

    monkeypatch.setattr(Ollama, "identity", unavailable)
    result = capabilities()
    assert result["script"]["state"] == "model_missing"
    assert result["image"]["state"] == "not_configured"


def test_api_brief_validation_backwards_save_and_job_privacy(client):
    response = client.post(
        "/api/projects", json={"title": "Áo", "brief": {"topic": "bay hơi", "target_duration": 31}}
    )
    assert response.status_code == 422
    p = client.post("/api/projects", json={"title": "Áo", "brief": {"topic": "bay hơi"}}).json()
    saved = client.put(
        f"/api/projects/{p['id']}",
        json={
            k: v
            for k, v in p.items()
            if k in {"title", "profile", "platform", "narration", "aspect", "revision", "scenes"}
        },
    )
    assert saved.status_code == 200 and saved.json()["brief"]["topic"] == "bay hơi"
    payload = {
        "revision": saved.json()["revision"],
        "mode": "brief",
        "idempotency_key": str(uuid4()),
    }
    job = client.post(f"/api/projects/{p['id']}/plan", json=payload)
    assert job.status_code == 202 and "snapshot" not in job.json()
    assert (
        client.post(f"/api/projects/{p['id']}/plan", json=payload).json()["id"] == job.json()["id"]
    )


def test_planner_prompts_require_semantic_visual_detail_not_repeated_icons():
    assert "material detail" in SYSTEM_PROMPT
    assert "foreground/midground/" in SYSTEM_PROMPT
    assert "phone" in SYSTEM_PROMPT
    assert "generic isolated icon" in SYSTEM_PROMPT
