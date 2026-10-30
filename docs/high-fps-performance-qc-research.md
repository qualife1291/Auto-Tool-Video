# High-FPS, sharpness, performance, render pipeline and QC — research dossier

**Status:** RESEARCH-ONLY / NOT IMPLEMENTED. Updated 2026-10-30. **No new real MP4 or benchmark has been run for this proposal.** Prioritize A02–A05 and existing 30fps releases until independent evidence is collected. Parent: [research-first G0–G6](research-first-quality-gates.md), [future video formats](future-video-formats-research.md), [video QC baseline](video-quality-standard.md).

## 1. Executive recommendation

1. Preserve 1080p / H.264 / yuv420p / 30fps as the default, verified compatibility *contract*; this does not imply the latest feature branch has completed creator acceptance.
2. Prototype **native 1080p60** by evaluating each procedural scene at genuine 60fps timestamps, rather than duplicating 30fps frames. Require visual improvement compared with 30fps and tolerable resource costs; 60fps may not improve static instructional slides.
3. Improve **source sharpness and text/edge rasterization** before considering AI super-resolution. Avoid pretending upscaling creates faithful detail. Use optional, ROI-targeted supersampling and asset quality rules, not blind 4K upscale.
4. Keep **30→60 interpolation** strictly opt-in per imported video clip when source motion genuinely warrants it. Compare FFmpeg `minterpolate` (MCI) and an isolated Practical-RIFE/RIFE experiment. Detect scene cuts/occlusion/fast text, skip unsafe intervals and retain source timing. A 60fps container is not proof of new motion.
5. Benchmark **encoder quality versus throughput**, not just speed. Current `libx264 -preset veryfast -crf 18 -threads 2` is a baseline; trial `medium/slow` and (only if supported) NVENC. Preserve software fallback and test decode/playback on target phones.
6. Add a strict multi-stage pipeline: `versioned Scene IR → capability/asset checks → timestamps/audio → per-scene render → encode → concat/mux → technical QC → perceptual QC → human signoff → immutable publish artifact`. Every step emits hashes, duration, errors, performance and cancellation state.
7. Promote only after **reproducible dual-aspect MP4 tests, legacy parity, p50/p95 resource measurements, visual A/B and human review**. Keep all unproven quality changes behind feature flags.

## 2. Source audit — actual current code (canonical branch, 2026-10-30)

| Layer / file | Verified behavior | Implication |
|---|---|---|
| `backend/auto_tool_video/render.py` | `FPS = 30`, `encode_scene` generates each PIL RGB frame, streams `rgb24` to FFmpeg `-r 30`; `libx264 -preset veryfast -crf 18 -threads 2`; landscape/portrait full 1920×1080/1080×1920; preview 640×360/360×640 | GPU encode alone will not accelerate Python painting; higher FPS doubles number of full raster frames |
| `backend/auto_tool_video/timing.py` | `frames_for(duration) = ceil(duration * 30 - 0.0001)`; scene time and frame start divided by 30 | FPS must become a consistent fraction/timebase in all timing helpers |
| `backend/auto_tool_video/render.py` | per-scene MP4 files, concat `-c:v copy`; one final 48k PCM narration track → AAC loudnorm | Independent scene render supports caching, but high FPS must preserve identical track timebases; audio cuts must remain sample-exact |
| `backend/auto_tool_video/render.py` | `narration_track` calculates `frames_for * (48000 // FPS)` | Works exactly at 30 and 60, but is not safe for arbitrary rational FPS (e.g. 60000/1001) |
| `backend/auto_tool_video/quality.py` | enforces 30fps `r_frame_rate`, PTS increments 1/30, exact frame counts, codec, 1080p, audio 48k, decode, loudness | New profiles need profile-aware QC; don't weaken 30fps gate |
| `backend/auto_tool_video/domain.py` | only `portrait|landscape` and `preview|export` options, second-based storyboard metadata; no FPS profile | Introduce a versioned profile with migrations and UI compatibility tests |
| `.github/workflows/ci.yml` and workboard | regression lint/typing/test/build/E2E, but no mandatory representative 60fps MP4 + creator QA | Separate short CI smoke from scheduled expensive full dual-aspect benchmark |
| `docs/video-quality-standard.md` | technical 30fps gate, flash/freeze proxy, creator rubric and separate pending approval | Parameterize per-profile checks and recalibrate temporal warning thresholds by seconds, not raw frame count |

