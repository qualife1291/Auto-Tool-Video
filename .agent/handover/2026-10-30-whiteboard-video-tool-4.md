---
status: partial
slug: whiteboard-video-tool
updated: 2026-10-30
---

# Handover — whiteboard-video-tool

## Kết quả

Đã triển khai QC sau gen và phiếu nghiệm thu1–5 theo nguồn người dùng, sửa lỗi âm lượng cảnh ngắn, kiểm lại hai mẫu và dựng lại với cùng input.176test qua. Toàn spec vẫn partial (M2 model live/M3 TTS UI/alignment/M4 OAuth chưa hoàn tất), không đổi status approved. Mẫu chờ creator nghe/xem; không tự chấm điểm manual, physics hoặc learned benchmark.

## Đối chiếu đặc tả

- specs/whiteboard-video-tool.md; amendment QC commit4ccba21 đã push trước code.
- Khớp: QC tự động, manual rubric/no-average-critical/hash/CAS, source/provenance/disclosure, CSV/JSON/UI, CLI audit và test/regression thật.
- Lệch đã được duyệt: không; không có lệch chưa duyệt. Giữ quyền code/push, không đổi/publish môi trường hoặc đăng video công khai.

## Đã làm

- quality.py: metadata/PTS/CFR/decode/audio gates; cancellation/process/output bounds; ROI scan mọi frame, flash/near-repeat có timestamp, motion intent/scene cuts/whiteboard hold; sharpness chỉ mô tả. Không thêm dependencies/weights/API trả phí.
- Renderer chạy QC trước success, report lỗi vẫn nằm ở job; file/project tốt trước giữ nguyên. Trim/pad hữu hạn trước loudnorm sửa fixture1s−9,6LUFS; silent không qua loudnorm để tránh NaN/AAC failure.
- Report/SHA/provenance/input hashes/known provider/snapshot; metadata MP4 export ID/origin/signature none. Không C2PA/robust watermark/AI detector/legal compliance certification.
- API project/export quality JSON/CSV/review; review_revision CAS và video SHA thực, cross-project/kind/hash/timestamp/score guards. Publish pack kèm gate/disclosure từ đúng export snapshot; download/hub vẫn để creator review/đăng thủ công.
- QualityPanel: kỹ thuật/warnings/seek/đối chiếu script-hình nguồn,5hạng1–5, critical override, playback/audio/caption/fact-age/disclosure/ack steps. Không prefill5 hoặc tự approved. Saved_at chỉ là metadata, lọc khỏi payload lần lưu sau.
- Scene.motion_expectation defaultallow_static tương thích project cũ; editor cho motion_required. Old export thiếu QC hiển thị unavailable.
- scripts/check_video_quality.py audit media read-only, JSON/CSV; docs/video-quality-standard.md có rubric và sheet dùng không cần code. Source-review/snapshot/license/development/QA/skill được cập nhật.
- Nguồn: VBench pinnedfd18b3d.../AIGCBenchcc230c84... Apache2.0 code, PDF CVPRW2026 và EU code hiện tại, Apiframe/Turing. Chỉ đọc/tóm tắt, không vendor/cài benchmark; learned metrics not_run.

## Chưa làm

- Learned VBench/VBench2/AIGCBench checkpoints/datasets/runtime và GPU benchmark; chưa có điểm benchmark chính thức. Các pixel proxies chưa được hiệu chuẩn trên dataset người chấm.
- Human full-playback/listening, physical/semantic/age approval và thiết bị thật. Machine checks/ASR không thay người duyệt.
- M2 model live/ref/batch/3D editor, M3 TTS UI/packaging/20câu/alignment/SRT, M4 OAuth/token/upload private-draft có quyền, cover/180s/packaging còn backlog như trước.

## Cách chạy

- README.md chạy app; sau xuất xem Kiểm định sau khi dựng và tải JSON/CSV. Rubric/lệnh CLI ở docs/video-quality-standard.md.
- .data/quality-upgrade có MP4/report/QC/CSV/verification và SQLite project, ngoài Git. APP_DATA_DIR=.data/quality-upgrade/studio-portrait bash scripts/dev.sh để mở mẫu (hoặc landscape). Bản cũ .data/review giữ nguyên.

