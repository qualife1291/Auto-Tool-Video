# C03 Dev Harness H0/H1 — Offline Task-Contract PoC

**Status:** IMPLEMENTATION POC / OPT-IN ONLY; **not enforced** in GitHub, CI, issue templates or production.  
**Audit date:** 2026-10-31 (Asia/Ho_Chi_Minh)  
**Owner:** C03; **BA:** BA01; **independent QA/merge:** T01.  
**Assignment:** [#48](https://github.com/qualife1291/Auto-Tool-Video/issues/48), parent research [#38](https://github.com/qualife1291/Auto-Tool-Video/issues/38).  
**Pinned canonical at claim:** [`2db0ba55ac1775f8d33b647bd62741ee4c6cba55`](https://github.com/qualife1291/Auto-Tool-Video/commit/2db0ba55ac1775f8d33b647bd62741ee4c6cba55). GitHub is mutable: **do not infer current branch freshness** from this snapshot.

## H0: verified workflow reality and gap analysis

| Gate | Observed evidence at audit | Gap / consequence | PoC action |
| --- | --- | --- | --- |
| Roles and substitution | [BA role charter](https://github.com/qualife1291/Auto-Tool-Video/blob/2db0ba55ac1775f8d33b647bd62741ee4c6cba55/docs/agent-role-charter.md) defines BA01, T01, C03, C04; shared GitHub login ≠ agent identity | Human claims can be misattributed across seats | Validate **declared** role syntax; never authenticate or assert current owner |
| Task contracts / CLAIM | [C03 #41](https://github.com/qualife1291/Auto-Tool-Video/issues/41) and [C04 #44](https://github.com/qualife1291/Auto-Tool-Video/issues/44) use human-readable owner, SHA, exclusive file scope, AC, test plan | Free-form text may omit fields or hide duplicate write scopes | Optional explicit machine-readable JSON block alongside human prose |
| Independent QA / exact SHA | [PR #42](https://github.com/qualife1291/Auto-Tool-Video/pull/42) initially blocked when its merge-ref did not have current-base CI; synced, later T01 merged with separate postmerge CI | Old PR-head green does **not** prove current merged tree | Require base SHA syntax, warn freshness **NOT VERIFIED**; never report CI PASS |
| Historical handover vs current | Existing `AGENTS.md`, workboard and handover are historical; [T01 PR #46](https://github.com/qualife1291/Auto-Tool-Video/pull/46) updates these paths separately | Stale documentation can mislead replacement coders | Read-only: leave all of T01's docs/workflows unchanged |
| C04 / T01 concurrent scope | [C04 PR #47](https://github.com/qualife1291/Auto-Tool-Video/pull/47) works on `api.py`; [T01 PR #37](https://github.com/qualife1291/Auto-Tool-Video/pull/37) on QA scenario tests | Two independent agents could accidentally claim the same directory | Multi-contract **declared** write/file-prefix collision check |
| FREE and event-volume guard | [T01 watcher hotfix #43](https://github.com/qualife1291/Auto-Tool-Video/pull/43) removed noisy `workflow_run` coupling | Automated triggers can flood expensive runners | This tool has **no events, scheduling, network or CI hook** |
| Secrets / permissions | GitHub connector account and agent seat IDs are distinct; task text is untrusted | Contract input cannot grant permission or approve paid spend | Strict data-only JSON, no `eval`, shell, GitHub token, file writes or code loading |

### Options and decision (2026-10-31)

| Alternative | Direct tool/license verification | Cost and security limitation | Decision |
| --- | --- | --- | --- |
| A. Human issue checklist only | Existing GitHub issue/PR Markdown, no extra package; GitHub-native | **FREE** for manual text checks, but omissions, duplicate scopes and stale SHA may remain undetected | Keep as legacy fallback; label `NOT_ENROLLED` |
| **B. Python stdlib offline checker** | Python 3.12+ already required by `backend/pyproject.toml`; no third-party import | **FREE**, no network credentials or runtime mutation; cannot know true GitHub head/reviews or author identity | **Choose for isolated H0/H1 PoC** |
| C. OpenHands full coding agent | [Official repo](https://github.com/OpenHands/OpenHands), repository license `MIT` (verified through GitHub repo metadata); [vendor pricing](https://www.openhands.dev/pricing) | Open-source/self-hosted code is free, **LLM inference/key and hardware may not be free**; hosted free tier/BYOK has separate usage limits. Agent with execution access requires sandbox/secrets review | Do **not** install/integrate under #48; future independent spike |
| D. Microsoft Agent Framework | [Official repo](https://github.com/microsoft/agent-framework), GitHub repo license `MIT` (verified through repo metadata); [official docs](https://learn.microsoft.com/en-us/agent-framework/support/faq) | Framework OSS, **model/provider and cloud execution not guaranteed free**; orchestration/runtime considerably broader than static contract lint | Do **not** install/integrate; future H2/H3 evaluation only |

GitHub Actions billing is **not** a premise of this script: [GitHub official billing documentation](https://docs.github.com/en/billing/concepts/product-billing/github-actions) says standard GitHub-hosted runners for **public repositories** are free; actual repo metadata shows `private=false` at audit. This does **not** grant unlimited storage, larger runners or private-repository quotas, nor does it prove the account's billing plan. This PR adds no CI workflow, timer or paid action; ordinary existing PR CI may still execute as part of T01's review.

## H1: opt-in Markdown JSON contract v1

Add exactly one unindented fenced JSON block to an issue **without replacing human-written requirements**. For concurrent claims, combine several fenced blocks in one explicitly supplied input and call `--multi` (the checker does not query GitHub or aggregate separate issues by itself):

````markdown
```agent-task-contract
{
  "schema_version": 1,
  "task_id": "C03-HARN-H01-CONTRACT-POC",
  "owner_id": "C03",
  "approved_spec": {
    "ref": "specs/whiteboard-video-tool.md",
    "status": "approved"
  },
  "base_branch": "feat/short-video-studio",
  "base_sha": "2db0ba55ac1775f8d33b647bd62741ee4c6cba55",
  "branch": "agent/C03-HARN-H01-task-contract-poc",
  "write_paths": [
    "scripts/dev_harness_contract.py",
    "backend/tests/test_dev_harness_contract.py",
    "docs/research/C03-dev-harness-contract-poc.md"
  ],
  "forbidden_paths": [".github/", "backend/auto_tool_video/"],
  "acceptance_criteria": [
    "Validate enrolled contracts; legacy must be NOT_ENROLLED",
    "Detect missing fields, traversal, duplicate keys and overlapping paths"
  ],
  "tests": ["python -m pytest backend/tests/test_dev_harness_contract.py -q"],
  "qa_owner": "T01",
  "dependencies": ["#38", "#45", "#46 read-only"],
  "rollback": "Stop invoking this optional checker. No repo/CI state is changed."
}
```
````

### Schema / compatibility / guardrails

- **Required exact keys**: `schema_version` (integer exactly `1`); `task_id` (uppercase hyphenated); `owner_id` (`BA01`, `T01`, `C03`...); `approved_spec` (object with exact `ref` and `status` `approved`/`skipped-by-user`); `base_branch`, `base_sha` (exact 40 lowercase hex), isolated `agent/...` branch; `write_paths` (nonempty list); `forbidden_paths` (list); `acceptance_criteria` and `tests` (nonempty string lists); `qa_owner` (separate `Txx` reviewer); `dependencies` (possibly empty list); `rollback` (nonempty string). Unknown/duplicate keys or versions **FAIL** instead of silently passing.
- Paths: literal, repo-relative POSIX strings. A **trailing `/` denotes a directory prefix**; a path without it denotes one file. `../`, `.`, absolute/Windows paths, backslashes, repeated slashes, percent-encoded segments, `.env` / `.git` sensitive paths, wildcards, colon, control characters and duplicate overlapping scopes fail. The script **never opens** paths named in a contract.
- Multi-contract: opt in with `--multi`; catches duplicate task IDs and any overlapping declared writes (including same file, explicit directory prefix and file/directory same stem), regardless of owner. It **cannot** discover other active claims not included in input.
- For un-enrolled older issues, **`NOT_ENROLLED`**, not `PASS`. For malformed/invalid opt-in contracts **`FAIL`**. Even `PASS` means only *syntactic/declared contract checks*, **not** approved spec provenance, real GitHub permissions, immutable base SHA, authenticated agent identity, CI status, or permission to merge.
- Untrusted Markdown/embedded shell/HTML and JSON strings are data; never executed. JSON duplicate keys and nonstandard constants (NaN/Infinity) fail. CLI reads explicitly supplied `.md` regular file or stdin; symlink and traversal `--file` paths are rejected, at most **1 MiB**, no token/environment/secret lookup, external requests, stdout content dump or writes. Avoid passing private or sensitive issue bodies to third-party systems.

### Run locally (no installation, network, authentication or mutation)

```bash
python -B scripts/dev_harness_contract.py --file issue.md
python -B scripts/dev_harness_contract.py --json < issue.md
python -B scripts/dev_harness_contract.py --json --multi < combined.md
python -m pytest backend/tests/test_dev_harness_contract.py -q
```

| Status | Exit | Meaning / safe follow-up |
| --- | ---: | --- |
| `PASS` | `0` | Fields internally consistent **only**; T01/BA01 must still check GitHub and approved spec |
| `FAIL` | `2` | Malformed/enrolled-invalid/duplicate/overlapping contract; repair before claiming |
| `NOT_ENROLLED` | `3` | Legacy text without an opt-in contract; manual BA checklist remains required |

For `--json`, output is deterministically ordered JSON with `status`, `contracts`, `task_ids`, `errors`, `warnings` and no timestamp/side effects. This is intentionally **not** a GitHub App, webhook or CI merge gate.

## Local benchmark / test protocol (not a claim of upstream CI)

- **Executed locally** in ephemeral environment with Python **3.13.5**: `python -m pytest backend/tests/test_dev_harness_contract.py -q` → **45 passed** (positive roles, not-enrolled, unsupported schema, missing fields, JSON duplicates, malformed/empty/truncated fences, invalid SHA/path, self-QA, collisions, Unicode, fake command injection, no file mutation, input cap, repeatability and stdin/file/exit-code checks).
- Pure in-process checker on one synthetic valid contract: **7 × 1,000 iterations**, median **0.070 ms/contract** (min 0.061, max 0.074) measured using `time.perf_counter` in this ephemeral environment. **Not** a cross-hardware or real GitHub throughput guarantee; excludes interpreter startup, disk I/O and real human review.
- **Existing full repository CI/Ruff/mypy/Playwright:** **PENDING GitHub exact-PR-head validation**; update PR body with run links and results, not these historical local timings.
- Quality targets: 100% explicit `NOT_ENROLLED` for legacy text; zero false `PASS` for malformed, duplicated, unknown-version, traversing or overlapping declarations; 100% deterministic repeat outputs; external network and runtime mutation operations = **zero**. The tests measure these selected cases, not statistically guarantee arbitrary input coverage.
- Adoption friction: 13 required keys + BA authoring/claim maintenance, roughly 5–10 minutes initial issue drafting (planning estimate, **not measured**). No migration of historical issues. A future opt-in pilot should compare 5–10 sanitized contracts against manual BA/T01 review, record true-positive/false-positive counts and overhead before deciding whether automation is worth it.

### H2+ roadmap (separately approved)

1. BA01 reviews this H0 gap matrix and agrees on v1 block syntax. T01 reviews edge cases, no-secret behavior, and independent QA protocol.
2. Trial manually with synthetic task contracts and compare to documented GitHub actual ownership/base/review. No paid providers and no auto-enforcement.
3. Only **new BA01 task authorization** may add issue templates, GitHub Actions hooks, schedule, evidence manifests, cross-issue checks, or a full agent framework. Keep agent **development harness** (claim/PR/QA) separate from **video job harness** (models, retries, render artifacts, QC, creator approval). Share names like SHA, status and idempotency, **never** credentials or implicit execution authority.
4. **Rollback**: stop invoking the CLI or drop its three isolated PoC files in a reviewed PR. There is no background process, persistent database or migration to unwind.

**Unresolved risks:** Markdown schema does not authenticate claim author or attest spec approval; input lacks a live current-head compare; filename-based ownership is conservative and symbolic, not Git's path permissions; older unauthenticated/legacy tasks still require human review; Unicode/confusable identifiers are restricted but free-text AC needs human understanding; creator video release gates are entirely outside scope.
