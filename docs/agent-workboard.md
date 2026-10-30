# AI Agent Workboard — Whiteboard Studio

Updated: 2026-10-30 · Status: **in progress / not release-ready**
Canonical feature branch: `feat/second-by-second-motion-voice` (forked from default `feat/short-video-studio` at `a7d000f6`).
Current owner of tasks: **unassigned** until an agent claims a task in its own branch/PR. Roles in the table are suggestions, not assignments.

> Source-of-truth policy: `specs/whiteboard-video-tool.md` sets approved scope; this board is a coordination document, not evidence that code has passed verification. An earlier unpushed local session was described by the user but is **not recoverable through this GitHub connection**. Do not assert that its 0.92x render or 47-beat timeline exists in Git. The work below is a new reconstruction on a feature branch.

## Verified baseline versus new WIP

| Milestone | Latest verified baseline on default branch | Feature branch status |
|---|---|---|
| M1 — 2D editor/render/QC | Implemented; past handover reports 182 pytest + 10 Vitest + 13 Playwright = 205 passing tests; 12-scene 38.7s MP4 in two aspects technical-QC passed, human review pending | Must preserve all regressions; **none rerun for this feature yet** |
| M2 — storyline/image AI | Ollama + ComfyUI local adapter/proposal/review/apply exists; live model inference not confirmed | WIP second-by-second schema and planner prompt; HF/Gradio/NIM candidates unverified |
| M3 — voice/polish | VieNeu experimental offline CLI; no production TTS UI; no forced alignment | WIP caption bounce and shirt animation; **0.92x at constant pitch not implemented/verified in this branch** |
| M4 — social | Manual export/upload hub; no OAuth/direct posting | Out of immediate scope |

## Parallel task board

Status vocabulary: `DONE-BASELINE` = verified in old handover only; `WIP-UNTESTED` = code exists on feature branch but not validated; `TODO` = no implementation; `BLOCKED` = needs external assets/access or creator review. Do not convert WIP to DONE without recorded test results.

| ID | Priority | Suggested role | Scope / file ownership | Status | Dependencies |
|---|---|---|---|---|---|
| A01 | P0 | Storyboard/domain agent | `backend/auto_tool_video/{domain,planning}.py`, `backend/tests/test_ai.py`; second-by-second 0..ceil(duration)-1, strict fields, preserve mode, timing changes, backward-compatible load | WIP-UNTESTED | None |
| A02 | P0 | 2D motion agent | `scripts/science_story.py`, `scripts/blender_review_art.py`, science-specific scene tests; wet→dry continuous mask, wind sway around fixed peg, fold→spread | WIP-UNTESTED | Existing transparent wet/dry art must be validated |
| A03 | P0 | Caption/UX agent | `backend/auto_tool_video/render.py`, `backend/tests/test_typography.py`, `apps/web/src/{main.tsx,domain.ts}`, web E2E; subtle page-entry animation and editable per-second storyboard | WIP-UNTESTED | A01 contract; coordinate shared renderer files |
| A04 | P0 | Voice/audio agent | `scripts/create_story_video.py` + new audio utility/tests; 0.92x tempo while preserving pitch, no speech clipping, regenerate timing from modified WAV, provenance | TODO | Real local narration/voice assets and A01 duration semantics |
| A05 | P0 | QA/integration agent | `backend/tests/test_composition.py`, integration E2E, `docs/qa-review.md`, `docs/storyboard-review.md`; render portrait & landscape with actual input then examine QC and creator flags | BLOCKED until A01–A04 merge & media are available | A01–A04, valid 2 GiB free space and FFmpeg |
| A06 | P1 | Hugging Face research agent | `docs/provider-evaluation-hf.md` (new); `@gradio/client`, HF Hub SDK, FLUX.1-schnell, SD 3.5 Large, Wan2.1 I2V, LTX Video Spaces; access, quotas, licenses, availability, schemas | TODO — *research only* | No app keys or source credentials in repo |
| A07 | P1 | NVIDIA research agent | `docs/provider-evaluation-nim.md` (new); DeepSeek V4.1 Flash, Magpie TTS Zeroshot, Riva Translate 4B v2, Llama Guard 4; region, vi-VN, endpoints, free-tier, gating | TODO — *research only* | Official docs/live authorized testing |
| A08 | P1 | AI orchestration agent | `backend/auto_tool_video/{providers,generation}.py`, tests; opt-in online provider abstraction (after A06/A07 gates) while retaining Ollama/Comfy local offline path | TODO | A01, A06/A07 results, explicit approval for network/terms |
| A09 | P2 | TTS product agent | UI voice picker, jobs/cache/alignment/subtitle SRT, optional provider; do not equate CLI experiment with shipped TTS | TODO | A04, packaging/licensing |
| A10 | P3 | Social agent | OAuth YouTube/TikTok/Facebook | TODO | Future scope; no public posting without permission |

## Definition of done per active task

