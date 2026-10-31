# Repository maintenance and log/evidence hygiene

Status: **policy for review**, 2026-10-30. **No deletion of tracked files or runtime artifacts was performed**. Relevant: [index](documentation-index.md), [PR audit](pr-merge-audit-2026-10-30.md), [BA process](ba-sdlc-process.md), [QA gates](qa-evidence-gates.md).

## 1. What to preserve vs clean

| Category | Examples | Safe action |
|---|---|---|
| **Source/legal** | `backend/`, `apps/`, `scripts/`, `specs/`, lockfiles, font OFL/license, image fixtures | Keep, code review only; never mass-delete |
| **Historical evidence** | dated `.agent/handover/`, `docs/qa-review.md`, `docs/render-benchmark.md`, `docs/source-snapshot.json` | Retain with dates and source SHA; new errata/addenda instead of rewriting old PASS/FAIL |
| **Live indexes** | `docs/agent-workboard.md`, `.agent/handover/LATEST.md`, `TASKS.md` | Update only with owner coordination and verified merged SHA; PR #21/#23 currently own files |
| **Private local state** | `.data/`, SQLite, user assets, model weights, exports | Already ignored; do NOT delete without user inventory, explicit approval and backup |
| **Temporary tests/profile** | `test-results/`, `playwright-report/`, `coverage/`, `htmlcov/`, `*.prof`, `*.memray` | Ignore from Git; store FAIL evidence in protected artifact storage; expiration only after approved retention policy |
| **Sensitive logs/HAR/replay** | `*.log`, stack traces, network captures, screenshots/replay | Never commit credentials/PII/user media; redact and attach to protected issue/CI artifacts with exact run/test/hash |

Git tree verified on 2026-10-30 (canonical SHA `514ddfd966b42183dd1ba6874553794faf3f55e2`): 131 Git tree entries; **no tracked .log, .mp4, .wav, .sqlite3, profiler dump or generated test trace**. No "log cleanup" deletion is needed in source control. Bundled Noto fonts, license files and `assets/examples/wet-shirt.png` are legitimate and must stay. The CI/action logs are managed in GitHub Actions separately.

## 2. Exhaustive *useful* logging without leaking secrets

Each QA/CI/bug record should identify `run_id`, `test_id`, PR/head/base/merged SHA, command/exit code, UTC time, runner/FFmpeg/Node/Python versions, fixture hash, artifact SHA256, regression baseline, unexpected skip/failure and owner. For media bugs add scene/frame/time, relevant crop, audio source and expected/observed behavior.

**Redact** tokens, cookies, Authorization headers, OAuth URLs, private path/user names, personal speech/audio and provider payloads before sharing. A HAR/screenshot/video replay proves an error only if it was genuinely captured, not reconstructed/fabricated. Do not automatically log all request/response bodies. Enforce retention and access control for collected artifacts.

A failing run is never overwritten by a subsequent passing rerun; link both and include root cause. `NOT RUN` ≠ PASS, `PR-CI PASS` ≠ merged-head pass, and technical MP4 pass ≠ creator/release approval.

## 3. Non-destructive cleanup procedure

1. BA issues inventory by `path, class, owner, source SHA, external references, size, safe_action, backup`. Confirm open PRs, workflows and who owns edits.
2. Tester and Coder verify no jobs are using files, no unreproduced failures depend on logs, and last approved output is immutable.
3. For tracked files: only delete content with a clearly justified and independently approved PR, backup/rollback and empty references; **never silently remove historical QA records**.
4. For untracked ignored files: first perform `git status --ignored --short` and a *read-only dry run*; no `git clean -fdx`, `rm -rf .data` or force push without distinct explicit approval.
5. CI logs/artifacts follow configured GitHub Actions retention and protected-access policy; passing-run temporary artifacts can expire if there is a signed audit summary, but release evidence/failed regression assets need retention separately agreed with owner. **No new automatic deletion timer has been configured.**
6. Recheck Markdown cross-links, relative paths, UTF-8, current merged-PR references, docs headings, SRS consistency, code lint/test/QA if affected, current commit SHA and output diff. Keep docs-only PR separate from runtime optimization.

**Suggested retention (not enacted):** PASS temporary traces 7–14 days, FAIL investigation traces 30–90 days or until issue disposition, release metadata/hashes and approved evidence as required by project policy. The actual period must be approved and checked against artifact privacy/size constraints before any deletion is scheduled.

## 4. .gitignore extension

The source already ignores `.data/`, `test-results/`, `playwright-report/`, `*.mp4`, `*.wav`, `*.sqlite3*`, models and common Python/JS caches. Add *specific* profiler/coverage/log masks rather than blanket `*.json`/`*.yaml` which would hide provenance, fixtures and config. Ignore ≠ delete; retain evidence under access-controlled storage.

## 5. Open PRs that must remain untouched by hygiene

- [#21](https://github.com/qualife1291/Auto-Tool-Video/pull/21): `docs/agent-workboard.md`, `docs/development-plan.md`, `AGENTS.md` and research files.
- [#23](https://github.com/qualife1291/Auto-Tool-Video/pull/23): `.agent/handover/LATEST.md` plus dated handover.
- [#18](https://github.com/qualife1291/Auto-Tool-Video/pull/18): `.github/workflows/qa-multi-pr-integration.yml`.
- [#8](https://github.com/qualife1291/Auto-Tool-Video/pull/8): A04 audio and its dedicated test/workflow.
- [#4](https://github.com/qualife1291/Auto-Tool-Video/pull/4) / [#7](https://github.com/qualife1291/Auto-Tool-Video/pull/7): provider research docs.

After merges, BA does a new owner-coordinated status-sync; this document is not that status sync. Maintainer must re-query live GitHub state, since this is a dated snapshot.
