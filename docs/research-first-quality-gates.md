# Research-first feature development and quality gates

Status: proposed process / not an implementation or release approval.
Canonical base: `feat/short-video-studio`. Owner: integrator. Updated: 2026-10-30.
Applies to all new features, AI providers, render engines, refactors and significant dependencies; A01–A10 retain their existing owners and acceptance criteria.

## Mandatory gate sequence

**G0 — Scope and ownership.** Read `AGENTS.md`, `AGENT-CODING-STANDARD.md`, approved spec, workboard, handover, development plan, video quality standard and affected code/tests. Check open PRs, claim a unique task ID, identify owned paths and conflicting work. Branch from the current canonical base. No shared-file edits without coordination.

**G1 — Evidence-based research BEFORE feature code.** Submit a research note under `docs/research/<feature>.md` with: user problem and measurable success; current implementation and exact file/contract map; at least two alternatives (including keeping current approach); official upstream docs, exact version/commit and license (code, weights, assets separately); hardware/OS and dependency compatibility; security/privacy/credential and network implications; cost/quota and offline fallback; failure modes; known unknowns; citations with retrieval dates. For UI changes, provide accessibility and mobile-safe-zone review; for AI, explain reproducibility, prompt/data provenance, hallucination and manual approval. No unverified marketing claims.

**G2 — Architecture and decision record.** Compare options by quality, maintainability, integration complexity, performance, privacy, license, total cost and reversibility. Identify schema/API migrations, backwards compatibility, feature flags, opt-in and rollback. Record a go/no-go decision and update or create an approved feature spec before implementation when scope changes. A researcher does not approve their own risk exceptions.

**G3 — Isolated proof of concept.** Use a disposable branch/sandbox and fixed fixtures, never replace the production renderer. Pin upstream versions and model digests. No arbitrary generated code execution in the backend process. Do not download weights, install unreviewed dependencies, call paid APIs or publish externally without explicit authorization. Record actual commands, exit codes, machine specs, seeds, artifacts and hashes. If execution is unavailable, write `NOT RUN`, never `PASS`.

**G4 — Implementation and automated verification.** Define contract tests, boundary/negative cases, migration/legacy tests, cancellation/retry/idempotency, resource caps, input validation, security, error propagation and deterministic fixtures. Run Python lint/typing/pytest, frontend typecheck/Vitest/build/format/Playwright, and relevant real FFmpeg export checks. CI must be green on the exact PR head. A test on another commit is not proof.

**G5 — Video/audio/creator quality.** For output-affecting features render both 1080x1920 and 1920x1080 at 30fps. Check full decode, H.264/yuv420p, PTS/CFR, A/V drift <=100ms, AAC48kHz, integrated loudness -16 +/-1 LUFS, true peak <=-1 dBTP, silence and subtitle safety. Measure visual continuity, flicker, ghosting, object movement, prompt/fact alignment and voice intelligibility; attach contact sheets and timestamped findings. Creator must watch/listen to the exact SHA256 artifacts and score all rubric categories >=4/5 with no critical issues. Machine QC is not creator approval.

**G6 — Review, merge and post-merge regression.** PR must link G1–G5 evidence and state failures, skips, limitations, provenance, licenses, rollback and touched paths. Independent reviewer/integrator checks evidence and conflict with active agents. Merge only when applicable gates pass; otherwise keep draft/blocked. Integrator reruns regression on the merged commit, updates workboard/handover, and leaves release status pending until artifact and human approval.

## Research report template

- Feature/task ID, owner, branch, base SHA, scope and affected paths
- User problem; measurable baseline; proposed improvement; non-goals
- Current architecture/contracts; compatibility risks; active PR overlaps
- Candidate A/B/current baseline; official source URLs and access dates; exact version/license
- Comparative scorecard with evidence and explicit unknowns
- Security, privacy, credentials, license, costs, quotas, hardware and offline behavior
- Test matrix: happy, negative, adversarial, concurrency, rollback, accessibility, media
- Prototype commands/environment/exit codes, input/output hashes, observed results (or NOT RUN)
- Decision: GO / RESEARCH MORE / NO-GO; reviewer; approved spec reference
- Follow-up, ownership and merge criteria

## Quality measurement framework

Keep separate measurements, not a single uncalibrated quality score:

