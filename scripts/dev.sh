#!/usr/bin/env bash
set -euo pipefail
studio_repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd "$studio_repo"
export APP_DATA_DIR="${APP_DATA_DIR:-$studio_repo/.data}"
export APP_PORT="${APP_PORT:-8765}"
if [[ ! -x backend/.venv/bin/python ]]; then
  echo 'Chạy uv sync --project backend --frozen --group dev trước.' >&2
  exit 1
fi
studio_pids=()
studio_cleanup() {
  for studio_pid in "${studio_pids[@]}"; do
    kill -TERM -- "-$studio_pid" 2>/dev/null || true
  done
}
trap studio_cleanup EXIT INT TERM
# Each process group is ours; interrupting the launcher also stops its encoder children.
setsid backend/.venv/bin/python -m auto_tool_video.worker &
studio_pids+=("$!")
setsid backend/.venv/bin/uvicorn auto_tool_video.api:create_app --factory --host 127.0.0.1 --port "$APP_PORT" --no-access-log &
studio_pids+=("$!")
echo "Studio local started; API/static port $APP_PORT."
if [[ "${STUDIO_WEB_DEV:-0}" == 1 ]]; then
  setsid npm --prefix apps/web run dev &
  studio_pids+=("$!")
fi
wait -n "${studio_pids[@]}"
