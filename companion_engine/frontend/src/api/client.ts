import type { EngineInput, EngineOutput, PersonaSnapshot, UserState } from "../types";

const API_BASE_URL = "";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  // 统一处理 fetch 错误；开发环境下请求会先到 Vite，再代理到 FastAPI。
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers ?? {}),
    },
    ...options,
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `请求失败：${response.status}`);
  }

  return response.json() as Promise<T>;
}

export async function getHealth(): Promise<{ status: string }> {
  return request<{ status: string }>("/health");
}

export async function sendChat(input: EngineInput, useLocalModel: boolean): Promise<EngineOutput> {
  const query = useLocalModel ? "?use_local_model=true" : "?use_local_model=false";
  return request<EngineOutput>(`/api/chat${query}`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export async function getUserState(userId: string): Promise<UserState> {
  return request<UserState>(`/api/state/${encodeURIComponent(userId)}`);
}

export async function savePersona(userId: string, persona: PersonaSnapshot): Promise<{ status: string }> {
  return request<{ status: string }>(`/api/persona/${encodeURIComponent(userId)}`, {
    method: "POST",
    body: JSON.stringify(persona),
  });
}

export async function resetUser(userId: string): Promise<{ status: string }> {
  return request<{ status: string }>(`/api/reset/${encodeURIComponent(userId)}`, {
    method: "POST",
  });
}
