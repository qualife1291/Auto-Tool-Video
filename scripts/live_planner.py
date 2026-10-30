"""Optional real Ollama smoke. Saves a proposal for review without applying it."""

import argparse
import json
from pathlib import Path
from uuid import uuid4

from auto_tool_video.domain import CreativeBrief, PlanInput, ProjectInput
from auto_tool_video.generation import enqueue_generation, run_generation
from auto_tool_video.store import Store

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--topic", default="Vì sao áo ướt khô?")
    parser.add_argument("--narration", default="")
    args = parser.parse_args()
    root = args.output_dir.resolve()
    store = Store(root / "planner-store")
    project = store.create(
        ProjectInput(
            title="Kiểm planner local",
            narration=args.narration,
            brief=CreativeBrief(topic=args.topic, target_duration=30),
        ).model_dump()
    )
    job = enqueue_generation(
        store,
        project["id"],
        PlanInput(
            revision=0,
            mode="preserve" if args.narration else "brief",
            idempotency_key=str(uuid4()),
        ),
    )
    run_generation(store, store.claim())
    result = store.get("jobs", job["id"])
    (root / "planner-result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    )
    if result["state"] != "succeeded":
        raise SystemExit(
            f"Planner failed: {result.get('error_code')}. See local report; no proposal applied."
        )
    assert store.get("projects", project["id"])["scenes"] == []
    print(
        json.dumps(
            {
                "state": result["state"],
                "provenance": result["result"]["provenance"],
                "report": str(root / "planner-result.json"),
                "applied": False,
            }
        )
    )
