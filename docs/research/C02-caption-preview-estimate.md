# C02 — A03 estimated caption pages: renderer contract and manual QA

**Issue:** [#57](https://github.com/qualife1291/Auto-Tool-Video/issues/57) ·
**PR:** [#62](https://github.com/qualife1291/Auto-Tool-Video/pull/62) ·
**Owner:** C02 · **Independent QA:** T01.
This research note belongs to C02's exclusive NEW documentation scope. It does not
change the renderer, API, persisted Scene schema or release rules.

## Source-path contrast

| Characteristic | Exported MP4 | Editor preview |
| --- | --- | --- |
| Implementation | `backend/auto_tool_video/render.py::caption_pages`, `ScenePainter.draw_caption` | `apps/web/src/domain.ts::estimateCaptionPages`, `main.tsx` |
| Width | Actual canvas caption box in export coordinates, scaled for renderer | Fixed conservative Unicode code-point budget (portrait 28; landscape 48) |
| Text measurement | Pillow/FreeType `ImageFont.getlength`, bundled NotoSans font | JavaScript `Array.from(text).length`, without matching actual glyph widths |
| Page balancing | Font-measured, global candidate partition and orphan penalty | Greedy two-line groups, limited final-pair rebalance |
| Display timing | Export frame progress chooses a page | User manually navigates Previous/Next; not synchronized to audio |
| Source of truth | Final encoded MP4; human visual/audio review separate | **Approximate**, explicitly labeled as such |

The editor formerly rendered the entire `scene.narration` as one clipped
`.portrait-caption`; the export renderer showed only one 1–2-line cue page
per frame segment. The editor now previews *estimated* pages, including
`Trang hiện tại/tổng số (ước lượng)` and **Ước lượng — xem video xuất để xác nhận**.
Caption style/card/contrast/accent and emphasis remain a per-visible-page concern;
the stored narration is not paginated or replaced.

## Decision and alternatives

1. **Old full-text mock:** trivial but visually dishonest and clips long narration.
2. **Client-only estimated pages (chosen):** deterministic, no backend write,
   no server request or dependencies; communicates its approximation honestly.
3. **Exact server pagination metadata (deferred):** could share real FreeType
   metrics, but adds an API/backend interface, caching, font-version/aspect
   consistency concerns, and crosses the approved #57 file boundary. If product
   later requires frame-accurate preview, BA01 should scope a separate contract
   including font/render version and exact-head dual-aspect regression tests.

## Explicit limits and safeguards

- The approximate budget counts Unicode **code points**, not graphemes or
  pixel widths; Vietnamese combining accents, kerning, wide punctuation,
  CSS fonts and display sizes can differ from server FreeType.
- A single uninterrupted token longer than the nominal line budget is kept
  **intact**, not silently truncated or mutated by the algorithm. Such a token
  may visually wrap inside the bounded caption area; neither two actual DOM
  lines nor exact export equivalence can be promised for pathological input.
  For intended readable captions, split very long compound words at real word
  boundaries or verify exported MP4. Avoid manufacturing spaces in saved text.
- Whitespace is normalized **only inside the preview estimate**, not in the
  stored `scene.narration`. Joining estimated pages with normalized spaces
  recovers the same ordered words/punctuation; Unicode content is unchanged.
- Page navigation is independent of export timing and does not seek any media.
  Buttons have descriptive labels, normal focus/keyboard behavior, and disabled
  boundaries. Changing scene, narration or aspect resets to page 1.
- No exact pixel parity is asserted. Horizontal/vertical preview scaling and
  390px/1366px browser viewports are not Pillow 1080p font measurements.
- Browser preview controls and safe-zone guide are never burned into the MP4.

## Tests and manual creator review

**Automated:** Vitest covers empty/short, accent phrase, Unicode, punctuation,
different aspects, multi-page determinism, pathological tokens and orphan
last-page behavior. Playwright at 390px portrait and 1366px landscape verifies
long real Vietnamese narration, visible honest disclaimer, keyboard navigation,
page counter, reset on narration edit, and persistence of entire original
narration after save/reload. This is not a substitute for G10 human review.

**Manual test, before creator approval:**

1. Open a project in **Kịch bản**, enter one 250–500-character Vietnamese
   paragraph about áo ướt/bay hơi with punctuation and accents; split to
   storyboard. Preview must show only page 1, a count and an estimate notice.
2. On 390px portrait, activate **Tiếp** by keyboard, then **Trước**, confirm
   the caption changes without editing the narration field and controls remain
   accessible/focusable. Repeat on desktop with 16:9 aspect.
3. Change caption style among card/contrast/accent. With accent, choose a
   phrase visible on a specific page; check it is not highlighted on unrelated
   pages. Edit narration while on page 2 and verify the counter resets.
4. Save, reload, reopen project; confirm the full original input remains
   present and selected style is preserved. Export both 9:16 and 16:9 MP4,
   watch page breaks and safe zones at actual 1080p, and record any mismatches
   as expected preview limitations or separate renderer defects.
5. Human creator approval for font readability, timing and audio remains
   separate. A green synthetic/engineering video smoke is **not** G10 approval.

**QA coordination:** C03 owns beat-persistence issue #58; test sync changes
remain outside C02's claim. T01 must run applicable exact-head/merge-ref CI
before independent QA and merge. No skipped or weakened required assertions.
