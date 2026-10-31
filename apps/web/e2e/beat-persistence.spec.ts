import { test, expect, type Page } from '@playwright/test';

// Synchronize each Save with its exact project PUT response, not the click.
// An immediate independent GET can otherwise race the pending save request.
// Assertions on BOTH the PUT result and stored GET must still reject stale
// revisions, missing beat edits, and wrong authored/needs_review transitions.
async function saveAndRead(
  page: Page,
  projectId: string,
  previousRevision: number,
  expectedStatus: 'authored' | 'needs_review',
) {
  const projectPath = `/api/projects/${projectId}`;
  const [response] = await Promise.all([
    page.waitForResponse((candidate) => {
      const { pathname } = new URL(candidate.url());
      return candidate.request().method() === 'PUT' && pathname === projectPath;
    }),
    page.getByRole('button', { name: 'Lưu thay đổi' }).click(),
  ]);
  expect(response.ok()).toBeTruthy();
  const result = await response.json();
  expect(result.revision).toBeGreaterThan(previousRevision);
  expect(result.scenes[0].beat_plan_status).toBe(expectedStatus);
  await expect(page.getByRole('button', { name: 'Đã lưu', exact: true })).toBeDisabled();
  await expect(page.getByText('Đã lưu trên máy.', { exact: true })).toBeVisible();

  const persisted = await page.request.get(projectPath, {
    headers: { 'X-Studio-Client': 'local' },
  });
  expect(persisted.ok()).toBeTruthy();
  const stored = await persisted.json();
  expect(stored.revision).toBe(result.revision);
  expect(stored.scenes[0].beat_plan_status).toBe(expectedStatus);
  return stored;
}

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
    let lastRevision = (await updated.json()).revision as number;

    await page.goto('/');
    await page.getByRole('button', { name }).click();
    await page.locator('.steps button').nth(1).click();
    await page.locator('.beat-editor > summary').click();
    const firstBeat = page.locator('.beat-row').first();
    await firstBeat.locator('summary').click();
    const changed = 'Áo khô từ từ và liên tục, không nhảy trạng thái';
    await firstBeat.getByRole('textbox', { name: 'Hành động và diễn biến' }).fill(changed);
    lastRevision = (await saveAndRead(page, project.id, lastRevision, 'needs_review')).revision;

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
    expect((await persisted.json()).scenes[0].beat_plan_status).toBe('needs_review');

    // Changing 3.0 to 2.9 keeps all three beats but invalidates their timing.
    await page.getByLabel('Thời lượng cảnh (giây)').fill('2.9');
    await expect(page.locator('.beat-editor > summary')).toContainText('(3/3)');
    const reviewNotice = page.getByText('Kế hoạch từng giây cần rà soát và xác nhận lại.');
    await expect(reviewNotice).toBeVisible();
    const staleProject = await saveAndRead(page, project.id, lastRevision, 'needs_review');
    lastRevision = staleProject.revision;
    const staleScene = staleProject.scenes[0];
    expect(staleScene.beat_plan_status).toBe('needs_review');
    expect(staleScene.second_by_second).toHaveLength(3);
    expect(staleScene.second_by_second[0].action).toBe(changed);

    // Editing one beat must not silently approve every remaining beat.
    const revised = 'Áo khô rất từ từ, không nhảy trạng thái và vẫn giữ dấu tiếng Việt';
    await savedBeat.getByRole('textbox', { name: 'Hành động và diễn biến' }).fill(revised);
    await expect(reviewNotice).toBeVisible();
    const partial = await saveAndRead(page, project.id, lastRevision, 'needs_review');
    lastRevision = partial.revision;
    expect(partial.scenes[0].second_by_second[0].action).toBe(revised);

    // The author confirms the complete, unchanged beat set explicitly.
    await page.getByRole('button', { name: 'Xác nhận đã rà soát từng giây' }).click();
    await expect(reviewNotice).toHaveCount(0);
    const accepted = await saveAndRead(page, project.id, lastRevision, 'authored');
    lastRevision = accepted.revision;
    const acceptedScene = accepted.scenes[0];
    expect(acceptedScene.beat_plan_status).toBe('authored');
    expect(acceptedScene.second_by_second[0].action).toBe(revised);
    expect(acceptedScene.second_by_second).toHaveLength(3);

    // Narration changes invalidate the previous second-by-second voice cues too.
    await page.getByLabel('Lời thoại của cảnh').fill('Áo ướt đang khô chậm hơn trước.');
    await expect(reviewNotice).toBeVisible();
    const narrationUpdated = await saveAndRead(page, project.id, lastRevision, 'needs_review');
    const updatedScene = narrationUpdated.scenes[0];
    expect(updatedScene.beat_plan_status).toBe('needs_review');
    expect(updatedScene.second_by_second[0].action).toBe(revised);
  });
}
