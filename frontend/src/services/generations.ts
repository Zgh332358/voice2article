import { api } from "@/services/api";
import { useAuthStore } from "@/store/auth";

export type GenerationMode = "dialogue" | "document" | "hybrid";
export type GenerationStatus = "draft" | "published" | "deleted";
export type Tone = "亲切" | "正式" | "幽默" | "理性";
export type Length = "short" | "medium" | "long";

export interface Generation {
  id: string;
  conversation_id: string | null;
  source_mode: GenerationMode;
  title: string | null;
  generated_content: string | null;
  word_count: number | null;
  status: GenerationStatus;
  created_at: string;
}

export interface GenerationList {
  items: Generation[];
  total: number;
}

export interface CreateGenerationPayload {
  conversation_id: string;
  mode?: GenerationMode;
  tone?: Tone;
  length?: Length;
  extra_instructions?: string | null;
}

export async function listGenerations(
  conversationId?: string
): Promise<GenerationList> {
  const { data } = await api.get<GenerationList>("/generations", {
    params: conversationId ? { conversation_id: conversationId } : undefined,
  });
  return data;
}

export async function getGeneration(id: string): Promise<Generation> {
  const { data } = await api.get<Generation>(`/generations/${id}`);
  return data;
}

export async function createGenerationSync(
  payload: CreateGenerationPayload
): Promise<Generation> {
  const { data } = await api.post<Generation>("/generations", payload, {
    timeout: 120000,
  });
  return data;
}

export type StreamEvent =
  | { type: "delta"; content: string }
  | { type: "done"; generation_id: string; title: string | null; word_count: number }
  | { type: "error"; code: string; detail: string };

/**
 * 流式生成。每收到一个 SSE 事件就调用 onEvent。
 *
 * 用 fetch + ReadableStream 而不是 axios，因为浏览器 axios 不支持原生 SSE 流读取。
 */
export async function createGenerationStream(
  payload: CreateGenerationPayload,
  onEvent: (event: StreamEvent) => void,
  signal?: AbortSignal
): Promise<void> {
  const baseURL = import.meta.env.VITE_API_BASE_URL || "/api/v1";
  const token = useAuthStore.getState().token;
  const resp = await fetch(`${baseURL}/generations/stream`, {
    method: "POST",
    signal,
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(payload),
  });

  if (!resp.ok || !resp.body) {
    let detail = "生成失败";
    try {
      const body = await resp.json();
      detail = body.detail || detail;
    } catch {
      /* keep default */
    }
    if (resp.status === 401) {
      useAuthStore.getState().clear();
    }
    throw new Error(detail);
  }

  const reader = resp.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    // SSE 以空行分事件，每个事件可能多个 "data:" 行（这里我们一行一个 data）
    let nlIdx;
    while ((nlIdx = buffer.indexOf("\n\n")) !== -1) {
      const rawEvent = buffer.slice(0, nlIdx).trim();
      buffer = buffer.slice(nlIdx + 2);
      if (!rawEvent.startsWith("data:")) continue;
      const json = rawEvent.slice("data:".length).trim();
      try {
        onEvent(JSON.parse(json) as StreamEvent);
      } catch {
        /* 跳过无法解析的 chunk */
      }
    }
  }
}