This audit identifies **coupled interfaces**, not a request to modify those files in this docs PR. A02/A03/A04/A05 own overlapping parts; do not edit runtime before ownership is explicitly assigned.

## 3. Visual profiles (candidate configuration; not a promise of quality)

| Profile | Video | Purpose | Status |
|---|---|---|---|
| `compat_1080p30` | 1080×1920 or 1920×1080, 30fps, H.264 8-bit yuv420p, AAC 48k | Default backward-compatible export | Existing spec; current branch needs A05 acceptance |
| `smooth_1080p60` | Native 60/1fps at 1080p, same codec/audio | Smooth text/hand/camera motion, where useful | Research/POC only |
| `quality_1080p30` | Higher-effort x264 quality preset and improved native edges at 30fps | High detail without doubling frames | Candidate benchmark |
| `quality_1080p60` | Higher-effort preset plus genuinely rendered 60fps | Quality-first but resource intensive | Candidate conditional |
| `future_4k30` | 2160×3840 or 3840×2160, native assets, platform capability check | Premium output for source content with real fine detail | Later POC, not upscale baseline |
| `future_4k60` | 4K native 60fps | Highly expensive premium experiment | Defer until 1080p60 metrics and hardware budgets pass |

1080p60 processes **2x** frames of 1080p30; 4K30 is **4x** pixels and 4K60 **8x** raw pixel work compared with 1080p30, before encoder, GPU and memory effects. For RGB24 full frame 1080×1920: **6,220,800 bytes/frame**, raw feed ~**186.6 MB/s at 30** and **373.2 MB/s at 60** per stream (decimal MB, excluding copies and temporary buffers). 4K60 raw is ~**1.49 GB/s**. These are analytical data volumes, **not measured process throughput**. Higher profiles must be gated by measured resource limits. Native 60fps = 16.6667ms/frame; 30fps = 33.3333ms/frame. FPS is not a proxy for high-quality animation, and 24/30 can be a valid artistic choice.

Prefer exactly `60/1` initially: at 48,000 samples/s, 800 audio samples per frame, versus 1,600 samples at 30fps. Future fractional `60000/1001` requires cumulative rational timestamp/sample mapping, not integer division.

## 4. Frame-exact and sample-exact timebase architecture

- Proposed `VideoProfile`: schema version, `fps_num`, `fps_den`, width/height, aspect, color primaries/transfer/matrix/range, pixel format, codec/encoder, rate-control config, motion handling and output compatibility target.
- Clock of record is rational (`Fraction`/numerator-denominator), in **frames + audio samples**, with scene duration quantization declared and checked. Keep authored beat milliseconds as semantic input; map to actual output frame indices (e.g. 60fps only displays a new sample every ~16.67ms).
- Compute `frame_count`, scene start, clip sample positions, transitions, keyframe interpolation and QC from **one shared profile/timebase API**. No incidental `/30` in renderer, audio, caption, QC or frontend.
- For fractional FPS, audio sample boundaries use cumulative rounding of global timestamp positions; enforce monotonic PTS and no fractional-sample drift. Keep scene boundary offsets integer exact wherever possible.
- Keyframe easing and object transforms evaluate `t = frame_index * fps_den / fps_num` (plus scene offset); do not derive motion from calling `frame` a fixed number of times or from previous frames unless state is deterministically reconstructible.
- Align 0.92× tempo-preserving audio on actual decoded WAV samples, not forecast scene duration. Retiming updates captions/keyframes, flags human re-review and never changes source narration silently.
- Zero-frame/empty/negative duration, cumulative roundoff, render retry, old snapshots and compare 30fps golden frames are explicit tests.

## 5. Genuine smoothness and animation physics

**Tier 1 — native parametric motion (recommended):** prefer vector animation, physics curves and easing computed at each target timestamp (camera and object transforms, pen strokes, particles, fabric motion). Test fast pan, thin line, small text, large geometric shapes, cloth, repeated patterns and intentional holds. Use motion blur selectively via subframe sampling for fast movement; do not introduce ghosting into titles, diagrams or static educational text.

