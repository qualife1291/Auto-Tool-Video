"""Local-only AI transports. Provider addresses and graphs never come from model/user input."""

from __future__ import annotations

import copy
import hashlib
import ipaddress
import json
import os
import time
from collections.abc import Callable
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import urlsplit

import httpx

from .media import MAX_UPLOAD
from .planning import Proposal
from .store import DomainError

Check = Callable[[], None]


def local_base(value: str) -> str:
    try:
        url = urlsplit(value)
        valid_host = (
            url.hostname == "localhost" or ipaddress.ip_address(url.hostname or "").is_loopback
        )
        port = url.port
    except ValueError:
        raise DomainError(
            "PROVIDER_CONFIG_ERROR", "Địa chỉ provider local không hợp lệ.", 503
        ) from None
    if (
        not valid_host
        or url.scheme != "http"
        or url.username
        or url.password
        or url.path not in {"", "/"}
        or url.query
        or url.fragment
        or not port
    ):
        raise DomainError(
            "PROVIDER_CONFIG_ERROR",
            "Provider phải là HTTP loopback với cổng rõ ràng, không user/password/path.",
            503,
        )
    return value.rstrip("/")


class LocalTransport:
    def __init__(self, base: str, client: httpx.Client | None = None):
        self.base = local_base(base)
        # This transport can only reach validated loopback. Private scripts never go to egress proxies.
        self.client = client or httpx.Client(
            trust_env=False, follow_redirects=False, timeout=httpx.Timeout(30, connect=3)
        )
        self.owns_client = client is None

    def close(self) -> None:
        if self.owns_client:
            self.client.close()

    def json(self, method: str, path: str, payload: dict | None = None) -> Any:
        started = time.monotonic()
        try:
            with self.client.stream(
                method, self.base + path, json=payload, follow_redirects=False
            ) as response:
                if not response.is_success:
                    raise DomainError(
                        "MODEL_UNAVAILABLE", "Dịch vụ local từ chối yêu cầu hoặc đổi địa chỉ.", 503
                    )
                content = bytearray()
                for chunk in response.iter_bytes():
                    if time.monotonic() - started > 30:
                        raise DomainError("MODEL_TIMEOUT", "Dịch vụ local phản hồi quá lâu.", 504)
                    content.extend(chunk)
                    if len(content) > 2 * 1024 * 1024:
                        raise DomainError("MODEL_OUTPUT_INVALID", "Phản hồi provider quá lớn.", 502)
                return json.loads(content)
        except (httpx.HTTPError, ValueError):
            raise DomainError(
                "MODEL_UNAVAILABLE",
                "Không liên lạc được dịch vụ AI local hoặc phản hồi không hợp lệ.",
                503,
            ) from None


