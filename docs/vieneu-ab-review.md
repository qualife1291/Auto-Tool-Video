# Thử giọng Việt tự nhiên — VieNeu v3 Turbo, A/B trên MP4 thật

**Trạng thái:** công cụ đối chiếu offline + test contract; **chưa thực thi hai giọng live trong PR này**.
Mục tiêu của chủ dự án là thay giọng eSpeak trong video được xem bằng VieNeu hoặc một giọng tiếng Việt tự nhiên có quyền sử dụng phù hợp, nhưng không nhầm test kỹ thuật với nghiệm thu âm thanh.

## Kế thừa đường chạy VieNeu có thật

Repo **đã có** `scripts/review-tts/generate.py` dùng VieNeu-TTS v3 Turbo ONNX CPU, 48 kHz, giọng preset (không clone), SDK `vieneu==3.8.3`, model `pnnbao-ump/VieNeu-TTS-v3-Turbo` ở revision cố định `61b85e3d937fbbacb387714180e8182823512523`, codec ONNX revision cố định, và kiểm hash/metadata. `scripts/review-tts/verify.py` giải mã MP4 cuối, đo loudness, chạy ASR. Trước đó ASR có 3/12 câu sai khác từ hoặc gần âm; đây **không chứng minh** TTS sai hay đúng cho tới khi người nghe xem lại.

Không thay thế việc QA eSpeak offline trong CI bằng model nặng hoặc tải weights khi khởi động app. Với mẫu VieNeu, tạo **hai thư mục riêng**, mỗi thư mục dùng một giọng preset khác nhau, cùng một `story.json` và cùng ảnh/video chuẩn; không đổi lời thoại ở giữa hai lượt.

Ví dụ (sau khi đã dựng đúng cấu hình venv và tải weights pin, được quản trị xác minh nguồn và giấy phép):

```bash
# Từ root repo, copy cùng story.json vào mỗi thư mục trước khi synth.
cp .data/story-upgrade/story.json .data/voice-ab-hai-dang/story.json
cp .data/story-upgrade/story.json .data/voice-ab-minh-quan/story.json

.tools/review-tts/bin/python scripts/review-tts/generate.py \
  --output-dir .data/voice-ab-hai-dang --model-dir .data/review-models --voice 'Hải Đăng'
.tools/review-tts/bin/python scripts/review-tts/generate.py \
  --output-dir .data/voice-ab-minh-quan --model-dir .data/review-models --voice 'Minh Quân'

# Xuất hai MP4 thật ở 1080p dọc và ngang với cùng hình/cảnh,
# và verify.py cho từng thư mục. Chỉ sau đó mới so bằng lệnh:
python scripts/review-tts/compare.py \
  --baseline .data/voice-ab-hai-dang \
  --candidate .data/voice-ab-minh-quan \
  --output .data/voice-ab-results.json
```

**Lưu ý:** các lệnh `generate.py` tạo WAV; mỗi thư mục cần thêm `review-portrait.mp4`, `review-landscape.mp4`, `verification.json` thực do pipeline dựng và `verify.py` chạy thành công trước khi compare. Không dùng lệnh compare như lệnh dựng video. Thư mục nêu là ví dụ, không phải hiện vật đã tồn tại. Không copy MP4 từ giọng A sang giọng B.

## Điều kiện nghiệm thu

Bộ A/B kiểm từng WAV SHA256, mẫu PCM16 mono 48 kHz, model/codec theo giấy phép Apache-2.0, lời thoại giống hệt giữa hai lượt, hash MP4 đã được verify, ASR token similarity để **chỉ ra vị trí cần nghe lại**. Báo cáo để `winner: null` và mỗi cảnh có trường manual listening trống; ASR tốt hơn không đồng nghĩa giọng tự nhiên hơn.

Người nghe Việt kiểm từng câu ở tốc độ 1×, cả bản thô và MP4 cuối, 4 tiêu chí: phát âm/dấu, ngữ điệu, tốc độ/ngắt nghỉ, giọng vùng miền và tính dễ hiểu với trẻ. Đặc biệt nghe đối chiếu **“phân tử”/“phần tử”**, **“chuyển”/“truyền”**, **“những”/“nhưng”** trong kịch bản khoa học có liên quan; không phán đoán ASR đúng tuyệt đối. Ghi timecode và hash MP4; người duyệt cuối quyết định.

Giấy phép: model card [VieNeu v3 Turbo](https://huggingface.co/pnnbao-ump/VieNeu-TTS-v3-Turbo) công bố Apache-2.0 (đọc thêm notices và giấy phép dependency/codec); repo chính [VieNeu-TTS](https://github.com/pnnbao97/VieNeu-TTS) có v3 Turbo mã nguồn mở và v4 dịch vụ proprietary. **Không clone giọng một người thật nếu chưa có quyền/chấp thuận thích hợp**. Giấy phép model không tự cấp quyền cho một giọng mẫu của bên thứ ba. Không đưa weights/WAV/MP4 vào Git.

**Không có G10 PASS tự động**: báo cáo compare là bằng chứng thử nghiệm, không là phê duyệt chất lượng hoặc phát hành.
