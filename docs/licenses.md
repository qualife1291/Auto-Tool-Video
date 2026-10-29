# Giấy phép và nguồn tài nguyên

## Artifact đã dùng trong M1

Khóa bản exact bằng `backend/uv.lock` và `apps/web/package-lock.json`; bảng này ghi bản đã cài/kiểm ngày2026-10-29. Giấy phép runtime không thay quyền ảnh/giọng/video người dùng nhập hoặc weights của model.

| Artifact | Bản/nguồn đã kiểm | Giấy phép/ghi chú |
|---|---|---|
|FastAPI|0.162.0, PyPI metadata|MIT|
|Uvicorn|0.54.0, PyPI metadata|BSD-3-Clause|
|Pydantic|2.14.1|MIT|
|python-multipart|0.0.32|Apache-2.0|
|Pillow|13.0.0|MIT-CMU theo metadata bản đã cài; không lấy tên license phiên bản cũ làm kết luận|
|NumPy|2.5.4|BSD-3-Clause, thành phần kèm theo0BSD/MIT/Zlib/CC0; xemwheellicense|
|opencv-python-headless|5.0.0.93|Apache-2.0; wheel có thành phần bên thứ ba, kiểm trước bundling|
|React/ReactDOM|19.x exact trong package-lock|MIT|
|Lucide React|exact trong package-lock|ISC; icon không mang nội dung riêng của người dùng|
|TypeScript/Vite/Vitest/Playwright/Prettier/axe|dev versions exact trong lock|Kiểm package license đi kèm, không thay giấy phép browser/runtime|
|SQLite|stdlib Python|Public domain cho SQLite; Python có license riêng|
|Noto Sans Regular/Bold|notofonts/noto-fonts, file đi kèm|SIL OFL; nguyên văn `assets/fonts/OFL.txt`|
|FFmpeg|7.1.5 Debian build, có `--enable-gpl`/libx264|Build này có GPL components; không gắn nhãn LGPL-only hoặc đưa binary vào installer mà chưa làm nghĩa vụ phân phối|
|Blender|4.3.2 cài sẵn, không copy binary vào repo|GPL chương trình; tranglicense trực tuyến trả403 ở lần đọc. Cần kiểm source/license gói khi đóng gói, không suy asset tự bị GPL chỉ từ chương trình|
|Hand illustration|hàm ScenePainter trong renderer|Đồ họa gốc bằng primitivePillow, không lấy tay từ video|
|wet-shirt.png|assets/examples, tạo bằng Pillow|Tranh gốc của dự án, không AI/stock/reference video|
|particle template|scripts/blender_scene.py|Code/mesh/material gốc, không dùng asset3D thương mại hoặc modelweights|

Mã dự án chưa được người dùng chọn một license phát hành tổng thể; không tự gắn MIT/Apache cho toàn repository. Bảng này ghi nghĩa vụ dependency/provenance, không cấp quyền mới cho bên thứ ba. Không kiểm vào Git clip tham chiếu, dữ liệu người dùng hoặc outputmodel chưa rõ quyền.

## Các lựa chọn chưa tích hợp

FLUX.2 Klein4B: upstreamApache2;9Bnon-commercial, không chọn mặc định thương mại. SDXL1.0: OpenRAIL++; LoRA có license riêng. Qwen/Ollama: model/runtime khác nhau. VieNeu: codeApache2, weights/preset/codec cần kiểm riêng. Wan2.2: README công bốApache2; LTX: kiểm đúngcheckpoint thay vì suy từ code. Không có weights trong repo, không có kết quảlive-model đã được tuyên bố.

## Audit hiện tại

- npm audit --omit=dev: không vulnerability runtime báo về trong lần kiểm.
- pip-audit --local: không advisory đã biết cho dependency đã audit; package nội bộ auto-tool-video không có trênPyPI nên không được database bên ngoài audit.
- Audit là ảnh chụp thời điểm, không chứng minh không có lỗi bảo mật hoặc license model đã đạt. Kiểm lại khi thaylock/dependency và trướcpháthành.
