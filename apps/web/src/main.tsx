import { api } from './api';
import { CreativePanel } from './CreativePanel';
import { ImageGenerationPanel } from './ImageGenerationPanel';
import { QualityPanel } from './QualityPanel';
import { useEffect, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import {
  ArrowDown,
  ArrowUp,
  Check,
  ChevronRight,
  Download,
  Film,
  ImagePlus,
  Layers,
  Mic,
  Plus,
  Save,
  ShieldCheck,
  Sparkles,
  X,
} from 'lucide-react';
import {
  duration,
  example,
  preflight,
  profiles,
  steps,
  sourceNeedsUpscale,
  captionParts,
  estimateCaptionPages,
  type Job,
  type Project,
  type Scene,
} from './domain';
import './style.css';

const asset = (id: string) => `/api/assets/${encodeURIComponent(id)}`;
const localTime = (iso: string) =>
  new Date(iso).toLocaleString('vi-VN', {
    timeZone: 'Asia/Ho_Chi_Minh',
    hour: '2-digit',
    minute: '2-digit',
    day: '2-digit',
    month: '2-digit',
  });

function App() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [project, setProject] = useState<Project | null>(null);
  const [step, setStep] = useState(0);
  const [sceneIndex, setSceneIndex] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [dirty, setDirty] = useState(false);
  const [guides, setGuides] = useState(true);
  const [captionPageIndex, setCaptionPageIndex] = useState(0);
  const [visualKinds, setVisualKinds] = useState<Record<string, string>>({});
  const [sourceWarnings, setSourceWarnings] = useState<Record<string, boolean>>({});
  const [hub, setHub] = useState<{
    note: string;
    providers: Record<string, { label: string; upload_url: string; account_note: string }>;
  } | null>(null);
  const [captions, setCaptions] = useState(true);
  const [silent, setSilent] = useState(false);
  const [audience, setAudience] = useState('pending');
  const [rights, setRights] = useState('pending');
  const [job, setJob] = useState<Job | null>(null);
  const [health, setHealth] = useState<{
    ffmpeg: boolean;
    font: boolean;
    milestone: string;
  } | null>(null);
  const generation = useRef(0);
  const exportKey = useRef<string | null>(null);
  const scene = project?.scenes[sceneIndex];
  const estimatedCaptionPages = scene
    ? estimateCaptionPages(scene.narration, project?.aspect ?? 'portrait')
    : [];
  const captionPage = Math.min(captionPageIndex, Math.max(0, estimatedCaptionPages.length - 1));
  const currentCaption = estimatedCaptionPages[captionPage] || '';
  useEffect(() => {
    setCaptionPageIndex(0);
  }, [scene?.id, scene?.narration, project?.aspect]);
  const running = job && ['queued', 'running'].includes(job.state);
  const issues = project ? preflight(project, silent) : [];

  async function refresh() {
    setProjects(await api<Project[]>('/projects'));
  }
  useEffect(() => {
    Promise.all([
      api<Project[]>('/projects'),
      api<{ ffmpeg: boolean; font: boolean; milestone: string }>('/health'),
    ])
      .then(([p, h]) => {
        setProjects(p);
        setHealth(h);
      })
      .catch((e) => setError(String(e.message)));
  }, []);
  useEffect(() => {
    api<typeof hub>('/social')
      .then(setHub)
      .catch(() => {});
  }, []);
  useEffect(() => {
    project?.scenes.forEach((s) => {
      if (s.image_id)
        api<{ kind: string; width: number; height: number }>(`/assets/${s.image_id}/info`)
          .then((a) => {
            setVisualKinds((v) => ({ ...v, [s.image_id!]: a.kind }));
            setSourceWarnings((v) => ({
              ...v,
              [s.image_id!]: sourceNeedsUpscale(
                a.width,
                a.height,
                project.aspect,
                s.layout,
                s.visual_fit,
              ),
            }));
          })
          .catch(() => {});
    });
  }, [project?.id, project?.revision, project?.aspect]);
  useEffect(() => {
    const warn = (event: BeforeUnloadEvent) => {
      if (dirty) {
        event.preventDefault();
        event.returnValue = '';
      }
    };
    window.addEventListener('beforeunload', warn);
    return () => window.removeEventListener('beforeunload', warn);
  }, [dirty]);
  useEffect(() => {
    if (!running || !job) return;
    const id = job.id;
    const timer = setInterval(() => {
      api<Job>(`/jobs/${id}`)
        .then((j) => setJob((current) => (current?.id === id ? j : current)))
        .catch((e) => setError(e.message));
    }, 1000);
    return () => clearInterval(timer);
  }, [job?.id, running]);
  useEffect(() => {
    if (!project) return;
    const saved = localStorage.getItem(`whiteboard-job-${project.id}`);
    if (saved)
      api<Job>(`/jobs/${saved}`)
        .then(setJob)
        .catch(() => localStorage.removeItem(`whiteboard-job-${project.id}`));
    else setJob(null);
  }, [project?.id]);
  useEffect(() => {
    exportKey.current = null;
  }, [project?.revision, silent, captions]);

  async function task(fn: () => Promise<void>) {
    setBusy(true);
    setError('');
    setNotice('');
    try {
      await fn();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Có lỗi xảy ra.');
    } finally {
      setBusy(false);
    }
  }
  async function save(): Promise<Project> {
    if (!project) throw new Error('Chưa chọn dự án.');
    if (!dirty) return project;
    const payload = {
      title: project.title,
      profile: project.profile,
      platform: project.platform,
      narration: project.narration,
      aspect: project.aspect,
      revision: project.revision,
      scenes: project.scenes,
      ...(project.brief ? { brief: project.brief } : {}),
    };
    const saved = await api<Project>(`/projects/${project.id}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
    setProject(saved);
    setDirty(false);
    await refresh();
    setNotice('Đã lưu trên máy.');
    return saved;
  }
  function update(changes: Partial<Project>) {
    setProject((p) => (p ? { ...p, ...changes } : p));
    setDirty(true);
  }
  function updateScene(changes: Partial<Scene>) {
    if (!project || !scene) return;
    update({
      scenes: project.scenes.map((s) => {
        if (s.id !== scene.id) return s;
        // A new timeline or narration can invalidate previously reviewed spoken cues.
        const beatTimingChanged =
          (changes.duration !== undefined && changes.duration !== s.duration) ||
          (changes.narration !== undefined && changes.narration !== s.narration);
        return {
          ...s,
          ...changes,
          ...(changes.narration !== undefined && s.audio_id ? { audio_stale: true } : {}),
          ...(beatTimingChanged && s.second_by_second?.length
            ? { beat_plan_status: 'needs_review' as const }
            : {}),
        };
      }),
    });
  }
  async function createProject() {
    if (dirty && !window.confirm('Có nội dung chưa lưu. Rời dự án này?')) return;
    const created = await api<Project>('/projects', {
      method: 'POST',
      body: JSON.stringify({
        title: 'Câu chuyện mới',
        profile: 'family',
        platform: 'shorts',
        narration: '',
      }),
    });
    setProject(created);
    setDirty(false);
    setSceneIndex(0);
    setStep(0);
    generation.current++;
    await refresh();
  }
  async function openProject(p: Project) {
    if (dirty && !window.confirm('Có nội dung chưa lưu. Rời dự án này?')) return;
    generation.current++;
    const id = generation.current;
    const opened = await api<Project>(`/projects/${p.id}`);
    if (id === generation.current) {
      setProject(opened);
      setDirty(false);
      setSceneIndex(0);
      setStep(0);
      setError('');
      setNotice('');
    }
  }
  async function split() {
    const p = await save();
    if (
      p.scenes.length &&
      !window.confirm(
        'Thay storyboard hiện tại bằng các đoạn lời thoại? Tệp ảnh/tiếng cũ không bị xóa.',
      )
    )
      return;
    const next = await api<Project>(`/projects/${p.id}/split`, {
      method: 'POST',
      body: JSON.stringify({ revision: p.revision, replace_existing: !!p.scenes.length }),
    });
    setProject(next);
    setDirty(false);
    setSceneIndex(0);
    setStep(1);
    await refresh();
  }
  async function upload(file: File | undefined) {
    if (!file || !scene) return;
    const selectedId = scene.id;
    await task(async () => {
      const p = await save();
      const form = new FormData();
      form.append('file', file);
      form.append('revision', String(p.revision));
      const next = await api<Project>(`/projects/${p.id}/scenes/${selectedId}/assets`, {
        method: 'POST',
        body: form,
      });
      setProject(next);
      setDirty(false);
      await refresh();
      setNotice('Đã nhập và lưu tài nguyên.');
    });
  }
  function reorder(direction: number) {
    if (!project) return;
    const to = sceneIndex + direction;
    if (to < 0 || to >= project.scenes.length) return;
    const scenes = [...project.scenes];
    [scenes[sceneIndex], scenes[to]] = [scenes[to], scenes[sceneIndex]];
    update({ scenes });
    setSceneIndex(to);
  }
  async function startExport(kind: string) {
    const p = await save();
    if (!exportKey.current) exportKey.current = crypto.randomUUID();
    const next = await api<Job>(`/projects/${p.id}/exports`, {
      method: 'POST',
      body: JSON.stringify({
        revision: p.revision,
        kind,
        silent,
        captions,
        aspect: p.aspect,
        idempotency_key: `${exportKey.current}-${kind}`,
      }),
    });
    localStorage.setItem(`whiteboard-job-${p.id}`, next.id);
    setJob(next);
  }
  async function downloadPack() {
    const p = await save();
    const data = await api<unknown>(
      `/projects/${p.id}/publish-pack?audience=${audience}&rights=${rights}${job?.state === 'succeeded' ? `&job_id=${job.id}` : ''}`,
    );
    const url = URL.createObjectURL(
      new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' }),
    );
    const link = document.createElement('a');
    link.href = url;
    link.download = 'publish-metadata.json';
    link.click();
    URL.revokeObjectURL(url);
  }
  async function appliedAi(saved: Project) {
    setProject((current) => (current?.id === saved.id ? saved : current));
    setDirty(false);
    await refresh();
    setNotice('Đã áp dụng kết quả được duyệt.');
  }
  function addScene() {
    if (!project || project.scenes.length >= 20) return;
    update({
      scenes: [
        ...project.scenes,
        {
          id: crypto.randomUUID(),
          title: `Cảnh ${project.scenes.length + 1}`,
          narration: '',
          image_prompt: '',
          image_id: null,
          audio_id: null,
          audio_stale: false,
          duration: 5,
          layout: 'full_frame',
          visual_fit: 'cover',
          transition: 'dissolve',
          focal_x: 0.5,
          focal_y: 0.5,
          draw_fraction: 0.78,
          style: 'whiteboard',
        },
      ],
    });
    setSceneIndex(project.scenes.length);
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a className="brand" href="/" aria-label="Whiteboard Studio">
          <span className="brand-mark">
            <Layers size={23} />
          </span>
          <span>
            Whiteboard<span className="brand-sub">STUDIO</span>
          </span>
        </a>
        <button
          className="button primary new-project"
          disabled={busy}
          onClick={() => task(createProject)}
        >
          <Plus size={18} /> Dự án mới
        </button>
        <div className="eyebrow">KHÔNG GIAN CỦA BẠN</div>
        <nav className="project-list" aria-label="Dự án đã lưu">
          {projects.map((p) => (
            <button
              disabled={busy}
              className={`project-link ${p.id === project?.id ? 'active' : ''}`}
              key={p.id}
              onClick={() => task(() => openProject(p))}
            >
              <Film size={17} />
              <span>
                {p.title}
                <small>{localTime(p.updated_at)}</small>
              </span>
            </button>
          ))}
        </nav>
        {!projects.length && (
          <p className="muted small">Tạo dự án đầu tiên để bắt đầu câu chuyện.</p>
        )}
        <div className="local-note">
          <span className="status-dot" /> Lưu trên máy của bạn
          <p>
            Không cần tài khoản.
            <br />
            Không phí API để nhập và dựng video.
          </p>
        </div>
      </aside>
      <main>
        <header className="topbar">
          <span className="breadcrumb">
            Không gian sáng tạo <ChevronRight size={14} /> {project?.title || 'Bắt đầu'}
          </span>
          <span className="badge">
            <span className="status-dot" />
            {health?.ffmpeg && health.font ? 'Renderer sẵn sàng' : 'Đang kiểm tra renderer'}
          </span>
        </header>
        <div className="workspace">
          <div className="page-heading">
            <div>
              <p className="eyebrow">TỪ Ý TƯỞNG ĐẾN CÂU CHUYỆN</p>
              <h1>{project ? project.title : 'Một nét vẽ. Một điều mới.'}</h1>
              <p className="muted">
                Tạo video whiteboard tiếng Việt, kể chuyện rõ ràng cho đúng người xem.
              </p>
            </div>
            {project && (
              <button
                className="button"
                disabled={busy || !dirty}
                onClick={() =>
                  task(async () => {
                    await save();
                  })
                }
              >
                <Save size={17} />
                {dirty ? 'Lưu thay đổi' : 'Đã lưu'}
              </button>
            )}
          </div>
          {error && (
            <div className="notice error" role="alert">
              <span>{error}</span>
              <button aria-label="Đóng thông báo lỗi" onClick={() => setError('')}>
                <X size={17} />
              </button>
            </div>
          )}
          {notice && (
            <div className="notice success" role="status">
              <Check size={17} />
              {notice}
            </div>
          )}
          {!project ? (
            <section className="welcome card">
              <div className="welcome-icon">
                <Sparkles size={35} />
              </div>
              <p className="eyebrow">WHITEBOARD STUDIO · BẢN KHỞI ĐẦU</p>
              <h2>
                Biến lời kể thành
                <br />
                những điều dễ hiểu.
              </h2>
              <p>
                Chọn người xem, chia lời thoại thành cảnh, thêm tranh và giọng đọc.
                <br />
                Xuất video dọc 1080p cho Shorts, TikTok và Reels.
              </p>
              <button
                className="button primary"
                disabled={busy}
                onClick={() => task(createProject)}
              >
                <Plus size={18} /> Tạo câu chuyện đầu tiên
              </button>
              <div className="welcome-features">
                <span>01 · Kịch bản rõ ý</span>
                <span>02 · Hình ảnh của bạn</span>
                <span>03 · Video dọc thật</span>
              </div>
            </section>
          ) : (
            <>
              <nav className="steps" aria-label="Các bước tạo video">
                {steps.map((label, i) => (
                  <button
                    key={label}
                    disabled={busy}
                    aria-current={step === i ? 'step' : undefined}
                    className={step === i ? 'current' : ''}
                    onClick={() => setStep(i)}
                  >
                    <span className="step-number">0{i + 1}</span>
                    <span>
                      {label}
                      <small>
                        {
                          [
                            'Chọn ý và người xem',
                            `${project.scenes.length} cảnh minh họa`,
                            'Âm thanh và thời lượng',
                            'Kiểm tra và tải xuống',
                          ][i]
                        }
                      </small>
                    </span>
                  </button>
                ))}
              </nav>
              {step === 0 && (
                <div className="script-layout">
                  <section className="card script-card">
                    <div className="section-top">
                      <div>
                        <h2>Câu chuyện bắt đầu từ lời kể</h2>
                        <p className="muted">
                          Mỗi đoạn xuống dòng sẽ thành một cảnh. Bạn có thể chỉnh lại sau.
                        </p>
                      </div>
                      <button
                        className="text-button"
                        disabled={busy}
                        onClick={() =>
                          update({
                            title: 'Chiếc áo ướt và hành trình của nước',
                            narration: example,
                          })
                        }
                      >
                        Dùng lời thoại ví dụ
                      </button>
                    </div>
                    <label>
                      Tên dự án
                      <input
                        disabled={busy}
                        maxLength={70}
                        value={project.title}
                        onChange={(e) => update({ title: e.target.value })}
                      />
                    </label>
                    <label>
                      Khung hình
                      <select
                        disabled={busy}
                        value={project.aspect}
                        onChange={(e) => update({ aspect: e.target.value as Project['aspect'] })}
                      >
                        <option value="portrait">Dọc 9:16 · 1080×1920</option>
                        <option value="landscape">Ngang 16:9 · 1920×1080</option>
                      </select>
                    </label>
                    <div className="form-row">
                      <label>
                        Người xem chính
                        <select
                          disabled={busy}
                          value={project.profile}
                          onChange={(e) => update({ profile: e.target.value })}
                        >
                          {profiles.map(([id, name]) => (
                            <option key={id} value={id}>
                              {name}
                            </option>
                          ))}
                        </select>
                      </label>
                      <label>
                        Nơi dự định đăng
                        <select
                          disabled={busy}
                          value={project.platform}
                          onChange={(e) => update({ platform: e.target.value })}
                        >
                          <option value="shorts">YouTube Shorts</option>
                          <option value="kids">YouTube · nội dung cho trẻ</option>
                          <option value="tiktok">TikTok</option>
                          <option value="reels">Facebook Reels</option>
                        </select>
                      </label>
                    </div>
                    <CreativePanel
                      key={project.id}
                      project={project}
                      disabled={busy}
                      onChange={(brief) => update({ brief })}
                      saveProject={save}
                      onApplied={async (saved) => {
                        await appliedAi(saved);
                        setSceneIndex(0);
                        setStep(1);
                      }}
                      onBusyChange={setBusy}
                    />
                    <label>
                      Lời thoại
                      <textarea
                        disabled={busy}
                        className="script-input"
                        maxLength={12000}
                        placeholder="Một câu hỏi thú vị, một điều bạn muốn giải thích…"
                        value={project.narration}
                        onChange={(e) => update({ narration: e.target.value })}
                      />
                    </label>
                    <div className="form-footer">
                      <span className="muted small">
                        Giữ nguyên lời thoại · Chia theo đoạn, chưa dùng AI
                      </span>
                      <button
                        className="button primary"
                        disabled={busy || !project.narration.trim()}
                        onClick={() => task(split)}
                      >
                        Tạo storyboard <ChevronRight size={17} />
                      </button>
                    </div>
                  </section>
                  <aside className="tips">
                    <section className="card">
                      <span className="tip-icon">
                        <ShieldCheck />
                      </span>
                      <h3>Đúng người, đúng cách kể</h3>
                      <p>{profiles.find(([id]) => id === project.profile)?.[2]}</p>
                      <p className="small">
                        Không có một nhịp kể phù hợp mọi độ tuổi. Chọn một nhóm chính cho mỗi video.
                      </p>
                    </section>
                    <section className="ai-note">
                      <Sparkles size={18} />
                      <div>
                        <strong>AI local, có bước duyệt.</strong>
                        <p>
                          M2 tạo đề xuất kịch bản bằng Ollama và ảnh qua ComfyUI đã cấu hình. Kết
                          quả chỉ thay dự án khi bạn xem và áp dụng. Giọng AI ở mốc tiếp theo.
                        </p>
                      </div>
                    </section>
                  </aside>
                </div>
              )}
              {(step === 1 || step === 2) && (
                <div className="editor-layout">
                  <section className="card scenes-panel">
                    <div className="section-top">
                      <h3>
                        Các cảnh <span className="count">{project.scenes.length}</span>
                      </h3>
                      <button
                        className="icon-button"
                        aria-label="Thêm cảnh"
                        disabled={busy || project.scenes.length >= 20}
                        onClick={addScene}
                      >
                        <Plus size={18} />
                      </button>
                    </div>
                    {project.scenes.length === 0 ? (
                      <p className="muted">Chia lời thoại ở bước Kịch bản, hoặc thêm một cảnh.</p>
                    ) : (
                      project.scenes.map((s, i) => (
                        <button
                          className={`scene-item ${i === sceneIndex ? 'selected' : ''}`}
                          key={s.id}
                          disabled={busy}
                          onClick={() => setSceneIndex(i)}
                        >
                          <span className="thumb">
                            {s.image_id ? (
                              visualKinds[s.image_id] === 'clip' ? (
                                <Film size={22} />
                              ) : (
                                <img alt={`Ảnh ${s.title}`} src={asset(s.image_id)} />
                              )
                            ) : (
                              <ImagePlus size={22} />
                            )}
                          </span>
                          <span>
                            <strong>
                              {i + 1}. {s.title}
                            </strong>
                            <small>
                              {s.duration.toFixed(1)}s · {s.image_id ? 'Có ảnh' : 'Thiếu ảnh'}
                            </small>
                          </span>
                        </button>
                      ))
                    )}
                    <div className="total-time">
                      Tổng thời lượng
                      <strong className={duration(project.scenes) > 60 ? 'danger' : ''}>
                        {duration(project.scenes).toFixed(1)} / 60s
                      </strong>
                    </div>
                  </section>
                  <section className="card preview-panel">
                    <div className="section-top">
                      <h3>Khung hình {project.aspect === 'landscape' ? 'ngang' : 'dọc'}</h3>
                      <span className="badge neutral">
                        {project.aspect === 'landscape' ? '16:9' : '9:16'} · 1080p
                      </span>
                    </div>
                    <div
                      className={`portrait ${project.aspect === 'landscape' ? 'landscape' : ''} ${scene?.layout === 'full_frame' ? 'full-frame' : ''}`}
                    >
                      <div className="portrait-title">{scene?.title || 'Chưa có cảnh'}</div>
                      <div className="portrait-image">
                        {scene?.image_id ? (
                          visualKinds[scene.image_id] === 'clip' ? (
                            <video
                              controls
                              playsInline
                              muted
                              style={{
                                objectFit:
                                  scene.layout === 'full_frame'
                                    ? scene.visual_fit || 'cover'
                                    : 'contain',
                                objectPosition: `${(scene.focal_x ?? 0.5) * 100}% ${(scene.focal_y ?? 0.5) * 100}%`,
                              }}
                              src={asset(scene.image_id)}
                              aria-label={`Clip ${scene.title}`}
                            />
                          ) : (
                            <img
                              alt={`Bố cục ${scene.title}`}
                              src={asset(scene.image_id)}
                              style={{
                                objectFit:
                                  scene.layout === 'full_frame'
                                    ? scene.visual_fit || 'cover'
                                    : 'contain',
                                objectPosition: `${(scene.focal_x ?? 0.5) * 100}% ${(scene.focal_y ?? 0.5) * 100}%`,
                              }}
                            />
                          )
                        ) : (
                          <div className="image-placeholder">
                            <ImagePlus size={35} />
                            <span>Nhập ảnh minh họa</span>
                            <small>PNG/JPEG/MP4 · Không tự cắt chủ thể</small>
                          </div>
                        )}
                      </div>
                      {captions && scene && currentCaption && (
                        <div
                          className={`portrait-caption caption-${scene.caption_style || 'card'}`}
                        >
                          {(scene.caption_style === 'accent'
                            ? captionParts(currentCaption, scene.caption_emphasis || '')
                            : [{ text: currentCaption, emphasis: false }]
                          ).map((part, index) =>
                            part.emphasis ? (
                              <mark key={index}>{part.text}</mark>
                            ) : (
                              <span key={index}>{part.text}</span>
                            ),
                          )}
                        </div>
                      )}
                      {guides && (
                        <div className="safe-guide">
                          <span>VÙNG CHỮ AN TOÀN</span>
                        </div>
                      )}
                    </div>
                    {captions && currentCaption && (
                      <div
                        className="caption-preview-controls"
                        aria-label="Phân trang phụ đề ước lượng"
                      >
                        <span className="caption-preview-status" role="status">
                          Trang {captionPage + 1}/{estimatedCaptionPages.length} (ước lượng)
                        </span>
                        {estimatedCaptionPages.length > 1 && (
                          <div className="caption-preview-navigation">
                            <button
                              type="button"
                              aria-label="Trang phụ đề trước"
                              disabled={captionPage === 0}
                              onClick={() => setCaptionPageIndex((index) => Math.max(0, index - 1))}
                            >
                              Trước
                            </button>
                            <button
                              type="button"
                              aria-label="Trang phụ đề tiếp"
                              disabled={captionPage >= estimatedCaptionPages.length - 1}
                              onClick={() =>
                                setCaptionPageIndex((index) =>
                                  Math.min(index + 1, estimatedCaptionPages.length - 1),
                                )
                              }
                            >
                              Tiếp
                            </button>
                          </div>
                        )}
                        <small>Ước lượng — xem video xuất để xác nhận</small>
                      </div>
                    )}
                    <label className="checkbox small">
                      <input
                        type="checkbox"
                        checked={guides}
                        onChange={(e) => setGuides(e.target.checked)}
                      />{' '}
                      Hiện vùng an toàn · không in vào video
                    </label>
                    <p className="muted small">
                      Bố cục tĩnh. Hiệu ứng nét và bàn tay có trong video dựng ở bước Xuất.
                    </p>
                  </section>
                  <section className="card properties-panel">
                    {scene ? (
                      <>
                        <div className="section-top">
                          <h3>Cảnh {sceneIndex + 1}</h3>
                          <div className="inline-actions">
                            <button
                              className="icon-button"
                              disabled={busy || sceneIndex === 0}
                              aria-label="Đưa cảnh lên"
                              onClick={() => reorder(-1)}
                            >
                              <ArrowUp size={17} />
                            </button>
                            <button
                              className="icon-button"
                              disabled={busy || sceneIndex === project.scenes.length - 1}
                              aria-label="Đưa cảnh xuống"
                              onClick={() => reorder(1)}
                            >
                              <ArrowDown size={17} />
                            </button>
                          </div>
                        </div>
                        <label>
                          Tiêu đề cảnh
                          <input
                            disabled={busy}
                            maxLength={70}
                            value={scene.title}
                            onChange={(e) => updateScene({ title: e.target.value })}
                          />
                        </label>
                        <label>
                          Lời thoại của cảnh
                          <textarea
                            disabled={busy}
                            rows={5}
                            maxLength={500}
                            value={scene.narration}
                            onChange={(e) => updateScene({ narration: e.target.value })}
                          />
                        </label>
                        <label>
                          Kiểu phụ đề
                          <select
                            disabled={busy}
                            value={scene.caption_style || 'card'}
                            onChange={(e) =>
                              updateScene({
                                caption_style: e.target.value as Scene['caption_style'],
                              })
                            }
                          >
                            <option value="card">Thẻ sáng · dễ đọc</option>
                            <option value="contrast">Nền đậm · nổi bật</option>
                            <option value="accent">Nhấn cụm từ · màu vàng</option>
                          </select>
                        </label>
                        <label>
                          Bố cục hình
                          <select
                            disabled={busy}
                            value={scene.layout || 'board'}
                            onChange={(e) =>
                              updateScene({ layout: e.target.value as Scene['layout'] })
                            }
                          >
                            <option value="full_frame">Toàn khung · chữ phủ trên hình</option>
                            <option value="board">Bảng minh họa · có lề</option>
                          </select>
                        </label>
                        {scene.layout === 'full_frame' && (
                          <>
                            <label>
                              Cách lấp khung
                              <select
                                disabled={busy}
                                value={scene.visual_fit || 'cover'}
                                onChange={(e) =>
                                  updateScene({ visual_fit: e.target.value as Scene['visual_fit'] })
                                }
                              >
                                <option value="cover">Phủ kín · có thể cắt mép</option>
                                <option value="contain">Giữ toàn bộ ảnh</option>
                              </select>
                            </label>
                            {scene.visual_fit !== 'contain' && (
                              <>
                                <label>
                                  Tiêu điểm ngang
                                  <input
                                    type="range"
                                    min="0"
                                    max="1"
                                    step="0.01"
                                    value={scene.focal_x ?? 0.5}
                                    onChange={(e) =>
                                      updateScene({ focal_x: Number(e.target.value) })
                                    }
                                  />
                                </label>
                                <label>
                                  Tiêu điểm dọc
                                  <input
                                    type="range"
                                    min="0"
                                    max="1"
                                    step="0.01"
                                    value={scene.focal_y ?? 0.5}
                                    onChange={(e) =>
                                      updateScene({ focal_y: Number(e.target.value) })
                                    }
                                  />
                                </label>
                                <p className="small muted">
                                  Phủ kín có thể cắt mép ảnh khác tỷ lệ. Chỉnh tiêu điểm và xem thử
                                  để giữ chủ thể quan trọng.
                                </p>
                              </>
                            )}
                          </>
                        )}
                        <label>
                          Chuyển cảnh
                          <select
                            disabled={busy}
                            value={scene.transition || 'cut'}
                            onChange={(e) =>
                              updateScene({ transition: e.target.value as Scene['transition'] })
                            }
                          >
                            <option value="dissolve">Hòa hình nhẹ · chữ giữ rõ</option>
                            <option value="cut">Cắt thẳng</option>
                          </select>
                        </label>
                        <label>
                          Phần thời gian dành để vẽ
                          <input
                            type="range"
                            min="0.3"
                            max="0.9"
                            step="0.01"
                            disabled={busy || scene.style !== 'whiteboard'}
                            value={scene.draw_fraction ?? 0.65}
                            onChange={(e) => updateScene({ draw_fraction: Number(e.target.value) })}
                          />
                        </label>
                        <label>
                          Cụm từ nhấn
                          <input
                            maxLength={70}
                            disabled={busy || scene.caption_style !== 'accent'}
                            value={scene.caption_emphasis || ''}
                            onChange={(e) => updateScene({ caption_emphasis: e.target.value })}
                            placeholder="Ví dụ: bay hơi"
                          />
                        </label>
                        <details className="beat-editor">
                          <summary>
                            Storyboard theo từng giây ({scene.second_by_second?.length || 0}/
                            {Math.ceil(scene.duration)})
                          </summary>
                          {(scene.second_by_second?.length || 0) !== Math.ceil(scene.duration) && (
                            <p className="small danger">
                              Thời lượng đã thay đổi hoặc chưa có beat. Kế hoạch cũ được giữ, cần rà
                              soát từng giây trước khi render.
                            </p>
                          )}
                          {scene.beat_plan_status === 'needs_review' &&
                            !!scene.second_by_second?.length && (
                              <p className="small muted">
                                Kế hoạch từng giây cần rà soát và xác nhận lại.
                              </p>
                            )}
                          {(scene.second_by_second || []).map((beat, beatIndex) => (
                            <details className="beat-row" key={beat.second}>
                              <summary>
                                Giây {beat.second}–{Math.min(beat.second + 1, scene.duration)}:{' '}
                                {beat.action}
                              </summary>
                              {(
                                [
                                  ['visual_state', 'Trạng thái hình và vật thể'],
                                  ['action', 'Hành động và diễn biến'],
                                  ['camera', 'Khung hình và camera'],
                                  ['on_screen_text', 'Chữ trên hình'],
                                  ['narration_cue', 'Cue lời đọc / khoảng nghỉ'],
                                  ['continuity', 'Nhất quán và nối cảnh'],
                                ] as const
                              ).map(([field, title]) => (
                                <label key={field}>
                                  {title}
                                  <textarea
                                    rows={2}
                                    disabled={busy}
                                    value={beat[field]}
                                    onChange={(event) => {
                                      const updated = [...(scene.second_by_second || [])];
                                      updated[beatIndex] = {
                                        ...beat,
                                        [field]: event.target.value,
                                      };
                                      // Editing one cue does not approve the whole draft.
                                      updateScene({
                                        second_by_second: updated,
                                        beat_plan_status: 'needs_review',
                                      });
                                    }}
                                  />
                                </label>
                              ))}
                            </details>
                          ))}
                          {scene.beat_plan_status === 'needs_review' &&
                            scene.second_by_second?.length === Math.ceil(scene.duration) && (
                              <button
                                type="button"
                                className="button"
                                disabled={
                                  busy ||
                                  !scene.second_by_second.every(
                                    (beat) =>
                                      beat.visual_state.trim() &&
                                      beat.action.trim() &&
                                      beat.camera.trim() &&
                                      beat.narration_cue.trim() &&
                                      beat.continuity.trim(),
                                  )
                                }
                                onClick={() => updateScene({ beat_plan_status: 'authored' })}
                              >
                                Xác nhận đã rà soát từng giây
                              </button>
                            )}
                        </details>
                        <label>
                          Kỳ vọng chuyển động
                          <select
                            disabled={busy}
                            value={scene.motion_expectation || 'allow_static'}
                            onChange={(e) =>
                              updateScene({
                                motion_expectation: e.target.value as Scene['motion_expectation'],
                              })
                            }
                          >
                            <option value="allow_static">
                              Cho phép cảnh tĩnh / giữ hình để đọc
                            </option>
                            <option value="motion_required">Cần chuyển động trong cảnh</option>
                          </select>
                        </label>
                        <p className="muted small">
                          Nhấn cụm có trong lời thoại khi chọn kiểu màu vàng. Hiệu ứng theo cảnh,
                          chưa căn từng từ.
                        </p>
                        <label>
                          Kiểu minh họa
                          <select
                            disabled={busy}
                            value={scene.style}
                            onChange={(e) =>
                              updateScene({ style: e.target.value as Scene['style'] })
                            }
                          >
                            <option value="whiteboard">Whiteboard · nét vẽ và bàn tay</option>
                            <option value="motion">Minh họa chuyển động · ảnh hoặc clip</option>
                          </select>
                        </label>
                        <label>
                          Thời lượng cảnh (giây)
                          <input
                            disabled={busy}
                            type="number"
                            min={1}
                            max={20}
                            step={0.1}
                            value={scene.duration}
                            onChange={(e) => updateScene({ duration: Number(e.target.value) })}
                          />
                        </label>
                        <ImageGenerationPanel
                          key={`${project.id}-${scene.id}`}
                          project={project}
                          scene={scene}
                          disabled={busy}
                          saveProject={save}
                          onPrompt={(image_prompt) => updateScene({ image_prompt })}
                          onApplied={appliedAi}
                          onBusyChange={setBusy}
                        />
                        <label className="upload-control">
                          <ImagePlus size={18} />{' '}
                          {scene.image_id ? 'Thay ảnh minh họa' : 'Nhập ảnh / clip MP4'}
                          <input
                            disabled={busy}
                            aria-label="Nhập ảnh minh họa"
                            type="file"
                            accept="image/png,image/jpeg,video/mp4"
                            onChange={(e) => {
                              void upload(e.target.files?.[0]);
                              e.target.value = '';
                            }}
                          />
                        </label>
                        <label className="upload-control">
                          <Mic size={18} />{' '}
                          {scene.audio_id ? 'Thay giọng đọc' : 'Nhập giọng đọc WAV/MP3'}
                          <input
                            disabled={busy}
                            aria-label="Nhập giọng đọc"
                            type="file"
                            accept="audio/wav,audio/mpeg,.wav,.mp3"
                            onChange={(e) => {
                              void upload(e.target.files?.[0]);
                              e.target.value = '';
                            }}
                          />
                        </label>
                        {scene.audio_id && (
                          <audio
                            controls
                            src={asset(scene.audio_id)}
                            aria-label={`Giọng đọc ${scene.title}`}
                          />
                        )}
                        <button
                          className="button"
                          disabled={
                            busy || project.scenes.some((s) => !s.audio_id || s.audio_stale)
                          }
                          onClick={() =>
                            task(async () => {
                              const current = await save();
                              const fitted = await api<Project>(
                                `/projects/${current.id}/fit-audio`,
                                {
                                  method: 'POST',
                                  body: JSON.stringify({
                                    revision: current.revision,
                                    pause_after: 0.12,
                                  }),
                                },
                              );
                              setProject(fitted);
                              setDirty(false);
                              await refresh();
                              setNotice('Đã khớp thời lượng theo giọng, thêm khoảng nghỉ ngắn.');
                            })
                          }
                        >
                          Khớp nhịp theo giọng đã nhập
                        </button>
                        <p className="small muted">
                          Cần giọng khớp lời ở mọi cảnh. Giữ trọn tệp audio và thêm 0,12 giây; không
                          ép mỗi cảnh 4–5 giây.
                        </p>
                        <p className={scene.audio_stale ? 'danger small' : 'muted small'}>
                          {scene.audio_stale
                            ? 'Lời thoại đã đổi. Cần nhập lại giọng trước khi xuất có tiếng.'
                            : 'Ảnh/clip tối đa 20 MiB. Audio/clip tối đa 19,65s. Clip tắt tiếng gốc, dùng giọng riêng.'}
                        </p>
                        {scene.image_id && sourceWarnings[scene.image_id] && (
                          <p className="source-warning">
                            Nguồn có độ phân giải thấp. Xuất 1080p không tạo thêm chi tiết thật; nên
                            thay nguồn nét hơn.
                          </p>
                        )}
                        {step === 2 && (
                          <div className="info-box">
                            <strong>Giọng đọc: nhập tệp của bạn</strong>
                            <p>
                              VieNeu chưa tích hợp ở M1. Không có âm thanh AI giả. Phụ đề hiện theo
                              phân đoạn ước lượng, chưa căn từng từ.
                            </p>
                          </div>
                        )}
                      </>
                    ) : (
                      <p className="muted">Chọn hoặc thêm một cảnh để chỉnh sửa.</p>
                    )}
                  </section>
                </div>
              )}
              {step === 3 && (
                <div className="export-layout">
                  <section className="card">
                    <p className="eyebrow">KIỂM TRA TRƯỚC KHI XUẤT</p>
                    <h2>Để câu chuyện sẵn sàng lên hình</h2>
                    <label>
                      Tỷ lệ xuất
                      <select
                        disabled={busy || !!running}
                        value={project.aspect}
                        onChange={(e) => update({ aspect: e.target.value as Project['aspect'] })}
                      >
                        <option value="portrait">9:16 · Dọc như điện thoại</option>
                        <option value="landscape">16:9 · Ngang</option>
                      </select>
                    </label>
                    {project.aspect === 'landscape' && (
                      <p className="info-box small">
                        Video ngang dùng cho video YouTube thông thường hoặc nơi hỗ trợ 16:9; không
                        tự trở thành Shorts.
                      </p>
                    )}
                    <div className="export-specs">
                      <span>{project.aspect === 'landscape' ? '16:9' : '9:16'}</span>
                      <span>{project.aspect === 'landscape' ? '1920×1080' : '1080×1920'}</span>
                      <span>30 fps</span>
                      <span>{duration(project.scenes).toFixed(1)} giây</span>
                    </div>
                    <label className="checkbox">
                      <input
                        type="checkbox"
                        checked={captions}
                        disabled={busy || !!running}
                        onChange={(e) => setCaptions(e.target.checked)}
                      />{' '}
                      Hiện phụ đề · phân đoạn theo cảnh
                    </label>
                    <label className="checkbox">
                      <input
                        type="checkbox"
                        checked={silent}
                        disabled={busy || !!running}
                        onChange={(e) => setSilent(e.target.checked)}
                      />{' '}
                      Tôi chủ động xuất không lời đọc
                    </label>
                    {silent && (
                      <p className="info-box small">
                        Video này không có lời đọc. Có thể thêm giọng/nhạc có quyền trong công cụ
                        biên tập sau.
                      </p>
                    )}
                    {issues.length ? (
                      <ul className="preflight">
                        {issues.map((message) => (
                          <li key={message}>{message}</li>
                        ))}
                      </ul>
                    ) : (
                      <p className="ready">
                        <Check size={18} /> Đủ ảnh và cấu hình để dựng video.
                      </p>
                    )}
                    <div className="button-row">
                      <button
                        className="button"
                        disabled={busy || !!running || !!issues.length}
                        onClick={() => task(() => startExport('preview'))}
                      >
                        Dựng xem thử
                      </button>
                      <button
                        className="button primary"
                        disabled={busy || !!running || !!issues.length}
                        onClick={() => task(() => startExport('export'))}
                      >
                        <Film size={17} /> Xuất MP4 1080p
                      </button>
                    </div>
                    {issues.length > 0 && (
                      <p className="muted small">
                        Sửa các mục trên để mở nút xuất. Tệp thành phẩm không có watermark.
                      </p>
                    )}
                    <hr />
                    <h3>Chuẩn bị đăng</h3>
                    <label>
                      Phân loại đối tượng
                      <select value={audience} onChange={(e) => setAudience(e.target.value)}>
                        <option value="pending">Chưa xác nhận — cần review</option>
                        <option value="made_for_kids">Tôi xác định là nội dung dành cho trẻ</option>
                        <option value="general_audience">Tôi xác định là khán giả phổ thông</option>
                      </select>
                    </label>
                    <label>
                      Quyền dùng tài nguyên
                      <select value={rights} onChange={(e) => setRights(e.target.value)}>
                        <option value="pending">Chưa xác nhận</option>
                        <option value="owned">Tôi sở hữu tài nguyên</option>
                        <option value="licensed">Tôi có quyền sử dụng phù hợp</option>
                      </select>
                    </label>
                    <button className="button" disabled={busy} onClick={() => task(downloadPack)}>
                      <Download size={17} /> Tải metadata & checklist
                    </button>
                    <section className="upload-hub">
                      <h3>Liên kết đăng video</h3>
                      <p className="muted small">{hub?.note}</p>
                      <div className="button-row">
                        {hub &&
                          Object.entries(hub.providers).map(([id, p]) => (
                            <a
                              key={id}
                              className="button"
                              target="_blank"
                              rel="noreferrer noopener"
                              href={p.upload_url}
                              title={p.account_note}
                            >
                              Mở {p.label}
                            </a>
                          ))}
                      </div>
                      <p className="muted small">
                        Chưa kết nối OAuth/API. Đây là link đăng thủ công, không tự gửi tệp hoặc
                        đăng bài.
                      </p>
                    </section>
                    <p className="muted small">
                      Creator tự đăng và quyết định audience. Made-for-kids không bảo đảm xuất hiện
                      trên YouTube Kids; app không tự đăng hay bảo đảm viral.
                    </p>
                  </section>
                  <section className="card result-panel">
                    <div className="section-top">
                      <h3>Video của bạn</h3>
                      <span className="badge neutral">
                        {job?.options.kind === 'preview' ? 'Xem thử 360p' : 'Thành phẩm'}
                      </span>
                    </div>
                    {job?.state === 'succeeded' && job.result_id ? (
                      <>
                        <video
                          ref={videoRef}
                          className={job.options.aspect === 'landscape' ? 'landscape-result' : ''}
                          controls
                          playsInline
                          src={asset(job.result_id)}
                          aria-label="Video whiteboard thành phẩm"
                        />
                        <a
                          className="button primary download-button"
                          href={asset(job.result_id)}
                          download={`whiteboard-${job.id}.mp4`}
                        >
                          <Download size={18} /> Tải MP4{' '}
                          {job.options.kind === 'preview' ? '360p' : '1080p'}
                        </a>
                        <p className="muted small">
                          File thuộc phiên bản {job.revision}. Chỉnh sửa mới không thay file này.
                        </p>
                      </>
                    ) : (
                      <div className="result-placeholder">
                        <Film size={40} />
                        <h3>{running ? 'Đang dựng câu chuyện…' : 'Video sẽ xuất hiện tại đây'}</h3>
                        <p>
                          {job?.error ||
                            (job?.state === 'cancelled'
                              ? 'Tác vụ đã hủy. Dự án và file xuất trước vẫn được giữ.'
                              : 'Bản xem thử và file xuất đều được dựng thật bằng renderer local.')}
                        </p>
                      </div>
                    )}
                    {job && (
                      <div className="job-status" role="status">
                        <span>
                          {
                            (
                              {
                                queued: 'Đang chờ worker',
                                running: 'Đang vẽ và mã hóa',
                                succeeded: 'Đã xuất và kiểm tệp',
                                cancelled: 'Đã hủy',
                                failed: 'Xuất thất bại',
                                interrupted: 'Worker bị gián đoạn',
                              } as Record<string, string>
                            )[job.state]
                          }
                        </span>
                        <progress value={job.progress} max={1} />
                        {running && (
                          <button
                            className="button"
                            disabled={busy}
                            onClick={() =>
                              task(async () => {
                                setJob(
                                  await api<Job>(`/jobs/${job.id}/cancel`, { method: 'POST' }),
                                );
                                exportKey.current = null;
                              })
                            }
                          >
                            Hủy tác vụ
                          </button>
                        )}
                        {['failed', 'interrupted', 'cancelled'].includes(job.state) && (
                          <button
                            className="button"
                            onClick={() => {
                              exportKey.current = null;
                              setJob(null);
                            }}
                          >
                            Chuẩn bị xuất lại
                          </button>
                        )}
                      </div>
                    )}
                    {job && ['succeeded', 'failed'].includes(job.state) && (
                      <QualityPanel
                        key={job.id}
                        projectId={project.id}
                        jobId={job.id}
                        onSeek={(time) => {
                          if (videoRef.current) {
                            videoRef.current.pause();
                            videoRef.current.currentTime = time;
                            videoRef.current.scrollIntoView({ block: 'center' });
                          }
                        }}
                      />
                    )}
                  </section>
                </div>
              )}
              <footer className="workspace-footer">
                <span>
                  <ShieldCheck size={14} /> Nội dung có ý nghĩa. Trải nghiệm vừa đủ.
                </span>
                <span>M2 · Planner và ảnh AI local cần model · Luôn có bước duyệt</span>
              </footer>
            </>
          )}
        </div>
      </main>
    </div>
  );
}

createRoot(document.getElementById('root')!).render(<App />);
