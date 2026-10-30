export async function api<T>(url: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set('X-Studio-Client', 'local');
  if (options.body && !(options.body instanceof FormData))
    headers.set('Content-Type', 'application/json');
  const response = await fetch(`/api${url}`, { ...options, headers });
  const data = await response.json().catch(() => null);
  if (!response.ok)
    throw new Error(data?.message || 'Không thể liên lạc dịch vụ. Dữ liệu đã lưu vẫn được giữ.');
  if (data === null) throw new Error('Dịch vụ trả phản hồi không hợp lệ. Hãy thử lại.');
  return data as T;
}