class Ollama(LocalTransport):
    def __init__(self, client: httpx.Client | None = None):
        super().__init__(os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434"), client)
        self.model = os.environ.get("OLLAMA_MODEL", "qwen3:8b")

    def identity(self) -> dict[str, str]:
        tags = self.json("GET", "/api/tags")
        if not isinstance(tags, dict) or not isinstance(tags.get("models"), list):
            raise DomainError("MODEL_OUTPUT_INVALID", "Danh sách model local không hợp lệ.", 502)
        for model in tags.get("models", []):
            if (
                isinstance(model, dict)
                and model.get("name") == self.model
                and isinstance(model.get("digest"), str)
                and model["digest"]
            ):
                return {"model": self.model, "digest": model["digest"]}
        raise DomainError(
            "MODEL_MISSING",
            "Ollama đang chạy nhưng chưa có model đã cấu hình. Cài model trước khi lập kế hoạch.",
            503,
        )

    def chat(self, messages: list[dict[str, str]], check: Check) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "format": Proposal.model_json_schema(),
            "stream": True,
            "think": False,
            "keep_alive": "10m",
            "options": {"temperature": 0.25, "num_predict": 4000, "num_ctx": 8192, "num_thread": 4},
        }
        content = ""
        started = time.monotonic()
        done = False
        try:
            with self.client.stream(
                "POST", self.base + "/api/chat", json=payload, follow_redirects=False
            ) as response:
                if not response.is_success:
                    raise DomainError("MODEL_UNAVAILABLE", "Ollama từ chối lập kế hoạch.", 503)
                pending = bytearray()

                def lines():
                    # Observe every received chunk; fixed-size buffering can hide slow trickles.
                    for chunk in response.iter_bytes():
                        check()
                        pending.extend(chunk)
                        if time.monotonic() - started > 600:
                            raise DomainError(
                                "MODEL_TIMEOUT", "Planner vượt giới hạn thời gian.", 504
                            )
                        while b"\n" in pending:
                            line, _, rest = pending.partition(b"\n")
                            if len(line) > 65536:
                                raise DomainError(
                                    "MODEL_OUTPUT_INVALID", "Dòng phản hồi quá lớn.", 502
                                )
                            pending[:] = rest
                            yield line
                        if len(pending) > 65536:
                            raise DomainError("MODEL_OUTPUT_INVALID", "Dòng phản hồi quá lớn.", 502)
                    if pending:
                        yield bytes(pending)

                for line in lines():
                    check()
                    if time.monotonic() - started > 600 or len(line) > 65536:
                        raise DomainError(
                            "MODEL_TIMEOUT", "Planner vượt giới hạn thời gian hoặc dữ liệu.", 504
                        )
                    if not line:
                        continue
                    data = json.loads(line)
                    if not isinstance(data, dict) or not isinstance(data.get("message", {}), dict):
                        raise TypeError("response")
                    if data.get("error"):
                        raise DomainError(
                            "MODEL_UNAVAILABLE", "Ollama không thể hoàn tất yêu cầu.", 503
                        )
                    part = data.get("message", {}).get("content", "")
                    if not isinstance(part, str):
                        raise TypeError("content")
                    content += part
                    if len(content) > 120000:
                        raise DomainError(
                            "MODEL_OUTPUT_INVALID", "Kịch bản model vượt giới hạn dữ liệu.", 502
                        )
                    if data.get("done"):
                        done = True
                        if data.get("done_reason") == "length":
                            raise DomainError(
                                "MODEL_OUTPUT_INVALID",
                                "Model hết token trước khi hoàn tất; thử brief ngắn hơn.",
                                502,
                            )
                        break
        except (httpx.HTTPError, ValueError, TypeError):
            raise DomainError(
                "MODEL_UNAVAILABLE",
                "Kết nối planner bị gián đoạn. Dữ liệu đã lưu vẫn được giữ.",
                503,
            ) from None
        if not done:
            raise DomainError("MODEL_OUTPUT_INVALID", "Planner chưa trả kết quả hoàn chỉnh.", 502)
        return content


# Intentional, low-risk choice: no arbitrary model-provided canvas sizes.
# High-detail is opt-in via a trusted local workflow config and uses more VRAM.
COMFY_RESOLUTION_PROFILES: dict[str, dict[str, tuple[int, int]]] = {
    "standard": {"portrait": (768, 1344), "landscape": (1344, 768)},
    "high_detail": {"portrait": (1024, 1792), "landscape": (1792, 1024)},
}


def load_workflow() -> dict[str, Any]:
    path = os.environ.get("COMFY_WORKFLOW_PATH")
    if not path:
        raise DomainError(
            "PROVIDER_NOT_CONFIGURED",
            "Chưa cấu hình workflow ComfyUI. Có thể tiếp tục nhập ảnh thủ công.",
            503,
        )
    try:
        file = Path(path)
        if file.stat().st_size > 1024 * 1024:
            raise ValueError("size")
        value = json.loads(file.read_text())
        graph, bindings = value["workflow"], value["bindings"]
        if (
            not isinstance(graph, dict)
            or not 1 <= len(graph) <= 200
            or str(value["output_node"]) not in graph
        ):
            raise ValueError("graph")
        if any(
            not isinstance(node, dict)
            or not isinstance(node.get("class_type"), str)
            or not node["class_type"]
            or not isinstance(node.get("inputs"), dict)
            for node in graph.values()
        ):
            raise ValueError("node")
        for field in ("positive", "negative", "seed", "width", "height", "checkpoint"):
            node, input_name = bindings[field]
            if (
                not isinstance(node, str)
                or not isinstance(input_name, str)
                or input_name not in graph[node]["inputs"]
            ):
                raise ValueError("binding")
        if not isinstance(value.get("checkpoint"), str) or not value["checkpoint"].strip():
            raise ValueError("checkpoint")
        profile = value.get("resolution_profile", "standard")
        if not isinstance(profile, str) or profile not in COMFY_RESOLUTION_PROFILES:
            raise ValueError("resolution_profile")
        value["sha256"] = hashlib.sha256(file.read_bytes()).hexdigest()
        return value
    except (OSError, ValueError, KeyError, TypeError):
        raise DomainError(
            "PROVIDER_CONFIG_ERROR",
            "Workflow ComfyUI không hợp lệ; quản trị cần kiểm graph và bindings.",
            503,
        ) from None


