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

## Nâng chất lượng tranh nhiều chi tiết (tùy chọn, không mất dữ liệu)

Trong bước **Tạo ảnh AI local**, dùng nút **Gợi ý minh họa giàu chi tiết, có bối cảnh** để bổ sung hướng dẫn dựng cảnh vào prompt đang có. Gợi ý yêu cầu vật thể/hành động khớp kịch bản, chất liệu, chiều sâu tiền–trung–hậu cảnh, đường nét sắc và chủ thể đủ lớn ở kích thước điện thoại. Prompt gốc được giữ; không gọi provider cho đến khi creator bấm **Tạo một ảnh xem thử**. Nếu prompt đã gần giới hạn 2.000 ký tự, nút không tự cắt nội dung người dùng.

Chất lượng thực tế phụ thuộc **checkpoint/model, workflow API, VRAM và ảnh nguồn**. SDXL có thể dùng img2img hoặc ControlNet (sketch/depth/lineart) để giữ bố cục giữa cảnh; đây là **hướng nâng cấp để kiểm thử**, không phải tính năng ControlNet đã tích hợp hoặc được chứng thực trên máy hiện tại. Tài liệu: [Diffusers img2img và ControlNet](https://huggingface.co/docs/diffusers/using-diffusers/img2img). Không tự tải weights/custom node hay tự nhận giấy phép. Nếu dùng model/bộ dữ liệu/ảnh tham chiếu bên ngoài, quản trị cần đối chiếu license cụ thể của từng thành phần.

Quy trình review: so ảnh candidate với lời thoại từng cảnh và style/character bible; xem đủ hình ở 9:16 và 16:9, vùng chữ, bề mặt vải/tay/vật thể và tính liên tục. Ảnh đủ pixel nhưng quá thô, sai vật thể hoặc đồ họa chỉ thay màu phải được thay trước khi xác nhận dùng. **AI generated candidate, QA fixture và codec PASS đều không tự tạo G10 PASS.**

### Độ phân giải ảnh nguồn cao hơn (tùy chọn)

Workflow ComfyUI cục bộ có thể khai báo `"resolution_profile": "high_detail"` ở **cấp gốc** file JSON tin cậy của quản trị. Ứng dụng sẽ yêu cầu ảnh nguồn portrait **1024×1792** hoặc landscape **1792×1024**, thay vì mặc định **768×1344/1344×768**. Kích thước không do prompt, model hoặc trình duyệt tùy ý thay đổi; giá trị khác `standard` hoặc `high_detail` bị từ chối. Mặc định cũ giữ nguyên cho máy không đủ RAM/VRAM.

Tùy chọn này chỉ tăng số pixel nguồn có thể giữ lại khi dựng FullHD; **không bảo đảm tăng chi tiết có ý nghĩa**, không tự upscale từ ảnh thấp nét và không chứng minh đã tạo thành công trên GPU. Ở cùng tham số model, số pixel tăng xấp xỉ 1,78×, nên có thể tăng VRAM và thời gian xử lý. Hãy kiểm thử với checkpoint có giấy phép hợp lệ, so sánh nguồn/MP4 cùng seed và đánh giá khả năng bám lời thoại, nét nhỏ, nhiễu, bàn tay và bố cục. SDXL thường tối ưu quanh 1024×1024; ảnh cao tỷ lệ dọc phải đánh giá kỹ vì độ phân giải cao hơn không luôn cho chất lượng tốt hơn. Tài liệu: [SDXL của Hugging Face](https://huggingface.co/docs/diffusers/main/using-diffusers/sdxl) và [ComfyUI Empty Latent Image](https://comfyui.dev/docs/guides/nodes/empty-latent-image/).

## Ranh giới kết nối

Provider chỉ chấp nhận HTTP loopback với cổng rõ, không user/password/path/query/fragment; không redirect. Transport local này bỏ egress proxy sau kiểm loopback để script riêng không gửi ra ngoài. Không nhận URL provider từ model hoặc form creator. Muốn chạy trên máy khác cần thiết kế mạng/auth riêng, không mở wildcard chỉ để vượt ràng buộc.

Client/app hiện là studio cá nhân local. Không triển khai API không auth lên mạng công khai. Cấu hình mẫu không có token/secret; không gửi secret trong chat hoặc commit `.env`.

## Giọng và video mẫu

Các script review dùng venv riêng và audio nhập vào renderer thật; đây chưa phải chức năng TTS của UI M3. [Hướng dẫn QA](qa-review.md) ghi cách tái tạo, model/revision, dependency CLI, giới hạn và license. Không cần Gradio Web UI để chạy phần inference CPU này.
