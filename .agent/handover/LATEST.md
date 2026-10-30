---
status: partial
slug: whiteboard-video-tool
updated: 2026-10-30
---

# Handover — whiteboard-video-tool

## Kết quả

Sửa nhịp/layout/renderer theo feedback và xuất mẫu12cảnh có lời,1080p hai aspect.205test qua. Silence17,361→3,173s, longest2,536→0,361s. Technicalpass, creatorreview còn pending:6motion warnings/aspect và3ASRmismatch. Toàn spec vẫn approved/partial vì M2live/M3UI/alignment/M4OAuth còn backlog.

## Đối chiếu đặc tả

- specs/whiteboard-video-tool.md; amendment69ad80a đã push trước code, caption page balancing bổ sung trước sửa khi thấy lỗi trên sample.
- Khớp fullframe/fit/focal/legacy/float/pen-up/frameclock/dissolve/PCM/singleAAC/fit-audio/story/nativeclips/pacingQC/test.
- Không lệch đã/chưa duyệt. Giữ quyền code/commit/push trên feat/short-video-studio; không đổi/publish cloud hoặc mạng xã hội.

## Đã làm

- layout.py dùng chung geometry/affine với QC; newScene full_frame/cover/dissolve, legacy board/contain/cut/reveal0,65. API giữ fields cũ thiếu theo sceneID; editor fit/focal/transition/reveal và warning crop/upscale theo canvas thật.
- Float affine ảnh, floor sourceclip clock theo outputframe, pen-up travel không nối nét giả. Visual dissolve5frame rồi title/caption riêng; caption dài cân toàn cue để bỏ trang cuối1–2từ.
- Video-only per scene; PCM48kHz/sample-exact theo frame rồi normalize/AAC một lần cuối. fit-audio revision/all fresh audio/60s, giữ trọn file+0,12s; import pause0,12 thay0,35.
- timing.py frame grid chịu microsecond rounding, scene timeline và silence parser thuần stdlib cho renderer/QC/isolated verifier. Policy local-qc-2: ROI đúng layout, hold theo draw_fraction, silence tổng/ratio/longest, warning>=0,8s; QualityPanel hiển thị nhịp, ack500findings, creator rubric/hash/CAS giữ nguyên.
- Planner yêu cầu đầu/giữa/cuối và cơ chế/hành động rõ hơn; UI sample12cảnh. science_story.py/create_story_video.py dựng native motion2×SSAA với áo Blender RGBA gốc, nhập app/render/QC thật; docs/storyboard-review.md ghi lời/timing/action/assumptions.
- TTS CLI bounded3seed retry khi clipping, strict empty/nonfinite/peakguard; trim outer silence có hash/margins, không cắt internal pauses. Đây chưa là TTS UI, physics simulation hoặc AI video diffusion.
- README/QA/quality-standard/development/skill/D-007/memory cập nhật; no dependencies/lock/media/weights trong Git. .data/review và .data/quality-upgrade giữ nguyên.

## Chưa làm

- Creator fullplayback/listening/manual/age và thiết bị thật; cảnh so sánh11 rất ít motion cần xem lại. Không suy cảm nhận từ205test/stills/ASR.
- Learned VBench/AIGCBench/runtime/checkpoints/dataset/GPU/calibration not_run; không C2PA/legalcertificate.
- M2 models live/ref/batch/3Deditor; M3TTSUI/packaging20câu/alignment/SRT; M4OAuth/live private-draft upload/cover/180s/packaging còn backlog.

## Cách chạy

- README chạy app; chọn fullframe/fit/focal, nhập đủ giọng rồi Khớp nhịp theo giọng đã nhập; xem QC sau xuất.
- APP_DATA_DIR=.data/story-upgrade/studio-portrait bash scripts/dev.sh (hoặc studio-landscape), chọn project mới nhất/Xuất. MP4/report/QC/CSV/verification/art/provenance/SQLite ở .data/story-upgrade ngoài Git. Tái tạo ở docs/qa-review.md; lời/diễn biến ở docs/storyboard-review.md.

## Test sẵn có

- Trước code156pytest/9Vitest/11Playwright=176pass; clean,1Starlette/httpx deprecation.
- Sau code182pytest/10Vitest/13Playwright=205pass, khôngskip. ASR/humanreview không tính vào testpass.

