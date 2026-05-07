#!/usr/bin/env bash
#
# W2 验收脚本 —— 端到端打通：
#   1) 起后端（如未运行）
#   2) 注册新用户拿 token
#   3) 调真 Step ASR /stt/transcribe（macOS say 生成测试音频）
#   4) 创建会话 → 把转写文本作为消息追加 → 列表 / 详情 / 删除
#
# 使用：
#   bash scripts/w2-smoke.sh                  # 用 8000 端口
#   PORT=8765 bash scripts/w2-smoke.sh        # 自定义端口
#   KEEP_BACKEND=1 bash scripts/w2-smoke.sh   # 不停掉本进程拉起的后端
#
# 退出码：0 = 全部通过，>0 = 第一个失败的步骤号

set -euo pipefail

PORT="${PORT:-8000}"
BASE_URL="http://127.0.0.1:${PORT}/api/v1"
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
EMAIL="w2-smoke-$(date +%s)@aiken.dev"
PASSWORD="smokepass1"

GREEN=$'\033[32m'
RED=$'\033[31m'
DIM=$'\033[90m'
RESET=$'\033[0m'

step() { printf "\n${DIM}── %s ──${RESET}\n" "$1"; }
ok() { printf "${GREEN}✓${RESET} %s\n" "$1"; }
fail() { printf "${RED}✗${RESET} %s\n" "$1"; exit "${2:-1}"; }

cleanup() {
  if [[ -n "${BACKEND_PID:-}" && "${KEEP_BACKEND:-0}" != "1" ]]; then
    kill "$BACKEND_PID" 2>/dev/null || true
  fi
  rm -f /tmp/w2_smoke.aiff /tmp/w2_smoke.wav /tmp/w2_resp.json
}
trap cleanup EXIT

# 0. 后端是否已经在跑？没在跑则起一个
if curl -sf "${BASE_URL}/health" > /dev/null 2>&1; then
  step "后端已在 ${PORT} 运行，复用"
else
  step "启动后端（${PORT}）"
  cd "${PROJECT_ROOT}/backend"
  uv run uvicorn app.main:app --host 127.0.0.1 --port "${PORT}" \
    > /tmp/w2-smoke-backend.log 2>&1 &
  BACKEND_PID=$!
  for _ in {1..15}; do
    sleep 0.5
    if curl -sf "${BASE_URL}/health" > /dev/null 2>&1; then
      ok "backend ready (pid=${BACKEND_PID})"
      break
    fi
  done
  curl -sf "${BASE_URL}/health" > /dev/null 2>&1 \
    || fail "后端 15 秒内未就绪，看 /tmp/w2-smoke-backend.log" 0
fi

# 1. 健康检查
step "1) /health"
HEALTH=$(curl -s "${BASE_URL}/health")
echo "${HEALTH}" | grep -q '"status":"ok"' && ok "/health → ok" || fail "/health 异常: ${HEALTH}" 1

# 2. 注册取 token
step "2) /auth/register"
REG=$(curl -s -X POST "${BASE_URL}/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"${EMAIL}\",\"password\":\"${PASSWORD}\",\"nickname\":\"W2 Smoke\"}")
TOKEN=$(echo "${REG}" | python3 -c "import sys,json;print(json.load(sys.stdin).get('access_token',''))")
[[ -n "${TOKEN}" ]] && ok "拿到 token (${#TOKEN} 字符)" || fail "register 失败: ${REG}" 2
AUTH=(-H "Authorization: Bearer ${TOKEN}")

# 3. 跑 STT（真打 Step API）
step "3) /stt/transcribe（Step ASR 真调）"
say -o /tmp/w2_smoke.aiff "今天我们要写一篇关于阶跃星辰的评测文章"
afconvert -f WAVE -d LEI16@16000 -c 1 /tmp/w2_smoke.aiff /tmp/w2_smoke.wav > /dev/null
SIZE=$(stat -f%z /tmp/w2_smoke.wav)
TRANSCRIBE=$(curl -s -X POST "${BASE_URL}/stt/transcribe" \
  "${AUTH[@]}" \
  -F "file=@/tmp/w2_smoke.wav;type=audio/wav")
TEXT=$(echo "${TRANSCRIBE}" | python3 -c "import sys,json;print(json.load(sys.stdin).get('text',''))")
[[ -n "${TEXT}" ]] && ok "ASR(${SIZE}B) → \"${TEXT}\"" || fail "STT 异常: ${TRANSCRIBE}" 3

# 4. 创建会话
step "4) POST /conversations"
CONV=$(curl -s -X POST "${BASE_URL}/conversations" \
  "${AUTH[@]}" -H "Content-Type: application/json" \
  -d '{"title":"W2 烟雾测试","mode":"dialogue"}')
CID=$(echo "${CONV}" | python3 -c "import sys,json;print(json.load(sys.stdin).get('id',''))")
[[ -n "${CID}" ]] && ok "会话创建 ${CID}" || fail "create conv 异常: ${CONV}" 4

# 5. 追加消息（用第 3 步转写的文本）
step "5) POST /conversations/{id}/messages"
APPEND_BODY=$(TEXT_VAL="${TEXT}" python3 <<'PY'
import json, os
print(json.dumps({"role": "user", "content": os.environ["TEXT_VAL"]}, ensure_ascii=False))
PY
)
APPEND=$(curl -s -X POST "${BASE_URL}/conversations/${CID}/messages" \
  "${AUTH[@]}" -H "Content-Type: application/json" \
  -d "${APPEND_BODY}")
echo "${APPEND}" | grep -q '"role":"user"' && ok "消息追加成功" || fail "append 异常: ${APPEND}" 5

# 6. 详情验证
step "6) GET /conversations/{id} → messages 长度 == 1"
DETAIL=$(curl -s "${BASE_URL}/conversations/${CID}" "${AUTH[@]}")
N=$(echo "${DETAIL}" | python3 -c "import sys,json;print(len(json.load(sys.stdin).get('messages',[])))")
[[ "${N}" == "1" ]] && ok "messages 长度 == 1" || fail "详情消息数 ${N}" 6

# 7. 列表
step "7) GET /conversations → total >= 1"
LIST=$(curl -s "${BASE_URL}/conversations?limit=10" "${AUTH[@]}")
TOTAL=$(echo "${LIST}" | python3 -c "import sys,json;print(json.load(sys.stdin).get('total',0))")
[[ "${TOTAL}" -ge 1 ]] && ok "列表 total=${TOTAL}" || fail "列表 total ${TOTAL}" 7

# 8. 删除
step "8) DELETE /conversations/{id} → 204 + 后续 404"
DEL_CODE=$(curl -s -o /dev/null -w '%{http_code}' -X DELETE \
  "${BASE_URL}/conversations/${CID}" "${AUTH[@]}")
[[ "${DEL_CODE}" == "204" ]] && ok "DELETE → 204" || fail "DELETE → ${DEL_CODE}" 8

GET_CODE=$(curl -s -o /dev/null -w '%{http_code}' \
  "${BASE_URL}/conversations/${CID}" "${AUTH[@]}")
[[ "${GET_CODE}" == "404" ]] && ok "已删除会话再读 → 404" || fail "删除后读 → ${GET_CODE}" 8

# 9. 越权检查
step "9) 不带 token → 401"
NO_AUTH_CODE=$(curl -s -o /dev/null -w '%{http_code}' "${BASE_URL}/conversations")
[[ "${NO_AUTH_CODE}" == "401" ]] && ok "无 token → 401" || fail "无 token → ${NO_AUTH_CODE}" 9

printf "\n${GREEN}全部 9 步通过 ✓${RESET}\n"
