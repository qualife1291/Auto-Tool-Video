# Kiểm thử và video review

## Kết quả và phạm vi

Kiểm ngày **2026-10-30**, trên Linux: 5 CPU logic nhìn thấy, quota CPU cgroup4core, giới hạn RAM cgroup32GiB, không có GPU NVIDIA. Kết quả cuối: **114 pytest + 8 Vitest + 9 Playwright = 131 test qua**, không skip. Có một cảnh báo deprecation upstream Starlette/httpx; không tắt cảnh báo/assertion. Ruff, format, mypy trên 12 module, TypeScript, Vite build và Prettier đã kiểm. Các ca AI dùng mock được ghi là contract, không phải model tạo ảnh/video đã chạy thật.

Bản mẫu chủ đề **“Chiếc áo khô: nước đi đâu?”**, profile family 6+, 8 cảnh/32 giây, tranh gốc (bản nâng dùng Blender/Pillow), giọng preset Hải Đăng, phụ đề tiếng Việt, kết hợp whiteboard và pan ảnh nhẹ. Xuất H.264/yuv420p/30fps + AAC 48 kHz, cả 1080×1920 và 1920×1080; video thực dài khoảng 32,021s do audio/container padding. Không watermark nhìn thấy, nhạc nền tắt, không giọng clone, không stock hoặc tài nguyên từ video tham chiếu.

Đây là mẫu từ **renderer ứng dụng thật với audio nhập vào**, có still3D procedural được dựng sẵn, không phải video3D/Wan/LTX tự sinh. Script TTS chạy riêng; UI chưa có TTS M3. Cần creator nghe/xem và nhận xét cảm nhận, nhịp và mức phù hợp tuổi. Không nhận đã có người nghe duyệt, không bảo đảm viral, kiếm tiền hoặc được vào YouTube Kids.

## Phụ đề và nguồn bài học sau nâng cấp

Mỗi cảnh chọn card sáng, contrast nền xanh đậm hoặc accent có cụm từ tô vàng; tiếng Việt giữ nguyên, khớp literal không thực thi HTML/regex người dùng. Tối đa2dòng/trang, không giả karaoke. Contrast chỉ trượt nhẹ12px trong0,18s, không nhấp nháy. Cả native/preview ở hai aspect dùng cùng field; project cũ default card. Kiểm pixel geometry/màu và highlight qua ngắt dòng, API invalid/default/restart; E2E kiểm lưu/reload và xuất phối3kiểu.

Thư viện4brief khoa học tiếng Việt nguyên bản có link Tongjiang Lab; chọn mẫu chỉ thay brief, có xác nhận nếu đang có nội dung. E2E cả desktop/mobile kiểm hủy/xác nhận, giữ lời thoại/storyboard, lưu/reload nguồn, axe và không tràn ngang. Publish metadata giữ nguồn của export snapshot dù draft về sau đổi nguồn. CC BY-NC4.0 của bài gốc được ghi rõ trong UI và [báo cáo nguồn](source-review.md); không chạy/vendor HTML bên ngoài.

## Các lỗi đã phát hiện và sửa

