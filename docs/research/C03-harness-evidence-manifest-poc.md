# C03 H1 — FREE-first evidence manifest and SDLC harness design spike

**State:** RESEARCH PROPOSED / DESIGN ONLY, no runtime or workflow implementation, no approval to deploy.  
**Owner:** C03 successor seat; **business acceptance:** BA01 + BA02 co-equal; **independent review/merge:** designated T01 or T02 with ONE QA_OWNER.  
**Assignment:** [#49](https://github.com/qualife1291/Auto-Tool-Video/issues/49); parent [#38](https://github.com/qualife1291/Auto-Tool-Video/issues/38).  
**Historical checkpoint (2026-10-31 ~03:4x ICT, not a live-state assertion):** At that checkpoint canonical `feat/short-video-studio` was **`fecfea79edab632da827507fb70c302e0acf824c`** after T01-QA-merged C03 #58/PR #67 and C01 #63. Earlier `980b7185b4cbcabf02d33edd1b4ba98ca9f89328` is another dated baseline. The later ~09:xx ICT evidence is listed below; all snapshots become historical when branches advance. **Read GitHub LIVE** before using any SHA, workflow verdict or QA decision.

## 2026-10-31 resumed-task verification ledger

- **BA authorization / personal role claim:** BA02 is equal to BA01 ([BA02 registry #72](https://github.com/qualife1291/Auto-Tool-Video/issues/72)); BA02 [unpaused/reassigned #49](https://github.com/qualife1291/Auto-Tool-Video/issues/49#issuecomment-6533037211) and C03 re-CLAIMED on issue #49. One exclusive new `docs/research/C03-harness-evidence-manifest-poc.md`; no runtime, code, workflow, credential, paid service or dependency edits.
- **Historical ~03:4x ICT canonical checkpoint (not latest):** `feat/short-video-studio` was `fecfea79edab632da827507fb70c302e0acf824c` (C03 #67 and C01 #63 integrated), [Main #41124112589 PASS](https://github.com/qualife1291/Auto-Tool-Video/actions/runs/41124112589), [Dual #41124112524 PASS](https://github.com/qualife1291/Auto-Tool-Video/actions/runs/41124112524). Earlier `980b7185...` references below are also historical.
- **Later 2026-10-31 ~09:xx ICT research PR gate (historical, verified before this clarification commit):** canonical `feat/short-video-studio` **`fd99764d738d0c16d0a2b60298bc123d3572fb0c`** after C04 #47/T01 merge; PR #65 was **Ready / NOT QA APPROVED** at exact HEAD **`b3bcd59cdefdcb096885ce6dc3f1e600a8b80304`**. Integration ref at that precise checkout was **`refs/pull/65/merge` = `5cf93a4808fd80a95b33e5f2fdf8c1436d276d9a`**. The head/current-base workflow evidence at that time was [Main #41155461051 SUCCESS](https://github.com/qualife1291/Auto-Tool-Video/actions/runs/41155461051) (410 pytest passed, 2 skipped; 10 Vitest and 15 Playwright passed), [A04 #41155460949 SUCCESS](https://github.com/qualife1291/Auto-Tool-Video/actions/runs/41155460949) and [Dual FullHD #41155461023 SUCCESS](https://github.com/qualife1291/Auto-Tool-Video/actions/runs/41155461023). [BA01/BA02 assigned QA_OWNER=T02](https://github.com/qualife1291/Auto-Tool-Video/pull/65#issuecomment-6536014966); independent T02 QA verdict was **PENDING/NOT RUN** at this snapshot. **After ANY later commit or canonical change, these SHAs and green checks are historical ONLY; new exact-head and current-base checks are mandatory.** No runtime implementation or G10 creator acceptance implied.
- **Resolved #58:** T01 [QA-PASS-CODE](https://github.com/qualife1291/Auto-Tool-Video/pull/67#issuecomment-6532584718) / merged #67 at `ba58bc8e9b48abdfd327d97b14d3e620c6795ace`, [postmerge Main PASS](https://github.com/qualife1291/Auto-Tool-Video/actions/runs/41121830700) and [Dual PASS](https://github.com/qualife1291/Auto-Tool-Video/actions/runs/41121830648). Historical #56 [main #41115725006](https://github.com/qualife1291/Auto-Tool-Video/actions/runs/41115725006) **ultimately FAILED** (asynchronous test read), rather than the old IN_PROGRESS snapshot. No traced HTTP HAR; no creator G10 signoff.
- **QA governance:** [#70](https://github.com/qualife1291/Auto-Tool-Video/issues/70) makes T01/T02 **co-equal independent QA and eligible merge**; *one assigned QA_OWNER per PR*, no auto double-signoff. BA01 and BA02 co-equal; no shared account attribution. The inert historic example JSON below intentionally refers to T01 on PR #56; it is **not** a recommendation that every future PR must use T01.
- **Open infra risks:** [#59](https://github.com/qualife1291/Auto-Tool-Video/issues/59) HTTP 403 watcher, Draft [PR #60](https://github.com/qualife1291/Auto-Tool-Video/pull/60); [#71](https://github.com/qualife1291/Auto-Tool-Video/issues/71) hardcoded stale coder/issue routing. QA/BA owns these; C03 is **read-only**. Historical #65 exact-head [Main PASS](https://github.com/qualife1291/Auto-Tool-Video/actions/runs/41116450620) + [Dual PASS](https://github.com/qualife1291/Auto-Tool-Video/actions/runs/41116450649) but [A04 FAIL](https://github.com/qualife1291/Auto-Tool-Video/actions/runs/41116450596); MUST rerun and report fresh exact-head integration, not reuse old green.
- **2026-10-31 official-source recheck:** [GitHub public standard runner billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions) is free but larger runners and artifact/storage have separate limits; exact account budgets and quotas **NOT VERIFIED**. [OpenHands MIT](https://github.com/OpenHands/OpenHands/blob/main/LICENSE), [Microsoft Agent Framework MIT](https://github.com/microsoft/agent-framework/blob/main/LICENSE), [Gemini CLI Apache-2.0](https://github.com/google-gemini/gemini-cli) and [June 18 Gemini CLI free-consumer cutoff](https://github.com/google-gemini/gemini-cli/discussions/28017) are verified upstream. These are license/terms facts, not a promise of free model inference, hosting or Antigravity quotas. No service installed or paid.
- **Research pilot boundary:** suggested manual manifest and negative cases S1–S5 remain **DESIGN ONLY / NOT RUN**. No changed CI workflow, runtime, auto-routing, external account or creator approval. Exact-head checks and independent QA follow a separately selected single QA_OWNER.

## Decision summary

**Recommendation:** retain GitHub-native issues, PRs, required checks, exact-SHA evidence and human BA01/BA02 business and T01/T02 independent QA decisions; design a small **optional human-authored JSON evidence manifest** stored as issue/PR text for comparison. No new workflow, bot, agent engine, credential, enforcement, hosted compute, or installation under #49. The earlier [C03 task-contract lint PoC](https://github.com/qualife1291/Auto-Tool-Video/blob/980b7185b4cbcabf02d33edd1b4ba98ca9f89328/docs/research/C03-dev-harness-contract-poc.md) parses **declared task contracts only**, and is **not** an authorized GitHub identity/CI/claim verifier.

The manifest proposed below is an evidence **index**, not a verdict or an executable contract. GitHub-native records and exact artifacts remain authoritative. Never turn a missing or stale result into PASS.

## 1. Real repo inventory and gaps (snapshot, not timeless state)

| SDLC area | Actually observed at audit | Gap / risk | Proposed non-enforcing response |
| --- | --- | --- | --- |
| Role governance, owner, claims | [Role charter](https://github.com/qualife1291/Auto-Tool-Video/blob/980b7185b4cbcabf02d33edd1b4ba98ca9f89328/docs/agent-role-charter.md), [BA registry #31](https://github.com/qualife1291/Auto-Tool-Video/issues/31), [C03 registry #28](https://github.com/qualife1291/Auto-Tool-Video/issues/28), claim in [#48](https://github.com/qualife1291/Auto-Tool-Video/issues/48), [C01 #55](https://github.com/qualife1291/Auto-Tool-Video/issues/55), [C02 #57](https://github.com/qualife1291/Auto-Tool-Video/issues/57), [C04 #61](https://github.com/qualife1291/Auto-Tool-Video/issues/61). Shared login does not identify seat. | Historic charter/workboard rows stale; two agents can declare overlapping paths; role identity unverified. | Pin role and explicit claim URL, owner ID and exclusive paths; BA01/BA02 recheck current claims. |
| Task lifecycle / PR | [#48→PR #56](https://github.com/qualife1291/Auto-Tool-Video/pull/56) used CLAIM → Draft → explicit Ready → T01 QA → merge. [PR #51](https://github.com/qualife1291/Auto-Tool-Video/pull/51) proposes role-charter refresh. | Ready does not imply CI passed or independent T01/T02 consent; historical statuses can outlive newer commits. | Separate draft/ready, code verdict, merge and creator verdict fields with timestamps and authoritative links. |
| Exact-head vs merge/postmerge | [PR #56](https://github.com/qualife1291/Auto-Tool-Video/pull/56) head **2c197a4042aeb974b42ad4a220e3ec3a6ed774da**; [main CI #41113943842](https://github.com/qualife1291/Auto-Tool-Video/actions/runs/41113943842) attempt 2, [dual #41113943967](https://github.com/qualife1291/Auto-Tool-Video/actions/runs/41113943967), [A04 #41113944178](https://github.com/qualife1291/Auto-Tool-Video/actions/runs/41113944178) SUCCESS on head. Merge **980b7185b4cbcabf02d33edd1b4ba98ca9f89328** is distinct. | Head green ≠ merged tree green. A main-CI rerun previously succeeded after intermittent Playwright failure; repeated evidence must preserve attempts. | One check record per workflow + SHA + attempt + conclusion + URL; postmerge gate separately evaluated at merge SHA. |
| Postmerge snapshot | On merge SHA, [Dual #41115724973](https://github.com/qualife1291/Auto-Tool-Video/actions/runs/41115724973) SUCCESS; [main #41115725006](https://github.com/qualife1291/Auto-Tool-Video/actions/runs/41115725006) was IN_PROGRESS at audit. | Never certify G11/postmerge before completion. | Explicit **NOT RUN/RUNNING**, then reread remote conclusion; preserve timestamp. |
| QA defects, repeatable RED | [Cross-lane #58](https://github.com/qualife1291/Auto-Tool-Video/issues/58) reports 390px/1366px beat persistence and focus E2E discrepancies; original root cause was not proven by a network trace, but C03 #58 identified premature GET before PUT; T01 independently QA-approved and merged test-only synchronization PR #67. No independent product runtime defect proven. | C04 #47 is QA blocked for unrelated E2E; incorrectly assigning a test failure to a coder/file can cause collisions. | Record exact failing test, expected/actual, run/attempt, actual task owner and exact evidence caveats; historical trace/HAR was **NOT RETRIEVED**. |
| Watcher, routing, spam | [.github/workflows/t01-pr-qa-watch.yml](https://github.com/qualife1291/Auto-Tool-Video/blob/980b7185b4cbcabf02d33edd1b4ba98ca9f89328/.github/workflows/t01-pr-qa-watch.yml) is **schedule + workflow_dispatch** only since [#43](https://github.com/qualife1291/Auto-Tool-Video/pull/43); on cron minutes 07/22/37/52 UTC, default-branch code scans open PR head checks, has comment dedupe markers, never auto-merges. | Historical watcher fallback hard-codes **C03/A02 #24** and **C04/A03 #25**, stale for #58/#61; T02 has filed independent [#71](https://github.com/qualife1291/Auto-Tool-Video/issues/71). No C03 research scope to edit watcher. Expected RED test phases could generate false blockers/spam. | A future T01-owned task may resolve lane via live claim/issue mapping; expected-RED status must be distinct from production CI red. **No edits here**. |
| Watcher permission failure | Scheduled [run #41113243273](https://github.com/qualife1291/Auto-Tool-Video/actions/runs/41113243273) FAIL after HTTP 403 comment write (see [T01 #59](https://github.com/qualife1291/Auto-Tool-Video/issues/59)); [T01 PR #60](https://github.com/qualife1291/Auto-Tool-Video/pull/60) Draft proposes fail-visible/read-only summary on denied write, not yet QA-certified. Earlier [run #41106235477](https://github.com/qualife1291/Auto-Tool-Video/actions/runs/41106235477) SUCCESS. | A configured issues:write stanza does NOT prove actual token can write. Failure can abort reporting to other agents. | Report DEGRADED / BLOCKED, retain read-only audit if possible; owner checks token policy with explicit authorization, no PAT workaround. |
| Durable handover | [AGENTS](https://github.com/qualife1291/Auto-Tool-Video/blob/980b7185b4cbcabf02d33edd1b4ba98ca9f89328/AGENTS.md), [.agent LATEST](https://github.com/qualife1291/Auto-Tool-Video/blob/980b7185b4cbcabf02d33edd1b4ba98ca9f89328/.agent/handover/LATEST.md), [workboard](https://github.com/qualife1291/Auto-Tool-Video/blob/980b7185b4cbcabf02d33edd1b4ba98ca9f89328/docs/agent-workboard.md), [T01 docs PR #46](https://github.com/qualife1291/Auto-Tool-Video/pull/46) separate. | Snapshots may lag GitHub issues. | Manifest records checkpoint/ref and last-read UTC; every successor must rerun live queries before writing. |
| Video jobs and QC (different harness) | [jobs.py](https://github.com/qualife1291/Auto-Tool-Video/blob/980b7185b4cbcabf02d33edd1b4ba98ca9f89328/backend/auto_tool_video/jobs.py) has request idempotency/hash, revision, frame limit, snapshot; [worker.py](https://github.com/qualife1291/Auto-Tool-Video/blob/980b7185b4cbcabf02d33edd1b4ba98ca9f89328/backend/auto_tool_video/worker.py) locks data dir and interrupts running jobs on restart; [QA gates](https://github.com/qualife1291/Auto-Tool-Video/blob/980b7185b4cbcabf02d33edd1b4ba98ca9f89328/docs/qa-evidence-gates.md) distinguish G1–G11 incl. media and creator G10. | An SDLC document cannot attest real video artifacts or Creator review. | Shared vocabulary only (SHA/status/attempt/idempotency). **No shared credential, token, execution right, job schema or approval**. |

**Observed run timestamps, not an uptime claim:** 15-minute watcher runs #41106235477 at 2026-10-30T18:21:28Z (SUCCESS, updated 18:21:41Z) and #41113243273 at 19:11:51Z (FAIL, updated 19:12:00Z). GitHub's scheduled events can be delayed/dropped under load: these two runs are **not** an empirical every-15-minute SLA, nor a representative latency benchmark. Actual watcher is currently not reliably delivering triage due to #59.

## 2. Evidence manifest v1 — **illustrative, inert JSON**

The object below is a **synthetic authoring example**, not a live API response, deployment config, trusted claim or verified PASS. The SHA fields are real example snapshots from #56, but statuses/links are mixed specifically to illustrate that code-PASS does not make postmerge and creator PASS. No source code may evaluate or execute the object.

~~~json
{
  "schema_version": 1,
  "purpose": "SDLC evidence index / proposal only",
  "task": {
    "issue_url": "https://github.com/qualife1291/Auto-Tool-Video/issues/48",
    "task_id": "C03-HARN-H01-CONTRACT-POC",
    "role_id": "C03",
    "identity_verified": false,
    "claim_comment_url": "https://github.com/qualife1291/Auto-Tool-Video/issues/48#issuecomment-6531075215",
    "spec_ref": "specs/whiteboard-video-tool.md",
    "spec_status_declared": "approved",
    "acceptance_criteria": ["Strict offline contract checks", "No automatic CI enforcement"],
    "exclusive_write_paths": ["scripts/dev_harness_contract.py", "backend/tests/test_dev_harness_contract.py", "docs/research/C03-dev-harness-contract-poc.md"],
    "dependencies": ["#38", "#45"],
    "next_owner": "T01"
  },
  "git": {
    "base_branch": "feat/short-video-studio",
    "base_sha": "2db0ba55ac1775f8d33b647bd62741ee4c6cba55",
    "feature_branch": "agent/C03-HARN-H01-task-contract-poc",
    "head_sha": "2c197a4042aeb974b42ad4a220e3ec3a6ed774da",
    "merge_sha": "980b7185b4cbcabf02d33edd1b4ba98ca9f89328",
    "pr_url": "https://github.com/qualife1291/Auto-Tool-Video/pull/56"
  },
  "evidence": [
    {"gate": "main-head", "status": "PASS", "sha": "2c197a4042aeb974b42ad4a220e3ec3a6ed774da", "attempt": 2, "run_url": "https://github.com/qualife1291/Auto-Tool-Video/actions/runs/41113943842", "artifact_sha256": null},
    {"gate": "postmerge-main", "status": "RUNNING", "sha": "980b7185b4cbcabf02d33edd1b4ba98ca9f89328", "attempt": 1, "run_url": "https://github.com/qualife1291/Auto-Tool-Video/actions/runs/41115725006", "artifact_sha256": null},
    {"gate": "manual-av", "status": "NOT_APPLICABLE", "sha": null, "attempt": null, "run_url": null, "artifact_sha256": null}
  ],
  "reviews": {
    "coder_self_test": "PASS_REPORTED",
    "t01_code_qa": "PASS",
    "t01_verdict_url": "https://github.com/qualife1291/Auto-Tool-Video/pull/56#issuecomment-6531763071",
    "creator_gate": "NOT_APPLICABLE",
    "release_approved": false
  },
  "recovery": {
    "checkpoint_key": "issue:48|head:2c197a4042aeb974b42ad4a220e3ec3a6ed774da|gate:main-head|attempt:2",
    "retry_count": 1,
    "retry_policy": "manual review of same-SHA flake; never weaken assertions",
    "last_observed_utc": "2026-10-30T19:30:45Z",
    "resume_requires": ["refresh GitHub issue/claim", "refresh PR base/head", "refresh exact run status", "check exclusive file ownership"]
  },
  "audit": {
    "source_of_truth": ["live issue/PR GitHub API", "exact-SHA workflow run", "independent T01 verdict"],
    "unverified": ["individual agent identity", "current branch freshness after snapshot", "user billing plan"],
    "rollback": "Stop manually emitting manifests; original GitHub records remain."
  }
}
~~~

**Validity contract (proposal, NOT implemented):** required keys, schema version, canonical 40-character SHA fields when present, exact run SHA equality, explicit workflow attempt, enum PASS / FAIL / BLOCKED / RUNNING / NOT RUN / NOT_APPLICABLE; unknown means **NOT RUN**, not PASS. Each artifact SHA256 must be 64 hexadecimal digits or null with **unverified** tag; a linked action artifact without a hash is never marked hash-verified. Reject duplicate task/owner path claims in combined views. No manifest may claim self-QA as independent T01/T02 QA, or present PR Ready as PASS. No secret values, raw client media, tokens or env dumps.

**Evidence priority:** (1) product-owner-approved spec and BA scope, (2) current GitHub issue CLAIM plus exact branch/PR snapshot, (3) exact-SHA run/attempt and artifact content hash, (4) designated T01/T02 independent decision, (5) G10 creator decision for AV, (6) release authorization. A manifest is a cross-reference; its fields can become **STALE** immediately. If a run lacks data, show NOT RUN or RUNNING and link the source.

### GitHub-native, read-only conceptual flow

~~~text
BA01/BA02 approved task/spec + exclusive path
              |
              v
C03 CLAIM (issue comment) -- check live base SHA + other PR ownership
              |
              v
C03 Draft PR -> RED reproduction (when bug) -> minimal fix/self-test
              |
              v
C03 Ready for review + exact-head evidence links
              |
              v
QA_OWNER (T01 or T02) reads exact-SHA runs, artifacts and owned paths
       | FAIL/BLOCKED             | PASS
       v                          v
C03 fix new SHA / new review      designated QA_OWNER authorized merge
                                  |
                                  v
                    merge-SHA CI + creator G10 if media
                                  |
                                  v
                    BA01/BA02 closes/continues task; release separately
~~~

**Checkpoint and idempotency proposal:** one logical observation identified by (repo, PR, head SHA, gate name, workflow run ID, attempt). On retry, first read the remote current PR head and run conclusion; a stale-head observation is historical only. Never create a new notification when an identical key has already been reported; changed conclusions on the **same** key become amendments, not duplicate comments. A permissions 403 is DEGRADED + BLOCKED; summary must not be silently suppressed. This is design guidance, **not** a deployed service.

## 3. FREE-first comparison of actual alternatives (official sources as of 2026-10-31)

| Alternative | Official code/license | Cost classification for this repo | Trust/security + migration |
| --- | --- | --- | --- |
| **Existing GitHub issue/PR text + manual evidence manifest** | Native GitHub current repo; no new dependency | **FREE VERIFIED** for this public repo's standard hosted runners; artifact storage/account spending must still be examined | Minimal change; BA/T01 remain final authority. Human omission/lag; mitigate with review checklist and explicit NOT RUN. **Recommended**. |
| **Optional Python standard-library checker from #48** | Already merged local script; Python stdlib, no new dependency | **FREE VERIFIED** as code execution offline; no usage-based model calls | Validates declared task fields only; cannot authenticate claims or fetch actual GitHub checks. Reversible by not invoking. |
| **OpenHands** | [Upstream repository](https://github.com/OpenHands/OpenHands) and [MIT license](https://github.com/OpenHands/OpenHands/blob/main/LICENSE) | **FREE WITH LIMITS**: OSS code free; model inference, hosting, hardware and agent execution not guaranteed free | May read/write files and invoke tools; requires sandbox, least privilege, supply-chain review, pinned version and independent QA. **Do not install**. |
| **Gemini CLI** | [Upstream](https://github.com/google-gemini/gemini-cli), [Apache-2.0/terms](https://github.com/google-gemini/gemini-cli/blob/main/docs/resources/tos-privacy.md) | **FREE WITH LIMITS / individual Gemini CLI free access ENDED.** Official [2026-06-18 upstream confirmation](https://github.com/google-gemini/gemini-cli/discussions/28017) reports Gemini CLI stopped serving individual free/Pro/Ultra users, redirecting them to Antigravity CLI. Enterprise/cloud/paid API key access remains. Antigravity quota and account eligibility are **NOT VERIFIED**. | OAuth/API + data processing terms; prompt and repo export risk. No connecting a provider or using credentials in #49. |
| **Microsoft Agent Framework** | [Official repository](https://github.com/microsoft/agent-framework), [MIT license](https://github.com/microsoft/agent-framework/blob/main/LICENSE) and [Python package](https://github.com/microsoft/agent-framework/blob/main/python/pyproject.toml) | **FREE WITH LIMITS**: SDK OSS, model/provider/cloud runtime may be paid | Overpowered for static manifest; multiple integrations expand dependency and attack surface. No installation. |

**Billing caveat, verified at primary official GitHub docs:** [GitHub Actions billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions) states standard hosted runners in **public repositories** are free and do not draw from included compute; larger runners are charged even on public repositories. [Included plan usage](https://docs.github.com/en/billing/reference/product-usage-included) now describes **dollar-denominated included compute** for applicable private/internal runner/cloud sandbox usage (e.g. GitHub Free $12/month), **not a guaranteed timeless 2,000-minute figure**. Storage is separately measured/accrued, artifacts share an allowance with Packages; an account's billing/spend-stop setting and whether a payment method is present were **NOT VERIFIED**. Owner should inspect its real Billing & licensing > Budgets and usage; configure an explicit **stop-usage** budget if needing a hard zero-overage policy, where supported. Do not use the public runner exemption to claim infinite artifacts, private runner quota, or zero cost for external AI services.

## 4. Watcher capacity, reliability, cost (calculate vs measure)

- Schedule on canonical: four checks/hour, **96 nominal checks per 24 h**, **2,880 nominal checks over a 30-day period**. This is requested cron frequency, **not observed runs** and not assurance of on-time delivery. GitHub official [scheduled-event docs](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule) and [troubleshooting](https://docs.github.com/en/actions/how-tos/troubleshoot-workflows) warn queued schedule events can be delayed and sometimes dropped.
- Current job has **10-minute per-run timeout** and public Ubuntu standard runner. The purely hypothetical max compute from every 10-minute timeout is **28,800 runner-minutes / 480 runner-hours in 30 days** (not actual observed usage, not necessarily billable standard-public runner usage). Duty cycle and total job runs depend on congestion, API rate limits and permissions.
- The two **observed** scheduled runs from API: #41106235477 SUCCESS over approximately **13 seconds** between created/updated timestamps; #41113243273 FAIL over approximately **9 seconds**. These timestamps are end-to-end record intervals, not billed runner duration, and two data points cannot prove typical cost/duration. If, hypothetically, every one of 2,880 runs took 9–13s wall time, that would be **7.2–10.4 hours monthly wall time**, **not an empirical performance measurement**.
- Head CI, dual1080/A04, scenario full-media, PR events and postmerge runs are **additional independent workloads**; budget/monitor their run IDs, bytes, retention and retry attempts. [#58](https://github.com/qualife1291/Auto-Tool-Video/issues/58) Playwright flakiness may cause expensive attempts; expected RED CI in development should not trigger repeated, misrouted bot comments.
- Known failure: watcher [#59](https://github.com/qualife1291/Auto-Tool-Video/issues/59) 403, [PR #60](https://github.com/qualife1291/Auto-Tool-Video/pull/60) Draft. Do not enable another frequent watcher or token, nor send repeated manual notifications while exact-head status is unchanged.

## 5. Acceptance matrix for an optional future manual pilot (NOT EXECUTED)

Use five sanitized, synthetic contracts/PR states; BA01 authors expected truth from GitHub and one designated independent QA owner (T01 or T02) verifies. **All outcomes below are proposed test oracles, not collected experiment results.**

| Case | Injected condition | Mandatory expected result |
| --- | --- | --- |
| S1 clean owner + head + current merge-ref | Approved task claim, no scope overlap, full head checks, distinct designated T01/T02 PASS, postmerge checks PASS | Correct route/owner; only the proven stage PASS; separate creator G10 if media |
| S2 stale-head | Stored green run at OLD commit after new push | **BLOCKED/NOT RUN** for current head; no reused PASS |
| S3 missing artifact hash | Head test PASS but mandatory video artifact absent/unverified | **NOT RUN** on artifact/QC; cannot mark video or release PASS |
| S4 duplicate ownership + expected RED | Two claims overlap path; one PR intentionally RED to demonstrate failure | **BLOCKED** until BA scopes; preserve RED proof and avoid wrong coder routing or duplicate failure comments |
| S5 GitHub QA PASS but creator not approved | Technical run green, manual G10 no reviewer/hash | **CREATOR PENDING**, no FEATURE-DONE-VERIFIED or RELEASE APPROVED |

**Target metrics (to test, not claim achieved):** at least 95% correctly routed true owner across labeled samples (expand beyond five to measure 95% meaningfully), **0 false PASS**, **0 duplicate notifications per observation key**, **100% explicit NOT RUN for missing evidence**, **$0 extra hosted Actions charge attributable to pilot** and **0 external model requests**. Establish manual GitHub checklist baseline and compare reviewer minutes, false positives, elapsed duration, flakes/retries and bytes retained. Collect enough labeled cases for confidence; five pilot cases cannot estimate a 95% rate precisely. Record actual observations, hardware/runner, SHA and run IDs before promoting a claim.

## 6. Risk register, rollout boundary and rollback

1. **Misattribution/identity:** A shared GitHub user or role text cannot authenticate BA01/C03/T01. BA maintains explicit task claims; T01 independently signs QA. **No self-review or automatic merge**.
2. **Privilege, secrets and untrusted content:** issue/PR text, web research, models, and outside tools are untrusted data. JSON examples are inert. No PAT, token, env dump, user audio, model weights, external skill execution or GitHub write automation installed. Enforce least privilege only in a separately authorized implementation project.
3. **Stale/incomplete results:** a previously green SHA does not approve a new head or merge. Preserve attempts, FAIL, skipped, cancelled and NOT RUN; a retry does not erase original RED evidence.
4. **Watcher spam/403/misrouting:** existing [#59](https://github.com/qualife1291/Auto-Tool-Video/issues/59) and stale A02/A03 hardcoded labels need a T01/BA-owned ticket; do **not** modify their workflow under C03 research scope.
5. **Costs/license and data governance:** local OSS software can still incur model, GPU, cloud compute, artifact retention, storage or operational cost. Require dated license and provider terms, hardware and privacy audit before an implementation plan.
6. **Rollback:** do not opt in to a runtime or workflow under this PR. Delete/stop using the manual manifest proposal and return to the existing GitHub issue/PR checklist; no runtime migration or service teardown. If future pilot approved, first timebox it behind an explicit BA task and allow manual deactivation without losing evidence history.

**Definition of done for THIS issue:** a single Markdown research deliverable, official source/date matrix, demonstrated GitHub state and explicit NOT RUN boundaries, synthetic manifest and test plan, no runtime/workflow changes, docs-only PR for BA01/BA02 acceptance and T01/T02 independent review. Research proposal ≠ code implementation, QA release sign-off or change to approved Whiteboard Studio spec.
