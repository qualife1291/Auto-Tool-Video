# Bằng chứng kiểm render

## Phạm vi đã chạy

Kiểm ngày2026-10-29 trên Linux x86_64, máy báo khoảng5 CPU/33,3GiB RAM; không xác minh GPU. FFmpeg7.1.5 có libx264/AAC, Blender4.3.2. Đây là kết quả hiện tại, không phải SLA cho máy khác hoặc model AI.

| Kiểm | Kết quả thực |
|---|---|
| Backend pytest |32 ca qua,0 fail,0 skip trong lần chạy cuối;1 cảnh báo upstream TestClient/httpx deprecated, không tắt assertion |
| Frontend Vitest |5 ca qua: readiness, silent, missing image, stale audio, duration và source scaling |
| E2E Chromium |4 ca qua: desktop/mobile import→render→download→restore; XSS/focus; axe WCAG2A/AA labels/contrast hai màn |
| Full1080p smoke |3 cảnh ở1080×1920 và1920×1080,30fps,H264,yuv420p,AAC; mỗi file3,021333s; full decode thành công |
| Clip narration |ImportMP4 thực rồi ghép audio fixture; decoded PCM có năng lượng, không lấy metadata làm bằng chứng có tiếng |
| Cancellation |Hủy encoder đang chạy; tmp riêng được dọn, file xuất cũ fixture giữ nguyên |
| Restart/idempotency |Running→interrupted; hai request đồng thời cùng job; snapshot không đổi khi sửa project |
| Blender original prototype |CPU Cycles, clip640×360/12fps/1s thực; test tự động320×180/2fps/1s cũng qua; chưa chứng minh3D fullHD chất lượng phát hành |
| npm audit (bao gồm dev) |0 advisory toàn dependency set ở lần kiểm; backend pip-audit không advisory được biết, bỏ qua package nội bộ không cóPyPI |

Audio smoke là tiếng sine tự sinh, **không phải TTS tiếng Việt**. Không có kết quả Qwen/FLUX/VieNeu/Wan/LTX hoặc upload OAuth thật. Ba chức năng không được suy là hoàn thành chỉ từ các kiểm trên.

## Benchmark20 cảnh

Lệnh: `uv run --project backend python scripts/benchmark_render.py --output-dir /tmp/studio-benchmark`

- 20 cảnh,600 frame,preview360×640,30fps, ba tranh Pillow gốc luân phiên và sine tone.
- Thời gian thực: 8.493s; 70.64 frame/s tính cả tạo project/import/render/mux/verify.
- Python peak RSS: 114404KiB; max-child RSS: 114404KiB theo resource.getrusage Linux, không cộng hai số làm tổng.
- MP4 duration20,021333s,600 frame video; full decode không lỗi.
- Đây không phải benchmark1080p, ảnh noise phức tạp hoặc model inference. Không dùng70fps preview để hứa1080p real-time.

## Tính tái lập

Hai lockfile khóa dependency. Font SHA256:

- NotoSans-Regular.ttf: `b85c38ecea8a7cfb39c24e395a4007474fa5a4fc864f6ee33309eb4948d232d5`
- NotoSans-Bold.ttf: `c976e4b1b99edc88775377fcc21692ca4bfa46b6d6ca6522bfda505b28ff9d6a`

Renderer preview vàfinal cùng ScenePainter nhưng chạy ở resolution đích riêng. Guides chỉ ởUI, không vàoMP4. Project/export snapshot, input hash/idempotency và các test có run mới; không đọc artifact của lượt cũ để báo pass. Screenshots đã xem ở390px và1366px, không tràn ngang. Source low-resolution có cảnh báo; upscale không bổ sung chi tiết thật.
