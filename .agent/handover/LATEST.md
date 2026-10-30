---
status: partial
slug: whiteboard-video-tool
updated: 2026-10-30
---

# Handover — whiteboard-video-tool

## Kết quả

M2 adapter, kiểm thử tổng quát, ba kiểu phụ đề và thư viện ý tưởng khoa học đã được code. Mẫu review gốc được nâng đồ họa Blender/Pillow, đã xuất và kiểm lại cả hai aspect. Toàn sản phẩm còn partial: chưa xác nhận planner/ảnh model live, TTS trong UI hoặc OAuth upload. Đặc tả giữ approved; không nhận đã có người nghe/xem duyệt chất lượng cảm nhận.

## Đối chiếu đặc tả

- File: specs/whiteboard-video-tool.md. Spec QA c37a50d và phụ đề/Tongjiang 8feefcc đã push trước commit code.
- Khớp: API/form/provider/review/apply, test hợp đồng riêng với live, caption theo cảnh, nguồn và license, mẫu thật hai aspect.
- Lệch đã được duyệt: không. CLI TTS loại UI Gradio theo spec, ghi rõ metadata SDK còn required.
- Lệch chưa duyệt: không. Không áp lại/publish cloud config, trả phí API hoặc upload công khai.

## Đã làm

- CreativeBrief và planner brief/preserve; server-owned chunk IDs, strict coverage/source refs, schema và bounded retry. Ollama loopback có model identity; Comfy graph quản trị tin cậy, không nhận code/custom nodes từ model/browser.
- Local transport chặn non-loopback/credentials/path/query/redirect; bound NDJSON/response/poll/time; kiểm deadline từng network chunk, chặn trickle không cần chờ buffer đầy. Candidate giữ riêng, hash bytes chuẩn hóa và provenance nguồn; revision/idempotency/cancel/restart/cross-project và explicit confirm/apply.
- UI CreativePanel/ImageGenerationPanel, capabilities đúng tình trạng, graph SDXL mẫu chuẩn và live_planner.py; docs/local-ai.md ghi cấu hình và giới hạn.
- Caption card/contrast/accent và literal emphasis, từ tiếng Việt/2 dòng cân bằng, canh giữa theo glyph thực, project cũ default card; React preview/save và Pillow renderer native/preview hai aspect. Không fake karaoke.
- Contour silhouette-first, AAC headroom trước encode để final true peak đạt. Art gốc thêm nếp vải/đường may/ô phóng đại; Blender CPU áo ướt/khô/cốc nước1600×1400, không physics simulation hoặc asset thương mại.
- Tongjiang Lab kiểm tại 4d63ce0a72d987c850ec6d919e570bdb752c87a6: 54 bài, THPT/tiếng Trung, CC BY-NC4.0 cho bài/cover/catalog; three.js MIT riêng. Chỉ link và4brief tự viết, không vendor/chạy HTML ngoài. Có xác nhận thay brief đã có nội dung, giữ script/scenes/assets; nguồn đi vào metadata đúng export snapshot.
- CLI review tách biệt: VieNeu3.8.3 ONNX CPU FP32/preset Hải Đăng thật, model/codec13file pin/hash; ASR turbo local. Không clone giọng, dịch vụ trả phí hoặc model3D/videoAI.
- Baseline MP4/report/story/TTS evidence và inputs giữ trong .data/review/baseline (ignored). Handover nghiên cứu và baseline đã archive trước ghi bản này.

## Chưa làm

- Qwen live và Comfy ảnh live chưa xác nhận; thiếu dịch vụ/model/GPU ảnh. Adapter/mock không chứng minh chất lượng model.
- Reference/character control, batch được duyệt và template3D editor còn M2. Không có engine quay HTML Tongjiang sang video; muốn dùng lại thương mại cần quyền riêng.
- M3 UI TTS/voice picker/jobs/cache, test20câu/nghe thật, forced alignment/SRT và naturalness10ảnh. Review CLI không là UI TTS hoàn chỉnh.
- M4 OAuth/token và upload private/draft YouTube/TikTok/Facebook, cover/180s/packaging/device QA chưa làm. Hub hiện là link thủ công.

## Cách chạy

- README.md cho app và kiểm; docs/local-ai.md cho Ollama/Comfy.
- docs/qa-review.md cho tạo art, TTS venv riêng và verify. Không auto tải weights khi mở app.
- Video/report thực ở .data/review ngoài Git; có snapshot/hash. Không Git-commit MP4/WAV/weights/cache.

## Test sẵn có

- Trước QA:31pytest pass/1health assertion M1 cũ fail; frontend5Vitest/typecheck pass; Ruff1/mypy3 lỗi đã ghi từ phiên nghiên cứu.
- Baseline QA:91pytest+5Vitest+7Playwright=103pass.
- Sau nâng cấp:114pytest+8Vitest+9Playwright=131pass, không skip. Một upstream Starlette/httpx deprecation warning, không disable.