## Test đã chạy

- Pytest182pass/36,66s:cover/focal/4mép/title/subpixel/penlift/dissolve/clipclock/PCM/framegrid/timeline/fit/stale/revision/legacy/invalidinput; real long-silence warning và intentional silent not_applicable, QC hold theo draw_fraction. Caption6newcases giữ đủ chữ/2dòng/trangcuối. M1/M2/QC regressions qua.
- Vitest10/TypeScript/build/Prettier qua; Ruff/format/mypy15module và diffcheck qua. Không thay lock/dependencies.
- E2E13pass/47,4s cuối:1366/390/axe/realFFmpeg/API,2newlayout/focal/reveal/fit/reload cases;3AI cases mock như trước. Lượt đầu buildUI cũ thiếu controls; lượt sau đo nhầm border2px. Build lại/đo clientWidthHeight, giữ assertion phủ kín.
- Hai MP4 H264/yuv420p/30fps/1160frame/AAC48kHz,38,666667s video/38,7s container, decode/CFR/PTS/audio qua. Cả hai−16,94LUFS/−1,53dBTP, AAC packet hashes giống nhau. Dọc4188150byte SHAebd70986f9476b8d70fefd3ab54275351a8f1e5b92b166faafbcdbcfeedf12e4; ngang4282634byte SHAf6b601b7a76e11257be4eb2804d50b872e4726ef4ed134630ad87db4babf009f.
- Silence−42dB/d>=0,25s:3,173459s/11intervals/longest0,361459s/0long-silencewarnings.6near-repeat warnings/aspect scene1/6/7/8/10/11 giữ nguyên; manual_review null/pending_review.
- ASR MP4dọc theo timeline thực9/12exactnormalizedtokens;scene3 phần/phân tử0,917;scene5 truyền/chuyển0,923;scene6 nhưng/những0,923. Cần nghe đối chiếu, không kết luận chắc TTS/ASR sai hoặc đổi script để làm khớp.
- Đã xem36frame đầu/giữa/cuối mỗi aspect và nativeart; sửa label đè kẹp áo/trang captionđuôi. Không nhận đã nghe hoặc xem fullplayback tốc độ thật.

## Test không chạy

- Human listening/playback/scoring/age/native devices chưa có người duyệt; GPU/livebench/OAuth như backlog, không fakepass.
- Audit dependencies không lặp vì lock không đổi; audit baseline0knownadvisory ở archive, không nhận đó là audit mới.
- USGS fact reference timeout; doc ghi chưa đọc/pin, không tự nhận factchecked.

## Quyết định đã ghi vào nhớ dài hạn

D-007:nhịp theo audio/fullframe/legacy/float/PCM và QCsilence sau feedback; không game proxies/ASR. PROJECT/ARCHITECTURE cập nhật; TASKS giữ backlog, SESSION trống.

## Rủi ro và nợ

- Proxies falsepositive/negative; motion nhẹ không tự là giật hoặc đạt. Chưa semanticvectorartist/clothfluidphysics; safezones cần device/platform QA.
- TTS3câu cần người nghe; CLI Gradio metadata vẫn hạn chế, chưa installerM3. Retry không chứng nhận phát âm.
- Unsigned metadata có thể strip; disclosure/audience/license cần creator. Không hứa viral/Kids/legal; cá nhân kiếm tiền không miễnNC, sample không dùng Tongjiang assets.

## File đã đụng

Backend domain/api/media/planning/render/quality/layout/timing và tests composition/quality/typography; web main/domain/domain.test/style/QualityPanel/e2estudio; Blender/TTS generate/verify/science_story/create_story_video; spec/README/docs QA/storyboard/rubric/development/skill/memory/handover. Media/models/data ignored.

## Agent sau đọc gì

1. AGENTS.md, spec approved, handover này.
2. docs/storyboard-review.md, qa-review.md và video-quality-standard.md cho artifact/timestamp/giới hạn thật.
3. PROJECT/ARCHITECTURE/DECISIONS D-007/TASKS; skill video-quality-review khi sửa renderer/provider.
4. Không áp lại/publish cloud hoặc đăng công khai; quyền Git push trên branch hiện tại đã có.
