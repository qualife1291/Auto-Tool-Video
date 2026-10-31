import { test, expect } from '@playwright/test';
import { resolve } from 'node:path';
import AxeBuilder from '@axe-core/playwright';

function shortVoice() {
  const rate = 24000;
  const frames = rate / 2;
  const wav = Buffer.alloc(44 + frames * 2);
  wav.write('RIFF', 0);
  wav.writeUInt32LE(wav.length - 8, 4);
  wav.write('WAVEfmt ', 8);
  wav.writeUInt32LE(16, 16);
  wav.writeUInt16LE(1, 20);
  wav.writeUInt16LE(1, 22);
  wav.writeUInt32LE(rate, 24);
  wav.writeUInt32LE(rate * 2, 28);
  wav.writeUInt16LE(2, 32);
  wav.writeUInt16LE(16, 34);
  wav.write('data', 36);
  wav.writeUInt32LE(frames * 2, 40);
  for (let i = 0; i < frames; i++) {
    wav.writeInt16LE(Math.round(Math.sin((2 * Math.PI * 440 * i) / rate) * 4000), 44 + i * 2);
  }
  return { name: 'voice.wav', mimeType: 'audio/wav', buffer: wav };
}

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
  const titleInput = page.getByLabel('Tên dự án');
  for (const width of [390, 1366]) {
    await page.setViewportSize({ width, height: width === 390 ? 844 : 900 });
    // Exercise actual keyboard navigation; programmatic locator.focus() does not
    // guarantee the browser's :focus-visible keyboard-modality heuristic.
    for (let repeat = 0; repeat < 3; repeat++) {
      await titleInput.click();
      await page.keyboard.press('Shift+Tab');
      await expect(titleInput).not.toBeFocused();
      await page.keyboard.press('Tab');
      await expect(titleInput).toBeFocused();
      const focus = await titleInput.evaluate((element) => ({
        focusVisible: element.matches(':focus-visible'),
        outlineStyle: getComputedStyle(element).outlineStyle,
        outlineWidth: getComputedStyle(element).outlineWidth,
        outlineColor: getComputedStyle(element).outlineColor,
      }));
      expect(focus.focusVisible).toBe(true);
      expect(focus.outlineStyle).not.toBe('none');
      expect(parseFloat(focus.outlineWidth)).toBeGreaterThanOrEqual(3);
      console.log(`FOCUS_KEYBOARD ${JSON.stringify({ width, repeat, focus })}`);
    }
    await page.screenshot({ path: test.info().outputPath(`focus-visible-${width}.png`) });
  }
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
  test(`full frame, focal crop and audio pacing persist at width ${width}`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    await page.goto('/');
    await page.getByRole('button', { name: 'Tạo câu chuyện đầu tiên' }).click();
    const title = `Nhịp kể ${width}`;
    await page.getByLabel('Tên dự án').fill(title);
    await page.getByLabel('Lời thoại', { exact: true }).fill('Nước bay hơi.');
    await page.getByRole('button', { name: 'Tạo storyboard' }).click();
    // A scrollable project list must remain keyboard focusable at mobile widths.
    await expect(page.locator('.project-list')).toHaveAttribute('tabindex', '0');
    await expect(page.getByLabel('Bố cục hình')).toHaveValue('full_frame');
    await expect(page.getByLabel('Cách lấp khung')).toHaveValue('contain');
    // New scenes protect source art; explicit creator cover+focal overrides that default.
    await page.getByLabel('Cách lấp khung').selectOption('cover');
    await expect(page.getByRole('button', { name: 'Khớp nhịp theo giọng đã nhập' })).toBeDisabled();
    await page
      .getByLabel('Nhập ảnh minh họa', { exact: true })
      .setInputFiles(resolve('../../assets/examples/wet-shirt.png'));
    await expect(page.locator('.portrait.full-frame img')).toBeVisible();
    const preview = await page.locator('.portrait-image').boundingBox();
    const canvas = await page.locator('.portrait').evaluate((element) => ({
      width: element.clientWidth,
      height: element.clientHeight,
    }));
    expect(preview?.width).toBeCloseTo(canvas.width, 0);
    expect(preview?.height).toBeCloseTo(canvas.height, 0);
    await page.getByLabel('Tiêu điểm ngang').fill('0.72');
    await page.getByLabel('Tiêu điểm dọc').fill('0.35');
    await expect(page.locator('.portrait-image img')).toHaveCSS('object-position', '72% 35%');
    await page.getByLabel('Bố cục hình').selectOption('board');
    await expect(page.getByLabel('Tiêu điểm ngang')).toHaveCount(0);
    await page.getByLabel('Bố cục hình').selectOption('full_frame');
    await page.getByLabel('Chuyển cảnh').selectOption('cut');
    await page.getByLabel('Phần thời gian dành để vẽ').fill('0.85');
    await page.getByLabel('Nhập giọng đọc', { exact: true }).setInputFiles(shortVoice());
    await expect(page.getByRole('button', { name: 'Khớp nhịp theo giọng đã nhập' })).toBeEnabled();
    await page.getByRole('button', { name: 'Khớp nhịp theo giọng đã nhập' }).click();
    await expect(page.getByLabel('Thời lượng cảnh (giây)')).toHaveValue('1');
    expect(
      (await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa']).analyze()).violations,
    ).toEqual([]);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(
      true,
    );
    await page.reload();
    await page.getByRole('button', { name: new RegExp(title) }).click();
    await page.getByRole('button', { name: /Storyboard/, exact: false }).click();
    await expect(page.getByLabel('Cách lấp khung')).toHaveValue('cover');
    await expect(page.getByLabel('Tiêu điểm ngang')).toHaveValue('0.72');
    await expect(page.getByLabel('Tiêu điểm dọc')).toHaveValue('0.35');
    await expect(page.getByLabel('Chuyển cảnh')).toHaveValue('cut');
    await expect(page.getByLabel('Phần thời gian dành để vẽ')).toHaveValue('0.85');
    await expect(page.getByLabel('Thời lượng cảnh (giây)')).toHaveValue('1');
  });

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
