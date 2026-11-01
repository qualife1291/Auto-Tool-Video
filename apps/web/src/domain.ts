export type CreativeBrief = {
  topic: string;
  objective: string;
  takeaways: string[];
  target_duration: 30 | 45 | 60;
  tone: string;
  required_facts: string;
  sources: string[];
  avoid: string;
  style_bible: string;
  character_bible: string;
};
export const emptyBrief: CreativeBrief = {
  topic: '',
  objective: '',
  takeaways: [],
  target_duration: 45,
  tone: 'Ấm áp, tò mò, rõ ràng; không giật gân',
  required_facts: '',
  sources: [],
  avoid: '',
  style_bible: 'Minh họa giáo dục giàu chất liệu, nhiều lớp tiền/trung/hậu cảnh; chủ thể chính lớn, đúng tỷ lệ, nét tinh, ánh sáng và bóng đổ rõ; vật thể phụ phải giải thích hành động trong lời thoại, không lặp icon đơn giản; bố cục đầy đặn nhưng chừa vùng chữ, không chữ/logo trong ảnh.',
  character_bible: '',
};
export type Capability = {
  state: string;
  message: string;
  model?: string;
  digest?: string;
  checkpoint?: string;
};
export type Capabilities = { script: Capability; image: Capability };
export type CandidateVisualReview = {
  policy: string;
  method: string;
  width: number;
  height: number;
  edge_fraction: number;
  occupied_tile_fraction: number;
  coarse_palette_bins: number;
  warnings: { code: string; message: string }[];
  semantic_review: 'not_performed';
  aesthetic_review: 'not_performed';
  human_approval: 'pending';
};

