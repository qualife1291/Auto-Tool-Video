# Future Video Formats and Quality Architecture — research dossier

Status: **RESEARCH / FUTURE BACKLOG ONLY**, no feature implementation authorized. Updated 2026-10-30.
Parent: [research-first gates](research-first-quality-gates.md), [development roadmap](development-plan.md), [workboard](agent-workboard.md). Preserve A02–A05 P0 and local-first default.

## Vision and non-goals

Make Whiteboard Studio a multi-format, multi-renderer, evidence-driven production system for educational, social, product and storytelling videos. Highest quality is a *per-output measured and creator-approved objective*, not an ungrounded promise that every model or engine will achieve a universal maximum. Maintain editability, correct facts, vi-VN audio, temporal consistency, reproducibility and offline functionality. No blanket framework rewrite, unapproved paid API, arbitrary downloaded model execution or automated publication.

## Format taxonomy and coverage

| Format | Typical output | Preferred primary engine | Key difficulty / QC | Priority |
|---|---|---|---|---|
| Whiteboard/explainer | 9:16, 16:9, 1:1 | Existing FFmpeg/Pillow + procedural Canvas | Contour correctness, motion clarity, typography | P0 |
| Kinetic typography/quotes | 9:16, 1:1, 4:5 | Procedural Canvas / FFmpeg | Safe zones, readable Vietnamese, rhythm | P1 |
| Mathematics/charts/data | 16:9, 9:16 | Manim CE / vector | Numeric accuracy, labels, geometry | P1 |
| Science simulation/diagrams | 16:9, 9:16 | Blender/Manim/parameterized templates | Physical plausibility and stated simplifications | P1 |
| Cut-paper/sketch/riso/pixel/isometric | all supported | Animate-style isolated kit | Style consistency, repeatability | P1 |
| 2D character storytelling | 9:16, 16:9 | Rigged/vector procedural + optional AI assets | Identity, mouth/pose, continuity | P2 |
| Documentary/stock footage | 16:9, 9:16 | Licensed footage + FFmpeg timeline | Source provenance, rights, relevance | P2 |
| Product demos/UI walkthroughs | 16:9, 9:16 | Screen capture + procedural overlays | Correct UI and privacy redaction | P2 |
| Motion comic/illustrated story | 9:16, 16:9 | Layered art, parallax, camera | Subject continuity, legibility | P2 |
| Cinematic AI video/I2V/T2V | 9:16, 16:9 | ComfyUI/provider adapter opt-in | Flicker, character identity, cost and licenses | P2 |
| Mixed-media hybrid | all supported | Scene compiler + engine routing + FFmpeg | Color/audio continuity, render contracts | P2 |
| Tutorial/course long-form | 16:9, chapters | Deterministic scenes, chapter composer | Resume, resource bounds, navigation | P2 |
| Localization/multilingual | 9:16, 16:9 | Transcript + TTS/ASR + subtitle layout | Translation, pronunciation, retiming | P2 |
| Series/batch templates | multiple formats | Versioned project/asset/style bible | Idempotency, cache, drift and review workload | P3 |
| Social distribution packages | 9:16, 4:5, 1:1, 16:9 | Safe-zone profiles + manual export | Platform policy, rights, disclosure | P3 |

The above is a *capability roadmap*, not a claim these formats are implemented. 1:1/4:5, long-form, multilingual and AI video require explicit new specs and real tests.

## Reference sources, boundaries and official checks

