---
status: partial
slug: whiteboard-video-tool
updated: 2026-10-29
---

# Handover — whiteboard-video-tool

## Kết quả

Đã bắt đầu dev và giao M1 chạy thật: studio tiếng Việt, hồ sơ tuổi, nhập lời thoại/ảnh/clip/giọng, sửa cảnh, chọn16:9/9:16, dựng preview/MP41080p, metadata và link upload chính thức. Prototype Blender gốc xuất clip3D thực có thể nhập lại app. Toàn sản phẩm chưa hoàn thành AI/OAuth/SRT/quality gates các mốc sau, giữ specapproved và handoverpartial.

## Đối chiếu đặc tả

- File: specs/whiteboard-video-tool.md.
- Khớp: lõi M1 và bổ sung aspect/motion/manual hub, không giả model hay public upload.
- Lệch đã được duyệt: chỉ thị mới nâng16:9/motion vào M1 đã ghi trước thay đổi code.
- Lệch chưa duyệt: không về scope M1; vẫn chưa đủ các mục toàn sản phẩm, xem Chưa làm.

## Đã làm

- React/TS/Vite UI responsive390px/desktop, bốn bước và profile riêng; source scaling warning và guides không xuất video.
- FastAPI, SQLite revision, asset validation/size/duration/type, local Host/Origin guard, streaming body limit.
- Whiteboard contour/hand/color, motionảnh/clip, native1080 haiaspect/30fps/H264CRF18, audioimport/resample/pad và captions phân đoạn ước lượng.
- Queue worker durable, one-worker lock, idempotency/concurrent claim, cancel encoder, interrupted restart và snapshot bất biến; full decode trước success.
- Tải MP4/JSON snapshot, audience/rights checklist; linkYouTube/TikTok/Facebook chỉmanual, không giảOAuthconnected.
- Blender CPU script mesh/material/animation gốc và research model/engine/video link; dependency locks/fontlicenses/README/docs/benchmark.
- Spec đã push trướcdev; nhánhfeat/short-video-studio, commitDocs9d4e33c và7925abc; code commit là commit chứa handover này.

## Chưa làm

- M2 model/script/image/video generation tự động và Blender template editor; mới có compositor và CLIprototype.
- M3 giọng VieNeu thật, nghe 20 câu, alignment thật, naturalness/quality review 10 ảnh và xuất LUFS/truepeak đo đầy đủ. Tonefixture không phải TTS.
- M4 OAuth/directupload. Chưa có các clientcredentials/appreview/accountpermissions; liveupload chưa chạy, không có bài đăng nào được tạo.
- SRT/import/timing, coverpack,180sShorts,1:1, packagingWindows/macOS và device/platformQA; chưa tuyên bố phát hành.

## Cách chạy

- npm --prefix apps/web ci
- uv sync --project backend --frozen --group dev
- npm --prefix apps/web run build
- bash scripts/dev.sh
- Dùng app local cổng8765; task không tạo preview link công khai. Script mặc địnhdata.data/ đã ignore.
- Phần kiểu videoDrive: mode motion nhậnMP4/ảnh; BlenderCLI tạo clip mẫu. Đây chưa là full tự động sinhvideo96s nhưreference.

## Test sẵn có

- Trước code: không có test/source/package, không gọi0test làpass.
- Sau code:32pytest,5Vitest,4Playwright qua; khôngskip trong lần chạy này. TestClient/httpx có1cảnh báo upstreamdeprecated, khôngfail và không tắttest.

## Test đã chạy

- LG-01/02/03/05/07,SEC-03/05/06/10/15: pytest backend/tests32pass, gồm stale audio, revision conflict, upload MIME giả, body chunked limit/path/symlink, source/host guard, missing asset vàduration.
- RW-01/03,JOB-01: concurrent double-submit chỉ1job; runningcancel dọn encoder/tmp vàgiữ file cũ; restartinterrupted; snapshotđúng.
- ASPECT-01/OUT-01/MOTION-01: bốn ca render preview/finalcả2aspect, H26430fps/full decode; MP4 nhập vànarration decode PCM nonzero. Smoke3cảnhfull1080 cả2aspect3,021333s, AACtone fixture.
- UI/UX/SEC-02/UPLOAD-01:4E2EChromium, desktop 1366/mobile 390, import→render→downloadMP4/metadata→reloadrestore, HTMLinput hiệndạngtext, keyboardfocus, linkwhitelist vàaxeWCAG2A/AAlabels/contrasthai màn. Lỗi contrast tìm được đã sửa, lượt cuối qua.
- FREE-01/QUALITY-01:5Vitest readiness/silent/stale/missing/time/sourcecontain; đườngimport/renderkhôngkey/APIfee/watermark.
- THREE-01(prototype): pytestCPUBlender320×180/2frame pass; manual12frame640×360/12fps clipthật. Khônggọi làfull3Dqualitygate.
- RW-07 benchmark:20cảnh600framepreview360×640,8,493s≈70,64fps, PythonpeakRSS114404KiB; full decode 20,021333s. KhôngápFPSnàycho1080/AI.
- Cổngchấtlượngcode:ruffcheck/formatcheck,mypy9sourcefiles,tsc,Vitebuild,Prettiercheckqua. npm runtimeaudit0vulnerability; pip-auditkhông có advisory được biết, package nội bộ không có PyPIskip auditdatabase.
- Launcher: đã chạy API cổng8767 với Vite5173, GET health và POST tạo project qua proxy thành công; Ctrl+C dọn process của lượt test.
- Frozeninstall:uvsync--frozen xácminh57packages; npmci vàaudit lại đượcchạy với lockfile.

## Test không chạy

- AI-01/02/03,VIDEOAI-01,WB-04: adapter/model chưa tích hợp, không có weights/GPU/license/voice samples thật; không dùngmockđểthaylive.
- OAUTH-01/SOCIAL-01/SOCIAL-LIVE-01,KIDS-01/OUT-02: cácmốc chưa triển khai, thiếuapp/credentials đểlive; no OAuth/directpublishclaim.
- Chưa kiểm nativeWindows/macOS, khônghứa mọiOS/platform.

## Quyết định đã ghi vào nhớ dài hạn

D-001 vàD-002: profile/portrait/qualityfree, haidiệnaspect vàreference3D/motion/manualhub.

## Rủi ro và nợ

M1 làlát cắt dùng được, không full sản phẩm. Scene motionpanảnhkhôngphải3D, modelvideochưa chạy; CLIBlenderprototype samples thấp khôngchứngminh qualityphát hành. Captionước lượngchưa căn từng từ. Audio loudnorm/limitercó nhưngchưa đo LUFS/true peak hoặc nghe final bằng giọng người. Nguồn thấp nét không sinh chi tiết mới. UploadlinkkhácOAuth; chính sách/Kids/rights cần creator review. Không biết 3D engine của tác giả chỉ từ file. Khôngcóuser secrettrongrepo.

## File đã đụng

specs/,AGENTS.md,AGENT-CODING-STANDARD.md,.agent/,.gitignore,.env.example,README.md,backend/,apps/web/,assets/fonts/,assets/examples/,scripts/,docs/. Khôngcommitruntime.data,node_modules,venv,video/userassets hoặcvideoDrive.

## Agent sau đọc gì

1. specs/whiteboard-video-tool.md và AGENTS.md.
2. .agent/memory/long-term/PROJECT.md,ARCHITECTURE.md,DECISIONS.md,CONVENTIONS.md.
3. .agent/handover/LATEST.md vàdocs/development-plan.md.
4. TASKS.md/SESSION.md để tiếp tục các mốc chưa xong, không xin lại quyền code/push đã cấp.
