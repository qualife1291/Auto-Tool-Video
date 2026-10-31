# C03 P1 #58 — Beat-persistence test synchronization investigation

**State:** implementation experiment in isolated test-only PR, **T01 QA PENDING**. No production defect attribution; test synchronization gap is confirmed by direct code inspection, but a separate application race is not ruled out.  
**Snapshot:** 2026-10-31 Asia/Ho_Chi_Minh; GitHub timestamps UTC 2026-10-30.  
**BA owner:** BA01. **Coder:** C03 successor. **Independent QA/merge:** T01.  
**Task:** [#58](https://github.com/qualife1291/Auto-Tool-Video/issues/58). **Current canonical base at claim:** `980b7185b4cbcabf02d33edd1b4ba98ca9f89328`, [C03 CLAIM](https://github.com/qualife1291/Auto-Tool-Video/issues/58#issuecomment-6531883183). P2 [#49](https://github.com/qualife1291/Auto-Tool-Video/issues/49) explicitly paused/released; [Draft PR #65](https://github.com/qualife1291/Auto-Tool-Video/pull/65) parked. Exclusively changed existing `apps/web/e2e/beat-persistence.spec.ts` and this NEW note. No C02 `main.tsx`/domain, C04 backend/media, T01 CI/workflows or shared docs changes.

## 1. Real failing evidence — no hidden test weakening

| Source | Exact head/branch | Observed result | What this proves |
| --- | --- | --- | --- |
| [C04 #47 main CI #41111160865](https://github.com/qualife1291/Auto-Tool-Video/actions/runs/41111160865) | `bdb6a29763b575ac9e5aa26d74899a3ff11bffd0` | At 390px `beat-persistence.spec.ts:99`: expected `authored` after explicit review/save, got `needs_review`; **14/15 browser E2E** | The browser test failed even though PR #47 only touches Fit Audio API/test; not proof of C04 Fit Audio regression |
| [BA01 #51 A04 #41113725342](https://github.com/qualife1291/Auto-Tool-Video/actions/runs/41113725342) | `016f2b70cee0e282b5091f428b48d243dd65bb9e` | 390px wrong `needs_review` at narration, 1366px wrong `authored` at review; 12/15 E2E; one `studio.spec.ts:114` outline assertion failed | Same test has failures at different transitions across unrelated PR heads; focus assertion is a separate issue with different file ownership |
| [C03 #56 attempt-1 main #41113943842](https://github.com/qualife1291/Auto-Tool-Video/actions/runs/41113943842) | `2c197a4042aeb974b42ad4a220e3ec3a6ed774da` | Main attempt 1 390px fail (14/15), attempt 2 on **identical head** SUCCESS without changing tests | Strong evidence of timing sensitivity, not an isolated code regression |
| [C03 #56 postmerge main #41115725006](https://github.com/qualife1291/Auto-Tool-Video/actions/runs/41115725006) | `980b7185b4cbcabf02d33edd1b4ba98ca9f89328` | At 1366px `beat-persistence.spec.ts:80`: expected `needs_review`, got `authored`; **14/15 E2E**. [Dual #41115724973](https://github.com/qualife1291/Auto-Tool-Video/actions/runs/41115724973) succeeded. | Confirmed defect is present on **canonical postmerge**, not only PR #47. Does not identify underlying UI/HTTP cause. |

Log source: GitHub job logs for IDs `124256294544`, `124262420556`, `124269336512`. At time of this report, GitHub runs did not expose test-results zip artifacts through the connector; Playwright logs contain local runner paths to `trace.zip`, screenshots and `error-context.md`, but **the actual trace bytes, network HAR and screenshots have NOT BEEN RETRIEVED**. Do not claim trace inspection or measured HTTP timeline.

## 2. Causal isolation from source (read-only on production)

Source reviewed at canonical: [E2E beat persistence](https://github.com/qualife1291/Auto-Tool-Video/blob/980b7185b4cbcabf02d33edd1b4ba98ca9f89328/apps/web/e2e/beat-persistence.spec.ts), and [UI `main.tsx`](https://github.com/qualife1291/Auto-Tool-Video/blob/980b7185b4cbcabf02d33edd1b4ba98ca9f89328/apps/web/src/main.tsx) (READ ONLY).

- The original test triggers Save via `await page.getByRole('button', { name: 'Lưu thay đổi' }).click()`, **then immediately runs a separate GET** to inspect state, at the same assertions that fail (original lines 80, 99, 109). A Playwright click waits for a click to dispatch, **not** necessarily for its async `onClick` task/HTTP PUT to finish. The test has no request-completion synchronization at those points. This is a demonstrable missing happens-before barrier.
- Production `save()` in `main.tsx:164–185` awaits the PUT response, refreshes, then sets the notice `Đã lưu trên máy.`; the click runs through `task(async () => await save())`. Thus a GET immediately after `click` can inspect the **previous** persisted revision while PUT is still in flight.
- `updateScene()` in `main.tsx:191–209` intentionally invalidates `beat_plan_status` to `needs_review` on duration/narration changes. The review button intentionally sets it to `authored`. **Those invariants are retained in full.**
- The existing test also used a UI notice barrier only for its **first** save; later save paths had no equivalent. The opposite observed statuses are consistent with reading an earlier revision. **This mechanism is supported by source and changing assertions, but not a captured live network trace.** If errors persist after exact-request synchronization, investigate a genuine app race; do not alter product logic without BA01 expanding scope.

## 3. Minimal permitted test-only change, without hiding defects

On branch `agent/C03-P1-beat-persistence-race`, a shared Playwright `saveAndRead` helper:

1. Registers a `page.waitForResponse` listener **before** clicking Save; matches exactly `PUT /api/projects/:id` and verifies the response is OK.
2. Requires the returned project revision strictly **increase**, and the **PUT response scene status** exactly match the expected `authored` or `needs_review`.
3. Waits for the UI `Đã lưu trên máy.` indicator, then independently GETs `/api/projects/:id` and verifies **the same revision and expected scene status**. There is **no** polling until arbitrary expected state, delay/sleep, skip, retry of save, timeout increase, status weakening or production edit. A genuine app wrong-state save **still fails immediately on PUT response**.
4. Retains actual `second_by_second[0].action` text assertions (Vietnamese), all three beat entries and every transition `authored → needs_review → needs_review → authored → needs_review`, at **390 and 1366px**.

**Risk/limit:** a browser may emit multiple identical endpoint PUTs; binding to the exact triggered click plus comparing strictly increased revision and GET equality will expose unexpected conflicting updates rather than certify them. Perceived user-facing latency is not measured by these checks. No artificial waiting or disabled assertions.

## 4. Verification ledger (honest, update upon CI completion)

| Gate | At initial patch | Expected next evidence |
| --- | --- | --- |
| Existing RED on unmodified baseline | **OBSERVED** multiple GitHub jobs in §1, not personally reproduced locally | Preserve links, exact SHA and failure stage |
| Local focused `npm --prefix apps/web run test:e2e -- --grep "edited second-by-second beat"` x3 at each viewport | **NOT RUN** — container `git ls-remote` DNS error (`Could not resolve host: github.com`), no mounted repository or isolated local full-stack installation | Controlled runner evidence if available; no invented repeats |
| Source/static review | **DONE** for permitted E2E helper and read-only UI, no C02 edits | T01 verify at current PR head |
| PR exact-head Main/dual/A04 | **NOT RUN** until PR opens; check actual IDs/conclusions after triggering | Only exact-head SUCCESS can justify Ready, and G11 requires postmerge SHA |
| Human creator review | **NOT APPLICABLE** to test-only fix; remains separate for audiovisual release | No release claims |

**Next:** create scoped Draft PR; watch exact-head CI, distinguish Main/A04 green from any other real UI failures, and do at least 3 bounded observed test executions per viewport if a focused runner becomes available. If CI still fails after waiting for actual PUT and matching GET, capture exact failing status/revision and route an app-code investigation to BA01 with independently allocated non-C02 scope. Only C03 may mark Ready after reproducible evidence; only T01 may QA/merge after proper review.

**Rollback:** revert only the E2E helper change on the feature branch or abandon the PR; no schema, runtime, workflow, migration, cost or credential change.
