import { test, expect } from '@playwright/test';

for (const width of [390, 1366]) {
  test(`edited second-by-second beat persists after save and reload at ${width}px`, async ({
    page,
  }) => {
    await page.setViewportSize({ width, height: 900 });
    const headers = { 'X-Studio-Client': 'local' };
    const name = `QA beat persistence ${width}`;
    const created = await page.request.post('/api/projects', {
      headers,
      data: { title: name, narration: 'Áo ướt chuyển thành áo khô.' },
    });
    expect(created.status()).toBe(201);
    const initial = await created.json();
    const split = await page.request.post(`/api/projects/${initial.id}/split`, {
      headers,
      data: { revision: initial.revision },
    });
    expect(split.ok()).toBeTruthy();
    const project = await split.json();
    const scene = { ...project.scenes[0], duration: 3 };
    const beats = Array.from({ length: Math.ceil(scene.duration) }, (_, second) => ({
      second,
      visual_state: `Áo xanh ở giây ${second}`,
      action: `Áo khô dần ở giây ${second}`,
      camera: 'Khung rộng ổn định',
      on_screen_text: '',
      narration_cue: 'Lời thoại theo cảnh',
      continuity: 'Giữ áo và điểm treo',
    }));
    const updated = await page.request.put(`/api/projects/${project.id}`, {
      headers,
      data: {
        title: project.title,
        profile: project.profile,
        platform: project.platform,
        narration: project.narration,
        aspect: project.aspect,
        revision: project.revision,
        scenes: [{ ...scene, second_by_second: beats, beat_plan_status: 'authored' }],
        brief: project.brief,
      },
    });
    expect(updated.ok()).toBeTruthy();

    await page.goto('/');
    await page.getByRole('button', { name }).click();
    await page.locator('.steps button').nth(1).click();
    await page.locator('.beat-editor > summary').click();
    const firstBeat = page.locator('.beat-row').first();
    await firstBeat.locator('summary').click();
    const changed = 'Áo khô từ từ và liên tục, không nhảy trạng thái';
    await firstBeat.getByRole('textbox', { name: 'Hành động và diễn biến' }).fill(changed);
    await page.getByRole('button', { name: 'Lưu thay đổi' }).click();
    await expect(page.getByText('Đã lưu trên máy.', { exact: true })).toBeVisible();

    await page.reload();
    await page.getByRole('button', { name }).click();
    await page.locator('.steps button').nth(1).click();
    await page.locator('.beat-editor > summary').click();
    const savedBeat = page.locator('.beat-row').first();
    await savedBeat.locator('summary').click();
    await expect(savedBeat.getByRole('textbox', { name: 'Hành động và diễn biến' })).toHaveValue(
      changed,
    );
    const persisted = await page.request.get(`/api/projects/${project.id}`, { headers });
    expect(persisted.ok()).toBeTruthy();
    expect((await persisted.json()).scenes[0].beat_plan_status).toBe('authored');

    // Changing 3.0 to 2.9 keeps all three beats but invalidates their timing.
    await page.getByLabel('Thời lượng cảnh (giây)').fill('2.9');
    await expect(page.locator('.beat-editor > summary')).toContainText('(3/3)');
    const reviewNotice = page.getByText('Kế hoạch từng giây cần rà soát và xác nhận lại.');
    await expect(reviewNotice).toBeVisible();
    await page.getByRole('button', { name: 'Lưu thay đổi' }).click();
    const stale = await page.request.get(`/api/projects/${project.id}`, { headers });
    expect(stale.ok()).toBeTruthy();
    const staleScene = (await stale.json()).scenes[0];
    expect(staleScene.beat_plan_status).toBe('needs_review');
    expect(staleScene.second_by_second).toHaveLength(3);
    expect(staleScene.second_by_second[0].action).toBe(changed);

    // Editing one beat must not silently approve every remaining beat.
    const revised = 'Áo khô rất từ từ, không nhảy trạng thái và vẫn giữ dấu tiếng Việt';
    await savedBeat.getByRole('textbox', { name: 'Hành động và diễn biến' }).fill(revised);
    await expect(reviewNotice).toBeVisible();
    await page.getByRole('button', { name: 'Lưu thay đổi' }).click();
    const partial = await page.request.get(`/api/projects/${project.id}`, { headers });
    expect((await partial.json()).scenes[0].beat_plan_status).toBe('needs_review');

    // The author confirms the complete, unchanged beat set explicitly.
    await page.getByRole('button', { name: 'Xác nhận đã rà soát từng giây' }).click();
    await expect(reviewNotice).toHaveCount(0);
    await page.getByRole('button', { name: 'Lưu thay đổi' }).click();
    const accepted = await page.request.get(`/api/projects/${project.id}`, { headers });
    expect(accepted.ok()).toBeTruthy();
    const acceptedScene = (await accepted.json()).scenes[0];
    expect(acceptedScene.beat_plan_status).toBe('authored');
    expect(acceptedScene.second_by_second[0].action).toBe(revised);
    expect(acceptedScene.second_by_second).toHaveLength(3);

    // Narration changes invalidate the previous second-by-second voice cues too.
    await page.getByLabel('Lời thoại của cảnh').fill('Áo ướt đang khô chậm hơn trước.');
    await expect(reviewNotice).toBeVisible();
    await page.getByRole('button', { name: 'Lưu thay đổi' }).click();
    const narrationUpdated = await page.request.get(`/api/projects/${project.id}`, { headers });
    const updatedScene = (await narrationUpdated.json()).scenes[0];
    expect(updatedScene.beat_plan_status).toBe('needs_review');
    expect(updatedScene.second_by_second[0].action).toBe(revised);
  });
}
