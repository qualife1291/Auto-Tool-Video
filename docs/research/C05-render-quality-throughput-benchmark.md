# C05 — Safe x264 1080p30 quality / throughput benchmark harness (Issue #99)

## Scope and authorization

- Engineering research baseline: `feat/short-video-studio` at `a6e9bc78f71edb3ca1cc60aaca230a4931e8c608` (Phase A) and `0e1c49fc819520d74b7cebeecd07b00b9087bd98` (Phase B personal CLAIM).
- BA01 approved Phase B narrow new-file code preparation; BA02 subsequently explicitly authorized **one batched isolated-branch GitHub push and Draft PR** after #95/#96 independently QA-merged and canonical postmerge Main+Dual succeeded. Authorization is **not** a production encoder change, manual Actions dispatch, independent QA pass, or merge approval. Renderer and production x264 settings are untouched; G10 creator quality/release approval is NOT RUN.
- Baseline production scene encoder is FFmpeg/libx264 `veryfast -crf 18 -threads 2` at 30fps native FullHD; final audio mux is separate, AAC 48kHz. Benchmark source is a new deterministic synthetic test fixture, **not** actual editorial art/audio and **not** a realtime renderer throughput promise.

## Opt-in use — never run in regular CI

Runs **only** when someone explicitly executes this standalone command on an authorized offline machine with installed FFmpeg 7.x, FFprobe and Python 3.12+ (no models, no downloads, no third-party dependency). Test fixtures 5–10 seconds, native 1080p in each selected aspect; at most two x264 presets per aspect and no 60fps / 4K / HEVC.

```bash
python scripts/benchmark_render_profiles.py \
  --output-dir /tmp/c05-x264-ab \
  --seconds 5 --aspect both --timeout-seconds 180 --max-rss-mib 2048
```

Output is a new unique subdirectory containing `report.json` and up to four MP4s. An interrupted or invalid run cleans its staging directory, keeps earlier successful outputs, and exits nonzero. A CI **pytest** import does not launch a 1080p benchmark. Each preset streams an independently regenerated deterministic 30fps RGB24 source from FFmpeg's built-in `testsrc2` generator. The harness SHA-256 hashes streamed RGB bytes on each encode and **fails if the input sources differ**. It pins CRF18/2 encoder threads and reports actual FFmpeg commands and video output SHA256/bytes, `ffprobe` codecs, 150–300 frame timestamps and independent decode of the full video. Duration is 5–10s, timeout 15–600s/run and combined observed producer+encoder RSS limit 256–4096 MiB. RSS is periodically sampled, not a hardware-enforced real-time OS cgroup cap; instantaneous unobserved spikes remain possible. A process that runs past its wall-time limit is forcefully terminated.

**Time interpretation:** `pipeline_wall_seconds` is generator + RGB24 pipe + x264 encoder + MP4 mux; this streaming implementation does **NOT** isolate pure encoder CPU time from generator work. To obtain genuinely separated encode-only timings, future BA review must authorize a separate bounded source replay/instrument without altering the production renderer. No source art/caption font fidelity or actual Studio ScenePainter workload is captured by `testsrc2`. RSS is sampled and cannot guarantee exact peak. This is a bounded technical comparison, not a creator quality verdict.

## Historical evidence — OBSERVED (Phase A; separate from this new harness)

Existing A04 synthetic/technical eSpeak artifact (run `41175175822`, artifact `13032855409`) was independently decoded for both aspects, 1080×1920/1920×1080, 30fps H.264/yuv420p, AAC 48kHz, 941 frames each, all PTS 1/30 cadence, no full-decode errors. **NOT** a current-HEAD CI check or human natural Vietnamese voice certification. Prior `docs/render-benchmark.md` measured 360×640 preview; its ~70fps measurement is **not** FullHD throughput.

A separate, explicit Phase A *local synthetic 5s fixture* A/B was measured before authoring this instrument (one sample/profile/aspect, same lossless RGB reference):

