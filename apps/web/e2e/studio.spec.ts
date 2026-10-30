import { test, expect } from '@playwright/test';
import { resolve } from 'node:path';
import AxeBuilder from '@axe-core/playwright';

for (const viewport of [
  { name: 'desktop', width: 1366, height: 900 },
  { name: 'mobile', width: 390, height: 844 },
]) {
  test(`create, upload, export, metadata and restore on ${viewport.name}`, async ({ page }) => {
    await page.setViewportSize(viewport);
    await page.goto('/');
    await page.getByRole('button', { name: 'Tạo câu chuyện đầu tiên' }).click();
    await page.getByLabel('Tên dự án').fill(`Nước đi đâu · ${viewport.name}`);
    await page
      .getByLabel('Lời thoại', { exact: true })
      .fill('Một chiếc áo ướt.\nNước bay hơi.\nNơi thoáng giúp áo khô.');
    await page.getByRole('button', { name: 'Tạo storyboard' }).click();
    await expect(page.locator('.scene-item')).toHaveCount(3);
    for (let i = 0; i < 3; i++) {
      await page.locator('.scene-item').nth(i).click();
      await page.getByLabel('Thời lượng cảnh (giây)').fill('1');
      await page
        .getByLabel('Nhập ảnh minh họa', { exact: true })
        .setInputFiles(resolve('../../assets/examples/wet-shirt.png'));
      await expect(page.getByText('Đã nhập và lưu tài nguyên.', { exact: true })).toBeVisible();
      await expect(page.locator('.portrait-image img')).toBeVisible();
      await page.getByLabel('Kiểu phụ đề').selectOption(['card', 'contrast', 'accent'][i]);
      if (i === 2) {
        await page.getByLabel('Cụm từ nhấn', { exact: true }).fill('thoáng');
        await expect(page.locator('.portrait-caption mark')).toHaveText('thoáng');
      }
    }
    await page.getByLabel('Kiểu minh họa').selectOption('motion');
    await page.getByRole('button', { name: 'Lưu thay đổi' }).click();
    await page.screenshot({
      path: test.info().outputPath(`studio-${viewport.name}.png`),
      fullPage: true,
    });
    expect(
      await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth),
    ).toBe(true);
    await page.getByRole('button', { name: /Xuất video/ }).click();
    await expect(page.getByRole('button', { name: 'Xuất MP4 1080p' })).toBeDisabled();
    await page.getByLabel('Tôi chủ động xuất không lời đọc').check();
    await page
      .getByLabel('Tỷ lệ xuất')
      .selectOption(viewport.name === 'desktop' ? 'landscape' : 'portrait');
    await page.getByRole('button', { name: 'Dựng xem thử', exact: true }).click();
    await expect(page.locator('.result-panel video')).toBeVisible({ timeout: 60000 });
    await expect(page.getByText('Đã xuất và kiểm tệp', { exact: true })).toBeVisible();
    const [download] = await Promise.all([
      page.waitForEvent('download'),
      page.getByRole('link', { name: /Tải MP4/ }).click(),
    ]);
    expect(await download.failure()).toBeNull();
    const [metadata] = await Promise.all([
      page.waitForEvent('download'),
      page.getByRole('button', { name: 'Tải metadata & checklist' }).click(),
    ]);
    expect(metadata.suggestedFilename()).toBe('publish-metadata.json');
    expect(await metadata.failure()).toBeNull();
    await expect(page.getByRole('link', { name: 'Mở YouTube Studio' })).toHaveAttribute(
      'href',
      'https://studio.youtube.com/',
    );
    await expect(page.getByRole('link', { name: 'Mở TikTok Studio' })).toHaveAttribute(
      'href',
      'https://www.tiktok.com/tiktokstudio/upload',
    );
    const projectTitle = `Nước đi đâu · ${viewport.name}`;
    await page.reload();
    await page.getByRole('button', { name: new RegExp(projectTitle) }).click();
    await page.getByRole('button', { name: /Storyboard/, exact: false }).click();
    await page.locator('.scene-item').nth(2).click();
    await expect(page.getByLabel('Kiểu phụ đề')).toHaveValue('accent');
    await expect(page.getByLabel('Cụm từ nhấn', { exact: true })).toHaveValue('thoáng');
    await page.getByRole('button', { name: /Xuất video/ }).click();
    await expect(page.locator('.result-panel video')).toBeVisible();
  });
}

