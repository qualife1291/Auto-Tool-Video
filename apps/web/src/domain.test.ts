import { describe, expect, it } from 'vitest';
import {
  captionParts,
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