export type GenerationJob = {
  id: string;
  project_id: string;
  revision: number;
  state: string;
  progress: number;
  error: string | null;
  error_code?: string;
  applied_revision?: number;
  options: {
    kind: 'plan' | 'image';
    mode?: 'brief' | 'preserve';
    scene_id?: string;
    seed?: number;
  };
  result?: {
    proposal?: {
      title: string;
      mode: 'brief' | 'preserve';
      source_preserved: boolean;
      review_required: boolean;
      scenes: Scene[];
    };
    candidate_id?: string;
    provenance?: Record<string, string | number>;
    visual_review?: CandidateVisualReview;
  };
};
export type SecondBeat = {
  second: number;
  visual_state: string;
  action: string;
  camera: string;
  on_screen_text: string;
  narration_cue: string;
  continuity: string;
};
export type Scene = {
  second_by_second?: SecondBeat[];
  beat_plan_status?: 'authored' | 'needs_review';
  id: string;
  title: string;
  narration: string;
  image_prompt: string;
  image_id: string | null;
  audio_id: string | null;
  audio_stale: boolean;
  duration: number;
  style: 'whiteboard' | 'motion';
  caption_style?: 'card' | 'contrast' | 'accent';
  caption_emphasis?: string;
  motion_expectation?: 'allow_static' | 'motion_required';
  layout?: 'board' | 'full_frame';
  visual_fit?: 'contain' | 'cover';
  focal_x?: number;
  focal_y?: number;
  transition?: 'cut' | 'dissolve';
  draw_fraction?: number;
  visual_description?: string;
  role?: string;
  reveal_order?: string[];
  fact_flags?: string[];
  source_refs?: number[];
};
export function captionParts(text: string, phrase: string) {
  const pattern = phrase
    .trim()
    .split(/\s+/)
    .filter(Boolean)
    .map((part) => part.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'))
    .join('\\s+');
  const match = pattern ? new RegExp(pattern, 'iu').exec(text) : null;
  if (!match) return [{ text, emphasis: false }];
  return [
    { text: text.slice(0, match.index), emphasis: false },
    { text: match[0], emphasis: true },
    { text: text.slice(match.index + match[0].length), emphasis: false },
  ];
}

/** Browser-only, character-budget preview; PIL/FreeType export remains authoritative. */
export function estimateCaptionPages(text: string, aspect: 'portrait' | 'landscape'): string[] {
  const words = text.trim().split(/\s+/u).filter(Boolean);
  if (!words.length) return [];

  // Conservative approximate line budgets, not pixel measurements of the backend font.
  const limit = aspect === 'portrait' ? 28 : 48;
  const linesFor = (items: string[]): string[] => {
    const lines: string[] = [];
    let line = '';
    for (const word of items) {
      const candidate = line ? `${line} ${word}` : word;
      if (line && Array.from(candidate).length > limit) {
        lines.push(line);
        line = word;
      } else {
        line = candidate;
      }
    }
    if (line) lines.push(line);
    return lines;
  };

  const lines = linesFor(words);
  const pages: string[] = [];
  for (let i = 0; i < lines.length; i += 2) pages.push(lines.slice(i, i + 2).join('\n'));

  // Rebalance just the final two pages when a greedy wrap leaves a one-word orphan.
  if (pages.length > 1 && pages[pages.length - 1].split(/\s+/u).length < 3) {
    const index = pages.length - 2;
    const tail = `${pages[index]} ${pages[index + 1]}`.trim().split(/\s+/u);
    let best: { first: string; last: string; score: number } | null = null;
    for (let split = 3; split <= tail.length - 3; split++) {
      const first = linesFor(tail.slice(0, split));
      const last = linesFor(tail.slice(split));
      if (first.length > 2 || last.length > 2) continue;
      const score = Math.abs(split - (tail.length - split));
      if (!best || score < best.score) {
        best = { first: first.join('\n'), last: last.join('\n'), score };
      }
    }
    if (best) {
      pages[index] = best.first;
      pages[index + 1] = best.last;
    }
  }
  return pages;
}

export type Project = {
  id: string;
  title: string;
  profile: string;
  platform: string;
  narration: string;
  aspect: 'portrait' | 'landscape';
  revision: number;
  scenes: Scene[];
  brief?: CreativeBrief;
  created_at: string;
  updated_at: string;
};
export type Job = {
  id: string;
  project_id: string;
  state: string;
  progress: number;
  revision: number;
  result_id: string | null;
  error: string | null;
  options: { kind: string; silent: boolean; captions: boolean; aspect: 'portrait' | 'landscape' };
};
export const profiles = [
  ['preschool', 'Mầm non · 3–4 tuổi', 'Một ý, vật quen thuộc, nhịp chậm. Người lớn đồng hành.'],
  [
    'kids',
    'Khám phá · 5–8 tuổi',
    'Câu ngắn, một ý mỗi cảnh. Giải thích trước khi gọi tên thuật ngữ.',
  ],
  [
    'older_kids',
    'Tìm hiểu · 9–12 tuổi',
    'Có cơ chế, ví dụ và câu hỏi suy luận; kiểm nguồn kiến thức.',
  ],
  ['family', 'Cả nhà · 6+', 'Dễ hiểu với trẻ, có điều hữu ích cho người lớn.'],
  [
    'general',
    'Khán giả phổ thông',
    'Cô đọng, chính xác. Profile không tự quyết định made-for-kids.',
  ],
] as const;
export const steps = ['Kịch bản', 'Storyboard', 'Giọng & nhịp', 'Xuất video'];
export const example = [
  'Áo vừa giặt còn ướt. Một lúc sau lại khô. Nước đã đi đâu?',
  'Nước thấm giữa các sợi vải. Ta cùng phóng to để xem nhé!',
  'Nước gồm những phần tử rất nhỏ, gọi là các phân tử.',
  'Ở bề mặt, một số phân tử nước thoát vào không khí.',
  'Nước lỏng chuyển thành hơi nước. Quá trình này gọi là bay hơi.',
  'Hơi nước thường vô hình. Những chấm xanh chỉ là hình minh họa.',
  'Bay hơi không cần nước sôi. Áo trong nhà vẫn có thể khô.',
  'Nơi ấm thường giúp nước bay hơi nhanh hơn. Nhưng còn một yếu tố nữa!',
  'Gió đưa không khí ẩm quanh áo đi, giúp nước tiếp tục bay hơi.',
  'Không khí quá ẩm thường làm áo lâu khô hơn, ngay cả khi trời nóng.',
  'Trải áo rộng, treo nơi thoáng, để nhiều bề mặt tiếp xúc với không khí.',
  'Nước không biến mất: nó chuyển vào không khí. Bạn thử quan sát chiếc khăn ướt nhé!',
].join('\n');
export function duration(scenes: Scene[]) {
  return scenes.reduce((total, scene) => total + scene.duration, 0);
}
export function preflight(project: Project, silent: boolean) {
  const errors: string[] = [];
  if (!project.scenes.length) errors.push('Chưa có cảnh. Chia lời thoại ở bước Kịch bản.');
  if (duration(project.scenes) > 60) errors.push('Tổng thời lượng vượt 60 giây. Rút gọn các cảnh.');
  project.scenes.forEach((scene, i) => {
    if (!scene.image_id) errors.push(`Cảnh ${i + 1}: chưa có ảnh.`);
    if (!silent && !scene.audio_id) errors.push(`Cảnh ${i + 1}: chưa có giọng đọc.`);
    if (!silent && scene.audio_stale)
      errors.push(`Cảnh ${i + 1}: lời thoại đã đổi, cần thu lại giọng.`);
  });
  return errors;
}
export function sourceNeedsUpscale(
  width: number,
  height: number,
  aspect: 'portrait' | 'landscape',
  layout: Scene['layout'] = 'board',
  fit: Scene['visual_fit'] = 'contain',
) {
  if (width <= 0 || height <= 0) return true;
  const [boxWidth, boxHeight] =
    layout === 'full_frame'
      ? aspect === 'landscape'
        ? [1920, 1080]
        : [1080, 1920]
      : aspect === 'landscape'
        ? [1440, 580]
        : [810, 850];
  const ratio =
    layout === 'full_frame' && fit === 'cover'
      ? Math.max(boxWidth / width, boxHeight / height)
      : Math.min(boxWidth / width, boxHeight / height);
  return ratio > 1;
}
