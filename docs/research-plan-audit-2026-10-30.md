# Independent audit of research and implementation readiness — 2026-10-30

**Audit scope:** GitHub canonical `feat/short-video-studio` source/roadmap/workboard/spec/CI/quality documents and documentation-only draft PR #21 research dossiers, plus open overlapping PRs. **Document review and source code inspection only.** This audit does not establish test pass on new FPS/engines or user approval. On canonical branch, PR #21 has **not merged** as of this review.

## Outcome

**Verdict: RESEARCH COVERAGE STRONG; IMPLEMENTATION PLANNING PARTIAL; ACCEPTANCE EVIDENCE BLOCKED.**

A01 current contract verified on earlier CI. A02–A05 and new integration testing are in active open PRs or blocked by assets/review; the 30fps 38.7-second sample is a historical baseline, not current release acceptance. Docs have broad ideas and credible safety gates, but do not yet supply production-ready specifications, executable quantitative fixtures, sampled measurements, allocations/owners and cost budgets for each proposal. A11–A48 are **future proposed IDs**; listing them does not assign work or authorize a coding agent to edit shared code.

## File-by-file evidence audit

| Source | Strength already present | Gap / severity | Required closure and owner |
|---|---|---|---|
| `docs/source-review.md` + `source-snapshot.json` | 29 repo / 8 model card / 12 Remotion skill snapshots recorded previously; code vs weights, license, hardware and provenance; local-first | **MEDIUM:** static access date; provider/model costs and compatibility change; upstream benchmarks not ours | Researchers refresh URLs, exact commits, licenses, runtime/model digest and confirm official API on task G1; run real POC |
| `docs/research-first-quality-gates.md` | G0–G6, research alternatives, sandbox, quality gates, rollback and human acceptance | **HIGH:** not merged; no enforceable PR template/checklist or outcome artifact yet | Integrator approves/merges process PR; then consider repository PR template/check or review labels without blocking existing agents |
| `docs/future-video-formats-research.md` | 15 content families, Scene IR, render adapters, A20–A33 dependency table and hard-stop | **HIGH:** format specs incomplete (exact scene attributes per style, platform profiles, device/performance budgets, fixtures/quality scorecard); no POC | A20 jointly with A14 drafts versioned schema/format matrix, migration and typed validators; A12 fixes reference fixtures |
| `docs/high-fps-performance-qc-research.md` | 30fps code audit, rational timebase, native60, interpolation gates, A34–A42, dual-aspect QC | **HIGH:** no real 60fps/video benchmark or tool availability matrix; no measured memory budget and no automated commands in dossier | A12/A34/A36/A41 publish environment+artifact manifests and run real tests before any implementation approval |
| `docs/video-quality-standard.md` + `qa-review.md` | 30fps hard codec/PTS/audio/decode, creator approval rubric, warning limitations, historical real MP4 evidence | **HIGH:** current head and multi-PR merge not yet new dual1080 human-approved; CI main workflow no required full media export | A05 and integration reviewer own exact-SHA QC, separately creator watch/listen; do not substitute tests from another commit |
| `.agents/skills/video-quality-review/SKILL.md` | Detailed human+technical quality review instructions | **MEDIUM:** not a dedicated performance profiler/cost/CI cache protocol | Add optional `performance-cost-review` skill; do not change existing QA skill's owner |
| `specs/whiteboard-video-tool.md` | Approved current product boundaries, code rights/CI and review definitions | **HIGH:** generic future features are not approved implementation specs | Each agent derives a narrow approved/spec RFC before code; no implementation from this research dossier alone |
| `docs/agent-workboard.md` | A01–A10 ownership, precise active acceptance and CI references | **HIGH:** future A11–A48 not actually claimed or synced after PR merge; open PR workload changes frequently | Integrator registers exact owner/file surface and issue/PR; compare current base SHA and open PRs before branch |
| `docs/development-plan.md` | M1–M4 and long-term roadmap | **MEDIUM:** text still says `A01–A03 WIP-UNTESTED` although A01 marked DONE-VERIFIED on workboard; source chronology ambiguous | Fix A01 label in docs-only PR. Do not mark unmerged A02/A04 PR code DONE on canonical |
| `.github/workflows/ci.yml` | Ruff/mypy/pytest/Vitest/build/Playwright, uv+npm cache | **HIGH:** no mandatory exact-commit real dual-aspect voiced 1080p regression; expensive test tiers not separately measured | A05/A12 and QA PR #18 own instrumentation and real media gates. Do not duplicate or overwrite active CI PR |
| Millisecond cinematography / screenplay | A01 has integer-second `SecondBeat` visual/action/camera/text/narration/continuity | **HIGH:** no formally approved millisecond/timecode scene schema for sound effects, lighting, environmental states, camera/lens, object IDs, audio sample sync; prior idea not implemented | Propose future A49 `cinematic timing + lighting/SFX IR research`, co-design with A20+A34; research only |
| `docs/performance-cost-optimization-research.md` | Stage profiling, tool comparison, cache/queue/UI/AI/CI experiments, A43–A48, stop gates | **HIGH initially:** new proposal lacks actual profiler run, source asset manifest/hardware and cost figures | A43/A12 collect real baseline before assigning numeric targets; do not claim savings from upstream README |