class Comfy(LocalTransport):
    def __init__(self, client: httpx.Client | None = None):
        super().__init__(os.environ.get("IMAGE_PROVIDER_URL", "http://127.0.0.1:8188"), client)

    def identity(self, config: dict[str, Any]) -> dict[str, str]:
        self.json("GET", "/system_stats")
        node_id, input_name = config["bindings"]["checkpoint"]
        node_type = config["workflow"][node_id]["class_type"]
        if not isinstance(node_type, str) or not node_type.replace("_", "").isalnum():
            raise DomainError("PROVIDER_CONFIG_ERROR", "Loại node checkpoint không hợp lệ.", 503)
        nodes = self.json("GET", "/object_info/" + node_type)
        try:
            available = nodes[node_type]["input"]["required"][input_name][0]
            if not isinstance(available, list) or config["checkpoint"] not in available:
                raise KeyError("checkpoint")
        except (KeyError, IndexError, TypeError):
            raise DomainError(
                "MODEL_MISSING", "Checkpoint trong workflow chưa có trong ComfyUI.", 503
            ) from None
        return {"checkpoint": config["checkpoint"], "workflow_sha256": config["sha256"]}

    @staticmethod
    def graph(config: dict[str, Any], prompt: str, negative: str, seed: int, aspect: str) -> dict:
        graph = copy.deepcopy(config["workflow"])
        # Trusted local config controls a bounded source resolution, not user/model text.
        profile = config.get("resolution_profile", "standard")
        if (
            not isinstance(profile, str)
            or profile not in COMFY_RESOLUTION_PROFILES
            or aspect not in {"portrait", "landscape"}
        ):
            raise DomainError(
                "PROVIDER_CONFIG_ERROR", "Hồ sơ độ phân giải ComfyUI không hợp lệ.", 503
            )
        width, height = COMFY_RESOLUTION_PROFILES[profile][aspect]
        values = {
            "positive": prompt,
            "negative": negative,
            "seed": seed,
            "width": width,
            "height": height,
            "checkpoint": config["checkpoint"],
        }
        for field, value in values.items():
            node, name = config["bindings"][field]
            graph[node]["inputs"][name] = value
        return graph

    def generate(
        self,
        config: dict[str, Any],
        graph: dict,
        client_id: str,
        check: Check,
        submitted: Callable[[str], None],
    ) -> bytes:
        response = self.json("POST", "/prompt", {"prompt": graph, "client_id": client_id})
        prompt_id = response.get("prompt_id") if isinstance(response, dict) else None
        if (
            not isinstance(prompt_id, str)
            or not prompt_id
            or len(prompt_id) > 128
            or not all(c.isalnum() or c in "-_" for c in prompt_id)
        ):
            raise DomainError("MODEL_OUTPUT_INVALID", "ComfyUI không trả mã tác vụ hợp lệ.", 502)
        try:
            submitted(prompt_id)
            deadline = time.monotonic() + 900
            while time.monotonic() < deadline:
                check()
                history = self.json("GET", "/history/" + prompt_id)
                if not isinstance(history, dict):
                    raise DomainError("MODEL_OUTPUT_INVALID", "History ComfyUI không hợp lệ.", 502)
                result = history.get(prompt_id)
                if result:
                    if (
                        not isinstance(result, dict)
                        or not isinstance(result.get("status", {}), dict)
                        or not isinstance(result.get("outputs", {}), dict)
                    ):
                        raise DomainError(
                            "MODEL_OUTPUT_INVALID", "Kết quả ComfyUI không hợp lệ.", 502
                        )
                    status = result.get("status", {})
                    if status.get("status_str") == "error":
                        raise DomainError(
                            "MODEL_UNAVAILABLE",
                            "ComfyUI không dựng được ảnh. Kiểm workflow/VRAM local.",
                            502,
                        )
                    output = result.get("outputs", {}).get(str(config["output_node"]), {})
                    if not isinstance(output, dict) or not isinstance(
                        output.get("images", []), list
                    ):
                        raise DomainError(
                            "MODEL_OUTPUT_INVALID", "Output ComfyUI không hợp lệ.", 502
                        )
                    images = output.get("images", [])
                    if images:
                        return self.image_bytes(images[0], check)
                    if status.get("completed"):
                        raise DomainError(
                            "MODEL_OUTPUT_INVALID",
                            "Workflow kết thúc nhưng không có ảnh ở output đã chọn.",
                            502,
                        )
                time.sleep(0.5)
            raise DomainError(
                "MODEL_TIMEOUT", "ComfyUI chưa xong trong 15 phút; ảnh cũ vẫn được giữ.", 504
            )
        finally:
            # Only delete our queued prompt. Never interrupt a shared ComfyUI instance globally.
            try:
                self.json("POST", "/queue", {"delete": [prompt_id]})
            except DomainError:
                pass  # Best effort cleanup; local cancellation still prevents applying late outputs.

    def image_bytes(self, item: dict, check: Check) -> bytes:
        if not isinstance(item, dict):
            raise DomainError("MODEL_OUTPUT_INVALID", "Metadata ảnh không hợp lệ.", 502)
        filename, folder = item.get("filename", ""), item.get("subfolder", "")
        if (
            not isinstance(filename, str)
            or not filename
            or len(filename) > 250
            or "/" in filename
            or "\\" in filename
            or ".." in filename
            or not isinstance(folder, str)
            or len(folder) > 500
            or "\\" in folder
            or PurePosixPath(folder).is_absolute()
            or ".." in PurePosixPath(folder).parts
            or item.get("type") != "output"
        ):
            raise DomainError(
                "MODEL_OUTPUT_INVALID", "Provider trả đường dẫn ảnh không an toàn.", 502
            )
        try:
            with self.client.stream(
                "GET",
                self.base + "/view",
                params={"filename": filename, "subfolder": folder, "type": "output"},
                follow_redirects=False,
            ) as response:
                if not response.is_success:
                    raise DomainError(
                        "MODEL_UNAVAILABLE", "Không lấy được ảnh từ ComfyUI local.", 502
                    )
                data = bytearray()
                for chunk in response.iter_bytes():
                    check()
                    data.extend(chunk)
                    if len(data) > MAX_UPLOAD:
                        raise DomainError("MODEL_OUTPUT_INVALID", "Ảnh model vượt 20 MiB.", 502)
                return bytes(data)
        except httpx.HTTPError:
            raise DomainError("MODEL_UNAVAILABLE", "Tải ảnh local bị gián đoạn.", 503) from None


def capabilities() -> dict:
    result = {}
    for name, factory in (("script", Ollama), ("image", Comfy)):
        provider = None
        try:
            provider = factory()
            identity = (
                provider.identity(load_workflow())
                if isinstance(provider, Comfy)
                else provider.identity()
            )
            result[name] = {
                "state": "ready",
                "message": "Dịch vụ và model local sẵn sàng.",
                **identity,
            }
        except DomainError as error:
            state = {
                "PROVIDER_NOT_CONFIGURED": "not_configured",
                "PROVIDER_CONFIG_ERROR": "config_error",
                "MODEL_MISSING": "model_missing",
            }.get(error.code, "unreachable")
            result[name] = {"state": state, "message": error.message}
        finally:
            if provider:
                provider.close()
    return result
