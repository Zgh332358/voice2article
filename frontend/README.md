# Frontend — voice-frontend

Vite 5 + React 18 + TypeScript + Ant Design，包管理用 [pnpm](https://pnpm.io)。

## 启动

```bash
pnpm install
cp .env.example .env
pnpm dev                # 默认 http://localhost:5173
```

开发模式下 `/api/*` 通过 vite 代理转发到 `http://localhost:8000`，所以后端要先启起来。

## 命令

```bash
pnpm dev          # 开发服务（HMR）
pnpm build        # 类型检查 + 生产构建
pnpm preview      # 预览构建产物
pnpm type-check   # 仅类型检查
```

## 目录约定

```
src/
├── main.tsx           # 入口，挂载 React + Router + AntD ConfigProvider
├── App.tsx            # 主路由 + 全局布局
├── pages/             # 路由级页面，PascalCase.tsx
├── components/        # 可复用组件，PascalCase.tsx
├── hooks/             # 自定义 hooks，camelCase.ts，use* 命名
├── services/          # API 客户端、第三方 SDK 封装
├── store/             # Zustand 全局状态
└── styles/            # 全局样式
```

路径别名：`@/*` 指向 `src/*`。

## 代码约定

- 函数组件 + Hooks，禁止 class 组件
- TS strict 模式开
- 错误信封：后端返回 `{detail, code?}`，axios 拦截器统一抛成 `Error`
