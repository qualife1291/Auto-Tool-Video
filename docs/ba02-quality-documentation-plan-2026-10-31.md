# BA02 — Documentation, QA, and coder utilization plan

**Audit:** 2026-10-31 ICT. **Owner:** BA01 = BA02 co-coordinators. **Status:** PLAN / IN-PROGRESS, not a claim that all docs are cleaned or all video tests passed. **Canonical reviewed:** `fecfea79edab632da827507fb70c302e0acf824c`; refresh before any merge. **Product spec:** `specs/whiteboard-video-tool.md` (approved).

## Verified baseline

- C01 [PR #63](https://github.com/qualife1291/Auto-Tool-Video/pull/63) merged after T01 QA; exact canonical [main CI #41124112589](https://github.com/qualife1291/Auto-Tool-Video/actions/runs/41124112589) and [Dual FullHD #41124112524](https://github.com/qualife1291/Auto-Tool-Video/actions/runs/41124112524) **SUCCESS**. No creator G10; engineering eSpeak != approved actual narration.
- Current role charter on canonical has stale `C01/C02 retired`, no T02 equal-merge or BA02. BA01 [PR #51](https://github.com/qualife1291/Auto-Tool-Video/pull/51) edits this exact file and is unmerged, so **DO NOT directly edit charter** until its review/rebase; coordinate additions in its PR.
- Canonical `docs/agent-workboard.md`, `.agent/memory/short-term/TASKS.md`, `.agent/handover/LATEST.md`, `docs/development-plan.md`, `README.md` have time-stamped older A01/A02/A03/A04 and two-coder task status. T01 [PR #46](https://github.com/qualife1291/Auto-Tool-Video/pull/46) already owns these paths; **one integration owner only** and T02 independently reviews tester-authored documentation.
- Open legacy docs [PR #27](https://github.com/qualife1291/Auto-Tool-Video/pull/27), [#21](https://github.com/qualife1291/Auto-Tool-Video/pull/21), [#23](https://github.com/qualife1291/Auto-Tool-Video/pull/23) overlap README/workboard/handover/AGENTS with #46; **DO NOT blind merge** or discard prior commits; diff/rebase, salvage unique verified content, close/supersede only with explicit recorded decision.
- Open [#51](https://github.com/qualife1291/Auto-Tool-Video/pull/51) still has T01-only prose despite owner-approved T02 equal authority. Open QA docs/fixture [#37](https://github.com/qualife1291/Auto-Tool-Video/pull/37) is T01-authored; assign T02 independent QA, and separate video technical quality from creator signoff. QA watcher [#60](https://github.com/qualife1291/Auto-Tool-Video/pull/60) Draft; defect routing [#71](https://github.com/qualife1291/Auto-Tool-Video/issues/71) is P1; avoid running duplicative 15-min scans or enabling uncontrolled comments.
- Other in-flight code [#62](https://github.com/qualife1291/Auto-Tool-Video/pull/62) C02 Ready, [#64](https://github.com/qualife1291/Auto-Tool-Video/pull/64) C04 Draft, [#47](https://github.com/qualife1291/Auto-Tool-Video/pull/47) C04 Ready/old E2E evidence, [#69](https://github.com/qualife1291/Auto-Tool-Video/pull/69) C05 Ready. All need exact-current-base CI/merge-ref and named primary QA_OWNER before merge.
- C03 [#49](https://github.com/qualife1291/Auto-Tool-Video/issues/49) / Draft [#65](https://github.com/qualife1291/Auto-Tool-Video/pull/65) paused for #58; #58 [PR #67](https://github.com/qualife1291/Auto-Tool-Video/pull/67) is merged and both subsequent canonical main and dual CI passed. Resume #49 by explicit BA comment after claim refresh, not duplicate issue. C01 now available after #63 merges; recommend narrow fresh science-art negative/continuous-motion QA task following A02 #11.

## Prioritized action plan (explicit evidence gates)

| Priority | Work ID | Responsible | Output / acceptance | Gate / dependency |
| --- | --- | --- | --- | --- |
| P0 | DOC-1 | BA01 + BA02; T02 independent review | Rebase/reconcile #46 then refresh canonical workboard/TASKS/handover/development-plan/README to link current issue+PR facts, mark stale histories **historical**, no false `DONE` | #46 ready; source only when current canonical SHA and T02 QA |
| P0 | DOC-2 | BA01 + BA02; T01/T02 review | Extend #51 charter for C01–C05, T01/T02 equal QA, BA02 equal BA01 + Draft→Ready lifecycle; keep this co-BA supplement as nonoverlapping source | #51 current owner BA01, no parallel edits |
| P1 | DOC-3 | BA02 triage + PR owners | Audit/salvage #27/#21/#23 conflicts, preserve unique research/skills; either rebase or explicit Superseded with link; no silent delete/history rewrite | After #46 ownership resolved |
| P1 | QA-1 | T01/T02 | Independent QA on Ready #62/#69/#47 and docs #46/#51, assign one QA_OWNER, verify checks **on current head+merge-ref**, no auto merge if red | #62 needs current 390/1366px+pagination evidence; #47 old red and must refresh |
| P1 | QA-2 | T01 code + T02 independent QA | Fix #59 watcher 403 and #71 obsolete C03/C04 routing, prove benign degraded behavior and no spam; PR #60 Draft; no new workflow without approved scope | No comment event storm, budget/permissions considered |
| P1 | ART-1 | C01 (proposed dedicated issue) / T01 or T02 QA | Real Blender A02 temporal continuity, peg/head/hem stability, wet/dry mask, fold/spread 9:16 and 16:9; regression+hash/contact sheets; human still pending | Fresh narrow claim, no science_story.py edit without contract |
| P2 | HARN-1 | C03 / BA01+BA02 acceptance, independent tester | Resume #49, review docs-only PR #65 on latest canonical; FREE-first evidence manifest, license, version, costs, benchmark, no CI enforcement or paid provider | #58 merged and main+dual postmerge green; fresh claim |
| P2 | MEDIA-1 | Creator + T01/T02 and BA | Original Vietnamese voiced dual-1080 sample, evidence G4–G9 + full G10 human watch/listen and rights, then release decision | Not satisfied by eSpeak sample, no automatic approval |

## Cleanup acceptance standard

1. Every active doc has clear purpose, status/effective date, canonical links and authoritative owner; never call a proposed PR merged.
2. Historical archive/status comments preserved, but add current top-of-doc pointers and supersession wording after verified merge.
3. README, workboard, development plan, TASKS and LATEST must not conflict with each other on C01–C05/T01–T02/BA01–BA02, latest task owner, Draft/Ready/QA/merge states and G10.
4. Cross-links must be valid and PR changed-path conflicts documented; avoid duplicate indexes. Prefer a single canonical index after deciding #27, not two parallel docs.
5. Update plans only via scoped PR and independent review; run Markdown links, conflict/Prettier tests where configured. Documentation pass is not code/video release pass.

**Next checkpoint:** after PR #46/#51 reviewers act, use current GitHub to revise this dated plan, not overwrite historical audit or blindly infer fixed issues.
