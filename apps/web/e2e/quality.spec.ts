import { test, expect } from '@playwright/test';
import { execFileSync } from 'node:child_process';
import { dirname } from 'node:path';
import { mkdirSync, readFileSync } from 'node:fs';
import AxeBuilder from '@axe-core/playwright';

for (const width of [1366, 390]) {
  test(`real QC freeze warning, critical rejection, approval and restore at ${width}`, async ({
    page,
  }) => {
    const clip = test.info().outputPath('intentional-frozen-fixture.mp4');
    mkdirSync(dirname(clip), { recursive: true });
    execFileSync('ffmpeg', [
      '-v',
      'error',
      '-y',
      '-f',
      'lavfi',
      '-i',
      'color=c=0x5CBAC6:size=640x360:rate=30',
      '-t',
      '2',
      '-c:v',
      'libx264',
      '-threads',
      '1',
      '-pix_fmt',
      'yuv420p',
      clip,
    ]);
    await page.setViewportSize({ width, height: 900 });
    page.setDefaultTimeout(10000);
    await page.goto('/');
    await page.getByRole('button', { name: 'Tạo câu chuyện đầu tiên' }).click();
    const title = `QC fixture ${width}`;
    await page.getByLabel('Tên dự án').fill(title);
    await page
      .getByLabel('Lời thoại', { exact: true })
      .fill('Hình tĩnh là fixture kiểm lỗi đứng hình.');
    await page.getByRole('button', { name: 'Tạo storyboard' }).click();
    await page.getByLabel('Nhập ảnh minh họa', { exact: true }).setInputFiles(clip);
    await expect(page.getByText('Đã nhập và lưu tài nguyên.', { exact: true })).toBeVisible();
    await page.getByLabel('Kỳ vọng chuyển động').selectOption('motion_required');
    await page.getByRole('button', { name: 'Lưu thay đổi' }).click();
    await page.getByRole('button', { name: /Xuất video/ }).click();
    await page.getByLabel('Tôi chủ động xuất không lời đọc').check();
    await page.getByLabel('Tỷ lệ xuất').selectOption(width === 1366 ? 'landscape' : 'portrait');
    await page.getByRole('button', { name: 'Dựng xem thử', exact: true }).click();
    await expect(page.locator('.result-panel video')).toBeVisible({ timeout: 60000 });
    const panel = page.getByRole('region', { name: 'Kiểm định video sau gen' });
    await expect(panel.getByText('Cần người duyệt', { exact: true })).toBeVisible();
    await expect(panel.getByText(/Kỹ thuật: đạt kiểm tra tự động/)).toBeVisible();
    await panel.getByRole('button', { name: /Xem tại/ }).click();
    await expect
      .poll(() =>
        page
          .locator('.result-panel video')
          .evaluate((video: HTMLVideoElement) => video.currentTime),
      )
      .toBeGreaterThan(0.1);
    await panel.getByLabel('Người duyệt', { exact: true }).fill('Creator kiểm thử');
    for (const label of [
      'Khớp kịch bản / prompt',
      'Chuyển động mượt',
      'Nhất quán thời gian',
      'Logic vật lý',
      'Chất lượng kỹ thuật',
    ]) {
      await panel.getByRole('combobox', { name: `Điểm · ${label}`, exact: true }).selectOption('5');
    }
    const critical = panel.getByLabel('Lỗi nghiêm trọng · Khớp kịch bản / prompt', { exact: true });
    await critical.check();
    await panel
      .getByRole('textbox', { name: 'Ghi chú · Khớp kịch bản / prompt', exact: true })
      .fill('=1+1 <img src=x onerror=alert(1)>');
    await panel.getByRole('button', { name: 'Lưu phiếu duyệt', exact: true }).click();
    await expect(panel.getByText('Loại bản này — cần làm lại', { exact: true })).toBeVisible();
    await critical.uncheck();
    for (const label of [
      'Tôi đã xem hết video ở tốc độ bình thường',
      'Tôi đã kiểm phụ đề, dấu và vùng an toàn',
      'Tôi đã đối chiếu kiến thức và độ tuổi',
      'Tôi đã xem xét nguồn gốc và nhãn AI phù hợp',
    ]) {
      await panel.getByLabel(label, { exact: true }).check();
    }
    await panel
      .getByRole('combobox', { name: 'Nguồn gốc do creator xác nhận', exact: true })
      .selectOption('no_ai');
    await panel.getByRole('button', { name: 'Lưu phiếu duyệt', exact: true }).click();
    await expect(panel.getByText('Cần người duyệt', { exact: true })).toBeVisible();
    await panel.getByLabel('Đã xem và đối chiếu cảnh báo này', { exact: true }).check();
    await panel.getByRole('button', { name: 'Lưu phiếu duyệt', exact: true }).click();
    await expect(panel.getByText('Creator đã duyệt chất lượng', { exact: true })).toBeVisible();
    expect(await panel.locator('img').count()).toBe(0);
    expect(
      (await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa']).analyze()).violations,
    ).toEqual([]);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(
      true,
    );
    const [download] = await Promise.all([
      page.waitForEvent('download'),
      panel.getByRole('link', { name: 'Tải phiếu QC CSV' }).click(),
    ]);
    expect(download.suggestedFilename()).toBe('quality-review.csv');
    expect(readFileSync((await download.path())!, 'utf8')).toContain("'=1+1");
    await page.reload();
    await page.getByRole('button', { name: new RegExp(title) }).click();
    await page.getByRole('button', { name: /Xuất video/ }).click();
    await expect(panel.getByText('Creator đã duyệt chất lượng', { exact: true })).toBeVisible();
    await expect(panel.getByLabel('Người duyệt', { exact: true })).toHaveValue('Creator kiểm thử');
  });
}
