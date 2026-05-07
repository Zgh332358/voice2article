import { api } from "@/services/api";

export type ConversationMode = "dialogue" | "document" | "hybrid";
export type MessageRole = "user" | "assistant" | "system";

export interface Conversation {
  id: string;
  title: string | null;
  mode: ConversationMode;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: MessageRole;
  content: string;
  audio_url: string | null;
  referenced_doc_ids: string[] | null;
  created_at: string;
}

export interface ConversationDetail extends Conversation {
  messages: Message[];
}

export interface ConversationList {
  items: Conversation[];
  total: number;
}

export async function listConversations(): Promise<ConversationList> {
  const { data } = await api.get<ConversationList>("/conversations");
  return data;
}

export async function getConversation(id: string): Promise<ConversationDetail> {
  const { data } = await api.get<ConversationDetail>(`/conversations/${id}`);
  return data;
}

export async function createConversation(
  payload: { title?: string | null; mode?: ConversationMode } = {}
): Promise<Conversation> {
  const { data } = await api.post<Conversation>("/conversations", {
    title: payload.title ?? null,
    mode: payload.mode ?? "dialogue",
  });
  return data;
}

export async function updateConversation(
  id: string,
  payload: { title?: string | null }
): Promise<Conversation> {
  const { data } = await api.patch<Conversation>(`/conversations/${id}`, payload);
  return data;
}

export async function deleteConversation(id: string): Promise<void> {
  await api.delete(`/conversations/${id}`);
}

export async function appendMessage(
  conversationId: string,
  payload: { role?: MessageRole; content: string; audio_url?: string | null }
): Promise<Message> {
  const { data } = await api.post<Message>(`/conversations/${conversationId}/messages`, {
    role: payload.role ?? "user",
    content: payload.content,
    audio_url: payload.audio_url ?? null,
  });
  return data;
}
