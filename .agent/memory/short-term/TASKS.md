# Việc đang code — Bảng điều phối nhiều AI agent

Cập nhật: 2026-10-30. **Nguồn chi tiết:** [docs/agent-workboard.md](../../../docs/agent-workboard.md). Branch đang phát triển: `feat/second-by-second-motion-voice`; branch mặc định `feat/short-video-studio` vẫn giữ baseline `a7d000f6`.

## Trạng thái thực (đừng đánh đồng với đã nghiệm thu)

- Baseline M1/QA theo handover cũ: **205 tests passed**; video 12 cảnh / ~38,7s ở 9:16 và 16:9 technical pass. Kết quả là của bản cũ, không phải feature branch.
- **WIP chưa chạy kiểm thử:** `domain.py` có `SecondBeat`; `planning.py` yêu cầu chi tiết từng giây (có fallback outline cho provider cũ cần rà lại); `science_story.py` thêm wet-dry blend/sway/unfold và beat script; `render.py` thêm caption bounce; `main.tsx`/web domain có editor beats.
- **Chưa có trên branch:** kéo giọng về **0,92× giữ cao độ**, import/regenerate audio và 47 beat thực từ local session trước; **chưa xuất** video 41,9s mới; chưa human playback/QC; thư viện HF/NIM chỉ là ứng viên.
- **Không thể lấy source chưa push** từ môi trường agent cũ qua GitHub. Không đoán là đã phục hồi.

## Các công việc có thể song song

| Task | Priority | Trạng thái | Phần trách nhiệm |
|---|---|---|---|
| A01 | P0 | WIP-UNTESTED | Backend schema/planner từng giây, retrocompat, duration-change, tests |
| A02 | P0 | WIP-UNTESTED | 2D áo ướt→khô, áo lay quanh điểm kẹp, gấp→trải, art QA |
| A03 | P0 | WIP-UNTESTED | Caption bounce, per-second UI, save/reload/E2E |
| A04 | P0 | TODO | 0,92× speech/pitch-safe, trim/re-timing, provenance |
| A05 | P0 | BLOCKED (A01–A04) | Hai MP4 render thật, full tests, QC/manual review |
| A06 | P1 | TODO | @gradio/client + HF Hub + FLUX/SD/Wan/LTX Space research |
| A07 | P1 | TODO | NVIDIA DeepSeek/Magpie/Riva/Llama Guard NIM verification |
| A08 | P1 | TODO (A06/A07) | Provider optional opt-in + local fallback |
| A09 | P2 | TODO | TTS UI/alignment/SRT |
| A10 | P3 | TODO | OAuth upload YouTube/TikTok/Facebook |

## Bàn giao/nhận việc

- Mỗi agent **nhận một ID**, branch riêng `agent/Axx-...` xuất phát từ `feat/second-by-second-motion-voice`; mở PR về branch này. Không cùng sửa một file; chi tiết file ownership trong workboard.
- Task chuyển sang DONE chỉ khi có mã commit, test được chạy thật và bằng chứng/artifacts hoặc lý do không chạy. Không coi mock model là live inference; không dùng benchmark pixel để khẳng định chất lượng cảm nhận.
- Không sửa `specs/whiteboard-video-tool.md` để hợp thức hóa code chưa được duyệt. Đọc `AGENTS.md` / `.agent/handover/LATEST.md` / `docs/agent-workboard.md` trước khi code.
- Giữ ưu tiên **2D + miễn phí + web UI local**. Không tự bật API trả phí, cloud, upload mạng xã hội hoặc push model/media/secrets.

## Điểm dừng tiếp theo

1. A01–A03 bổ sung tests và chạy lint/typecheck, rà schemas + editor.
2. A04 tạo audio ở tempo 0,92× từ narration đã được phép dùng; chốt duration thực (không mặc định 41,9s).
3. A05 render hai aspect, QA kỹ thuật và bàn giao cho creator nghe/xem.
4. A06/A07 nghiên cứu docs/quota/licensing độc lập, không merge runtime trước gate.
