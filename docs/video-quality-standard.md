# Quy trình kiểm định video sau gen

## Phạm vi và cách dùng

Quy trình nội bộ ngày2026-10-30 áp dụng cho file thành phẩm của tool, gồm kiểm kỹ thuật tự động và nghiệm thu của creator. Thang1–5 dưới đây là rubric của dự án dựa trên yêu cầu người dùng, không phải thang điểm chính thức hoặc chứng nhận của VBench, AIGCBench hay EU. Tài liệu có thể dùng trực tiếp để review thủ công, in ra hoặc điền cùng CSV tải từ tool, không cần chạy code.

Sau khi xuất, mở **Kiểm định sau khi dựng**, xem báo cáo/timestamp, đối chiếu script và hình nguồn của chính bản xuất. Chấm từng hạng, ghi mốc lỗi, đánh dấu critical nếu phá thông điệp/logic hoặc lỗi thấy rõ ở tốc độ bình thường. Xem hết clip, nghe audio thành phẩm, kiểm caption/fact/tuổi và khai báo nguồn gốc trước khi lưu phiếu. Tool giữ hash video và phiên bản phiếu; chỉnh draft không sửa kết quả của file cũ.

## Hai lớp kiểm tra

| Lớp | Kiểm gì | Kết quả và giới hạn |
|---|---|---|
| Kỹ thuật bắt buộc | SHA256, kích thước theo option, H264/yuv420p/30fps, PTS từng frame tăng đều, duration/A–V lệch<=100ms, AAC48kHz, decode toàn tệp | Sai chặn success của bản xuất mới và lưu report lỗi; không thay file tốt trước đó. Đủ1080p không chứng minh nội dung đủ nét. |
| Âm thanh | Integrated−16LUFS±1, truepeak<=−1dBTP sau AAC; silent mode do creator chọn kiểm silence riêng | Không coi −inf/NaN là lời đọc đạt; A/V duration không chứng minh lip-sync. Mẫu giọng vẫn cần người nghe. |
| Cảnh báo nhẹ | Mọi frame trong ROI minh họa, ảnh phân tích160×160 xám: thay đổi sáng ngắn, gần lặp kéo dài trong cảnh yêu cầu chuyển động | Cảnh báo có timestamp, phương pháp/threshold/version. Phải xem/ack trước duyệt; không là benchmark học sâu hoặc chứng nhận nhạy sáng. |
| Độ nét tham khảo | Laplacian variance percentile thấp, delta pixel theo từng cảnh | Không đặt ngưỡng blur chung: line art/nền mềm có thể đúng ý đồ. Không chuyển thành điểm1–5. |
| Creator | Prompt, mượt, consistency, vật lý, kỹ thuật nhìn/nghe; caption/fact/tuổi/disclosure | Máy không tự chấm. Không có điểm trung bình cho phép bù critical. |

Policy `local-qc-2`: luma jump>=35/255 giữa frame liền kề và trở lại trong8mức xám; near-repeat MAE<=0,08, run>=0,5s khi `motion_required`. Scan reset ở từng scene; pha hold whiteboard bắt đầu theo `draw_fraction` (snapshot cũ0,65). `allow_static` mặc định cho phép giữ hình để đọc. ROI dùng hình học đúng layout: board theo vùng hình cũ; full_frame lấy phần giữa24–67% chiều cao, tránh title/caption. Không coi camera chuyển nhẹ, chuyển vật thể và optical flow là cùng một tín hiệu.

Đo nhịp trên audio thành phẩm bằng `silencedetect`−42dBFS, khoảng liên tục>=0,25s; JSON/UI có tổng giây, tỷ lệ và khoảng dài nhất. Từ0,8s tạo warning với timestamp/cảnh và yêu cầu nghe/ack; không tự cắt từ hoặc loại mọi khoảng nghỉ có chủ đích. Silent mode ghi not_applicable. Timeline30fps dùng cùng helper cho render/QC/ASR, tránh cộng một frame do container làm tròn microsecond. Video-only ghép với PCM48kHz theo số mẫu chính xác, loudnorm và AAC chỉ một lần cuối.

Các thông số nội bộ chưa hiệu chuẩn trên dataset người chấm; có thể có false positive và false negative. Report giữ tối đa20mốc hình/cảnh (20cảnh) cùng các khoảng im lặng; phiếu hỗ trợ ack500mốc và vẫn yêu cầu xem hết video. Không có warning không chứng minh không có lỗi; camera affine và PTS đều không tự chứng nhận cảm nhận mượt.

CRF18 có bitrate biến thiên: tranh tĩnh có thể có bitrate thấp mà vẫn rõ, vì vậy không ép một bitrate tối thiểu tùy ý hoặc coi bitrate cố định là chuẩn cho mọi cảnh. Kiểm playback, chữ/viền/vỡ khối ở kích thước thật. VMAF/PSNR/SSIM cần reference cùng nội dung/căn chỉnh để kiểm encode; FVD là đo phân phối trên tập video, không dùng một clip đơn để chứng nhận hấp dẫn, kiến thức hoặc vật lý.

## Rubric nghiệm thu 1–5

