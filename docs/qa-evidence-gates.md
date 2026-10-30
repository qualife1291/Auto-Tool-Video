# A05 — Strict, reproducible QA evidence gates

**Date:** 2026-10-30 · **Status:** POLICY DOCUMENT ONLY; NOT PRODUCT RELEASE APPROVAL  
**Owner:** [A05 documentation claim #13](https://github.com/qualife1291/Auto-Tool-Video/issues/13)  
**Applies to:** `feat/short-video-studio` and every agent PR targeting it  
**Related:** [workboard](agent-workboard.md), [quality rubric](video-quality-standard.md), [QA review](qa-review.md), [storyboard](storyboard-review.md), [A04 code PR #8](https://github.com/qualife1291/Auto-Tool-Video/pull/8)

## Non-negotiable rules

A **technical pass**, **video QC pass**, **visual/audio human acceptance**, and **release approval** are different decisions. Never claim a later decision from an earlier one. A GitHub Actions green check at an old SHA does not certify a newer PR, merge result or local, uncommitted source. A skipped mandatory test is **NOT RUN**; a fail cannot be made green by deleting the test, weakening the assertion, changing an output threshold, silently using mocks or changing generated inputs until the check is meaningless. Track every failure including pre-fix results and root cause. Never mark live cloud providers tested without an authorized request and redacted account evidence.

**Gates that fail stop the next release stage.** Partial source work may continue on isolated branches, but never merge/publish a purportedly approved deliverable or move the canonical workboard to DONE-VERIFIED without the required evidence. `continue-on-error` is reserved for explicitly labeled *nonblocking diagnostic audits*, never for required build, QA, audio/video or human checks.

## 0. Ownership, baseline and provenance

1. Read `AGENTS.md`, `AGENT-CODING-STANDARD.md`, `docs/agent-workboard.md`, `.agent/handover/LATEST.md` and the latest open issues/PRs. Claim exactly one workstream in an issue; document exclusive paths. Confirm no overlapping in-flight PR and leave agents' owned files alone.
2. Record full 40-character **Git head SHA**, base SHA, PR merge-ref SHA, dirty/clean status, date/time UTC, Linux image, Python/Node/npm/uv versions, FFmpeg/FFprobe/Blender/Chromium versions. Use `uv sync --frozen` and `npm ci`; never update lockfiles as a testing side effect.
3. Use fresh isolated `APP_DATA_DIR` and `.data/<case-id>` on each run. Preserve data if a failure occurs; do not reuse unvalidated output or mix reports from two runs. Do not upload personal audio, paid credentials, API outputs with private prompts or model weights.
4. Store SHA-256 of each source WAV, trimmed WAV, retimed WAV, exported MP4, exact story JSON, provenance JSON, QA report and script inputs; include model/tool version and transformation command. Hash mismatch fails, regardless of how playable the file looks.

## 1. Gate matrix: required, auditable evidence

| Stage / owner | Hard acceptance gate | Required proof | What a pass does **not** imply |
| --- | --- | --- | --- |
| G0 preflight | Head/base SHA, dependencies, disk, ownership, no secret; source matches PR | `git status`, `git rev-parse`, tool versions, issue/PR | Current branch is releasable |
| G1 static | Ruff check AND format across **entire** repository, mypy, frontend TypeScript, Prettier, production build | Commands, exit 0, exact SHA | UI works |
| G2 fast tests | All Python pytest tests incl. negative and failed-publish paths, all Vitest; **zero failures**, mandatory skip count zero when tools are installed | Counts + warning list + JUnit/artifacts when supported | Media passes on real codecs |
| G3 browser + contract | Chromium Playwright E2E with isolated FastAPI/SQLite and local/contract AI adapters; scene edit/reload, Unicode, accessibility, error/revision/cancellation and guarded export | E2E pass count, environment and trace on failure | Real Ollama/ComfyUI inference is proven |
| G4 voiced source | Exactly 12 original Vietnamese **spoken WAVs**, original narrator provenance, each mono PCM16, meaningful signal, source/retime SHA, correct narration order, no external voice cloning | `voice-source-manifest.json`, `tts-provenance.json`, `audio-timing.json`, WAV count and hashes | Spoken Vietnamese quality is human-approved |
| G5 tempo/timeline | Explicit `atempo=0.92` with preserved pitch, measured duration from output sample count, scene frame count at 30FPS and global <=60s, no omitted or clipped tail; reject malformed/stale WAV | source vs processed spectral checks, sample rate, hashes, `story.json`, per-scene duration deltas | Timing is perceptually well paced |
| G6 failure atomicity | Wrong hash, corrupt/stereo WAV, silent WAV, overlong scene, missing voice, simulated disk write and later-scene failure never corrupt source, approved outputs or published metadata | Dedicated negative tests + before/after SHA comparisons | Storage backup/restore is guaranteed across total machine power loss |
| G7 actual 1080p media | Run **12-scene voice-driven** MP4 for portrait 1080×1920 AND landscape 1920×1080; decode **entire** audio/video; exact H.264/yuv420p/AAC48kHz/30fps CFR/PTS and per-frame count; audio-video/container length mismatch <=100ms | MP4 SHA, ffprobe streams/PTS, full `ffmpeg -xerror` decode, QC JSON for each aspect | Visual content is scientifically accurate |
| G8 strict audio QC | Local renderer's policy `local-qc-2`: integrated loudness between −17 and −15 LUFS, true peak <=−1 dBTP after AAC; non-silent speech, sensible end and reported silences. **Do not widen thresholds on failure.** | Exact `quality-report` passed checks and `silencedetect` ranges, measured on final exported MP4 (not unencoded WAV) | Listener understands all words |
| G9 visual/time warnings | Full-frame QC scan reports flashes/freeze/near repeats; warnings are documented with scene/timestamp and not automatically dismissed | QC findings, frame thumbnails head/mid/tail, 390px/1080p/1920p crop inspection | Human perceives smooth motion or correct cloth physics |
| G10 human review | Watch/listen **entire file** at normal speed, both aspect ratios; validate factual claims, Vietnamese pronunciation, children/audience suitability, caption safe-zones, motion, source rights, disclosure. Score each criterion 1–5; no critical, all 4–5, acknowledge warnings, explicit reviewer sign-off | Human reviewer ID/date/device, video hash, criteria, timestamps and `manual_review` | Rights/platform certification |
| G11 integration/release | Rerun G1–G9 on merge commit with no tests silently skipped. G10 on the **exact hash being published**; approve upload separately | Final SHA, CI links, QC/creator approval, release decision | Guaranteed inclusion on a platform or YouTube Kids |

**G4 fixture versus production:** eSpeak `-v vi` produces **real synthesized Vietnamese speech audio** appropriate for detecting codec/timing/loudness integration bugs. It is not the pinned/approved VieNeu sample, a native-speaker benchmark, a pronunciation proof or a user-authorized voice clone. A04 may master *its own eSpeak fixture* to supply stable test dynamics, but must not alter production renderer QC thresholds. The real 12-scene approved narrator test is a distinct required production gate, not fulfilled by eSpeak.

## 2. Reproducible local commands

Use these from repo root on Ubuntu Linux after installation. Never use a dev-server working directory containing a previous test's SQLite database.

```bash
set -euo pipefail
git rev-parse HEAD
git status --short
python3 --version; node --version; ffmpeg -hide_banner -version | head -1
ffprobe -hide_banner -version | head -1
blender --version | head -1
espeak --version | head -1
uv sync --project backend --frozen --group dev
npm --prefix apps/web ci
uv run --project backend ruff check backend scripts
uv run --project backend ruff format --check backend scripts
uv run --project backend mypy backend/auto_tool_video
uv run --project backend pytest backend/tests -q
npm --prefix apps/web run check
npm --prefix apps/web run format:check
npm --prefix apps/web run build
npm --prefix apps/web run test:e2e
uv run --project backend python scripts/smoke_export.py --portrait1080
# Only after A04 PR #8 merged, or with its branch explicitly checked out:
uv run --project backend python scripts/voice_wav_acceptance.py \
  --output-dir .data/voice-acceptance --render
```

The last command is **not** a replacement for inspecting the two resulting `voice-report-*.json` files. On failure, inspect `voice-qc-failure-*.json` and keep the job red; never change `local-qc-2` just to force success. If a command from this example does not exist on the selected commit, record `NOT RUN — missing A04 integration` rather than assuming success.

## 3. Required audio/video acceptance evidence

For **each scene** record: scene index and cue text; input WAV path+SHA, sample rate, channels, sample format, frame count, duration, last non-silent speech; WAV after trim SHA and margin; WAV after `atempo=0.92` SHA, actual sample duration, tempo ratio and pitch test results; allocated 30FPS frames and corresponding scene duration.

For **each aspect** record: MP4 SHA, bytes, H.264 pix format, width/height, 30FPS, timestamp sequence and biggest frame gap, expected frames versus actual, audio codec/48kHz/channel, audio/video/container duration, loudness integrated LUFS, true peak dBTP, silence duration and longest interval, full decode status, policy version and each failed QC check. Store `quality_report`, not only a green summary. Scan all frames with FFmpeg/FFprobe; screenshot selection alone cannot reveal hidden broken frames. Human review examines beginning/middle/end and transitions at real speed; no automatic pixel score can approve natural motion or physical realism.

The 12-cue eSpeak fixture and any renderer generated visual must be labeled **engineering synthetic**. Its result is not the approximately 41.9-second earlier VieNeu project; never substitute their expected duration or sample hashes.

## 4. Failure-response protocol

1. **Red CI or a mandatory skip:** mark BLOCKED, capture run/step/log, commit SHA, data hash and reproducible command. Check missing binary/version before changing code, but do not call dependency failure a pass.
2. **QC failed:** extract all failed check IDs and their actual values. For example, `narration_loudness=-17.62 LUFS` is out of −17 to −15; use provenance-aware input-fixture mastering or fix the real audio processing, not weakened threshold, `silent=True`, shortened fake speech, or modified source text.
3. **Change control:** fix only the current agent's owned files on a dedicated branch. Add a regression that fails before the fix. Run focused tests, then full CI against the *new* merge-ref. Old green runs remain historical evidence.
4. **Rerun and reconcile:** preserve both failed and passing run URLs, capture artifact hashes and compare the new tree/mergeability. Don't count a failed job's successful earlier steps as an overall pass.
5. **Publish gate:** source and media must have matching SHA, no stale voice, QC technical passed for **both** aspect ratios, and human `manual_review` must approve the exact exported file. Do not auto-upload/publish, infer legal rights or mark creator review done automatically.

## 5. Multi-agent integration schedule

- A01: DONE-VERIFIED; treat schema and beat compatibility as regression requirements; tests must always run with post-A01 merged source.
- A02 and A03: PRs #12 and #10 have separate visual/editor ownership. Preserve their in-flight changes and test actual merged code before the respective feature is called verified.
- A04: [PR #8](https://github.com/qualife1291/Auto-Tool-Video/pull/8) owns WAV and timeline sources/tests and a separately installed Blender+eSpeak media CI. Track the latest **full SHA**, not a prior successful PR run.
- A05: this document claims only the evidence methodology. Full technical+creator acceptance still needs authorized original VieNeu audio/media and an explicit reviewer; the document itself does not satisfy G10.
- A06/A07: research-only PRs #7/#4 cannot certify live model quality/access. A08 needs approved privacy/access/price/contract gates. A09/A10 remain unimplemented.

Use one PR per agent and do not edit `docs/agent-workboard.md` or `.agent/handover/LATEST.md` concurrently without coordinating. After each merge, rebase/integrate the next PR and rerun the canonical CI. If no original voice/model/asset exists, record exactly which case was blocked and preserve the right to test later, rather than manufacturing a substitute reviewer decision.

## 6. Release evidence record template

Maintain the following fields in a machine-readable release report (JSON/CSV) with hashes and direct artifact links; redact local private paths or user data before posting publicly:

```text
release_id, utc_timestamp, pr_number, head_sha, base_sha, merge_ref_sha
runner_image, python, node, uv, ffmpeg, ffprobe, blender, chromium
lint_status, full_format_status, mypy_status, ts_status, prettier_status
pytest_pass, pytest_fail, pytest_skip, vitest_pass, playwright_pass
input_cue_count, all_wav_sha256, tempo_policy, source_sample_rate
timeline_seconds, elapsed_speech_seconds, output_scene_frame_count
portrait_mp4_sha256, portrait_qc_status, portrait_failed_check_ids
landscape_mp4_sha256, landscape_qc_status, landscape_failed_check_ids
portrait_lufs, portrait_truepeak, landscape_lufs, landscape_truepeak
decode_status_both, fps_pts_status_both, warnings_and_timestamps
human_review_status, reviewer, reviewed_mp4_sha256, next_action
```

**Status vocabulary:** `PASS` means evidence on the exact commit and artifact; `FAIL` means a verified failing gate; `NOT RUN` means no execution evidence, missing dependencies/rights or intentionally skipped; `BLOCKED` means a required gate cannot proceed; `PENDING HUMAN REVIEW` means machine QC is not a publication decision. No blanket `ALL PASS` when any mandatory gate remains untested.