- Animate (https://github.com/cth9191/animate): Canvas procedural, headless Chromium frame export, 7 style kits, story grammar, style frames, beat approvals, frame-hash regression, rhythm/text/hero QC; benchmark isolated adapter first. Verify exact pinned commit and license before reuse.
- OpenMontage (https://github.com/calesthio/OpenMontage): multi-stage orchestration, footage retrieval, approval and provenance ideas; repository advertises AGPLv3. Study architecture, do not copy code without license/legal decision.
- OpenCreator (https://github.com/krillinai/OpenCreator): creator workspace, skills, versioning, project/agent run management; assess UX concepts without replacing React/FastAPI.
- Manim CE (https://docs.manim.community/en/stable/): precise mathematical animations, community MIT; keep version distinction from other Manim variants and asset rights.
- Blender (https://www.blender.org/about/license/): parametric 3D and science assets; GPL applies to Blender software, outputs generally remain creator's property; add-ons/assets may have separate terms.
- ComfyUI (https://github.com/Comfy-Org/docs/blob/main/development/api-development/workflow-api-format.mdx): pin API-format workflow graph, custom nodes, checkpoints and hashes; browser save JSON differs from API JSON. Official v2 SDK docs https://github.com/Comfy-Org/docs/blob/main/development/api-development/sdks.mdx describe idempotent jobs, but cloud API needs a paid subscription; local-first integration should not assume cloud free.
- Remotion (https://www.remotion.pro/license; https://github.com/remotion-dev/remotion/blob/main/LICENSE.md): evaluate only as optional React composition POC; license depends on entity/use case, with extra restrictions for derivative editor products. No default integration before license review.
- FlowKit / unofficial Google Flow automation: research-only due brittle, undocumented interfaces, credentials/ToS and stability. Prefer official authorized APIs; never rely on hidden endpoints.
- faster-whisper / forced alignment: investigate language coverage and word timing against manually corrected Vietnamese transcripts; ASR is not ground truth or proof of voice quality.

Official web checks performed 2026-10-30 for Manim, Blender, ComfyUI, Remotion; other source characteristics based on inspected repository READMEs, not live production performance.

## Architecture contract (design target, not current API)

`Brief + factual sources + approved Script -> Versioned Storyboard/Scene IR -> Scene Compiler -> Engine Router -> Isolated Render Adapters -> FFmpeg Composer -> Technical QC -> Creator QC -> Export Packs`

**Scene IR v1 proposal**: `project_version`, `scene_id`, `duration_frames`, `fps`, `aspect`, `safe_zone_profile`, `visual_layers`, `objects`, `keyframes`, `camera`, `narration_asset_sha256`, `audio_cues`, `caption_cues`, `continuity_refs`, `style_ref`, `engine`, `source_provenance`, `review_state`. Stable object IDs and frame-based timings; schema migrations and legacy fallback are mandatory. Scene metadata is not magically a renderer animation.

**Render adapter contract**: validate scene/engine capabilities; report unsupported features; render a deterministic sequence or mezzanine clip with alpha/audio policy; output manifest (engine/version, commands, seed, hashes, color profile, frame count, dimensions, performance and warnings); support cancellation, timeout, restart, bounded resources and cache invalidation. Composer controls single final AAC/loudness normalization, captions, color conversion and transitions. Render adapters must not silently invoke paid services or execute generated scripts without isolation.

**Creator UX target**: intake -> factual/script approval -> beat/storyboard approval -> style/look approval -> low-cost preview -> full render -> timestamped technical/human QC -> version compare -> approved export. Every gate links immutable input/output hashes.

## Research-first experiments required before adoption

1. **Reference fixture pack**: >=12 representative scenes (whiteboard, Vietnamese dense text, math, cloth motion, human character, UI, licensed footage, low-motion hold, transition, audio retime, portrait/landscape), with consented assets and known facts. Keep a fixed control render.
2. **Engine comparison**: identical story, audio, fonts, frame budget, target formats, hardware and measurement script. Record 5 warm measured runs per engine/configuration; median, p95, peak RSS/VRAM, CPU/GPU, bytes, crash/cancel/retry and failed scenes. Treat small sample p95 as exploratory, not SLA.
3. **Visual checks**: full decode, PTS/CFR, crop/safe zones, Vietnamese glyphs, frame duplicates, scene boundary transitions, optical-flow/flicker proxies, continuity/ghosting; inspect false positives against intentional holds. Any learned VBench/AIGCBench score must be versioned and calibrated, never invented.
4. **Audio checks**: sample counts, pitch preservation after 0.92x, 48kHz AAC, LUFS/truepeak, silence, forced alignment error vs manually corrected transcript, clipped phonemes, speaker intelligibility. Evaluate at phone speaker and headphones.
5. **Human scoring**: independent raters where possible; all five existing 1–5 rubric axes >=4 and no critical, plus readability, audience suitability, scientific accuracy, copyright/disclosure and artifacts hashes. Record disagreement and sample sizes.
6. **Reliability/security**: path traversal, malformed media, oversized files, untrusted generated code, malicious workflows, prompt injection in retrieved sources, network egress, secret exposure, sandbox isolation, cancellation, retry, storage pressure, concurrent jobs and rollback.
7. **Licensing/cost**: separate code/model weights/dataset/fonts/music/stock assets and output rights; cost per *accepted* minute, including retries, GPU, storage, subscription, operator time and maintenance.
8. **Decision**: compare against existing baseline; require measurable benefit with no critical regression. A no-go result is valid research output.

## Proposed later tasks (unclaimed, blocked until prerequisite review)

| ID | Scope | Prerequisite | First deliverable |
|---|---|---|---|
| A20 | Format matrix + versioned scene IR and 1:1/4:5 feasibility | A12 | Schema/compatibility RFC and 12-scene fixture plan |
| A21 | Motion typography + 7 style kits | A13, A14 | Isolated 3-style POC, safe-zone comparisons |
| A22 | Manim math and graph templates | A12, A14 | 3 verified educational examples, numeric review |
| A23 | Blender physics/science templates | A12, A14 | Parameterized cloth/evaporation/mechanics examples, expert review |
| A24 | Character rig/style bible and temporal identity | A14 | Character continuity evaluation and consent/license audit |
| A25 | Documentary/stock/media provenance pipeline | A12, A14 | Rights manifest, source attribution and asset validation |
| A26 | UI/screen demo and privacy masking | A14 | Redaction test and replay-safe capture POC |
| A27 | Mixed-media composer and color management | A14 | A/B video transitions, color/audio continuity tests |
| A28 | Long-form/chapter rendering and resume | A12, A14 | 3/10/30-minute benchmark and interruption recovery |
| A29 | Localization and multilingual dubbing | A15, A14 | Vietnamese baseline + 2 languages, alignment QA |
| A30 | Batch series/style/version library | A16, A14 | Reproducible 10-episode sample with per-video QC |
| A31 | 1:1/4:5/social-safe exports | A20, A14 | Native layouts, not center-cropped, platform profiles |
| A32 | Hybrid AI video routing and shot consistency | A18, A14 | Opt-in fixed-shot benchmark, cost and privacy gates |
| A33 | Advanced creator quality console | A17, A16 | Timestamped evidence, per-scene comparison, human calibration |

**Ownership:** No agent may claim A20–A33 until integrator registers an approved spec/issue/PR, confirms prerequisite evidence, and reserves file ownership in workboard. All begin at G1 research, not feature code. If future model or upstream version changes, redo compatibility/license and fixed-fixture benchmarks. Agent should update research notes with dated official sources, exact revisions and verified experiments rather than blindly executing this plan.

## Frame/sample-level screenplay, light and sound design research

The current integer-second `SecondBeat` lacks formally structured millisecond events, environmental state, lens/camera settings, lighting rigs, SFX/music/ambience, object identity, edit intent and audio sample alignment. Propose **A49 (RESEARCH ONLY)**: review OpenTimelineIO's rational-time/track concepts (https://opentimelineio.readthedocs.io/en/latest/) and OpenUSD time-sampled scene concepts (https://openusd.org/release/), define optional typed `cinematic_events` with lighting/SFX/camera/scene state and frame/audio sample quantization; validate semantic event timelines against real render capabilities. Coordinate A49 jointly with A20 Scene IR and A34 FPS clock; never assume 1ms means a distinct image frame at 30/60fps. Require G1 source/license evaluation, grammar and negative tests, migration/legacy round-trips, human semantic review and no generator arbitrary code execution before implementation.

## FPS, fidelity and performance expansion

Detailed study: [High-FPS/performance/QC dossier](high-fps-performance-qc-research.md). Versioned target profiles, rational timebase, 1080p60 native and selective clip interpolation, source-first sharpness, encoder/hardware A/B, pipeline and QC, plus unclaimed A34–A42 tasks. Do not presume 60fps/4K/AI restoration is a verified improvement without fixed-fixture benchmark and creator review.

## Sequencing and release gates

- **Foundation:** Finish A02–A05; implement A12 only with A05 coordination. Do not compromise baseline for feature breadth.
- **Render architecture:** A13 Animate POC, A15 alignment research, A20 Scene IR, A14 adapter; choose IR/adapter jointly to avoid competing contracts.
- **Deterministic formats:** A21, A22, A23, A31 first; measure quality and maintainability.
- **Creative workflows:** A24–A27, A16 and A33 after contracts stabilize.
- **Scale:** A28–A30, A17, A18/A32 only when resources, security, licenses and human QC are ready.

**Hard stop:** Any output-affecting feature must pass dual-aspect real MP4 acceptance for current formats, preserve legacy project files and obtain creator approval on exact SHA256 artifacts. Future formats require their own resolution/codec/typography/safe-zone matrices. Release approval never follows solely from green unit tests.
