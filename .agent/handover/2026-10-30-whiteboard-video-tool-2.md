---
status: partial
slug: whiteboard-video-tool
updated: 2026-10-30
---

# Handover — whiteboard-video-tool

## Kết quả

Đã hoàn thành lượt kiểm thử hiện trạng và tạo video review theo yêu cầu mới: 103 test qua, hai MP4 thật32s/1080p có giọng Việt Hải Đăng, tranh gốc và captions; đã xem still hai aspect, kiểm full decode/âm lượng và ASR. Đã sửa lỗi phát hiện và hoàn thiện code M2 đang dở ở mức adapter/contract. Toàn sản phẩm vẫn partial: chưa live Comfy/Qwen, chưa UI TTS/alignment/3D editor hoặc OAuth uploads. Spec giữ approved; không claim mọi model hoặc chất lượng cảm nhận đã duyệt.

## Đối chiếu đặc tả

- File: specs/whiteboard-video-tool.md, đã bổ sung hợp đồng QA và script review trước code; spec commit c37a50d đã push trước code.
- Khớp: kiểm general hiện có, sửa lỗi trong scope, video mẫu thật hai aspect, nguồn/license/checksum, test contract tách live model và review con người.
- Lệch đã được duyệt: không. CLI inference loại Gradio theo spec để tránh Pillow có advisory; metadata upstream thiếu dependency UI được ghi rõ.
- Lệch chưa duyệt: không. Không áp lại hoặc xuất bản cấu hình cloud, không upload công khai, không paid API.

## Đã làm

- M2 code được hoàn thiện: CreativeBrief/strict proposal/source coverage, Ollama/Comfy transports và capabilities, plan/image jobs/snapshot/idempotency/cancel/review/apply, API và hai panel React. Giữ project M1/backwards save khi thiếu brief.
- Provider guard: loopback-only, no redirect kể cả injected client, bound NDJSON/response/time, malformed payload/graph nodes thành lỗi an toàn, không lấy filename provider làm đường dẫn file cục bộ.
- Candidate hash khớp bytes chuẩn hóa, hash nguồn trong provenance; không tự thay cảnh hoặc file đã duyệt, conflict/cross-project bị chặn.
- Renderer sửa xuống dòng tiếng Việt, cân caption2dòng, vẽ silhouette trước chi tiết và AAC headroom (TP-2 trước encode để final≤-1dBTP).
- Có config/comfy-sdxl-api.example.json, scripts/live_planner.py, docs/local-ai.md, hướng dẫn config và .env.example đúng trạng thái adapter.
- Script review/lock riêng: tranh gốc Pillow1600×1400, TTS VieNeu3.8.3 CPU ONNX FP32, preset Hải Đăng thực, model/codec13file kiểm checksum/revision; ASR large-v3-turbo local MIT. Không clone giọng hoặc dùng stock.
- Video cuối .data/review/review-portrait.mp4 và review-landscape.mp4, cùng report/verification/story/provenance/contact sheets/poster ngoài Git. Renderer app thật, audio nhập vào; câu kết nhắc lại ý chính và reuse audio cảnh2 có provenance.
- Đã archive nguyên handover nghiên cứu cũ vào .agent/handover/2026-10-30-whiteboard-video-tool.md trước ghi bản này.

## Chưa làm

- AI-PLAN/AI-IMAGE live: Comfy/GPU/checkpoint chưa có, Ollama/Qwen chưa xác nhận live. Script smoke và contract không thay bằng chứng này. Không gán điểm chất lượng ảnh/video AI.
- Reference/character image control, batch sau approval và 3D template editor còn M2 mở rộng; whiteboard contour order chỉ là heuristic, chưa semantic reveal toàn bộ.
- M3 UI TTS/voice picker/job cache, test20câu/nghe thật, forced alignment/SRT và human quality review còn thiếu. CLI review không là UI TTS hoàn chỉnh.
- M4 OAuth/API upload private/draft bằng credentials có quyền, cover/180s/packaging/device QA chưa làm. Không có publish thật.

## Cách chạy

- App: README.md; AI local: docs/local-ai.md.
- Tái tạo sample: docs/qa-review.md với venv CLI riêng, requirements có hashes và excludes.txt; model không tự tải lúc mở app.
- File review thực trong .data/review (ignored), video không commit Git. Các report có checksum và snapshot để đối chiếu.

## Test sẵn có

- Trước sửa:31pytest qua/1fail health image do assertion M1 cũ; frontend5Vitest/typecheck qua. Ruff1/mypy3 lỗi đã được ghi từ phiên trước.
- Sau sửa:91pytest+5Vitest+7Playwright=103pass, khôngskip. Có1upstream Starlette/httpx deprecation warning, khôngtắt.

## Test đã chạy

