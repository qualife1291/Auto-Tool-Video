# Push discipline and CI capacity policy (proposal for BA/QA review)

**Scope:** Auto-Tool-Video, canonical branch `feat/short-video-studio`, issue [#86](https://github.com/qualife1291/Auto-Tool-Video/issues/86). The current PR only adds pull-request run concurrency and this operational standard. **No test gate is removed, skipped or relaxed.** This process is subject to BA01+BA02 and independent T01/T02 QA review before adoption.

## Why this matters

Measured GitHub Actions sample (100 most recent runs at owner audit, 2026-10-31): 29 Whiteboard CI (~3 min each), 24 A04 (~5.25 min each), 30 Dual FullHD (~0.84 min each), 8 Blender (~0.96 min each). A documentation-only PR with three sequential commits can trigger nine core/heavy runs. Frequent pushes of a partially tested PR consume hosted runners and produce obsolete SHA evidence. Scheduling BA/Coder/Tester every hour can continue; this policy is about **push cadence and CI waste**, not building a separate realtime Agent platform.

## Push / PR lifecycle (all Coder, BA-doc and QA-doc contributors)

1. **Before editing:** read the assigned GitHub issue and approved spec, personally CLAIM any required write paths, inspect latest canonical SHA and existing open PR changed paths. Keep an isolated feature branch; never push directly to canonical or overwrite another agent's claimed files.
2. **Work locally, commit logically:** multiple local commits are fine. Do not push each tiny documentation typo, style correction or intermediate RED step solely to "see CI." Keep a local RED→GREEN reproduction for bugs and rerun affected tests before the remote push.
3. **Run local preflight (where tools exist):** at minimum `git diff --check`, inspect `git status --short`, review the changed file list and any secrets/large assets. For applicable Python work: `uv run --project backend ruff check backend scripts`, `uv run --project backend ruff format --check backend scripts`, and the relevant `uv run --project backend pytest ...`; for web work: `npm --prefix apps/web run check` and `npm --prefix apps/web run format:check`. Preflight may be narrower per task but record exactly what ran and what was NOT RUN. For cross-module/API/security/audio/video changes, run the wider locally feasible suite before requesting review.
4. **Batch into a useful push:** push when a coherent milestone is ready for remote feedback, not once per agent-message or one-word comment. This is a guideline rather than a fixed time or hard commit-count cap; hotfixes/failed QA fixes can be pushed promptly. Avoid multiple autonomous agents writing/pushing the same branch.
5. **Start Draft; go Ready only with evidence:** Draft PR while implementation is unfinished. Update issue and PR with base/head SHA, scope, local test results, evidence/artifacts, blocked/NOT RUN gates and rollback. Ready for review only after self-checks and an intentional final push. QA_OWNER=T01 or T02 only after BA/QA routing. Do not use "[skip ci]" to bypass mandatory checks.
6. **After Ready:** treat the PR as stable. Respond to review feedback on the issue/PR first, consolidate changes, run local regressions and push one coherent correction. If a code change invalidates previous QA, require a **new exact-HEAD + current merge-ref review** and do not reuse an older successful run. Do not force-push shared/reviewed branches or rewrite another agent's commits.
7. **After merge:** T01/T02 owns independent QA and any eligible merge, post-merge canonical checks and exception decisions; creator G10/manual video review remains separate. A canceled obsolete run, a skipped job, a local-only PASS or a green historical SHA **never counts** as current PR QA PASS.

### Evidence template (paste to assigned issue / PR at meaningful checkpoints)

```text
[PRE-PUSH / PR HANDOFF]
SEAT_ID: Cxx | Txx | BAxx
TASK_ISSUE / CLAIM: #...
BRANCH / BASE_SHA / PR_HEAD_SHA: ...
CHANGED_PATHS / CONFLICT_CHECK: ...
LOCAL_PREFLIGHT: command → PASS/FAIL/NOT RUN
REMOTE_CI: exact run URL + SHA + status (not assumed PASS while queued)
CONTENT/MEDIA_QA: applicable? evidence or NOT RUN
QA_OWNER: T01 | T02 | UNASSIGNED
BLOCKERS / NEXT_ACTION / ROLLBACK: ...
```

## Phase 1 code change in this PR: per-workflow PR concurrency

Each of the four core workflows now uses:

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.event_name }}-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: ${{ github.event_name == 'pull_request' }}
```

**Effect:** when a newer run starts for the **same PR and same workflow**, its older running/queued version may be canceled. Different PRs have different group keys. Canonical `push` and `workflow_dispatch` use distinct event groups and do **not** auto-cancel. This does **not** prevent the newer PR run from executing full tests. All original workflow names, triggers, job names, full render steps, formatting thresholds and permissions remain unchanged.

**Known limits:** cancellation cannot recover time already consumed, doesn't eliminate the first expensive run for a docs-only PR, and one could still create many PRs at once. Treat `cancelled` as `OBSOLETE / NOT PASS`; do not use cancellation as a success signal.

## Suggested QA verification — before merge

- Review exact changed workflow YAML and expression syntax; verify group isolation by workflow, event, PR number or ref; confirm `cancel-in-progress` applies **only** to pull_request.
- Run existing full required checks on this PR's exact head and merge-ref. Verify no job name/required check is deleted, permissions are not broadened, and all A04/FullHD/Blender gates still execute when currently applicable.
- **If BA/T01/T02 authorize a controlled test:** use a dedicated test PR with two close-together pushes and observe previous same-workflow run cancellation while the current exact SHA finishes; check another PR and canonical postmerge runs are unaffected. No forced rerun just to manufacture evidence.
- Keep a rollback: revert this PR if newer runs are improperly canceled or current required checks become blocked.
- Measure wasted obsolete-run wall time, number of canceled runs, total CI duration for comparable PR updates, queue/runner-delay separately, and unresolved gate count after rollout. Baseline required; do not invent savings.

## Phase 2, only after BA+QA approval: smarter CI routing

Documentation-only PRs still trigger full Whiteboard CI, A04 and Dual workflows after Phase 1. To reduce **this** waste, BA/T01/T02 should separately review an event/changed-path classifier and required-status policy, then keep fast lint/contract checks on all PRs and schedule expensive media suites on relevant changes/Ready/final integration without producing a false green when FullHD **was not run**. Avoid workflow-level `paths-ignore` on required checks unless branch protection and pending/skipped behavior are explicitly verified. Do not silently mark `A04 full regression PASS` if media was bypassed. The T01 watcher is separately owned by [#59](https://github.com/qualife1291/Auto-Tool-Video/issues/59) / [#71](https://github.com/qualife1291/Auto-Tool-Video/issues/71) and not modified here.

## Reporting and coordination

BA01/BA02 remain co-equal, use the existing hourly watch as an accepted reconciliation loop; no new chatbot webhook/agent runtime or scheduled task is introduced. The Coder and QA communication contract remains Draft→Ready→exact-SHA independent QA→eligible merge→postmerge checks→separate creator G10. Owner approval is required for any changes that weaken approved gates, expose private data, broaden permissions or incur paid services.

**Source:** GitHub Actions concurrency and skipped-required-check behavior should be verified against current official GitHub documentation during BA/T01/T02 review.
