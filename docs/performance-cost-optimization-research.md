# Performance, latency and cost optimization — research and execution plan

Status: **RESEARCH / FUTURE WORK ONLY**, not a deployed optimization. Research date: 2026-10-30.
Linked: [quality/research gates](research-first-quality-gates.md), [high FPS and fidelity](high-fps-performance-qc-research.md), [future formats](future-video-formats-research.md), [audit of plan completeness](research-plan-audit-2026-10-30.md), [existing QA skill](../.agents/skills/video-quality-review/SKILL.md), [new performance-cost skill](../.agents/skills/performance-cost-review/SKILL.md).

## Executive findings (facts vs hypotheses)

**Verified in canonical source:** `backend/auto_tool_video/render.py` generates each 30fps RGB24 frame via `ScenePainter.frame` using Pillow, constructs layers/masks, copies/composes, writes `composed.tobytes()` to an FFmpeg pipe, encodes a fresh H.264 MP4 **per scene** via `libx264 -preset veryfast -crf 18 -threads 2`, concatenates segment streams with video copy, builds a single 48kHz PCM narration track and final AAC audio. `quality.py` reads/decodes and scans the output using FFmpeg/FFprobe/OpenCV and hashes output. `store.py` queues jobs in SQLite. The canonical `.github/workflows/ci.yml` already enables `uv` and npm caches for dependency setup; browser E2E and installation run in the ordinary validation job. A separate multi-PR QA workflow is proposed in open PR #18, **not merged on canonical**.

**Hypotheses, not measured causes:** Python draw/mask copies, RGB24 pipe bandwidth, multiple FFmpeg process startup, resampling images, repeated QC decoding, fixed encoder threads, store polling and frontend main-thread work could contribute to latency. Benchmarks must attribute real costs before changing algorithms. Avoid benchmarking just an isolated `ffmpeg` command and applying the result to overall render.

**Definitions of lag:**
1. **Editor interaction lag:** keystroke/scrub response, React commit/long tasks, 390px device.
2. **Preview lag:** click → first usable frame, seek p50/p95, dropped frames, timeline state drift.
3. **Export latency:** enqueue wait, asset prep, drawing, encoding, audio, mux, QC, transfer.
4. **Playback stutter:** decode buffer, effective presented frames, device capability, asset bitrate.
5. **AI provider lag:** warm/cold model loading, queue, tokens/steps, transmission, failures/retries.
6. **Developer CI latency:** PR feedback wall time, reruns, asset downloads, cache misses.

Optimizing one metric must not invisibly worsen another.

## Research candidates and go/no-go

