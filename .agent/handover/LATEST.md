---
status: partial
slug: whiteboard-video-tool
updated: 2026-10-30
---

# Handover — Whiteboard Studio

**Repository branch:** `feat/short-video-studio` is the canonical shared development branch. Current tracking: [workboard](../../docs/agent-workboard.md) A01–A10, [active tasks](../memory/short-term/TASKS.md), [roadmap](../../docs/development-plan.md), and [approved spec](../../specs/whiteboard-video-tool.md). This handover is a technical snapshot; do not confuse merged WIP with completed release.

## What is in source

- M1 baseline: 2D local web studio, import/render MP4 for both ratios, captions, audio-sync workflow, technical QC and creator review; local Ollama/ComfyAI adapter contract available for M2.
- Latest code additions: `SecondBeat` scene metadata, planner prompt/partial fallback for second-by-second outlines, per-second editor, short caption-page bounce, sample native shirt wet/dry blending, peg-relative swaying and unfolding. **Not yet verified by a fresh test run or real export**.
- Current gaps: invalid/incomplete beat coverage and retiming semantics need strengthened tests; beat timeline not compiled to generic renderer keyframes; wet/dry alpha matching and glyph safe-zones need visual inspection. Voice 0.92× preserving pitch and its timeline, final new MP4, HF/NIM research and live AI provider benchmarking are **not complete**. A04/A05 are top blockers.

## Last verified historical baseline, not current QA

On the earlier commit `a7d000f6`, the prior handover recorded 182 pytest + 10 Vitest + 13 Playwright = **205 pass**; a 12-scene ~38.7-second sample in portrait and landscape passed technical QC. It still had six near-repeat/motion warnings per aspect; narration ASR exact-normalized 9/12, human playback/listening/fact/age review pending. Details: [QA review](../../docs/qa-review.md), [storyboard review](../../docs/storyboard-review.md), [quality standard](../../docs/video-quality-standard.md). Source snapshots and earlier handovers remain in Git history/`.agent/handover/`.

**Since the additions above:** no new authoritative Ruff/mypy/pytest/Vitest/Playwright results, no video hashes/audio QA. Do not count historical 205 as current passing tests. The user's earlier local workspace change reports are not recoverable from GitHub without an explicit file upload.

## Next agents

1. Claim an ID A01–A10 via the workboard/PR; branch from `feat/short-video-studio`. Avoid overlapping write ownership.
2. A01–A03 fix/test the schema, motion and editor. A04 generate 0.92× audio from approved voice assets, log SHA/time, adjust scene timings without clipping. A05 independently rerun full tests and real portrait+landscape 1080p export, technical QC, and creator review.
3. A06/A07 investigate HF/Gradio and NVIDIA NIM with current official sources; do not treat ZeroGPU/limited trials as production-free or a safety model as a Kids certificate. A08 adapter after gates.
4. For all results, record **which exact commit**, environment/commands, exit status, artifacts/hashes, limitations and any blocked external access. Save outputs under ignored `.data/`; no cloud/social publish or secret upload.

## Launch and QA

See [README](../../README.md), [runbook](../../docs/agent-workboard.md) and the [video QA rubric](../../docs/video-quality-standard.md). Linux/Node24+/Python3.12+/uv/FFmpeg/Chromium for E2E. Native Windows/macOS, online AI live tests, GPU learned benchmarks, OAuth upload and manual reviewer sign-off remain outside established baseline.

**Historical checkpoints are preserved; future agents should update this handover only with new verified evidence.**
