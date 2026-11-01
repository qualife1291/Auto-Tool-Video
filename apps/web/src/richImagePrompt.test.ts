import { describe, expect, it } from 'vitest';
import { RICH_DETAIL_MARKER, suggestDetailedImagePrompt } from './richImagePrompt';

const source = {
  title: 'Bay hơi',
  narration: 'Nước bay hơi từ sợi vải.',
  visual_description: 'Áo ướt treo ngoài sân, hơi ẩm bay lên.',
  image_prompt: 'Original cotton shirt on a clothesline',
};

describe('opt-in detailed illustration preset', () => {
  it('adds scene-specific actions, material details and phone legibility', () => {
    const result = suggestDetailedImagePrompt(source);
    expect(result).toContain(source.image_prompt);
    expect(result).toContain(source.visual_description);
    expect(result).toContain('foreground, midground and background');
    expect(result).toContain('fabric/material textures');
    expect(result).toContain('phone size');
    expect(result).toContain('No rendered text');
    expect(result.length).toBeLessThanOrEqual(2000);
  });

  it('does not duplicate or secretly start image generation on repeated suggestions', () => {
    const prompt = suggestDetailedImagePrompt(source);
    expect(suggestDetailedImagePrompt({ ...source, image_prompt: prompt })).toBe(prompt);
    expect(prompt.split(RICH_DETAIL_MARKER)).toHaveLength(2);
  });

  it('does not lose a long user-authored prompt or break server limits', () => {
    const longPrompt = 'H'.repeat(1999);
    expect(suggestDetailedImagePrompt({ ...source, image_prompt: longPrompt })).toBe(longPrompt);
  });

  it('provides meaningful scene context even without a starting prompt', () => {
    const result = suggestDetailedImagePrompt({
      title: 'Quạt mát',
      narration: 'Tắt quạt khi ra khỏi phòng.',
      visual_description: '',
      image_prompt: '',
    });
    expect(result).toContain('Quạt mát');
    expect(result).toContain('Tắt quạt khi ra khỏi phòng.');
    expect(result).toContain('generic icon');
  });
});
