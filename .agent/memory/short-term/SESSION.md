# Bối cảnh phiên

2026-10-30: workspace kết nối lại, code M2 còn nguyên và chưa commit. Người dùng bổ sung tìm source/skill nâng chất lượng/tối ưu/đa dạng. Đã đọc 28 repo, 8 model card, 12 skill Remotion; docs/source-review.md và source-snapshot.json, skill QA local nguyên bản; chưa cài/chạy model/engine mới từ nghiên cứu. Chỉ commit/push tài liệu và spec; code M2 giữ ở working tree.

Trạng thái hiện tại trước sửa code tiếp: 31 pytest pass/1 fail health image (`local_provider` so với assertion cũ `not_implemented`); ruff 1 TRY004 providers.py; 3 mypy (config optional/callback return/result dict); frontend typecheck + 5 Vitest qua. Không claim toàn bộ test pass. M1 historical 41 test qua ở commit da54821, xem archive handover.

M2 cần sửa lỗi trên, hoàn thiện config/comfy-sdxl-api.example.json, scripts/live_planner.py, docs/local-ai.md và test provider/AI job/UI. Cần live planner/ảnh có bằng chứng riêng. Ollama 0.40.13 tar đã checksum và runtime local trước outage; pull qwen3:8b chưa được xác nhận hoàn thành, kiểm lại process/model/digest trước chạy. Không auto tải weights từ snapshot nguồn.

Giữ M3/M4 backlog, quyền push nhánh feat/short-video-studio đã có; không publish cloud config. Bàn giao và các nguồn mới nằm trong LATEST.md.
