import { api } from "@/services/api";
import type { AuthUser } from "@/store/auth";

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: AuthUser;
}

export async function register(payload: {
  email: string;
  password: string;
  nickname?: string;
}): Promise<TokenResponse> {
  const { data } = await api.post<TokenResponse>("/auth/register", payload);
  return data;
}

export async function login(payload: {
  email: string;
  password: string;
}): Promise<TokenResponse> {
  const { data } = await api.post<TokenResponse>("/auth/login", payload);
  return data;
}

export async function fetchMe(): Promise<AuthUser> {
  const { data } = await api.get<AuthUser>("/auth/me");
  return data;
}
