# Quyết định

## D-001 — Video dọc và chất lượng theo nhóm tuổi

- Ngày: 2026-10-29
- Trạng thái: accepted
- Lý do: người dùng yêu cầu Shorts/Kids/TikTok/Facebook và bắt đầu dev.
- Hệ quả: 9:16 trước, profile riêng; không bảo đảm vào Kids hoặc viral; free local trước.
- Đặc tả: specs/whiteboard-video-tool.md

## D-002 — Hai aspect và compositor cho reference mới

- Ngày: 2026-10-29
- Trạng thái: accepted
- Lý do: người dùng bổ sung Drive reference, yêu cầu16:9/9:16 và liên kết upload.
- Hệ quả: render1080p hai layout, nhận clipMP4 và ảnhmotion; Blender template cho đồ họa khoa học, không dùng diffusion viết số liệu. Hub upload manual ởM1, OAuth/live upload cònM4; không gọi link là connected.
- Đặc tả: specs/whiteboard-video-tool.md

## D-003 — Nguồn có kiểm chứng và QA trước khi mở provider

- Ngày: 2026-10-30
- Trạng thái: accepted
- Lý do: người dùng yêu cầu tìm source/skill để tăng chất lượng, tối ưu và đa dạng, ưu tiên giải pháp free.
- Hệ quả: docs/source-review.md và source-snapshot.json phân biệt code/weights/license, benchmark upstream/local và provider đã chạy/ứng viên. Giữ FFmpeg/Blender, hoàn thiện Ollama/Comfy trước; engine khác chỉ thử có mẫu và gate, không auto cài/paid fallback. Skill QA nguyên bản tại .agents/skills/video-quality-review/SKILL.md; skill Remotion chỉ tham khảo, chưa vendor/cài. Không coi nghiên cứu là M2–M4 hoàn tất.
- Đặc tả: specs/whiteboard-video-tool.md
