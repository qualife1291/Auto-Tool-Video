/** An opt-in, editable art-direction suggestion, NOT a model-quality guarantee. */

import type { Scene } from './domain';

export const RICH_DETAIL_MARKER = '[Detailed story illustration preset v1]';

const ART_DIRECTION = [
  'High-detail original editorial illustration for an educational story.',
  'Show the specific action and objects described in this scene, not a generic icon.',
  'Use a coherent place with meaningful foreground, midground and background details.',
  'Believable geometry, accurate object proportions, fabric/material textures,',
  'fine yet readable line work, varied line weights, controlled lighting and shadows.',
  'Keep one dominant focal subject readable at phone size and fully inside the frame.',
  'Reserve margins for separately overlaid subtitles. No rendered text, logos or watermarks.',
  'Avoid repeated empty backgrounds, flat primitive clip art and duplicated generic symbols.',
  'Preserve character and object consistency across other scenes; no unsupported factual details.',
].join(' ');

export function suggestDetailedImagePrompt(
  scene: Pick<Scene, 'title' | 'narration' | 'visual_description' | 'image_prompt'>,
): string {
  const original = scene.image_prompt;
  if (original.includes(RICH_DETAIL_MARKER)) return scene.image_prompt;
  const focus = [scene.visual_description, scene.narration, scene.title]
    .map((value) => value.trim())
    .find(Boolean);
  const addition = [
    RICH_DETAIL_MARKER,
    `Scene: ${scene.title.trim().slice(0, 100)}.`,
    `Visible narrative action: ${(focus || '').slice(0, 240)}.`,
    ART_DIRECTION,
  ].join('\n');
  const enriched = [original.trim() ? original : '', addition].filter(Boolean).join('\n\n');
  // The server's ImageInput/Scene schema caps prompt length at 2,000 characters.
  // Never cut or silently discard any user-authored prompt to fit a preset.
  return enriched.length <= 2000 ? enriched : scene.image_prompt;
}
