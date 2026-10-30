import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { resolve } from 'node:path';
import { readFile } from 'node:fs/promises';

const caps = {
  script: { state: 'ready', message: 'Planner contract fixture', model: 'test-model' },
  image: { state: 'ready', message: 'Image contract fixture' },
};
const scene = {
  id: 'proposed-scene',
  title: 'Nước đi đâu?',
  narration: 'Nước đi vào không khí.',
  image_prompt: 'Original blue shirt illustration',
  duration: 4,
  style: 'whiteboard',
  image_id: null,
  audio_id: null,
  audio_stale: false,
  visual_description: 'Một chiếc áo xanh',
  reveal_order: ['áo', 'không khí'],
  fact_flags: ['Cần người lớn kiểm nội dung.'],
};

for (const viewport of [
  { width: 1366, height: 900 },
  { width: 390, height: 844 },
]) {
  test(`mock planner proposal needs review, survives reload, applies at ${viewport.width}`, async ({
    page,
  }) => {
    await page.setViewportSize(viewport);
    await page.route('**/api/capabilities', (route) => route.fulfill({ json: caps }));
    let projectId = '';
    let revision = 0;
    const job = () => ({
      id: 'mock-plan',
      project_id: projectId,
      revision,
      state: 'succeeded',
      options: { kind: 'plan', mode: 'brief' },
      result: {
        proposal: {
          title: '<img src=x onerror=alert(1)>',
          mode: 'brief',
          source_preserved: false,
          scenes: [scene],
        },
      },
    });
    await page.route('**/api/projects/*/plan', async (route) => {
      projectId = route.request().url().split('/').at(-2)!;
      revision = route.request().postDataJSON().revision;
      await route.fulfill({ status: 202, json: { ...job(), state: 'queued', result: null } });
    });
    await page.route('**/api/jobs/mock-plan', (route) => route.fulfill({ json: job() }));
    await page.route('**/api/projects/*/plans/mock-plan/apply', async (route) => {
      const response = await page.request.get(`/api/projects/${projectId}`);
      const p = await response.json();
      await route.fulfill({ json: { ...p, revision: revision + 1, scenes: [scene] } });
    });
    await page.goto('/');
    await page.getByRole('button', { name: 'Tạo câu chuyện đầu tiên' }).click();
    await page.getByLabel('Tên dự án').fill(`AI review ${viewport.width}`);
    await page.getByLabel('Chủ đề', { exact: true }).fill('Bay hơi');
    await page.getByRole('button', { name: 'Tạo đề xuất AI', exact: true }).click();
    await expect(page.locator('.proposal-review')).toBeVisible();
    await expect(page.locator('.proposal-review h3')).toHaveText('<img src=x onerror=alert(1)>');
    await expect(page.locator('.proposal-review h3 img')).toHaveCount(0);
    await expect(page.getByRole('button', { name: 'Áp dụng storyboard đã duyệt' })).toBeDisabled();
    await page.reload();
    await page.getByRole('button', { name: new RegExp(`AI review ${viewport.width}`) }).click();
    await expect(page.locator('.proposal-review')).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(
      true,
    );
    const accessibility = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa']).analyze();
    expect(accessibility.violations).toEqual([]);
    await page.getByLabel('Tôi đã xem lời thoại, hình và các điểm cần kiểm.').check();
    await page.getByRole('button', { name: 'Áp dụng storyboard đã duyệt' }).click();
    await expect(page.locator('.scene-item')).toHaveCount(1);
    await expect(
      page.getByRole('textbox', { name: 'Lời thoại của cảnh', exact: true }),
    ).toHaveValue(scene.narration);
  });
}

test('mock image candidate keeps current image until explicitly applied', async ({ page }) => {
  await page.route('**/api/capabilities', (route) => route.fulfill({ json: caps }));
  let job: Record<string, unknown>;
  let current: Record<string, unknown>;
  await page.route('**/api/projects/*/scenes/*/images', async (route) => {
    const id = route.request().url().split('/').at(-4)!;
    current = await (await page.request.get(`/api/projects/${id}`)).json();
    job = {
      id: 'mock-image',
      project_id: id,
      revision: current.revision,
      state: 'succeeded',
      options: { kind: 'image', seed: 42 },
      result: { candidate_id: 'mock-candidate', provenance: { checkpoint: 'test-checkpoint' } },
    };
    await route.fulfill({ status: 202, json: job });
  });
  await page.route('**/api/assets/mock-candidate', async (route) =>
    route.fulfill({
      contentType: 'image/png',
      body: await readFile(resolve('../../assets/examples/wet-shirt.png')),
    }),
  );
  await page.route('**/api/assets/mock-candidate/info', (route) =>
    route.fulfill({ json: { kind: 'image', width: 1600, height: 1400 } }),
  );
  await page.route('**/api/projects/*/images/mock-image/apply', async (route) => {
    const scenes = current.scenes as Record<string, unknown>[];
    await route.fulfill({
      json: {
        ...current,
        revision: Number(current.revision) + 1,
        scenes: scenes.map((s, i) => (i === 0 ? { ...s, image_id: 'mock-candidate' } : s)),
      },
    });
  });
  await page.goto('/');
  await page.getByRole('button', { name: 'Tạo câu chuyện đầu tiên' }).click();
  await page.getByLabel('Lời thoại', { exact: true }).fill('Một chiếc áo ướt.');
  await page.getByRole('button', { name: 'Tạo storyboard' }).click();
  await page
    .getByLabel('Nhập ảnh minh họa', { exact: true })
    .setInputFiles(resolve('../../assets/examples/wet-shirt.png'));
  await expect(page.locator('.portrait-image img')).toBeVisible();
  const oldSource = await page.locator('.portrait-image img').getAttribute('src');
  await page.getByLabel('Prompt ảnh', { exact: true }).fill('Original shirt');
  await page.getByRole('button', { name: 'Tạo một ảnh xem thử' }).click();
  await expect(page.locator('.candidate-review img')).toBeVisible();
  await expect(page.locator('.portrait-image img')).toHaveAttribute('src', oldSource!);
  await page.getByRole('button', { name: 'Dùng ảnh đề xuất cho cảnh' }).click();
  await expect(page.locator('.portrait-image img')).toHaveAttribute(
    'src',
    '/api/assets/mock-candidate',
  );
});
