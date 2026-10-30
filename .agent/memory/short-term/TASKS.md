# Việc đang code — snapshot 2026-10-31

**Canonical:** `feat/short-video-studio` @ `09c4a8ea858e26f7e3f0b5147377d9d0930a541a` khi cập nhật; **refresh HEAD GitHub trước mỗi hành động**. Nguồn phân vai/ownership/AC: [stable role charter](../../../docs/agent-role-charter.md), [Agent Role and Task Contracts](../../../docs/agent-role-task-contracts.md), [BA registry #31](https://github.com/qualife1291/Auto-Tool-Video/issues/31) và [workboard](../../../docs/agent-workboard.md). **BA01** điều phối/PM/R&D; **C03/C04** dev; **T01** QA độc lập và code-merge gate khi đủ evidence; **Creator** nghiệm thu video. C01/C02 không còn active.

## Active work / trạng thái chính thức

| Agent | Task / PR | Status / next concrete step |
| --- | --- | --- |
| **BA01** | [Epic #26](https://github.com/qualife1291/Auto-Tool-Video/issues/26), [#31](https://github.com/qualife1291/Auto-Tool-Video/issues/31); research [#38](https://github.com/qualife1291/Auto-Tool-Video/issues/38), [#39](https://github.com/qualife1291/Auto-Tool-Video/issues/39) | ACTIVE: cập nhật AC/owner/file scopes, backlog, SDLC/harness FREE-first, release plan. Research NOT implementation. |
| **C03** | **P1-C [#41](https://github.com/qualife1291/Auto-Tool-Video/issues/41)** / [PR #42](https://github.com/qualife1291/Auto-Tool-Video/pull/42) | **CODE MERGED** at `97dfea49a712de2263648e187e08c4495098182b`, exact synced-head main CI 335 pytest, 10 Vitest, 15 Playwright, dual1080 and A04 PASS. Merged-SHA CI and creator gate remain separately pending. P1-C reservation complete; C03 available for new BA01 assignment. |
| **C04** | **P1-B [#44](https://github.com/qualife1291/Auto-Tool-Video/issues/44)** | BA ASSIGNED / CLAIM PENDING. Prove 19.65s audio + 1s pause causes >20s scene via actual RED; then minimal `backend/auto_tool_video/api.py::fit_audio` validation + NEW `backend/tests/test_fit_audio_scene_limit.py`. No overlap C03. |
| **T01** | QA [#17](https://github.com/qualife1291/Auto-Tool-Video/issues/17), creator feedback [#36](https://github.com/qualife1291/Auto-Tool-Video/issues/36), four-content scenarios [PR #37](https://github.com/qualife1291/Auto-Tool-Video/pull/37) | Hourly PR/CI + random focused regression/standards research + mandatory manual report every time. PR #37 still BLOCKED by strict final audio QC pending four-story dual MP4 evidence; fix owned QA fixture, not C03/C04 product code. Independent code merges on verified current SHA only, report BA01. |

## Code integrated — human review outstanding

- **A01** [PR #2](https://github.com/qualife1291/Auto-Tool-Video/pull/2) baseline beat data integrity.
- **A02/C03** [PR #34](https://github.com/qualife1291/Auto-Tool-Video/pull/34) cloth/Blender **CODE MERGED / technical PASS**; human motion continuity/physics both aspects pending.
- **A03/C04** [PR #35](https://github.com/qualife1291/Auto-Tool-Video/pull/35) captions/beat UI **CODE MERGED / technical PASS**; creator typography/bounce/safe zones pending.
- **A04** [PR #8](https://github.com/qualife1291/Auto-Tool-Video/pull/8) voice 0.92× **CODE MERGED / real dual FullHD synthetic audio technical PASS**; approved original speaker/voice and human listening NOT RUN.
- **P1-A/C04** [PR #40](https://github.com/qualife1291/Auto-Tool-Video/pull/40) WAV/MP4 import duration invalidates authored beat approval, verified RED→GREEN, **CODE MERGED** at `09c4a8ea858e26f7e3f0b5147377d9d0930a541a`.
- **GitHub T01 watcher** [PR #43](https://github.com/qualife1291/Auto-Tool-Video/pull/43) emergency spam fix **MERGED**, now cron **every 15 minutes only** plus manual dispatch, not after each CI.
- **A05/human creator signoff** [#36](https://github.com/qualife1291/Auto-Tool-Video/issues/36) and final release gate remain BLOCKED. CI-green ≠ human-approved video.

## Mandatory workflow

1. BA01 task spec/AC + single-writer path reservation; C03/C04 claim by issue, base SHA, branch, files, conflict check. Coder RED→GREEN with negative/happy/boundary and current-head lint/types/pytest/Vitest/E2E/dual FullHD.
2. T01 reviews diff/ownership/current integrated SHA/checks. FAIL or NOT RUN → leave PR open and return to correct owner; all mandatory PASS → T01 authorized merge to canonical with expected HEAD SHA, postmerge CI and BA01 comment.
3. **Every hour** T01 must send user actual result PASS/FAIL/BLOCKED/NOT RUN, a verified downloadable preview/FullHD link if available (else OLD BUILD/NO BUILD), 3–6 steps manual test and ask feedback. Log issue/device/aspect/timestamp/expected/actual to [#36](https://github.com/qualife1291/Auto-Tool-Video/issues/36). Creator exact video hash watch/listen before feature DONE and release.
4. All claims need exact commit/run/video SHA; no fabricated media, no unapproved paid provider, no premature social publishing. See [quality gates](../../../docs/qa-evidence-gates.md) and [approved spec](../../../specs/whiteboard-video-tool.md).

**Historical statuses in earlier handovers/PR #23/#21 are not current; preserve provenance, update before integration.**
