# 语音对话公众号生成器

> 说一段话 → 4 周后产出可直接发布的公众号文章。
>
> Phase 1 MVP：纯对话 → 文章 → 一键排版。

## 项目状态

- **Phase**: W1 Day 1-2（脚手架就绪）
- **PRD**: `docs/PRD_v1.0.md`（待移入），原文在 `~/Documents/PRD_语音对话公众号生成器.md`
- **Proposal**: `~/Documents/Proposal_语音对话公众号生成器_v0.1.md`

## 技术栈

| 层 | 选型 | 理由 |
|---|---|---|
| 后端 | FastAPI + Python 3.12 + uv | 算法集成顺，uv 装包快 |
| 前端 | Vite + React 18 + TypeScript + Ant Design | 生态成熟 |
| 数据库 | PostgreSQL（W1 Day 3-4 引入） | 关系型 + JSON 字段 |
| 缓存 | Redis（按需引入） | 会话缓存 / 限流 |
| LLM | Step-2（默认）/ Claude 兜底 | 阶跃生态对齐 |
| STT | Step-Audio（默认）/ Whisper 兜底 | 同上 |
| 部署 | 本地 Docker（Demo 期） | 演示成本最低 |

## 目录结构

```
voice/
├── backend/                # FastAPI 服务
│   ├── app/
│   │   ├── main.py         # 入口
│   │   ├── config.py       # 配置（Pydantic Settings）
│   │   ├── api/            # 路由
│   │   ├── core/           # 日志、错误处理、安全
│   │   ├── models/         # SQLAlchemy ORM（W1 Day 3-4）
│   │   ├── schemas/        # Pydantic schema
│   │   └── services/       # 业务/外部服务封装（STT/LLM 等）
│   ├── tests/
│   ├── pyproject.toml
│   └── .env.example
├── frontend/               # Vite + React + TS
│   ├── src/
│   │   ├── pages/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── services/       # API client
│   │   ├── store/          # 全局状态
│   │   └── styles/
│   ├── package.json
│   └── .env.example
├── docs/                   # PRD、技术设计、API 文档
├── scripts/                # 启动 / 部署脚本
├── docker-compose.yml      # 本地开发依赖（Postgres / Redis）
└── README.md
```

## 本地启动

### 前置要求

- Python 3.12+ 和 [uv](https://github.com/astral-sh/uv)
- Node 22+ 和 pnpm 10+
- Docker（用于 Postgres / Redis，W1 Day 3-4 起）

### 后端

```bash
cd backend
uv sync                                  # 安装依赖
cp .env.example .env                     # 复制并填好 .env
uv run uvicorn app.main:app --reload     # 启动开发服务（默认 8000 端口）
```

健康检查：`curl http://localhost:8000/api/health`

### 前端

```bash
cd frontend
pnpm install
cp .env.example .env
pnpm dev                                 # 启动开发服务（默认 5173 端口）
```

打开 `http://localhost:5173`。

## 进度路线图

- **W1（当前）**：脚手架 + DB schema + 用户认证 + API 框架
- **W2**：STT 接入、录音组件、对话存储
- **W3**：LLM 封装、Prompt 工程、生成 API
- **W4**：排版模板、一键排版、HTML 导出、E2E

详见 `~/Documents/Proposal_语音对话公众号生成器_v0.1.md`。

## 代码约定

- **Python**：PEP 8 + 类型注解（强制）；async/await 全程；模块名 snake_case；类名 PascalCase
- **TypeScript**：strict 模式；React 函数组件 + Hooks；组件文件 `PascalCase.tsx`，其他 `kebab-case.ts`
- **API**：REST + JSON；URL 用 `/api/v1/...`；JSON 字段用 `snake_case`；错误响应统一 `{detail: string, code?: string}`
- **Commit**：Conventional Commits（`feat:` / `fix:` / `chore:` / `docs:`）
