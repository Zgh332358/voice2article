import axios, { AxiosError, type AxiosInstance, type InternalAxiosRequestConfig } from "axios";

import { notify } from "@/services/notify";
import { useAuthStore } from "@/store/auth";

declare module "axios" {
  export interface AxiosRequestConfig {
    /** true 时不弹全局错误 toast，调用方自行处理（如表单内联提示）。 */
    silent?: boolean;
  }
}

const baseURL = import.meta.env.VITE_API_BASE_URL || "/api/v1";

export const api: AxiosInstance = axios.create({
  baseURL,
  timeout: 30000,
});

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = useAuthStore.getState().token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ detail?: string; code?: string }>) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().clear();
    }

    const detail = error.response?.data?.detail || error.message || "请求失败";
    const silent = (error.config as InternalAxiosRequestConfig & { silent?: boolean })?.silent;
    if (!silent) {
      notify.error(detail);
    }
    return Promise.reject(new Error(detail));
  }
);

export interface HealthResponse {
  status: string;
  name: string;
  version: string;
  env: string;
}

export async function fetchHealth(): Promise<HealthResponse> {
  const { data } = await api.get<HealthResponse>("/health");
  return data;
}
