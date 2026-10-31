# Whiteboard Studio

## Sản phẩm là gì

Công cụ web local làm video whiteboard tiếng Việt cho từng nhóm tuổi. Bản M1 đã có lưu dự án, chia đoạn thành cảnh, nhập ảnh/clip MP4 và giọng WAV/MP3, sửa thứ tự, chọn whiteboard hoặc minh họa chuyển động, xuất MP4 dọc 9:16 hoặc ngang 16:9 ở 1080p. Có preview, phụ đề phân đoạn ước lượng và gói metadata/checklist. Không phí API bắt buộc, không watermark.

Đã có adapter/form AI viết storyboard qua Ollama và tạo ảnh candidate qua ComfyUI, luôn duyệt trước áp dụng; cần dịch vụ/model local được cấu hình theo [hướng dẫn AI](docs/local-ai.md). Có ba kiểu phụ đề từng cảnh và nhấn cụm từ; thư viện ý tưởng khoa học với brief tiếng Việt nguyên bản kèm nguồn Tongjiang Lab, điều kiện dùng lại nguồn ở [báo cáo](docs/source-review.md). Script review tạo tranh Blender/Pillow và giọng local để nhập vào renderer; UI tạo giọng, template3D editor và OAuth upload trực tiếp còn trong [kế hoạch phát triển](docs/development-plan.md). Hub đăng hiện mở trang đăng chính thức sau khi tải tệp; không giả kết nối/đăng thành công. Nhãn made-for-kids không bảo đảm vào YouTube Kids. [Đặc tả](specs/whiteboard-video-tool.md) còn `approved` tới khi đủ mọi mốc.

## Tài liệu chung cho AI agent

- [Bảng công việc A01–A10](docs/agent-workboard.md): nơi duy nhất theo dõi task, ưu tiên, tiêu chí nghiệm thu và cách phối hợp.
- [Bàn giao hiện tại](.agent/handover/LATEST.md), [các việc còn mở](.agent/memory/short-term/TASKS.md), [lộ trình M1–M4](docs/development-plan.md), [đặc tả đã duyệt](specs/whiteboard-video-tool.md).
- **Branch làm việc chung:** `feat/short-video-studio`. Các phần storyboard từng giây, áo chuyển trạng thái và caption bounce mới nhập là WIP chưa kiểm thử lại; video 0,92× chưa render/xác minh. Không lấy kết quả QC cũ làm chứng nhận cho code mới.

## Cách chạy

Sau mỗi lần xuất, tool kiểm kỹ thuật/audio và đưa cảnh báo kèm timestamp; creator điền phiếu1–5 theo đúng hash video. Có JSON/CSV và [rubric kiểm thủ công](docs/video-quality-standard.md). Đây là QC local và người duyệt, chưa chạy learned scores VBench/AIGCBench hoặc chứng nhận pháp lý. MP4 vẫn tải được để review khi chưa duyệt.

Cần Linux, Node24+, Python3.12+, uv và FFmpeg/FFprobe có libx264/AAC. Font Noto có dấu đã đi kèm giấy phép; không tải font qua mạng lúc render.

```bash
npm --prefix apps/web ci
uv sync --project backend --frozen --group dev
npm --prefix apps/web run build
bash scripts/dev.sh
```

Mở trình duyệt local ở cổng8765. Launcher mặc định lưu vào `.data/` đã được ignore; `APP_DATA_DIR` đặt nơi khác nếu cần. Không dùng chung data directory cho hai worker; Ctrl+C dọn các process do launcher tạo. Chế độ sửa UI: `STUDIO_WEB_DEV=1 bash scripts/dev.sh`, giao diện dev ở cổng5173. Browser mobile ở đây là kiểm layout, renderer chạy ở backend.

Tạo dự án → nhập lời thoại, mỗi đoạn một cảnh → nhập `assets/examples/wet-shirt.png` hoặc ảnh của bạn → nhập giọng từng cảnh (hoặc chủ động chọn không lời đọc) → chọn tỷ lệ và xuất. Clip MP4 chỉ nhận H.264, tối đa19,65s/cảnh; tắt tiếng gốc, dùng narration riêng. Nguồn thấp nét không trở thành nhiều chi tiết hơn chỉ vì xuất1080p. Video ngang không tự thành YouTube Shorts.

Cảnh mới mặc định hình toàn khung; chọn giữ toàn ảnh hoặc phủ kín và chỉnh tiêu điểm để kiểm crop. Có tùy chọn bố cục bảng cũ, hòa hình nhẹ và tốc độ reveal nét vẽ. Sau khi nhập đủ giọng khớp lời, bấm **Khớp nhịp theo giọng đã nhập** để bỏ thời gian giữ hình dư, giữ trọn audio và thêm khoảng nghỉ ngắn. QC hiển thị tổng khoảng im lặng và báo đoạn dài; nghe/xem vẫn là bước duyệt cần thiết. Kịch bản mẫu12cảnh và diễn biến hình được ghi tại [storyboard](docs/storyboard-review.md).

Prototype3D có tham số, không phải model AI hay mô phỏng khoa học chính xác:

```bash
blender -b --threads 2 --python scripts/blender_scene.py -- --output /tmp/particles.mp4 --width 1920 --height 1080 --frames 60 --fps 30 --samples 32
```

Nhập clip đó vào một cảnh “Minh họa chuyển động”. Render CPU độ phân giải cao có thể lâu; mẫu smoke đã kiểm chỉ640×360/12fps/1s, không phải bằng chứng đạt chất lượng3D của toàn video tham chiếu.

## Cách kiểm

```bash
uv run --project backend ruff check backend scripts
uv run --project backend ruff format --check backend scripts
uv run --project backend mypy backend/auto_tool_video
uv run --project backend pytest backend/tests -q
npm --prefix apps/web run check
npm --prefix apps/web run build
npm --prefix apps/web run test:e2e
uv run --project backend python scripts/smoke_export.py --portrait1080
npm --prefix apps/web audit --omit=dev
uv run --project backend pip-audit --local --progress-spinner off
```

E2E dùng Chromium ở `/usr/bin/chromium`; đặt `CHROMIUM_BIN` nếu khác. Test server dùng data directory riêng dưới `/tmp`, không đổi dự án đang dùng. Trong sandbox chặn IPC/socket, chạy API/E2E bằng cơ chế cấp quyền của môi trường; không tắt assertion để làm pass. File smoke có track sine fixture, không phải giọng TTS. Xem [bằng chứng render](docs/render-benchmark.md), [giấy phép](docs/licenses.md), [nghiên cứu video](docs/reference-video.md) và [handover](.agent/handover/LATEST.md).

Video mẫu có giọng Việt thật, cách tái tạo và kết quả kiểm tổng quát nằm trong [QA review](docs/qa-review.md). Báo cáo tách test contract AI khỏi model live và phần còn thiếu; không có test nào bảo đảm video được đề xuất hoặc vào Kids.
