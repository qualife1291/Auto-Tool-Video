# Kế hoạch phát triển

## Đợt triển khai tiếp theo — 2D nhiều agent (đang thực hiện, chưa release)

Bảng phối hợp, trạng thái từng hạng mục, file ownership, conditions-of-done và cách nhận việc: [AI Agent Workboard](agent-workboard.md). Nhánh làm việc `feat/second-by-second-motion-voice`; nhánh mặc định `feat/short-video-studio` giữ nguyên baseline.

- **P0 / A01–A03 (WIP-UNTESTED):** storyboard với beats từng giây và mô tả visual/action/camera/text/narration/continuity; áo ướt→khô, lay dưới điểm kẹp, gấp→trải; hiệu ứng caption nảy rất ngắn, phần editor beats. Đây mới là code chưa chạy test, chưa chứng minh chất lượng video.
- **P0 / A04 (TODO):** giọng 0,92× giữ pitch, bảo toàn nội dung audio, tính lại duration theo file thực và làm mới timing/asset provenance; không lấy số 41,9s trước đó làm kết quả render.
- **P0 / A05 (BLOCKED):** dựng video 12 cảnh hai aspect, chạy lại toàn bộ test, QC technical/audio/motion, xem/nghe thủ công; kiểm theo `docs/video-quality-standard.md`; báo pending khi thiếu reviewer.
- **P1 / A06–A08 (RESEARCH/TODO):** thẩm định `@gradio/client`, HF Hub SDK, Space FLUX.1-schnell/SD3.5/Wan2.1/LTX và NIM DeepSeek V4.1 Flash/Magpie TTS/Riva Translate/Llama Guard. Phải tách endpoint được quảng cáo với endpoint hiện hoạt, free trial/ZeroGPU quotas với miễn phí bền vững, code license với weights/outputs/Space terms; chỉ thử online bằng quyền hợp lệ. Không đưa vào runtime chưa kiểm chứng, không auto paid fallback.
- **P2/P3 / A09–A10 (TODO):** TTS UI + alignment/SRT và OAuth upload khi pipeline 2D ổn định.

**Khác biệt thiết yếu:** Project cũ có thể không có second-by-second beats. Kế hoạch từng giây cần có trạng thái `needs_review` khi thiếu/không còn khớp duration, giữ bản cũ để người dùng chủ động chỉnh; tránh đánh lừa rằng lời đã forced-align. Đợt này chưa có camera keyframe compiler cho mọi beat; beat metadata chỉ phục vụ kịch bản và editor trước khi renderer nâng cấp.

**Kiểm chứng:** báo cáo 205 test pass và MP4 38,7s chỉ thuộc baseline trước đợt này; feature branch chưa chạy test/không có MP4 mới. Mọi agent phải ghi lệnh/test/artifact thật trước khi đánh DONE.

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