**Tier 2 — clips at source FPS:** retain source frame rate and original timing as the truth. Upsample only where desired and only with evidence. Explicitly annotate `motion_source_fps`, interpolation type and scene-cut positions. Motion expectation metadata distinguishes intentionally static visuals from unintended freezes.

**Tier 3 — frame interpolation opt-in:** compare (A) repeat/duplicate as control; (B) FFmpeg `minterpolate` with `mi_mode=mci` and scene-change detection; (C) an isolated RIFE / Practical-RIFE model. Benchmark real 1080p costs; upstream RIFE's stated 720p 2080Ti speed is **not** proof of our workstation performance. Exclude clip boundaries, fades, changes of text/caption, fast occlusions, transparent artwork, large disocclusions and unstable generated imagery by explicit heuristics/manual decision. On uncertainty, leave clip native / choose static fallback. No global interpolation after final caption composition.

## 6. Sharpness and fidelity without fabricated detail

1. **Asset intake gate:** report source pixel dimensions, aspect/crop factor, focus area, compression, color profile, available pixels at final screen ROI, and provenance. Reject/flag severe enlargement; don't infer quality from container resolution.
2. **Vector/text first:** fonts, graphs, curves, geometry and labels are rasterized at target pixel resolution. Preserve glyph anti-aliasing, Vietnamese diacritics, thin-line visibility, minimum phone-size font and safe zones. Avoid per-frame font loading; cache static backgrounds, text and masks keyed by style/asset/hash.
3. **Supersampling only where A/B supports it:** render selected high-contrast shape/text layers at 1.5x–2x resolution, then quality downsample; compare sharpness, ringing, aliasing and CPU/RAM overhead. Full-frame 2x in each dimension means 4x source pixels; avoid defaulting to that.
4. **High-quality resize/colors:** compare Lanczos/bicubic/area and linear-light vs display-light handling on text/photography separately; check ringing/halo and color consistency. Declare SDR Rec.709 metadata and explicit full/limited range conversion, test cross-device playback.
5. **Codec preservation:** A/B `libx264` veryfast/medium/slow at quality-matched size/bitrate or target visual quality; CRF 18 is not a universal fidelity guarantee. Tune scene granularity and keyframe handling without losing concat copy compatibility.
6. **Optional restoration:** test Real-ESRGAN on *degraded raster source assets*, not on output text, graphs or clean vector artwork. Flag hallucinated scientific details, temporal shimmer and character changes; image-by-image restoration can introduce temporal instability. Isolated model/runtime, pinned hashes and license audit; not mandatory dependency.
7. **Optional 10-bit/HDR/4K:** only after platform compatibility, color-pipeline and display QC. 10-bit H.264/HEVC and HDR introduce decode and metadata pitfalls; keep H.264 8-bit default.

## 7. Encoder, pipeline and resource optimization experiments

### Encode alternatives

| Option | Hypothesis | Evidence needed |
|---|---|---|
| x264 `veryfast` CRF18 | Existing measured reference implementation | Repeat baseline same commit/hardware |
| x264 `medium`, CRF 16/18/20 | Slower encode may improve quality per byte; not guaranteed best at every scene | SSIM/PSNR/VMAF when reference exists, bitrate, seconds per video-second, device playback |
| x264 `slow` | Additional compression efficiency may cost excessive time | Incremental benefit vs `medium`, low-motion scenes |
| NVENC H.264 `p4/p5/p6` supported by device | Dedicated hardware encode may free CPU for painting | `ffmpeg -h encoder=h264_nvenc`, GPU/driver/SDK, quality at matched bitrate, peak memory, failures, fallback |
| HEVC/AV1 | Potential distribution/storage benefit | Compatibility, licensing/distribution requirements, hardware decode; never silently replace H.264 baseline |

NVENC settings depend on GPU/driver and FFmpeg build. Do not claim hardware speed before testing. No fixed `-threads` value is universally optimal; total concurrent paint/encode/FFmpeg/QA threads must be bounded to prevent oversubscription.

### Stage-level observability

