import { useEffect, useState } from 'react';
import { api } from './api';

export const criteriaLabels = {
  prompt_alignment: 'Khớp kịch bản / prompt',
  motion_smoothness: 'Chuyển động mượt',
  temporal_consistency: 'Nhất quán thời gian',
  physical_plausibility: 'Logic vật lý',
  technical_quality: 'Chất lượng kỹ thuật',
} as const;
type Criterion = keyof typeof criteriaLabels;
type Rating = { score: number | null; critical: boolean; note: string; at_seconds: number | null };
type Review = {
  reviewer: string;
  criteria: Partial<Record<Criterion, Rating>>;
  watched_full: boolean;
  listened_audio: boolean;
  checked_captions: boolean;
  checked_facts_age: boolean;
  disclosure_reviewed: boolean;
  content_origin: 'unknown' | 'ai_assisted' | 'no_ai';
  disclosure_note: string;
  acknowledged_findings: string[];
};
type Quality = {
  policy_version: string;
  pacing?:
    | {
        status: 'measured';
        silence_seconds: number;
        silence_ratio: number;
        longest_interval_seconds: number;
      }
    | { status: 'not_applicable'; reason: string };
  artifact?: { sha256: string; duration: number; silent: boolean; captions: boolean };
  technical?: {
    status: string;
    checks: { id: string; status: string; message: string; actual: unknown }[];
  };
  signals?: {
    findings: { id: string; timestamp: number; scene: number; message: string; remedy: string }[];
    scenes?: unknown[];
  };
  expected_scenes?: {
    id: string;
    title: string;
    narration: string;
    image_prompt: string;
    image_id: string | null;
  }[];
  benchmarks: { name: string; status: string; reason: string }[];
  gate: { status: string; reasons: string[] };
  manual_review?: Review | null;
  review_revision?: number;
};
const blankRating = (): Rating => ({ score: null, critical: false, note: '', at_seconds: null });
const blankReview = (): Review => ({
  reviewer: '',
  criteria: {},
  watched_full: false,
  listened_audio: false,
  checked_captions: false,
  checked_facts_age: false,
  disclosure_reviewed: false,
  content_origin: 'unknown',
  disclosure_note: '',
  acknowledged_findings: [],
});
export function reviewDraft(review: Partial<Review> | null | undefined): Review {
  const empty = blankReview();
  // Server-only metadata (saved_at) belongs in the report, never in a strict update payload.
  return Object.fromEntries(
    (Object.keys(empty) as (keyof Review)[]).map((key) => [key, review?.[key] ?? empty[key]]),
  ) as Review;
}
const gateLabels: Record<string, string> = {
  pending_review: 'Cần người duyệt',
  approved: 'Creator đã duyệt chất lượng',
  rejected: 'Loại bản này — cần làm lại',
  revise: 'Cần sửa trước khi duyệt',
  blocked: 'Chưa đạt cổng kỹ thuật',
  unavailable: 'Chưa có báo cáo QC',
};

