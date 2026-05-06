import axios, { AxiosError, type AxiosInstance } from "axios";

import { useAuthStore } from "@/store/auth";

const baseURL = import.meta.env.VITE_API_BASE_URL || "/api/v1";

export const api: AxiosInstance = axios.create({
  baseURL,
  timeout: 30000,
});

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ detail?: string; code?: string }>) => {
    // 401 自动清登录态
    if (error.response?.status === 401) {
      useAuthStore.getState().clear();
    }
    const detail = error.response?.data?.detail || error.message || "请求失败";
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