test('input stays text and keyboard focus is visible', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'Tạo câu chuyện đầu tiên' }).click();
  await page.getByLabel('Tên dự án').fill('<img src=x onerror=alert(1)>');
  await page.getByRole('button', { name: 'Lưu thay đổi' }).click();
  await expect(page.locator('h1')).toHaveText('<img src=x onerror=alert(1)>');
  expect(await page.locator('h1 img').count()).toBe(0);
  await page.getByLabel('Tên dự án').focus();
  expect(
    await page.getByLabel('Tên dự án').evaluate((e) => getComputedStyle(e).outlineStyle),
  ).not.toBe('none');
});

test('accessible labels and contrast on initial and storyboard screens', async ({ page }) => {
  await page.goto('/');
  const initial = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa']).analyze();
  expect(initial.violations).toEqual([]);
  await page.getByRole('button', { name: 'Tạo câu chuyện đầu tiên' }).click();
  await page.getByLabel('Lời thoại', { exact: true }).fill('Cùng quan sát nước.');
  await page.getByRole('button', { name: 'Tạo storyboard' }).click();
  const editor = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa']).analyze();
  expect(editor.violations).toEqual([]);
});

for (const width of [1366, 390]) {
  test(`lesson idea preserves script and requires confirmation at width ${width}`, async ({
    page,
  }) => {
    await page.setViewportSize({ width, height: 900 });
    await page.goto('/');
    await page.getByRole('button', { name: 'Tạo câu chuyện đầu tiên' }).click();
    const title = `Ý tưởng khoa học ${width}`;
    await page.getByLabel('Tên dự án').fill(title);
    await page.getByLabel('Lời thoại', { exact: true }).fill('Nước vẫn ở quanh ta.');
    await page.getByRole('button', { name: 'Tạo storyboard' }).click();
    await page.getByRole('button', { name: /Kịch bản/, exact: false }).click();
    await page.getByText('Thư viện ý tưởng khoa học', { exact: true }).click();
    await page.getByRole('button', { name: 'Dùng ý tưởng: Một giọt nước đi đâu?' }).click();
    await expect(page.getByLabel('Chủ đề', { exact: true })).toHaveValue('Một giọt nước đi đâu?');
    await expect(page.getByRole('textbox', { name: 'Lời thoại', exact: true })).toHaveValue(
      'Nước vẫn ở quanh ta.',
    );
    const river = page.getByRole('button', {
      name: 'Dùng ý tưởng: Dòng sông làm đổi bờ như thế nào?',
    });
    page.once('dialog', (dialog) => dialog.dismiss());
    await river.click();
    await expect(page.getByLabel('Chủ đề', { exact: true })).toHaveValue('Một giọt nước đi đâu?');
    page.once('dialog', (dialog) => dialog.accept());
    await river.click();
    await page.getByRole('button', { name: 'Lưu thay đổi' }).click();
    const accessible = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa']).analyze();
    expect(accessible.violations).toEqual([]);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(
      true,
    );
    await page.reload();
    await page.getByRole('button', { name: new RegExp(title) }).click();
    await expect(page.getByLabel('Chủ đề', { exact: true })).toHaveValue(
      'Dòng sông làm đổi bờ như thế nào?',
    );
    await expect(
      page.getByRole('textbox', { name: 'Nguồn tham khảo · tối đa 10 dòng', exact: true }),
    ).toHaveValue('https://lab.tongjiang.app/c/river-step/');
    await page.getByRole('button', { name: /Storyboard/, exact: false }).click();
    await expect(page.locator('.scene-item')).toHaveCount(1);
    await expect(
      page.getByRole('textbox', { name: 'Lời thoại của cảnh', exact: true }),
    ).toHaveValue('Nước vẫn ở quanh ta.');
  });
}