## Cross-task architecture conflicts and corrections

1. **A14 vs A20:** Adapter API and Scene IR **must be designed in one joint RFC** with schema version, timebase, capability negotiation, renderer fallback and migration. A14 must not design plugin interface that predates the A20 data contract.
2. **A12 vs A36 vs A43:** A12 owns fixtures/reference benchmark harness; A43 owns wall/resource span schema, source-cost accounting; A36 owns *optimization* experiments after profiler evidence. Avoid three incompatible metrics/report formats.
3. **A34 vs A04/A05:** FPS migration affects 48kHz sample count, timing/caption/PTS and A05 QC. Keep current 30fps unchanged until A05 verified; conditional 60fps POC in isolated branch.
4. **A41 vs A05 QA vs A47:** QA cost-tiering cannot relax exact-source human signoff. Cheap PR smoke, integration gate, nightly research gate and release/human gate have distinct evidence labels.
5. **A42 all A35–A41:** Scheduler research can begin after A12/A43 baseline; advanced resource-aware scheduler implementation should depend only on proven actual contention/need, not every optional interpolation/4K/AI feature finishing.
6. **A02/A03 and QA PR #18:** Active PRs #8 A04, #12 A02, #14 A05 QA, #18 multi-PR integration, #21 docs (plus open provider PRs and handover #23) may touch related paths/evidence. Never assume branch isolation alone prevents semantic conflict.
7. **SecondBeat metadata:** second-level plan is not a frame-level command, and `SecondBeat` currently lacks sound, lighting, physics and per-millisecond event clock. A49 is research only; do not mutate legacy scene data without dedicated approved spec.
8. **Single total quality score:** Reject score aggregation that compensates technical/copyright/science hard failure with better speed or VMAF. Keep separate Pareto frontier and creator gates.
9. **Training data and licensing:** Source-code license does not grant model weights/music/footage/character identity rights. License-refresh mandatory before running external code/model.
10. **Historical and PR-CI status:** Tests on an individual PR head or simulated multi-PR merge are not proof canonical merge has passed human QC. Require exact merged SHA and artifact hashes.

## Definition of a *fully detailed, agent-ready* future task

All 12 must be present; otherwise status RESEARCH MORE / SPEC BLOCKED:

1. **Problem and user-observable success** incl. scope and explicit non-goals.
2. **Real owner and file reservation** plus open PR/branch conflict check and parent SHA.
3. **Approved spec** with precise data types/timebase, integrations, migration/compatibility.
4. **References** official source URLs + version/commit/access date and code/model/data license.
5. **Alternatives** baseline vs at least 2 candidate solutions, decision rationale.
6. **Cost/resource forecast** hardware tiers, budget ceilings, local/cloud privacy, off/no-cost fallback.
7. **Deterministic fixtures** input hashes, script, voice/assets/fonts, target expected measurements.
8. **Executable commands** install (if authorized), test, sample render, QC, failure injection and benchmark.
9. **Objective gates** actual audio/video technical thresholds, no unreviewed breakage and measured performance deltas.
10. **Human gates** exact artifact SHA, timestamped creator review, no critical and all 1–5 rubric axes >=4.
11. **Security/failure/rollback** secrets/network, hostile assets, cancellation/retry, cache poisoning and recovery.
12. **Evidence + integration** run IDs/exit codes, cold/warm data, independent review, merged-SHA repeat and post-merge handover.

