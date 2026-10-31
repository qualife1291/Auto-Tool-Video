# Việc đang code — snapshot 2026-10-31

**Canonical:** `feat/short-video-studio` @ `09c4a8ea858e26f7e3f0b5147377d9d0930a541a` khi cập nhật; **refresh HEAD GitHub trước mỗi hành động**. Nguồn phân vai/ownership/AC: [stable role charter](../../../docs/agent-role-charter.md), [Agent Role and Task Contracts](../../../docs/agent-role-task-contracts.md), [BA registry #31](https://github.com/qualife1291/Auto-Tool-Video/issues/31) và [workboard](../../../docs/agent-workboard.md). Đoạn mở đầu này được viết tại checkpoint ban đầu; bảng ngày 2026-10-31 phía dưới mới là tình trạng đã kiểm chứng. **BA01/BA02 đồng cấp; C01–C05 đang hoạt động; T01/T02 ngang quyền QA/merge theo từng QA_OWNER.**

## Current verified role and work status — 2026-10-31 ~11:00 ICT

**Canonical:** `feat/short-video-studio` @ `3868fcf0d068b18033516470f942ec393ba9d378` ([T02-QA-merged research PR #81](https://github.com/qualife1291/Auto-Tool-Video/pull/81)); postmerge [Main #41165945577](https://github.com/qualife1291/Auto-Tool-Video/actions/runs/41165945577) and [Dual #41165945740](https://github.com/qualife1291/Auto-Tool-Video/actions/runs/41165945740) SUCCESS. This is a **dated evidence snapshot**; GitHub live issues, PRs, current HEAD and required CI outrank any later-stale line here.

**Governance:** **BA01 and BA02 are co-equal** ([#31](https://github.com/qualife1291/Auto-Tool-Video/issues/31), [#72](https://github.com/qualife1291/Auto-Tool-Video/issues/72)); **T01 and T02 have equal independent QA-PASS-CODE/eligible merge authority**, with **one QA_OWNER per PR**, independent of its author ([#70](https://github.com/qualife1291/Auto-Tool-Video/issues/70)). **C01–C05** are five staffed coder seat IDs; role families `BA/C/T` are separate from numbered seats. New `TR / AIQ / VD / OPS` categories are **research proposals only** [#82](https://github.com/qualife1291/Auto-Tool-Video/issues/82)/[PR #83](https://github.com/qualife1291/Auto-Tool-Video/pull/83): no automatically created seat, scheduler, GitHub identity or authorization.

| Accountable seat | Observed task/PR status, linked evidence |
| --- | --- |
| **BA01 + BA02** | Co-coordinate roadmaps, assignments, role charter, FREE-first research and source/skill refresh; [BA01 charter PR #51](https://github.com/qualife1291/Auto-Tool-Video/pull/51) still Ready/old-base A04 FAIL; [BA02 new-doc PR #73](https://github.com/qualife1291/Auto-Tool-Video/pull/73) Ready/old-base 3 CI green but current integration pending; [DOC cleanup #75](https://github.com/qualife1291/Auto-Tool-Video/issues/75) open. Proposed specialist role research [#83](https://github.com/qualife1291/Auto-Tool-Video/pull/83) Ready/old-base CI green, activation deferred. |
| **C01** | [Peg pivot #55 / PR #63](https://github.com/qualife1291/Auto-Tool-Video/pull/63) **MERGED** `fecfea79...`; [30 FPS art evidence #74 / PR #76](https://github.com/qualife1291/Auto-Tool-Video/pull/76) **Ready**, latest-current-base Main/A02 Blender/Dual FullHD PASS, A04 regression **in progress at this checkpoint**, independent **QA_OWNER=T01**; composite-alpha/garment safe-zone risks remain open for native visual review. |
| **C02** | [Caption preview #57 / PR #62](https://github.com/qualife1291/Auto-Tool-Video/pull/62) **MERGED** `73717943...` after T01 independent code QA; [new offline Vietnamese storyboard eval #84](https://github.com/qualife1291/Auto-Tool-Video/issues/84) queued, no provider calls. |
| **C03** | [Beat E2E #58 / PR #67](https://github.com/qualife1291/Auto-Tool-Video/pull/67) MERGED; [H1 evidence research #49 / PR #65](https://github.com/qualife1291/Auto-Tool-Video/pull/65) **Ready**, current-base Main/Dual PASS, A04 **in progress**, **QA_OWNER=T02**. Research ≠ implemented harness automation. |
| **C04** | [Media 30 FPS #61 / PR #64](https://github.com/qualife1291/Auto-Tool-Video/pull/64), [Fit Audio #44 / PR #47](https://github.com/qualife1291/Auto-Tool-Video/pull/47) and [focus-visible #77 / PR #78](https://github.com/qualife1291/Auto-Tool-Video/pull/78) **MERGED**; [safe Playwright evidence research #79 / PR #85](https://github.com/qualife1291/Auto-Tool-Video/pull/85) Ready/content QA accepted but requires latest-base integrated CI; **QA_OWNER=T01**, no CI security implementation approved. |
| **C05** | [Science review proposed beats #68 / PR #69](https://github.com/qualife1291/Auto-Tool-Video/pull/69) **Ready** at old `489f6669...`; earlier 3 workflows SUCCESS but current-canonical sync/combined test **NOT RUN**, **QA_OWNER=T01**, no creator approval. |
| **T01 + T02** | **QA_OWNER=T01** for #69/#76/#83/#85; **QA_OWNER=T02** for T01-authored [docs PR #46](https://github.com/qualife1291/Auto-Tool-Video/pull/46), BA02 [#73](https://github.com/qualife1291/Auto-Tool-Video/pull/73), C03 [#65](https://github.com/qualife1291/Auto-Tool-Video/pull/65) and other explicitly assigned PRs. T01 [watcher PR #60](https://github.com/qualife1291/Auto-Tool-Video/pull/60) Draft; [#37](https://github.com/qualife1291/Auto-Tool-Video/pull/37) has **8 validated preview MP4s** (four 12/30/45/60s scenarios × two aspect ratios) at historic [run #41103011675](https://github.com/qualife1291/Auto-Tool-Video/actions/runs/41103011675), separate native FullHD scenario skipped, current-base integration still pending. Human creator full media G10 **NOT APPROVED**. |

**Mandatory workflow:** issue/AC and exclusive path claim → Draft → real RED/GREEN or justified coverage scope → author marks Ready → assigned independent QA_OWNER checks exact current SHA, current-base merged tree/CI and evidence → QA PASS/CHANGES REQUESTED → only QA_OWNER may merge (never self-merge) → postmerge CI → human creator audiovisual G10 if applicable. Research-only docs and synthetic eSpeak engineering clips **never** equal implemented tooling, activated personnel or creator release approval. On each actual work session/authorized schedule, everyone proactively follows their own task/CI/feedback, checks official skills and trustworthy sources, and proposes concrete measurable FREE-first quality improvements via BA coordination.

### Archived status notes below (historical evidence only)



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
2. QA_OWNER=T01 or T02 independently reviews diff/ownership/current integrated SHA/checks. FAIL or NOT RUN → leave PR open and return to correct owner; all mandatory PASS → QA_OWNER authorized merge to canonical with expected HEAD SHA, postmerge CI and BA01 comment.
3. **Every hour** T01 must send user actual result PASS/FAIL/BLOCKED/NOT RUN, a verified downloadable preview/FullHD link if available (else OLD BUILD/NO BUILD), 3–6 steps manual test and ask feedback. Log issue/device/aspect/timestamp/expected/actual to [#36](https://github.com/qualife1291/Auto-Tool-Video/issues/36). Creator exact video hash watch/listen before feature DONE and release.
4. All claims need exact commit/run/video SHA; no fabricated media, no unapproved paid provider, no premature social publishing. See [quality gates](../../../docs/qa-evidence-gates.md) and [approved spec](../../../specs/whiteboard-video-tool.md).

**Historical statuses in earlier handovers/PR #23/#21 are not current; preserve provenance, update before integration.**
