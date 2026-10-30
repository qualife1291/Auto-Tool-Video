---
status: partial
slug: whiteboard-video-tool
updated: 2026-10-30
---

# Handover — whiteboard-video-tool

## Kết quả

Hoàn thành bước nghiên cứu theo yêu cầu mới: đọc 28 repository GitHub, 8 model card và 12 file skill Remotion, chọn phương án free trước theo chất lượng/giấy phép/phần cứng. Có báo cáo so sánh, snapshot commit/revision/hash và skill QA nguyên bản của dự án. Chưa tích hợp/cài/chạy các engine mới từ nghiên cứu, không tuyên bố video AI đã đạt chất lượng. Toàn sản phẩm vẫn partial: M1 đã push ở da54821; code M2 có trong working tree và chưa kiểm xong/chưa commit; M3/M4 còn backlog.

## Đối chiếu đặc tả

- File: specs/whiteboard-video-tool.md, status approved; đã bổ sung hợp đồng nghiên cứu trước khi tạo tài liệu/skill.
- Khớp: tìm nguồn chính thức/skill, kiểm code và weights riêng, free/conditional/paid, phương án theo cấu hình máy; kế hoạch cho sáu hướng thể hiện, hai aspect và các gate chất lượng.
- Lệch đã được duyệt: không. Người dùng tiếp tục quyền code/commit/push đã có; bước hiện tại ưu tiên yêu cầu nghiên cứu mới.
- Lệch chưa duyệt: không. Không thay runtime từ danh sách nguồn và không publish cấu hình cloud.

## Đã làm

- docs/source-review.md: bảng nguồn, hướng Blender/vector/ảnh/video/TTS/caption/upscale, skill Remotion và QA local, chi phí thực tế, kiến trúc adapter, benchmark/gates và thứ tự triển khai.
- docs/source-snapshot.json: 29 repo đã thử/28 truy cập được, 9 model card đã thử/8 truy cập được, 12 file skill; giữ cả lỗi404/401. Chỉ metadata/link/hash, không vendor mã/weights hoặc auto-download.
- .agents/skills/video-quality-review/SKILL.md: quy trình QA nguyên bản cho artifact thật, không cần dependency hoặc dịch vụ tính phí.
- Cập nhật docs/development-plan.md, docs/licenses.md và bộ nhớ. Không đổi app/backend trong lượt nghiên cứu này.
- D-003: ghi nguồn và kiểm chất lượng có bằng chứng trước mở provider, không coi README hoặc mock là live validation.
- Đã chép nguyên handover M1 cũ sang .agent/handover/2026-10-29-whiteboard-video-tool.md trước ghi bản này.

## Chưa làm

- M2: sửa 1 lỗi Ruff/3 mypy và test health đang lệch hợp đồng; thêm test planner/Comfy/job/apply/UI; hoàn thiện config/comfy-sdxl-api.example.json, scripts/live_planner.py, docs/local-ai.md; live Qwen/ảnh có report riêng. Frontend brief/candidate và backend planner/generation/providers mới vẫn là code local chưa commit.
- Runtime Ollama0.40.13 trước outage đã tải/kiểm checksum ở đường dẫn local; pull qwen3:8b khi đó chưa được xác nhận hoàn thành. Kiểm lại process/model/digest trước inference; không suy model có sẵn từ file tải.
- Các engine Manim/Motion Canvas/Three.js/Wan/LTX/LightX2V chưa cài hoặc benchmark trong lượt này. Sáu hướng trong tài liệu chưa phải sáu preset UI; scene.style hiện chỉ whiteboard/motion.
- M3 TTS/forced alignment/loudness và M4 OAuth/live uploads/SRT/180s/cover/packaging chưa hoàn tất.

## Cách chạy

- Lệnh app/check giữ như README.md; không có lệnh cài engine mới trong bước nghiên cứu.
- Đọc docs/source-review.md và source-snapshot.json để chọn thử; runtime không được đọc snapshot để tự tải model.
- Khi kiểm video/provider thật, đọc .agents/skills/video-quality-review/SKILL.md cùng đặc tả.

## Test sẵn có