| Candidate | Source / capability | Applicable part | Why it may help | Risk / readiness |
|---|---|---|---|---|
| **py-spy** | https://github.com/benfred/py-spy | Low-overhead Python CPU sampling | Find actual hot functions on real render without code instrumentation | First tool; process-permission constraints, sampled data not exact timings |
| **Scalene** | https://github.com/plasma-umass/scalene | Python/native allocations, copies, CPU/GPU | Diagnose Pillow/NumPy/OpenCV copies and memory growth | Profile only, isolated optional dependency; NVIDIA GPU features optional; AI advice not execution proof |
| **Memray** | https://bloomberg.github.io/memray/ | Native+Python memory allocations | Track peak allocations/leaks by stack | Diagnostic overhead, Linux/macOS only; not a production requirement |
| **hyperfine** | https://github.com/sharkdp/hyperfine | Repeatable CLI benchmark | Warm-up, repeated runs, variance, export JSON/CSV | End-to-end harness must control artifacts, hardware and thermal effects |
| **FFmpeg benchmark/progress** | https://ffmpeg.org/ffmpeg.html | Encode/concat/decode/QC stage | `-benchmark`, `-benchmark_all`, `-progress` show encode internals/progress | Benchmark overhead, stderr volume and pipe handling; feature-probe available flags |
| **psutil + monotonic spans** | https://psutil.readthedocs.io/ + stdlib | Worker/child-process CPU/RSS/disk/time | Cheap local metrics, JSONL stage profiling without server | Child tree must be observed; psutil not yet in repo, add only if justified |
| **OpenTelemetry** | https://opentelemetry.io/docs/languages/python/instrumentation/ | End-to-end tracing | Tie UI/job/render/AI/QC spans with job ID | Optional later; no telemetry sent off-device without consent |
| **libvips/pyvips** | https://github.com/libvips/pyvips | Large raster asset preprocessing | Demand-driven streaming and low-memory bulk resizing | Not necessarily faster for tiny per-frame dynamic drawing; compare targeted workload first |
| **DiskCache** | https://github.com/grantjenks/python-diskcache | Content-addressed local cache | Atomic, process-safe, bounded disk-backed derived assets | Prefer existing SQLite/file structure first; pickle/deserialization untrusted risk; cache coherency |
| **Native Pillow/NumPy caching** | Current runtime, Python stdlib | Reuse immutable backgrounds/text/masks | Low-change, likely ROI with fewer dependencies | Must never reuse mutable frame state across scenes/cues |
| **React Profiler/Chrome DevTools** | https://react.dev/reference/react/Profiler ; https://developer.chrome.com/docs/devtools/performance | Editor responsiveness | Identify expensive commits and long tasks | Do not optimize UI without reproducing real interaction lag |
| **requestVideoFrameCallback** | https://developer.mozilla.org/en-US/docs/Web/API/HTMLVideoElement/requestVideoFrameCallback | Video playback/preview | Measure actual presented frame progress and decoder processing duration | Not guaranteed vsync-exact, browser compatibility check |
| **uv + GitHub Actions cache/concurrency** | https://docs.astral.sh/uv/concepts/cache/ ; https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching ; https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency | CI setup costs | Reuse dependencies, stop obsolete runs, separate fast/slow gates | Existing npm/uv caching present; cache security, storage and cancel rules must be audited |
| **Diffusers precision/offload/compile** | https://huggingface.co/docs/diffusers/optimization/memory ; https://huggingface.co/docs/diffusers/optimization/fp16 | Optional local AI generator | Tune memory/steps/precision, cold/warm costs and failures | Model-specific; CPU offload can be *much slower*; never treat low VRAM as free speed |
| **ComfyUI partial-graph reuse** | https://docs.comfy.org/ (verify installed version and actual graph behavior) | AI candidate iteration | Avoid re-executing unchanged graph nodes | Exact node/model hash, seeds and custom-node cache policy required; not verified live |

### License and packaging checkpoints (source snapshot only)

| Tool | Upstream license documented | Runtime packaging consequence |
|---|---|---|
| py-spy | MIT | Standalone profiler, not needed in production runtime; attach permissions OS dependent |
| Scalene | Apache-2.0 (upstream project metadata) | Local diagnostics only; GPU reporting NVIDIA-limited; do not invoke optional AI recommendation service without separate consent |
| Memray | Apache-2.0 | Memory investigations on Linux/macOS; avoid mandatory Windows package dependency |
| hyperfine | MIT OR Apache-2.0 | Standalone benchmark CLI; only test machines need it |
| libvips | LGPL-2.1-or-later | Native library binary obligations must be assessed before distribution; pyvips binding terms independently verified |
| DiskCache | Apache-2.0 | Third-party runtime package only if built-in file/SQLite cache cannot meet acceptance |
| FFmpeg | Build-dependent LGPL/GPL | Existing x264 build and distributed binary licensing must be separately audited |
| Diffusers | Apache-2.0 code (subject to per-version check) | Weights, LoRA, datasets and graph nodes may have distinct terms |

Package license does **not** certify binary bundle, plugin/custom-node, model weights or content ownership. At implementation G1, pin exact git commit/tag and read LICENSE file rather than relying on this summary. Source references: https://github.com/benfred/py-spy , https://github.com/plasma-umass/scalene , https://github.com/bloomberg/memray , https://github.com/sharkdp/hyperfine , https://github.com/libvips/libvips , https://github.com/grantjenks/python-diskcache .

