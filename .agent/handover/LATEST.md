---
status: partial
slug: whiteboard-video-tool
updated: 2026-10-30
---

# Handover — Whiteboard Studio

## Bảng hiện hành — 2026-10-31 ICT (lấy live GitHub làm chuẩn)

Canonical đã quan sát: `ba58bc8e9b48abdfd327d97b14d3e620c6795ace` ([PR #67](https://github.com/qualife1291/Auto-Tool-Video/pull/67) C03 E2E synchronization merged). **Refresh branch, issue, PR và CI đúng SHA trước mọi hành động.** BA01 phụ trách SRS/AC, phân việc và quyền sở hữu file; **C01–C05** là năm coder seat đã được owner kích hoạt. **T01 và T02 có quyền QA-PASS-CODE và merge code ngang nhau** theo [owner registry #70](https://github.com/qualife1291/Auto-Tool-Video/issues/70), nhưng mỗi PR có đúng **một QA_OWNER=T01 hoặc T02**, reviewer còn lại hỗ trợ khi cần. Không được tự QA/merge PR do chính mình viết. QA_OWNER khác chỉ takeover qua comment/handoff chính thức; mọi phát hiện BLOCKED phải được xử lý trước khi merge.

| Seat | Task/PR và trạng thái kiểm chứng |
| --- | --- |
| **BA01** | Role/Ready flow [PR #51](https://github.com/qualife1291/Auto-Tool-Video/pull/51) Ready nhưng A04 E2E cũ FAIL; cần sync canonical và retest. TR01 mới là vị trí read-only đề xuất. |
| **C01** | Peg anchor [#55 / PR #63](https://github.com/qualife1291/Auto-Tool-Video/pull/63) **Ready**, đã sync #67, FullHD và A02 Blender/A04 PASS; Main CI mới chưa hoàn tất ở thời điểm cập nhật, **QA_OWNER=T01**. |
| **C02** | Caption preview [#57 / PR #62](https://github.com/qualife1291/Auto-Tool-Video/pull/62) **Draft**, đã sync canonical, main + dual FullHD PASS, A04 chưa hoàn tất; không merge Draft. |
| **C03** | Beat persistence [#58 / PR #67](https://github.com/qualife1291/Auto-Tool-Video/pull/67) QA-PASS-CODE/**MERGED**; nghiên cứu [#49 / PR #65](https://github.com/qualife1291/Auto-Tool-Video/pull/65) **Draft/paused**. |
| **C04** | Fit Audio [#44 / PR #47](https://github.com/qualife1291/Auto-Tool-Video/pull/47) Ready, Main CI ở head cũ FAIL do shared E2E #58; cần sync/retest, **QA_OWNER=T01**. Media frame grid [#61 / PR #64](https://github.com/qualife1291/Auto-Tool-Video/pull/64) **Draft**, main/A04/dual1080 PASS trên head `813727e1...`, chờ chuyển Ready và **QA_OWNER=T02**. |
| **C05** | Proposed science beats [#68 / PR #69](https://github.com/qualife1291/Auto-Tool-Video/pull/69) **Ready**, ba CI head cũ PASS, chờ sync nhánh #67 và CI tích hợp, **QA_OWNER=T01**. |
| **T01/T02** | **QA_OWNER=T01:** #69, #63, #47. **QA_OWNER=T02:** #37, #60, #64 và PR tài liệu #46 (do T01 viết). [#37](https://github.com/qualife1291/Auto-Tool-Video/pull/37) đã có **4 scenario jobs PASS, 8 MP4 preview** 12/30/45/60s × 9:16/16:9 ở [run #41103011675](https://github.com/qualife1291/Auto-Tool-Video/actions/runs/41103011675); job scenario-native FullHD 12s **SKIPPED** có chủ ý, không phải PASS. #37 hiện **BLOCKED vì head cũ/chưa có CI current-base**, **không phải do audio QC đang FAIL**. eSpeak chỉ là fixture, creator G10 chưa ký duyệt. |

**Quy trình coder và QA-tooling/docs:** BA01 giao issue/AC và path → agent CLAIM → Draft PR → RED→GREEN, self-test exact HEAD → tác giả chuyển **Ready for review** → **QA_OWNER độc lập** rà soát code, CI exact-head và current-base/merge-ref, artifacts/scope → PASS-CODE hoặc CHANGES REQUESTED → chính QA_OWNER merge theo expected SHA → postmerge CI → **Creator G10** xem/nghe và ký duyệt nếu áp dụng. PASS ở head cũ, skipped, queued và Draft không thay thế bước nào. Role ID không đồng nghĩa tài khoản GitHub riêng.

### Archived planning snapshots (historical only; not live ownership)

## CURRENT verified multi-agent handoff — 2026-10-31 (supersedes earlier planning text below)

**Canonical:** `feat/short-video-studio` at observed merge SHA `97dfea49a712de2263648e187e08c4495098182b`. Refresh GitHub HEAD before any new action. Stable [role charter](../../docs/agent-role-charter.md); role/task contracts: [docs/agent-role-task-contracts.md](../../docs/agent-role-task-contracts.md); current [workboard](../../docs/agent-workboard.md), [short-term tasks](../memory/short-term/TASKS.md), BA [registry #31](https://github.com/qualife1291/Auto-Tool-Video/issues/31) / [Epic #26](https://github.com/qualife1291/Auto-Tool-Video/issues/26).

**People:** BA01 owns BA/PM/source research, assignments, shared-path conflict & release coordination; C01, C02, C03 and C04 are four owner-activated coder seats; C01/C02 newly registered ([#52](https://github.com/qualife1291/Auto-Tool-Video/issues/52), [#53](https://github.com/qualife1291/Auto-Tool-Video/issues/53)), currently AVAILABLE / UNASSIGNED; historical retired aliases are superseded; T01 owns independent technical QA, authorized gated PR code merges and hourly manual reports; creator owns final full-video watch/listen/rights signoff. Role ID is not GitHub login.

**Completed code integrations (human video QA NOT YET DONE):** C03 A02 [PR #34](https://github.com/qualife1291/Auto-Tool-Video/pull/34), C04 A03 [#35](https://github.com/qualife1291/Auto-Tool-Video/pull/35), A04 0.92× voice [#8](https://github.com/qualife1291/Auto-Tool-Video/pull/8), C04 P1-A WAV/MP4 beat invalidation [#40](https://github.com/qualife1291/Auto-Tool-Video/pull/40), C03 P1-C export frame cap [#42](https://github.com/qualife1291/Auto-Tool-Video/pull/42) **merged** at `97dfea49a712de2263648e187e08c4495098182b` after 335 pytest + 10 Vitest + 15 Playwright and dual FullHD/A04 regressions PASS on exact PR head. No inference of postmerge PASS until new merged-SHA workflows complete. Synthetic eSpeak is NOT approved Vietnamese narration.

**Active:** C03 [Harness #48](https://github.com/qualife1291/Auto-Tool-Video/issues/48) CLAIMED (new offline CLI/test/research files), #49 research queued; C04 [P1-B #44](https://github.com/qualife1291/Auto-Tool-Video/issues/44) assigned pending claim; exclusive `api.py::fit_audio` + new test, negative RED required. T01 [PR #37](https://github.com/qualife1291/Auto-Tool-Video/pull/37) 12/30/45/60s dual-aspect scenario videos remains QA-blocked by strict audio QC/actual MP4 proof, T01-owned. BA01 [Harness #38](https://github.com/qualife1291/Auto-Tool-Video/issues/38) and [iNew #39](https://github.com/qualife1291/Auto-Tool-Video/issues/39) are research-only, not implementation. Human user manual QA at [#36](https://github.com/qualife1291/Auto-Tool-Video/issues/36). A06–A10 are research/future backlog.

**Operational rules:** BA assigns/authorizes exclusive paths → coder claim/RED→GREEN/source PR → assigned independent QA_OWNER=T01 or T02 reviews current HEAD and integrated CI, merges only if all required checks PASS, updates BA → postmerge CI → creator actual video signoff (exact artifact hash) → BA marks feature/release. Every hour T01 reports test/standard research and manual checklist to owner. GitHub watcher [PR #43](https://github.com/qualife1291/Auto-Tool-Video/pull/43) is cron every 15 minutes or manual **ONLY**; `workflow_run` broad event trigger was removed after spam incident. Keep planned scope free-first and secrets out of Git.

### Historical handover below (2026-10-30 baseline; outdated statuses superseded by section above)



**Repository branch:** `feat/short-video-studio` is the canonical shared development branch. Current tracking: [workboard](../../docs/agent-workboard.md) A01–A10, [active tasks](../memory/short-term/TASKS.md), [roadmap](../../docs/development-plan.md), and [approved spec](../../specs/whiteboard-video-tool.md). This handover is a technical snapshot; do not confuse merged WIP with completed release.

## What is in source

- M1 baseline: 2D local web studio, import/render MP4 for both ratios, captions, audio-sync workflow, technical QC and creator review; local Ollama/ComfyAI adapter contract available for M2.
- Latest code additions: `SecondBeat` metadata, planner prompt/fallback, per-second editor, caption bounce, shirt wet/dry blend/sway/unfold. **A01 data integrity tests now verified; motion/voice behavior has not been manually reviewed in a new video export**.
- Current gaps: beat timeline not compiled to generic renderer keyframes; wet/dry alpha matching and glyph safe-zones need visual inspection. Voice 0.92× preserving pitch and its timeline, final new MP4, HF/NIM research and live AI provider benchmarking are **not complete**. A04/A05 are top blockers.

## Last verified historical baseline, not current QA

On the earlier commit `a7d000f6`, the prior handover recorded 182 pytest + 10 Vitest + 13 Playwright = **205 pass**; a 12-scene ~38.7-second sample in portrait and landscape passed technical QC. It still had six near-repeat/motion warnings per aspect; narration ASR exact-normalized 9/12, human playback/listening/fact/age review pending. Details: [QA review](../../docs/qa-review.md), [storyboard review](../../docs/storyboard-review.md), [quality standard](../../docs/video-quality-standard.md). Source snapshots and earlier handovers remain in Git history/`.agent/handover/`.

**A01 verified:** [GitHub Actions run 41052656718](https://github.com/qualife1291/Auto-Tool-Video/actions/runs/41052656718) passed at PR head `cb9b68bf` (merged as `3354ca8e`): Ruff/check format/mypy passed, **212 pytest passed / 1 skipped**, **10 Vitest passed**, Vite build/Prettier passed and **13 Playwright E2E passed**. Total **235 passed / 1 skipped**; one Starlette/httpx deprecation warning. This is a verified **code/contract** result, not a new video render or human content approval. The user's earlier local workspace change reports are not recoverable from GitHub without an explicit file upload.

## Next agents

1. Claim an ID A01–A10 via the workboard/PR; branch from `feat/short-video-studio`. Avoid overlapping write ownership.
2. A01 is done; A02/A03 continue motion and UI visual QA. A04 generate 0.92× audio from approved voice assets, log SHA/time, adjust scene timings without clipping. A05 independently rerun full tests and real portrait+landscape 1080p export, technical QC, and creator review.
3. A06/A07 investigate HF/Gradio and NVIDIA NIM with current official sources; do not treat ZeroGPU/limited trials as production-free or a safety model as a Kids certificate. A08 adapter after gates.
4. For all results, record **which exact commit**, environment/commands, exit status, artifacts/hashes, limitations and any blocked external access. Save outputs under ignored `.data/`; no cloud/social publish or secret upload.

## Launch and QA

See [README](../../README.md), [runbook](../../docs/agent-workboard.md) and the [video QA rubric](../../docs/video-quality-standard.md). Linux/Node24+/Python3.12+/uv/FFmpeg/Chromium for E2E. Native Windows/macOS, online AI live tests, GPU learned benchmarks, OAuth upload and manual reviewer sign-off remain outside established baseline.

**Historical checkpoints are preserved; future agents should update this handover only with new verified evidence.**
