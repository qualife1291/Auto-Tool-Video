# Kế hoạch phát triển

## Đã triển khai M1

- Studio tiếng Việt local, năm hồ sơ người xem, bốn bước, editor responsive desktop/mobile.
- Project SQLite với revision; source script giữ riêng, chia đoạn thủ công ghi rõ không phảiAI.
- Nhập PNG/JPEG/WAV/MP3/MP4 H.264, giới hạn nội dung, MIME thực, kích thước, duration; asset scene riêng.
- Whiteboard reveal theo contour, bàn tay minh họa gốc, hiện màu; mode motion dùng ảnh zoom nhẹ hoặc clip thực, tiếng gốc clip tắt.
- Chọn 1080×1920 hoặc1920×1080, preview riêng, chữ Noto ở độ phân giải đích, CRF18; không render nhỏ rồi upscale cả video.
- Worker một tác vụ nặng, snapshot/idempotency/cancel/interrupted; FFprobe/full decode trước success; upload metadata đúng snapshot xuất.
- Download MP4 và publish JSON; mở YouTube Studio/TikTok Studio/Facebook Reels. Đây là hub thủ công, không OAuth/direct upload.
- Script Blender nguyên bản dựng particle illustration; đã render clip smoke thật, có thể nhập lại app. Chưa có template editor hoặc tự dựng nội dung từ narration.

## M2 — Tạo nội dung và nguồn ảnh/video

Đã có form brief, hai mode planner (viết mới/giữ lời), adapter Ollama và ComfyUI loopback, proposal/candidate jobs có revision/idempotency/provenance, review/apply rõ ràng và test hợp đồng. Graph mẫu SDXL dùng node chuẩn; chưa xác nhận Qwen live hoặc sinh ảnh live vì thiếu dịch vụ/model/GPU. [Hướng dẫn AI local](local-ai.md) ghi khả năng hiện có và cách chạy smoke. Các mục dưới đây gồm cả phần đã code và gate còn thiếu; chưa đánh M2 hoàn tất.

Đã thêm thư viện4ý tưởng khoa học nguyên bản có nguồn Tongjiang Lab. Lesson/covers/catalog gốc CC BY-NC4.0, không vendor/chạy mã ngoài; giữ nguồn qua export snapshot. [Báo cáo nguồn](source-review.md) phân biệt dùng lại phi thương mại và đồ họa tự dựng.

- Kết quả [rà nguồn GitHub/skill](source-review.md) và [snapshot nguồn](source-snapshot.json) phân biệt code/weights/license, chi phí và số đo upstream/local. Có [skill QA nguyên bản](../.agents/skills/video-quality-review/SKILL.md) cho các phiên kiểm render/provider; chưa thêm các engine nghiên cứu vào runtime.
- Form brief đầy đủ; Ollama/Qwen schema và source spans; duyệt thay đổi trước áp dụng.
- Adapter ComfyUI local cho FLUX.2 Klein4B; benchmark SDXL dự phòng và license từng model/LoRA.
- Style/character bible, reference/seed, một ảnh thử trước batch; cancel/retry/provenance.
- Template Blender/Three.js có các đối tượng giáo dục và thông số đã kiểm; không dùng diffusion viết số liệu.
- Đánh giá Wan2.2 TI2V5B trước khi có GPU phù hợp; LTX tùy checkpoint/Community License và benchmark thật. Không gọi LTX luôn free hoặc suy Apache từ code đời cũ. LightX2V chỉ thử tối ưu sau baseline đạt chất lượng; chưa tải/chạy model video, chưa có điểm chất lượng.

## M3 — Giọng và chất lượng

Đợt sửa theo feedback nhịp/hình: full_frame/cover/focal và legacy board, affine float, pen-up travel, visual-only dissolve; PCM timeline với một lần AAC/loudnorm. UI khớp thời lượng theo audio thực và QC đo/cảnh báo silence. Kịch bản mẫu12cảnh kèm clip minh họa native hai aspect, không chỉ8ảnh giữ4s; xem [storyboard](storyboard-review.md) và [QA](qa-review.md). Motion nhẹ vẫn có warning và cần creator playback; không tăng chuyển động vô nghĩa để qua proxy.

Đã triển khai QC sau render: metadata/PTS/CFR/decode/LUFS/truepeak/silence, lightweight flash/freeze proxies theo scene và motion intent; hard gate kỹ thuật, phiếu creator1–5/hash/review revision, critical override, timestamp/seek và JSON/CSV. Nguồn VBench/AIGCBench/CVPRW2026/EU được đối chiếu trong [quy trình QA](video-quality-standard.md); chưa chạy benchmark learned metrics hoặc C2PA. Sửa normalize audio ngắn và silent branch; human listening/physics/semantic quality vẫn cần creator.

Đã sửa word-wrap/cân2dòng, contour silhouette-first và AAC headroom; thêm3kiểu caption card/contrast/accent với literal emphasis, lưu/preview/render hai aspect. Mẫu review thật dùng tranh procedural Blender/Pillow có chi tiết và VieNeu FP32 local qua CLI riêng, ASR/loudness/full decode có báo cáo ở [QA](qa-review.md). Đây chưa là TTS trong UI, forced alignment hoặc quality gate có người nghe duyệt; SDK CLI còn giới hạn packaging được ghi trong QA.

- VieNeu CPU FP32, voice list/digest/license thật; nghe20 câu. Không fake audio hoặc auto đổi sang dịch vụ tính phí.
- Caption alignment theo phrase/cue thật, SRT; renderer cải thiện naturalness từ10 ảnh và review người dùng.
- Scene composition nâng cao, vùng safe zone riêng theo platform/version; kiểm ảnh/clip thiếu chi tiết và âm lượng thật.

## M4 — Liên kết tài khoản và phát hành

- OAuth state/PKCE, mã hóa token local, scope tối thiểu, refresh/revoke, không token ở frontend/log.
- YouTube resumable upload private mặc định; TikTok inbox draft; Facebook Page Reels với quyền được cấp. Chỉ publish sau xác nhận cuối trong UI, không tự đăng trong phiên agent.
- Test mocked HTTP/retry/expiry/quota/idempotency và test live bằng tài khoản được người dùng cấp quyền. Không gọi mocked test là đã upload thật.
- Hiện chưa có các client credentials/quyền ứng dụng; người dùng cấu hình an toàn khi đến mốc này, không gửi secret trong chat.
- Video dài180s, cover/SRT pack, device QA và packaging một OS; quyền dùng âm nhạc/audience/phân phối kiểm trước phát hành.

## Điều kiện tiếp tục

Đọc đặc tả và handover, tiếp tục backlog; không yêu cầu lại quyền code/push đã cấp. Không đổi spec thànhimplemented cho tới đủ mốc và bằng chứng. Không áp lại hoặc publish cấu hình cloud; các lượt xuất bản môi trường trước là hành động của người dùng, khác với Git push.