**Decisions:** Prioritize built-in profiling and immutable scene cache before introducing many dependencies. Avoid full renderer rewrites, globally replacing Pillow with libvips, mandatory cloud observability, gratuitous parallel workers or GPU acceleration without measured gains.

## Experiment A — stage-level instrumentation (A12 + A36 + proposed A43)

Report wall times using `time.perf_counter_ns`, and process/children CPU and RSS where available. Stable span names:

`job.queue_wait`, `asset.validate`, `asset.preprocess`, `model.load`, `ai.generate`, `scene.painter_init`, `scene.frame_draw`, `scene.encode`, `scene.tear_down`, `audio.decode_tempo_mix`, `video.concat_mux`, `qc.hash`, `qc.ffprobe_pts`, `qc.full_decode`, `qc.visual_scan`, `qc.audio_scan`, `job.export_atomic`, `ui.preview_first_frame`, `ui.seek`, `ui.editor_input`, `ci.install`, `ci.test`.

Structured output: one JSONL row/span with `schema_version, run_id, job_id, stage, scene_id, parent_span_id, start_monotonic_ns, end_monotonic_ns, wall_ms, cpu_ms, peak_rss_bytes, peak_vram_bytes|null, frames, width, height, fps, bytes_in, bytes_out, cache_hit, process_exit, cancelled, quality_status`. Separate reproducibility manifest (commit SHA, source hashes, font digest, FFmpeg build, OS, CPU/GPU, driver, workers, thermal/power note, fixture case, cold/warm, optional model digest/seed, no secrets). Do not sum overlapping wall-time spans or equate subprocess RSS with parent RSS; document units.

Baseline >=12 representative scenes including static, dense Vietnamese captions, pen draw, cloth, source clip, dissolves, different audio lengths, both 1080p aspects, 30fps. If source/fixture unavailable, mark BLOCKED (no synthetic video substitute for creator review). Future FPS/4K cases benchmark separately and only after A34 gating.

For each comparable candidate: one warm-up + >=5 measured independent runs; cold run separately; report median, spread, 95th percentile **exploratory** and confidence caveat, peak RAM/VRAM/disk, full-video wall time, FPS throughput, seconds per delivered video second, failure rate and cancel behavior. Baseline noise must be estimated before thresholds.

## Experiment B — caching/avoided recomputation (A36 + proposed A44)

Cache graph by stage: original verified asset → normalized media → static visual layers/font glyph textures → source-clip decoded index/proxy → scene frames or encoded segment → final composed export → QC report. Prefer **coarse, per-scene encoded-segment cache first** if profiler confirms scene rerender is expensive and outputs are deterministic. Recompute final audio/QC for every changed narration; cached QC result is valid only for the exact artifact hash and QC policy version.

Canonical cache key = SHA256(canonicalized inputs): `{schema_version, scene_ir, ordered asset sha256, voice sha256, captions/style, font digest, engine+commit+dependency versions, input source timebase, width,height,fps,color profile, encoder preset+CRF+pixel format, transition boundary refs, randomness seed, policy version}`. Include neighboring scene boundary/reference for dissolves and cross-scene continuity; a one-scene change can invalidate adjacent segments. Do NOT key only on `scene_id`, filename, timestamp or user-facing project revision. File writes atomic (`tmp` + fsync + rename with local storage assumptions), hash validate on every hit, lock or single-flight duplicate request, compute-only-after-success; no `pickle.loads` from untrusted cache. Never reuse a segment when the previous scene's blend is different.

Tests: identical repeat is a hit with pixel/hash equivalent output and materially reduced render time; changing any one factor invalidates right parts only; same scene new narration when voice is not baked into segment can reuse visuals but must redo timing, audio and final QC; altered font/quality policy invalidates relevant artifacts; concurrent writers, interrupted writes, disk full, stale artifact, cache eviction, cancellation and rollback cannot corrupt last approved export.