| Vấn đề                                                              | Kết quả sửa/kiểm                                                                                                                                                                |
| ------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Caption cắt giữa một từ tiếng Việt và để một từ hỏi đơn độc ở dòng 2 | Xuống dòng theo từ; chỉ hard-wrap token dài không vừa một dòng. Cân hai dòng để tránh orphan. Test giữ nguyên chữ, giới hạn chiều rộng và toàn bộ câu trong mẫu vừa1 cue/2 dòng.  |
| Nét vẽ bắt đầu ở mũi tên/chi tiết nhỏ                               | Ưu tiên silhouette lớn trước, thứ tự ổn định. Đã xem frame đầu/giữa/cuối của từng cảnh; đây là heuristic cho tranh mẫu, chưa là điều khiển semantic mọi ảnh.                    |
| True peak AAC ở bản đầu −0,58dBTP, vượt mục tiêu −1                 | Chừa headroom trước AAC: loudnorm TP−2dB. Đo **input_i/input_tp của file thành phẩm**, không nhầm output giả định của filter phân tích. Hai aspect đều được kiểm lại.           |
| Lint/typecheck M2 còn dở                                            | Sửa kiểu config/callback/result và ngoại lệ; không bỏ kiểm kiểu.                                                                                                                |
| Provider trả JSON/graph lỗi, stream quá lớn, redirect hoặc trickle               | Giới hạn dòng/response/time trên từng chunk (JSON30s/chat600s, không buffer4096byte trước kiểm); kiểm shape/nodes; từ chối redirect ngay cả client injected có bật follow. Test không fetch đường dẫn/model URL lạ.                                 |
| Candidate image lưu SHA từ bytes gốc thay vì file chuẩn hóa         | Hash asset khớp file thực; hash nguồn giữ riêng trong provenance. Duyệt/apply/revision/idempotency giữ project cũ.                                                              |
| Gradio của SDK kéo Pillow 12.3 có 39 advisory                          | Loại bộ Web UI không dùng khỏi venv review CLI bằng excludes, khóa còn 48 package; audit lại không còn advisory được báo. App backend đã dùng Pillow 13 riêng, không bị đổi xuống. |

## Bằng chứng tự động

| Nhóm                    | Lệnh/thực hiện                                                                        | Kết quả                                                                                                                                                                |
| ----------------------- | ------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Backend                 | `backend/.venv/bin/python -m pytest backend/tests -q`                                 | 114 passed; import/MIME/path/revision/audio-stale/jobs/cancel/restart/render hai aspect và provider contracts.                                                           |
| Frontend                | `npm --prefix apps/web run check`                                                     | TypeScript và 8 Vitest qua.                                                                                                                                              |
| Browser                 | `npm --prefix apps/web run test:e2e`                                                  | 9 passed; desktop 1366/mobile 390, import→render→download→reload, keyboard/text injection, axe WCAG 2A/AA; mock planner review/reload/apply và candidate không tự thay ảnh. |
| Python quality          | Ruff check, Ruff format check, mypy `backend/auto_tool_video`                         | Qua;12source modules.                                                                                                                                                  |
| Web quality             | `npm --prefix apps/web run build`, `run format:check`                                 | Qua.                                                                                                                                                                   |
| App dependency audit    | `npm --prefix apps/web audit --omit=dev`; backend `pip-audit --local`                 | Không advisory được báo. Package nội bộ chưa có trênPyPI không được database audit, không gọi là đã audit mã nội bộ.                                                   |
| Review dependency audit | `pip-audit --path <review-venv>/lib/python3.12/site-packages`                         | Không advisory được báo sau loạiUI; chưa là chứng nhận không có mọi lỗi.                                                                                               |
| MP4 thật                | `scripts/review-tts/verify.py`                                                        | FFprobe, full decode với `-xerror`, A/V duration lệch<100ms, resolution/codec/fps và LUFS/true peak được assert trên hai file.                                          |
| Lời đọc thật            | CTranslate2 ASR multilingual large-v3-turbo, CPUint8, nhận waveform 16 kHz của MP4 cuối | So transcript với lời đã duyệt, bỏ qua case/punctuation. Chi tiết từng câu ở `verification.json` ngoàiGit; ASR không chứng nhận phát âm hoặc thay nghe tay.            |
| Hình                    | Contact sheets24frame/aspect và still native, font và safe zones                      | Xem đầu/giữa/cuối mọi cảnh, kiểm crop/chữ/hình và continuity áo xanh; creator còn cần review chuyển động ở tốc độ thật.                                                |

## Artifact và số đo baseline trước nâng đồ họa

Artifacts giữ ngoài Git trong thư mục output do người chạy chọn: `review-portrait.mp4`, `review-landscape.mp4`, `story.json`, `tts-provenance.json`, `report-portrait.json`, `report-landscape.json`, `verification.json`, tranh gốc và audio từng cảnh. Các MP4/link review được cung cấp trong phản hồi cho người dùng; không upload công khai lên mạng xã hội.

