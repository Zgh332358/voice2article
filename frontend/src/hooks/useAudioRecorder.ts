import { useCallback, useEffect, useRef, useState } from "react";

export type RecorderStatus = "idle" | "requesting" | "recording" | "stopping" | "stopped" | "error";

export interface UseAudioRecorderResult {
  status: RecorderStatus;
  duration: number; // 秒
  blob: Blob | null;
  mimeType: string | null;
  error: string | null;
  start: () => Promise<void>;
  stop: () => Promise<Blob | null>;
  reset: () => void;
}

/** 浏览器优先级：Chrome/Firefox 优 webm-opus；Safari 退到 mp4 */
const PREFERRED_MIME_TYPES = [
  "audio/webm;codecs=opus",
  "audio/webm",
  "audio/mp4",
  "audio/mpeg",
];

function pickMimeType(): string | null {
  if (typeof MediaRecorder === "undefined") return null;
  for (const mime of PREFERRED_MIME_TYPES) {
    if (MediaRecorder.isTypeSupported(mime)) return mime;
  }
  return null;
}

function extensionFor(mime: string): string {
  if (mime.startsWith("audio/webm")) return "webm";
  if (mime.startsWith("audio/mp4")) return "mp4";
  if (mime.startsWith("audio/mpeg")) return "mp3";
  if (mime.startsWith("audio/wav")) return "wav";
  return "audio";
}

/**
 * 麦克风录音 hook。返回 status / duration / blob 三态以及 start/stop/reset 控制函数。
 *
 * 使用：
 *   const { status, duration, blob, start, stop, reset } = useAudioRecorder();
 *   await start();    // 申请权限并开始录
 *   const audio = await stop();  // 停止并拿到 Blob
 */
export function useAudioRecorder(): UseAudioRecorderResult {
  const [status, setStatus] = useState<RecorderStatus>("idle");
  const [duration, setDuration] = useState(0);
  const [blob, setBlob] = useState<Blob | null>(null);
  const [mimeType, setMimeType] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<number | null>(null);
  const startedAtRef = useRef<number>(0);

  const cleanup = useCallback(() => {
    if (timerRef.current !== null) {
      window.clearInterval(timerRef.current);
      timerRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    mediaRecorderRef.current = null;
  }, []);

  useEffect(() => () => cleanup(), [cleanup]);

  const start = useCallback(async () => {
    if (status === "recording" || status === "requesting") return;
    setError(null);
    setBlob(null);
    setDuration(0);
    chunksRef.current = [];

    if (!navigator.mediaDevices?.getUserMedia) {
      setStatus("error");
      setError("当前浏览器不支持麦克风录音");
      return;
    }

    setStatus("requesting");
    let stream: MediaStream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (e) {
      setStatus("error");
      const message = e instanceof Error ? e.message : "无法访问麦克风";
      setError(`麦克风权限被拒绝：${message}`);
      return;
    }

    const mime = pickMimeType();
    if (!mime) {
      stream.getTracks().forEach((t) => t.stop());
      setStatus("error");
      setError("当前浏览器不支持任何受支持的录音编码");
      return;
    }

    streamRef.current = stream;
    setMimeType(mime);

    const recorder = new MediaRecorder(stream, { mimeType: mime });
    mediaRecorderRef.current = recorder;

    recorder.ondataavailable = (e) => {
      if (e.data.size > 0) chunksRef.current.push(e.data);
    };

    recorder.start();
    startedAtRef.current = Date.now();
    setStatus("recording");

    timerRef.current = window.setInterval(() => {
      setDuration(Math.floor((Date.now() - startedAtRef.current) / 1000));
    }, 250);
  }, [status]);

  const stop = useCallback((): Promise<Blob | null> => {
    return new Promise((resolve) => {
      const recorder = mediaRecorderRef.current;
      if (!recorder || recorder.state === "inactive") {
        resolve(null);
        return;
      }

      setStatus("stopping");
      recorder.onstop = () => {
        const finalMime = recorder.mimeType || mimeType || "audio/webm";
        const finalBlob = new Blob(chunksRef.current, { type: finalMime });
        setBlob(finalBlob);
        setStatus("stopped");
        cleanup();
        resolve(finalBlob);
      };
      recorder.stop();
    });
  }, [mimeType, cleanup]);

  const reset = useCallback(() => {
    cleanup();
    setStatus("idle");
    setDuration(0);
    setBlob(null);
    setMimeType(null);
    setError(null);
  }, [cleanup]);

  return { status, duration, blob, mimeType, error, start, stop, reset };
}

export function buildRecordingFilename(mime: string | null): string {
  const ext = extensionFor(mime || "audio/webm");
  const ts = new Date().toISOString().replace(/[:.]/g, "-");
  return `recording-${ts}.${ext}`;
}