| Local synthetic metric | Portrait veryfast | Portrait medium | Landscape veryfast | Landscape medium |
|---|---:|---:|---:|---:|
| Elapsed generator/encode/mux in historical A/B (s) | 2.044 | 7.359 | 1.899 | 6.916 |
| Video file bytes | 5,765,636 | 6,612,352 | 5,534,448 | 6,294,719 |
| Peak measured max RSS (KiB) | 340,316 | 544,060 | 353,528 | 547,808 |
| PSNR vs identical original synthetic frame sequence (dB) | 46.3103 | 49.0927 | 46.5942 | 49.3046 |
| Full video-only decode / FPS / frames | PASS / 30 / 150 | PASS / 30 / 150 | PASS / 30 / 150 | PASS / 30 / 150 |

These numbers are **historical Phase A standalone measurements**, **not** outputs from this new benchmark script, not automated acceptance thresholds, and not future production SLA. The local historical synthetic fixture differed from this tool's exact `testsrc2` generator, so **do not compare numbers directly across harness versions**. Medium increased PSNR for this particular source but was ~3.6× slower and made larger files at identical CRF. Equal-CRF comparisons are not equal-size or equal-quality rate-distortion comparisons. Genuine editorial asset A/B, moving caption legibility, banding perception and warm/cold variance are **NOT RUN**; VMAF/VBench and G10 **NOT RUN**. No audio is generated in this harness; do not assert AAC, LUFS or audio/video sync for its MP4s.

## Safety unit tests and QA gates

- Normal unit tests exercise argument builder contract, strict 5–10s duration, memory and timeout bounds, PR-safe disabled-by-default heavy integration, wrong FPS/frame/codec/PTS rejection, partial/decode failure, cleanup and previous-result preservation, timeout and RAM breach kill handling.
- Optional **tiny 32×32 / 1s** real FFmpeg smoke is explicitly enabled with `C05_TINY_FFMPEG=1 pytest ...`, not auto-triggered by regular pytest. FullHD A/B must be separately invoked manually on an approved local machine with enough RAM.
- An engineering decision to alter production x264 preset requires measured full-pipeline + representative source A/B, two aspect images/caption sharpness, resource budget, current exact merged-head Main+A04+Dual (+A02 when applicable), T01/T02 sole independent QA_OWNER and manual G10. No automatic quality score and no renderer/encoder product change here.

## Failure and rollback

- Source RGB24 SHA mismatch, missing FFmpeg, bad stream/PTS/full decode, duration/format mismatch, nonzero return, memory/timeout breach => report error / nonzero exit and delete new staging outputs. Existing completed runs stay intact.
- This script is opt-in/offline and changes zero production defaults. Rollback is to not run it, remove its temporary output and leave `veryfast CRF18 threads2` unchanged. If this new harness is later merged then found faulty, revert only the 3 new C05 paths after independent review.

## NEW Phase B script self-test evidence — local-only (not GitHub CI)

A controlled opt-in run of **this exact Phase B script** was performed locally on 2026-10-31 with 5s and two 1080p aspects, `--timeout-seconds 180 --max-rss-mib 2048`. Both x264 presets per aspect read the same verified RGB24 stream hash. Four generated MP4s each contain exactly 150 monotonically spaced 30fps frames, yuv420p H.264, and full-video FFmpeg decode passed. Video has no soundtrack. Report and MP4 are in the local staging directory only; none were uploaded or committed to GitHub.

| Observed on this local host (5s synthetic `testsrc2`, generation+encode+mux) | Portrait veryfast | Portrait medium | Landscape veryfast | Landscape medium |
|---|---:|---:|---:|---:|
| `pipeline_wall_seconds` | 4.4668 s | 8.5240 s | 3.7667 s | 8.2454 s |
| Sampled combined producer+encoder peak RSS | 543.9 MiB | 855.8 MiB | 506.5 MiB | 853.0 MiB |
| Output MP4 bytes | 5,537,294 | 6,328,888 | 5,213,317 | 5,884,340 |
| 150 frame PTS / 30fps / full decode | PASS | PASS | PASS | PASS |

