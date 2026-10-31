# C04 #89 — Import vs Fit Audio 30 FPS parity reproduction

**Status: TEST-ONLY REPRO CANDIDATE / NO PRODUCTION FIX / QA PENDING.** Current source baseline: `feat/short-video-studio` @ `4df70a0cb74d64a5d10deb5cf2677fca36c4c64e` (2026-10-31 ICT). Independent test QA proposed T02; BA01+BA02 must decide product semantics and allocate any production repair. This note accompanies *only* the new test file `backend/tests/test_import_fit_audio_grid_parity.py`. CI conclusions and actual RED/PASS must be recorded on PR/issue comments **after** execution; this file does not claim tests have run locally or remotely.

## Reviewed source and falsifiable hypothesis

- [media.py import_asset lines 153–167](https://github.com/qualife1291/Auto-Tool-Video/blob/4df70a0cb74d64a5d10deb5cf2677fca36c4c64e/backend/auto_tool_video/media.py#L153-L167): a clip import sets `max(1,frames_for(clip_duration)/30)` and, if audio already attached, keeps the larger audio timeline; **audio import** sets `max(1,frames_for(audio_duration+0.12)/30)` without checking an existing longer clip. Beat text remains intact but status is marked `needs_review` when import changes duration.
- [api.py fit_audio](https://github.com/qualife1291/Auto-Tool-Video/blob/4df70a0cb74d64a5d10deb5cf2677fca36c4c64e/backend/auto_tool_video/api.py): Fit Audio uses `max(1, ceil((asset_duration+pause_after)*30)/30)` for **audio only**, with scene 20s/total 60s validation and revision CAS. Existing visual clips do not participate in its maximum-duration expression.
- [timing.py frames_for](https://github.com/qualife1291/Auto-Tool-Video/blob/4df70a0cb74d64a5d10deb5cf2677fca36c4c64e/backend/auto_tool_video/timing.py#L7-L11): tolerance `ceil(seconds*30-0.0001)` to avoid extra frames from FFprobe microsecond rounding. In genuine near-boundary probes, compare the *actual measured asset.duration* and an explicitly equal pause; do not assume independent probes agree bit-for-bit.
- [Store.save](https://github.com/qualife1291/Auto-Tool-Video/blob/4df70a0cb74d64a5d10deb5cf2677fca36c4c64e/backend/auto_tool_video/store.py): versioned CAS, asset ownership and authored beat invalidation on duration changes. **No edits** to this or any other source.

**Source-level suspected divergence (not a runtime result yet):** with the *same* 25 FPS, 2.12s H.264 clip and 1s WAV, fixed `pause_after=0.12`, the clip timeline is expected to require **64/30 = 2.133333s**, while short audio requires **34/30 = 1.133333s**. A clip-before-audio import may reduce scene to 34 frames, while audio-before-clip preserves 64 until Fit Audio reduces it again. Both paths could still be on the 30 FPS grid; the safety question is **lost visual-clip frames and ordering semantics**, not necessarily a fractional-frame misalignment.

**Product decision required:** Is truncating a longer clip to Fit Audio's shorter voice (even when no explicit trim was chosen) intended? If yes, document approved trim behavior and adapt future tests to the explicit contract; if no, a separate BA-authorized source task is needed to preserve the full clip floor without breaking total/scene limits or user-requested retimes. Do **not** label either business rule approved based on this code read.

## Deterministic, synthetic test matrix

| Test group | Source/inputs | Assertion and anticipated status |
| --- | --- | --- |
| WAV + same pause | 1s, 2s, 19.65s PCM16 48 kHz, portrait/landscape, `pause_after=0.12` | Measured asset unchanged, import/fit equal `frames_for(asset_duration+0.12)/30`, 1–20s, CAS. **Expected PASS.** |
| Author beats + retime | 2s WAV, authored second-by-second text, unchanged 0.12 then changed 0.35 pause | Unchanged authored remains authored; genuine retime goes `needs_review` but beat text persists. **Expected PASS.** |
| Short clip + long narration | 25 FPS 2.12s MP4 and 2s WAV (same grid ceil 64 frames), both import orders | Import and Fit retain same 64-frame duration, image/audio IDs and motion style. **Expected PASS.** |
| Long clip + short narration | Same clip and 1s WAV, clip imported **before** audio | Assert scene duration never falls below clip's exact renderer frame count. **Potential actual RED**, not yet measured on GitHub. |
| Fit after long clip + short narration | Same pair, audio imported **before** clip, followed by Fit `pause_after=0.12` | Assert duration remains at least video frame floor. **Potential actual RED**, pending CI; BA must decide if clip truncation is legitimate. |
| Negative CAS and missing audio | Stale `revision`, project with no audio | Must return 409/`REVISION_CONFLICT` or 400/`MISSING_AUDIO`; no persisted mutation. **Expected PASS.** |
| 3 scenes, 60-second exact limit | Three 19.65s WAVs, Fit `pause_after=0.35` then 0.36 | Exactly 20s each/60s total valid; >20s rejected atomically. **Expected PASS.** |

Synthetic WAV and color-only H.264 MP4 use built-in Python wave and CI FFmpeg; no real creator voice, external model, secrets, uploaded traces or paid providers. Two aspect ratios are tested for WAV; media timeline is aspect-independent but this does not replace native 9:16/16:9 watch/listen.

## Interpretation and acceptance

- **If the focused runtime test fails** on the long-clip scenarios, quote exact `test_import_fit_audio_grid_parity.py` assertion and SHA/run, plus observed clip/audio asset durations and revision/beat status **without customer data**. Treat as actual test RED for the **candidate clip-preservation policy**, not automatic authorization to change source. Leave test-only PR DRAFT / QA BLOCKED, alert BA01+BA02 and T02 for a contract/owner decision. Do not xfail, skip, relax expectations or self-merge to hide the failure.
- **If all pass**, report `PASS / NO BUG REPRODUCED IN TESTED MATRIX` and do not manufacture RED or claim broad coverage. Record exact HEAD/current-base CI and test counts, plus named limitations.
- Any production fix later must be separately assigned with a single source owner, a negative-baseline proof and a green regression covering audio-first/clip-first, changed pause, clip trim decisions, authored beats, CAS and scene 1–20s/total 60s. Avoid cross-lane source edits to C04's old #44/#61, T01 watcher #59/#71, BA #86 CI concurrency.

**No execution claimed here:** local pytest, actual runtime RED, GitHub Main/A04/Dual, creator G10 and visual/voice approval = **NOT RUN at document drafting**. Rollback is simply dropping this test-only branch/PR if BA decides the candidate business invariant is wrong; no production rollback needed.


## Runtime RED checkpoint — 2026-10-31 / GitHub Actions (observed, not inferred)

**Immutable initial test-only HEAD:** `4961ac0cb0deb215f0c30f933a8a84afeb1b62ef`, source baseline `4df70a0cb74d64a5d10deb5cf2677fca36c4c64e`. [A04 workflow #41173149131](https://github.com/qualife1291/Auto-Tool-Video/actions/runs/41173149131) ran full backend pytest: **455 PASSED, 2 FAILED**; both newly added candidate visual-floor assertions failed. Importing a 1s synthetic WAV *after* a 2.12s/25fps H.264 clip shortened scene to **34/30 = 1.133333s** from visual floor **64/30 = 2.133333s** (`test_long_clip_plus_short_wav_import_order_preserves_visual_frame_floor`, line 203). Importing WAV first and clip second retained full length until `fit-audio(pause_after=0.12)`, which shortened it to **34/30** (`test_long_clip_short_wav_fit_does_not_drop_clip_frames`, line 226). This demonstrates **order-sensitive media retiming** for the proposed keep-full-clip invariant; it does **not** establish whether intentional clip trimming violates the APPROVED product contract.

[Main #41173149173](https://github.com/qualife1291/Auto-Tool-Video/actions/runs/41173149173) stopped at Ruff **format check in this NEW test file**, before pytest, not a product runtime FAIL. The follow-up test-only revision performs 4 formatting-only adjustments (no assertion/fixture logic change). [Dual FullHD #41173149084](https://github.com/qualife1291/Auto-Tool-Video/actions/runs/41173149084) **SUCCESS**. No human G10, private media, or manual approval.

**Decision requested from BA01+BA02:** approve invariant "Fit Audio must never cut previously imported visual clip" and allocate a separate narrowly scoped production fix, **or** approve intentional trim semantics with documented explicit UX warning/clip-trim behavior and redesign future test assertions. T02 remains proposed single QA_OWNER. Do not mark this Draft test-only PR Ready or merge with two failing mandatory assertions; do not mute them with xfail/skip or loosen thresholds. The report records actual RED faithfully; no source code was changed.
