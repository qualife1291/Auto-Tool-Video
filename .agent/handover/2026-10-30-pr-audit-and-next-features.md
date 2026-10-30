# PR audit, integration handover and next-feature context — 2026-10-30

**Status:** CURRENT-EVIDENCE SNAPSHOT / TEN PRs OPEN / RELEASE-NOT-APPROVED  
**Canonical:** `feat/short-video-studio` @ `58a939503f0ef5eb80ebec261bfe798928d3ee7b`  
**Claim:** [Issue #22](https://github.com/qualife1291/Auto-Tool-Video/issues/22). Documentation-only, no code, media or CI changes.  
**Do not confuse:** a PR head's green CI, a clean merge simulation, an actual canonical merge, and creator acceptance are four different states.

## 1. GitHub snapshot: 10 PRs still unmerged

All listed PRs are OPEN and GitHub currently reports `mergeable=true` **against canonical individually**. Check exact SHAs again immediately before merging; one successful PR-to-base comparison does not guarantee a future sequence without conflicts.

| PR | Scope / files | Exact head SHA (prefix) | Observed verification / disposition |
| --- | --- | --- | --- |
| [#4](https://github.com/qualife1291/Auto-Tool-Video/pull/4) A07 NVIDIA NIM | New provider research document only | `67ab4337` | **DOC REVIEW**; no PR-head Actions checks and no account/API live benchmark. Do not activate paid/cloud provider. |
| [#7](https://github.com/qualife1291/Auto-Tool-Video/pull/7) A06 Hugging Face/Gradio | New provider research document only | `cec3af1b` | **DOC REVIEW**; no PR-head Actions checks, no real cloud inference or billable provider agreement. |
| [#8](https://github.com/qualife1291/Auto-Tool-Video/pull/8) A04 voice | 7 files, `audio_tempo.py`, `create_story_video.py`, 12-WAV test harness/CI | `a5776f23` | Full [A04 CI #41066889036](https://github.com/qualife1291/Auto-Tool-Video/actions/runs/41066889036) PASS: 235 pytest, 10 Vitest, 13 Playwright; 12 **eSpeak synthetic** cues, 2 1080p 31.4s MP4, QC and hashes. **Not original VieNeu**; human acceptance pending. |
| [#10](https://github.com/qualife1291/Auto-Tool-Video/pull/10) A03 QA | 2 new caption/bounce + beat-save/reload tests | `b5678295` | [CI #41060285243](https://github.com/qualife1291/Auto-Tool-Video/actions/runs/41060285243) PASS. Tests do not implement beat-to-motion compiler or substitute mobile visual sign-off. |
| [#12](https://github.com/qualife1291/Auto-Tool-Video/pull/12) A02 QA | 3 new tests and Blender real PNG motion verifier/CI | `dcf4e017` | [Blender QA #41064445011](https://github.com/qualife1291/Auto-Tool-Video/actions/runs/41064445011) PASS; [canonical CI](https://github.com/qualife1291/Auto-Tool-Video/actions/runs/41064444999) PASS. Physics/cloth continuity still requires visual playback by creator. |
| [#14](https://github.com/qualife1291/Auto-Tool-Video/pull/14) A05 QA process | New `docs/qa-evidence-gates.md` | `ad719972` | [CI #41066463774](https://github.com/qualife1291/Auto-Tool-Video/actions/runs/41066463774) PASS; **process only**, creator not signed. |
| [#16](https://github.com/qualife1291/Auto-Tool-Video/pull/16) dual-FullHD QA | 3 new verifier/tests/workflow | `f2b4b7eb` | [1080p media CI #41067677622](https://github.com/qualife1291/Auto-Tool-Video/actions/runs/41067677622) and [canonical CI](https://github.com/qualife1291/Auto-Tool-Video/actions/runs/41067677684) PASS; sine-engineering clips only. |
| [#18](https://github.com/qualife1291/Auto-Tool-Video/pull/18) exact-SHA integration | New ephemeral merge/test workflow | `7f1b84f6` | **Mixed check results:** [exact-SHA integration #41071418459](https://github.com/qualife1291/Auto-Tool-Video/actions/runs/41071418459) PASS: **311 pytest / 10 Vitest / 15 Playwright / no skips**, real 1080p and 12-cue eSpeak both aspects. [Standard workflow #41071418465](https://github.com/qualife1291/Auto-Tool-Video/actions/runs/41071418465) is reported **failure** at run level while its job API shows `queued`; investigate/re-run rather than describing every check as green. Its fixed base and pinned heads become stale after each merge. |
| [#20](https://github.com/qualife1291/Auto-Tool-Video/pull/20) A05 frame QC | `quality.py` + new adversarial PTS tests | `b2257cf8` | [CI #41071036094](https://github.com/qualife1291/Auto-Tool-Video/actions/runs/41071036094) PASS: 229 pytest, 1 Blender skip, 10 Vitest, 13 Playwright. Catches missing/start-shifted frames without relaxing QC. Included in exact-SHA integration #18 PASS. |
| [#21](https://github.com/qualife1291/Auto-Tool-Video/pull/21) research-first / formats roadmap | `AGENTS.md`, workboard, plan, 2 new research docs | `84bbb365` | [CI #41073616069](https://github.com/qualife1291/Auto-Tool-Video/actions/runs/41073616069) PASS. **Review requested**: workboard stale statuses vs PR evidence; AGENTS still says A01–A10 while roadmap proposes A11–A33; G0–G6 research versus G0–G11 QA need distinct names. No runtime features added. |

**Conflict observation:** filename ownership checked across all ten PRs. The changed paths do not directly overlap one another; `#21` owns shared rules/workboard/plan and **must not** be edited concurrently. Actual cross-PR merge simulation `#18` passed for pinned #4/#7/#8/#10/#12/#14/#16/#20, **not #21**, and never proves creator approval.

## 2. What truly exists on canonical versus on PR heads

- **Canonical, already merged:** A01 SecondBeat data schema/planner/legacy preservation, M1 FastAPI/React/SQLite editor + 9:16/16:9 FFmpeg/H.264 export, local Ollama/ComfyUI adapters, technical QC and manual review interface. Baseline smoke and development features exist, but current PR-only changes are **not present on canonical**.
- **Proposed but unmerged in code:** A04 measured `atempo=0.92` WAV path, A05 strict expected-frame/timestamp validation, negative caption-motion/beat E2E, Blender wet/dry tests, independent 1080p and exact-SHA integration workflows.
- **Documented but unmerged:** A05 QA0–QA11 evidence contract, A06/A07 cloud-provider research, A11 research RG0–RG6 and 15-format future roadmap.
- **Still NOT COMPLETED by technical tests:** original approved VieNeu 12-scene ~41.9s video, native-speaker listening/ASR correction, real story-specific cloth transition and caption/beat visual acceptance, human fact/child-suitability/rights signoff, renderer compilation of arbitrary authored beats, full TTS UI/forced alignment/SRT, direct social OAuth publishing or live paid AI provider adapters. Synthetic `eSpeak` QA 31.4s is **not** the original voice, creative movie or release approval.
- **Status language:** `MERGED-VERIFIED`, `PR-CI-VERIFIED`, `PR-DOC-REVIEW`, `PR-CI-INCOMPLETE`, `UNIMPLEMENTED`, `BLOCKED-BY-HUMAN/ASSET`. Do not replace these with blanket `DONE`.

## 3. Recommended safe merge/integration protocol (not automatic approval)

1. For each PR read full changed-file list/review notes, exact head/base SHAs and current GitHub check runs. A green check from a previous head or ephemeral combined commit is historical. Ask for independent review on any output-affecting code.
2. Prioritize narrow QC/test changes **#20, #10, #12, #16** (conditional on latest CI), then voice implementation **#8** (with real WAV and safety checks). Review documentation **#14, #4, #7** independently; **#21** only after status/gate terminology review; **#18** integration workflow must be reviewed last or refreshed after every merge. This is a dependency preference, not license to merge on the user's behalf.
3. After **every** merge update canonical SHA and refresh #18's base + pinned branch heads. Run canonical full lint/format/mypy/pytest, TS/Vitest/Playwright/build, Blender+eSpeak WAV, full 1080p both aspects, FFprobe/PTS/decoded-frame QC, per-audio LUFS/truepeak and SHA reconciliation on the **new merge commit**. Do not silently skip required tests.
4. For #18's unresolved run-level failure/queued job (despite separate integration PASS), obtain a clean standard CI run and root cause. If it is a provider Actions reporting inconsistency, record API evidence and obtain a new green run; do not fabricate a pass.
5. Keep developer/creator review separate from CI: detailed generated video must be watched in full by a reviewer with timestamped issues and explicit `approved` against artifact hashes; only then discuss publication readiness.
6. No direct edits to other agent branches; coordinate through issues/PR comments. No auto-merge, auto-publish, model download, paid API or credential handling.

## 4. Next implementation roadmap (PROPOSED only, no code authorization)

**Immediate P0 (finish integration and real quality):** complete reviews/merge sequence #4–#21; fix canonical handover/workboard status drift; run exact merged-commit CI, A02 cloth continuity and A03 caption/layout human QA; A05 approved original Vietnamese audio/full story + science/age/rights check. Existing deterministic and local-first output remain default.

**Foundation P0/P1:** A12 reproducible benchmark/fixture manifest and hardware measurements (after coordinating A05); A15 Vietnamese transcript/forced-alignment and SRT research after A04. Require corpus + native review; ASR ≠ ground truth. Decide a versioned **Scene IR** (A20) with 30fps duration_frames, stable object IDs, camera, keyframes, text/audio cues, provenance and backward-compatible project migrations before adding generic beat-to-render compiler.

**Isolated engine research P1:** A13 Animate-style procedural Canvas POC (license/commit pinned, no direct import), A14 only then an adapter/scene compiler; A16 research orchestration/retry/approval, A17 optional learned QC calibrated to people; A18 only after A06/A07/A08 provider access/privacy/cost gates; A19 accessible creator UX. #21's research-first gating and rollback is required but **still unmerged**.

**Future coverage A20–A33 (15 format categories; all research-only):** whiteboard/explainer, kinetic typography, math/charts, science simulation, artistic styles, 2D characters, documentary/stock, product/UI demos, motion comics, AI cinematic I2V/T2V, mixed-media, long-form course, localization, series/batch, multi-aspect social packages. The proposed A20–A33 map respectively to Scene IR + 1:1/4:5; motion-type kits; Manim; Blender physics; rig/characters; stock rights; UI capture privacy; hybrid composition; long-form resume; localization; batch series; native square/4:5; AI-video shot continuity; creator QC console.

**Research security and product stop rules:** keep local-first; any third-party provider requires separate code/weight/asset/output license, privacy/consent, quota/price/region tests and authorized live quality benchmark. A11 RG0–RG6 (research & implementation process) and A05 QA0–QA11 (technical + human release evidence) serve **different purposes**. Proposals are not automatically approved technical specs or open coding tasks.

## 5. Handover checklist for the next agent

- Check [live open PRs](https://github.com/qualife1291/Auto-Tool-Video/pulls) and the newest canonical SHA before choosing a task. `AGENTS.md` and workboard on canonical may lag this snapshot until their respective PRs merge.
- Record `branch + base SHA + PR head SHA + CI run/job IDs + media SHA + owned files`. Claim one task and avoid overlap.
- First ask **what has actually merged**; don't interpret a green A04 or combined test as proof that its code lives on canonical.
- Never confuse 31.4s eSpeak sample with ~41.9s original VieNeu narrative, synthetic static drawings with tested natural physics, or machine QC `passed` with creator `approved`.
- New video format architecture, AI/video providers and upload integrations are *research/backlog*, not functional features. Refresh upstream license/version and compare a fixed reference video before writing new implementations.
- If an agent changes the shared branch after this document is created, **this snapshot becomes historical immediately**. Update with a new dated entry or an explicitly reviewed handover, and rerun integrations on the new commit.
