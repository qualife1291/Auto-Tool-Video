# Kiến trúc

## Stack

- Python3.12, FastAPI0.162/Pydantic2.14/Uvicorn0.54, sqlite3.
- Pillow13, NumPy2.5, OpenCV5 headless; FFmpeg7.1.5 native H264/AAC.
- React19/TypeScript5.9/Vite7.3; npm package-lock và uv.lock.
- Blender4.3.2 dùng script prototype, không cần cho đường import/render thông thường.

## Thư mục

- backend/auto_tool_video/: API, domain, store, media, jobs, renderer, worker, social hub.
- apps/web/: giao diện và Vitest/Playwright.
- assets/: font/licence và tranh mẫu gốc; scripts/: launcher/smoke/benchmark/Blender.
- docs/: kế hoạch, nghiên cứu reference, license và bằng chứng render.

## Dữ liệu chạy thế nào

APP_DATA_DIR ngoài Git, launcher default.data/. Project/asset/job metadata SQLite; media file trong assets/exports/tmp. Worker chỉ một process cho mỗi data dir bằng lock Linux; restart running→interrupted. Export snapshot và idempotency, progress frame, full decode trước success. Renderer final trực tiếp1080p theo aspect, preview nhỏ riêng; mode whiteboard hoặc motion (ảnh/clip).

## Lệnh

- Cài: npm --prefix apps/web ci; uv sync --project backend --frozen --group dev.
- Build: npm --prefix apps/web run build.
- Chạy: bash scripts/dev.sh; STUDIO_WEB_DEV=1 cho UI hot reload.
- Kiểm Python: ruff check/format --check, mypy, pytest backend/tests qua uv --project backend.
- Kiểm web: npm --prefix apps/web run check / format:check / test:e2e.
- Smoke: uv run --project backend python scripts/smoke_export.py --portrait1080.

M1 không có AI runtime, OAuth/direct publish. Social hub chỉ link upload web. Linux đã kiểm; native Windows/macOS chưa kiểm. Không tạo worktree cho task cloud đã cách ly.