Report gồm checksum MP4, project revision/snapshot, thời gian render, FFprobe, giọng/SDK/model/codec revision/hash và transcript kiểm. Số đo được trích từ report cùng phiên; không lấy số từ README upstream. Native1080p là canvas/composition và chữ; hình gốc 1600×1400 được contain, không giả source 480p là native HD.

Mục tiêu: integrated loudness−16LUFS±1, true peak≤−1dBTP. Cảnh có ý ngắn được giữ 4s, audio thật ngắn hơn có silence padding chủ đích; không time-stretch hoặc cắt chữ. Mỗi cảnh một cue, chưa forced alignment từng từ. Bản ngang và dọc có layout riêng; không stretch hoặc center-crop chủ thể.

Hai file baseline đều đo **−15,72LUFS / −1,37dBTP**, full decode qua. ASR khớp 8/8 cue sau chuẩn hóa hoa/thường/dấu câu, trong đó câu kết nhắc lại lời cảnh 2 và dùng lại audio thật. Đây là kiểm tra trên đúng mẫu này, không là độ chính xác chung của TTS/ASR. Trong quá trình biên tập, ASR nhỏ nhận sai nhiều, turbo bản đầu khớp6/8cue; hai câu5/8 được viết gọn/rõ lại, câu8 nhắc lại câu2. Số8/8 thuộc kịch bản đã chỉnh, không phải bằng chứng model tự sửa phát âm hoặc benchmark khách quan mọi câu.

| File | Bytes | Thời gian render | SHA256 |
|---|---:|---:|---|
| review-portrait.mp4 | 1403017 | 33,947s | `7e0a62e3814ddbef249cd8510bbb4a2105862f493ac39f25105af97b6c430a38` |
| review-landscape.mp4 | 1148727 | 30,568s | `7db9f1f9070c4821a5c5616b5433ca29c54889e7b1acee8c34820e182eee935f` |

Thời gian render là một lượt warm/cached-input trên máy phiên này, chưa là SLA hoặc kết quả benchmark mọi cảnh/model. TTS dùng 2 thread CPU FP32; ASR 2 thread int8. Chưa thu peak RAM/VRAM của toàn pipeline, không đưa số ước lượng làm kết quả đo.

## Bản nâng đồ họa đã xuất

Ảnh3D gốc1600×1400, Cycles CPU/128samples/seed20261030 (áo2thread, cốc4thread): áo cùng silhouette/vật liệu xanh ở trạng thái có giọt nước trên vải và áo khô; cốc nước thường và nhiệt kế không gán số. Không phải mô phỏng vật lý. Tranh whiteboard thêm đường may, nếp vải, ô phóng đại sơ đồ sợi vải/nước; cảnh ấm/thoáng có ký hiệu ánh nắng và luồng khí. Text và dấu do Noto/renderer dựng ở canvas đích, không sinh chữ trong ảnh bằng diffusion.

Kiểm nháp phát hiện mặt nước bị disk vành cốc che, trông như nắp: đã sửa thành cốc rỗng có thành trong và mặt nước nằm dưới miệng cốc; kiểm nháp640px rồi xuất lại cup. Giữ baseline và input cũ, không thay để che lỗi. Lượt all3D được dừng sau hai ảnh áo hoàn thành; thời gian hai ảnh lấy từ render log, riêng cốc từ lần chạy lại có provenance.

Hai MP4 nâng cấp full decode/metadata qua, cùng **−15,72LUFS / −1,37dBTP**, H264/yuv420p/30fps/AAC48kHz,32,021333s. ASR trên bản dọc khớp8/8cue chuẩn hóa; đã hash packet AAC của hai aspect và xác nhận giống nhau (audio-identity.json). Đây vẫn là hỗ trợ tự động; creator nghe/xem còn chờ. Đã xem24frame đầu/giữa/cuối mỗi aspect và still native của hook, accent, cốc và cảnh kết; dấu/chữ/nhấn/crop đúng ở các frame đã kiểm, không suy thành review chuyển động toàn clip ở tốc độ thật.

