# Việc đang code

**Branch chung:** `feat/short-video-studio`. **Bảng điều phối duy nhất:** [docs/agent-workboard.md](../../../docs/agent-workboard.md). Nhận một task A01–A10 qua issue/PR, tạo nhánh `agent/Axx-...` từ branch chung và gửi PR trở lại branch chung. Không gán agent nếu chưa thực sự nhận việc.

## Ưu tiên và trạng thái (2026-10-30)

- **P0 / A01 (DONE-VERIFIED):** [PR #2](https://github.com/qualife1291/Auto-Tool-Video/pull/2) đã merge; chuẩn giây liên tiếp, bảo toàn khi đổi thời lượng, lưu qua client cũ, preserve tiếng Việt và revision. [CI pass](https://github.com/qualife1291/Auto-Tool-Video/actions/runs/41052656718): 212 pytest pass/1 skip, 10 Vitest và 13 Playwright pass; lint/mypy/build/format pass.
- **P0 / A02 (WIP-UNTESTED):** áo ướt→khô/lay/gấp→trải; cần test continuity/crop/mask ở cả 9:16 và 16:9.
- **P0 / A03 (WIP-UNTESTED):** caption bounce và beat editor; cần typecheck/E2E/readability/save-reload.
- **P0 / A04 (TODO):** giọng 0,92× giữ cao độ và tính lại timeline bằng WAV thật; chưa có MP4 41,9s được xác minh.
- **P0 / A05 (BLOCKED A02–A04):** kiểm thử tổng hợp, xuất 2 MP4 mới, đo QC và thu đánh giá người xem. Chỉ báo cáo baseline 205 tests/38,7s của phiên trước, **không áp dụng kết quả đó cho code đã merge**.
- **P1 / A06–A07 (TODO):** xác minh Hugging Face/Gradio Spaces và NVIDIA NIM, quyền truy cập, phí, license, tiếng Việt, độ trễ và hạn mức thực.
- **P1 / A08 (TODO, phụ thuộc A06–A07):** online AI opt-in có fallback local độc lập.
- **P2 / A09 (TODO):** TTS UI, phrase alignment/SRT. **P3 / A10 (TODO):** OAuth/social upload.

## Điều kiện đánh dấu hoàn thành

Có commit/PR, test thực tế, bằng chứng chất lượng/artifact và ghi rõ nội dung chưa được xem/nghe hoặc kiểm model live. Không tự xem trạng thái merge là QA pass. Không thêm dependency online trả phí, upload mạng xã hội hoặc ghi secret/weights vào Git.

## Tài liệu liên quan

- [Handover](../../handover/LATEST.md) — bản bàn giao kỹ thuật gần nhất.
- [Lộ trình](../../../docs/development-plan.md) — M1–M4.
- [Quy chuẩn video](../../../docs/video-quality-standard.md) — test/QC và manual review.
- [Đặc tả](../../../specs/whiteboard-video-tool.md) — nguồn xác định phạm vi đã duyệt.