## Test sẵn có

- Trước code:114pytest/8Vitest/9Playwright=131pass,1upstream deprecation; working tree clean.
- Sau code:156pytest/9Vitest/11Playwright=176pass, khôngskip. Benchmark và nghe tay không được tính vào test pass.

## Test đã chạy

- pytest156pass/17,62s:9technical negative gates, nonfinite/silent, flash/freeze/intent/hold/cut, critical1–2/3/4–5 và thiếu review; real export/hash/CAS/restart/cross-project/tamper/strictscore/CSVformula/oldjobs/publish snapshot. QC fail giữ file cũ, cancel dọn childprocess, output lớn reject. RegressionM1/M2/typography qua.
- npm check:TypeScript/9Vitest qua (thêm hồi quy saved_at). Vitebuild/Prettier qua; Ruff/format/mypy13module qua.
- Playwright11pass/35,6s:2newQC cases dùng real frozenMP4/worker/API ở1366/390, seek/rejectcritical/ack/approved/reload/CSV/plaintext/axe;9regression qua.3AI cases vẫn mock contract.
- E2E từng fail vì silent loudnorm, selector label select và review saved_at422; đã sửa nguyên nhân và giữ assertion, full suite cuối qua. Không tắt check/assertion/warning để pass.
- npm runtime audit/pip-audit backend0known advisory; package nội bộ không được external DB audit.1Starlette/httpx deprecation còn upstream.
- Hai MP4 cũ audit policy mới technicalpass/0warning; hai MP4 dựng lại32,021333s, H264/yuv420p30fps/AAC48kHz/full decode/PTS/audio qua,−15,69LUFS/−1,43dBTP; ASR dọc8/8cue khớp chuẩn hóa. QA/report/hash tại docs/qa-review.md và runtime files.
- Xem contact sheets24frame/aspect bản mới, cùng art inputs đã kiểm native đợt trước; creator playback/listening chưa có. Manual_review=null, gate pending_review đúng sự thật.

## Test không chạy

- VBench/AIGCBench/VLM/physics learned evaluations: chưa cài runtime/checkpoint/dataset/hardware phù hợp; không auto tải để có tên benchmark.
- Human scoring/listening/full playback/5profile×style×thiết bị thật; chưa có người duyệt.
- M2 live models/OAuth/social live upload/nativeWindows-macOS như backlog; không dựng mock thành thành công thật.

## Quyết định đã ghi vào nhớ dài hạn

D-006: tách hard technical gates, proxies và creator rubric; learned metrics not_run, unsigned provenance không chứng nhận EU. PROJECT/ARCHITECTURE cập nhật dataflow QC/review.

## Rủi ro và nợ

- Heuristic có false positives/negatives; static không tự kém chất lượng, motion mạnh không tự tốt. Require creator ack/review, không claim an toàn nhạy sáng hoặc đúng khoa học tự động.
- Metadata/sidecar unsigned có thể bị strip/tamper ngoài tool; khai báo nhập ngoài chưa xác minh, creator chịu trách nhiệm xác nhận/nhãn/quyền trước đăng. Không hứa legal compliance/Kids/viral.
- TTS review CLI packaging Gradio metadata còn hạn chế từ trước; không installer M3, không model weights/video/private data trong Git.

## File đã đụng

backend quality/domain/render/api và tests quality/studio; frontend QualityPanel/test/main/domain/style/e2equality; scripts/check_video_quality.py; spec/README/docs QA/rubric/source snapshot/review/license/development; skill local và memory/handover. No dependency lock changes/media in Git.

## Agent sau đọc gì

1. AGENTS.md, spec đãapproved, handover này.
2. docs/video-quality-standard.md và qa-review.md; source-review/snapshot cho bằng chứng nguồn.
3. PROJECT/ARCHITECTURE/DECISIONS vàTASKS; tiếp backlog theo quyền code/push đã có.
4. Skill video-quality-review khi đổi renderer/provider; không publish cấu hình cloud hoặc video công khai.
