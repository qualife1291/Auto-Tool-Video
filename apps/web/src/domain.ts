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
  style_bible: 'Nét đen sạch, ít màu, nền kem, không chữ trong ảnh',
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
  };
};
export type Scene = {
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
export const example =
  'Một chiếc áo vừa giặt còn ướt. Treo một lúc, áo lại khô. Vậy nước đã đi đâu?\nNước không tự biến mất. Từng chút nước đi vào không khí dưới dạng hơi nước. Hiện tượng này gọi là bay hơi.\nNước không cần sôi mới bay hơi. Áo treo trong nhà vẫn có thể khô dù không có nắng chiếu vào.\nNơi ấm và thoáng thường giúp áo khô nhanh hơn. Theo bạn, áo trải rộng hay cuộn lại sẽ dễ khô hơn?';
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
) {
  if (width <= 0 || height <= 0) return true;
  const [boxWidth, boxHeight] = aspect === 'landscape' ? [1440, 580] : [810, 850];
  return Math.min(boxWidth / width, boxHeight / height) > 1;
}
