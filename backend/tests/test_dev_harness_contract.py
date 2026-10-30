"""C03 H0/H1 offline contract checker — no GitHub or paid provider required."""

from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "dev_harness_contract.py"
spec = importlib.util.spec_from_file_location("c03_dev_harness_contract", SCRIPT)
assert spec and spec.loader
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


def contract(*, owner="C03", task="C03-HARN-H01-CONTRACT-POC", paths=None):
    return {
        "schema_version": 1,
        "task_id": task,
        "owner_id": owner,
        "approved_spec": {"ref": "specs/whiteboard-video-tool.md", "status": "approved"},
        "base_branch": "feat/short-video-studio",
        "base_sha": "2db0ba55ac1775f8d33b647bd62741ee4c6cba55",
        "branch": f"agent/{owner}-task-contract",
        "write_paths": paths or ["scripts/dev_harness_contract.py"],
        "forbidden_paths": [".github/", "backend/auto_tool_video/"],
        "acceptance_criteria": ["Fail closed for overbroad write ownership", "Giữ nguyên chữ Việt"],
        "tests": ["pytest backend/tests/test_dev_harness_contract.py -q"],
        "qa_owner": "T01",
        "dependencies": [],
        "rollback": "Stop invoking the opt-in CLI; no repository migration is needed.",
    }


def markdown(*contracts):
    return "# BA01 issue text\n" + "\n".join(
        "```agent-task-contract\n" + json.dumps(c, ensure_ascii=False) + "\n```"
        for c in contracts
    )


def invoke(source: str, *args):
    # Exercise the pure core for the large negative matrix; reserve subprocess
    # for actual stdin/file/exit-code integration so CI stays fast and offline.
    if not args or args == ("--multi",):
        report = checker.lint_markdown(source, multi=bool(args))
        return {"PASS": 0, "FAIL": 2, "NOT_ENROLLED": 3}[report["status"]], report, ""
    run = subprocess.run(
        [sys.executable, "-B", str(SCRIPT), "--json", *args],
        input=source,
        text=True,
        capture_output=True,
        check=False,
        timeout=10,
    )
    return run.returncode, json.loads(run.stdout), run.stderr


@pytest.mark.parametrize("owner", ["C03", "C04"])
def test_enrolled_valid_contract_passes_without_live_claim_authentication(owner):
    value = contract(owner=owner, task=f"{owner}-HARN-H01-CONTRACT-POC")
    code, report, err = invoke(markdown(value))
    assert code == 0 and report["status"] == "PASS" and not err
    assert report["task_ids"] == [value["task_id"]]
    assert "NOT verified" in report["warnings"][0]


def test_legacy_and_non_contract_fenced_markdown_is_not_enrolled():
    for source in (
        "# Old issue\nAssignee: C03\nSHA 2db0ba55...\n",
        "```bash\npython scripts/dev_harness_contract.py\n```",
        '```markdown\n```agent-task-contract\n{"schema_version":1}\n```\n```',
    ):
        code, output, _ = invoke(source)
        assert code == 3 and output["status"] == "NOT_ENROLLED"
        assert output["contracts"] == 0


@pytest.mark.parametrize(
    "field,replacement,expected",
    [
        ("schema_version", "1", "schema_version"),
        ("schema_version", 2, "schema_version"),
        ("owner_id", "qualife1291", "owner_id"),
        ("owner_id", "C3", "owner_id"),
        ("task_id", "bad id", "task_id"),
        ("base_sha", "abcd", "base_sha"),
        ("base_sha", "F" * 40, "base_sha"),
        ("approved_spec", {"ref": "README.md", "status": "draft"}, "approved_spec"),
        ("approved_spec", {"status": "approved"}, "approved_spec"),
        ("base_branch", "../main", "base_branch"),
        ("branch", "feat/short-video-studio", "branch"),
        ("branch", "agent/../steal", "branch"),
        ("write_paths", [], "write_paths"),
        ("write_paths", ["../../.env"], "write_paths"),
        ("write_paths", ["C:\\secrets\\key"], "write_paths"),
        ("write_paths", ["docs//evil"], "write_paths"),
        ("write_paths", ["docs/%2e%2e/secret"], "write_paths"),
        ("write_paths", [".git/config"], "write_paths"),
        ("write_paths", [".env.local"], "write_paths"),
        ("write_paths", ["docs//"], "write_paths"),
        ("write_paths", ["foo", "foo"], "write_paths"),
        ("write_paths", ["foo/", "foo/bar.md"], "write_paths"),
        ("write_paths", ["backend/auto_tool_video/jobs.py"], "conflict"),
        ("forbidden_paths", ["foo//"], "forbidden_paths"),
        ("acceptance_criteria", [], "acceptance_criteria"),
        ("tests", [], "tests"),
        ("tests", ["", "pytest"], "tests"),
        ("qa_owner", "C03", "qa_owner"),
        ("qa_owner", "BA01", "qa_owner"),
        ("rollback", "", "rollback"),
        ("dependencies", ["", "#44"], "dependencies"),
    ],
)
def test_fails_closed_for_invalid_or_missing_contract_fields(field, replacement, expected):
    value = contract()
    value[field] = replacement
    code, report, _ = invoke(markdown(value))
    assert code == 2 and report["status"] == "FAIL"
    assert any(expected in s for s in report["errors"]), report
    del value[field]
    code, report, _ = invoke(markdown(value))
    assert code == 2 and any(field in s for s in report["errors"])


