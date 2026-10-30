# Kiến trúc

## Stack

- Python3.12, FastAPI0.162/Pydantic2.14/Uvicorn0.54, sqlite3.
- Pillow13, NumPy2.5, OpenCV5 headless; FFmpeg7.1.5 native H264/AAC.
- React19/TypeScript5.9/Vite7.3; npm package-lock và uv.lock.
- Blender4.3.2 dùng script prototype, không cần cho đường import/render thông thường.

## Thư mục

- backend/auto_tool_video/: API, domain, store, media, jobs, renderer, worker, social hub; planning/providers/generation cho Ollama và Comfy.
- apps/web/: giao diện và Vitest/Playwright.
- assets/: font/licence và tranh mẫu gốc; scripts/: launcher/smoke/benchmark/Blender.
- docs/: kế hoạch, nghiên cứu reference, license và bằng chứng render.

## Dữ liệu chạy thế nào

APP_DATA_DIR ngoài Git, launcher default.data/. Project/asset/job metadata SQLite; media file trong assets/exports/tmp. Worker chỉ một process cho mỗi data dir bằng lock Linux; restart running→interrupted. Export snapshot và idempotency, progress frame, full decode trước success. Renderer final trực tiếp1080p theo aspect, preview nhỏ riêng; mode whiteboard hoặc motion (ảnh/clip).

Plan/image jobs giữ proposal/candidate riêng, explicit review/apply và revision. LocalTransport chỉ loopback HTTP explicit port, trust_envFalse/no redirects có chủ đích cho service local, bounded stream/time; không thực thi code/modeltool. Comfy dùng graph quản trị tin cậy, không cài node từ browser/LLM. Nguồn brief theo export snapshot ra publish JSON. Caption styles defaultcard/contrast/accent, emphasis literal; React preview và Pillow native dùng cùng field.

scripts/review-tts là CLI isolated, lock/hash riêng; model chính thức pin revision và streaming hash. VieNeu3.8.3 direct ONNX engine, preset thực; faster-whisper waveform CPU cho QA. Gradio bị loại khỏi CLI do dependency Pillow cũ có advisory; SDK metadata vẫn required, pipcheck không sạch. Không nhúng CLIvenv vàoinstaller M3. scripts/blender_review_art.py tạo stills procedural gốc, không physics simulation hoặc editor3D.

quality.py chạy sau render trước success; hard metadata/decode/CFR/audio gates, ROI pixel proxies theo scene/motion intent. Review trong jobs JSON với review_revision CAS và artifact SHA; API project/export/quality(.csv)/quality-review, QualityPanel xem/seek/chấm. Publish pack theo export snapshot kèm gate/disclosure. Không SQL migration/dependency mới; signed provenance/learned benchmark chưa có. CLI check_video_quality.py audit media cũ không sửa tệp. Silent bỏ loudnorm, narration trim/pad hữu hạn trước normalize để cảnh ngắn không quá lớn.

layout.py chia sẻ geometry full_frame/board, cover/contain và affine float với QC; timing.py là frame grid30fps/timeline/silence parser thuần stdlib, được verifier isolated import. Render scene video-only, visual dissolve rồi text overlay; narration PCM48kHz/sample-exact, AAC/loudnorm một lần cuối. POST projects/{id}/fit-audio kiểm revision/all audio fresh/60s. Save legacy dựa field-set và sceneID để không tự đổi bố cục. Policy local-qc-2 có pacing và draw_fraction-aware hold; ack tối đa500findings. Science templates gốc dựng clip native theo aspect và nhập app; không chạy code LLM.

## Lệnh

- Cài: npm --prefix apps/web ci; uv sync --project backend --frozen --group dev.
- Build: npm --prefix apps/web run build.
- Chạy: bash scripts/dev.sh; STUDIO_WEB_DEV=1 cho UI hot reload.
- Kiểm Python: ruff check/format --check, mypy, pytest backend/tests qua uv --project backend.
- Kiểm web: npm --prefix apps/web run check / format:check / test:e2e.
- Smoke: uv run --project backend python scripts/smoke_export.py --portrait1080.

M1 không cần AI runtime, M2 adapter cần local model/service tùy chọn; chưa live confirmed. OAuth/direct publish chưa triển khai. Social hub chỉ link upload web. Linux đã kiểm; native Windows/macOS chưa kiểm. Không tạo worktree cho task cloud đã cách ly.
