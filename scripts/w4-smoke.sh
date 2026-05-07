#!/usr/bin/env bash
#
# W4 验收脚本 —— 端到端打通：
#   注册 → 创建会话 → 真打 ASR → 真打 LLM 生成 → 列模板 → 真打排版
#
# 跑法：
#   bash scripts/w4-smoke.sh
#   PORT=8765 bash scripts/w4-smoke.sh
#
# 退出码：0 = 全过

set -euo pipefail

PORT="${PORT:-8000}"
BASE_URL="http://127.0.0.1:${PORT}/api/v1"
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
EMAIL="w4-smoke-$(date +%s)@aiken.dev"
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
  rm -f /tmp/w4_smoke.aiff /tmp/w4_smoke.wav /tmp/w4_html.json /tmp/w4_full.html
}
trap cleanup EXIT

# 0. 启后端
if curl -sf "${BASE_URL}/health" > /dev/null 2>&1; then
  step "后端已在 ${PORT} 运行，复用"
else
  step "启动后端（${PORT}）"
  cd "${PROJECT_ROOT}/backend"
  uv run uvicorn app.main:app --host 127.0.0.1 --port "${PORT}" \
    > /tmp/w4-smoke-backend.log 2>&1 &
  BACKEND_PID=$!
  for _ in {1..15}; do
    sleep 0.5
    curl -sf "${BASE_URL}/health" > /dev/null 2>&1 && break
  done
  curl -sf "${BASE_URL}/health" > /dev/null 2>&1 || fail "后端未就绪" 0
  ok "backend ready"
fi

# 1. register
step "1) /auth/register"
TOKEN=$(curl -s -X POST "${BASE_URL}/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"${EMAIL}\",\"password\":\"${PASSWORD}\"}" \
  | python3 -c "import sys,json;print(json.load(sys.stdin).get('access_token',''))")
[[ -n "${TOKEN}" ]] && ok "拿到 token" || fail "register 失败" 1
AUTH=(-H "Authorization: Bearer ${TOKEN}")

# 2. 录音 + STT
step "2) /stt/transcribe"
say -o /tmp/w4_smoke.aiff "今天介绍一下 Step 2 模型在长文本上的表现"
afconvert -f WAVE -d LEI16@16000 -c 1 /tmp/w4_smoke.aiff /tmp/w4_smoke.wav > /dev/null
TEXT=$(curl -s -X POST "${BASE_URL}/stt/transcribe" "${AUTH[@]}" \
  -F "file=@/tmp/w4_smoke.wav;type=audio/wav" \
  | python3 -c "import sys,json;print(json.load(sys.stdin).get('text',''))")
[[ -n "${TEXT}" ]] && ok "ASR → \"${TEXT}\"" || fail "STT 失败" 2

# 3. 创建会话 + 追加消息
step "3) 创建会话 + 追加消息"
CID=$(curl -s -X POST "${BASE_URL}/conversations" "${AUTH[@]}" \
  -H "Content-Type: application/json" -d '{"title":"W4","mode":"dialogue"}' \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])")
ok "会话 ${CID}"
APPEND_BODY=$(TEXT_VAL="${TEXT}" python3 -c '
import json, os
print(json.dumps({"role": "user", "content": os.environ["TEXT_VAL"]}, ensure_ascii=False))
')
curl -sS -o /dev/null -w "" -X POST "${BASE_URL}/conversations/${CID}/messages" \
  "${AUTH[@]}" -H "Content-Type: application/json" -d "${APPEND_BODY}"
ok "消息追加"

# 4. 列排版模板
step "4) /formatting/templates"
TEMPLATES=$(curl -s "${BASE_URL}/formatting/templates" "${AUTH[@]}" \
  | python3 -c "import sys,json;d=json.load(sys.stdin);print(','.join(t['id'] for t in d['items']))")
[[ -n "${TEMPLATES}" ]] && ok "模板：${TEMPLATES}" || fail "列模板失败" 4

# 5. 同步 LLM 生成（短）
step "5) /generations（同步 step-2-16k）"
GEN_BODY=$(python3 -c "import json,sys;print(json.dumps({'conversation_id':sys.argv[1],'mode':'dialogue','length':'short'}))" "${CID}")
START=$(date +%s)
GEN=$(curl -s -X POST "${BASE_URL}/generations" "${AUTH[@]}" \
  -H "Content-Type: application/json" -d "${GEN_BODY}")
ELAPSED=$(( $(date +%s) - START ))
TITLE=$(echo "${GEN}" | python3 -c "import sys,json;print(json.load(sys.stdin).get('title') or '')")
WC=$(echo "${GEN}" | python3 -c "import sys,json;print(json.load(sys.stdin).get('word_count',0))")
CONTENT=$(echo "${GEN}" | python3 -c "import sys,json;print(json.load(sys.stdin).get('generated_content') or '')")
[[ -n "${CONTENT}" ]] && ok "生成 ${WC} 字（${ELAPSED}s）：${TITLE}" || fail "生成失败 ${GEN}" 5

# 6. 排版（minimal）
step "6) /formatting/apply minimal"
FMT_BODY=$(TITLE="${TITLE}" CONTENT="${CONTENT}" python3 -c '
import json, os
print(json.dumps({
    "template_id": "minimal",
    "title": os.environ["TITLE"],
    "content": os.environ["CONTENT"],
}, ensure_ascii=False))
')
HTML=$(curl -s -X POST "${BASE_URL}/formatting/apply" "${AUTH[@]}" \
  -H "Content-Type: application/json" -d "${FMT_BODY}" \
  | python3 -c "import sys,json;print(json.load(sys.stdin).get('html',''))")
echo "${HTML}" | grep -q '<section style=' && ok "排版返回 inline HTML（${#HTML} 字符）" || fail "排版失败" 6

# 7. full_page 下载
step "7) full_page=true"
FMT_FULL=$(TITLE="${TITLE}" CONTENT="${CONTENT}" python3 -c '
import json, os
print(json.dumps({
    "template_id": "tech",
    "title": os.environ["TITLE"],
    "content": os.environ["CONTENT"],
    "full_page": True,
}, ensure_ascii=False))
')
HTML2=$(curl -s -X POST "${BASE_URL}/formatting/apply" "${AUTH[@]}" \
  -H "Content-Type: application/json" -d "${FMT_FULL}" \
  | python3 -c "import sys,json;print(json.load(sys.stdin).get('html',''))")
echo "${HTML2}" | grep -q '<!doctype html>' && ok "完整 HTML 文档（${#HTML2} 字符）" || fail "full_page 失败" 7

# 8. 未知模板 404
step "8) 未知模板 → 404"
CODE=$(curl -s -o /dev/null -w '%{http_code}' \
  -X POST "${BASE_URL}/formatting/apply" "${AUTH[@]}" \
  -H "Content-Type: application/json" \
  -d '{"template_id":"unknown","content":"x"}')
[[ "${CODE}" == "404" ]] && ok "未知模板 → 404" || fail "未知模板 ${CODE}" 8

printf "\n${GREEN}全部 8 步通过 ✓${RESET}\n"