| Hạng | 1 — sai nghiêm trọng | 2 — lỗi rõ | 3 — cần sửa | 4 — đạt | 5 — đạt tốt trong trường hợp đã xem |
|---|---|---|---|---|---|
| Khớp kịch bản / prompt | Sai ý cốt lõi, hành động đảo ngược | Thiếu vật thể/chi tiết quan trọng, sai số lượng/màu | Đúng ý chính nhưng chi tiết cần chỉnh | Đủ yêu cầu, lỗi nhỏ không đổi ý | Yêu cầu vật thể, thuộc tính, hành động và bố cục được thể hiện rõ |
| Chuyển động mượt | Giật/nhảy làm không theo dõi được | Freeze/camera rung gây mất tập trung | Chuyển cảnh hoặc nhịp còn cần chỉnh | Chuyển động/hold có chủ ý, dễ theo dõi | Chuyển động rõ mục đích và nhịp kể nhất quán, không lỗi thấy được |
| Nhất quán thời gian | Đổi người/vật/trang phục phá câu chuyện | Méo hình, texture/nền nhấp nháy thấy rõ | Chi tiết thay đổi cần sửa | Chủ thể/nền ổn định, sai lệch nhỏ không ảnh hưởng | Silhouette, màu, vật thể và quan hệ không gian nhất quán suốt clip |
| Logic vật lý | Sai nhân quả/quy luật làm người xem hiểu sai | Xuyên vật thể, biến dạng cơ thể hoặc chuyển động vô lý | Minh họa chưa đủ rõ hoặc cần ghi giả định | Logic phù hợp phong cách, mô hình đơn giản được giải thích | Hành động/cơ chế hợp lý xuyên cảnh; giả định/tỷ lệ minh họa rõ và fact được đối chiếu |
| Kỹ thuật | Hỏng file/không đọc được/che mất nội dung | Blur/vỡ khối/chữ cắt làm không hiểu | Cần đổi nguồn hoặc dựng/encode lại | Đúng kích thước, rõ chữ/viền, playback tốt ở thiết bị kiểm | Hình/audio/caption sạch trong toàn trường hợp đã kiểm, kể cả chuyển cảnh và điện thoại |

Đồ họa cách điệu không bắt buộc có chuyển động như phim người thật, nhưng không được minh họa khoa học sai. Ví dụ: vapor thường vô hình; giọt nước/mũi tên/phóng đại phải được hiểu là sơ đồ, không biến thành chứng cứ mô phỏng. Trẻ em cần một ý mỗi cảnh, thời gian đọc phù hợp, không thêm flicker/giật gân chỉ để tăng dynamic degree.

## Phiếu QA/QC dùng thủ công

Điền: **người duyệt / ngày / video SHA256 hoặc tên và phiên bản / aspect / profile / thiết bị / model-workflow-seed / nguồn script-reference**. Xem đúng MP4 được hash, không chấm file đã thay hoặc ảnh poster đơn lẻ.

| Phân vùng | Pass signal | Lỗi cần tìm | Điểm1–5 | Critical? | Cảnh / giây | Bằng chứng và biện pháp |
|---|---|---|---|---|---|---|
| Prompt alignment | Đúng vật thể, màu, số lượng, hành động và ý chính | Thiếu chi tiết, sai bối cảnh, đảo hành động | ___ | ___ | ___ | ___ |
| Motion smoothness | Camera/vật thể trôi chảy; hold có mục đích | Frame skip, freeze không chủ định, giật | ___ | ___ | ___ | ___ |
| Temporal consistency | Chủ thể, trang phục, nền giữ continuity | Đổi áo/mặt, nhấp nháy texture, méo hình | ___ | ___ | ___ | ___ |
| Physical plausibility | Logic hợp phong cách và kiến thức | Xuyên vật, cơ thể dị dạng, sai cơ chế | ___ | ___ | ___ | ___ |
| Technical quality | Kích thước đúng, chữ nét, audio/playback tốt | Blur/răng cưa/vỡ khối/âm lượng lỗi | ___ | ___ | ___ | ___ |

- [ ] Đã xem hết video ở tốc độ thật; xem chậm/frame quanh lỗi nghi ngờ.
- [ ] Đã xem đầu/giữa/cuối mọi cảnh và đối chiếu reference; nhân vật lặp kiểm nhiều cảnh.
- [ ] Đã nghe audio trong MP4 nếu có lời; kiểm mất/lặp/sai từ, nhạc che giọng.
- [ ] Đã kiểm phụ đề so script/audio, dấu tiếng Việt,2dòng, crop/safe zones trên màn hình nhỏ.
- [ ] Đã đối chiếu fact, logic và nhóm tuổi; xác định audience/quyền tài nguyên trước đăng.
- [ ] Đã kiểm nguồn AI và cách ghi nhãn thích hợp; đã xem/ack mọi warning tự động.

**Decision rule:** kỹ thuật fail=>blocked/sửa xuất; bất kỳ critical hoặc điểm1–2=>reject, giữ artifact để truy lỗi và làm lại cảnh cần thiết; có3=>revise; thiếu điểm hoặc bước duyệt=>pending; chỉ toàn4–5, không critical, đủ bước duyệt và warning đã xem mới approved. Không trung bình hóa. `Approved` là tuyên bố của creator trên phạm vi đã kiểm, không bảo đảm mọi tuổi, viral, YouTube Kids hoặc pháp lý.

