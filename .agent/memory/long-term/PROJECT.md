# Dự án

## Sản phẩm là gì

Studio video tiếng Việt local; M1 whiteboard/motion, nhập ảnh/clip/giọng, hai tỷ lệ16:9/9:16 và xuất1080p. Có3kiểu phụ đề/nhấn cụm từ và thư viện4brief khoa học nguyên bản tham khảo Tongjiang. M2 đã có Ollama/Comfy adapters và review/apply, chưa xác nhận model live. M3 giọng/alignment UI và M4 OAuth upload còn backlog. Đặc tả vẫn approved, chưa implemented.

Xuất video có QC local tự động (PTS/decode/audio/proxies), phiếu creator1–5/hash/CAS và CSV/JSON. Benchmark learned VBench/AIGCBench chưa chạy; không tự chấm vật lý/nội dung hoặc chứng nhận EU.

Cảnh mới full_frame/cover/focal/dissolve, legacy giữ board/contain/cut; fit-audio để giảm hold dư. Renderer affine float/pen-up và PCM timeline với một lần AAC; QC có silence/pacing. Mẫu12cảnh native science motion tại scripts/science_story.py/create_story_video.py và docs/storyboard-review.md, vẫn cần creator nghe/xem; không phải TTS UI hoặc physics simulator.

## Người dùng

Người tạo nội dung; đối tượng xem chọn theo độ tuổi, không gộp mọi lứa tuổi vào một kịch bản.

## Ranh giới bền

- Ưu tiên chất lượng và giải pháp không có phí API bắt buộc.
- Không tự đăng hoặc bảo đảm vào YouTube Kids.
- Video review thật dùng art Blender/Pillow gốc, VieNeu local qua CLI riêng; không coi đây là UI TTS M3. License của từng model/asset riêng; Tongjiang bài/cover/catalog CC BY-NC4.0, kênh cá nhân kiếm tiền không tự được miễn NC.
