from __future__ import annotations

from typing import Annotated, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, StrictInt, model_validator

PROFILES = {
    "preschool": {
        "label": "Mầm non · 3–4 tuổi",
        "advice": "Một ý, hình quen thuộc, nhịp chậm; người lớn đồng hành.",
    },
    "kids": {
        "label": "Khám phá · 5–8 tuổi",
        "advice": "Câu ngắn, giải thích từ mới, một ý mỗi cảnh.",
    },
    "older_kids": {
        "label": "Tìm hiểu · 9–12 tuổi",
        "advice": "Giải thích cơ chế, ví dụ và câu hỏi suy luận.",
    },
    "family": {
        "label": "Cả nhà · 6+",
        "advice": "Dễ hiểu với trẻ, có thông tin hữu ích cho người lớn.",
    },
    "general": {
        "label": "Khán giả phổ thông",
        "advice": "Cô đọng, chính xác; không tự suy là không dành cho trẻ.",
    },
}
Profile = Literal["preschool", "kids", "older_kids", "family", "general"]
Platform = Literal["shorts", "kids", "tiktok", "reels"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class CreativeBrief(StrictModel):
    topic: str = Field(default="", max_length=300)
    objective: str = Field(default="", max_length=1000)
    takeaways: list[Annotated[str, Field(max_length=300)]] = Field(
        default_factory=list, max_length=3
    )
    target_duration: Literal[30, 45, 60] = 45
    tone: str = Field(default="Ấm áp, tò mò, rõ ràng; không giật gân", max_length=300)
    required_facts: str = Field(default="", max_length=3000)
    sources: list[Annotated[str, Field(max_length=500)]] = Field(
        default_factory=list, max_length=10
    )
    avoid: str = Field(default="", max_length=1000)
    style_bible: str = Field(
        default="Nét đen sạch, ít màu, nền kem, không chữ trong ảnh", max_length=1500
    )
    character_bible: str = Field(default="", max_length=1000)


class Scene(StrictModel):
    id: str = Field(default_factory=lambda: str(uuid4()), min_length=1, max_length=64)
    title: str = Field(default="Cảnh mới", min_length=1, max_length=70)
    narration: str = Field(default="", max_length=500)
    image_prompt: str = Field(default="", max_length=2000)
    image_id: str | None = None
    audio_id: str | None = None
    audio_stale: bool = False
    duration: float = Field(default=5, ge=1, le=20, allow_inf_nan=False)
    style: Literal["whiteboard", "motion"] = "whiteboard"
    caption_style: Literal["card", "contrast", "accent"] = "card"
    caption_emphasis: str = Field(default="", max_length=70)
    motion_expectation: Literal["allow_static", "motion_required"] = "allow_static"
    visual_description: str = Field(default="", max_length=1000)
    role: Literal["hook", "context", "explain", "example", "payoff"] = "explain"
    reveal_order: list[str] = Field(default_factory=list, max_length=10)
    fact_flags: list[str] = Field(default_factory=list, max_length=10)
    source_refs: list[int] = Field(default_factory=list, max_length=10)


class ProjectInput(StrictModel):
    title: str = Field(min_length=1, max_length=70)
    profile: Profile = "family"
    platform: Platform = "shorts"
    narration: str = Field(default="", max_length=12000)
    aspect: Literal["portrait", "landscape"] = "portrait"
    brief: CreativeBrief = Field(default_factory=CreativeBrief)


class ProjectUpdate(ProjectInput):
    revision: int = Field(ge=0)
    scenes: list[Scene] = Field(default_factory=list, max_length=20)


class SplitInput(StrictModel):
    revision: int = Field(ge=0)
    replace_existing: bool = False


class ExportInput(StrictModel):
    revision: int = Field(ge=0)
    kind: Literal["preview", "export"] = "export"
    silent: bool = False
    captions: bool = True
    aspect: Literal["portrait", "landscape"] = "portrait"
    idempotency_key: str = Field(min_length=8, max_length=100)


class PublishInput(StrictModel):
    audience: Literal["pending", "made_for_kids", "general_audience"] = "pending"
    rights: Literal["pending", "owned", "licensed"] = "pending"


Criterion = Literal[
    "prompt_alignment",
    "motion_smoothness",
    "temporal_consistency",
    "physical_plausibility",
    "technical_quality",
]


class CriterionReview(StrictModel):
    score: Annotated[StrictInt, Field(ge=1, le=5)] | None = None
    critical: bool = False
    note: str = Field(default="", max_length=500)
    at_seconds: float | None = Field(default=None, ge=0, allow_inf_nan=False)

    @model_validator(mode="after")
    def describe_critical(self):
        if self.critical and not self.note:
            raise ValueError("Describe the critical failure.")
        return self


class QualityReviewInput(StrictModel):
    video_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    review_revision: int = Field(ge=0)
    reviewer: str = Field(min_length=1, max_length=100)
    criteria: dict[Criterion, CriterionReview] = Field(default_factory=dict)
    watched_full: bool = False
    listened_audio: bool = False
    checked_captions: bool = False
    checked_facts_age: bool = False
    disclosure_reviewed: bool = False
    content_origin: Literal["unknown", "ai_assisted", "no_ai"] = "unknown"
    disclosure_note: str = Field(default="", max_length=500)
    acknowledged_findings: list[Annotated[str, Field(max_length=100)]] = Field(
        default_factory=list, max_length=400
    )


class PlanInput(StrictModel):
    revision: int = Field(ge=0)
    mode: Literal["brief", "preserve"] = "brief"
    idempotency_key: str = Field(min_length=8, max_length=100)


class ImageInput(StrictModel):
    revision: int = Field(ge=0)
    seed: int = Field(default=42, ge=0, le=2**32 - 1)
    idempotency_key: str = Field(min_length=8, max_length=100)


class ApplyInput(StrictModel):
    revision: int = Field(ge=0)
    confirm: bool = False


def split_script(text: str) -> list[Scene]:
    """Paragraph-based editing helper, deliberately not marketed as AI."""
    paragraphs = [part.strip() for part in text.splitlines() if part.strip()]
    if not paragraphs:
        raise ValueError("Nhập lời thoại trước khi chia cảnh.")
    if len(paragraphs) > 20:
        raise ValueError("Tối đa 20 đoạn/cảnh. Hãy rút gọn lời thoại.")
    if any(len(part) > 500 for part in paragraphs):
        raise ValueError("Một đoạn quá 500 ký tự. Tách đoạn bằng xuống dòng.")
    return [
        Scene(title=f"Cảnh {i + 1}", narration=part, duration=min(10, max(3, len(part) / 20)))
        for i, part in enumerate(paragraphs)
    ]
