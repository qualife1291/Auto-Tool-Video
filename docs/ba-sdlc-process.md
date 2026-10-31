# AI-BA — quy trình SRS, phân rã công việc và điều phối SDLC

**Đã chọn vai trò (2026-10-30):** AI-BA quản lý nghiên cứu, lập kế hoạch, SRS và handoff. AI-Coder sở hữu implementation; AI-Tester độc lập kiểm chứng. **Không đồng nhất** BA tạo issue với việc coder đã nhận tin; không đồng nhất PR-CI xanh với creator/release approved. Tài liệu này bổ sung, không thay thế [AGENT-CODING-STANDARD](../AGENT-CODING-STANDARD.md), [đặc tả đang approved](../specs/whiteboard-video-tool.md), [workboard](agent-workboard.md), [QA gates](qa-evidence-gates.md) và [đánh giá PR](pr-merge-audit-2026-10-30.md).

## 1. Phân quyền và điểm kiểm soát

| Vai trò | Quyết định/đầu ra | Không tự nhận |
|---|---|---|
| **AI-BA / PM** | Nghiên cứu, nhu cầu người dùng, SRS, Epic/Feature/Story, AC testable, dependency, ước lượng SP, file ownership, ưu tiên, điều phối và snapshot tiến độ sau verification | Không tự ghi Test PASS, không merge code khi thiếu QA/creator approval, không giả đã phát webhook |
| **AI-Coder** | Claim GitHub issue/branch, read approved spec & nghiên cứu, code tối thiểu, negative/regression tests, lệnh chạy và artifact hashes, PR/rollback | Không đổi spec, chấm creator, tự merge bypass Tester |
| **AI-Tester** | Requirement→Test ID matrix, unit/integration/E2E/real media/security/perf/QA evidence, bug report với SHA+logs đã redact, independent go/no-go | Không tạo fake screenshot/test success, không bỏ hard gates để pass |
| **Integrator/reviewer** | Xác minh GitHub reviewers, merge conflicts, CI exact SHA, release gating và merge theo quyền được cấp | Không suy API-green là release-ready |
| **Creator/product owner** | Duyệt tính chính xác, nghe/xem video, quyền tài nguyên và quyết định phát hành | Không thay thế bởi semantic/VMAF/CI scores |

## 2. Chuỗi làm việc

`IDEA → G1 RESEARCH → DRAFT SRS → APPROVED SPEC → READY FOR CODER → IN PROGRESS → PR/REVIEW → TESTER PASS → HUMAN ACCEPTANCE (nếu xuất video) → MERGED-VERIFIED → DONE`

- **Research:** ít nhất baseline và 2 phương án, source/version/license/cost/hardware/privacy; đánh giá phụ thuộc A01–A10; chỉ mô tả tương lai trong research backlog khi chưa có spec duyệt.
- **SRS:** dùng chính xác format và yêu cầu approval trong `AGENT-CODING-STANDARD.md`. Không ghi `approved` chỉ vì BA viết xong. User story phải có positive/negative/edge/security/performance/compatibility AC và acceptance evidence owner.
- **Cấp việc:** one GitHub issue per independent write surface, link parent Epic và prerequisite, chỉ định *role lane* + chính xác account nếu xác minh. Nếu account không biết, để GitHub `assignees=[]` và `AWAITING CLAIM`; coder nhận bằng comment rồi BA xác nhận. Không tự gán tài khoản owner hoặc bot giả.
- **Handoff:** tạo issue/PR comment chứa spec SHA, AC/test matrix, owned paths, expected duration/resource scope, blocked preconditions. Webhook chỉ khi có authorized endpoint và integration được cấu hình/kiểm thử; không gửi code/voice/PII/log raw qua webhooks. Không thể tự nhắn trực tiếp sang phiên chat AI khác từ GitHub issue.
- **Review & QA:** Tester kiểm đúng PR head/merge ref, báo BUG với commit, frame/timestamp, expected/actual, exact commands/exit/logs và severity. BA ưu tiên reassign cùng chủ sở hữu; **mọi mandatory fail BLOCK**, not_run ≠ pass. Khi merge, kiểm SHA canonical mới và chạy gate hậu merge.
- **Closure:** BA chỉ đổi state DONE và cộng story points nếu Tester ký acceptance (và creator ký video nếu bắt buộc). PR docs merge không chứng minh chức năng runtime.

## 3. Epic/Feature/Story map

| Epic | Features / tasks | Ưu tiên, trạng thái |
|---|---|---|
| E1: Chất lượng video 2D ổn định | A01 integrity; **A02-FINAL #24** real cloth, **A03-FINAL #25** caption/beat; A04 #6 PR #8; A05 QA #17 PR #18 | **P0**: A01 đã được kiểm; các story còn lại cần exact-head/human evidence |
| E2: Local AI và giọng | A06 #5 / PR #7; A07 #3 / PR #4; A08 integration, A09 phrase alignment/TTS UI | **P1/P2**: research trước khi bật provider |
| E3: Đa engine và chuẩn storyboard | A11–A33 / A49 research-first, Scene IR, animation, scientific scene library, millisecond SFX/light/camera schema | **FUTURE PROPOSED**, thuộc PR #21, chưa được duyệt code |
| E4: FPS, fidelity & performance | A34–A48, profiling/cache/60fps/native sharpness/AI budget/CI optimization | **FUTURE PROPOSED**, không hứa lợi ích khi chưa benchmark |
| E5: Distribution & compliance | A10 OAuth/upload, video rights/consent/safety | **P3** sau audio and creator approval |

