# Cấu hình AI local

## Trạng thái thực tế

Đã có form brief, planner Ollama, job đề xuất/duyệt, adapter ComfyUI và ảnh candidate trước khi chọn. Test contract kiểm các luồng này, không chứng minh mọi model/workflow chạy thật. Xem [QA](qa-review.md) cho kết quả phiên hiện tại. Không model nào tự tải khi mở app; không có fallback trả phí. TTS trong UI và OAuth upload trực tiếp vẫn chưa triển khai.

## Planner Ollama

Cài Ollama từ nguồn chính thức và model được chọn vào máy local theo tài nguyên/quyền dùng; ứng dụng không làm bước này thay người dùng. Mặc định adapter dùng `http://127.0.0.1:11434`, model `qwen3:8b`; có thể đặt `OLLAMA_BASE_URL` và `OLLAMA_MODEL` trước khi chạy launcher. Capabilities đọc model name/digest thực qua tags. Port sống nhưng chưa có model được chọn sẽ báo thiếu model.

Nhập brief, chọn viết mới hoặc giữ nguyên nguồn, tạo đề xuất rồi xem từng cảnh/fact flag. Chỉ sau checkbox duyệt và apply mới thay storyboard. Sửa project sau lúc tạo đề xuất gây revision conflict; tạo lại để tránh mất bản mới. Nguồn người dùng nhập không được tự fetch hoặc xác minh. Output hiển thị text, không có tools/eval.

Khi dịch vụ/model thực sẵn sàng, có thể kiểm từ thư mục root:

```bash
backend/.venv/bin/python scripts/live_planner.py --output-dir /tmp/planner-live-review
```

Report chứa nội dung đề xuất nên giữ ngoài Git; lệnh không tự áp vào project. Không gọi thành công của mock là thành công của lệnh live này.

## Tạo ảnh qua ComfyUI

Chạy ComfyUI trên loopback, tự cài checkpoint đúng quyền và đủ RAM/VRAM. Đặt `IMAGE_PROVIDER_URL` nếu khác mặc định `http://127.0.0.1:8188`. Đặt `COMFY_WORKFLOW_PATH` trỏ tới **workflow API JSON tin cậy**, với `workflow`, `bindings`, `checkpoint`, `output_node` theo [mẫu SDXL](../config/comfy-sdxl-api.example.json).

Mẫu chỉ dùng node lõi và tên `sd_xl_base_1.0.safetensors`; phải khớp checkpoint thực trong ComfyUI. Graph được kiểm cấu trúc/bindings và contract, **chưa có smoke SDXL live trên GPU trong phiên QA này**. Không giả graph này dùng được cho FLUX. Với FLUX, quản trị export workflow API đúng phiên bản, kiểm node/model/license rồi cấu hình graph riêng. Không cho model/browser gửi custom node hoặc mã để server chạy.

Adapter kiểm checkpoint có trong node metadata, lưu tên checkpoint và hash workflow; API này chưa xác nhận hash nội dung weights. Quản trị cần khóa/checksum weights riêng trước khi coi preset có thể tái lập. Chiều ảnh 768×1344/1344×768 là kích thước tạo sinh của graph hiện tại, không phải claim native final1080p. Final được compose theo aspect, contain nguồn và dựng chữ ở độ phân giải đích.

Tạo một ảnh mẫu, xem candidate/provenance rồi bấm dùng ảnh cho cảnh. Ảnh cũ và bản xuất cũ được giữ. Hủy chỉ xóa prompt của job đang chờ; Comfy có thể tiếp tục prompt đã bắt đầu vì app không global-interrupt các tác vụ khác. Lỗi/timeout/restart không tự retry vô hạn hoặc mua API khác.

## Ranh giới kết nối

Provider chỉ chấp nhận HTTP loopback với cổng rõ, không user/password/path/query/fragment; không redirect. Transport local này bỏ egress proxy sau kiểm loopback để script riêng không gửi ra ngoài. Không nhận URL provider từ model hoặc form creator. Muốn chạy trên máy khác cần thiết kế mạng/auth riêng, không mở wildcard chỉ để vượt ràng buộc.

Client/app hiện là studio cá nhân local. Không triển khai API không auth lên mạng công khai. Cấu hình mẫu không có token/secret; không gửi secret trong chat hoặc commit `.env`.

## Giọng và video mẫu

Các script review dùng venv riêng và audio nhập vào renderer thật; đây chưa phải chức năng TTS của UI M3. [Hướng dẫn QA](qa-review.md) ghi cách tái tạo, model/revision, dependency CLI, giới hạn và license. Không cần Gradio Web UI để chạy phần inference CPU này.
