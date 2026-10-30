#!/usr/bin/env python3
"""Optional, read-only, standard-library task contract lint for Markdown issues.

No GitHub access, shell execution, interpolation, dependency installation or writes.
The JSON block is explicitly opt-in and validates only *declared* facts.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

MAX_INPUT_BYTES = 1_048_576
BLOCK_START = re.compile(r"^```agent-task-contract[ \t]*$")
FENCE = re.compile(r"^(`{3,}|~{3,})([^\r\n]*)$")
ROLE = re.compile(r"^(?:BA\d{2}|T\d{2}|C\d{2,})$")
TASK_ID = re.compile(r"^[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+$")
SHA = re.compile(r"^[0-9a-f]{40}$")
REQUIRED = frozenset(
    {
        "schema_version",
        "task_id",
        "owner_id",
        "approved_spec",
        "base_branch",
        "base_sha",
        "branch",
        "write_paths",
        "forbidden_paths",
        "acceptance_criteria",
        "tests",
        "qa_owner",
        "dependencies",
        "rollback",
    }
)


class DuplicateKey(ValueError):
    """JSON object has a duplicate key (last-write-wins would be unsafe)."""


def object_pairs_unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for key, value in pairs:
        if key in output:
            raise DuplicateKey(f"duplicate JSON key: {key}")
        output[key] = value
    return output


def extract_blocks(markdown: str) -> tuple[list[str], list[str]]:
    """Enroll only exact top-level contract fences; skip other code blocks."""
    blocks: list[str] = []
    errors: list[str] = []
    active: list[str] | None = None
    other_fence: tuple[str, int] | None = None
    for line in markdown.splitlines():
        fence = FENCE.fullmatch(line)
        if active is not None:
            if fence and fence.group(1) == "```" and not fence.group(2).strip():
                blocks.append("\n".join(active))
                active = None
            else:
                active.append(line)
        elif other_fence:
            if (
                fence
                and fence.group(1)[0] == other_fence[0]
                and len(fence.group(1)) >= other_fence[1]
                and not fence.group(2).strip()
            ):
                other_fence = None
        elif BLOCK_START.fullmatch(line):
            active = []
        elif fence:
            other_fence = (fence.group(1)[0], len(fence.group(1)))
    if active is not None:
        errors.append("unclosed agent-task-contract fence")
    return blocks, errors


def valid_path(value: Any) -> bool:
    """A literal repo-relative POSIX file or directory-prefix (trailing /) path."""
    if not isinstance(value, str) or not value or len(value) > 260:
        return False
    if value.startswith(("/", "~")) or "\\" in value or ":" in value:
        return False
    if value != value.strip() or any(ch in value for ch in "*?[]{}%\x00"):
        return False
    if any(ord(ch) < 32 for ch in value) or value.endswith("//"):
        return False
    segments = value.rstrip("/").split("/")
    if any(part in ("", ".", "..") for part in segments):
        return False
    return not any(part == ".git" or part.startswith(".env") for part in segments)


def collides(left: str, right: str) -> bool:
    """File/file equality or explicit directory-prefix overlap."""
    if left.rstrip("/") == right.rstrip("/"):
        return True
    return (left.endswith("/") and right.startswith(left)) or (
        right.endswith("/") and left.startswith(right)
    )


def validate_contract(value: Any, index: int) -> list[str]:
    prefix = f"contract[{index}]"
    errors: list[str] = []
    if not isinstance(value, dict):
        return [f"{prefix}: JSON contract must be an object"]
    missing = sorted(REQUIRED - value.keys())
    extra = sorted(value.keys() - REQUIRED)
    errors.extend(f"{prefix}: missing required field {key}" for key in missing)
    errors.extend(f"{prefix}: unknown field {key}" for key in extra)
    if type(value.get("schema_version")) is not int or value.get("schema_version") != 1:
        errors.append(f"{prefix}.schema_version: expected integer 1")
    task = value.get("task_id")
    if not isinstance(task, str) or not TASK_ID.fullmatch(task):
        errors.append(f"{prefix}.task_id: expected uppercase hyphenated task ID")
    owner = value.get("owner_id")
    if not isinstance(owner, str) or not ROLE.fullmatch(owner):
        errors.append(f"{prefix}.owner_id: expected BA01/T01/C03-style role ID")
    qa = value.get("qa_owner")
    if not isinstance(qa, str) or not re.fullmatch(r"T\d{2,}", qa):
        errors.append(f"{prefix}.qa_owner: independent Txx role required")
    elif qa == owner:
        errors.append(f"{prefix}.qa_owner: self-QA is prohibited")
    spec = value.get("approved_spec")
    if not isinstance(spec, dict) or set(spec) != {"ref", "status"}:
        errors.append(f"{prefix}.approved_spec: expected ref/status object")
    else:
        if not valid_path(spec["ref"]) or spec["ref"].endswith("/"):
            errors.append(f"{prefix}.approved_spec.ref: unsafe/empty reference path")
        if spec["status"] not in ("approved", "skipped-by-user"):
            errors.append(f"{prefix}.approved_spec.status: must be approved/skipped-by-user")
    base_branch = value.get("base_branch")
    branch = value.get("branch")
    for key, item in (("base_branch", base_branch), ("branch", branch)):
        if not valid_path(item) or (isinstance(item, str) and item.endswith("/")):
            errors.append(f"{prefix}.{key}: invalid branch ref")
    if isinstance(base_branch, str) and isinstance(branch, str) and base_branch == branch:
        errors.append(f"{prefix}.branch: must differ from base_branch")
    if isinstance(branch, str) and not branch.startswith("agent/"):
        errors.append(f"{prefix}.branch: must use isolated agent/ branch")
    sha = value.get("base_sha")
    if not isinstance(sha, str) or not SHA.fullmatch(sha):
        errors.append(f"{prefix}.base_sha: expected 40 lowercase hexadecimal characters")

    for key in ("write_paths", "forbidden_paths"):
        paths = value.get(key)
        if not isinstance(paths, list) or (key == "write_paths" and not paths):
            requirement = "nonempty list" if key == "write_paths" else "list"
            errors.append(f"{prefix}.{key}: expected {requirement}")
            continue
        if any(not valid_path(p) for p in paths):
            errors.append(f"{prefix}.{key}: unsafe/empty repo-relative path")
        if any(isinstance(p, str) and paths.count(p) > 1 for p in paths):
            errors.append(f"{prefix}.{key}: duplicate path")
        good = [p for p in paths if valid_path(p)]
        if any(collides(a, b) for i, a in enumerate(good) for b in good[i + 1 :]):
            errors.append(f"{prefix}.{key}: internally overlapping paths")

    writes, forbidden = value.get("write_paths"), value.get("forbidden_paths")
    if isinstance(writes, list) and isinstance(forbidden, list):
        if any(
            collides(a, b)
            for a in writes
            for b in forbidden
            if valid_path(a) and valid_path(b)
        ):
            errors.append(f"{prefix}: write_paths conflict with forbidden_paths")
    for key in ("acceptance_criteria", "tests", "dependencies"):
        items = value.get(key)
        if not isinstance(items, list) or (key != "dependencies" and not items):
            requirement = "list" if key == "dependencies" else "nonempty list"
            errors.append(f"{prefix}.{key}: expected {requirement}")
        elif any(not isinstance(p, str) or not p.strip() for p in items):
            errors.append(f"{prefix}.{key}: entries must be nonempty strings")
        elif len(items) != len(set(items)):
            errors.append(f"{prefix}.{key}: duplicate entries")
    if not isinstance(value.get("rollback"), str) or not value["rollback"].strip():
        errors.append(f"{prefix}.rollback: nonempty rollback procedure required")
    return errors


def lint_markdown(markdown: str, *, multi: bool = False) -> dict[str, Any]:
    blocks, errors = extract_blocks(markdown)
    if not blocks and not errors:
        return {
            "status": "NOT_ENROLLED",
            "contracts": 0,
            "task_ids": [],
            "errors": [],
            "warnings": ["No opt-in agent-task-contract block; legacy Markdown is NOT certified."],
        }
    if len(blocks) > 1 and not multi:
        errors.append("multiple contract blocks require explicit --multi")
    contracts: list[Any] = []
    for i, raw in enumerate(blocks):
        try:
            value = json.loads(
                raw,
                object_pairs_hook=object_pairs_unique,
                parse_constant=lambda constant: (_ for _ in ()).throw(
                    ValueError(f"nonstandard JSON constant: {constant}")
                ),
            )
        except (ValueError, RecursionError) as exc:
            errors.append(f"contract[{i}]: invalid JSON ({exc})")
            continue
        errors.extend(validate_contract(value, i))
        contracts.append(value)
    if multi:
        ids: set[str] = set()
        for i, value in enumerate(contracts):
            if not isinstance(value, dict):
                continue
            task = value.get("task_id")
            if isinstance(task, str):
                if task in ids:
                    errors.append(f"contract[{i}]: duplicate task_id {task}")
                ids.add(task)
        for i, a in enumerate(contracts):
            if not isinstance(a, dict) or not isinstance(a.get("write_paths"), list):
                continue
            for j, b in enumerate(contracts[i + 1 :], i + 1):
                if not isinstance(b, dict) or not isinstance(b.get("write_paths"), list):
                    continue
                for left in a["write_paths"]:
                    for right in b["write_paths"]:
                        if valid_path(left) and valid_path(right) and collides(left, right):
                            errors.append(
                                f"contract[{i}] and contract[{j}]: overlapping write scope "
                                f"{left} / {right}"
                            )
    return {
        "status": "FAIL" if errors else "PASS",
        "contracts": len(blocks),
        "task_ids": [
            v["task_id"]
            for v in contracts
            if isinstance(v, dict) and isinstance(v.get("task_id"), str)
        ],
        "errors": sorted(set(errors)),
        "warnings": [
            "Offline only: spec approval, base_sha freshness, actual GitHub claims "
            "and permissions NOT verified."
        ],
    }


def read_source(filename: str | None) -> str:
    if filename is None:
        content = sys.stdin.read(MAX_INPUT_BYTES + 1)
        if len(content.encode("utf-8")) > MAX_INPUT_BYTES:
            raise ValueError("Markdown exceeds 1 MiB cap")
        return content
    path = Path(filename)
    if ".." in path.parts or path.is_symlink():
        raise ValueError("--file rejects traversal and symlink paths")
    if path.suffix.lower() != ".md" or not path.is_file():
        raise ValueError("--file must refer to an existing Markdown .md regular file")
    if path.stat().st_size > MAX_INPUT_BYTES:
        raise ValueError("Markdown exceeds 1 MiB cap")
    content = path.read_text(encoding="utf-8")
    if len(content.encode("utf-8")) > MAX_INPUT_BYTES:
        raise ValueError("Markdown exceeds 1 MiB cap")
    return content


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", help="Explicit Markdown file (default: stdin)")
    parser.add_argument("--json", action="store_true", help="Write deterministic JSON report")
    parser.add_argument(
        "--multi", action="store_true", help="Validate several opt-in contracts and scopes"
    )
    args = parser.parse_args(argv)
    try:
        report = lint_markdown(read_source(args.file), multi=args.multi)
    except (ValueError, UnicodeError, OSError) as exc:
        report = {
            "status": "FAIL", "contracts": 0, "task_ids": [],
            "errors": [f"input: {exc}"], "warnings": [],
        }
    if args.json:
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    else:
        print(f"{report['status']} — {report['contracts']} enrolled contract(s)")
        for message in report["errors"]:
            print(f"ERROR: {message}")
        for message in report["warnings"]:
            print(f"NOTE: {message}")
    return {"PASS": 0, "FAIL": 2, "NOT_ENROLLED": 3}[report["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
