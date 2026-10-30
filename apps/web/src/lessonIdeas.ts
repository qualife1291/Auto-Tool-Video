import { emptyBrief, type CreativeBrief } from './domain';

// Original Vietnamese briefs. External lessons are references, never fetched or executed.
export const lessonIdeas = [
  {
    slug: 'water-cycle-step',
    title: 'Một giọt nước đi đâu?',
    objective: 'Phân biệt bay hơi, ngưng tụ và mưa bằng một hành trình ngắn.',
    facts:
      'Hơi nước thường vô hình. Mây gồm các giọt nước nhỏ hoặc tinh thể băng. Không đồng nhất mây với hơi nước.',
    age: 'Cả nhà · 6+',
  },
  {
    slug: 'brownian-step',
    title: 'Hạt nhỏ chuyển động vì sao?',
    objective:
      'Hiểu rằng chuyển động Brown là chuyển động ngẫu nhiên của hạt do va chạm với các phân tử môi trường.',
    facts:
      'Phân biệt hạt quan sát được và các phân tử không nhìn thấy bằng mắt thường; minh họa hạt không phải ảnh phân tử thực.',
    age: 'Tìm hiểu · 9–12+; cần giải thích từ mới',
  },
  {
    slug: 'earth-motion-step',
    title: 'Vì sao có ngày và đêm?',
    objective: 'Dùng một quả địa cầu quay để giải thích mặt được Mặt Trời chiếu sáng.',
    facts:
      'Ngày đêm chủ yếu do Trái Đất tự quay. Không giải thích mùa bằng khoảng cách tới Mặt Trời. Kích thước và khoảng cách mô hình không theo tỷ lệ.',
    age: 'Cả nhà · 6+',
  },
  {
    slug: 'river-step',
    title: 'Dòng sông làm đổi bờ như thế nào?',
    objective: 'Phân biệt xói mòn và bồi tụ bằng một khúc sông uốn cong.',
    facts:
      'Giải thích xu hướng xói mòn bờ ngoài và bồi tụ bờ trong ở khúc uốn bằng mô hình đơn giản; tránh khẳng định mọi con sông đều giống nhau.',
    age: 'Tìm hiểu · 9–12+',
  },
] as const;

export function briefFromIdea(idea: (typeof lessonIdeas)[number]): CreativeBrief {
  return {
    ...emptyBrief,
    takeaways: [idea.objective],
    topic: idea.title,
    objective: idea.objective,
    target_duration: 45,
    required_facts: idea.facts,
    sources: [`https://lab.tongjiang.app/c/${idea.slug}/`],
    avoid:
      'Không hướng dẫn thí nghiệm nguy hiểm. Người lớn duyệt kiến thức và độ tuổi. Không sao chép hình, chữ hoặc mã bài tham khảo khi chưa kiểm quyền sử dụng.',
    style_bible:
      'Minh họa khoa học nguyên bản, hình khối rõ và chi tiết có mục đích, palette nhất quán, không chữ trong ảnh. Mỗi cảnh chỉ giải thích một ý; nhãn do editor dựng.',
  };
}
