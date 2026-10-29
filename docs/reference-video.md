# Nghiên cứu video tham chiếu thứ hai

## Bằng chứng quan sát

Nguồn người dùng: Drive file `1TVTrleolsrLJUzch6QUHnhIdJ54klpBi`, tên `snaptik.vn_7701978010064325906_wm.mp4`. Đã mở/download công khai bằng đường Drive được chia sẻ, không cần đăng nhập hoặc trích credential. Không commit video/watermark vào repo. FFprobe:96,736s,576×1024,H26430fps,AAC. Rà mỗi4s suốt video; chưa có transcript âm thanh độc lập.

| Mốc gần đúng | Nhìn thấy | Nhu cầu engine |
|---|---|---|
|0–12s|Địa hình/độ cao, camera qua rừng/bậc thang|3D scene, camera path, scale có tham số|
|12–25s|Đồng hồ nhiệt, Mặt Trời/Trái Đất, nhãn số|Text/số dựng xác định, không diffusion text|
|25–48s|Cắt lớp khí quyển, bếp ví von, áp kế và lượng khí|Mesh/layer/transparent material và motion graphics|
|48–64s|Các hạt chuyển động, bơm xe, cột đo|Animation có kịch bản; fact check cách giải thích vật lý|
|64–96s|Công thức, so nhiệt độ, thời tiết, chốt kiến thức|Typography/captions/diagram đồng bộ lời|

Không xác định được tác giả dùng Blender, Three.js, template hay AI chỉ từ file. Một số con số trong video là xấp xỉ theo điều kiện, không tự sao chép thành quy luật tuyệt đối. Rà hình không chứng minh narration/chất lượng khoa học đã được kiểm đầy đủ.

## So sánh công nghệ

| Phương án | Điểm mạnh | Giới hạn/chi phí | Khuyến nghị |
|---|---|---|---|
|Blender procedural CPU/GPU|3D thật, camera/vật thể/thông số/nhãn có thể kiểm; không phí theo lượt|Công dựng template, CPU chậm; license chương trình khác quyền asset|Ưu tiên cảnh giáo dục như video; bản4.3.2 có sẵn, prototype thực đã chạy|
|Three.js + capture compositor|Đối tượng/nhãn tương tác, preview web|WebGL/headless và capture chất lượng cần benchmark, không hứa pixel giống render khác|Ứng viên template editor sau, chưa thêm dependency/runtime|
|Wan2.2 TI2V5B|Text/image-to-video cho b-roll, upstream công bố720p24fps|Upstream hướng GPU khoảng24GB;14B có lệnh80GB. Cần weights/disk/time, không bảo đảm chữ/số hay cơ chế khoa học|Không bắt chạy trên CPU cloud hiện tại; benchmark checkpoint trước tích hợp|
|LTX-2/LTX-family|Image/text video; repo hiện có nhiều pipeline chất lượng/tốc độ|License từng checkpoint, quantization/offload/VRAM và upscale phải kiểm; không lấy benchmark upstream làm máy mình|Ứng viên b-roll, chưa tải/chạy hay xếp hạng chất lượng|
|Ảnh FLUX/SDXL + chuyển động2D|Rẻ hơn GPUvideo, nhất quán tranh và dễ sửa|Pan/zoom ảnh không phải cảnh3D có parallax/đối tượng độc lập|Mode motion hiện đã chạy, ghi rõ giới hạn|
|Nhập clip3D/AI do người dùng sở hữu|Đưa asset chất lượng từ công cụ ngoài vào cùng editor|Cần source nét và quyền dùng; render1080 không khôi phục chi tiết đã mất|Đã hỗ trợ MP4 H264 ngắn, voice riêng, cả hai aspect|

## Chất lượng và kiểm chứng

M1 render final trực tiếp1080p, CRF18, Noto tiếng Việt; contain không kéo méo. Không quảng cáo “nét nhất tuyệt đối”: nguồn576p của clip tham chiếu không chứa chi tiết1080p gốc. Nên dựng từ asset/3D ở độ phân giải đích, text vector/font native, tránh encode lại nhiều lần. 4K/AI upscale chỉ cân nhắc khi so mẫu cho thấy lợi ích; không biến upscale thành bằng chứng thông tin thật.

Blender smoke12frame640×360/12fps: particle illustration gốc, CyclesCPU12samples, không physics simulator. Build hiện thiếu OpenImageDenoise; script tắt chức năng denoise không có sẵn, giữ render bằng samples thật. Clip chạy được không có nghĩa đã tái tạo toàn bộ video96s hoặc có chất lượng phát hành. Muốn final tăng resolution/samples và QA thời gian/noise bằng mẫu thật.

## Nguồn đã đọc

- https://github.com/Wan-Video/Wan2.2 — README model/hardware và Apache2 theo upstream; kiểm lại checkpoint khi tải.
- https://github.com/Lightricks/LTX-2 — README pipelines và các tradeoff chất lượng/VRAM; weights license chưa rà đầy đủ.
- Blender cài sẵn4.3.2; trang https://www.blender.org/about/license/ trả403 ở lần đọc, không coi là đã đọc; cần rà giấy phép phân phối trước đóng gói.
- https://developers.google.com/youtube/v3/guides/using_resumable_upload_protocol — upload resumable, không thay OAuth/app review.
- https://developers.tiktok.com/doc/content-posting-api-reference-upload-video/ — inbox init/upload/draft, không nhầm với published.
- https://developers.facebook.com/docs/video-api/guides/reels-publishing/ — Page Reels publishing; quyền/token/live test còn thiếu.

Không mua/thuê dịch vụ hoặc đăng bất kỳ bài/video nào trong nghiên cứu này.