| Bản nâng | Bytes | Dựng MP4 + contact sheets | SHA256 |
|---|---:|---:|---|
| review-portrait.mp4 | 1632420 | 35.044s | `19d1f6c65d91081402c2caa200a9b9d51bb1112d6619c87ae3f16c847690fac3` |
| review-landscape.mp4 | 1325349 | 32.778s | `fe3ed6749d164b16e622a74301d0109d4f44eae015a1dd74afe8f6c63363cb6f` |

Ảnh áo ướt281,19s, áo khô276,53s theo Blender render log (không gồm setup); cốc rỗng153,013s gồm setup/render ở4thread. Tất cả1600×1400/128samples/seed20261030. Thời gian MP4 trên gồm tạo contact sheets, khác phạm vi đo baseline; không dùng làm kết luận tăng/giảm tốc độ tương đối. Không phí API, không GPU, chưa thu peak RSS toàn pipeline.

Package riêng trong `.data/review`: MP4, stills, audio, art/provenance, reports và hai SQLite project store. Có thể mở dự án mẫu với `APP_DATA_DIR=.data/review/studio-portrait bash scripts/dev.sh` (hoặc studio-landscape); không cần TTS model để nghe audio đã nhập. Thư mục này bị ignore, không phân phối weights hoặc đăng công khai.

## Giấy phép cho nhu cầu cá nhân

Với đúng bộ tài nguyên trong mẫu, nhu cầu dùng cá nhân phù hợp với các giấy phép đã kiểm. Không suy “cá nhân” thành “mọi model đều miễn phí”: kênh cá nhân có quảng cáo/kiếm tiền vẫn có thể là cách dùng thương mại theo điều khoản của một model.

| Thành phần mẫu             | Nguồn/giấy phép                                                                                                                                            | Phạm vi kết luận                                                                                                        |
| -------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| Kịch bản/tranh/bàn tay     | Nội dung gốc dự án                                                                                                                                         | Không lấy asset của tác giả video tham chiếu hoặc nhân vật thương mại.                                                  |
| Font Noto Sans             | SIL OFL, license đóng gói trong assets/fonts                                                                                                                | Giữ license khi phân phối font. Video không phải gói phân phối binary của engine.                                       |
| VieNeu-TTS SDK 3.8.3/preset | Upstream `pnnbao97/VieNeu-TTS`, Apache-2.0; wheel/hash khóa trong requirements                                                                             | Preset Hải Đăng thực có trong SDK; không clone giọng người dùng. Metadata giọng và hash preset được ghi.                |
| VieNeu v3 Turbo ONNX       | `pnnbao-ump/VieNeu-TTS-v3-Turbo` revision`61b85e3d937fbbacb387714180e8182823512523`, Apache-2.0                                                            | Đã kiểm 13 graph/config/model files của TTS+codec; không dùngcheckpoint khác ngầm.                                        |
| Codec ONNX                 | `OpenMOSS-Team/MOSS-Audio-Tokenizer-Nano-ONNX` revision`ceff0d0749bfb3fa2d61149794ec6feef0d1e1ae`, Apache-2.0                                              | Dùng bản ONNX riêng đã kiểmlicense/hash, không suy license từ repo codec khác.                                          |
| Phonemizer sea-g2p         | Package 0.10.0, file LICENSE đi kèm Apache-2.0                                                                                                                           | Đã đọc license trong wheel; đây không phải việc cấp quyền nhân thân/asset bên ngoài.           |
| ASR để kiểm                | faster-whisper1.2.1 MIT; checkpoint chuyển đổi `mobiuslabsgmbh/faster-whisper-large-v3-turbo` revision`0a363e9161cbc7ed1431c9597a8ceaf0c4f78fcf`, card MIT | Chỉ kiểm audio local, không phải giọng phát trong video.                                                                |
| FFmpeg/libx264             | Build local có GPL components                                                                                                                              | Dùng để xuất video; nếu đóng gói/phân phối binary phải làm nghĩa vụ GPL tương ứng. Không tự gán GPL cho mọi video xuất. |

