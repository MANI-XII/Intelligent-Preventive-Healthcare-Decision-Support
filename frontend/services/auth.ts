import axios from "axios";

const baseURL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
const TOKEN_STORAGE_KEY = "health.auth.token";

type AuthResponse = {
  access_token: string;
  token_type: string;
  user_id: string;
};

type MeResponse = {
  user_id: string;
};

const authApi = axios.create({
  baseURL,
  timeout: 120000,
});

export function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_STORAGE_KEY);
}

export function setStoredToken(token: string): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(TOKEN_STORAGE_KEY, token);
}

export function clearStoredToken(): void {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(TOKEN_STORAGE_KEY);
}

export async function signup(user_id: string, password: string): Promise<AuthResponse> {
  const res = await authApi.post<AuthResponse>("/auth/signup", { user_id, password });
  return res.data;
}

export async function login(user_id: string, password: string): Promise<AuthResponse> {
  const res = await authApi.post<AuthResponse>("/auth/login", { user_id, password });
  return res.data;
}

export async function me(token: string): Promise<MeResponse> {
  const res = await authApi.get<MeResponse>("/auth/me", {
    headers: { Authorization: `Bearer ${token}` },
  });
  return res.data;
}
