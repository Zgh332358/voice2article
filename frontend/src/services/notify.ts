/**
 * 全局通知通道。
 *
 * AntD v5 的 message 静态调用脱离 ConfigProvider 上下文（主题不会生效）。
 * 这里通过 main.tsx 在 AntdApp 内拿到 message 实例并注入，
 * 任何模块（包括 axios 拦截器、非组件代码）都能调用 notify.error 等方法。
 */

import type { MessageInstance } from "antd/es/message/interface";

let messageApi: MessageInstance | null = null;

export function setMessageApi(api: MessageInstance): void {
  messageApi = api;
}

export const notify = {
  error(content: string, duration = 4): void {
    messageApi?.error(content, duration);
  },
  success(content: string, duration = 2): void {
    messageApi?.success(content, duration);
  },
  info(content: string, duration = 2): void {
    messageApi?.info(content, duration);
  },
  warning(content: string, duration = 3): void {
    messageApi?.warning(content, duration);
  },
};
