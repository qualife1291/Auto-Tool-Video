import { useEffect, useState } from 'react';
import { api } from './api';
import { type Capabilities, type GenerationJob, type Project, type Scene } from './domain';
import { suggestDetailedImagePrompt } from './richImagePrompt';

type Props = {
  project: Project;
  scene: Scene;
  disabled: boolean;
  saveProject: () => Promise<Project>;
  onPrompt: (prompt: string) => void;
  onBusyChange: (busy: boolean) => void;
  onApplied: (project: Project) => Promise<void>;
};
export function ImageGenerationPanel({
  project,
  scene,
  disabled,
  saveProject,
  onPrompt,
  onApplied,
  onBusyChange,
}: Props) {
  const [caps, setCaps] = useState<Capabilities | null>(null);
  const [job, setJob] = useState<GenerationJob | null>(null);
  const [seed, setSeed] = useState(42);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const key = `whiteboard-image-${project.id}-${scene.id}`;
  const active = !!job && ['queued', 'running'].includes(job.state);
  const detailedPrompt = suggestDetailedImagePrompt(scene);
  useEffect(() => {
    api<Capabilities>('/capabilities')
      .then(setCaps)
      .catch(() => setError('Không kiểm tra được ComfyUI.'));
    const id = localStorage.getItem(key);
    if (id)
      api<GenerationJob>(`/jobs/${id}`)
        .then(setJob)
        .catch(() => localStorage.removeItem(key));
  }, [key]);
  useEffect(() => {
    if (!active || !job) return;
    const timer = setInterval(
      () =>
        api<GenerationJob>(`/jobs/${job.id}`)
          .then(setJob)
          .catch(() => setError('Mất kết nối trạng thái; tải lại để tiếp tục.')),
      1000,
    );
    return () => clearInterval(timer);
  }, [active, job?.id]);
  async function action(fn: () => Promise<void>) {
    setBusy(true);
    onBusyChange(true);
    setError('');
    try {
      await fn();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Không thể tạo ảnh.');
    } finally {
      setBusy(false);
      onBusyChange(false);
    }
  }
  async function start() {
    const p = await saveProject();
    const next = await api<GenerationJob>(`/projects/${p.id}/scenes/${scene.id}/images`, {
      method: 'POST',
      body: JSON.stringify({ revision: p.revision, seed, idempotency_key: crypto.randomUUID() }),
    });
    setJob(next);
    localStorage.setItem(key, next.id);
  }
  async function apply() {
    if (!job) return;
    const p = await saveProject();
    const saved = await api<Project>(`/projects/${p.id}/images/${job.id}/apply`, {
      method: 'POST',
      body: JSON.stringify({ revision: p.revision, confirm: true }),
    });
    await onApplied(saved);
    setJob({ ...job, applied_revision: saved.revision });
  }
  return (
    <section className="image-generation" aria-label="Tạo ảnh AI local">
      <h3>Ảnh AI · xem trước rồi chọn</h3>
      <p className="muted small">{caps?.image.message || 'Đang kiểm tra ComfyUI local…'}</p>
      <label>
        Prompt ảnh
        <textarea
          rows={3}
          maxLength={2000}
          disabled={busy || disabled || active}
          value={scene.image_prompt}
          onChange={(e) => onPrompt(e.target.value)}
        />
      </label>
      <button
        className="button"
        type="button"
        disabled={busy || disabled || active || detailedPrompt === scene.image_prompt}
        onClick={() => onPrompt(detailedPrompt)}
      >
        Gợi ý minh họa giàu chi tiết, có bối cảnh
      </button>
      <p className="muted small">
        Gợi ý chỉ sửa prompt. Không tự tạo ảnh hay tự duyệt chất lượng.
      </p>
      <label>
        Seed ảnh
        <input
          type="number"
          min={0}
          max={4294967295}
          value={seed}
          disabled={busy || active}
          onChange={(e) => setSeed(Number(e.target.value))}
        />
      </label>
      <button
        className="button"
        disabled={
          busy || disabled || active || caps?.image.state !== 'ready' || !scene.image_prompt.trim()
        }
        onClick={() => void action(start)}
      >
        Tạo một ảnh xem thử
      </button>
      <p className="muted small">
        Ảnh cũ không bị thay đến khi bạn chọn ảnh mới. Seed/phong cách không bảo đảm nhân vật giống
        tuyệt đối.
      </p>
      {active && (
        <>
          <p role="status">ComfyUI đang tạo ảnh…</p>
          <button
            className="button"
            disabled={busy}
            onClick={() =>
              void action(async () => {
                if (job)
                  setJob(await api<GenerationJob>(`/jobs/${job.id}/cancel`, { method: 'POST' }));
              })
            }
          >
            Hủy chờ ảnh
          </button>
          <p className="muted small">
            ComfyUI có thể tiếp tục tác vụ đã bắt đầu; app không ngắt các tác vụ khác.
          </p>
        </>
      )}
      {error && (
        <p className="notice error" role="alert">
          {error}
        </p>
      )}
      {job && ['failed', 'cancelled', 'interrupted'].includes(job.state) && (
        <p className="source-warning" role="status">
          {job.error || 'Đã dừng tác vụ. Ảnh cũ được giữ.'}
        </p>
      )}
      {job?.state === 'succeeded' && job.result?.candidate_id && (
        <div className="candidate-review">
          <img
            alt="Ảnh AI đề xuất chưa tự áp dụng"
            src={`/api/assets/${job.result.candidate_id}`}
          />
          <p className="small">
            Checkpoint: {String(job.result.provenance?.checkpoint || '')} · seed {job.options.seed}
          </p>
          <button
            className="button primary"
            disabled={busy || disabled || !!job.applied_revision}
            onClick={() => void action(apply)}
          >
            {job.applied_revision ? 'Đã chọn ảnh này' : 'Dùng ảnh đề xuất cho cảnh'}
          </button>
          <p className="muted small">
            Chọn ảnh xác nhận bạn đã xem nội dung và quyền dùng. Bản xuất trước không thay đổi.
          </p>
        </div>
      )}
    </section>
  );
}
