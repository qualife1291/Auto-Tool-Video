# A06 — Hugging Face / Gradio provider feasibility review

**Observed:** 2026-10-30 (UTC+07) · **Base:** feat/short-video-studio @ 7331a2296e9999bec155991d1c3cf79c81600fb5  
**Scope:** read-only technical assessment; no endpoint invocation generating media, no token or purchased credits, no runtime integration.  
**Status:** DOCUMENTED / READ-ONLY VERIFIED; LIVE INFERENCE NOT RUN; integration NOT APPROVED.

## 1. Decision for Whiteboard Studio

**Keep local Ollama + ComfyUI as the default. Do not add automatic Hugging Face fallback in A06.** Hugging Face hosts distinct resources: model weights, user-operated Gradio Spaces, ZeroGPU quotas, Inference Providers and paid hardware. Availability, license and billing of one do not imply those of another.

Recommended future A08 experiment (only after explicit creator opt-in): one image candidate per scene with reproducible seed, visible remote-provider warning, hard budget and concurrency limits, and a mandatory preview / review / apply step. **Do not make Wan2.1 or LTX external video generation the production default.** Native procedural/Blender science animation remains more controllable for scientific explanations, continuity and readable Vietnamese text.

Definitions used below:
- **OBSERVED:** official page, model card, or public Space source was inspected on 2026-10-30; operational state is a point-in-time observation.
- **DOCUMENTED:** official product API/pricing/license guidance; not a live account entitlement.
- **NOT RUN:** authenticated API discovery, paid/free GPU inference, media sample quality, frame QC, Vietnamese prompt result, billing or personal-data handling in production.
- A Space shown as Running is **not** proof that its Gradio endpoint is callable from our service, that a queue slot is available, or that a completed media generation succeeds.

## 2. Candidate evidence matrix

