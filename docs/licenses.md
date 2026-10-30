# Giấy phép và nguồn tài nguyên

## Artifact đã dùng trong M1

Khóa bản exact bằng `backend/uv.lock` và `apps/web/package-lock.json`; bảng này ghi bản đã cài/kiểm ngày2026-10-29. Giấy phép runtime không thay quyền ảnh/giọng/video người dùng nhập hoặc weights của model.

| Artifact                                       | Bản/nguồn đã kiểm                             | Giấy phép/ghi chú                                                                                                                                   |
| ---------------------------------------------- | --------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| FastAPI                                        | 0.162.0, PyPI metadata                        | MIT                                                                                                                                                 |
| Uvicorn                                        | 0.54.0, PyPI metadata                         | BSD-3-Clause                                                                                                                                        |
| Pydantic                                       | 2.14.1                                        | MIT                                                                                                                                                 |
| python-multipart                               | 0.0.32                                        | Apache-2.0                                                                                                                                          |
| Pillow                                         | 13.0.0                                        | MIT-CMU theo metadata bản đã cài; không lấy tên license phiên bản cũ làm kết luận                                                                   |
| NumPy                                          | 2.5.4                                         | BSD-3-Clause, thành phần kèm theo0BSD/MIT/Zlib/CC0; xemwheellicense                                                                                 |
| opencv-python-headless                         | 5.0.0.93                                      | Apache-2.0; wheel có thành phần bên thứ ba, kiểm trước bundling                                                                                     |
| React/ReactDOM                                 | 19.x exact trong package-lock                 | MIT                                                                                                                                                 |
| Lucide React                                   | exact trong package-lock                      | ISC; icon không mang nội dung riêng của người dùng                                                                                                  |
| TypeScript/Vite/Vitest/Playwright/Prettier/axe | dev versions exact trong lock                 | Kiểm package license đi kèm, không thay giấy phép browser/runtime                                                                                   |
| SQLite                                         | stdlib Python                                 | Public domain cho SQLite; Python có license riêng                                                                                                   |
| Noto Sans Regular/Bold                         | notofonts/noto-fonts, file đi kèm             | SIL OFL; nguyên văn `assets/fonts/OFL.txt`                                                                                                          |
| FFmpeg                                         | 7.1.5 Debian build, có `--enable-gpl`/libx264 | Build này có GPL components; không gắn nhãn LGPL-only hoặc đưa binary vào installer mà chưa làm nghĩa vụ phân phối                                  |
| Blender                                        | 4.3.2 cài sẵn, không copy binary vào repo     | GPL chương trình; tranglicense trực tuyến trả403 ở lần đọc. Cần kiểm source/license gói khi đóng gói, không suy asset tự bị GPL chỉ từ chương trình |
| Hand illustration                              | hàm ScenePainter trong renderer               | Đồ họa gốc bằng primitivePillow, không lấy tay từ video                                                                                             |
| wet-shirt.png                                  | assets/examples, tạo bằng Pillow              | Tranh gốc của dự án, không AI/stock/reference video                                                                                                 |
| particle template                              | scripts/blender_scene.py                      | Code/mesh/material gốc, không dùng asset3D thương mại hoặc modelweights                                                                             |

Mã dự án chưa được người dùng chọn một license phát hành tổng thể; không tự gắn MIT/Apache cho toàn repository. Bảng này ghi nghĩa vụ dependency/provenance, không cấp quyền mới cho bên thứ ba. Không kiểm vào Git clip tham chiếu, dữ liệu người dùng hoặc outputmodel chưa rõ quyền.

## Các lựa chọn chưa tích hợp

Xem [nghiên cứu nguồn ngày2026-10-30](source-review.md) và [commit/revision/hash tài liệu](source-snapshot.json). Đây là các ứng viên, chưa là dependency được cài hoặc chứng nhận toàn bộ chuỗi quyền.

FLUX.2 Klein 4B: code và đúng model card 4B Apache-2.0; 9B non-commercial, không tự thay. SDXL 1.0: OpenRAIL++; LoRA có license riêng. Qwen3-8B model card Apache-2.0, digest Ollama thực tế cần ghi riêng. VieNeu GitHub đúng `pnnbao97/VieNeu-TTS`; code, card v3 Turbo và codec MOSS Nano khai Apache-2.0, preset/phonemizer/phụ thuộc vẫn phải pin/kiểm. Wan2.2 code/model Apache-2.0 theo nguồn đã đọc. LTX-2.5 dùng Community License 2.x, có điều kiện trả phí theo doanh thu/cách dùng; LTX-Video code Apache-2.0 không áp chung cho mọi weights. Remotion dùng license riêng, không free vô điều kiện. F5-TTS code MIT nhưng pretrained weights CC-BY-NC, không chọn mặc định thương mại. Piper hiện hành GPL-3.0, voice/data riêng. Skill Remotion chưa tìm thấy LICENSE riêng ở tree đã kiểm nên chỉ tham khảo link/ý tưởng, không vendor.

Không có weights mới trong repo, không có kết quả live ảnh/video/voice được tuyên bố từ bước nghiên cứu. File skill QA local là nội dung nguyên bản của dự án, không chép skill upstream và không gán license tổng thể cho mã dự án.

## Audit hiện tại

- npm audit --omit=dev: không vulnerability runtime báo về trong lần kiểm.
- pip-audit --local: không advisory đã biết cho dependency đã audit; package nội bộ auto-tool-video không có trênPyPI nên không được database bên ngoài audit.
- Audit là ảnh chụp thời điểm, không chứng minh không có lỗi bảo mật hoặc license model đã đạt. Kiểm lại khi thaylock/dependency và trướcpháthành.
