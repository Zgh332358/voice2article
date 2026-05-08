#!/usr/bin/env bash
#
# 关掉 demo-up.sh 拉起的后端和前端进程。
# 不删 dev.db / 不动 .env，下次起还能复用。

set -u

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PID_DIR="${PROJECT_ROOT}/.demo"

GREEN=$'\033[32m'
DIM=$'\033[90m'
RESET=$'\033[0m'

stop_one() {
  local name="$1" pid_file="${PID_DIR}/$1.pid"
  if [[ -f "${pid_file}" ]]; then
    local pid
    pid=$(cat "${pid_file}")
    if kill "${pid}" 2>/dev/null; then
      printf "${GREEN}✓${RESET} 关闭 %s (pid=%s)\n" "${name}" "${pid}"
    else
      printf "${DIM}-${RESET} %s (pid=%s) 已不在\n" "${name}" "${pid}"
    fi
    rm -f "${pid_file}"
  else
    printf "${DIM}-${RESET} 没找到 %s.pid\n" "${name}"
  fi
}

stop_one backend
stop_one frontend

# 清掉 demo-up 写的 vite 代理覆盖
rm -f "${PROJECT_ROOT}/frontend/.env.local"

# 注意：不做端口扫描兜底 —— 之前会误杀 8000 上别的 uvicorn 项目
# 如果 backend.pid 丢了进程没关，手动 lsof -nP -iTCP:8000 -sTCP:LISTEN 看 PID 再 kill

echo "demo 已关闭。dev.db 和 .env 保留，可再次 bash scripts/demo-up.sh"