- Sau workspace kết nối lại, trước thay đổi tài liệu: backend/.venv/bin/python -m pytest backend/tests -q — 31 passed, 1 failed, 1 upstream Starlette/httpx deprecation warning. Fail tại test_source_origin_host_and_security_headers: health ai.image hiện local_provider trong code M2, assertion M1 chờ not_implemented. Đây là trạng thái code dở có từ trước lượt nghiên cứu.
- npm --prefix apps/web run check — TypeScript qua, Vitest 5 passed.
- backend/.venv/bin/ruff check backend scripts — 1 TRY004 providers.py:136 (kiểu lỗi nên dùng TypeError).
- backend/.venv/bin/mypy backend/auto_tool_video — 3 lỗi: config Optional đưa vào Comfy.identity; callback generate trả dict thay None; kiểu result dict suy luận thiếu bool. Không tắt rule/assertion và chưa ghi pass cho M2.
- Sau tài liệu: không đổi code/dependency nên không chạy lặp lại regression. Bằng chứng 41 test M1 lịch sử chỉ áp commit da54821; xem archive, không dùng cho working tree M2 hiện tại.

## Test đã chạy

- Nguồn: GitHub/Hugging Face API và tài liệu được đọc ở commit/revision; hash đối chiếu 85 tài liệu đã tải ngoài Git khớp snapshot. Xác minh 28 commit repo, 8 model revision và 12 skill records có định danh hợp lệ.
- Tài liệu: kiểm một H1/file ở4 file tài liệu/skill mới hoặc cập nhật và8 link tương đối resolve; JSON parse/counts/hash hợp lệ.
- Format: apps/web/node_modules/.bin/prettier --check docs/source-review.md docs/source-snapshot.json .agents/skills/video-quality-review/SKILL.md docs/development-plan.md docs/licenses.md — qua sau format.
- Whitespace: git diff --check và git diff --cached --check — qua trước commit.
- Commit chỉ tài liệu/spec/memory/skill; app/backend/lockfile M2 không được stage hoặc push trong commit nghiên cứu.

## Test không chạy

- Không chạy video/model mới, không chấm điểm chất lượng hình/giọng từ README. Số VRAM/tốc độ trong báo cáo ghi upstream, chưa là số đo local.
- Không chạy lại E2E/render vì bước này không đổi runtime; các test M2 mới còn thiếu. Không lấy mock hoặc test M1 thay live AI.
- Chưa live upload, chưa có app credentials/tài khoản được cấp quyền cho bước M4; không kết nối hoặc tự đăng.
- Chưa kiểm native Windows/macOS hay mọi thiết bị, không hứa mọi nền tảng.

## Quyết định đã ghi vào nhớ dài hạn

D-003 bổ sung bên cạnh D-001/D-002; PROJECT cập nhật trạng thái thực M1/M2/M3/M4.

## Rủi ro và nợ

- Code M2 chưa commit vẫn cần giữ nguyên và hoàn thiện; không reset/checkout đè để làm tree sạch. Chỉ tài liệu được commit trong lượt này.
- Model repository có thể đổi; snapshot nghiên cứu không phải lockfile triển khai. Pin release/weights/components sau benchmark. Skill Remotion chưa tìm thấy license riêng trong cây đã kiểm nên chỉ link/tham khảo, không vendor/cài.
- Remotion/LTX có điều kiện phát sinh chi phí; F5 pretrained NC, Piper voice riêng, custom node/LoRA riêng. Free không loại chi phí máy/điện/thời gian.
- Chất lượng cảm nhận/nội dung/độ tuổi cần creator duyệt, không chỉ độ phân giải hay điểm tự động. Không bảo đảm viral hoặc Kids inclusion.
- Không đọc secret, không đưa dữ liệu/video riêng vào nguồn nghiên cứu hoặc Git; không có external install/paid API ở bước này.

## File đã đụng

specs/whiteboard-video-tool.md; docs/source-review.md; docs/source-snapshot.json; docs/development-plan.md; docs/licenses.md; .agents/skills/video-quality-review/SKILL.md; .agent/handover/LATEST.md và archive; .agent/memory/long-term/DECISIONS.md, PROJECT.md; .agent/memory/short-term/SESSION.md. Các file app/backend/lockfile M2 được bảo toàn ngoài index.

## Agent sau đọc gì

1. AGENTS.md, AGENT-CODING-STANDARD.md và specs/whiteboard-video-tool.md.
2. .agent/memory/long-term/PROJECT.md, ARCHITECTURE.md, DECISIONS.md, CONVENTIONS.md.
3. Handover này, archive M1 và TASKS.md/SESSION.md; không xin lại quyền code/push.
4. docs/source-review.md, source-snapshot.json, development-plan.md; skill QA local khi tới kiểm render/model thật.
5. git status/diff để tiếp tục code M2 đang dở; sửa lỗi/test trước commit code. Không áp lại/publish môi trường cloud.
