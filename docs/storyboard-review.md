# Storyboard mẫu: Áo khô, nước đã đi đâu?

## Mục tiêu và nhịp kể

Mẫu gốc dành cho profile **cả nhà6+**, người lớn đồng hành khi giải thích khái niệm phân tử. Không dùng cùng tốc độ này làm chuẩn cho trẻ3–4tuổi. Người xem nhận ra nước không mất đi, phân biệt bay hơi với sôi, hiểu vai trò của nhiệt độ, gió, độ ẩm và diện tích tiếp xúc. Đây là minh họa giáo dục, chưa có nghiệm thu phù hợp tuổi từ creator.

Lời đọc thực quyết định thời lượng: **12cảnh/1160frame/38,667s ở30fps**, mỗi cảnh2,633–4,167s. Audio giữ60ms đầu/100ms cuối quanh vùng hoạt động, chỉ bỏ silence ở hai đầu với provenance; không xóa khoảng nghỉ trong câu. Thêm0,10s sau giọng và làm tròn lên lưới30fps. Bản app cho chọn khớp giọng giữ trọn file và thêm0,12s; không tự trim tệp người dùng.

Không giữ mỗi ảnh4s để đủ tổng thời lượng. Hòa hình visual5frame ở đầu cảnh tiếp, không chồng chữ hoặc giọng. Cảnh cắt/giữ hình vẫn có thể phù hợp mục đích giải thích; không thêm rung, nhấp nháy hoặc hiệu ứng vô nghĩa để qua metric.

## Diễn biến từng cảnh

Mốc dưới đây là timeline video thực; container AAC có thể dài thêm vài chụcms. Narration khớp `scripts/science_story.py` và kịch bản mẫu trong UI. Mọi lời/chi tiết khoa học vẫn cần creator kiểm trước đăng.

| Cảnh / mốc giây | Lời đọc nguyên văn | Đầu → giữa → cuối và mục đích hình |
|---|---|---|
|1 ·0,000–3,400 · hook|Áo vừa giặt còn ướt. Một lúc sau lại khô. Nước đã đi đâu?|Chiếc áo xanh lớn, thấy giọt nước/đường may/nếp vải và kẹp áo → camera tiến nhẹ bằng tọa độ lẻ, mặt trời quay chậm → nối sang vùng sợi vải. Đặt câu hỏi trước khi gọi tên hiện tượng; không nói áo khô tức thì.|
|2 ·3,400–6,333 · context|Nước thấm giữa các sợi vải. Ta cùng phóng to để xem nhé!|Khung phóng đại tròn → vẽ9sợi dọc và9sợi ngang theo thứ tự có độ trễ, đường cong tạo cảm giác dệt → các chấm nước nằm trong khe, nhãn “Nước giữa các sợi vải”. Không vẽ chấm ngoài vòng như vật thể bay trong phòng.|
|3 ·6,333–9,033 · explain|Nước gồm những phần tử rất nhỏ, gọi là các phân tử.|Khung chất lỏng và bề mặt rõ → các chấm rung nhẹ liên tục trong nước → giữ nhãn “Phóng đại minh họa”, vùng “Không khí” bên trên. Không dùng chấm như ảnh chụp phân tử hoặc cấu trúc hóa học chính xác.|
|4 ·9,033–11,667 · explain|Ở bề mặt, một số phân tử nước thoát vào không khí.|Giữ cùng khung nước → một số chấm rời bề mặt theo quỹ đạo cong, độ trong suốt tăng/giảm mềm → mũi tên nối vùng nước với vùng không khí. Không làm toàn bộ nước biến mất hoặc dựng mây khói.|
|5 ·11,667–14,633 · explain|Nước lỏng chuyển thành hơi nước. Quá trình này gọi là bay hơi.|Tiếp tục mô hình cùng màu/kích thước → chuyển động thoát khỏi bề mặt củng cố cơ chế → phụ đề gọi tên “bay hơi”. Câu dài chia trang cân bằng, tránh một trang chỉ còn “hơi.”.|
|6 ·14,633–17,533 · context|Hơi nước thường vô hình. Những chấm xanh chỉ là hình minh họa.|Trở lại áo → các chấm xanh sơ đồ mờ dần → áo/không gian vẫn rõ khi chấm đã hết. Title nêu hơi thường vô hình; bản dọc bỏ nhãn lặp đè kẹp áo. Giữ điều này để trẻ không hiểu hơi nước là hạt xanh nhìn thấy.|
|7 ·17,533–20,700 · example|Bay hơi không cần nước sôi. Áo trong nhà vẫn có thể khô.|Áo và ký hiệu cốc nước thường → nhìn thấy bề mặt, không bọt/khói/lửa → nối sang điều kiện làm khô. Cốc là ký hiệu2D, không phải phép đo nhiệt độ; không hướng dẫn trẻ đun nước.|
|8 ·20,700–24,200 · explain|Nơi ấm thường giúp nước bay hơi nhanh hơn. Nhưng còn một yếu tố nữa!|Cùng áo/vật liệu → nền ánh sáng ấm và mặt trời quay nhẹ → câu nối dẫn tới gió. Dùng “thường”, tránh khẳng định chỉ cần nóng là áo luôn khô nhanh. Không suy ký hiệu mặt trời thành mô phỏng năng lượng.|
|9 ·24,200–27,467 · explain|Gió đưa không khí ẩm quanh áo đi, giúp nước tiếp tục bay hơi.|Giữ áo làm mốc →4luồng khí cong với mũi tên chạy cùng hướng, đường khí biến đổi trơn theo thời gian → nhãn “Không khí được trao đổi”. Thể hiện đổi lớp khí quanh vải, không nói gió hút nước hoặc làm nước biến mất.|
|10 ·27,467–30,800 · explain|Không khí quá ẩm thường làm áo lâu khô hơn, ngay cả khi trời nóng.|Hai vùng ít ẩm/nhiều ẩm cùng khung → mật độ12/40chấm tương phản, dao động nhẹ → giữ nhãn “Mật độ chấm: minh họa”. Không đưa các số chấm thành phần trăm độ ẩm hoặc dữ liệu thực nghiệm.|
|11 ·30,800–34,500 · example|Trải áo rộng, treo nơi thoáng, để nhiều bề mặt tiếp xúc với không khí.|Vải gấp và áo trải đặt cạnh nhau → mũi tên hướng từ trạng thái gấp tới trải → nhãn rõ từng phía. Đây là cảnh so sánh có ít chuyển động; QC giữ warning để creator đánh giá hold/nhịp, không giả cloth-unfolding simulation.|
|12 ·34,500–38,667 · payoff|Nước không biến mất: nó chuyển vào không khí. Bạn thử quan sát chiếc khăn ướt nhé!|Trở về áo khô cùng silhouette/màu xanh → gió tiếp tục, liên hệ lời giải với hook → kết ngay sau câu mời quan sát khăn. Không yêu cầu cung cấp thông tin cá nhân, không CTA giật gân hoặc giữ màn hình câm vài giây.|

