# Whiteboard Studio — AI Agent Workboard

Updated: 2026-10-31 · **Development-in-progress**, technical code merges ≠ creator-ready.

**Canonical branch:** `feat/short-video-studio`. All new agent tasks branch from it and submit PRs back to it. This document is the single source of truth for open task ownership, status and acceptance criteria. `.agent/memory/short-term/TASKS.md` is a brief index; `.agent/handover/LATEST.md` gives the latest evidence; `docs/development-plan.md` is the long-term roadmap.

## Latest verified handoff after T01 merged QA race fix — 2026-10-31

**Canonical code:** `ba58bc8e9b48abdfd327d97b14d3e620c6795ace` after independent T01 [PR #67](https://github.com/qualife1291/Auto-Tool-Video/pull/67) merge. C03 beat-persistence E2E test now waits for matching async PUT/save revision and verifies persisted GET; main/dual1080 CI on **merge SHA queued at audit**, so do not count merged-SHA PASS early. Prior `C03 #58 claim pending` entries below are historical.

| Role | Verified current role / task |
| --- | --- |
| **BA01** | Owns assignments, reusable role charter [PR #51](https://github.com/qualife1291/Auto-Tool-Video/pull/51) about TR01/C01–C05/Draft→Ready, **QA-BLOCKED** on old exact-head A04 E2E until integrated retest; [Epic #26](https://github.com/qualife1291/Auto-Tool-Video/issues/26). |
| **C01** | [#55](https://github.com/qualife1291/Auto-Tool-Video/issues/55) / [PR #63](https://github.com/qualife1291/Auto-Tool-Video/pull/63) peg-anchor art **Ready for review but old main CI FAILED at beat-persistence E2E**, must sync/retest with merged #67. |
| **C02** | [#57](https://github.com/qualife1291/Auto-Tool-Video/issues/57) / [PR #62](https://github.com/qualife1291/Auto-Tool-Video/pull/62) caption preview **Draft**, latest code integration tests ongoing. |
| **C03** | [#58 / PR #67](https://github.com/qualife1291/Auto-Tool-Video/pull/67) **QA-PASS-CODE / MERGED** `ba58bc8...`; [#49 / PR #65](https://github.com/qualife1291/Auto-Tool-Video/pull/65) research **Draft/paused**, may be reprioritized by BA01. |
| **C04** | [#44 / PR #47](https://github.com/qualife1291/Auto-Tool-Video/pull/47) Fit Audio **Ready but old main CI red from #58**, needs fresh integrated tests; [#61 / PR #64](https://github.com/qualife1291/Auto-Tool-Video/pull/64) imported frame-grid **Draft** at latest inspection. |
| **C05** | [#68 / PR #69](https://github.com/qualife1291/Auto-Tool-Video/pull/69) proposed science beats **Ready + three old-base HEAD CI green**, independent T01 **integration HOLD** until sync with #67 merged SHA and new combined CI. |
| **T01/T02** | T01 primary independent merge authority; T02 independent supplementary QA/test sharing, no implied release signoff. [#37](https://github.com/qualife1291/Auto-Tool-Video/pull/37) QA scenario FullHD artifact still strict-audio QC blocked; [#60](https://github.com/qualife1291/Auto-Tool-Video/pull/60) watcher fix Draft. Human creator review [#36](https://github.com/qualife1291/Auto-Tool-Video/issues/36) remains separate. |

**Gate:** Only coder-submitted non-Draft **Ready for review** PR with exact-current-base integrated CI, owned diff, complete T01 QA can merge; no old-SHA CI reuse. `QA-PASS-CODE` ≠ creator video approval. Earlier snapshot headings below are kept for history, not current assignments.

## Live role/task refresh — 2026-10-31 02:35 ICT (overrides older historical snapshots)

| Role | Current BA assignment / live GitHub status |
| --- | --- |
| **BA01** | Product/PM/Technology Scout; stable charter #45 merged, update [PR #51](https://github.com/qualife1291/Auto-Tool-Video/pull/51) adds TR01 proposal and C01/C02 workflow, but **A04 E2E failed, PR not merged**. |
| **C01** | Owner-reactivated [#52](https://github.com/qualife1291/Auto-Tool-Video/issues/52), BA-assigned peg motion [#55](https://github.com/qualife1291/Auto-Tool-Video/issues/55); [PR #63](https://github.com/qualife1291/Auto-Tool-Video/pull/63) **Draft**, main CI failed; no merge. |
| **C02** | Owner-activated [#54](https://github.com/qualife1291/Auto-Tool-Video/issues/54), BA-assigned caption preview [#57](https://github.com/qualife1291/Auto-Tool-Video/issues/57); [PR #62](https://github.com/qualife1291/Auto-Tool-Video/pull/62) **Draft**, CI ongoing; no merge. |
| **C03** | Harness [#48 / PR #56](https://github.com/qualife1291/Auto-Tool-Video/pull/56) **merged** at `980b7185b4cbcabf02d33edd1b4ba98ca9f89328`; urgent [Playwright issue #58](https://github.com/qualife1291/Auto-Tool-Video/issues/58) assigned/claim pending; P2 research [#49 / PR #65](https://github.com/qualife1291/Auto-Tool-Video/pull/65) paused/Draft. |
| **C04** | [P1-B #44 / PR #47](https://github.com/qualife1291/Auto-Tool-Video/pull/47) Ready for T01 but QA **BLOCKED** by #58 shared E2E failure; [P1-D #61 / PR #64](https://github.com/qualife1291/Auto-Tool-Video/pull/64) Draft. |
| **T01** | Independent QA/merge upon current-base exact-SHA PASS; [scenario #37](https://github.com/qualife1291/Auto-Tool-Video/pull/37) actual MP4 QC blocked, [GitHub watcher #59 / PR #60](https://github.com/qualife1291/Auto-Tool-Video/pull/60) Draft; creator feedback [#36](https://github.com/qualife1291/Auto-Tool-Video/issues/36). |
| **C05** | New [onboarding #66](https://github.com/qualife1291/Auto-Tool-Video/issues/66), awaiting BA01 reservation, not yet claimed an active task. |

**Required coder handoff:** `ASSIGNED → CLAIMED → DRAFT PR → SELF-TEST exact SHA → READY FOR REVIEW → T01 independent QA → QA PASS / FIX REQUESTED → T01 gated MERGE → postmerge CI → creator human approval`. Draft and pending/failed CI cannot be merged. GitHub identity and agent role ID are not interchangeable. Historical statuses below are evidence snapshots, not current assignments.

## VERIFIED CURRENT ASSIGNMENTS — 2026-10-31 (supersedes historical A01 snapshot below)

**[Stable agent role charter](agent-role-charter.md)** (BA01-owned) and **[current role/task responsibility, file ownership and QA gates](agent-role-task-contracts.md)** are mandatory before assigning or testing. Agent IDs: **BA01 coordinator/Product/PM/Technology Scout; C01, C02, C03, C04 are four active coder seats; T01 independent tester; human creator final perceptual reviewer**. Owner has newly activated [C01 #52](https://github.com/qualife1291/Auto-Tool-Video/issues/52) and [C02 #53](https://github.com/qualife1291/Auto-Tool-Video/issues/53); both AVAILABLE/UNASSIGNED with no code claims. Earlier retired aliases are historical. This workboard is a status index; for latest timing and exact SHA consult GitHub task issues/PRs.

| Priority | Workstream / official issue | Role owner | VERIFIED STATUS at this snapshot |
| --- | --- | --- | --- |
| P0 | A02 [#24](https://github.com/qualife1291/Auto-Tool-Video/issues/24) / [PR #34](https://github.com/qualife1291/Auto-Tool-Video/pull/34) | **C03** | CODE MERGED, CI/Blender technical PASS; creator physical motion review PENDING |
| P0 | A03 [#25](https://github.com/qualife1291/Auto-Tool-Video/issues/25) / [PR #35](https://github.com/qualife1291/Auto-Tool-Video/pull/35) | **C04** | CODE MERGED, caption/beat tests PASS; creator safe-zone/font review PENDING |
| P0 | A04 [#6](https://github.com/qualife1291/Auto-Tool-Video/issues/6) / [PR #8](https://github.com/qualife1291/Auto-Tool-Video/pull/8) | historical A04 lane, BA01 | CODE MERGED; 12-scene synthetic voiced dual FullHD PASS; approved narrator NOT RUN |
| P0 | A05 [#17](https://github.com/qualife1291/Auto-Tool-Video/issues/17), [#36](https://github.com/qualife1291/Auto-Tool-Video/issues/36) | **T01** | Independent QA ACTIVE, **creator final watch/listen and release BLOCKED** |
| P1 | P1-A [#29](https://github.com/qualife1291/Auto-Tool-Video/issues/29) / [PR #40](https://github.com/qualife1291/Auto-Tool-Video/pull/40) | **C04** | BUGFIX CODE MERGED (real RED→GREEN); manual UI test outstanding |
| P1 | P1-B [#44](https://github.com/qualife1291/Auto-Tool-Video/issues/44) | **C04** | BA ASSIGNED / CLAIM PENDING; `api.py::fit_audio` only + NEW test; old behavior not yet reproduced |
| P1 | P1-C [#41](https://github.com/qualife1291/Auto-Tool-Video/issues/41) / [PR #42](https://github.com/qualife1291/Auto-Tool-Video/pull/42) | **C03** | **CODE MERGED** at `97dfea49a712de2263648e187e08c4495098182b`; exact synced PR-head 335 pytest, 10 Vitest, 15 Playwright, FullHD+A04 PASS; merged-SHA CI and human quality gate separate |
| P1 | Four videos 12/30/45/60s [PR #37](https://github.com/qualife1291/Auto-Tool-Video/pull/37) | **T01** | TEST HARNESS OPEN / strict audio QC BLOCKED; no verified eight MP4 outputs |
| Research | FREE-first Harness [#38](https://github.com/qualife1291/Auto-Tool-Video/issues/38), iNew-style workflow [#39](https://github.com/qualife1291/Auto-Tool-Video/issues/39) | **BA01** | RESEARCH PROPOSAL only, no implementation assignment |
| Research/backlog | A06–A10 | BA01 for allocation | Provider licensing/free quotas research and future TTS/OAuth; not a deployed feature |

**Workflow:** BA01 issues AC/path reservation → Coder CLAIM+RED→GREEN+exclusive PR → T01 independent exact-HEAD & current-base CI gate → T01 may MERGE when fully PASS (user authorized) → postmerge CI → creator manual watch/listen exact file SHA → BA01 records feature/release approval. Missing mandatory evidence = `NOT RUN`/`BLOCKED`, never PASS. C03 only `jobs.py` enqueue + NEW export cap test on #41; C04 only `api.py::fit_audio` + NEW fit-audio cap test on #44; T01 owns scenario QA paths; no overlapping edits without BA01. For full evidence, see [quality gate matrix](qa-evidence-gates.md).

**Operational QA:** T01 hourly ChatGPT summary **always includes 3–6 manual test steps and verified media link or explicit NO BUILD**, plus rotating research or focused regression. GitHub T01 watcher is **15-minute cron/manual only** after spam hotfix [PR #43](https://github.com/qualife1291/Auto-Tool-Video/pull/43); do **not** re-add `workflow_run.completed` broad trigger.

### Historical workboard below (2026-10-30 baseline; NOT current assignments)

## Latest verified CI (A01)

[GitHub Actions run 41052656718](https://github.com/qualife1291/Auto-Tool-Video/actions/runs/41052656718), PR head `cb9b68bf`, merged in [PR #2](https://github.com/qualife1291/Auto-Tool-Video/pull/2) as `3354ca8e`:

- Ruff check and format pass; mypy pass (15 modules).
- Backend pytest **212 passed, 1 skipped**; TypeScript/Vitest **10 passed**; build/Prettier pass; Playwright Chromium **13 passed**.
- **235 tests passed, 1 skipped**, with one Starlette/httpx deprecation warning. CI verifies API/contracts and existing renderer/browser regressions, not a new generated MP4 or creator perceptual review.
- A01 is complete. A02/A03 remain **WIP pending dedicated visual and persistence acceptance**; A04/A05 remain pending audio and new full video QA.

## Project baseline and evidence

- **M1:** local 2D video editor and FFmpeg renderer for 9:16 and 16:9 at 1080p, SQLite project store, captions, audio, render QC, manual publish hub. Historical handover reports **182 pytest + 10 Vitest + 13 Playwright = 205 pass** and a **12-scene 38.7-second** video in both ratios. These results are *historical*, not rerun after the latest code changes.
- **M2:** Ollama planner + ComfyUI image adapter/candidate approval implemented; live-model end-to-end quality is **not verified**. Second-by-second storyboard validation, retiming and legacy save protection are **A01 DONE-VERIFIED**. Beat descriptions still do not drive the generic renderer automatically.
- **M3:** experimental VieNeu local TTS CLI and video QC; no finished TTS UI, forced alignment or SRT. Caption entrance motion and shirt wet/dry/sway/unfold code are **WIP-UNTESTED**. **0.92× pitch-preserving audio and new 41.9-second MP4 have not been produced or verified in Git.**
- **M4:** direct social OAuth/upload **not implemented**; manual upload only.
- Previous unpushed local agent work is unavailable through GitHub and has **not** been restored; the current edits are a new reconstruction from the user's description. Earlier preview/test evidence must not be attributed to the latest commit.

Status language: **DONE-VERIFIED** = current code passed recorded CI, **DONE-BASELINE** = evidenced on earlier commit, **WIP-UNTESTED** = committed but not verified, **TODO** = not implemented, **BLOCKED** = prerequisite/asset/human review missing. **Merging source into a branch changes none of these evidence statuses.**

## Workstreams — claim tasks through a PR

| ID | Priority | Area / primary files | Status | Immediate deliverable |
|---|---|---|---|---|
| A01 | P0 | Backend `domain.py`, `planning.py`, `api.py`, `store.py`, AI tests | DONE-VERIFIED | [PR #2](https://github.com/qualife1291/Auto-Tool-Video/pull/2) merged; strict 0-based beats, safe re-timing, legacy save, Unicode and conflict tests |
| A02 | P0 | `scripts/science_story.py`, Blender art, motion tests | WIP-UNTESTED | Review wet/dry mask blend, wind sway around fixed peg, fold→spread across both layouts |
| A03 | P0 | `render.py`, typography tests, `apps/web/src/{main.tsx,domain.ts}` | WIP-UNTESTED | Validate brief caption bounce, beat editing, persistence, safe zones, 390px/1080p/1920p |
| A04 | P0 | `scripts/create_story_video.py`, audio utilities + tests | TODO | Tempo 0.92× with pitch preserved, WAV hashes/provenance, recalculate duration from actual audio |
| A05 | P0 | QA scripts/tests, `docs/qa-review.md`, `docs/storyboard-review.md` | BLOCKED A01–A04 | Run full regression, render both MP4s, log SHA/PTS/audio/QC and creator pending review |
| A06 | P1 | `docs/provider-evaluation-hf.md` (new) | TODO | Verify Gradio/HF SDK, FLUX.1 Schnell, SD3.5 Large, Wan2.1/LTX Spaces: actual access, limits, license, price |
| A07 | P1 | `docs/provider-evaluation-nim.md` (new) | TODO | Verify NVIDIA NIM DeepSeek V4.1 Flash, Magpie TTS, Riva Translate, Llama Guard: API, vi-VN, terms, costs |
| A08 | P1 | Provider abstraction + contract tests | TODO, needs A06/A07 | Opt-in online providers if verified; default local Ollama/ComfyUI unchanged, no implicit paid fallback |
| A09 | P2 | TTS UI/jobs/cache/alignment | TODO | Proper bundled/authorized TTS integration, review 20 voice samples, real phrase/SRT alignment |
| A10 | P3 | Social OAuth/upload | TODO | Private/draft first; explicit user consent and authorized providers, no automatic publication |

Suggested ownership is *not* a claim. Check open PRs before touching a file. Different agents may work A02, A04, A06, A07 concurrently. A03 shares renderer/schema integration and must coordinate with A01/A05.

## Acceptance criteria

**A01:** A 3.3-second scene has beats indexed 0–3, each with visual state, action, camera, exact on-screen text (or empty), speech cue and continuity; reject invalid/missing authored fields and gaps/duplicates; existing scenes without beats still load. Retiming preserves old beats, flags `needs_review`, and requires creator to review. A proposal fallback created for old model responses is always `needs_review`, never called complete. Preserve mode never silently rewrites spoken source.

**A02:** Wet/dry art has compatible geometry and alpha; wet→dry state is visibly continuous without double-image ghosting, fixed peg, gentle hem movement, fold→spread follows one object. Inspect initial/middle/final and between-frame changes at both aspects, not just pixel metrics.

**A03:** Caption entry only (<=0.26s) then remains still; no cropped glyphs or unreadable scientific text; verify save/reload and editing of full per-second fields, responsive UI and accessibility. Beat metadata is **not** a guarantee of keyframed animation.

**A04:** Tempo = 0.92×, original pitch preserved, speech not cut, provenance hashed and command documented; recalculate each scene from its output WAV, keep under 60s. The earlier ~41.9-second estimate is **unverified**.

**A05:** Actual Python/Ruff/mypy/pytest, TS/Vitest/build/Playwright and real 1080p portrait/landscape export; record hashes, duration, 30fps CFR, decoder, AAC/LUFS/truepeak, silence, ASR uncertainty and warnings. Human full watch/listen/age/science score separately; a technical pass is not manual approval.

**A06–A08:** Use official versioned documentation and authorized live tests. Distinguish free trial vs ongoing free use, code vs weights vs Space license, data sharing/privacy and server-side quota. Never scrape undocumented endpoints or silently buy credits. A safety model cannot certify eligibility for YouTube Kids.

## Multi-agent workflow

1. Read `AGENTS.md`, `specs/whiteboard-video-tool.md`, this board, `.agent/handover/LATEST.md` and `docs/video-quality-standard.md`.
2. Claim one ID in an issue/PR comment or update the board in a small PR. Branch `agent/Axx-description` **from `feat/short-video-studio`**, open a PR **targeting `feat/short-video-studio`**. One agent per write-owned file at a time; coordinate shared contracts in the PR.
3. Include changed paths, tests with actual commands/exits, video/sample hashes, remaining problems, any dependency/license change. A test named in docs but never executed is `NOT RUN`.
4. Integrator reruns regression after merging each task. Do not claim DONE, update release readiness, or mark `specs/whiteboard-video-tool.md` implemented until acceptance evidence exists.
5. No secret/model weights/media under Git. Do not post to social, open cloud endpoints, auto-install external code, clone a voice without consent, or switch to a paid API without explicit authorization.

## CI verification commands (run on PR #2; rerun after any code change)

```bash
npm --prefix apps/web ci
uv sync --project backend --frozen --group dev
uv run --project backend ruff check backend scripts
uv run --project backend ruff format --check backend scripts
uv run --project backend mypy backend/auto_tool_video
uv run --project backend pytest backend/tests -q
npm --prefix apps/web run check
npm --prefix apps/web run build
npm --prefix apps/web run test:e2e
uv run --project backend python scripts/smoke_export.py --portrait1080
```

See README for prerequisites (Linux, Node 24+, Python 3.12+, uv, FFmpeg/FFprobe, Chromium). Ignored `.data/story-upgrade/` artifacts from prior environments do not live in Git. Retest with fresh local assets before claiming export success.
