import { useEffect, useState } from 'react';
import { api } from './api';
import { briefFromIdea, lessonIdeas } from './lessonIdeas';
import {
  emptyBrief,
  type Capabilities,
  type CreativeBrief,
  type GenerationJob,
  type Project,
} from './domain';

type Props = {
  project: Project;
  disabled: boolean;
  onChange: (brief: CreativeBrief) => void;
  saveProject: () => Promise<Project>;
  onBusyChange: (busy: boolean) => void;
  onApplied: (project: Project) => Promise<void>;
};
export function CreativePanel({
  project,
  disabled,
  onChange,
  saveProject,
  onApplied,
  onBusyChange,
}: Props) {
  const brief = { ...emptyBrief, ...project.brief };
  const [mode, setMode] = useState<'brief' | 'preserve'>('brief');
  const [caps, setCaps] = useState<Capabilities | null>(null);
  const [job, setJob] = useState<GenerationJob | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [reviewed, setReviewed] = useState(false);
  const active = !!job && ['queued', 'running'].includes(job.state);
  const key = `whiteboard-plan-${project.id}`;
  const proposal = job?.result?.proposal;
  function update(patch: Partial<CreativeBrief>) {
    onChange({ ...brief, ...patch });
  }
  async function capability() {
    try {
      setCaps(await api<Capabilities>('/capabilities'));
    } catch {
      setError('Không kiểm tra được dịch vụ local. Bạn vẫn có thể chia đoạn thủ công.');
    }
  }
  useEffect(() => {
    void capability();
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
          .catch(() => setError('Mất kết nối trạng thái; tải lại để tiếp tục xem tác vụ.')),
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
      setError(e instanceof Error ? e.message : 'Không thể thực hiện.');
    } finally {
      setBusy(false);
      onBusyChange(false);
    }
  }
  async function start() {
    const p = await saveProject();
    const next = await api<GenerationJob>(`/projects/${p.id}/plan`, {
      method: 'POST',
      body: JSON.stringify({ revision: p.revision, mode, idempotency_key: crypto.randomUUID() }),
    });
    localStorage.setItem(key, next.id);
    setJob(next);
    setReviewed(false);
  }
  async function apply() {
    if (!job || !reviewed) return;
    if (
      project.scenes.length &&
      !window.confirm(
        'Thay storyboard hiện tại bằng đề xuất đã duyệt? Ảnh và audio cũ không bị xóa.',
      )
    )
      return;
    const p = await saveProject();
    const saved = await api<Project>(`/projects/${p.id}/plans/${job.id}/apply`, {
      method: 'POST',
      body: JSON.stringify({ revision: p.revision, confirm: true }),
    });
    await onApplied(saved);
    setJob({ ...job, applied_revision: saved.revision });
    setReviewed(false);
  }
  return (
    <section className="creative-panel" aria-label="Brief và planner AI">
      <div className="section-top">
        <div>
          <h3>Từ ý tưởng đến storyboard</h3>
          <p className="muted small">
            AI đề xuất, bạn giữ quyền biên tập. Chưa tự thay lời thoại hoặc cảnh.
          </p>
        </div>
        <button
          className="text-button"
          disabled={busy || disabled}
          onClick={() => void capability()}
        >
          Kiểm tra AI local
        </button>
      </div>
      <p className="provider-status" role="status">
        {caps?.script.message || 'Đang kiểm tra Ollama local…'}
        {caps?.script.model && ` · ${caps.script.model}`}
      </p>
      <fieldset disabled={disabled || busy || active}>
        <details className="brief-details">
          <summary>Thư viện ý tưởng khoa học</summary>
          <p className="muted small">
            Brief tiếng Việt nguyên bản, có tham khảo Tongjiang Lab. Bài học gốc dành cho THPT; bạn
            cần chọn độ tuổi và duyệt lại kiến thức. Hình, chữ, code và catalog gốc dùng CC BY-NC
            4.0: nếu dùng lại cần ghi nguồn, chỉ phi thương mại.
          </p>
          <div className="lesson-ideas">
            {lessonIdeas.map((idea) => (
              <article key={idea.slug}>
                <h4>{idea.title}</h4>
                <p className="small">{idea.age}</p>
                <p className="small">{idea.objective}</p>
                <a
                  href={`https://lab.tongjiang.app/c/${idea.slug}/`}
                  target="_blank"
                  rel="noreferrer"
                >
                  Xem bài tham khảo
                </a>
                <button
                  type="button"
                  className="secondary"
                  onClick={() => {
                    const populated = Object.entries(brief).some(
                      ([key, value]) =>
                        JSON.stringify(value) !==
                        JSON.stringify(emptyBrief[key as keyof CreativeBrief]),
                    );
                    if (
                      populated &&
                      !window.confirm(
                        'Thay brief hiện tại bằng ý tưởng này? Storyboard và tài nguyên vẫn được giữ.',
                      )
                    )
                      return;
                    onChange(briefFromIdea(idea));
                  }}
                >
                  Dùng ý tưởng: {idea.title}
                </button>
              </article>
            ))}
          </div>
        </details>
        <label>
          Cách tạo storyboard
          <select value={mode} onChange={(e) => setMode(e.target.value as typeof mode)}>
            <option value="brief">Viết kịch bản mới từ brief</option>
            <option value="preserve">Giữ nguyên lời thoại, AI lập hình minh họa</option>
          </select>
        </label>
        <details className="brief-details" open={mode === 'brief'}>
          <summary>Brief chi tiết và phong cách</summary>
          <label>
            Chủ đề
            <input
              maxLength={300}
              value={brief.topic}
              onChange={(e) => update({ topic: e.target.value })}
              placeholder="Ví dụ: vì sao chiếc áo ướt khô?"
            />
          </label>
          <label>
            Mục tiêu người xem hiểu được
            <textarea
              rows={2}
              maxLength={1000}
              value={brief.objective}
              onChange={(e) => update({ objective: e.target.value })}
            />
          </label>
          <div className="form-row">
            <label>
              Thời lượng mục tiêu
              <select
                value={brief.target_duration}
                onChange={(e) =>
                  update({ target_duration: Number(e.target.value) as 30 | 45 | 60 })
                }
              >
                <option value={30}>30 giây</option>
                <option value={45}>45 giây</option>
                <option value={60}>60 giây</option>
              </select>
            </label>
            <label>
              Giọng kể
              <input
                maxLength={300}
                value={brief.tone}
                onChange={(e) => update({ tone: e.target.value })}
              />
            </label>
          </div>
          <label>
            Điều cần nhớ · tối đa 3 dòng
            <textarea
              rows={3}
              value={brief.takeaways.join('\n')}
              onChange={(e) => update({ takeaways: e.target.value.split('\n').slice(0, 3) })}
            />
          </label>
          <label>
            Kiến thức bắt buộc
            <textarea
              rows={3}
              maxLength={3000}
              value={brief.required_facts}
              onChange={(e) => update({ required_facts: e.target.value })}
            />
          </label>
          <label>
            Nguồn tham khảo · tối đa 10 dòng
            <textarea
              rows={2}
              value={brief.sources.join('\n')}
              onChange={(e) => update({ sources: e.target.value.split('\n').slice(0, 10) })}
            />
          </label>
          <p className="muted small">
            Nguồn do bạn cung cấp; AI không tự kiểm chứng các đường dẫn.
          </p>
          <label>
            Điều cần tránh
            <textarea
              rows={2}
              maxLength={1000}
              value={brief.avoid}
              onChange={(e) => update({ avoid: e.target.value })}
            />
          </label>
          <label>
            Phong cách hình ảnh
            <textarea
              rows={2}
              maxLength={1500}
              value={brief.style_bible}
              onChange={(e) => update({ style_bible: e.target.value })}
            />
          </label>
          <label>
            Nhân vật xuyên suốt
            <textarea
              rows={2}
              maxLength={1000}
              value={brief.character_bible}
              onChange={(e) => update({ character_bible: e.target.value })}
            />
          </label>
        </details>
        <button
          className="button primary"
          disabled={
            caps?.script.state !== 'ready' ||
            (mode === 'brief' ? !brief.topic.trim() : !project.narration.trim())
          }
          onClick={() => void action(start)}
        >
          Tạo đề xuất AI
        </button>
      </fieldset>
      {error && (
        <p className="notice error" role="alert">
          {error}
        </p>
      )}
      {job && (
        <div className="generation-status" role="status">
          {
            (
              {
                queued: 'Đang chờ planner',
                running: 'Ollama đang soạn storyboard…',
                failed: job.error || 'Tạo đề xuất thất bại',
                cancelled: 'Đã hủy chờ planner',
                interrupted: 'Worker bị gián đoạn. Hãy tạo lại.',
                succeeded: job.applied_revision
                  ? 'Đề xuất này đã được áp dụng.'
                  : 'Đề xuất đã có — cần bạn xem và duyệt.',
              } as Record<string, string>
            )[job.state]
          }
        </div>
      )}
      {active && (
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
          Hủy tạo đề xuất
        </button>
      )}
      {proposal && job?.state === 'succeeded' && (
        <div className="proposal-review">
          <h3>{proposal.title}</h3>
          <p className="muted small">
            {proposal.source_preserved
              ? 'Lời thoại được lấy lại từ nguồn; model chỉ lập storyboard.'
              : 'Đây là lời thoại mới do AI đề xuất, cần kiểm nội dung.'}{' '}
            Chưa có ảnh hay giọng đọc tự sinh ở bước này.
          </p>
          {proposal.scenes.map((scene, index) => (
            <article className="proposal-scene" key={scene.id}>
              <h4>
                {index + 1}. {scene.title} <small>· {scene.duration}s</small>
              </h4>
              <p>{scene.narration}</p>
              <p className="small">
                <strong>Hình:</strong> {scene.visual_description}
              </p>
              <details>
                <summary>Prompt và thứ tự vẽ</summary>
                <p className="small">{scene.image_prompt}</p>
                <ol>
                  {scene.reveal_order?.map((value, i) => (
                    <li key={i}>{value}</li>
                  ))}
                </ol>
              </details>
              <ul className="fact-flags">
                {scene.fact_flags?.map((value, i) => (
                  <li key={i}>{value}</li>
                ))}
              </ul>
            </article>
          ))}
          <label className="checkbox">
            <input
              type="checkbox"
              checked={reviewed}
              disabled={!!job.applied_revision}
              onChange={(e) => setReviewed(e.target.checked)}
            />{' '}
            Tôi đã xem lời thoại, hình và các điểm cần kiểm.
          </label>
          <button
            className="button primary"
            disabled={!reviewed || busy || disabled || !!job.applied_revision}
            onClick={() => void action(apply)}
          >
            Áp dụng storyboard đã duyệt
          </button>
          {project.revision !== job.revision && !job.applied_revision && (
            <p className="source-warning">
              Dự án đã đổi sau lúc tạo đề xuất. Tạo lại để không ghi đè bản mới.
            </p>
          )}
        </div>
      )}
    </section>
  );
}
