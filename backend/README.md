# Backend — voice-backend

FastAPI + Python 3.12，依赖管理用 [uv](https://github.com/astral-sh/uv)。

## 启动

```bash
uv sync                                  # 创建 .venv 并安装依赖
cp .env.example .env                     # 配置环境变量
uv run uvicorn app.main:app --reload     # 默认 http://localhost:8000
```

- 健康检查：`GET /api/v1/health`
- API 文档（dev 模式）：`http://localhost:8000/docs`

## 测试与代码风格

```bash
uv run pytest                  # 跑测试
uv run ruff check .            # lint
uv run ruff format .           # format
uv run mypy app                # 类型检查
```

## 目录约定

```
app/
├── main.py        # FastAPI 入口、CORS、生命周期
├── config.py      # Pydantic Settings，环境变量收口
├── api/           # 路由层；每个领域一个模块
├── core/          # 横切关注点：日志、错误、安全
├── models/        # SQLAlchemy ORM（W1 Day 3-4 引入）
├── schemas/       # Pydantic 请求/响应模型
└── services/      # 业务逻辑、外部 API 封装（Step LLM/STT）
```

## 错误响应约定

所有非 2xx 响应统一信封：

```json
{ "detail": "人类可读的错误描述", "code": "machine_error_code" }
```

校验错误（422）会附加 `errors` 字段（来自 Pydantic）。