## Thiết kế hình và phụ đề

- Canvas native1080×1920 hoặc1920×1080; bố cục lại theo aspect. Dọc ưu tiên áo lớn hoặc sơ đồ giữa màn hình; ngang áo bên trái, sơ đồ/nhãn bên phải. Không crop từ bản ngang để giả bản dọc, không kéo méo.
- Áo là still3D procedural gốc Cycles128samples,1600×1400RGBA nền trong suốt. Giữ đường may, cổ/túi/nếp vải; hai trạng thái dùng cùng hình học/vật liệu. Không dùng stock hoặc asset của video tham chiếu/Tongjiang.
- Clip nguồn gồm gradient nền/lớp cảnh, cutout áo, đường dệt, chấm, quỹ đạo/mũi tên và nhãn. Vẽ tại2×kích thước đích rồi Lanczos; camera affine float sau antialias. Clip H264/CRF12/30fps, app overlay và encode CRF18 ở native1080p. Chữ Noto được vẽ ở độ phân giải đích; không nhờ diffusion viết chữ/số.
- Full_frame phủ cả canvas. Chủ thể không buộc lấp100% diện tích: chừa vùng đọc sơ đồ/title/caption và khoảng thở có mục đích. Nguồn khác tỷ lệ chọn cover/focal để tránh mất chủ thể, hoặc contain khi phải giữ toàn hình; UI cảnh báo crop/upscale.
- Title và caption là lớp riêng, giữ rõ khi hòa hình. Caption card/contrast/accent luân phiên có chủ đích, tối đa2dòng/trang, cân lượng từ giữa trang để tránh đuôi1–2từ. Nhấn literal các cụm như “sợi vải”, “vô hình”, “không biến mất”; không fake karaoke hoặc forced alignment.
- Whiteboard của tool có silhouette-first, nối contour theo endpoint gần và pen-up travel, draw_fraction có thể chỉnh. Đây vẫn là contour tracer; mẫu mới dùng thêm clip minh họa theo lớp để có chuyển động mô tả cơ chế. Chưa có semantic vector artist hoặc cloth/fluid simulator.

## Kiểm chứng và nguồn

Nội dung/lời/mesh/đồ họa là bản gốc của dự án. Preset Hải Đăng và cùng weights VieNeu/codec đã pin dùng local; font/ASR/license và giới hạn SDK ở [QA review](qa-review.md). TTS từ chối waveform rỗng/nonfinite/clipping, thử tối đa3seed có ghi log; không sửa gain để che clipping. Không gọi API trả phí hoặc tự đổi model.

Nguồn khoa học để creator đối chiếu trước nghiệm thu: [USGS Water Science School: Evaporation and the Water Cycle](https://www.usgs.gov/special-topics/water-science-school/science/evaporation-and-water-cycle). Lần truy cập tự động trong phiên bị timeout, không ghi là đã đọc/pin trang này. Các chấm/tỷ lệ/quỹ đạo và mật độ trong mẫu đều là sơ đồ, không lấy số liệu từ trang hoặc bài học bên ngoài. Phiếu kiểm fact/tuổi còn pending.

Kiểm file cuối bằng decode/PTS/LUFS/truepeak, đo silence, ASR theo duration từng cảnh thực và contact sheets đầu/giữa/cuối. Báo cáo và cách tái tạo ở [QA](qa-review.md); manual smoothness/physics/age vẫn cần xem/nghe ở tốc độ thật. Không dùng kết quả kỹ thuật thay phản hồi cảm nhận của người xem.