Capture wall and CPU time, process tree peak RSS, GPU utilization/VRAM (if available), disk peak+temporary writes, bytes piped, frame render vs encode vs audio vs concat vs QC time, queue duration, cancellation latency, retry success, worker exits, errors with redacted stderr, artifacts/hash, config and environment versions. Count real source frames and duplicated frames separately. Per-scene render stats allow hotspots to be attributed rather than blaming FFmpeg alone.

### Performance architecture

- Cache stable overlays, fonts, masks, backgrounds and source decodes with content-addressed keys, render/profile versions and invalidation tests.
- Avoid per-frame conversions/copies when possible (currently PIL RGB frame → `tobytes()` → raw pipe); prototype compatible zero-copy/buffer reuse or hardware-native paths without compromising deterministic visual output.
- Bound producer/consumer queue and pipe backpressure: max in-flight frames, avoid storing all 1080p/4K raw frames in RAM; FFmpeg child process exit should propagate without deadlocks.
- Continue per-scene bounded rendering and resume with validated segment manifests/hashes. A cache hit must not bypass current QC or trust a segment generated by a different scene/provenance.
- CPU vs GPU acceleration should be considered at the **bottleneck stage**. If PIL painting dominates, NVENC may yield little total gain; if encoding dominates, test presets first.
- Prioritize fast preview (lower resolution) only for **editing**; final should use real final-resolution rasterization, never stretch a low-res preview to 1080p.
- Concurrency: existing one-heavy-job worker remains default. Parallel scene rendering only after memory, CPU and disk budget experiments; add resource-aware scheduler and cancellation safety.

## 8. Reproducible benchmark protocol

**Design:** A12 owns harness; proposed A34–A39 research items below are unclaimed. Freeze one commit, project snapshot, 12-scene or richer fixture manifest, source WAV/fonts/assets hashes and 30fps control outputs. Benchmark both portrait/landscape, at least three hardware classes if available (CPU-only low-end, CPU mid, optional NVIDIA GPU), and record full version manifests.

**Test matrix — minimum:**
- 30fps baseline veryfast CRF18 / 1080p; 60fps native veryfast CRF18 / 1080p.
- 30fps x264 medium CRF18 and other CRF points; 60fps medium only if budget passes.
- 30→60 interpolation on suitable stock/animation clips, each method with static control.
- Native small-text/vector science diagram and low-res photographic source.
- Optional NVENC matched-quality/matched-bitrate tests only where hardware exists; optional 4K30 after 1080p60 passes.
- Every representative test scene: static slide, pen drawing, camera pan, title bounce, small Vietnamese glyphs, thin graph, wet/dry cloth, fade/cut/scene boundary, moving source video, quick occlusion, high-frequency pattern, silent and narration timeline.

**Instrumentation:** warm-up, then ≥5 runs for each comparable candidate per machine; all runs and failures reported, not just successful fastest run. p50 and max, exploratory p95 (small samples cannot prove SLA), variance, %speed ratio and peak resource; A/B visual blind review on real phone and desktop. Report filesize, compression ratio, target bytes, decode/seek and power/battery if accessible. Report full hardware/software/driver hashes, concurrency and thermal conditions.

**Claims policy:** no speed or objective perceptual improvement is demonstrated by estimated pixels/s. There is no one universal "best" CRF/preset/FPS. List candidates by **Pareto frontier** (quality, render time, memory, bytes, compatibility); choose configurable user-visible modes only after real data.

## 9. Quality gates — automated and manual

### Fast PR gate (short deterministic, CPU only)

- Unit: rational frame/sample mapping, 30/60 fps, 0.001–20s and fractional duration, monotonic PTS, frame/scene boundaries, A/V, old project snapshots, cancellation, retry, fallbacks and invalid input.
- Integration: 2–5s real synthetic scene per profile and aspect, exact frame counts and duration, FFprobe codec/pixel format/frame rate, full decode, audio 48k, no subtitle clipping and 30fps golden parity.
- Browser/UI: profile controls, unsupported encoder guards, preview/export distinction, save/reload/migration, mobile/390px and accessibility.
- Security/resource: malicious/oversized inputs, no unreviewed model/network installation, FFmpeg args not shell interpolated; bounded memory, timeout/error handling, no stale cache publish.