Research evidence (source inspection) satisfies neither runtime benchmark nor human review. Every feature spec should include a `requirements-to-test` matrix mapping each requirement to a test/QA artifact owner, with link or `NOT RUN`. For new models/plugins, record runtime sandbox, model digest, memory/VRAM and licensing per weight separately.

## Research-to-implementation readiness scoring (process rubric, not video quality)

Score each dimension 0=missing, 1=described but not independently verified, 2=fully specified and backed by evidence. Do not infer numbers for individual future tasks not individually audited.

| Dimension | Current plan assessment | Main blocker |
|---|---|---|
| Strategic scope and formats | **2/2** | Clear long-range scope and non-goals; subject to future change |
| Alternatives/source references | **1/2** | Sources exist but some versions/licenses and assumptions need fresh validation |
| Component contracts + exact specs | **1/2** | Scene IR/renderer interfaces proposed, not agreed/migrated |
| Owner/PR conflict coordination | **1/2** | Rule exists; A11–A48 owners/claims not assigned |
| Benchmark fixtures + executable methods | **1/2** | Matrix exists; no reproducible A12 baseline on current combined head |
| Cost/resource ceilings | **0/2** | No actual hardware measurements or budget ceilings in canonical evidence |
| Runtime+human acceptance | **0/2** | No new accepted artifacts for proposed engines/FPS |
| CI/release enforcement | **1/2** | Existing tests + PR #18 in progress; no completed exact-head quality gate |

**Illustrative planning maturity 7/16**, not a certified score or estimate that the product is 44% complete. It is a process gap count (2+1+1+1+1+0+0+1=7), not derived from running video. Purpose: prioritize missing evidence, not encourage vanity scoring. Recalculate only with owner-signed evidence after merge.

## Priority remediation (no runtime edits in this PR)

- **Gate R0:** Integrator resolves active A02–A05 QA and PR #18 on exact head. Keep all future builds blocked until verified where applicable.
- **Gate R1:** A12 approves fixture pack and expected video/audio hashes; A43 records stage CPU/RAM/disk/latency baseline; acceptance method signed.
- **Gate R2:** A20 + A14 unify IR/renderer contract; A34 rational FPS and audio clock research co-designed; A49 storyboard ms specification co-designed, no immediate code.
- **Gate R3:** A44/A45/A46/A47 research only after fixture and ownership; choose first cheap change by measured dominant time/cost stage.
- **Gate R4:** Repeat same assets and exact source commit in ≥5 warm runs + cold case, blind quality review; test cancellation/disk full/cache corruption. Independent reviewer decides deploy/no-go.
- **Gate R5:** Update workboard, handover and roadmap **after merge and evidence**; cannot overwrite PR #23 handover changes during this docs PR.

## Open PR conflict snapshot

Queried open PRs on 2026-10-30; observed relevant #4 (NIM research), #7 (HF research), #8 (tempo), #12 (Blender art QA), #14 (A05 QA protocol), #18 (multi-PR integration), #21 (this planning PR), #23 (handover context). This is a snapshot; re-query at G0 and don't blindly trust it after time passes.

## Audit provenance and exclusions

- Checked canonical `docs/development-plan.md`, `docs/agent-workboard.md`, `AGENTS.md`, `specs/whiteboard-video-tool.md`, `docs/source-review.md`, `source-snapshot.json`, `docs/qa-review.md`, `docs/video-quality-standard.md`, `render.py`, `timing.py`, `quality.py`, `store.py`, `.github/workflows/ci.yml`.
- Checked PR #21 branch research dossiers `research-first-quality-gates.md`, `future-video-formats-research.md`, `high-fps-performance-qc-research.md`. Read current original `.agents/skills/video-quality-review/SKILL.md`.
- External sources checked 2026-10-30: Python profiler and benchmarking, FFmpeg, VMAF, diffusers, caching, React/Chrome and official GitHub Actions docs linked in the performance dossier.
- **NOT RUN:** local clone tests, CPU profiling, GPU benchmarks, 60fps/4K outputs, VMAF, media player playback or human signoff. PR docs changes need independent review and CI, and have not been merged into canonical.