**Điểm số ước lượng**: #24 = 5 SP, #25 = 5 SP (provisional, được coder xác nhận sau nghiên cứu). Không suy total project % từ 10 SP này: toàn bộ stories M1–M4 chưa được estimate và có nhiều gate human/AI unrun. Chỉ tính `verified_completed_story_points / approved_total_story_points × 100` sau khi toàn bộ backlog có baseline AC, sizing nhất quán; báo `NOT BASELINED` thay vì số % bịa.

## 4. Hai lane coder được mở ngày 2026-10-30

| Lane | Issue và branch đề xuất | Chỉ ghi IN PROGRESS khi | Không được sửa |
|---|---|---|---|
| AI-Coder 1 | [#24 A02-FINAL](https://github.com/qualife1291/Auto-Tool-Video/issues/24), `agent/A02-final-motion-review` | Comment claim và xác nhận art paths `scripts/science_story.py`, `scripts/blender_review_art.py`, `scripts/verify_science_art.py`; spec/AC research done | `render.py`, frontend, A04 audio, docs/CI/QC người khác |
| AI-Coder 2 | [#25 A03-FINAL](https://github.com/qualife1291/Auto-Tool-Video/issues/25), `agent/A03-caption-beats-final` | Comment claim và xác nhận `render.py` caption region, `apps/web/src/main.tsx`, `domain.ts` beat UX | `science_story.py`, A04 audio, quality/timing/schema, docs/CI/QC người khác |

**Existing ownership:** A04 [#6](https://github.com/qualife1291/Auto-Tool-Video/issues/6) → [PR #8](https://github.com/qualife1291/Auto-Tool-Video/pull/8) (do not duplicate). Integration/Tester [#17](https://github.com/qualife1291/Auto-Tool-Video/issues/17) → [PR #18](https://github.com/qualife1291/Auto-Tool-Video/pull/18) (do not edit its workflow). A05 QA evidence policy #14 already merged; actual voice/creator full acceptance still pending. PR #21 owns workboard/roadmap/AGENTS changes; #23 owns LATEST handover. BA issue assignment does not grant extra file write rights beyond approved specification.

## 5. Definition of Ready (DoR)

- [ ] User story + measurable AC and boundaries explicitly trace to approved `specs/<slug>.md` (or narrow approved sub-spec).
- [ ] Current canonical SHA/PR overlap checked, one owner per write path.
- [ ] Official alternatives/license/current version/hardware/privacy/costs assessed where relevant.
- [ ] Baseline fixture, expected outputs, test IDs and negative/edge cases specified.
- [ ] Dependencies met or marked BLOCKED, resource and rollback strategy declared.
- [ ] Owner (GitHub login when verified; else role lane awaiting claim) explicitly confirmed.

## 6. Definition of Done (DoD)

- [ ] Coder PR with exact commands/exits + test artifacts (no invented run).
- [ ] Independent Tester green on exact PR SHA, no new mandatory skip; security/performance negative tests as relevant.
- [ ] Real dual-aspect Full HD MP4 and audio/visual QC where output changed; creator review on exact SHA256 (status may remain PENDING HUMAN).
- [ ] CI exact canonical merged head, docs/QA report no stale status, previous approved artifacts preserved.
- [ ] BA updates GitHub issue, workboard/handover under exclusive file coordination, link merge SHA and evidence; only then mark DONE.

## 7. Risk register and next checkpoints

| Risk | Impact | BA action |
|---|---|---|
| Current PR #21 and #23 both involve coordination docs | Stale workboard/handover and semantic conflicts | Do not edit their paths in parallel; merge order then status sync |
| PR #8 A04 unmerged; full creator-approved original WAV unavailable | A05 true release gate blocked | Verify PR #8 and source/rights; no fake synthetic fixture approval |
| QA #18 exact-merge simulation uses earlier merge heads | Green PR ≠ green current canonical integration | Tester rerun on updated target SHA and approved source combination |
| #24/#25 have no confirmed AI GitHub identities | Assigned role != dispatched work | Require coder claim/comment; otherwise TO DO |
| Experimental AI/60fps/4K expands cost and QA surface | Delayed baseline and false quality claims | Keep future backlog research-only until A05/A12 and measured budgets |

## 8. Proactive research cadence

When BA is actively asked to review (or configured external scheduler exists), re-check official SDK/standard/OWASP/ISTQB sources by date and compare verified revisions, without downloading untrusted code or silently modifying lockfiles. **There is no continuously running BA process or webhook in this documentation**, and status only changes on a real tool invocation or authorized external automation. Recommend frequency: before every feature spec/PR review plus weekly dedicated backlog triage if an automation is subsequently configured.
