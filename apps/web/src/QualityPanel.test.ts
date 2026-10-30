import { expect, it } from 'vitest';
import { reviewDraft } from './QualityPanel';

it('a saved review can be edited again without sending server metadata to a strict API', () => {
  const saved = {
    ...reviewDraft(null),
    reviewer: 'Creator',
    saved_at: '2026-10-30T05:00:00Z',
    criteria: {
      prompt_alignment: { score: 5, critical: false, at_seconds: null, note: 'Đã đối chiếu.' },
    },
  };
  const edited = reviewDraft(saved);
  expect(edited.reviewer).toBe('Creator');
  expect(edited.criteria.prompt_alignment?.note).toBe('Đã đối chiếu.');
  expect(JSON.stringify(edited)).not.toContain('saved_at');
  expect(edited.watched_full).toBe(false);
});
