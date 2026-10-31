---
name: performance-cost-review
description: Nghiên cứu, đo và review độ trễ editor/preview/render/AI, tài nguyên RAM/VRAM, chi phí, cache, pipeline và QC thật của Whiteboard Studio trước khi tối ưu hoặc merge tính năng.
---

# Performance and cost review — Whiteboard Studio

## When to use

Mandatory when task changes renderer/FFmpeg, FPS, preview/timeline, asset conversion, inference, TTS, scheduling, caching, CI workload or quality checks; optional for source-only research. Read `AGENTS.md`, `AGENT-CODING-STANDARD.md`, `specs/whiteboard-video-tool.md`, `docs/agent-workboard.md`, `docs/research-first-quality-gates.md`, `docs/research-plan-audit-2026-10-30.md`, `docs/performance-cost-optimization-research.md`, `docs/high-fps-performance-qc-research.md` and `.agents/skills/video-quality-review/SKILL.md`.

This skill is **a reproducible checklist**, not a benchmarking runtime. It does not install anything or grant permissions to run cloud providers, buy credits, modify CI, publish content, access secrets, skip checks or merge changes.

## Procedure

1. **Ownership and evidence class:** Query canonical branch, open PRs, pinned commit SHA and available fixture assets. Claim approved task ID and writable paths; if missing, stop at RESEARCH. Distinguish source inspection, synthetic fixture, real user output, CI regression and creator accepted output. Record NOT RUN for tests not executed.
2. **Define lag:** editing p50/p95 response; click-to-preview, seek and dropped frames; job queue and stage latency; AI cold/warm load/generation; final device playback; CI feedback time. Do not report generic FPS as a catch-all lag metric.
3. **Freeze inputs:** version, full asset hashes, 9:16+16:9 project and WAV, style/seed, FPS/resolution/encoder, tool versions, hardware/thermal/power, available RAM/VRAM, benchmark environment and concurrency. No unapproved media upload.
4. **Measure before changes:** first try builtin `time.perf_counter_ns`, process metrics, FFmpeg `-benchmark/-progress`, Chrome DevTools/React Profiler. Optional standalone `hyperfine`, `py-spy`, `Scalene`, `Memray` must have version/license check and permission for installation. For subprocess-heavy workloads attribute child CPU/RSS too. Measure both cold and warmed cache, ≥5 representative independent warm runs (report variation/p95 as exploratory).
5. **Pinpoint bottleneck:** trace queue wait, asset decode, frame painter, pipe backpressure, x264/NVENC encode, audio, concat, full decode, QC/visual scans, browser preview. Identify dominating wall-time and bytes copied, not just CPU flame graph.
6. **Compare at least 2 options:** control unchanged vs low-risk cache/algorithm change vs engine/parallel/GPU alternative. Estimate complexity, disk/RAM/VRAM and maintenance costs. Prefer no new dependency when stdlib/SQLite/FFmpeg already does the job. Study upstream docs/version/license; published speedups are never evidence of our machine.
7. **Guard cache correctness:** full SHA256 key of scene data, asset/font/audio/renderer versions/FPS/encoder/transition dependencies; single-flight/atomic writes/eviction; no untrusted pickle; no result reuse after font/source/model/QC policy change; neither corrupted cache nor disk full may replace prior approved export.
8. **Cost accounting:** compute total actual API/hardware/energy/storage/CI/retries/human review per **approved minute**, never cost per successful API call alone. Set hard job budget and opt-in before paid services. Model offload/precision changes need quality, cold-start and resource benchmarks; CPU offload can be extremely slow.
9. **Quality-proof:** run old 30fps profiles and applicable new profiles at 1080p both aspects; full decode, frame/PTS/CFR, A/V drift, AAC/LUFS/truepeak, caption crop, motion continuity and word integrity. For visual changes perform matched-reference comparison and blinded human rubric review of **exact SHA**. Passing speed with worse critical quality = FAIL. Refer to video-quality skill for full gates.
10. **Fault injection:** kill FFmpeg/process, cancel mid-scene, disk full, corrupted cache/manifest, stale project revision, repeated job, missing GPU/driver, failed optional provider, non-ASCII media path, sudden source-clip FPS change; recovery/rollback must preserve last approved output.
11. **Review independent evidence:** PR contains hardware manifest, raw each-run timings/metrics, tests/exits, artifact hashes, analysis, known limitations, owner and rollback, no fabricated p95/quality. Reviewer checks minimal surface and relevant open PRs before merge; rerun on merged SHA and update workboard/handover. If user/device/GPU or consent missing, keep BLOCKED/NOT RUN.

## Required report

Use approved `docs/research/<task-id>-performance.md` or agreed QA artifact. Do not create parallel conflicting status boards.

| Field | Required evidence |
|---|---|
| Source | task/owner/base SHA/PR, official URL/version/license, exact code paths |
| Baseline | original manifest, 5+ runs + cold case, output hashes and quality status |
| Candidate | isolated change/flag, version and cache invalidation, no silent paid action |
| Wall time | per-stage and total ms, median, spread, queue time and preview/seek p50/p95 |
| Resources | CPU process tree, peak RAM/VRAM, peak disk, bytes piped, power if available |
| Cost | local/API/CI/storage/retries/review and per approved minute, explicit missing values |
| QA | ffprobe/decode/PTS/audio and human exact-SHA review, test IDs and pass/fail |
| Faults | cancel/duplicate/cache corruption/disk full/model failure/rollback |
| Decision | GO / INVESTIGATE / NO-GO with independent reviewer and remaining risk |

**Stop conditions:** no approved task/spec, unclear source/weight license, overlapping file ownership, missing reproducible fixture, no profiler evidence for invasive rewrite, quality regression, unbounded cache/queues, unauthorized network/API, false benchmark attribution, or incomplete rollback. Do not silently weaken the criteria.

## Context-specific cautions

- Existing 30fps pipeline uses per-scene x264 + rgb24 raw frame pipe; swapping only encoder does not speed the Pillow painter.
- Existing code-quality CI already enables npm/uv dependency caching; compare measured cache-hit behavior before claiming an improvement.
- A02/A03/A04/A05 and QA PR #18 are overlapping, unmerged work; never touch their files without a coordinated approved task.
- Human accepted artifact is tied to SHA256 and reviewer revision; cache or old contact sheets cannot replace it.
- Full resolution, high FPS and AI sharpening are not equivalent to authentic detail or attractive motion.
- No extrapolating future GPU, cloud or service prices from an upstream README.

## Suggested research-only commands (run only where tools are installed and authorized)

```bash
# Read-only capability/version inspection
ffmpeg -version
ffmpeg -hide_banner -encoders
ffprobe -version
python --version
# Example standalone encoder metrics, after preparing an approved fixture:
# ffmpeg -benchmark -progress pipe:1 -i approved-input.mp4 -c:v libx264 -preset veryfast -crf 18 -an isolated-output.mp4
# Optional hyperfine after installation and with separate runs/outputs:
# hyperfine --warmup 1 --runs 5 --export-json isolated-benchmark.json 'approved-command-here'
```

Avoid presenting suggested commands as executed results. Redact path/user/model secrets from logs; do not check in private media or generated benchmark blobs.
