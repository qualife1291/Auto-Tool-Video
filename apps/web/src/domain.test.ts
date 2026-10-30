import { describe, expect, it } from 'vitest';
import {
  captionParts,
  estimateCaptionPages,
  duration,
  preflight,
  sourceNeedsUpscale,
  type Project,
  type Scene,
} from './domain';
const scene: Scene = {
  id: 's',
  title: 'Áo ướt',
  narration: 'Nước đi đâu?',
  image_prompt: '',
  image_id: 'image',
  audio_id: null,
  audio_stale: false,
  duration: 3,
  style: 'whiteboard',
};
const project: Project = {
  id: 'p',
  title: 'Bay hơi',
  profile: 'family',
  platform: 'shorts',
  narration: 'Nước đi đâu?',
  revision: 0,
  aspect: 'portrait',
  scenes: [scene],
  created_at: '',
  updated_at: '',
};
describe('export readiness', () => {
  it('requires audio unless silent was explicitly selected', () => {
    expect(preflight(project, false)).toContain('Cảnh 1: chưa có giọng đọc.');
    expect(preflight(project, true)).toEqual([]);
  });
  it('requires actual images even in silent mode', () => {
    expect(preflight({ ...project, scenes: [{ ...scene, image_id: null }] }, true)).toContain(
      'Cảnh 1: chưa có ảnh.',
    );
  });
  it('blocks stale audio and a timeline above the common short preset', () => {
    expect(
      preflight({ ...project, scenes: [{ ...scene, audio_id: 'a', audio_stale: true }] }, false)[0],
    ).toMatch('đã đổi');
    expect(preflight({ ...project, scenes: Array(21).fill(scene) }, true)[0]).toMatch('60 giây');
  });
  it('adds actual scene durations', () =>
    expect(
      duration([
        { ...scene, duration: 1.5 },
        { ...scene, duration: 2.2 },
      ]),
    ).toBeCloseTo(3.7));
});

it('warns based on contain scaling rather than a fixed source dimension', () => {
  expect(sourceNeedsUpscale(800, 1200, 'portrait')).toBe(false);
  expect(sourceNeedsUpscale(640, 360, 'landscape')).toBe(true);
  expect(sourceNeedsUpscale(1920, 1080, 'landscape')).toBe(false);
});

it('warns when full frame cover needs upscale even though the old board did not', () => {
  expect(sourceNeedsUpscale(800, 1200, 'portrait', 'full_frame', 'cover')).toBe(true);
  expect(sourceNeedsUpscale(1920, 1080, 'portrait', 'full_frame', 'cover')).toBe(true);
  expect(sourceNeedsUpscale(1080, 1920, 'portrait', 'full_frame', 'cover')).toBe(false);
  expect(sourceNeedsUpscale(1920, 1080, 'portrait', 'full_frame', 'contain')).toBe(false);
});

describe('caption emphasis', () => {
  it('matches accented Vietnamese and preserves all original text', () => {
    const text = 'Đây là Bay Hơi, không phải khói.';
    const parts = captionParts(text, 'bay hơi');
    expect(parts.map((part) => part.text).join('')).toBe(text);
    expect(parts.filter((part) => part.emphasis).map((part) => part.text)).toEqual(['Bay Hơi']);
  });
  it('treats regex and HTML characters as literal content', () => {
    expect(captionParts('A .* <img> B', '.* <img>').filter((part) => part.emphasis)[0].text).toBe(
      '.* <img>',
    );
    expect(captionParts('Nước đi đâu?', '.*').some((part) => part.emphasis)).toBe(false);
  });
  it('keeps unmatched or empty emphasis as plain text', () => {
    expect(captionParts('Nước bay hơi.', '')).toEqual([{ text: 'Nước bay hơi.', emphasis: false }]);
    expect(captionParts('Nước bay hơi.', 'lửa')).toEqual([
      { text: 'Nước bay hơi.', emphasis: false },
    ]);
  });
});

describe('estimated caption pages (browser preview, not pixel-exact export)', () => {
  const long =
    'Áo vừa giặt còn ướt, nhưng một lúc sau lại khô. ' +
    'Các phân tử nước chuyển từ mặt vải vào không khí. ' +
    'Gió đưa lớp không khí ẩm đi xa, giúp nước tiếp tục bay hơi. ' +
    'Không khí ẩm quá mức sẽ làm áo khô chậm hơn ngay cả khi trời ấm.';

  it('returns no overlay for empty narration and leaves a short cue unchanged', () => {
    expect(estimateCaptionPages('', 'portrait')).toEqual([]);
    expect(estimateCaptionPages('   \n\t  ', 'landscape')).toEqual([]);
    for (const aspect of ['portrait', 'landscape'] as const) {
      expect(estimateCaptionPages('Nước bay hơi.', aspect)).toEqual(['Nước bay hơi.']);
    }
  });

  it('preserves every Vietnamese word and punctuation in two-line estimated pages', () => {
    for (const aspect of ['portrait', 'landscape'] as const) {
      const pages = estimateCaptionPages(long, aspect);
      expect(pages.length).toBeGreaterThan(1);
      expect(pages.every((page) => page.split('\n').length <= 2)).toBe(true);
      expect(pages.join(' ').replace(/\s+/gu, ' ')).toBe(long);
      expect(estimateCaptionPages(long, aspect)).toEqual(pages);
    }
    expect(estimateCaptionPages(long, 'portrait').length).toBeGreaterThanOrEqual(
      estimateCaptionPages(long, 'landscape').length,
    );
  });

  it('normalizes whitespace without changing diacritics, hyphenated words or token order', () => {
    const input = '  Nước   bay-hơi\n  rất   nhẹ.  Cây uống nước\t  mỗi ngày! ';
    const pages = estimateCaptionPages(input, 'portrait');
    expect(pages.join(' ').replace(/\s+/gu, ' ')).toBe(
      'Nước bay-hơi rất nhẹ. Cây uống nước mỗi ngày!',
    );
    expect(pages.join(' ')).toContain('bay-hơi');
  });

  it('preserves unbroken long Unicode tokens without silently dropping characters', () => {
    const token = 'Nước-'.repeat(25) + 'hoà';
    for (const aspect of ['portrait', 'landscape'] as const) {
      const pages = estimateCaptionPages(token, aspect);
      expect(pages.join(' ')).toBe(token);
      expect(estimateCaptionPages('  ' + token + '  ', aspect)).toEqual(pages);
    }
  });

  it('avoids a one-word last page when a balanced split fits in two lines per page', () => {
    const narration = Array(11).fill('Nước').join(' ');
    const pages = estimateCaptionPages(narration, 'portrait');
    expect(pages).toHaveLength(2);
    expect(pages[1].split(/\s+/u).length).toBeGreaterThanOrEqual(3);
    expect(pages.join(' ').replace(/\s+/gu, ' ')).toBe(narration);
  });

  it('does not emphasize a phrase on an unrelated page', () => {
    const text = 'hơi nước mở đầu câu chuyện. ' + long;
    const pages = estimateCaptionPages(text, 'portrait');
    const parts = pages.flatMap((page) => captionParts(page, 'hơi nước'));
    const emphasized = parts.filter((part) => part.emphasis);
    expect(emphasized.map((part) => part.text)).toEqual(['hơi nước']);
    expect(
      captionParts('Nước bay hơi.', 'bay hơi')
        .map((part) => part.text)
        .join(''),
    ).toBe('Nước bay hơi.');
  });
});