Verified RGB24 source SHA256, portrait (`veryfast` and `medium` identical): `67ea9228576e9bbd…`; landscape pair identical: `bd3dc9d389a347cd…`. Original full SHA256, exact FFmpeg commands, output hashes and PTS are in `report.json`. Total external Python process wall time observed 33.77s with max process RSS 635,356 KiB; **this is different from summed child RSS across FFmpeg processes**. No representative Studio render, PSNR for the new fixture, VMAF/VBench, warm/cold variance or human G10 was evaluated.

Normal unit preflight: **26 passed, 1 intentionally skipped** (tiny FFmpeg opt-in is off by default); explicit tiny 32×32 1s integration: **27 passed**. Python syntax compile PASS. **Ruff format/check, mypy, full repository pytest, Frontend/Playwright and current integrated GitHub Main/A04/Dual were NOT RUN** here; the isolated local environment has no cached Ruff. Repo-wide checks and GitHub PR CI must be run and independently reviewed after the authorized Draft PR is opened. This local preparation alone does not assert Ready-for-review or independent QA PASS.

## Additional local verification after C05 lint/format correction — 2026-11-02

**Environment:** isolated agent container, Python 3.13.5, FFmpeg/FFprobe 7.1.5. This is not a Mac M1 or a measurement of the Studio's full RGB-to-render pipeline.

- `py_compile`: PASS.
- Focused contract tests: **26 passed, 1 intentionally skipped**.
- Explicit `C05_TINY_FFMPEG=1` 32×32 smoke: **27 passed**.
- A fresh bounded **5s / 150-frame / 1080p30** run completed all four outputs (portrait + landscape × veryfast + medium); each output passed H.264/yuv420p/30fps, 150-frame PTS checks and full video decode. Both presets consumed the same RGB24 source hash for each aspect.
- These timings are `pipeline_wall_seconds` (generator + RGB24 pipe + encode/mux), **not isolated encoder CPU time**. No audio, real Studio art, VMAF/VBench or human G10 quality review was part of this fixture.

| Aspect / preset | Pipeline wall (s) | Sampled combined RSS (KiB) | MP4 bytes | Frames / PTS / decode |
|---|---:|---:|---:|---|
| Portrait / veryfast | 3.2655 | 525,024 | 5,537,294 | 150 / 30fps / PASS |
| Portrait / medium | 5.6042 | 894,880 | 6,329,271 | 150 / 30fps / PASS |
| Landscape / veryfast | 2.0970 | 615,500 | 5,213,317 | 150 / 30fps / PASS |
| Landscape / medium | 5.0665 | 866,872 | 5,884,340 | 150 / 30fps / PASS |

Source SHA-256:
- Portrait: `67ea9228576e9bbd6d2e5fca458d1394ac8eaf946e24ff6ebadfa9cfe22f9d83`
- Landscape: `bd3dc9d389a347cdde071ccd961e1f1a0e46a73e27b5e9b2edf3e71c7fb49f3a`

Output MP4 SHA-256:
- Portrait veryfast: `c922b45bb17dc501dcd362daa7a98d1f5f9db59e270b235b2add4c22373498d1`
- Portrait medium: `0ad7d0ccac6b0c47e45a74d0ebf244326cfeb7d0ae8bdc2cd5f2d9bc7259b99d`
- Landscape veryfast: `6bda7a265e8853c3cf644348bfc66ab726936a7330860578ca8b73b09a7a5b73`
- Landscape medium: `48229a6fdbb2f0026245fa4183b94922d117823c723470a46a8a2274dfc62ab3`

All four outputs have first PTS 0.000000s and last PTS 4.966667s.

**Ruff check/format remains NOT RUN locally**: no Ruff binary is cached and package/release DNS is unavailable in this environment. Import order, the four previously reported Ruff findings, syntax and 100-character line length were checked manually; the exact-head GitHub Main/A04/Dual workflows remain the authoritative Ruff and integrated-test gate. No production encoder defaults changed.
