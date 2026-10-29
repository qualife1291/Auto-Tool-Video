import { describe, expect, it } from 'vitest';
import { duration, preflight, sourceNeedsUpscale, type Project, type Scene } from './domain';
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
