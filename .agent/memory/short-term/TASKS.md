# Việc đang code — snapshot 2026-10-31

**Canonical:** `feat/short-video-studio` @ `09c4a8ea858e26f7e3f0b5147377d9d0930a541a` khi cập nhật; **refresh HEAD GitHub trước mỗi hành động**. Nguồn phân vai/ownership/AC: [stable role charter](../../../docs/agent-role-charter.md), [Agent Role and Task Contracts](../../../docs/agent-role-task-contracts.md), [BA registry #31](https://github.com/qualife1291/Auto-Tool-Video/issues/31) và [workboard](../../../docs/agent-workboard.md). **BA01** điều phối/PM/R&D; **C01/C02/C03/C04** dev; **T01** QA độc lập và code-merge gate khi đủ evidence; **Creator** nghiệm thu video. C01/C02 được chủ dự án kích hoạt mới ([#52](https://github.com/qualife1291/Auto-Tool-Video/issues/52), [#53](https://github.com/qualife1291/Auto-Tool-Video/issues/53)), AVAILABLE / chưa claim task hay source.

## Latest verified handoff after T01 merged QA race fix — 2026-10-31

**Canonical code:** `ba58bc8e9b48abdfd327d97b14d3e620c6795ace` after independent T01 [PR #67](https://github.com/qualife1291/Auto-Tool-Video/pull/67) merge. C03 beat-persistence E2E test now waits for matching async PUT/save revision and verifies persisted GET; main/dual1080 CI on **merge SHA queued at audit**, so do not count merged-SHA PASS early. Prior `C03 #58 claim pending` entries below are historical.

| Role | Verified current role / task |
| --- | --- |
| **BA01** | Owns assignments, reusable role charter [PR #51](https://github.com/qualife1291/Auto-Tool-Video/pull/51) about TR01/C01–C05/Draft→Ready, **QA-BLOCKED** on old exact-head A04 E2E until integrated retest; [Epic #26](https://github.com/qualife1291/Auto-Tool-Video/issues/26). |
| **C01** | [#55](https://github.com/qualife1291/Auto-Tool-Video/issues/55) / [PR #63](https://github.com/qualife1291/Auto-Tool-Video/pull/63) peg-anchor art **Ready for review but old main CI FAILED at beat-persistence E2E**, must sync/retest with merged #67. |
| **C02** | [#57](https://github.com/qualife1291/Auto-Tool-Video/issues/57) / [PR #62](https://github.com/qualife1291/Auto-Tool-Video/pull/62) caption preview **Draft**, latest code integration tests ongoing. |
| **C03** | [#58 / PR #67](https://github.com/qualife1291/Auto-Tool-Video/pull/67) **QA-PASS-CODE / MERGED** `ba58bc8...`; [#49 / PR #65](https://github.com/qualife1291/Auto-Tool-Video/pull/65) research **Draft/paused**, may be reprioritized by BA01. |
| **C04** | [#44 / PR #47](https://github.com/qualife1291/Auto-Tool-Video/pull/47) Fit Audio **Ready but old main CI red from #58**, needs fresh integrated tests; [#61 / PR #64](https://github.com/qualife1291/Auto-Tool-Video/pull/64) imported frame-grid **Draft** at latest inspection. |
| **C05** | [#68 / PR #69](https://github.com/qualife1291/Auto-Tool-Video/pull/69) proposed science beats **Ready + three old-base HEAD CI green**, independent T01 **integration HOLD** until sync with #67 merged SHA and new combined CI. |
| **T01/T02** | T01 primary independent merge authority; T02 independent supplementary QA/test sharing, no implied release signoff. [#37](https://github.com/qualife1291/Auto-Tool-Video/pull/37) QA scenario FullHD artifact still strict-audio QC blocked; [#60](https://github.com/qualife1291/Auto-Tool-Video/pull/60) watcher fix Draft. Human creator review [#36](https://github.com/qualife1291/Auto-Tool-Video/issues/36) remains separate. |

**Gate:** Only coder-submitted non-Draft **Ready for review** PR with exact-current-base integrated CI, owned diff, complete T01 QA can merge; no old-SHA CI reuse. `QA-PASS-CODE` ≠ creator video approval. Earlier snapshot headings below are kept for history, not current assignments.

## Live role/task refresh — 2026-10-31 02:35 ICT (overrides older historical snapshots)

| Role | Current BA assignment / live GitHub status |
| --- | --- |
| **BA01** | Product/PM/Technology Scout; stable charter #45 merged, update [PR #51](https://github.com/qualife1291/Auto-Tool-Video/pull/51) adds TR01 proposal and C01/C02 workflow, but **A04 E2E failed, PR not merged**. |
| **C01** | Owner-reactivated [#52](https://github.com/qualife1291/Auto-Tool-Video/issues/52), BA-assigned peg motion [#55](https://github.com/qualife1291/Auto-Tool-Video/issues/55); [PR #63](https://github.com/qualife1291/Auto-Tool-Video/pull/63) **Draft**, main CI failed; no merge. |
| **C02** | Owner-activated [#54](https://github.com/qualife1291/Auto-Tool-Video/issues/54), BA-assigned caption preview [#57](https://github.com/qualife1291/Auto-Tool-Video/issues/57); [PR #62](https://github.com/qualife1291/Auto-Tool-Video/pull/62) **Draft**, CI ongoing; no merge. |
| **C03** | Harness [#48 / PR #56](https://github.com/qualife1291/Auto-Tool-Video/pull/56) **merged** at `980b7185b4cbcabf02d33edd1b4ba98ca9f89328`; urgent [Playwright issue #58](https://github.com/qualife1291/Auto-Tool-Video/issues/58) assigned/claim pending; P2 research [#49 / PR #65](https://github.com/qualife1291/Auto-Tool-Video/pull/65) paused/Draft. |
| **C04** | [P1-B #44 / PR #47](https://github.com/qualife1291/Auto-Tool-Video/pull/47) Ready for T01 but QA **BLOCKED** by #58 shared E2E failure; [P1-D #61 / PR #64](https://github.com/qualife1291/Auto-Tool-Video/pull/64) Draft. |
| **T01** | Independent QA/merge upon current-base exact-SHA PASS; [scenario #37](https://github.com/qualife1291/Auto-Tool-Video/pull/37) actual MP4 QC blocked, [GitHub watcher #59 / PR #60](https://github.com/qualife1291/Auto-Tool-Video/pull/60) Draft; creator feedback [#36](https://github.com/qualife1291/Auto-Tool-Video/issues/36). |
| **C05** | New [onboarding #66](https://github.com/qualife1291/Auto-Tool-Video/issues/66), awaiting BA01 reservation, not yet claimed an active task. |

**Required coder handoff:** `ASSIGNED → CLAIMED → DRAFT PR → SELF-TEST exact SHA → READY FOR REVIEW → T01 independent QA → QA PASS / FIX REQUESTED → T01 gated MERGE → postmerge CI → creator human approval`. Draft and pending/failed CI cannot be merged. GitHub identity and agent role ID are not interchangeable. Historical statuses below are evidence snapshots, not current assignments.

## Active work / trạng thái chính thức

| Agent | Task / PR | Status / next concrete step |
| --- | --- | --- |
| **C01** | [Registry #52](https://github.com/qualife1291/Auto-Tool-Video/issues/52) | AVAILABLE / UNASSIGNED, không thừa kế claim cũ, chờ BA01 giao task có AC/file scope. |
| **C02** | [Registry #53](https://github.com/qualife1291/Auto-Tool-Video/issues/53) | AVAILABLE / UNASSIGNED, không thừa kế claim cũ, chờ BA01 giao task có AC/file scope. |
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

1. BA01 task spec/AC + single-writer path reservation; C01/C02/C03/C04 claim by issue, base SHA, branch, files, conflict check. Coder RED→GREEN with negative/happy/boundary and current-head lint/types/pytest/Vitest/E2E/dual FullHD.
2. T01 reviews diff/ownership/current integrated SHA/checks. FAIL or NOT RUN → leave PR open and return to correct owner; all mandatory PASS → T01 authorized merge to canonical with expected HEAD SHA, postmerge CI and BA01 comment.
3. **Every hour** T01 must send user actual result PASS/FAIL/BLOCKED/NOT RUN, a verified downloadable preview/FullHD link if available (else OLD BUILD/NO BUILD), 3–6 steps manual test and ask feedback. Log issue/device/aspect/timestamp/expected/actual to [#36](https://github.com/qualife1291/Auto-Tool-Video/issues/36). Creator exact video hash watch/listen before feature DONE and release.
4. All claims need exact commit/run/video SHA; no fabricated media, no unapproved paid provider, no premature social publishing. See [quality gates](../../../docs/qa-evidence-gates.md) and [approved spec](../../../specs/whiteboard-video-tool.md).

**Historical statuses in earlier handovers/PR #23/#21 are not current; preserve provenance, update before integration.**