### Scheduled/agent acceptance gate (expensive but required before feature approval)

- Full ≥30s dual-aspect 1080p30 and 1080p60 export; 60fps must contain real native intermediate object states for motion-required scenes.
- Full decode, CFR/PTS expected gap `fps_den/fps_num` (tolerance in seconds calibrated at profile), exact expected frame count, 0-start timestamps, duration and A/V drift ≤100ms; H.264/yuv420p, AAC 48k, LUFS −16±1 and true peak ≤−1dBTP. Silent-mode exception explicit.
- Automated temporal checks at identical **time durations** across FPS: freeze ratio/hold intent, repeated frames, luma-flash/flicker, scene cut, optical-flow stability, ghosting, motion continuity and caption overlays; source→output frame matching for interpolated clips.
- Sharpness/color: target-resolution text/strokes (Vietnamese accents, number/formula integrity), ROI crop, edge halo/ringing, banding, color transfer/range. Compare decoded output to reference render, not 60fps interpolated clip vs unrelated 30fps footage.
- Objective: FFmpeg PSNR/SSIM for aligned identical-reference frames; Netflix VMAF v1 1080p and phone models where tool available, **_hfr model for ~50/60fps** with correctly aligned reference and model/engine versions. No comparing VMAF across different FPS without timebase/ref normalization; VMAF can miss temporal defects and has HFR limitations.
- Manual: blinded 30/60 and x264/NVENC A/B; 1–5 existing rubric, phone-sized text, comfort, motion clarity, no invented details, physics/facts, hearing and epilepsy-related caution (flash proxy is not certification). Reviewer signs hashes and warnings; all axes ≥4, no critical issue.
- Regression after merge: exact merged commit and fresh MP4; failures prevent DONE/RELEASE even if all code tests pass.

### Quality targets and non-targets

**Hard zero-tolerance:** wrong FPS/dimensions/codec profile, PTS regression, missing frames, mismatched audio duration threshold, full decode error, missing source attribution, critical caption crop, unsupported output marked success, silent paid fallback or inconsistent SHA report.

**Investigative targets (not release promises):** demonstrable native motion improvement in moving test scenes; lower interframe jerk without blur/ghosting; equal-or-better reference metrics at matched filesize; no meaningful regression in legibility; measurable render-time/memory costs; stable cancel/retry. Set numerical budgets only after A12 baseline and hardware tiers are characterized. Motionless scenes need not generate artificial movement merely to pass.

## 10. Failure modes and explicit mitigations

| Risk | Failure | Mitigation |
|---|---|---|
| Change `-r 60` only | Duplicated/timed-wrong frames, broken QC and audio mismatch | Profile/timebase migration across render+timing+QC+API and E2E |
| `minterpolate` or RIFE globally | Cut blending, hand duplication, moving glyphs, edge ghosts | Scene-aware opt-in, masks, exclude transitions and caption compositing; revert |
| Blanket sharpening/upscale | Halos, fabricated science details, temporal shimmer | Native vector/text, source asset audit, per-ROI tuning and manual scientific QA |
| NVENC by default | Missing driver/GPU, different quality/codec compatibility | Capability probe, x264 fallback, hardware-tier benchmark |
| Per-scene process fanout | Disk/RAM exhaustion, contention and cache races | Bounded worker pool and resource budgets; current single-job default |
| FPS-dependent heuristics | Freeze/flash false positives at 60fps | Define detection thresholds in time/scene intent and calibrate on labeled fixtures |
| Quality score gaming | VMAF/PSNR increase but visually worse scene | Use matched references, temporal tests, blind subjective human signoff |
| 4K without native assets | Same blurred content at greater cost | 4K only after source-resolution validation and ROI QA |
| Changed project schema | Old projects silently break | Migrations, round-trip tests, fixed 30fps compatibility profile |
| Cancel/error during pipes | Zombie FFmpeg, stalled queue, broken partial output | Subprocess ownership, timeouts, cleanup, transactional artifacts |

## 11. Proposed new, **unclaimed** tasks for future integrator

