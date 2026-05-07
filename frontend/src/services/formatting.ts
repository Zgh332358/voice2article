import { api } from "@/services/api";

export interface Template {
  id: string;
  name: string;
  description: string;
}

export interface FormatResult {
  template_id: string;
  html: string;
  title: string | null;
}

export async function listTemplates(): Promise<Template[]> {
  const { data } = await api.get<{ items: Template[] }>("/formatting/templates");
  return data.items;
}

export async function applyTemplate(payload: {
  template_id: string;
  title?: string | null;
  content: string;
  full_page?: boolean;
}): Promise<FormatResult> {
  const { data } = await api.post<FormatResult>("/formatting/apply", payload);
  return data;
}