- backend/.venv/bin/python -m pytest backend/tests -q:91passed,10,76s ở lượt full cuối;4typography cases được kiểm lại khi chỉnh câu sample.
- AI/SEC/LG/JOB: strict source IDs/Unicode/invalid refs/retry bounded/identity changed, confirm/conflict/idempotency/cross-project/cancel/restart, candidate verify/apply, malformed graph, redirect/path/oversized stream và safe capability.
- npm --prefix apps/web run check:TypeScript qua,5Vitest pass. npm run build và format:check qua.
- npm --prefix apps/web run test:e2e:7passed25s, desktop1366/mobile390, axeWCAG2A/AA, import/export/download/reload, keyboard/plain text, proposal checkbox/reload/apply và candidate không tự thay ảnh.3AI cases làmock contract.
- Ruff check/format check và mypy12sourcefiles qua trước commit; khôngdisable rule. Test locator mới từng fail do getByLabel với textarea có nội dung, sửa dùng accessible role giữ nguyên assertion; lượt cuối7pass.
- npm runtime audit và pip-audit backend:không advisory báo; app nội bộ không có trênPyPI không được database audit. Venv CLI ban đầu39Pillow12.3advisory doGradio, đã loạiUI/khóa48packages/audit lại0. Inference sautáchbyte-identical câu1, ASR thật qua.
- OUT/AR/AUD: full decode -xerror cả2MP4, H264/yuv420p30fps/AAC48kHz,32,021333s; A/Vlệch<100ms. Final measured integrated-15,72LUFS, truepeak-1,37dBTP ở cả2aspect.
- ASR final khớp8/8cue sau bỏcase/punctuation; cảnh8 lànhắc lại lời cảnh2 vàreuseaudio. Đây là sample-specific; không gọi làđộchínhxácchung hoặcngườiđãnghe. Creator reviewcònchờ.
- Xem contact sheets24frame/aspect, stillnative vàcảnhkếtcả2layout. Guides khônginvideo; chữgiữdấu/khôngngắtgiữatừ/cropchủthể.

## Test không chạy

- AI-PLAN/AI-IMAGE/VIDEOAI live và Wan/LTX/FLUX/SDXL benchmarks:thiếu model/GPU/service phùhợp. Không lấycontractpass thaylive.
- M3 human listening20câu/forcedalignment/wordtiming và full3Dqualitygate:chưa triểnkhai. Video hiệnscene-level captions.
- SOCIAL-LIVE/OAUTH/KIDS inclusion:chưacredentials/appquyền vàchưaM4; khôngupload thật.
- NativeWindows/macOS hoặcđiệnthoạithật:chưa kiểm, chỉChromiumemulation.

## Quyết định đã ghi vào nhớ dài hạn

D-004:QA bằng artifact thật, license theo đúng thành phần và CLI inference riêng, không đánh đồng personal với mọi NC model. ARCHITECTURE/PROJECT phản ánh M2 adapter và TTS review.

## Rủi ro và nợ

- Không hứa“chấtlượngtốtnhất”trêntấtcảstyle/độtuổi/model. Cần creator nghe/xem và duyệt nội dung trướcđăng; ASRkhôngthayviệcđó.
- SDK upstream khaiGradio required nhưng CLI chủđộngloạibộUI khôngdùng. uvpipcheck trênvenvCLI sẽbáothiếuGradio;khôngclaimcheckđópass hoặcSDKWebUIđầyđủ. Cầnpackaging inference đúng hoặcupstreamfix trướcđónggói M3.
- Comfy metadata cho têncheckpoint/workflowhash,chưa xácminhhashweights;quảntrịpin/checksumriêng. Mẫu SDXL chỉcontract,chưa smokeGPU.
- Giấyphép mẫu:tranhgốc,NotoOFL,VieNeu+codecONNX+sea-g2pApache2,ASRMIT. Cá nhâncókiếmtiềnvẫncầnkiểmđiềukhoảnmodelkhác. KhôngphânphốibinaryFFmpeg/Blendertrongrepo.
- Cácmodel/MP4/WAV/cache/.data/.toolskhôngởGit;khôngcósecret/APItrảphí,khôngpublishcloudconfig.

## File đã đụng

backend/auto_tool_video (domain/api/worker/providers/planning/generation/render), backend/tests, backend/pyproject.toml/uv.lock; apps/web/src và e2e/ai.spec.ts; config/comfy-sdxl-api.example.json; scripts/create_review_video.py,live_planner.py,review-tts/requirements.in,requirements.txt,excludes.txt,generate.py,verify.py; README,.env.example,.gitignore; docs/local-ai.md,qa-review.md,development-plan.md,licenses.md; .agent/memory vàhandover.

## Agent sau đọc gì

1. AGENTS.md vàspecs/whiteboard-video-tool.md.
2. Handover này vàdocs/qa-review.md,local-ai.md,development-plan.md; artifact .data/review nếucònworkspace.
3. PROJECT/ARCHITECTURE/DECISIONS/CONVENTIONS vàTASKS/SESSION; tiếpM2live/M3/M4 khôngxinngười dùngcấpquyềncode/pushlại.
4. .agents/skills/video-quality-review/SKILL.md khiQAartifactmới;khôngáp/publishcloudcũ.