Với nhóm nhiều người, chấm độc lập một tập cố định trước, thảo luận bất đồng bằng timestamp và rubric; giữ cả các lần fail/retry, không chỉ clip đẹp nhất. Cá nhân có thể tự chấm nhưng phải ghi đúng một người chấm, không nhận có hội đồng/độ đồng thuận đo được. Tốc độ/RAM/VRAM/disk/chi phí để cột riêng, không cộng vào điểm chất lượng.

## Đối chiếu benchmark và minh bạch

| Nguồn | Áp dụng vào tool | Chưa thể kết luận |
|---|---|---|
| [VBench](https://vchitect.github.io/VBench-project/) | Tách subject/background consistency, flicker, motion, độ nét, style và semantic alignment; so các chiều độc lập | Chưa chạy learned metrics VBench/VBench2.0 hoặc có tổng điểm chính thức; pixel proxy không thay DINO/CLIP/flow/model của benchmark. Custom-input không hỗ trợ mặc định mọi16dimension; cần đúng chế độ/prompt suite. |
| [Survey CVPRW2026](https://openaccess.thecvf.com/content/CVPR2026W/VGBE/papers/Safavigerdini_Generative_AI_Video_Evaluation_Survey_of_Metrics_Benchmarks_and_Trustworthiness_CVPRW_2026_paper.pdf) | Phân biệt perceptual/semantic/temporal/physics/human/trust; tránh static-frame bias và chấm “đẹp” thay “đúng” | Không có một metric tổng đủ cho mọi nội dung; chưa dùng VLM judge hoặc chứng minh physics correctness. |
| [AIGCBench](https://www.benchcouncil.org/AIGCBench/) | So script/reference với output I2V, motion effects, temporal consistency và technical quality | Chưa chạy11metric/dataset chuẩn, không gán MSE/CLIP/FVD cho ảnh zoom hoặc tranh whiteboard khác reference. |
| [EU transparency code](https://digital-strategy.ec.europa.eu/en/policies/code-practice-ai-generated-content) | Giữ hash/provenance, export ID/origin metadata, creator disclosure trong phiếu và publish pack | Unsigned metadata có thể bị xóa, không là C2PA/robust watermark/AI detector. Phạm vi nghĩa vụ và nhãn phụ thuộc vai trò/cách dùng/pháp luật; tool không chứng nhận tuân thủ. |
| [Apiframe](https://apiframe.ai/blog/how-to-test-quality-of-ai-generated-video), [Turing](https://www.linkedin.com/posts/turingcom_in-our-latest-case-study-we-evaluated-1600-activity-7444432744677478400-9AMe) | Tập test cố định, scoring từng yếu tố, ghi timestamp và tách alignment/realism/visual quality | Nội dung công nghiệp/case study, không phải chuẩn pháp lý hoặc số đo của dự án; không lấy kết quả marketing upstream làm kết quả local. |

VBench và AIGCBench code tại commit đã kiểm đều Apache2.0; runtime/checkpoints/datasets/third-party components có điều kiện riêng. Hiện không cài benchmark hoặc tải weights; không phát sinh phí API. Khi cần bật, dùng venv riêng và pin đúng commit, kiểm từng checkpoint/license/hardware, chạy cùng input/aspect/seed, ghi mọi failure và mẫu người chấm. Không đổi app runtime sang CUDA/torch chỉ để có tên benchmark trong report.

EU page được đọc ngày2026-10-30 mô tả code tự nguyện đã được Commission/AI Board xác nhận là công cụ hỗ trợ; nghĩa vụ Article50 áp dụng từ2026-08-02, khác việc tham gia code. Không tự suy dùng cá nhân ở Việt Nam có cùng nghĩa vụ với mọi provider/deployer EU. Tool lưu nguồn AI đã biết và khai báo creator, không nhận dạng deepfake, tự chọn nhãn nền tảng hoặc ký provenance. Chi tiết nguồn/commit/hash ở [source-review](source-review.md) và [source-snapshot](source-snapshot.json).

## Lệnh kiểm dành cho người phát triển

Renderer chạy QC tự động trước success. Muốn đọc lại video đã có, không sửa media:

```bash
uv run --project backend python scripts/check_video_quality.py --video .data/review/review-portrait.mp4 --snapshot .data/review/report-portrait.json --output-dir .data/quality-audit/portrait
```

CLI cần snapshot thật để biết scene boundaries/aspect/options, không đoán từ video. Báo cáo JSON và CSV nằm ngoài Git. File cũ chưa có report trong database phải xuất lại để có phiếu UI gắn job; không giả tự duyệt file cũ. Thay file/hash hoặc phiếu cập nhật ở tab khác gây409; tải lại phiếu và đối chiếu đúng bản trước lưu. Giữ video và nguồn cũ khi sửa, không tự chuyển paid API hoặc gen vô hạn để tìm một clip đẹp.