Storage: explicit user-configured max bytes, LRU or weighted reuse, idle cleanup, priority for approved originals and immutable artifacts; do not garbage-collect the last approved output. Show cache hit %, reclaimed bytes, write amplification and net time saved, including hash validation overhead. No shared cloud cache with user media by default.

## Experiment C — lower Python frame overhead (A36)

1. Profile `ScenePainter.__init__`, `frame`, `visual_frame`, `draw_overlays`, `transition_visual`, `composed.tobytes`; split time between Python draw, native resize/convert, copy and pipe blocking.
2. Trial caching fonts/backgrounds/text overlays/contours; hoist repeated allocations and immutable masks. Since whiteboard masks evolve per frame, compare a correct differential update/reference result and explicit seek/retry semantics before sharing mutable buffers.
3. Trial a bounded queue between painter and encoder only where CPU and encoder overlap improves; max raw frames in queue by bytes, not item count alone (1080p RGB24 ~6.22 MB/frame). Avoid unbounded raw-frame caches.
4. Compare x264 preset `veryfast` vs `medium` at matched bitrate and matched reference quality; only trial hardware NVENC when available. CPU slots/FFmpeg threads must be sized by total worker tree, not individual subprocess alone.
5. Consider pyvips only for large static images / pre-scaling. For per-frame dynamic text or drawing, it's a different workload; reject on complexity if no measurable benefit.
6. Cache painter static resources but preserve exact semantic frame content, shadow/AA, fonts, layout and dual aspect. 1080p30 pixel/golden comparison must remain valid (allow explicit tolerance only for controlled expected changes).
7. FFmpeg process-per-scene overhead: quantify startup, file writes and rereads first. Streaming single encode could reduce I/O but can complicate cancellation, seek, scene caching and artifact boundaries. Do not rewrite without Pareto evidence.

## Experiment D — responsive editor and playback (proposed A45)

Use React Profiler and Chrome Performance traces for: project load, 20-scene script editing, beat editor, 390px layout, drag/scrub, thumbnail strip, zoom/pan, first preview frame, rapid job progress updates, render running simultaneously. Record input → paint p50/p95, long-task count/duration, React commits, memory growth, dropped/presented frames from `requestVideoFrameCallback` / `getVideoPlaybackQuality`, seek accuracy and staleness after revision.

Try first: memoize expensive derived scene data only where profiler shows rerenders, defer noncritical work, debounce costly recompute while preserving save correctness, virtualize long lists if scene count rises, render thumbnails on-demand, avoid event-loop blocking for media processing. Test keyboard, editing revision conflict, accurate progress and 390px accessibility. Preview is deliberately lower resolution but the final 1080p is never upscaled from it.

**Proposed target, not measured:** editor interaction p75 <=200ms on nominated reference devices, no editor freeze >500ms for normal operations, stable memory over repeated edits; adopt absolute targets only after device baseline. Keep manual UX review for perceived smoothness.

## Experiment E — AI inference latency and cost (A06–A09 + proposed A46)

For Ollama/ComfyUI/local TTS and any opt-in providers, record `model_load_ms, queue_ms, generate_ms, decode_ms, transfer_ms, peak_vram, warm/cold, candidate_approved, retries, model_hash, graph_hash, steps, resolution, license, cost`. Costs include **GPU electricity/hardware amortization** for local, API provider fees for online (including retries), storage/network and reviewer time; no assumptions that "local is free" or "free tier" is permanent.

Trial one reference image/voice before batch; check whether cached models/partial graphs truly skip work; hardware-appropriate dtype/quantization/attention/steps under exact-model license; compare quality with blinded human review; only reuse seeds/assets with provenance. Cold-load latency and VRAM vs CPU offload tradeoffs must be measured; diffusion docs caution sequential offload can be extremely slow. Declare opt-in and a **hard per-job maximum budget**; if estimate exceeds cap, refuse or ask for user approval, never silently switch to paid providers. `cost_per_accepted_video_minute = total_real_cost / sum(approved_output_minutes)`; failures/retries count in numerator and only human-approved duration in denominator. Do not apply nominal vendor pricing to a user's plan without current verification.

