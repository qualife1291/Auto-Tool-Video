# Prompting Playbook → Auto-Tool-Video: evidence-backed improvement assessment

> **Research proposal only — not a task assignment, implementation approval, QA PASS, creator approval or release.**
> **Requested by product owner:** 2026-10-31, BA01 + BA02 to review jointly, synthesize priorities, plan approved pilot and coordinate later implementation.
> **Issue:** [#80](https://github.com/qualife1291/Auto-Tool-Video/issues/80)
> **Repository:** `qualife1291/Auto-Tool-Video`, branch `feat/short-video-studio`
> **Source audit SHA:** `fd99764d738d0c16d0a2b60298bc123d3572fb0c`; freshness checked at `737179432bcdc2adc9822208498ea5efd24f6f60`.
> **Freshness caveat:** GitHub compare reported 26 newer commits and modified paths only in the C02 web caption-preview/domain and related research files; the inspected backend AI modules did not change in that range. Recheck head/PRs before any code claim or merge.
> **Validation:** static code and docs read through connected GitHub. No local git clone, live Ollama inference, full pytest/Playwright, video render or benchmark executed by this assessment; results are NOT RUN.

## 1. Executive decision request

BA01 and BA02 should distinguish three concepts:
1. **Existing constraints** (preserve): provider loopback boundaries, no tools/shell for storyboard planner, strongly typed JSON, source-index binding, review-before-apply, optimistic revision and idempotency, technical media QC and creator review.
2. **Verified design gap:** model validation errors are not returned in structured detail to the retry step, and the single-call storyboard path has no independent semantic quality eval suite.
3. **Hypotheses pending measurement:** long multi-scene beat output may exceed token budgets; staged planning or bounded targeted repair could improve quality/cost; a semantic evaluator could catch cross-scene contradictions before render.

**Recommendation:** approve an EVAL-ONLY baseline investigation first, then a small reversible, experiment-controlled repair path. Do not introduce a generic multi-agent framework, paid model, new runtime provider or auto-merge process just because the talk describes them.

Inspired by [The Prompting Playbook (Anthropic/Claude talk)](https://www.youtube.com/watch?v=G2B0YWuJUgI): eval cases first; distinguish prompt behavior from capability/tool limits; hard outputs and controlled context; and Generate → Evaluate → Repair. These are proposed applications, not claims that Anthropic endorsed this architecture.

## 2. Audit map: existing source / evidence / classification

| Component | Evidence at audited SHA | Verified current design | Opportunity / caution |
| --- | --- | --- | --- |
| `backend/auto_tool_video/planning.py` | [source](https://github.com/qualife1291/Auto-Tool-Video/blob/fd99764d738d0c16d0a2b60298bc123d3572fb0c/backend/auto_tool_video/planning.py) lines 17–33, 59–85, 106–223 | Pydantic ProposedScene/Proposal, constant SYSTEM_PROMPT; validates source chunk coverage, scene durations, beat ordering; compatibility fallback marked `needs_review` | Add granular diagnostics before any semantic judge; clean/structure and version prompt only after baseline |
| `backend/auto_tool_video/generation.py` | [source](https://github.com/qualife1291/Auto-Tool-Video/blob/fd99764d738d0c16d0a2b60298bc123d3572fb0c/backend/auto_tool_video/generation.py#L169-L190) | Two attempts max; second attempt adds generic `Previous output failed validation...`; checks model identity | Bounded structured repair with explicit rule/path/scene rather than generic full regenerate |
| `backend/auto_tool_video/providers.py` | [source](https://github.com/qualife1291/Auto-Tool-Video/blob/fd99764d738d0c16d0a2b60298bc123d3572fb0c/backend/auto_tool_video/providers.py#L116-L125) | Ollama JSON Schema `Proposal.model_json_schema()`; `think=False`, `num_predict=4000`, `num_ctx=8192`; loopback-only transport | Benchmark token/time pressure, do not infer model quality from contract tests |
| `backend/auto_tool_video/domain.py` | [source](https://github.com/qualife1291/Auto-Tool-Video/blob/fd99764d738d0c16d0a2b60298bc123d3572fb0c/backend/auto_tool_video/domain.py) | `CreativeBrief`, `SecondBeat` (visual_state/action/camera/on_screen_text/narration_cue/continuity), `Scene`, 5 profile types | Reuse strict domains; avoid duplicating schema in evaluator |
| `backend/auto_tool_video/api.py` | [source](https://github.com/qualife1291/Auto-Tool-Video/blob/fd99764d738d0c16d0a2b60298bc123d3572fb0c/backend/auto_tool_video/api.py) | plan, apply, image endpoints; revision and confirm apply; local origin checks | No silent acceptance or mutation from AI evaluator |
| `backend/tests/test_ai.py` | [source](https://github.com/qualife1291/Auto-Tool-Video/blob/fd99764d738d0c16d0a2b60298bc123d3572fb0c/backend/tests/test_ai.py) | Mock provider contract, retry, source fidelity, bad output, security, cancellation tests; explicit note mocks ≠ live quality | Add eval fixture set & optional live-model evidence separate from contract tests |
| `backend/auto_tool_video/quality.py` | [source](https://github.com/qualife1291/Auto-Tool-Video/blob/fd99764d738d0c16d0a2b60298bc123d3572fb0c/backend/auto_tool_video/quality.py) | Post-export FFmpeg/PTS/audio/scene signals, review decision and creator feedback | Reuse report concepts but DO NOT conflate model-based pre-render warnings with media QC/human approval |
| `apps/web/src/CreativePanel.tsx` | [source](https://github.com/qualife1291/Auto-Tool-Video/blob/fd99764d738d0c16d0a2b60298bc123d3572fb0c/apps/web/src/CreativePanel.tsx) | Shows proposal, fact flags, explicit review checkbox, apply action | Later optional per-scene diagnostics and regenerate; preserve creator choice |
| `docs/qa-evidence-gates.md` | [source](https://github.com/qualife1291/Auto-Tool-Video/blob/fd99764d738d0c16d0a2b60298bc123d3572fb0c/docs/qa-evidence-gates.md) | Exact-head/merge-ref/test/media/creator gates G0–G11 | Never convert eval pass into G10 or release approval |
| `scripts/dev_harness_contract.py` | [source](https://github.com/qualife1291/Auto-Tool-Video/blob/fd99764d738d0c16d0a2b60298bc123d3572fb0c/scripts/dev_harness_contract.py) | Optional offline issue task-contract lint; cannot validate live GitHub claims by itself | Separate developer/SDLC harness from product storyboard eval pipeline |

## 3. Architecture and failure classification

Current product flow (already implemented, approximate):
`CreativeBrief/Source → Ollama JSON generation → validate_proposal → generic one retry on MODEL_OUTPUT_INVALID → candidate proposal → explicit creator review/apply → media render → technical QC → creator G10`.

Proposed pilot product flow (NOT implemented):
`Input snapshot → Prompt version → Generate → deterministic structural checks → structured, bounded repair if eligible → optional semantic warning evaluator → explicit creator review/apply → unchanged render + QC + G10`.

A **deterministic failure** is a clear violation of schema/source IDs/beat index/duration/revision and must be decided by Python, not LLM. **Semantic weakness** (continuity, pedagogy, plausible physical changes, image prompt feasibility) gets separate evidence and, where relevant, human review. **Provider/capability failure** (timeout, unfinished output, unavailable model) does not automatically justify more prompt tweaks. Never repair invalid `preserve` data by changing original narration, bypassing validation, or widening output limits without evidence.

### Example machine-readable repair error (illustrative, not current API)

```json
{
  "error_code": "BEAT_COVERAGE_INVALID",
  "scene_index": 2,
  "field_path": "scenes[2].second_by_second",
  "expected_seconds": [0, 1, 2, 3],
  "observed_seconds": [0, 1, 2],
  "repair_scope": "scene_only",
  "preserve_narration": true
}
```

Proposed safeguards: max **one targeted repair candidate for the pilot** (further retries require measured approval); preserve pristine original output/source as hash; never expose sensitive user data to public CI logs; if repair fails, mark failed with explainable diagnostics, do not silently produce plausible but wrong data. Repair generation must still run the **same full hard validators** before returning a candidate.

## 4. PPL backlog and impact/effort/risk

| ID | Priority (provisional) | Change to consider | Files likely to touch later (read-only here) | Cost/risk | Decision gate |
| --- | --- | --- | --- | --- | --- |
| PPL-01 | P1 | Fixed storyboard eval dataset (mock and optional local live tier) | NEW `backend/tests/fixtures/storyboard_eval/`, NEW `scripts/eval_storyboard.py`, test file | FREE if existing tools; running local models consumes compute; quality test labels require manual audit | Baseline report and stable deterministic tests before prompt edits |
| PPL-02 | P1 | Structured validation failures → bounded scene repair | `planning.py`, `generation.py`, focused tests | Moderate code complexity, token/latency increase | No source corruption, no false PASS, RED→GREEN and rollback |
| PPL-03 | P1/P2 | Prompt parts + version hash/registry | NEW `backend/auto_tool_video/prompts/`, `planning.py` | Risk of output behavior drift; version migration and prompt injection surface | A/B baseline equivalence and repeatable prompt digest |
| PPL-04 | P2 | Outline → scenes → second-by-second staged candidate | `generation.py`, `planning.py`, provider adapter | More model calls, possible slower/less reliable; unknown benefit | Side-by-side live eval and latency/token/resource budget |
| PPL-05 | P2 | Pre-render semantic QA/warning evidence | NEW evaluator module and optional UI | False positives, over-trust AI judge, cost | Independent labeled set, confusion matrix and no G10 bypass |
| PPL-06 | P2 | Privacy-safe observability for LLM calls | job provenance, provider metadata/structured event | Sensitive prompts/log leaks; storage | Hash-only prompt provenance, redaction and ZERO external egress |
| PPL-07 | P2 | UI per-scene explanation / targeted regenerate | `CreativePanel.tsx`; Playwright | State and revision races, accessibility | Cross-viewport E2E, cancellation, idempotency and no silent apply |
| PPL-08 | Existing | Align role/task/QA governance + SDLC harness | **Already owned** by #38/#49/#75/#46/#51; NO new conflicting edits | Concurrency / document conflicts | BA reconcile existing issues and primary QA_OWNER |

**Important coordination:** The code and docs paths in this table are *future candidate paths*, NOT claimed ownership. Before BA creates implementation tasks, inspect newest open PRs and reserve exclusive scope. In particular, `planning.py`/`generation.py` can be independently researched but must not be concurrently modified by two coders.

## 5. Evaluation specification: proposed test suite

### 5.1 Fixed data / categories
Starting proposal: **at least 30 unique frozen cases**, not a claim they already exist. Include:
- **Control (6):** straightforward 12/30/45/60s briefs, simple factual story, 9:16 and 16:9.
- **Source preservation (6):** Vietnamese Unicode, double spaces/newlines, repeated clauses, omitted/duplicated/reversed source IDs, source data injection.
- **Timeline (6):** scene duration fractional seconds, 20s/60s limits, invalid beat sequence, empty beat fallback marked `needs_review`, staleness on retime, audio-driven timing.
- **Semantic/temporal (6):** one object wet→dry, scene-to-scene transition, character bible, contradictory visual actions, static-vs-motion intent, causality.
- **Capability/boundary (6):** unsupported scientific claim, missing brief sources, provider timeout/truncation, oversized JSON, off-topic instructions in source, contradictory directives.

These are **counts for pilot design only**, not observed cases. Coverage matrix must track age profile, mode, duration and aspect without claiming full Cartesian coverage from 30 cases. Prefer reproducible original Vietnamese scenarios and source hashes.

### 5.2 Metrics / evidence contract
- **Hard contract pass** = valid JSON and Pydantic, valid IDs, source fidelity, duration/beat coverage, revision/cancel/idempotency; report case ID, observed/expected and exact exception/status.
- **Semantic score** = independent human-rubric agreement / known contradictions; model judge score is optional diagnostic, never sufficient alone.
- **Reliability** = first-try success, repair-try success, total failure, escaped regressions; do not report historical benchmark counts as current.
- **Resources** = model/digest, prompt SHA, output tokens *only when actually reported*, wall latency, retries, CPU/RAM/VRAM optional; report N/A otherwise.
- **Evidence** = immutable case IDs, input hash, date, current source/head SHA, exact CLI command, environment, results and sanitized output artifacts. Never upload narration, credentials, full raw traces/DOM or unpublished images in public CI artifacts.
- **Stop rule** = no automatic rollout if a hard invariant regresses, false PASS is observed, privacy leak occurs, retry loop unbounded, model switching undetected, or tests lack evidence.

### 5.3 Run-tier distinction
- Tier A: offline mocked provider + deterministic structural tests; suitable for normal CI.
- Tier B: *opt-in* locally available model smoke on fixed non-private fixtures; status **NOT RUN** when Ollama/model absent.
- Tier C: creator perceptual review on final actual audio/video and licensed originals (G10); no replacement by Tier A/B.
No new paid SaaS, network provider dependency or required GPU is approved by this note.

## 6. Planned experiment, acceptance and rollback

**Phase 0 — BA review (no code):** BA01/BA02 reconcile #26 release blockers, #75 documents, #38 Dev Harness and #49 research; decide ADOPT/MODIFY/DEFER/REJECT per PPL ID; capture date, canonical SHA and constraints. Optional compare technologies only if directly needed.

**Phase 1 — Eval baseline only (candidate ~3–5 SP):**
- Freeze dataset, spec and labeling policy; independent tester reviews sample quality.
- Run deterministic tests on current canonical and optionally Tier B.
- Publish red/green counts and per-category failure patterns; initial target is **no false hard PASS** across declared cases, not promise of universal correctness.
- Keep production code unchanged.

**Phase 2 — Controlled repair (candidate ~3–5 SP):**
- Add typed `ValidationFinding` (rule, path, scene, safe expected/actual), no raw private prompt in log.
- Retry once for eligible model-structure errors only; cancellation/timeouts/identity change remain failures; run final validations and reject unsupported edits.
- Compare baseline vs candidate on identical fixture inputs + model digest, with fixed budget and explicit treatment of non-determinism.
- Switch defaults only after independent QA and BA acceptance; flag option/backwards-compatible behavior as needed.

**Phase 3 — Prompt refactor / staged-planner PoC (candidate ~2–5 SP each):**
- Prompts as structured role/policy/data/output sections, hashes; no magic XML claim.
- Measure single-pass versus outline→scene→beat on the same tasks; if overall quality/cost/latency does not improve, reject/defer.
- Preserve original, simpler path as rollback.

**Phase 4 — Optional pre-render warnings and UX (P2):**
- Present scene/beat locations, warning rationale, human review button and no automatic apply.
- Test failure, cancellation, stale revision, source changes, accessibility; label semantic uncertainty.
- Technical media QC and creator G10 remain independent and unchanged.

**Indicative evaluation thresholds for BA to approve, not observed results:** preserve-mode source coverage 100% on all declared hard fixtures, 0 swallowed invalid-output errors, no test bypass, no auto-apply, zero secret leakage; candidate semantically better than baseline *under independent labeled comparisons*, and total time/token use within BA-approved compute budget. BA should define acceptable quality gain and latency caps based on measured baseline, not invent percentage improvements.

**Rollback:** delete/revert isolated candidate changes (prompt/repair/staged feature), restore current `prompt_messages` + two-attempt validation behavior and existing schema, rerun entire CI/QA matrix; do not discard bug reproduction evidence, approved projects, media hashes or prior review statuses.

## 7. Multi-agent / governance handoff

- **Coordination:** BA01 = BA02, see [registry #31](https://github.com/qualife1291/Auto-Tool-Video/issues/31), [BA02 registry #72](https://github.com/qualife1291/Auto-Tool-Video/issues/72). They own review, requirement/spec alignment, project priorities and assignment; this research note does not impersonate either BA.
- **Coder roles:** C01–C05; BA-assigned issue, isolated branch, personally CLAIM (GitHub login is not seat identity), exclusive paths, base SHA, explicit AC/test/evidence, Draft→Ready for Review. No self-merge.
- **QA roles:** T01/T02 share independent QA and eligible merge authority; designate **one primary QA_OWNER per PR**, other may independently cross-check, record exact head + merge-ref CI and post-merge result. G10 creator approval is separate.
- **Do not duplicate existing work:** [#26 release Epic](https://github.com/qualife1291/Auto-Tool-Video/issues/26), [#38 SDLC Dev Harness](https://github.com/qualife1291/Auto-Tool-Video/issues/38), [#49 / PR #65 H1 evidence](https://github.com/qualife1291/Auto-Tool-Video/pull/65), [#75 docs reconciliation](https://github.com/qualife1291/Auto-Tool-Video/issues/75), [#36 creator QA](https://github.com/qualife1291/Auto-Tool-Video/issues/36).
- **Current documentation caveat:** canonical `docs/agent-role-charter.md` in the audited snapshot still contains stale C01/C02 and T01-only role language; #75 tracks the existing fix and several open PRs own affected files. This document deliberately edits NONE of those files.
- **Cost:** existing offline tests = free software; local inference still uses electricity/hardware. SaaS/free tier costs and rights cannot be assumed. No paid service, third-party skill/plugin or cloud publishing authorized.
- **Handoff artifact expected from BA:** a decision table, ordered roadmap with dependencies, explicit task contracts and owners, eval dataset acceptance, independent QA routing, effort/benefit/rollback, and issue links. A new user approval is required for any paid/cloud-sensitive capability or unauthorized scope change.

## 8. Exact commands BA may request from an implementation owner (NOT RUN here)

```bash
git fetch origin feat/short-video-studio
git rev-parse HEAD
git status --short
uv sync --project backend --frozen --group dev
uv run --project backend ruff check backend scripts
uv run --project backend ruff format --check backend scripts
uv run --project backend mypy backend/auto_tool_video
uv run --project backend pytest backend/tests -q
npm --prefix apps/web run check
npm --prefix apps/web run build
npm --prefix apps/web run test:e2e
```

If model not installed, new optional live-eval commands are **NOT RUN**; no silent mocked-live substitution. Exact head/merge-ref/postmerge checks, full dual-aspect media regression if applicable and creator G10 remain controlled by approved QA gates.

## 9. BA decision form (to complete via issue #80)

| PPL item | Adopt / Modify / Defer / Reject | Why / value / risk | Dependency / scope owner | Allowed cost | Next action |
| --- | --- | --- | --- | --- | --- |
| 01 Eval suite | TBD | | | | |
| 02 Structured repair | TBD | | | | |
| 03 Prompt registry | TBD | | | | |
| 04 Staged planner | TBD | | | | |
| 05 Semantic QA | TBD | | | | |
| 06 Observability | TBD | | | | |
| 07 UI diagnostics | TBD | | | | |
| 08 SDLC docs/harness | TBD (existing issues) | | | | |

**Status legend:** RESEARCH PROPOSAL → BA REVIEWED → APPROVED TASK CONTRACT → CLAIMED → CODE/PR READY → T01/T02 QA PASS-CODE → MERGED/POSTMERGE → CREATOR G10 (when needed). No stage is implied by having created this document.
