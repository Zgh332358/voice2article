import { api } from "@/services/api";

export interface TranscribeResponse {
  text: string;
  model: string;
  audio_bytes: number;
}

/**
 * 上传一段音频到后端 /stt/transcribe，返回转写文本。
 *
 * - blob：来自 MediaRecorder 或 File 输入
 * - filename：服务端用来记录 + 决定后缀，含合理后缀（.webm / .wav 等）
 * - silent：表单内联展示错误时设 true，避免双重 toast
 */
export async function transcribe(
  blob: Blob,
  filename: string,
  options: { silent?: boolean } = {}
): Promise<TranscribeResponse> {
  const form = new FormData();
  form.append("file", blob, filename);
  const { data } = await api.post<TranscribeResponse>("/stt/transcribe", form, {
    silent: options.silent,
    timeout: 60000,
  });
  return data;
}
