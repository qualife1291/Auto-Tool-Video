# Chỉ mục tài liệu — Whiteboard Studio

**Vai trò:** trang điều hướng, không phải bảng trạng thái hay chứng cứ release. Snapshot 2026-10-30. Khi hai trang mâu thuẫn, chọn nguồn đúng chức năng, rồi kiểm tra SHA/PR mới nhất.

| Nội dung | Nguồn chính | Quy tắc |
|---|---|---|
| Chạy tool / cấu hình local | [README](../README.md), [Local AI](local-ai.md) | Không suy từ README rằng provider/model đã test live |
| Quyền hạn, ranh giới sản phẩm | [SRS/Spec đã duyệt](../specs/whiteboard-video-tool.md), [Coding Standard](../AGENT-CODING-STANDARD.md) | User story mới phải có phạm vi và quyền riêng |
| **AI-BA điều phối SDLC** | [BA process + stories](ba-sdlc-process.md), [BA skill](../.agents/skills/ba-project-management/SKILL.md) | BA viết SRS, AC, ưu tiên, phân phối; Coder code; Tester kiểm chứng |
| Trạng thái, claim, phạm vi file từng agent | [Agent Workboard](agent-workboard.md) | Nguồn tiến độ; chưa có owner thật thì ghi UNASSIGNED |
| Nhiệm vụ ngắn hạn | [TASKS](../.agent/memory/short-term/TASKS.md) | Chỉ mục đang làm, không dùng làm nhật ký lịch sử |
| Bàn giao hiện hành | [LATEST](../.agent/handover/LATEST.md) | PR #23 còn sửa LATEST; không ghi đè trước khi giải quyết |
| Lộ trình M1–M4 | [Development plan](development-plan.md) | Roadmap hiện hành, không tự coi PR nghiên cứu #21 là đã merge |
| **PR đã/chưa merge** | [PR merge audit 2026-10-30](pr-merge-audit-2026-10-30.md) | Snapshot có thời gian; kiểm tra GitHub trực tiếp trước quyết định |
| **Log/file cleanup & chứng cứ** | [Maintenance policy](repository-maintenance.md) | Không xóa bằng chứng không có retention owner |
| Quy trình QC/acceptance | [Video quality standard](video-quality-standard.md), [A05 evidence gates](qa-evidence-gates.md) | Technical PASS ≠ Creator APPROVED ≠ release |
| Bằng chứng lịch sử | [QA review](qa-review.md), [Render benchmark](render-benchmark.md), [Storyboard review](storyboard-review.md) | Giữ commit/ngày/hashes; không cộng thành kết quả mới |
| Source/license audit | [Source review](source-review.md), [Snapshot](source-snapshot.json), [Licenses](licenses.md) | Research/reuse phải xác minh phiên bản/giấy phép lại |
| Cảm hứng / video tham chiếu | [Reference video](reference-video.md) | Không phải số đo video tool hiện tại |

## Những nghiên cứu/PR chưa thuộc canonical tại snapshot

- [PR #21](https://github.com/qualife1291/Auto-Tool-Video/pull/21) (Draft): bổ sung nghiên cứu đa dạng video, FPS/độ nét, tối ưu chi phí, quy trình research-first và skill. Chỉ sau merge mới được link tới các file đó trên branch canonical.
- [PR #23](https://github.com/qualife1291/Auto-Tool-Video/pull/23): thay đổi `.agent/handover/LATEST.md` và lịch sử bàn giao; cleanup không sửa đè.
- [PR #18](https://github.com/qualife1291/Auto-Tool-Video/pull/18): workflow QA tích hợp đa PR; CI ở PR head không thay cho kết quả sau merge hoặc review con người.

## Phân lớp tài liệu để không sinh trùng

**Normative:** SRS/spec, BA process, AGENTS, coding standard, QC gates. **Operational index:** workboard, latest handover, TASKS. **Historical evidence:** handovers có ngày, source snapshots, QA reports, benchmark. **Research proposal:** tài liệu lựa chọn công nghệ/kiến trúc chưa được duyệt triển khai. **Generated:** video, waveform, CI console/trace, HTML coverage và profiler dumps — phải giữ ở nơi evidence/artifact, không thêm bừa vào Git.

Cấm dùng từ `DONE` hay 100% cho story nếu chỉ có PR merge nhưng thiếu mandatory verification. Cấm xóa handover/báo cáo cũ với lý do "trùng". Ghi rõ version, nguồn, ngày và link tới nguồn sự thật thay vì copy lại các bảng tiến độ.

## Sau mỗi PR merge

BA xác nhận GitHub `merged=true`, SHA canonical mới và phạm vi thay đổi; Tester kiểm lại CI+QA ở đúng SHA và ký acceptance; BA cập nhật story/roadmap/risks/next owners sau khi có kết quả. Nếu thiếu quyền webhook/notification, dùng GitHub issue/PR assignment/comment như cơ chế bàn giao minh bạch; không tự nói đã gửi webhook.