- **A01:** Pydantic rejects duplicate/gapped/nonzero-first seconds and incomplete beat fields for authored proposals; scene duration 3.3s produces beats 0,1,2,3; old projects remain loadable; adjusting duration does **not** silently erase beats and sets needs-review; preserve-mode narration remains byte-for-byte correct. Add unit/API tests and document the contract. Important: current WIP planner builds a fallback sketch for old mock responses; fallback is **not** accepted as a completed authored plan.
- **A02:** Real original same-sized alpha wet/dry cutouts; continuity across two frames and scene boundaries; shirt peg remains visually fixed, hem sways smoothly, gradual dampness and unfold visually obvious, no cropped cuffs in portrait/landscape. Test representative first/mid/last frames; don't mistake pixel-difference metric for perceptual quality.
- **A03:** Bounce occurs per caption page for <=0.26s, then **zero movement**; no clipping at 390px/1080p/1920p and all 3 styles; editable second beats saved/reloaded, re-timing warning with old beats intact; accessibility and readable contrast. Test Python + Vitest/Playwright; avoid animating scientific numeric labels indiscriminately.
- **A04:** Exactly 0.92x speech tempo, stable pitch, no trimmed syllables or overlong silent tail; hash input/output and record filter command. 12 new scene durations recalculated from stretched actual WAV; total <=60s (otherwise edit narration instead of truncating). The user's earlier ~41.9s figure is **unverified** until actual output is measured.
- **A05:** Capture version/commit, source hashes, duration, audio LUFS/true peak, decode/CFR/PTS, motion findings and ASR uncertainties; run 182+ baseline Python tests, 10+ web tests, 13+ E2E tests (counts may increase), export two real MP4s with recorded SHA. Human playback/listening/age/factual verification may remain pending; mark honestly.

## AI providers: verify before any integration

| Option | Proposed role | Verification required | Gate |
|---|---|---|---|
| `@gradio/client` | API client for Hugging Face Spaces | Exact version, `view_api()` endpoint schema, auth/CORS, timeout, quota and change tolerance | Server-side opt-in adapter only; no scraping/abusing public resources |
| `@huggingface/hub` | Catalog/model info | Official API, stable Space/model IDs, per-model weights and license | Research first |
| FLUX.1-schnell Space | 2D image candidate | Space running/suspended, queue, ZeroGPU credits, commercial rights, latency on repeat tests | Optional; local Comfy remains default |
| SD 3.5 Large Space | 2D detailed illustration | Entitlements, Stability license, Space availability and queue | Optional |
| Wan2.1 I2V / LTX Space | Motion/reference experiment | Active Space ID and true public API, price/quota, input privacy, weight/license | P2 experiment; 2D core first |
| DeepSeek V4.1 Flash NIM | Storyboard JSON | Exact deployed model ID, structured-output compliance and pricing/free-tier | Independent test suite |
| Magpie TTS Zeroshot NIM | Vietnamese narration | Actual vi-VN inference, consented reference voice and license/entitlement | No voice cloning without permission |
| Riva Translate 4B v2 | Localization | Actual supported languages, quality and endpoint eligibility | Later |
| Llama Guard 4 12B | Safety classifier | Taxonomy, false positives/negatives, accepted image inputs | Assist review, not a YouTube Kids certification |

Any claim of "free", "official Vietnamese", or "1–2 seconds per image" must have a dated source and real account-qualified measurement. Never silently switch to paid endpoints, log sensitive audio, or ship a model only because a Space exists.

## Coordination protocol

1. Agent first reads `AGENTS.md`, approved spec, this board, `.agent/handover/LATEST.md`, baseline QA. Claim **one task ID** by commenting on the coordination PR or branch/task document and create `agent/Axx-short-name` **from** `feat/second-by-second-motion-voice`, not old default.
2. One agent per write-owned file at a time. A01 owns domain/planning, A02 science-story, A03 UI/renderer, A04 audio, A05 only tests/docs until integration; agree on a contract before touching cross-owned files.
3. PR base `feat/second-by-second-motion-voice`. In the PR include exact changed paths, schema and defaults, user-visible behavior, commands/tests with actual exit codes, artifacts, known untested work, and any new dependency/license.
4. Preserve original assets and existing exports. Never commit `.data/`, model weights, recordings, API keys, HF tokens, or auto publish videos. Do not modify cloud deployment or post to social networks.
5. Integrator rebases after each PR and reruns tests. Only after A01–A05 verified should the feature branch be proposed for merge into the default branch.
6. If the environment cannot access previous local uncommitted work, do not claim to have restored it; reproduce observable behavior from code and preserve an audit trail.

## Runbook / commands

```bash
git fetch origin
git checkout feat/second-by-second-motion-voice
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

Prerequisites: Linux, Node 24+, Python 3.12+, uv, FFmpeg/FFprobe with libx264/AAC; E2E Chromium. Video review requires assets in the creator's ignored `.data/story-upgrade/` or an explicitly supplied licensed fixture. **No command above has been rerun in this branch by the current assistant.**

## Current technical concerns on branch

- Storyboard beats are stored and rendered as **editorial metadata**, not keyframed by the generic renderer; generative per-second motion remains an integration task. Draft `beat_plan_status` and fallback might need stricter review semantics. API tests not yet added.
- New visual shirt morph and folded-to-open scale need full-size image inspection. Wet and dry cutouts must match geometrically; alpha blending alone might produce ghosting.
- New caption bounce is deliberately small but must be reviewed for frame/page boundaries.
- No 0.92x voice audio has been generated in this branch; no 41.9s sample can be claimed as available.
- Past 205 passing tests apply to default-branch baseline and **not** the feature branch.

## Next merge order

**A01 contract + tests → A02 + A03 animation/editor → A04 pitch-safe audio → A05 real video & QA → A06/A07 research → optional A08 integration.** Keep 2D and fully local fallback as first priority.