## Experiment F — cheaper *yet rigorous* QA/CI (A05 + A12 + proposed A47)

**Layer 1 PR-fast:** syntax/typing/unit/schema, critical smoke export + FFprobe/PTS/codec/decode 2–5s, small caption/visual golden tests, critical security and cancellation. Deterministic CPU fallback and 30fps compatibility.
**Layer 2 PR-integration:** real dual-aspect samples with audio and per-scene continuity; execute for changes in renderer, timing, audio, QC, caption, schema, media. Path filters must never skip a relevant transitive dependency. Keep regression gate for code changes touching shared contracts.
**Layer 3 nightly or scheduled:** full 12-scene/30–60s dual1080, long-run memory, 30→60/encoder experiments, richer temporal metrics, history and hardware-specific artifacts. Nightly green alone cannot authorize merge of new user-visible output without an exact-commit artifact.
**Layer 4 release/human:** real signed-off artifact SHA, full watch/listen, consent/licensing, device playback and science/rubric, no critical issues. Do not cache a human review of a different SHA.

Before any CI edits, coordinate with PR #18 `qa-multi-pr-integration.yml` and QA-owner PR #14; they are currently unmerged. Existing CI already uses `setup-uv enable-cache` and `setup-node cache:npm`, so do not sell "enable cache" as an unimplemented win. Audit dependency cache sizes, Playwright browser downloads, runner minutes and relevance before adding concurrency; cancellation must not interrupt critical audit/release jobs. Cold cache and warm cache must both be tested. GitHub Actions cache is untrusted, must exclude secrets and sensitive media; retention/storage/billing depends on plan and current GitHub rules.

## Gate/metric matrix

| Metric | Baseline and method | Guardrail / candidate success |
|---|---|---|
| End-to-end latency | enqueue → technical QC → export success; wall and stage spans | >=15% reduction in *measured median* for targeted experiment, or document reason if quality better; proposed screening bar, not SLO |
| Preview/UI | Browser profiler + presented frames | p75 interaction <=200ms proposed; no missed audio/scene state, regression tests pass |
| Cost accepted minute | all local amortized+API+retries+QA labor / approved output minutes | >=15% reduction against stable baseline with no quality loss (research screening target) |
| Peak memory/disk | process-tree sampling; workspace disk writes | No OOM; ideally <= baseline; proposed cap based on actual reference hardware |
| Failure/retry | 20+ stress repetitions + fault injection | No new failures, no stale hashes, cancel/rollback passes |
| Output correctness | 30fps legacy and new profiles; exact hash/PTS/decode/A/V/LUFS | All critical existing QC gates remain mandatory |
| Visual quality | matched reference SSIM/VMAF where valid + contact sheets + manual blinded A/B | No newly critical crop/ghosting/speech/fact defects; human rubric >=4 |
| CI feedback | exact workflow/runner versions, cold/warm job times | Faster PR feedback without reduced required test coverage |

Do not interpret >=15% screening thresholds as a guaranteed outcome or universal requirement: confidence intervals, workload sensitivity and hardware limits matter. Any artifact quality regression on critical dimensions blocks, even when runtime/cost improves.

## No-go and rollback

- No unreviewed dependency, model weights, cloud API or monitoring upload.
- No dropping full decode/PTS/creator QA, no fake success on timeout or skipped test.
- No 60fps created merely by repeated 30fps frames, no 4K from blurry source advertised as extra detail.
- No cache hit without version/hash validation and current QC.
- No renderer rewrite until per-stage profiles show the bottleneck and prototype confirms gains.
- No arbitrary concurrent jobs unless CPU/RAM/VRAM/disk budgets are actually measured.
- Rollback must switch to prior 30fps x264 software pipeline and invalidate incompatible new caches; accepted originals remain immutable.
- New cross-cutting tasks need an approved spec and workboard owner reservation before touching `render.py`, `quality.py`, `timing.py`, `apps/web/src`, CI or SQLite schema.

