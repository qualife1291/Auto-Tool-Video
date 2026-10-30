---
name: video-quality-review
description: Kiểm chất lượng video thật của Auto-Tool-Video và so provider bằng bằng chứng về hình, giọng, phụ đề, continuity, hai tỷ lệ và tài nguyên.
---

# Kiểm chất lượng video

## Khi sử dụng

Dùng sau khi thay renderer/template/model/provider, khi review clip thành phẩm hoặc trước khi bật preset mới. Đây là quy trình QA nguyên bản của dự án, không phải model tạo video. Không dùng để tuyên bố chất lượng từ nghiên cứu README hoặc mock test.

Đọc `specs/whiteboard-video-tool.md`, `docs/source-review.md` và handover hiện tại. Chỉ kiểm những capability đang thực sự triển khai; giữ nguyên quyền đã được người dùng cấp. Không cài engine, tải weights, gửi asset lên dịch vụ ngoài, mua API, kết nối tài khoản hoặc publish chỉ để thực hiện review.

## Quy trình

1. Xác định artifact và snapshot: project revision, aspect, profile, input/ref hash, template/workflow/model digest, font, seed, thông số encode và máy chạy. Thiếu model thật thì ghi chưa kiểm live. Không thay input để che lỗi; giữ asset cũ.
2. Dùng lệnh kiểm trong README của repo. Test hành vi/schema/media/job là bằng chứng kỹ thuật; mock provider không phải bằng chứng model tạo hình/giọng tốt. Ghi riêng lỗi có từ trước và lỗi do thay đổi.
3. Kiểm metadata bằng FFprobe và decode toàn file qua FFmpeg theo argv, không ghép input vào shell. Trước khi dùng filter cụ thể, kiểm build có hỗ trợ. Kiểm kích thước/fps/duration/audio thật; nếu build thiếu công cụ thì ghi giới hạn, không bỏ assertion để pass.
4. Xem still đầu/giữa/cuối **mọi cảnh**, thêm frame ở chuyển động/chuyển cảnh nghi ngờ; xem lại clip ở tốc độ thật. Still không chứng minh temporal continuity. Kiểm chữ tiếng Việt/nhãn/tay/vật thể, crop, mờ/halo/flicker, chuyển động có ý nghĩa. Xem full size và kích thước điện thoại. Ghi native/upscaled đúng nguồn.
5. Với nhân vật lặp, đối chiếu tối thiểu5 cảnh và các reference đã duyệt: silhouette, màu, trang phục, tỷ lệ, vật thể và hướng chuyển động. Seed/embedding không thay người duyệt. Một cảnh mẫu đẹp chưa đủ mở batch tự động.
6. Nghe giọng và audio **trong thành phẩm**, không chỉ file TTS đầu vào. Kiểm bỏ/lặp/sai từ, âm cuối, khoảng dừng, nhạc che lời. Nếu chưa có người nghe hoặc công cụ nghe phù hợp, ghi chưa đánh giá cảm nhận; có waveform/track không đủ để ghi đã nghe. Đo LUFS/true peak thật theo gate trong đặc tả; silent mode là chủ động, không lỗi bị che.
7. So caption với script đã duyệt và audio thật. Kiểm cue tăng dần, ranh giới/2 dòng/dấu tiếng Việt/safe zones; ghi các mốc lệch và sửa theo phrase khi alignment không chắc. ASR không tự sửa script. Không gọi timestamps ước lượng là karaoke chính xác.
8. Xuất cùng trường hợp kiểm ở 16:9 và 9:16 với layout/camera riêng. Kiểm đủ nội dung, không méo, không crop mất chủ thể, chữ đọc được và guides không bị ghi vào video. Kiểm từng profile đang bật; người lớn duyệt phù hợp tuổi/kiến thức.
9. So tối ưu với baseline cùng brief/ref/resolution/budget: cold/warm runtime, peak RAM/VRAM, disk, retry/failure và chi phí API nếu có. Không áp tốc độ upstream lên máy local. Quantization/upscale/giảm bước chỉ chấp nhận khi sample đạt; giữ cấu hình quay lại. VMAF/SSIM chỉ cho reference cùng nội dung, không chấm tính đúng/hấp dẫn.
10. Test cancel/restart/duplicate/late result/revision conflict và mất provider: không mất bản tốt cũ, không nhân job hay tự chuyển paid API. Không bật preset nếu gate bắt buộc chưa đạt; tiếp tục những phần độc lập còn làm được.
11. Sau gen lấy quality_report của đúng export job, hoặc dùng scripts/check_video_quality.py với snapshot thật. Đọc docs/video-quality-standard.md cho rubric1–5: critical/1–2 loại,3sửa, thiếu review chờ, toàn4–5 chỉ duyệt khi kỹ thuật và các bước con người đủ. Không tự chấm điểm thay creator. Motion intent/scene cuts/whiteboard hold phải được xét trước khi gọi near-repeat là freeze; MAE/luma/Laplacian là proxies chưa hiệu chuẩn, không là VBench/physics scores. VBench/AIGCBench chưa chạy thì giữ not_run. Ghi rõ hash/review revision/nguồn và disclosure; unsigned metadata không phải C2PA, watermark bền vững hoặc legal certification.

## Báo cáo cần có

Ghi vào handover hoặc báo cáo benchmark đã được đặc tả cho phép, tránh tạo tài liệu trùng vai trò. Mỗi kết luận gắn artifact/command/input và kết quả; không đưa video người dùng, secret hoặc dữ liệu riêng vào Git.

| Trường     | Phải ghi                                                                                      |
| ---------- | --------------------------------------------------------------------------------------------- |
| Phạm vi    | Provider/style/profile/aspect nào, bản code/model/config và máy nào                           |
| Bằng chứng | Test đã chạy và số ca, artifacts đã xem/nghe, lệnh decode/đo, cold/warm resource usage        |
| Lỗi        | Đoạn/frame/cue cụ thể, mức ảnh hưởng và cách tái hiện; ảnh gốc và bản đã duyệt vẫn giữ        |
| Giới hạn   | Chưa có GPU/model/quyền, chưa nghe tay, chưa kiểm OS/thiết bị hoặc live upload                |
| Quyết định | Đạt gate nào, chặn gate nào, preset được bật hay tiếp tục thử; không hứa viral/Kids inclusion |

Không dùng một điểm tổng hợp tự tạo để che lỗi bắt buộc. Chỉ ghi hoàn tất khi các gate trong đặc tả tương ứng thực sự đạt.