| Task | Priority | Prerequisite | First research/POC artifact | Implementation approval gate |
|---|---|---|---|---|
| **A34** | P0 after A05 | A12, A05 | Frame/sample-accurate FPS profile RFC; inventory every hard-coded `30`, contract and migrations | Legacy 30fps parity + 60fps dual-aspect real smoke; independent review |
| **A35** | P1 | A34, A13/A14 coordination | Native 60fps frame-evaluation POC on 6+ scenes | Human A/B on motion, correct PTS/audio, measured CPU/RAM |
| **A36** | P1 | A12, A34 | Render/encode/QA bottleneck profile and caching/streaming experiments | Reproducible p50/p95, memory/disk/cancel, no visual regression |
| **A37** | P1 | A12 | Source asset sharpness and native text/vector fidelity evaluation | Small glyph/ROI/color/halo visual and reference QA; no fabricated detail |
| **A38** | P2 | A34, A35, A36 | x264 preset/CRF vs supported NVENC encoding tradeoff matrix | Full decode/playback and quality-matched throughput evidence, fallback |
| **A39** | P2 | A12, A34 | FFmpeg MCI vs Practical-RIFE/RIFE masked source-clip interpolation | 30→60 blind review, cut/occlusion failure study, license/VRAM gates |
| **A40** | P2 | A12, A37 | Optional Real-ESRGAN source enhancement and 4K feasibility | Scientific accuracy, shimmer/halo and GPU/CPU budgets |
| **A41** | P1 | A12, A17 coordination | High-FPS reference metrics and temporal/perceptual QC calibration | Versioned VMAF v1 + HFR / CAMBI and ITU-style human protocol, no false claims |
| **A42** | P2 | A35–A41 | Resource-aware render scheduler, checkpoint/retry/cancel and profile UX | Fault-injection and regression on each supported hardware tier |

**All task statuses = PROPOSED / NOT CLAIMED / RESEARCH FIRST.** The integrator must register them in the workboard, check active PRs, reserve write-owned paths, approve requirements, and coordinate A34 with A02/A03/A04/A05 because FPS touches renderer/audio/contracts/QC. Never start by modifying `render.py` or `quality.py` concurrently with those agents.

## 12. References — authoritative sources, researched 2026-10-30

1. FFmpeg filters: `minterpolate`, `fps`, `libvmaf`, `blurdetect`, `blockdetect`, `libplacebo`, `scdet`: https://ffmpeg.org/ffmpeg-filters.html
2. FFmpeg encoders (`libx264`, `h264_nvenc` capability and preset caveats): https://ffmpeg.org/ffmpeg-codecs.html
3. NVIDIA NVENC encoder programming and recommended settings: https://docs.nvidia.com/video-technologies/video-codec-sdk/13.0/nvenc-video-encoder-api-prog-guide/index.html
4. Netflix VMAF core and CAMBI: https://github.com/Netflix/vmaf and **VMAF v1 high-frame-rate model**: https://github.com/Netflix/vmaf/blob/master/resource/doc/models_v1.md (released June 2026; choose correct HFR/phone/display model and record version; not sufficient alone for overall quality)
5. ITU-R BT.500-15, 2023 subjective image quality testing guidance: https://www.itu.int/rec/R-REC-BT.500-15-202305-I/en
6. ECCV 2022 RIFE paper: https://www.ecva.net/papers/eccv_2022/papers_ECCV/html/95_ECCV_2022_paper.php ; official implementation https://github.com/hzwer/ECCV2022-RIFE (MIT repo) and engineering variant https://github.com/hzwer/Practical-RIFE (MIT repo), weights/dependencies independently review.
7. Real-ESRGAN source restoration: https://github.com/xinntao/Real-ESRGAN (BSD-3-Clause repo), independently check model weight and asset terms.
8. Project's verified code paths: `backend/auto_tool_video/render.py`, `timing.py`, `quality.py`, `domain.py`, `docs/video-quality-standard.md`; historical CI in `docs/agent-workboard.md`.

**Evidence classification:** External research + static GitHub source inspection DONE; local 60fps prototype, RIFE, Real-ESRGAN, NVENC, VMAF, real 60fps export, cross-device playback and human QC **NOT RUN**. Official upstream capability is not a locally verified feature.