## Future proposed tasks, **NOT CLAIMED**

| ID | Owner surface after approval | Dependency | Research deliverable | Verification gate |
|---|---|---|---|---|
| **A43** | observability/benchmark `docs/` + isolated harness | A05/A12 coordination | Instrumented stage profile, warm/cold, per-job cost and hardware manifest | >=5 runs, both aspects; independent review; no runtime modification in research stage |
| **A44** | content-addressed scene cache and invalidation | A43 + A14/A20 contract review | Cache key RFC, mutable boundary tests and 3 proof-of-concept cases | Bit-equivalent success, invalidation/rollback/disc/full/cancel tests |
| **A45** | frontend responsiveness and preview | A43, A03 done | React/browser traces and bottleneck-driven UI POC | 390px/desktop p75, first preview, dropped-frame and accessibility E2E |
| **A46** | AI model/ComfyUI/TTS cost planner | A06–A09 research, A43 | Cold/warm provider benchmark, budget cap design and accepted-cost accounting | Same assets/seed, licensed checkpoint, human quality, no silent paid calls |
| **A47** | CI/test-cost optimization and QC cadence | A05 + A12 + PR #18 coordination | Exact-SHA CI time/cost audit, four-tier test matrix and coverage mapping | No coverage loss, security/cache review, fast and full gate proof |
| **A48** | reference hardware and operating profiles | A43/A44/A45/A46/A47 analysis | CPU-only, mid-CPU, optional GPU decision table / Pareto frontier | Published reproducible raw data + no-go options and creator review |

**No overlapping IDs:** A12 builds fixture/reference benchmark system; A36 optimizes Python/encode internals after profiling; A43 adds cross-stage observability; A44 cache; A45 web; A46 AI; A47 CI; A48 hardware selection. A34 FPS clock and A41 video metrics remain separate. Agent must not treat any task proposed here as permission to code.

## Skill handoff and evidence file

Agent must read [performance-cost-review skill](../.agents/skills/performance-cost-review/SKILL.md), this dossier, [plan audit](research-plan-audit-2026-10-30.md), and G0–G6. Future research output path `docs/research/<task-id>-performance.md` with source access dates/commits/licenses, reproducible commands, exit codes, model/GPU specs, benchmark manifest, raw per-run JSON/CSV, fixed fixture hashes, QC/human artifact SHA, changed paths, risk/rollback, decision GO/NO-GO. `NOT RUN` is never a synonym for green.

## Evidence attribution / official references

- Python profiling: py-spy (https://github.com/benfred/py-spy), Scalene (https://github.com/plasma-umass/scalene), Memray (https://bloomberg.github.io/memray/overview.html), hyperfine (https://github.com/sharkdp/hyperfine).
- FFmpeg stage benchmark/progress: https://ffmpeg.org/ffmpeg.html .
- React/browser: https://react.dev/reference/react/Profiler , https://developer.chrome.com/docs/devtools/performance , https://developer.mozilla.org/en-US/docs/Web/API/HTMLVideoElement/requestVideoFrameCallback .
- Media preprocessing/cache: https://github.com/libvips/pyvips , https://github.com/grantjenks/python-diskcache .
- Python tracing: https://opentelemetry.io/docs/languages/python/instrumentation/ .
- AI: https://huggingface.co/docs/diffusers/optimization/memory , https://huggingface.co/docs/diffusers/optimization/fp16 , https://docs.comfy.org/ .
- CI: https://docs.astral.sh/uv/concepts/cache/ , https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching , https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency .
- Source: canonical `render.py`, `timing.py`, `quality.py`, `store.py`, `.github/workflows/ci.yml`; all inspected 2026-10-30. All external sources must be re-verified at the time of adoption.

**Verification boundary:** Repo/source/document research DONE; py-spy/hyperfine/Scalene/Memray/pyvips/DiskCache/AI optimization real performance and memory tests NOT RUN. No asserted speedup, cost savings or new release readiness.