export function QualityPanel({
  projectId,
  jobId,
  onSeek,
}: {
  projectId: string;
  jobId: string;
  onSeek: (time: number) => void;
}) {
  const path = `/projects/${projectId}/exports/${jobId}`;
  const [report, setReport] = useState<Quality | null>(null);
  const [draft, setDraft] = useState<Review>(blankReview);
  const [busy, setBusy] = useState(false);
  const [dirty, setDirty] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  useEffect(() => {
    let active = true;
    api<Quality>(`${path}/quality`)
      .then((value) => {
        if (active) {
          setReport(value);
          setDraft(reviewDraft(value.manual_review));
        }
      })
      .catch((e) => {
        if (active) setError(e.message);
      });
    return () => {
      active = false;
    };
  }, [path]);
  function update(patch: Partial<Review>) {
    setDraft({ ...draft, ...patch });
    setDirty(true);
    setNotice('');
  }
  function rate(key: Criterion, patch: Partial<Rating>) {
    update({
      criteria: {
        ...draft.criteria,
        [key]: { ...blankRating(), ...draft.criteria[key], ...patch },
      },
    });
  }
  async function reload() {
    if (dirty && !window.confirm('Tải lại sẽ bỏ phần phiếu chưa lưu. Tiếp tục?')) return;
    setBusy(true);
    setError('');
    try {
      const value = await api<Quality>(`${path}/quality`);
      setReport(value);
      setDraft(reviewDraft(value.manual_review));
      setDirty(false);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Không tải được phiếu.');
    } finally {
      setBusy(false);
    }
  }
  async function save() {
    if (!report?.artifact) return;
    setBusy(true);
    setError('');
    setNotice('');
    try {
      const saved = await api<Quality>(`${path}/quality-review`, {
        method: 'PUT',
        body: JSON.stringify({
          ...draft,
          video_sha256: report.artifact.sha256,
          review_revision: report.review_revision,
        }),
      });
      setReport(saved);
      setDraft(reviewDraft(saved.manual_review));
      setDirty(false);
      setNotice('Đã lưu phiếu cho đúng file video này.');
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Không lưu được phiếu.');
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="quality-panel" aria-label="Kiểm định video sau gen">
      <h3>Kiểm định sau khi dựng</h3>
      <p className="muted small">
        Máy kiểm tệp và gợi ý mốc cần xem. Creator duyệt nội dung, chuyển động, vật lý và cảm nhận.
      </p>
      {error && (
        <p role="alert" className="error-box">
          {error}
        </p>
      )}
      {notice && <p role="status">{notice}</p>}
      {!report && !error && <p role="status">Đang tải báo cáo QC…</p>}
      {report && (
        <>
          <p className="qc-gate" role="status">
            {gateLabels[report.gate.status] || report.gate.status}
          </p>
          {report.gate.reasons.length > 0 && (
            <ul className="small">
              {report.gate.reasons.map((reason) => (
                <li key={reason}>{reason}</li>
              ))}
            </ul>
          )}
          <div className="button-row">
            <a className="button" href={`/api${path}/quality`} download="quality-report.json">
              Tải báo cáo QC JSON
            </a>
            <a className="button" href={`/api${path}/quality.csv`} download="quality-review.csv">
              Tải phiếu QC CSV
            </a>
            <button className="button" disabled={busy} onClick={() => void reload()}>
              Tải lại phiếu
            </button>
          </div>
          {report.technical && (
            <details>
              <summary>
                Kỹ thuật:{' '}
                {report.technical.status === 'passed' ? 'đạt kiểm tra tự động' : 'chưa đạt'}
              </summary>
              <ul className="small">
                {report.technical.checks.map((check) => (
                  <li key={check.id}>
                    <strong>
                      {check.status === 'passed'
                        ? 'Đạt'
                        : check.status === 'not_applicable'
                          ? 'Không áp dụng'
                          : 'Lỗi'}
                    </strong>{' '}
                    · {check.message} <code>{JSON.stringify(check.actual)}</code>
                  </li>
                ))}
              </ul>
            </details>
          )}
          {report.pacing && (
            <p className="small">
              {report.pacing.status === 'measured'
                ? `Nhịp lời đọc: ${report.pacing.silence_seconds.toFixed(2)} giây im lặng (${(report.pacing.silence_ratio * 100).toFixed(1)}%); đoạn dài nhất ${report.pacing.longest_interval_seconds.toFixed(2)} giây. Chỉ tính khoảng từ 0,25 giây; cần nghe lại để đánh giá nhịp.`
                : 'Nhịp lời đọc: không áp dụng vì đã chủ động chọn không lời.'}
            </p>
          )}
          {report.signals?.findings.map((finding) => (
            <article className="qc-finding" key={finding.id}>
              <button className="text-button" onClick={() => onSeek(finding.timestamp)}>
                Xem tại {finding.timestamp.toFixed(2)} giây · cảnh {finding.scene}
              </button>
              <p>{finding.message}</p>
              <p className="small muted">{finding.remedy}</p>
              <label className="checkbox">
                <input
                  type="checkbox"
                  checked={draft.acknowledged_findings.includes(finding.id)}
                  disabled={busy}
                  onChange={(e) =>
                    update({
                      acknowledged_findings: e.target.checked
                        ? [...draft.acknowledged_findings, finding.id]
                        : draft.acknowledged_findings.filter((id) => id !== finding.id),
                    })
                  }
                />
                Đã xem và đối chiếu cảnh báo này
              </label>
            </article>
          ))}
          <details>
            <summary>Đối chiếu kịch bản và hình nguồn của bản xuất</summary>
            {report.expected_scenes?.map((scene, index) => (
              <article className="qc-expected" key={scene.id}>
                <h4>
                  {index + 1}. {scene.title}
                </h4>
                <p>{scene.narration}</p>
                <p className="small">{scene.image_prompt}</p>
                {scene.image_id && (
                  <a
                    href={`/api/assets/${encodeURIComponent(scene.image_id)}`}
                    target="_blank"
                    rel="noreferrer"
                  >
                    Mở hình / clip nguồn của cảnh {index + 1}
                  </a>
                )}
              </article>
            ))}
          </details>
          <details>
            <summary>Phạm vi benchmark và phép đo</summary>
            {report.benchmarks.map((benchmark) => (
              <p className="small" key={benchmark.name}>
                {benchmark.name}: chưa chạy — {benchmark.reason}
              </p>
            ))}
            <p className="small">
              Biến động pixel/độ sáng và độ sắc nét chỉ là tín hiệu tham khảo; không phải điểm
              VBench, thước đo vật lý hoặc chứng nhận an toàn nhạy sáng.
            </p>
          </details>
          {report.artifact && (
            <fieldset disabled={busy}>
              <legend>Phiếu người duyệt · 1–5</legend>
              <p className="small">
                1: sai nghiêm trọng · 2: lỗi rõ · 3: cần sửa · 4: đạt, lỗi nhỏ không ảnh hưởng · 5:
                đạt tốt trong trường hợp đã xem. Critical hoặc điểm1–2 loại bản này; không lấy trung
                bình để bù lỗi.
              </p>
              <label>
                Người duyệt
                <input
                  maxLength={100}
                  value={draft.reviewer}
                  onChange={(e) => update({ reviewer: e.target.value })}
                />
              </label>
              {(Object.entries(criteriaLabels) as [Criterion, string][]).map(([key, label]) => {
                const rating = draft.criteria[key] || blankRating();
                return (
                  <section className="qc-rating" key={key} aria-label={label}>
                    <h4>{label}</h4>
                    <label>
                      Điểm · {label}
                      <select
                        value={rating.score ?? ''}
                        onChange={(e) =>
                          rate(key, { score: e.target.value ? Number(e.target.value) : null })
                        }
                      >
                        <option value="">Chưa chấm</option>
                        {[1, 2, 3, 4, 5].map((n) => (
                          <option key={n} value={n}>
                            {n}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label className="checkbox">
                      <input
                        type="checkbox"
                        checked={rating.critical}
                        onChange={(e) => rate(key, { critical: e.target.checked })}
                      />
                      Lỗi nghiêm trọng · {label}
                    </label>
                    <label>
                      Mốc lỗi (giây) · {label}
                      <input
                        type="number"
                        min="0"
                        max={report.artifact?.duration}
                        step="0.01"
                        value={rating.at_seconds ?? ''}
                        onChange={(e) =>
                          rate(key, { at_seconds: e.target.value ? Number(e.target.value) : null })
                        }
                      />
                    </label>
                    <label>
                      Ghi chú · {label}
                      <textarea
                        rows={2}
                        maxLength={500}
                        required={rating.critical}
                        value={rating.note}
                        onChange={(e) => rate(key, { note: e.target.value })}
                      />
                    </label>
                  </section>
                );
              })}
              {(
                [
                  ['watched_full', 'Tôi đã xem hết video ở tốc độ bình thường'],
                  ['listened_audio', 'Tôi đã nghe lời đọc trong thành phẩm'],
                  ['checked_captions', 'Tôi đã kiểm phụ đề, dấu và vùng an toàn'],
                  ['checked_facts_age', 'Tôi đã đối chiếu kiến thức và độ tuổi'],
                  ['disclosure_reviewed', 'Tôi đã xem xét nguồn gốc và nhãn AI phù hợp'],
                ] as const
              )
                .filter(
                  ([key]) =>
                    !(key === 'listened_audio' && report.artifact?.silent) &&
                    !(key === 'checked_captions' && !report.artifact?.captions),
                )
                .map(([key, label]) => (
                  <label className="checkbox" key={key}>
                    <input
                      type="checkbox"
                      checked={draft[key]}
                      onChange={(e) => update({ [key]: e.target.checked })}
                    />
                    {label}
                  </label>
                ))}
              <label>
                Nguồn gốc do creator xác nhận
                <select
                  value={draft.content_origin}
                  onChange={(e) =>
                    update({ content_origin: e.target.value as Review['content_origin'] })
                  }
                >
                  <option value="unknown">Chưa xác nhận</option>
                  <option value="ai_assisted">Có AI hỗ trợ hình / giọng / nội dung</option>
                  <option value="no_ai">Tôi xác nhận không dùng AI sinh nội dung</option>
                </select>
              </label>
              <label>
                Ghi chú minh bạch khi đăng
                <textarea
                  rows={2}
                  maxLength={500}
                  value={draft.disclosure_note}
                  onChange={(e) => update({ disclosure_note: e.target.value })}
                />
              </label>
              <p className="muted small">
                Thông tin nguồn gốc và hash giúp truy vết bản đã duyệt. Đây chưa phải chữ ký C2PA,
                watermark bền vững hoặc xác nhận tuân thủ pháp luật.
              </p>
              <button
                className="button primary"
                disabled={busy || !draft.reviewer.trim()}
                onClick={() => void save()}
              >
                {busy ? 'Đang lưu phiếu…' : 'Lưu phiếu duyệt'}
              </button>
            </fieldset>
          )}
        </>
      )}
    </section>
  );
}
