import axios, { type AxiosInstance } from "axios";

const baseURL = import.meta.env.VITE_API_BASE_URL || "/api/v1";

export const api: AxiosInstance = axios.create({
  baseURL,
  timeout: 30000,
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const detail = error?.response?.data?.detail || error.message || "请求失败";
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