## Test đã chạy

- Pytest114pass/13,58s: API/schema/media/path/revision/audio-stale/jobs/full render hai aspect; provider invalid/oversize/redirect/model identity/source coverage/confirm/cancel/restart; caption literal Unicode/cross-line/default/persistence/style geometry ở4canvas; metadata lấy nguồn từ snapshot dù draft đổi.
- TypeScript và8Vitest pass; Vite build và Prettier qua. Ruff check/format và mypy12source qua, không hạ assertion/typecheck.
- Playwright9pass/29s: desktop1366/mobile390, axeWCAG2A/AA, nhập/render/download/reload, plain text/keyboard;3AI cases mock contract; caption style/emphasis và thư viện ý tưởng hủy/xác nhận/giữ storyboard/nguồn/reload.
- Một số E2E locator textarea có nội dung từng fail; sửa sang accessible role, giữ assertion; lượt cuối9pass. Helper backend cũ không gửi brief khiến test nguồn mới fail; sửa helper gửi field có thật, test old-client save riêng vẫn còn và qua.
- npm runtime audit, backend pip-audit và venv TTS audit:0known advisory được báo; package app nội bộ không có trênPyPI không được database audit.
- Baseline video32,021333s, full decode, A/V lệch<100ms, -15,72LUFS/-1,37dBTP và ASR8/8cue khớp chuẩn hóa. Bản nâng cùng thông số audio/decode và ASR8/8cue qua, AAC packet hash hai aspect giống nhau. Dọc1.632.420byte/35,044s, ngang1.325.349byte/32,778s (gồm contact sheets); hash cuối trong docs/qa-review.md/verification.json.
- Xem layout cả8cảnh/hai aspect, art3D áo native; phát hiện/sửa cốc bị mặt vành che nước trước render cuối. Đã xem24frame đầu/giữa/cuối mỗi aspect, native hook/accent/cốc/ending; playback và nghe có người duyệt còn chờ.

## Test không chạy

- Model Qwen/Comfy/Wan/LTX/FLUX/SDXL live và benchmark GPU: chưa có model/service phù hợp; không thay bằng mock.
- Human listening20câu, playback/người dùng duyệt và đầy đủ ma trận tuổi/style/thiết bị: chưa có bằng chứng. ASR hỗ trợ, không thay người nghe.
- OAuth/social live upload/Kids inclusion: chưa có credentials/quyền app và chưa M4. Native Windows/macOS/điện thoại thật chưa kiểm.

## Quyết định đã ghi vào nhớ dài hạn

D-004 (artifact thật/CLI/licensing) và D-005 (caption/Tongjiang). PROJECT/ARCHITECTURE cập nhật trạng thái M2 adapters, M3 CLI và source restrictions.

## Rủi ro và nợ

- SDK upstream required Gradio; CLI bỏ UI để tránh Pillow12.3 có39advisory. Lock48package/audit0known, inference thật sau tách chạy; uv pip check CLI sẽ báo thiếuGradio. Chưa là SDK Web UI đầy đủ; phải sửa packaging trước installer M3.
- Comfy workflow/checkpoint name có provenance, hash weights cần quản trị pin riêng. Live generation chưa được thử; không hứa native AI video/chất lượng chung.
- Cá nhân không miễn mọi NC license. Mẫu dùng art gốc/NotoOFL/VieNeu+codec+sea-g2pApache2/ASRMIT, không asset Tongjiang/Remotion/LTX/F5NC. Binary FFmpeg/Blender không phân phối trong repo.
- Chữ/geometry/ASR/decode qua không chứng minh nội dung phù hợp mọi tuổi, tự viral hoặc được vào Kids. Creator còn phải nghe/xem và chọn audience/quyền trước đăng.

## File đã đụng

Backend modules/tests/lock; frontend src/e2e; config/comfy-sdxl-api.example.json; scripts/create_review_video.py,blender_review_art.py,live_planner.py,review-tts; README,.env.example,.gitignore; docs/local-ai,qa-review,source-review,source-snapshot,licenses,development-plan; spec/memory/handover. Media/model chỉ ở runtime ignored.

## Agent sau đọc gì

1. AGENTS.md và specs/whiteboard-video-tool.md.
2. Handover này và docs/qa-review.md,local-ai.md,source-review.md; artifacts .data/review nếu workspace còn.
3. PROJECT/ARCHITECTURE/DECISIONS/CONVENTIONS và TASKS; tiếp M2 live/M3/M4 theo quyền code/push đã có.
4. Skill video-quality-review khi đổi render/provider; không áp/publish cấu hình cloud cũ.