1. **Correctness:** contract pass/fail, factual alignment, storyboard continuity, migration preservation.
2. **Video technical:** dimensions, 30fps PTS/CFR, frame count, full decode, codec, duration, visual crop/legibility.
3. **Audio:** 48kHz AAC, LUFS/truepeak, silence, missing words, vi-VN WER/CER with manually corrected ground truth, cue alignment.
4. **Visual/perceptual:** near-repeat with intentional hold labels, flicker, ghosting, temporal identity, motion clarity, phone-size readability, physical plausibility.
5. **Performance/reliability:** render time/finished second, median and p95 from >=5 comparable runs after warm-up, peak RSS/VRAM, CPU/GPU, disk, cancel/retry/restart success.
6. **AI/provider:** prompt adherence, seeds/model digest, quality per accepted output, failure rate, latency, price, quota, privacy and license.
7. **Security and accessibility:** dependency audit, sandbox/file path traversal, untrusted media, consent, 390px/mobile and keyboard/axe.
8. **Human acceptance:** rubric 1–5 on exact hashed video; no critical issue; warnings acknowledged. Human assessment cannot be replaced by learned metrics.

Do not report VBench/AIGCBench, ASR quality, hardware benchmarks or live-provider results as executed unless actual reproducible logs and artifacts exist. Compare engines using the same storyboard, narration, duration, aspect, fonts and scoring protocol; report differences and confidence intervals rather than cherry-picking best runs.

## Proposed extension backlog (not claimed or started)

| ID | Priority | Dependency | Research/POC deliverable | Merge gate |
|---|---|---|---|---|
| A11 | P0 | none | This governance and quality measurement plan; agent research-first template | Docs reviewed; no runtime changes |
| A12 | P0 | A02–A04, A05 coordination | Reproducible benchmark harness, fixture manifest, real dual-aspect export and CI smoke | Evidence on exact commit; full render separately |
| A13 | P1 | A12 | Procedural Animate feasibility, code/license audit, 3-scene sandbox, both aspect ratios | Visual/human QA and security; no direct runtime import |
| A14 | P1 | A12, A13 | Versioned render-engine interface/scene compiler; rollback and legacy compatibility | Contract, migration and E2E pass |
| A15 | P1 | A04, A12 | Vietnamese forced alignment/faster-whisper evaluation, corrected WER/CER and SRT timings | Human voice checks, offline model licensing |
| A16 | P1 | A12 | Orchestration research (OpenMontage as reference only), approval/retry/provenance/cost model | Isolated prototype, no AGPL code copying without legal review |
| A17 | P2 | A12 | Optional learned temporal/semantic benchmark research and calibration against humans | Model license/hardware and false-positive study |
| A18 | P2 | A14, A06–A08 | AI video provider and character-consistency reference workflow | Opt-in, consent, cost cap, license and live evidence |
| A19 | P2 | A14 | OpenCreator-inspired editor/UX research, without framework migration | Accessibility, persistence and mobile E2E |

These are proposals, **not claims of ownership**. A01–A10 remain canonical and are not superseded. The integrator must register new IDs in the workboard before agent implementation, verify active PRs and avoid concurrent writes to the same files.

## FPS, resolution and performance research

See [high-FPS/sharpness/performance/QC research](high-fps-performance-qc-research.md), which inventories current 30fps contracts, proposes rational FPS migration and native 60fps proof, encoder/streaming experiments, 4K/interpolation gates and benchmark/QC. All A34–A42 remain unclaimed; research revalidation and real dual-aspect outputs mandatory before any code implementation.

## Future multi-format research

See [future video formats research](future-video-formats-research.md) for 15 format families, Scene IR and renderer contracts, benchmark protocol and proposed A20–A33 backlog. Every future agent must independently refresh official documentation and reproduce quality measurements before proposing implementation. Backlog entries are not approvals.

## Performance, cost and plan verification

Read [performance/cost optimization dossier](performance-cost-optimization-research.md), [plan readiness audit](research-plan-audit-2026-10-30.md) and the dedicated [performance-cost-review skill](../.agents/skills/performance-cost-review/SKILL.md). Cross-stage observability, cache correctness, web preview, provider costs, tiered CI, energy/RAM and accepted-minute costs are mandatory research considerations for future feature specs. A43–A48 and cinematic millisecond-schema A49 are proposed only and require workboard ownership and approved specs. No quality gate can be traded for a speed improvement.

## Immediate sequencing

- **Now:** Finish A02/A03/A04 and A05 real export acceptance. A06/A07 may research independently. Add this research gate to agent onboarding.
- **Next:** A12 benchmark harness and fixture manifest, on a dedicated branch coordinated with A05.
- **Then:** A13 isolated Animate POC and A15 alignment research in parallel, provided file ownership does not overlap.
- **Later:** A14 adapter only after POC evidence; A16/A17/A18/A19 remain research-first until prerequisites pass.

**Stop conditions:** unapproved spec change, unclear license, unauthorized network/paid action, overlapping ownership, missing real tests, new critical perceptual defects, nonreproducible result or incomplete rollback. Record BLOCKED and request integrator decision; do not silently weaken QC.