Không dùng Remotion, LTX, F5pretrainedNC hoặc FLUX9B/dev cho video mẫu này. Các lựa chọn đó có điều kiện riêng trong [báo cáo nguồn](source-review.md); không cần mua license/API cho cấu hình mẫu đã chọn. Phần mềm miễn phí vẫn dùng điện, máy và dung lượng; không có API trả phí trong lần tạo mẫu.

## Tái tạo bản mẫu

Chạy từ root, sau khi cài dependency backend/frontend theo README. `uv` cần cache writable theo môi trường; không cài global. Ví dụ dùng `.tools/review-tts` và `.data/review`, đều ngoài Git qua ignore của dự án:

```bash
uv venv --python backend/.venv/bin/python .tools/review-tts
uv pip sync --python .tools/review-tts/bin/python --require-hashes scripts/review-tts/requirements.txt
blender -b --threads 2 --python scripts/blender_review_art.py -- --output-dir .data/review/art-3d --samples 128
backend/.venv/bin/python scripts/create_review_video.py --output-dir .data/review --prepare --art-dir .data/review/art-3d
.tools/review-tts/bin/python scripts/review-tts/generate.py --output-dir .data/review --model-dir .data/review-models
backend/.venv/bin/python scripts/create_review_video.py --output-dir .data/review
.tools/review-tts/bin/python scripts/review-tts/verify.py --output-dir .data/review --model-dir .data/review-models
```

Lần đầu cần mạng tới PyPI/HuggingFace để tải dependency/weights; script kiểm đúng revision/license và SHA256 LFS/Git blob, không tải Python remote từ model. Sau tải, inference dùng đường dẫn model local. CLI luôn chủ động do người chạy gọi, không app startup hoặc paid fallback.

Lock được tạo bằng:

```bash
uv pip compile scripts/review-tts/requirements.in --excludes scripts/review-tts/excludes.txt --python-version 3.12 --generate-hashes -o scripts/review-tts/requirements.txt
```

**Giới hạn packaging:** SDK upstream khai Gradio là dependency bắt buộc, nhưng CLI này chỉ dùng module ONNX/audio và chủ động loại bộ UI. Vì vậy `uv pip check` trên venv riêng sẽ báo thiếu Gradio; không tuyên bố bản cài SDK Web UI đầy đủ hoặc check đó qua. Inference thật sau loạiUI đã tạo audio byte-identical với câu đầu bản trước; ASR thật cũng chạy qua. Cần sửa packaging upstream hoặc adapter inference tối giản riêng trước khi đưa TTS vào gói M3 cho người dùng cuối. Không dùng override hạ audit hoặc cài Pillow có advisory để làm thỏa metadata.

## Phần chưa được kiểm/triển khai

- Chưa có GPU và checkpoint ComfyUI, nên FLUX/SDXL live generation chưa chạy; graph mẫu chỉ được kiểm contract. Qwen/Ollama live chưa xác nhận, có script smoke riêng; model3D/videoAI chưa benchmark.
- TTS là script review tách biệt, chưa có voice picker/job/cache/alignment trong UI M3. Mẫu có câu kết nhắc lại ý chính và tái sử dụng audio cùng lời thoại có provenance; không sinh lại audio vô ích.
- Chưa có người nghe duyệt, test 20 câu đa dạng hoặc device QA ngoài Chromium desktop/mobile emulation. ASR không thay các mục này.
- OAuth/token/live upload YouTube/TikTok/Facebook, SRT/cover/180s/packaging còn M4. Không có publish thật hay xác nhận inclusion vào Kids.
- Xem [handover](../.agent/handover/LATEST.md) để tiếp tục; không đổi toàn đặc tả thành implemented chỉ vì test hiện tại qua.