| Candidate / official resource | License / access checked | Observed Space and implementation | Feasibility decision |
|---|---|---|---|
| [FLUX.1 Schnell weights](https://huggingface.co/black-forest-labs/FLUX.1-schnell) | Apache-2.0 weights; model card says 1–4 inference steps; Hub API currently identifies model as gated=auto (account acceptance may be required to download). Separate demo hosting terms apply. | [Official Space](https://huggingface.co/spaces/black-forest-labs/FLUX.1-schnell) showed **Running on Zero**; [app.py](https://huggingface.co/spaces/black-forest-labs/FLUX.1-schnell/blob/main/app.py) uses Diffusers and a ZeroGPU decorator, exposes prompt/seed/random seed/width/height/steps and returns image + seed. Source currently caps UI width/height at 2048, but actual queue or memory success unverified. | Best first **image-only** opt-in smoke candidate, not production-ready or guaranteed free. Check actual published API schema and legal ability to send user's content before first request. |
| [Stable Diffusion 3.5 Large](https://huggingface.co/stabilityai/stable-diffusion-3.5-large) | Gated terms require account acceptance and contact information sharing. **Stability AI Community License**, not Apache; model card describes free commercial use for users/organizations under US$1M annual revenue, otherwise enterprise terms; confirm latest binding license independently. | [Official Space](https://huggingface.co/spaces/stabilityai/stable-diffusion-3.5-large) showed **Running on Zero**; [app.py](https://huggingface.co/spaces/stabilityai/stable-diffusion-3.5-large/blob/main/app.py) uses a 65-second ZeroGPU-decorated inference function and returns image + seed. | Optional image benchmark **only after license/gate review**. A visible demo does not waive the model agreement, quota or output review. |
| [Wan2.1 T2V 1.3B weights](https://huggingface.co/Wan-AI/Wan2.1-T2V-1.3B) | Model repo lists **Apache-2.0** for this exact 1.3B checkpoint; distinguish from other Wan model families and from third-party inference services. | [Wan-AI/Wan2.1 Space](https://huggingface.co/spaces/Wan-AI/Wan2.1) displayed **Runtime error**, including missing Python tomli after a dashscope import. Crucially, its [app.py](https://huggingface.co/spaces/Wan-AI/Wan2.1/blob/main/app.py) installs/imports dashscope and calls VideoSynthesis with wanx2.1-* remote models via DASHSCOPE_API_KEY; it is **not evidence of local execution of Wan2.1 open weights on HF ZeroGPU**. | **Do not integrate this Space**. Requires separate official service billing, data/privacy and permission review even if runtime is repaired. Evaluate open weights locally only with hardware and tests later. |
| [LTX-Video model collection](https://huggingface.co/Lightricks/LTX-Video) | Hugging Face shows license **other** and the model card links a specific Open Weights License for 0.9.6–0.9.8 variants. Do **not** infer Apache licensing from a code repository, older checkpoint or another component. Pin exact variant and check terms before commercial use. | [Lightricks/ltx-video-distilled Space](https://huggingface.co/spaces/Lightricks/ltx-video-distilled) showed **Running on Zero**. [app.py](https://huggingface.co/spaces/Lightricks/ltx-video-distilled/blob/main/app.py) uses 13B 0.9.8 distilled, **xlarge ZeroGPU** (2× quota cost), allows text/image/video conditioning, declares named /text_to_video, /image_to_video, /video_to_video endpoints; UI duration up to 8.5s. Other [LTX ICLoRA Space](https://huggingface.co/spaces/Lightricks/ltx-video-iclora) was **Paused**. | Research prototype only; large GPU quota consumption and model/variant license gate. No 1080p/30fps/CFR/physics/continuity quality claim. |

**Important provenance distinction:** the Wan2.1 Space itself declares an MIT license in its Space README; this is not evidence that the DashScope remote backend is free, nor a replacement for the original Wan weights license. The LTX Space uses a particular 13B checkpoint; do not mix its 0.9.8 terms with another LTX model version.

## 3. API contract: Gradio Space versus HF Inference Providers

Gradio documents the Python client interfaces Client(...), view_api(), predict() and submit(). The endpoint name, parameter order/types, file upload format, output shape and API exposure belong to **each running Space**, and can change when its owner deploys. For example the current LTX Space source explicitly names three endpoints; the FLUX and SD3.5 source connects Gradio events without a pinned api_name and must be discovered, not guessed. **Never hardcode a generic /predict endpoint against all four resources.** Sources: [Gradio client](https://www.gradio.app/docs/python-client/client), [Gradio API visibility](https://www.gradio.app/guides/view-api-page), [LTX Space app](https://huggingface.co/spaces/Lightricks/ltx-video-distilled/blob/main/app.py).

Read-only discovery example, to be run on a machine with approved internet access and a dependency pinned in a disposable environment:

    from gradio_client import Client
    # No user script/assets; no media-generation call:
    c = Client("black-forest-labs/FLUX.1-schnell")
    c.view_api()

This was **not executed in this assessment**. The web-read attempt to inspect the public /gradio_api/info URLs was unavailable from this environment. Hence specific live request schemas and successful generation are marked NOT RUN. Do not copy an example argument list directly into A08 without recording an actual view_api result, runtime revision, and a consented smoke request.

HF **Inference Providers** use a different routed API and billing path (e.g. Hugging Face InferenceClient); a checkpoint displayed in the Hub or a Space is **not** automatically supported by an Inference Provider. Providers may route to third parties. Model card widgets are not a contractual free endpoint. Source: [HF Inference Providers pricing](https://huggingface.co/docs/inference-providers/pricing).

A08 architecture suggestion: add separate opt-in provider types (local_comfy, hf_gradio_space, hf_inference_provider), never reusing the local-only HTTP loopback transport or expanding its allowlist implicitly. Verify an exact server-side approved Space ID + version/commit, endpoint signature and purpose before requests. For an externally hosted Space, treat all remote output paths, redirects, filenames, and metadata as untrusted until bytes are downloaded under explicit size/time budgets and decoded by the existing importer.

## 4. Quota, price and latency: documented, not benchmarked

As checked on 2026-10-30, official [HF ZeroGPU guide](https://huggingface.co/docs/hub/spaces-zerogpu) states **daily included GPU time**: unauthenticated 2 minutes, Free account 5 minutes, PRO 40 minutes, Team member 40 minutes, Enterprise member 60 minutes. Quota resets 24 hours after first GPU use; queues and availability are not guaranteed. xlarge consumes **2×** quota compared to large. PRO/Team/Enterprise can use prepaid credits beyond quota, documented as US$1 per 10 GPU minutes; this is **not unlimited free usage**. These figures are account-specific policies subject to change, not a per-render promise. Hosting a ZeroGPU Space has distinct eligibility requirements and quotas.

The [HF Inference Providers pricing page](https://huggingface.co/docs/inference-providers/pricing) separately lists monthly included inference credits of **US$0.10 for Free** and **US$2 for PRO** (subject to change), with further usage requiring credits/purchased allocation; a custom provider key is billed by that provider. Neither the Space demo nor Apache model weights imply a free Inference Provider deployment.

The [Spaces hardware pricing page](https://huggingface.co/docs/hub/spaces-gpus) distinguishes CPU Basic (US$0/hour in the listed hardware table) from paid GPU hardware, which is billed by the minute while starting/running, potentially **while idle**. The current guide also says creating a new compute-based Gradio/Docker Space requires a paid plan; recheck eligibility before proposing personal self-hosting. Do not calculate total video cost by multiplying a benchmark number from another GPU.

**Empirical cost, latency, queues, outputs and tokens used:** NOT RUN. No Hugging Face account token or explicit authorization to spend was available; no media generated and no model weights downloaded.

## 5. Security, privacy, licensing and acceptance gates for A08

1. **Consent and cost gate:** creator explicitly enables cloud processing *per project or per candidate*, confirms provider identity, remote transmission, applicable usage terms and a hard maximum budget. No silent paid fallback from offline defaults, no automatic uploads to social.
2. **Server-side credentials only:** use opt-in, least-privilege, fine-grained HF tokens where appropriate. Never persist secrets in SQLite project JSON, browser localStorage, job snapshots, Git, URLs or logs. Follow [HF token guidance](https://huggingface.co/docs/hub/security-tokens). Keep the existing default local loopback-only transport untouched.
3. **No arbitrary URL or SSRF:** provider destination is a trusted administratively selected identifier, not an arbitrary user/model-generated URL. Pin the Space ID, approved host, endpoint, schema and revisions; reject redirects to non-allowlisted hosts and never fetch raw output URLs without separate safe validation. Inspect Gradio file upload/returned paths.
4. **Private source material:** no unreviewed narration, private audio, photos of children, client data, credentials or copyrighted assets sent to a third-party Space by default. Third-party Space logs and retention cannot be assumed private from the mere fact that its disk is ephemeral; confirm actual provider privacy/retention agreement. Never rely on temporary file storage as a deletion guarantee ([HF Spaces storage](https://huggingface.co/docs/hub/spaces-storage)).
5. **Job semantics:** explicit cancellation and bounded polls/deadlines; Gradio queued cancellation may not stop work already running (see [client job cancellation](https://www.gradio.app/guides/getting-started-with-the-python-client)). Idempotent local job keys, no unbounded paid retries, record external job ID and network failure state without claiming remote cancellation.
6. **Media preflight:** enforce current importer constraints (PNG/JPEG <=20 MiB, <=20 MP decoded and resized; MP4 H.264 <=19.65s per scene and <=20 MiB). Reject invalid mime-by-content, path traversal, oversized payload, EXIF problems and unexpected audio/video streams. Store normalized/output/input SHA256 with model/checkpoint/Space revision, prompt hash, seed, cost estimate/actual charge if available; candidate must be reviewed before apply.
7. **Creative/quality review:** never put scientific facts or Vietnamese labels *inside generated pixels* when the renderer can typeset them. Check object-count, character identity, causal mechanism, captions, aspect, safe zones, temporal continuity, original clip audio removal and final post-render QC separately. An image demo does not validate 30fps video.
8. **Licenses:** check model weights (checkpoint-specific), Space app code, any LoRA/upscaler/voice assets, output/use restrictions and hosting ToS independently. SD3.5 gating/Community License and LTX 0.9.8 Open Weights License require explicit sign-off; Apache Schnell/Wan1.3B does not waive third-party service terms.

## 6. Reproducible negative/positive test plan (not yet executed)

| Gate | Test (one controlled, consented request where relevant) | Pass requirement |
|---|---|---|
| Read-only availability | Discover actual Space runtime, SHA and Client.view_api signature. Test each named endpoint without invoking generation during discovery. | API schema captured and versioned; no silent assumptions. |
| No-expense default | With no cloud opt-in and no token, create/apply/export in existing local app; inspect network/worker logs. | Zero remote requests and zero provider charges. |
| Auth/gate/quota | Use disposable approved account; exercise missing token, 401/403, Space sleeping/runtime error, queue exhaustion and quota limit. | Clear error code; no automatically purchased credits/retry storm. |
| Timeouts/cancel | Queue operation then cancel; simulate after-start remote cancellation, malformed SSE/events, lost connection, 429/5xx. | Accurate local state; no false claim of remote cancellation. |
| Image format | Feed fixture output: valid PNG/JPEG, HTML mislabeled as image, forged size, decompression bomb, EXIF rotated, 21 MiB payload, cross-scene asset reference. | Fail closed, no project replacement or unsafe download. |
| Video format | Fixture MP4 H.264, wrong codec, missing video, >19.65s, 21 MiB, non-monotonic timestamps. | No invalid candidate applied; actual export still checked by FFprobe/QC. |
| Snapshot integrity | Generate a proposal from revision N, edit project to N+1 before candidate returns, attempt apply. | 409 revision conflict and old approved assets preserved. |
| Language and semantic QC | Same fixed Vietnamese science brief, 9:16 and 16:9, 3 seeds each, human checks object count, wrong text, age, physics and continuity. | Scores + timestamped defects, not marketing screenshots; cannot auto-pass semantic quality. |
| Cost/accounting | Log measured GPU quota spent / billed credits vs estimate and number of failed calls. | Bounded per-project cost; provider differences explicit. |
| Model license | Record exact checkpoint variant, source revision, current terms and owner signoff before commercial rollout. | No ambiguous "license: other" treated as Apache. |

**Evidence completed for A06:** public documentation / model pages / source code / visible Space runtime statuses reviewed; model types, exact Space capabilities and the Wan2.1 DashScope dependency cross-checked. No secrets, workloads, billed requests, inference API probes, 1080p exports, GPU benchmarks, human quality scoring or existing repository regression were executed. This is **not** A08 integration testing and should not be counted among project pytest/Vitest/Playwright pass totals.

## 7. Follow-on features/problems to consider (proposals only)

- **Provider readiness panel (A08):** show local versus remote, exact model SHA, gated-license state, uptime/queue state, estimated per-request cost and whether sample generation was verified; show DISABLED/UNKNOWN rather than a deceptive green READY.
- **Per-scene provenance and budget ledger:** actual credits consumed, source/normalized hashes, approved candidate, provider revision and creator review. Must be outside sensitive project snapshots and not expose token or private raw prompts in logs.
- **Safety-first retry policy:** exponential backoff for transient errors with small retry bound, but never replay a chargeable inference without an idempotent/provider-supported mechanism or explicit consent. Store cost uncertainty.
- **Visual continuity regression pack:** fixed test scenes (blue shirt wet→dry; molecular evaporation; clothing sway; fold→spread; Vietnamese captions), reference first/middle/last frames, two aspects, motion/physics human-review rubric. Do not replace factual Blender diagrams with diffusion unless quality actually improves.
- **Beats-versus-render status:** the second-by-second storyboard currently describes editable intent but does not drive general keyframe animation. Display "plan-only / needs review" distinctly from "rendered motion verified"; coordinate with A01–A03, no edits in A06.
- **Review gate before publishing:** technical pass or model-card marketing claims must not bypass full playback, audio, age, source and creator approval. Keep manual upload/OAuth future milestone separate.

## 8. Primary sources accessed on 2026-10-30

- [S01] HF ZeroGPU documentation: https://huggingface.co/docs/hub/spaces-zerogpu
- [S02] HF Inference Providers billing: https://huggingface.co/docs/inference-providers/pricing
- [S03] HF Spaces GPU billing/hardware: https://huggingface.co/docs/hub/spaces-gpus
- [S04] Gradio Python Client: https://www.gradio.app/docs/python-client/client
- [S05] Gradio API visibility: https://www.gradio.app/guides/view-api-page
- [S06] Hugging Face access tokens: https://huggingface.co/docs/hub/security-tokens
- [S07] FLUX Schnell card/source/runtime: https://huggingface.co/black-forest-labs/FLUX.1-schnell · https://huggingface.co/spaces/black-forest-labs/FLUX.1-schnell/blob/main/app.py · https://huggingface.co/spaces/black-forest-labs/FLUX.1-schnell
- [S08] SD3.5 Large card/source/runtime: https://huggingface.co/stabilityai/stable-diffusion-3.5-large · https://huggingface.co/spaces/stabilityai/stable-diffusion-3.5-large/blob/main/app.py · https://huggingface.co/spaces/stabilityai/stable-diffusion-3.5-large
- [S09] Wan2.1 1.3B card/source/runtime: https://huggingface.co/Wan-AI/Wan2.1-T2V-1.3B · https://huggingface.co/spaces/Wan-AI/Wan2.1/blob/main/app.py · https://huggingface.co/spaces/Wan-AI/Wan2.1
- [S10] LTX-Video card/source/runtime: https://huggingface.co/Lightricks/LTX-Video · https://huggingface.co/Lightricks/LTX-Video/blob/main/LTX-Video-Open-Weights-License-0.X.txt · https://huggingface.co/spaces/Lightricks/ltx-video-distilled/blob/main/app.py · https://huggingface.co/spaces/Lightricks/ltx-video-distilled
- [S11] HF Space disk persistence notes: https://huggingface.co/docs/hub/spaces-storage
- [S12] Gradio cancel semantics: https://www.gradio.app/guides/getting-started-with-the-python-client

**Hand-off:** one documentation-only PR for A06, targeting feat/short-video-studio. Revalidate official prices and runtime status immediately before any future A08 implementation. No claim that source inspection equals production readiness.
