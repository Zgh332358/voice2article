# voice2article

> 说一段话 → 一篇可直接发布的微信公众号文章。
> 阶跃 Step-Audio + Step-2 标杆 demo（4 周 MVP，已完成）。

## TL;DR — 5 分钟跑起来

```bash
git clone git@github.com:Zgh332358/voice2article.git
cd voice2article

# 1) 装依赖
cd backend && uv sync && cd ..
cd frontend && pnpm install && cd ..

# 2) 配 Step API key
cp backend/.env.example backend/.env
# 编辑 backend/.env，填 STEP_API_KEY=sk-... （从 platform.stepfun.com 拿）

# 3) 一键启 demo（自动建 demo 账号 + 3 条示例会话）
bash scripts/demo-up.sh

# 4) 浏览器打开 http://localhost:5173
#    账号 demo@aiken.dev / 密码 demo-password-1
```

5 分钟不到，麦克风对着说一段话，30 秒后能拿到一篇带标题的中文文章 + 排版好的 HTML，可以直接 Cmd+V 粘进微信公众号编辑器。

完整演示稿：[`docs/DEMO.md`](docs/DEMO.md)

## 项目状态

**MVP v0.1.0 已完成** · 2026-05-07

| Phase | 内容 | 状态 |
|---|---|---|
| W1 | 脚手架 + DB schema + JWT 认证 + API 框架 | ✅ |
| W2 | Step-Audio 接入 + 录音组件 + 对话存储 | ✅ |
| W3 | Step-2 LLM 封装 + Prompt 模板 + SSE 流式生成 + 历史 | ✅ |
| W4 | 公众号排版模板 + 一键 HTML 导出 + Demo | ✅ |

**端到端链路**：

```
说话 → Step-Audio ASR → 入会话 → Step-2-16k SSE 生成 → 一键排版 → 复制到微信编辑器
```

## 技术栈

| 层 | 选型 | 备注 |
|---|---|---|
| 后端 | FastAPI 0.115 + Python 3.12 + uv | 41 个测试 / ruff / mypy 全绿 |
| 前端 | Vite 5 + React 18 + TypeScript strict + Ant Design 5 | flat ESLint + 路径别名 `@/*` |
| 数据库 | SQLite + Alembic（开发）/ Postgres（生产，URL 切换） | 4 张核心表 + UUID PK |
| 认证 | JWT HS256 + bcrypt cost 12 | 错误信封 `{detail, code}` |
| LLM | Step-2-16k（OpenAI 兼容 SSE 流式） | `trust_env=False` 绕开系统代理 |
| ASR | Step-Audio (`step-asr`，multipart 上传) | 自带中文标点 |
| 排版 | markdown-it-py + 3 套 inline-style 模板 | 直接粘微信编辑器 |

## 目录结构

```
voice2article/
├── backend/                 # FastAPI 服务
│   ├── app/
│   │   ├── api/             # 路由：health/metrics/auth/stt/conversations/generations/formatting
│   │   ├── core/            # logging / errors / security
│   │   ├── models/          # SQLAlchemy ORM
│   │   ├── schemas/         # Pydantic 请求/响应
│   │   └── services/        # llm / stt / prompts / formatting
│   ├── alembic/             # 异步 alembic 迁移
│   └── tests/               # 41 个 e2e + 单元测试
├── frontend/                # Vite + React + TS
│   ├── src/
│   │   ├── pages/           # Login / Register / Home / Conversations / History / NotFound
│   │   ├── components/      # AudioRecorder / FileUploader / GenerationPanel / FormatModal / ProtectedRoute
│   │   ├── hooks/           # useAudioRecorder
│   │   ├── services/        # axios + auth/stt/conversations/generations/formatting/notify
│   │   ├── store/           # Zustand auth store（localStorage 持久化）
│   │   └── layouts/         # MainLayout (Sider+Header+Content) / AuthLayout
│   └── eslint.config.js     # ESLint 9 flat config
├── docs/
│   ├── DEMO.md              # 5 分钟演示稿
│   ├── W2-manual-test.md    # 浏览器手测清单
│   └── voice2article.postman_collection.json
├── scripts/
│   ├── demo-up.sh           # 一键起服务 + seed
│   ├── demo-down.sh         # 一键关服务
│   ├── seed-demo.py         # 创建 demo 账号 + 3 条示例会话
│   ├── eval-prompts.py      # Prompt 评测（手动跑，烧 token）
│   ├── w2-smoke.sh          # W2 端到端 9 步
│   └── w4-smoke.sh          # W4 端到端 8 步
└── README.md                # 本文档
```

## 本地启动（详细版）

### 前置要求

- macOS / Linux（Windows 没测）
- Python 3.12+ 和 [uv](https://github.com/astral-sh/uv) 0.11+
- Node 22+ 和 pnpm 10+
- Step API key（[platform.stepfun.com](https://platform.stepfun.com)，需开通 LLM + ASR）

### 一键 demo

见上文 TL;DR。`scripts/demo-up.sh` 帮你做完所有事。

### 手动启动（开发用）

**后端**

```bash
cd backend
uv sync                                  # 装依赖（~30s 第一次）
cp .env.example .env                     # 配 STEP_API_KEY
uv run alembic upgrade head              # 建表
uv run uvicorn app.main:app --reload     # http://localhost:8000
```

健康检查：

```bash
curl http://localhost:8000/api/v1/health
# {"status":"ok","name":"voice-backend","version":"0.1.0","env":"development"}
```

Swagger UI：`http://localhost:8000/docs`

**前端**

```bash
cd frontend
pnpm install
cp .env.example .env
pnpm dev                                 # http://localhost:5173
```

vite 已配代理，前端 `/api/*` 自动转后端 `8000`。

## 测试

```bash
# 后端
cd backend
uv run ruff check .
uv run mypy app
uv run pytest                            # 41 个用例

# 前端
cd frontend
pnpm type-check
pnpm lint
pnpm build

# 端到端（要求 .env 里有可用的 STEP_API_KEY）
bash scripts/w2-smoke.sh                 # 录音→ASR→会话→消息（9 步）
bash scripts/w4-smoke.sh                 # 上述 + LLM→排版（8 步）
```

## 端口冲突？

如果 8000 / 5173 被别的项目占着：

```bash
BACKEND_PORT=8003 FRONTEND_PORT=5174 bash scripts/demo-up.sh
```

W2/W4 smoke 同样支持 `PORT=xxxx bash scripts/w2-smoke.sh`。

## 代码约定

- **Python**：PEP 8 + 类型注解全程；async/await；模块 `snake_case`，类 `PascalCase`
- **TypeScript**：strict 模式；React 函数组件 + Hooks；组件 `PascalCase.tsx`
- **API**：REST + JSON；URL `/api/v1/...`；字段 `snake_case`；错误统一 `{detail: string, code?: string}`
- **Commit**：Conventional Commits（`feat:` / `fix:` / `chore:` / `docs:` / `test:`）
- **安全**：`.env` 永不入库；STEP_API_KEY 不要贴在 issue / 聊天里

## V2 路线（不在 MVP 范围）

- **文档库**（PRD §4.3）：上传历史文章 → 向量检索 → 风格学习
- **混合生成**（PRD §4.4.2 模式 C）：对话 + 引用文档融合
- **多模态**：Step-1V 看图说话，自动配图
- **多平台分发**：小红书 / 知乎 / 头条
- **声音克隆**：Step-TTS 用作者声音播报

## License

MIT，见仓库根。
