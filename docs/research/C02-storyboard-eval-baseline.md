# C02 PPL-01 — Offline Vietnamese storyboard evaluation baseline

**Task:** [#84](https://github.com/qualife1291/Auto-Tool-Video/issues/84) · **Role:** C02 · **Classification:** deterministic Tier-A structural tests, **not** an evaluation of an actual Ollama or other LLM.  
**Authorization:** product owner explicitly directed C02 to execute in the live session after previous BA HOLD; exception and reviewer/CI capacity reconciliation are recorded on #84. PR must remain **Draft** until a single independent `QA_OWNER` is formally set and new exact-head CI is reviewed. Do not treat owner direction as an independent BA release comment.

## Scope and frozen oracle

Exactly three new paths: `backend/tests/fixtures/storyboard_eval_cases.json` (source data), `backend/tests/test_storyboard_eval_baseline.py` (pytest contract test), this research report. No production source/CI/workflows/provider/other seats modified; no external calls or paid compute. Data license **CC0-1.0**: entirely fictional, newly authored Vietnamese test stories with no user text or scraped material, seed `20261031`, schema `1`, case IDs P01..P20/N01..N20. The fixture JSON records project, storyboard proposal, independent expected results/exception class, source provenance and case reason. Expected narration and per-scene status are **fixed literals**, not copied from the validator's outputs.

| Coverage | Values | Cases / special oracles |
| --- | --- | --- |
| 5 profiles | `preschool`, `kids`, `older_kids`, `family`, `general` | P01–P20 (four per profile) |
| Aspects | `portrait`, `landscape` | Both; no visual or pixel-score claim |
| Modes | `preserve`, `brief` | Source chunks vs generated speech separately |
| Valid targets | 30, 45, 60 seconds | P01 is **12 seconds aggregate** with target 30 |
| Invalid target | 12 | N18 rejects via `ProjectInput` Pydantic, not planner target |
| Authored beats | `0..ceil(scene_duration)-1` | P02 fractional 3.3s/4 beats, P03 20s/20 beats, P12 5.2s/6 beats |
| Review-only compatibility | missing beats → generated placeholders | P04 accepts `needs_review`, not `authored` |
| Source binding | `source_ids` vs `source_refs` distinct | P01/P05/P07/P09/P15/P17; N01–N10 |
| Negative contract | duplicate, missing, reordering, coercion, schema, duration, JSON | N01–N20, exact error classes |

**Pairwise coverage only.** The 40 cases are not the 5×3×2×2 full Cartesian space. In preserve mode `source_ids` must enumerate all `source_chunks` once and in order, retaining Vietnamese whitespace/punctuation when grouped; `source_refs` indexes only unverified `CreativeBrief.sources`. Brief mode requires nonempty narration and `source_ids=[]`. Explicit missing/reordered/duplicate beats must error; absent beats are accepted as `needs_review`. Durations are 1–20s per scene; aggregate must be at most target duration.

## Local offline reproduction

From repo root, with installed existing project dependencies (no downloads by this evaluator):

```bash
uv run --project backend pytest -q -s backend/tests/test_storyboard_eval_baseline.py
uv run --project backend pytest -q backend/tests/test_ai.py backend/tests/test_storyboard_beats.py
uv run --project backend ruff check backend/tests/test_storyboard_eval_baseline.py
uv run --project backend ruff format --check backend/tests/test_storyboard_eval_baseline.py
sha256sum backend/tests/fixtures/storyboard_eval_cases.json
```

`STORYBOARD_EVAL_FIXTURE_SHA256` is printed by the metadata test for exact-byte provenance, independently verifiable by `sha256sum`. Do not substitute a manually guessed hash. Runner CI uses the existing `.github/workflows/ci.yml`; **no new workflow** is added.

## Results, limitations and evidence ledger

| Gate | Result as authored | Interpretation |
| --- | --- | --- |
| Fixture suite 20 valid + 20 negative | **NOT RUN** until actual CI/pytest execution | Frozen expectations only; no fictitious pre-fix RED |
| Existing Python/format/mypy/web checks | **NOT RUN** at authoring | Require exact commit/head evidence |
| A04 FullHD / Dual | **NOT RUN** at authoring | PR review requires current merge-ref checks |
| Native science/semantics/causal and character continuity | **NOT MEASURED / MANUAL REVIEW** | A validator cannot prove science or creative quality |
| 30fps timing | **NOT MEASURED** by planner evaluator | `frames_for()` belongs to rendering; planner is seconds/beats |
| Actual model quality p50/p95, latency, token/cost | **NOT RUN / DEFERRED** | No Ollama/Comfy/live model or paid service calls |
| Human creator G10 + source rights + release | **PENDING HUMAN REVIEW** | No automatic release authorization |

**Observed values must be recorded only after real tests/CI** (case count and PASS/FAIL/SKIP; fixture SHA-256; Python/tool versions; exact PR head/merge-ref and workflow links). A negative fixture passing proves the evaluator catches malformed contracts, **not** a product regression or a true semantic quality score. The existing generation retry mechanism and persistence guarantees are separate tested contracts, not automatically claimed by these 40 examples.

**Next gate:** independent BA01/BA02 reconciliation of owner-requested priority override; finalize one T01 or T02 `QA_OWNER`, check P1 #86/#59, exact current base and Main/A04/Dual before Draft→Ready. C02 never self-merges.
