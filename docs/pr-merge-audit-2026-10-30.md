# Kiểm kê merge và bằng chứng — 2026-10-30

**Loại:** snapshot audit, KHÔNG phải trang theo dõi PR live. **Nguồn:** GitHub PR metadata trực tiếp; kiểm tra ngày 2026-10-30 khoảng 15:30 UTC (22:30 Việt Nam). **Canonical:** `feat/short-video-studio`, head **`514ddfd966b42183dd1ba6874553794faf3f55e2`** tại thời điểm kiểm tra.

## 1. PR: tổng 13, 7 đã merge, 6 đang mở

| PR | Hạng mục | Trạng thái metadata GitHub | Merge SHA / action |
|---|---|---|---|
| [#1](https://github.com/qualife1291/Auto-Tool-Video/pull/1) | Tích hợp storyboard/motion source WIP | MERGED 2026-10-30 11:48 UTC | `7331a2296e99` |
| [#2](https://github.com/qualife1291/Auto-Tool-Video/pull/2) | A01 integrity/legacy safety | MERGED 12:08 UTC | `3354ca8e45fa` |
| [#10](https://github.com/qualife1291/Auto-Tool-Video/pull/10) | Caption/beat persistence regression | MERGED 15:15 UTC | `61ab530b13ff` |
| [#12](https://github.com/qualife1291/Auto-Tool-Video/pull/12) | A02 Blender art/motion QA tests | MERGED 15:18 UTC | `32b2c6adb64d` |
| [#14](https://github.com/qualife1291/Auto-Tool-Video/pull/14) | A05 QA evidence protocol docs | MERGED 15:21 UTC | `514ddfd966b4` |
| [#16](https://github.com/qualife1291/Auto-Tool-Video/pull/16) | Real dual-aspect 1080p integrity smoke | MERGED 15:11 UTC | `477388c1340e` |
| [#20](https://github.com/qualife1291/Auto-Tool-Video/pull/20) | QC strict missing/shifted/fabricated frames | MERGED 15:04 UTC | `4db4dac1dea5` |
| [#4](https://github.com/qualife1291/Auto-Tool-Video/pull/4) | A07 NVIDIA NIM provider research | OPEN | Docs-only; need reviewer decision; no live-provider pass implied |
| [#7](https://github.com/qualife1291/Auto-Tool-Video/pull/7) | A06 HF Gradio evaluation | OPEN | Docs-only; no cloud test implied |
| [#8](https://github.com/qualife1291/Auto-Tool-Video/pull/8) | A04 0.92× tempo and audio tests | OPEN | CI reported success on PR head, NOT merged, no original voice human approval |
| [#18](https://github.com/qualife1291/Auto-Tool-Video/pull/18) | Multi-PR exact-SHA integration gate | OPEN | Head's 3 automated workflows success; need independent integration/release review |
| [#21](https://github.com/qualife1291/Auto-Tool-Video/pull/21) | Future research/quality/skills roadmap | OPEN, DRAFT | Docs-only; not on canonical; review and merge explicitly |
| [#23](https://github.com/qualife1291/Auto-Tool-Video/pull/23) | Handover update | OPEN | Owns `.agent/handover/LATEST.md`; cleanup PR must not overwrite |

**Warning:** GitHub may show a `merge_commit_sha` for OPEN PRs as a *test merge* ref; it is **NOT proof of a merged PR**. Use `merged=true` and `merged_at` from PR metadata, then compare target branch SHA.

## 2. Canonical CI evidence (not creator approval)

At exact canonical head `514ddfd966b42183dd1ba6874553794faf3f55e2`:
- [Whiteboard Studio CI, run 41080033962](https://github.com/qualife1291/Auto-Tool-Video/actions/runs/41080033962): GitHub reports `completed / success`, push event.
- [QA Dual FullHD MP4 Integrity, run 41080033983](https://github.com/qualife1291/Auto-Tool-Video/actions/runs/41080033983): GitHub reports `completed / success`, push event.
- Important: dual1080 smoke and waveform engineering fixture do **not** prove a newly approved 12-scene original Vietnamese narrator export, semantic/physics quality or creator full watch/listen.
- At #18 head `9c7ba1f609acdb0d394166212e5a4ba8542cc823`: Whiteboard Studio CI / QA Dual FullHD / QA Exact-SHA Multi-PR Integration all reported success. This is **PR-head** evidence and cannot substitute for running on a later canonical merged head.
- At #21 head `bdc397a426e3da530d69489decc78d6e010162c5`: Whiteboard Studio CI and QA Dual FullHD MP4 Integrity reported success. This is **docs-only PR-head** evidence; no model, 60FPS or new format execution is implied.

## 3. Integrity / ownership observations

- The canonical tree had 131 entries and no tracked `*.log`, `*.mp4`, `*.wav`, `*.sqlite3`, profiling dump or GitHub Actions console log file. Media examples/fonts/lockfiles were tracked deliberately; `assets/fonts/*.ttf` and `assets/examples/wet-shirt.png` are legitimate assets and must not be deleted.
- Existing `.gitignore` already excluded `.data/`, `test-results/`, `playwright-report/`, node/venv caches, SQLite and outputs. Expand only known profiler/test output patterns, not all JSON/YAML or README snapshots.
- Five dated handover notes and source snapshot / QA review are **historical evidence**, not useless duplicates. Keep them intact and use `LATEST.md` as index, not rewriting history.
- Workboard, roadmap, LATEST and TASKS still contain pre-new-PR statuses; update **after** #21/#23 and A04/#18 merge, with exact proof. Do not silently promote A02–A05 to complete because related tests merged.
- The `docs/qa-evidence-gates.md` policy was merged in #14 and defines mandatory source/QA/human/release gates separately; cleanup must not loosen them.

## 4. Actionable next steps and conflict-free sequence

1. **Now — non-destructive hygiene:** keep source/QA history, add documentation index, log/evidence policy, QA gatekeeper skill and explicit merged/unmerged reference; do not edit active PR-owned files.
2. **Independent reviewer:** assess #4/#7 research-only; approve or request changes based on cited official docs/terms. Do not auto-claim live model access.
3. **A04 owner/reviewer:** review #8 and verify voice provenance, tempo tests, original WAV/human listening; only then decide merge under approved A05 policy.
4. **Integration QA owner:** rebase or recompute #18 against latest canonical + approved #8 and other head SHAs; rerun exact-merge test. Green historical simulation alone cannot authorize a new merge.
5. **Docs integrator:** review #21 separately, merge when approved and current; review #23 separately, re-check its list of PRs/HEAD to avoid stale status. After merges update canonical workboard, roadmap and handover in ONE owner-controlled sync.
6. **Release:** require dual1080 original voiced export + full decode, PTS/audio QC, independent human review on exact MP4 hash, then explicit release/publish authorization.

## 5. Terminology to prevent false claims

`PR_MERGED` = GitHub metadata confirms source merged.
`PR_CI_PASS` = tests completed successfully at given PR head.
`CANONICAL_CI_PASS` = tests success on canonical head SHA.
`TECHNICAL_MP4_PASS` = media constraints verified on exact exported MP4.
`HUMAN_APPROVED` = independent reviewer watched/listened on exact hash, correct rights/meaning; no critical.
`RELEASE_APPROVED` = all required earlier gates + explicit publisher approval.

**No CI, unit, smoke or PR merge status is a synonym for the last three states.**

## 6. Live recheck protocol

When reopening this report, query latest GitHub PR `state/merged/merged_at/base/head_sha`, current branch SHA and push workflow status, then regenerate status summary. **Never auto-merge or delete historical files from an old snapshot.**
