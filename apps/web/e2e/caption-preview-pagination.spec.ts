import { expect, test } from '@playwright/test';

const narration =
  'Áo vừa giặt còn ướt, nhưng một lúc sau đã khô. Các phân tử nước ở bề mặt ' +
  'có thể thoát vào không khí, đó là hiện tượng bay hơi. Gió đưa lớp không khí ẩm ' +
  'đi xa, giúp thêm nhiều phân tử nước bay hơi. Khi không khí quá ẩm, áo sẽ khô ' +
  'chậm hơn ngay cả khi trời vẫn ấm. Hãy quan sát chiếc khăn ướt trong nhà nhé!';

for (const viewport of [
  { width: 390, height: 844 },
  { width: 1366, height: 900 },
]) {
  test(`long Vietnamese captions are honestly paginated at ${viewport.width}px`, async ({
    page,
  }) => {
    await page.setViewportSize(viewport);
    await page.goto('/');
    await page.getByRole('button', { name: 'Tạo câu chuyện đầu tiên' }).click();
    const title = `Phân trang tiếng Việt ${viewport.width}`;
    await page.getByLabel('Tên dự án').fill(title);
    await page.getByLabel('Lời thoại', { exact: true }).fill(narration);
    if (viewport.width === 1366) {
      await page.getByLabel('Khung hình').selectOption('landscape');
    }
    await page.getByRole('button', { name: 'Tạo storyboard' }).click();
    await expect(page.locator('.portrait')).toHaveClass(
      viewport.width === 1366 ? /landscape/ : /^portrait(?!.*landscape)/,
    );
    await expect(page.locator('.scene-item')).toHaveCount(1);
    await expect(page.getByLabel('Lời thoại của cảnh')).toHaveValue(narration);

    const preview = page.locator('.portrait-caption');
    await expect(preview).toBeVisible();
    await expect(page.getByText('Ước lượng — xem video xuất để xác nhận')).toBeVisible();
    await expect(page.locator('.caption-preview-status')).toContainText(/^Trang 1\/[2-9]\d*/);
    await expect(preview).not.toContainText(narration);
    const firstPage = await preview.innerText();
    const nextPage = page.getByRole('button', { name: 'Trang phụ đề tiếp' });
    await nextPage.focus();
    await page.keyboard.press('Enter');
    await expect(page.locator('.caption-preview-status')).toContainText(/^Trang 2\//);
    expect(await preview.innerText()).not.toBe(firstPage);
    await page.getByRole('button', { name: 'Trang phụ đề trước' }).click();
    await expect(preview).toHaveText(firstPage);

    // When the editor narration changes, reset the estimated preview without editing project schema.
    await nextPage.click();
    await page.getByLabel('Lời thoại của cảnh').fill('Nước bay hơi.');
    await expect(page.locator('.caption-preview-status')).toContainText('Trang 1/1');
    await expect(preview).toHaveText('Nước bay hơi.');
    await expect(nextPage).toHaveCount(0);
    await page.getByLabel('Lời thoại của cảnh').fill(narration);
    await expect(page.locator('.caption-preview-status')).toContainText(/^Trang 1\/[2-9]\d*/);

    // Make a real editor change before using the Save button (otherwise it is disabled).
    await page.getByLabel('Kiểu phụ đề').selectOption('contrast');
    await expect(preview).toHaveClass(/caption-contrast/);
    const [persisted] = await Promise.all([
      page.waitForResponse(
        (response) =>
          response.request().method() === 'PUT' && response.url().includes('/api/projects/'),
      ),
      page.getByRole('button', { name: 'Lưu thay đổi' }).click(),
    ]);
    expect(persisted.ok()).toBeTruthy();
    await expect(page.getByText('Đã lưu trên máy.', { exact: true })).toBeVisible();
    await page.reload();
    await page.getByRole('button', { name: new RegExp(title) }).click();
    await page.getByRole('button', { name: /Storyboard/ }).click();
    await expect(page.getByLabel('Lời thoại của cảnh')).toHaveValue(narration);
    await expect(page.getByText('Ước lượng — xem video xuất để xác nhận')).toBeVisible();
  });
}
