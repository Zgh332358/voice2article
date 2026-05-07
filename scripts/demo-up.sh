#!/usr/bin/env bash
#
# 一键启 demo：后端（uvicorn）+ 前端（vite dev）+ seed demo 数据。
#
# 用法：
#   bash scripts/demo-up.sh                  # 默认 backend 8000 / frontend 5173
#   BACKEND_PORT=8003 bash scripts/demo-up.sh
#
# 关掉：bash scripts/demo-down.sh

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
PID_DIR="${PROJECT_ROOT}/.demo"
mkdir -p "${PID_DIR}"

GREEN=$'\033[32m'
YELLOW=$'\033[33m'
DIM=$'\033[90m'
RESET=$'\033[0m'

log() { printf "${DIM}[demo]${RESET} %s\n" "$1"; }
ok() { printf "${GREEN}✓${RESET} %s\n" "$1"; }
warn() { printf "${YELLOW}!${RESET} %s\n" "$1"; }

# 端口被占用就退出，让用户自己换或先 demo-down
if lsof -nP -iTCP:${BACKEND_PORT} -sTCP:LISTEN >/dev/null 2>&1; then
  warn "端口 ${BACKEND_PORT} 被占用 —— 先关掉占用者，或 BACKEND_PORT=xxxx bash scripts/demo-up.sh"
  exit 1
fi
if lsof -nP -iTCP:${FRONTEND_PORT} -sTCP:LISTEN >/dev/null 2>&1; then
  warn "端口 ${FRONTEND_PORT} 被占用 —— 先关掉占用者，或 FRONTEND_PORT=xxxx bash scripts/demo-up.sh"
  exit 1
fi

# 后端
log "启动后端（${BACKEND_PORT}）"
cd "${PROJECT_ROOT}/backend"
uv run alembic upgrade head >/dev/null
nohup uv run uvicorn app.main:app --host 127.0.0.1 --port "${BACKEND_PORT}" \
  > "${PID_DIR}/backend.log" 2>&1 &
echo $! > "${PID_DIR}/backend.pid"
sleep 1
for _ in {1..20}; do
  curl -sf "http://127.0.0.1:${BACKEND_PORT}/api/v1/health" >/dev/null 2>&1 && break
  sleep 0.5
done
curl -sf "http://127.0.0.1:${BACKEND_PORT}/api/v1/health" >/dev/null 2>&1 \
  || { warn "后端未就绪，看 ${PID_DIR}/backend.log"; exit 2; }
ok "后端 → http://127.0.0.1:${BACKEND_PORT}/docs"

# Seed demo 数据
log "Seed demo 数据"
BASE_URL="http://127.0.0.1:${BACKEND_PORT}/api/v1" \
  FRONTEND_URL="http://localhost:${FRONTEND_PORT}" \
  uv run python "${PROJECT_ROOT}/scripts/seed-demo.py" | sed 's/^/   /'

# 前端
log "启动前端（${FRONTEND_PORT}）"
cd "${PROJECT_ROOT}/frontend"
nohup pnpm dev --port "${FRONTEND_PORT}" \
  > "${PID_DIR}/frontend.log" 2>&1 &
echo $! > "${PID_DIR}/frontend.pid"
sleep 2
for _ in {1..20}; do
  curl -sf "http://localhost:${FRONTEND_PORT}/" >/dev/null 2>&1 && break
  sleep 0.5
done
curl -sf "http://localhost:${FRONTEND_PORT}/" >/dev/null 2>&1 \
  || { warn "前端未就绪，看 ${PID_DIR}/frontend.log"; exit 3; }
ok "前端 → http://localhost:${FRONTEND_PORT}"

cat <<EOF

${GREEN}=========================================================${RESET}
  Demo 就绪 —— 打开浏览器开始演示

  入口:     http://localhost:${FRONTEND_PORT}/
  Swagger:  http://127.0.0.1:${BACKEND_PORT}/docs
  账号:     demo@aiken.dev
  密码:     demo-password-1

  日志:     ${PID_DIR}/{backend,frontend}.log
  关闭:     bash scripts/demo-down.sh
${GREEN}=========================================================${RESET}
EOF
