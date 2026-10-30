# C04 / A03 — Caption and per-second beat integrity audit

**2026-10-30 · Status: research/pre-merge evidence (not creator approval)**  
**Owner:** C04 · **BA:** BA01 · **independent QA:** T01  
**Task:** [#25](https://github.com/qualife1291/Auto-Tool-Video/issues/25) · **approved parent specification:** `specs/whiteboard-video-tool.md` · **baseline:** `feat/short-video-studio` at `514ddfd966b42183dd1ba6874553794faf3f55e2`.

## User problem, scope and contracts

Creators must preserve authored Vietnamese narration, diacritics and per-second storyboards while reviewing captions and editing audio/timeline lengths. The editor must never present an unreviewed beat plan as already authored. The desktop and 390px mobile UIs share the React implementation.

- `apps/web/src/main.tsx`: `updateScene()`, the `beat-editor` and its per-beat textareas; state and save/reload.
- `apps/web/src/domain.ts`: optional `second_by_second` and `beat_plan_status` `authored | needs_review`.
- `backend/auto_tool_video/store.py`: `Store.save` invalidates authored beat plans **when duration changes**, preserving original beats (only on a server save).
- `backend/auto_tool_video/domain.py`: strict 0-based consecutive beats and length validation for authored plans.
- `backend/auto_tool_video/render.py`: captions are rasterized separately; `SecondBeat` metadata is **not** compiled into animation keyframes.
- `backend/tests/test_caption_entry_regression.py` and `apps/web/e2e/beat-persistence.spec.ts`: merged #10 baseline tests.

### Reproducible static-source defect (not a claimed local RED run)

1. Prepare a scene with `duration=3.0`, three authored beats at seconds 0–2 and valid narration.
2. Change duration to 2.9 in the React UI. The original `updateScene` spreads `changes` into the scene without invalidating `beat_plan_status`; `ceil(3.0) === ceil(2.9)`, so the UI's existing count-mismatch warning is absent.
3. Existing UI beat-edit onChange unconditionally sets `beat_plan_status: 'authored'`, even if a plan was `needs_review` and the editor changed only one beat.
4. The backend invalidates duration on save, but cannot correct the misleading **pre-save** UI or automatically know which individual generated cues a user has reviewed. A narration edit can also make authored spoken cues stale before save.

Evidence: current canonical file paths above, task #25 and test changes on this branch. **A pre-fix runtime regression was NOT RUN**; Playwright on exact branch PR head must verify actual behavior.

## Options, decision and reversibility

| Option | Quality and correctness | Cost/compatibility | Decision |
| --- | --- | --- | --- |
| A. Keep current UI | UI may claim authored after partial edit; duration change of equal beat count has no UI warning | Zero change, unsafe approval semantics | NO-GO |
| B. Local UI status invalidation + explicit creator beat confirmation | Safe pre-save feedback; preserve content and server contract; no schema migration | Small scoped React + E2E patch; changes only draft-status UI | **GO** |
| C. Introduce full backend beat-review state machine | Audit individual cue approvals and cross-client invalidation | Backend schema/API/migration/security changes; outside A03 exclusive paths | RESEARCH MORE; BA-owned scope |

**Implemented design target B:** mark plan `needs_review` immediately if duration/narration changes; editing one beat preserves its current plan status. Explicit button to confirm a **fully populated, correctly counted** beat plan, not an automated approval. This confirms storyboarding fields only, **never video motion, fact accuracy, voice quality or human perceptual QC**. Existing API contract and snapshots remain untouched. Rollback: revert isolated React code and its focused test commit; no data migration.

## Test matrix and risks

- Existing authored beat edit persists exact Vietnamese Unicode and `authored` status.
- 3.0 -> 2.9 sec keeps the same three beat records yet changes status to `needs_review` **before save**, and reload preserves text.
- Editing one drafted/stale cue cannot silently elevate remaining draft to authored.
- Explicit confirmation requires expected count and all required fields; remains unavailable for incomplete or empty drafts.
- Modifying narration after confirmation invalidates spoken cue review; saved result still preserves old beat fields.
- Run on 390px and 1366px Chromium; retained mobile overflow and accessibility tests must pass.
- Preserve previous caption bounce, safe zones, original text, 30fps PTS and dual-aspect 1080p technical QC. No renderer, schema, audio or shared documentation edits.

**Pending verification:** GitHub Actions exact-HEAD Ruff/mypy/pytest/TS/Vitest/build/Prettier/Chromium and dual1080 media. No original approved Vietnamese narration, creator visual/listening approval, GPU inference or release authority. Those stages are **NOT RUN**.

## Security, performance and operational review

No new package, paid provider, network API, database column, user account, secret or external processing. Existing local project revision CAS remains authoritative. Array editing is linear in scene count + beat count (<=20 each), constant-bounded for this app; no renderer or video byte changes. The UI confirmation is an acknowledgement of all editable beat fields only and is not a substitution for T01 regression or human creative review.

Sources reviewed: approved project spec; BA01 [task #25](https://github.com/qualife1291/Auto-Tool-Video/issues/25); canonical source modules above and [merged QA PR #10](https://github.com/qualife1291/Auto-Tool-Video/pull/10), all read 2026-10-30. Since no new upstream dependency/technology is introduced, the current implementation is the version-pinned comparison baseline; no online framework migration or independent official upstream compatibility claim is being made.