def test_unsupported_keys_invalid_json_and_duplicate_json_keys_fail():
    issue = contract()
    issue["unexpected_extension"] = "allow_all"
    assert "unknown field" in "\n".join(invoke(markdown(issue))[1]["errors"])
    raw = markdown(contract()).replace(
        '"schema_version": 1', '"schema_version": 1, "schema_version": 1'
    )
    code, report, _ = invoke(raw)
    assert code == 2 and "duplicate JSON key" in "\n".join(report["errors"])
    for source in (
        "```agent-task-contract\n{\n```",
        "```agent-task-contract\n{\"schema_version\": NaN}\n```",
        "```agent-task-contract\n[]\n```",
        "```agent-task-contract\n{}",
        "```agent-task-contract\n",
    ):
        code, report, _ = invoke(source)
        assert code == 2 and report["status"] == "FAIL"


def test_duplicate_contracts_require_multi_flag_and_unique_task_ids():
    a = contract()
    b = contract(owner="C04", task="C04-HARN-H01-CONTRACT-POC", paths=["backend/tests/other.py"])
    text = markdown(a, b)
    assert invoke(text)[1]["status"] == "FAIL"
    code, report, _ = invoke(text, "--multi")
    assert code == 0 and report["status"] == "PASS" and report["contracts"] == 2
    b["task_id"] = a["task_id"]
    assert "duplicate task_id" in "\n".join(invoke(markdown(a, b), "--multi")[1]["errors"])


@pytest.mark.parametrize(
    "other_path",
    ["scripts/dev_harness_contract.py", "scripts/", "scripts/dev_harness_contract.py/"],
)
def test_cross_owner_directory_or_same_file_write_collision(other_path):
    a = contract()
    b = contract(owner="C04", task="C04-HARN-H01-CONTRACT-POC", paths=[other_path])
    code, result, _ = invoke(markdown(a, b), "--multi")
    assert code == 2 and "overlapping write scope" in "\n".join(result["errors"])


def test_inert_untrusted_markdown_and_unicode_text(tmp_path):
    marker = tmp_path / "do-not-create.txt"
    injected = f'$(touch "{marker}")\n<script>alert(1)</script>\n{{{{ 7*7 }}}}'
    c = contract()
    c["acceptance_criteria"] = [injected, "Tiếng Việt: giọt nước ☔"]
    source = markdown(c) + "\n```bash\nrm -rf /\n```\n"
    code, report, _ = invoke(source)
    assert code == 0 and report["status"] == "PASS"
    assert not marker.exists()


def test_deterministic_report_json_file_and_stdin_no_mutations(tmp_path):
    content = markdown(contract())
    filename = tmp_path / "issue.md"
    filename.write_text(content, encoding="utf-8")
    original = filename.read_bytes()
    a = invoke(content)
    b = invoke(content)
    c = invoke("", "--file", str(filename))
    assert a == b == c
    assert filename.read_bytes() == original
    assert sorted(p.name for p in tmp_path.iterdir()) == ["issue.md"]


def test_reject_non_markdown_file_and_oversize_input(tmp_path):
    secret = tmp_path / ".env"
    secret.write_text("FAKE_TOKEN=do-not-leak")
    code, report, _ = invoke("", "--file", str(secret))
    assert code == 2 and "Markdown .md" in report["errors"][0]
    assert "FAKE_TOKEN" not in json.dumps(report)
    code, report, _ = invoke("x" * (checker.MAX_INPUT_BYTES + 1), "--json")
    assert code == 2 and "1 MiB" in report["errors"][0]


def test_valid_json_syntax_but_invalid_contract_never_false_passes():
    c = contract()
    for value in (True, False, {}, [1], None, "schema 1"):
        bad = copy.deepcopy(c)
        bad["schema_version"] = value
        code, report, _ = invoke(markdown(bad))
        assert code == 2 and report["status"] == "FAIL"


def test_actual_cli_uses_exit_codes_and_inert_stdin():
    cases = [
        (markdown(contract()), 0),
        ("Legacy issue", 3),
        ("```agent-task-contract\n{bad}\n```", 2),
    ]
    for markdown_content, expected in cases:
        run = subprocess.run(
            [sys.executable, "-B", str(SCRIPT), "--json"],
            input=markdown_content,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        assert run.returncode == expected
        expected_status = {0: "PASS", 2: "FAIL", 3: "NOT_ENROLLED"}[expected]
        assert json.loads(run.stdout)["status"] == expected_status


def test_cli_refuses_untrusted_file_traversal_or_symlink(tmp_path):
    issue = tmp_path / "issue.md"
    issue.write_text(markdown(contract()), encoding="utf-8")
    link = tmp_path / "link.md"
    link.symlink_to(issue)
    for bad in (str(link), str(tmp_path / ".." / "issue.md")):
        exit_code, report, _ = invoke("", "--file", bad)
        assert exit_code == 2 and report["status"] == "FAIL"
        assert "traversal" in report["errors"][0]
