# Whiteboard Studio — AI Agent Workboard

Updated: 2026-10-30 · **Development-in-progress**, not release-ready.

**Canonical branch:** `feat/short-video-studio`. All new agent tasks branch from it and submit PRs back to it. This document is the single source of truth for open task ownership, status and acceptance criteria. `.agent/memory/short-term/TASKS.md` is a brief index; `.agent/handover/LATEST.md` gives the latest evidence; `docs/development-plan.md` is the long-term roadmap.

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

## Research-first requirement for every new feature

Before feature code, follow [G0–G6 research and quality gates](research-first-quality-gates.md): source/architecture audit, official upstream/version/license evidence, alternatives and risk comparison, approved spec/decision, isolated POC, actual tests, real video/audio and creator review when relevant, independent PR review and post-merge regression. New task owners must attach a research note and test matrix. `NOT RUN` is not `PASS`. No silent scope changes, dependency installs, cloud costs, arbitrary AI-generated code execution or overlapping file ownership.

**Future video-format backlog:** [15-format research dossier and A20–A33](future-video-formats-research.md). All IDs are unclaimed and research-only until prerequisites, spec approval and file ownership are confirmed. No agent should begin implementation from the backlog alone.

**Future FPS/sharpness/performance backlog:** [research dossier A34–A42](high-fps-performance-qc-research.md): rational FPS contract, native 60fps, stage profiling/cache, source sharpness, x264/NVENC A/B, scene-aware RIFE/minterpolate, optional restoration/4K, VMAF-HFR + temporal QC and resource scheduler. **ALL UNCLAIMED**, and none may change `render.py`/`timing.py`/`quality.py` before A02–A05 ownership and an approved spec; no local 60fps benchmarks yet.

**Performance/cost and research-completeness review:** [audit of plans and evidence gaps](research-plan-audit-2026-10-30.md), [profiling/cache/UI/AI/CI cost playbook](performance-cost-optimization-research.md) and [agent performance review skill](../.agents/skills/performance-cost-review/SKILL.md). Proposed **A43–A48** (observability, content-addressed cache, editor/preview latency, AI cost, tiered CI, hardware decision profiles) and **A49** (frame/sample-accurate screenplay with lighting/SFX/context). **All unclaimed, research-only**, no runtime/CI edits. Performance profiling can start as documentation/isolated harness coordinated with A05/A12 before FPS migrations; never merge claimed gains without same-machine A/B and unchanged quality gates.

**Proposed follow-on IDs (not yet claimed):** A11 research-first governance (docs PR); A12 reproducible benchmark/CI render; A13 Animate sandbox POC; A14 render-engine adapter; A15 Vietnamese alignment; A16 orchestration/approval research; A17 learned QC calibration; A18 AI video consistency/provider research; A19 editor UX research. Detailed dependencies, acceptance and stop conditions are in the linked plan. Existing A01–A10 statuses are unchanged. Agent claims require checking open PRs first.

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
