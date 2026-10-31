# A07 — NVIDIA NIM provider evaluation

**Date:** 2026-10-30 (Asia/Ho_Chi_Minh)  
**Status:** DOC-RESEARCHED / LIVE-NOT-TESTED / INTEGRATION-NOT-APPROVED  
**Task:** [A07 in workboard](agent-workboard.md) · [claim issue #3](https://github.com/qualife1291/Auto-Tool-Video/issues/3)  
**Branch:** `agent/A07-nim-provider-evaluation` (target `feat/short-video-studio`)  
**Scope:** this document only. No code/config/secret, no remote inference, no cost or deployment commitment.

## Executive decision

**Do not integrate or replace the current Ollama/ComfyUI local providers yet.** NVIDIA's catalog documents relevant models and APIs, but access, per-account limits, latency, actual vi-VN quality, privacy suitability and production costs have **not been verified by an authenticated experiment**. A07 therefore produces a researched shortlist and a reproducible acceptance plan, **not** an A08 approval. Keep the no-required-paid-API baseline and explicit candidate/review/apply process intact.

| Candidate and intended role | Verified from NVIDIA docs/catalog | Still NOT VERIFIED | Decision |
| --- | --- | --- | --- |
| NVIDIA-hosted **DeepSeek-V4.1-Flash**, storyboard proposal | NVIDIA model page describes a multimodal text/image model and trial usage. NIM LLM family uses OpenAI-compatible `POST https://integrate.api.nvidia.com/v1/chat/completions` (verify exact model ID from the selected page/API catalog before calling). | This precise model's entitlement for our account, exact request schema and model ID in a live response, structured JSON strictness, Vietnamese scene/beat completeness, request/price limits, response time | Research candidate only; **no adapter** |
| **Magpie TTS Multilingual**, narration | Official model card lists Vietnamese among 12 languages, male and female speakers and an internal Vietnamese test set. The model-card CER figure is **upstream**; not a result on this project's voice corpus. | Whether a hosted inference endpoint is enabled for our account, request/voice API details, voice licenses, spoken numbers/acronyms/dialect, WAV sample format, loudness, speed, quality, quota and cost | Promising M3 candidate; **no TTS UI or active voice integration** |
| **Riva Translate**, translation / subtitle localization | Official Riva translation guide lists Vietnamese among supported languages; `riva-translate-1.6b` API page documents gRPC client, authentication metadata and querying supported pairs via `--list-models`. | Exact available model/version, enabled vi-VN direction pairs in our account, domain terminology, punctuation, latency, costs, retention | Optional translation candidate, **not** a forced aligner or TTS |
| **Meta Llama-Guard-4-12B** via NIM, safety screening | NVIDIA docs describe text/image safety classifier, `meta/llama-guard-4-12b` at chat completions, hazard labels and Llama 4 Community Model License. | Accuracy on children's Vietnamese educational scripts/visuals, false positive/negative rate, account entitlement, privacy, costs | Research-only additional signal. **Never certify YouTube Kids, legal compliance or factual accuracy** |

### Source identity and version caveats

- NVIDIA's LLM list shows **`deepseek-ai/deepseek-v4-flash`**, which is a *different* catalog listing from **`nvidia/deepseek-v4.1-flash`**. Never silently substitute their IDs, release versions, context size or license statements. The specific NVIDIA V4.1 model page should be the source of the selected model identifier and access contract.
- Hosted trial API and downloadable/self-hosted microservices are **different offerings**. Model-weight license, NVIDIA API trial terms, NIM container use and underlying creator/license terms must be checked separately; availability in a catalog does not mean perpetual free service or unrestricted commercial use.
- NVIDIA catalog updates over time. All facts above are documentation observations on the date shown, not pinned runtime behavior.

## Official references reviewed

1. [NVIDIA LLM NIM API reference](https://docs.api.nvidia.com/nim/reference/llm-apis) — common chat-completions endpoint and catalog listing.
2. [NVIDIA / DeepSeek V4.1 Flash model card](https://docs.api.nvidia.com/nim/reference/nvidia-deepseek-v4_1-flash) — model description, terms, reported release and intended use.
3. [DeepSeek-AI V4 Flash model card](https://docs.api.nvidia.com/nim/reference/deepseek-ai-deepseek-v4-flash) — distinct model identity; do not conflate with V4.1.
4. [Magpie TTS Multilingual model card](https://build.nvidia.com/nvidia/magpie-tts-multilingual/modelcard) — supported languages including Vietnamese, speakers, evaluation provenance.
5. [Riva Translation Overview](https://docs.nvidia.com/deeplearning/riva/user-guide/docs/translation/translation-overview.html) — Vietnamese in multilingual translation model's supported languages and language directions.
6. [Riva Translate 1.6B API](https://build.nvidia.com/nvidia/riva-translate-1_6b/api) — gRPC client example and model discovery, not OpenAI chat API.
7. [Llama Guard 4 12B model card](https://docs.api.nvidia.com/nim/reference/meta-llama-guard-4-12b) and [inference API](https://docs.api.nvidia.com/nim/reference/meta-llama-guard-4-12b-infer) — safety categories, modality, license, endpoint.
8. [NVIDIA NIM General FAQ](https://docs.api.nvidia.com/nim/docs/product) — Developer Program prototype access, separate enterprise trial.
9. [NVIDIA-hosted Llama Guard listing](https://build.nvidia.com/meta/llama-guard-4-12b) — trial privacy notice explicitly says inputs/outputs may be recorded to provide/improve service.

**Evidence type:** public provider docs, not API calls. No API key was accessed, no paid credits bought, no models/weights installed or executed. Documentation is subject to provider changes.

## Product and security gates before A08

1. **Access/quota/cost:** with an explicitly authorized developer account, read the current console's concrete entitlements, quota, rate limits, supported model IDs, and billing rules. Record date/region and 401/403/429 handling. Treat prototype or trial credits as finite unless the provider explicitly confirms ongoing terms.
2. **Privacy:** do not submit unpublished narration, minors' information, personal audio, private project assets or secret tokens to hosted endpoints without specific user permission. Evaluate recording/retention and data-sharing terms **per service**. Store credentials only server-side and redact tokens, source text and outputs from logs.
3. **Vietnamese quality:** run an original, consented fixed 20-cue vi-VN benchmark with numbers, names, accents, scientific terminology and age-appropriate tone. Blind human listen for TTS, word error/CER as descriptive signals, audio duration, clipped syllables, pronunciation, source fidelity; compare to authorized local baseline. For translation, verify exact vi/en directions, named entities, scientific facts and subtitle lengths with human review.
4. **Storyboard contract:** feed the same original brief to candidate and Ollama; validate against `planning.validate_proposal` and `SecondBeat` coverage of `ceil(scene.duration)` with no invented sources; preserve mode must reproduce user narration and ordered source IDs. Limit retries, response sizes and latency, record exact model/ref.
5. **Safety:** evaluate a Vietnamese education-specific labeled sample set including disallowed claims and benign examples; measure false-negative/false-positive, record policy/version. Safety screening is advisory and never replaces creator review, knowledge verification, audience decision or platform requirements.
6. **Operational:** explicit opt-in **per provider**; bounded timeout, authenticated requests, no redirects to unrelated hosts, server-only credentials, idempotency/revision semantics, cancellation, provenance (provider/model/version/request fingerprint), failures safe against replacing an approved asset, local-independent fallback with no unexpected charges.
7. **Licenses:** archive terms applicable to hosted service and downloaded weights at time of activation; legal/rights review before distributing media generated using any voice/model, including attribution and commercial usage where applicable.

### Live test recording template (NOT RUN)

| Check | Pass evidence required | Current result |
| --- | --- | --- |
| Authenticated model discovery / exact ID | Redacted response, date, region, status | **NOT RUN — no authorized API credentials** |
| Hosted storyboard output against strict schema | JSON validation cases, source-preserve diff, timestamps, model/version | **NOT RUN** |
| 20 Vietnamese TTS samples | Consent/license, WAV hashes, original text, native listening scores, WER/CER limits and audio tech checks | **NOT RUN** |
| Riva vi-VN translation directions | `--list-models` redacted output, direction and translation samples | **NOT RUN** |
| Llama Guard Vietnamese moderation | Labeled set, confusion matrix, per-category accuracy/false alarms | **NOT RUN** |
| Quota, privacy, billing, rate limit | Account-specific contract/console evidence without tokens | **NOT RUN** |
| A08 regression and real video exports | Ruff, mypy, pytest, TS, Vitest, Playwright, 1080p both ratios, QC, manual review | **OUT OF A07 SCOPE — NOT RUN** |

## A07 document-only validation

- The PR must change **only** `docs/provider-evaluation-nim.md`.
- Every provider capability assertion above is attributed to a dated **official** URL. No fabricated token, benchmark run, paid-tier access or hosted API success.
- Internal paths/links and task ownership must match this repository; open PR **toward `feat/short-video-studio`**, not direct merge.
- **Acceptance limit:** public-documentation evaluation can be marked `DOC-RESEARCHED`, but full A07 live-provider gate and A08 implementation remain blocked pending credentials/permission and reproducible test artifacts.

## Recommended next action

Close the documentation-only research subtask after review if desired; keep A07's live validation in a separate follow-up issue or leave this issue open. Proceed to provider adapter A08 **only after** its required authorization, privacy, pricing and real Vietnamese evaluations pass. Do not start unrelated work automatically after this documentation PR.
