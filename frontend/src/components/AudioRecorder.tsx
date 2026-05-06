import { useState } from "react";
import { AudioOutlined, LoadingOutlined, StopOutlined } from "@ant-design/icons";
import { Alert, Button, Space, Tag, Typography } from "antd";

import { useAudioRecorder, buildRecordingFilename } from "@/hooks/useAudioRecorder";
import { transcribe } from "@/services/stt";

const { Text } = Typography;

interface AudioRecorderProps {
  onTranscribed: (text: string, source: { kind: "recording"; duration: number }) => void;
}

function formatDuration(s: number): string {
  const mm = Math.floor(s / 60).toString().padStart(2, "0");
  const ss = (s % 60).toString().padStart(2, "0");
  return `${mm}:${ss}`;
}

function AudioRecorder({ onTranscribed }: AudioRecorderProps) {
  const recorder = useAudioRecorder();
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const handleStart = async () => {
    setSubmitError(null);
    await recorder.start();
  };

  const handleStop = async () => {
    setSubmitError(null);
    const blob = await recorder.stop();
    if (!blob) return;

    setSubmitting(true);
    try {
      const filename = buildRecordingFilename(recorder.mimeType);
      const result = await transcribe(blob, filename, { silent: true });
      onTranscribed(result.text, { kind: "recording", duration: recorder.duration });
      recorder.reset();
    } catch (e) {
      setSubmitError(e instanceof Error ? e.message : "转写失败");
    } finally {
      setSubmitting(false);
    }
  };

  const isRecording = recorder.status === "recording";
  const isBusy = recorder.status === "requesting" || recorder.status === "stopping" || submitting;

  return (
    <Space direction="vertical" size="middle" style={{ width: "100%" }}>
      <Space align="center" size="middle">
        {!isRecording ? (
          <Button
            type="primary"
            size="large"
            icon={<AudioOutlined />}
            onClick={handleStart}
            loading={recorder.status === "requesting"}
            disabled={submitting}
          >
            开始录音
          </Button>
        ) : (
          <Button
            danger
            size="large"
            icon={<StopOutlined />}
            onClick={handleStop}
            loading={recorder.status === "stopping"}
          >
            停止并转写
          </Button>
        )}

        <Tag color={isRecording ? "red" : "default"} icon={isRecording ? <LoadingOutlined /> : null}>
          {formatDuration(recorder.duration)}
        </Tag>

        {recorder.mimeType && (
          <Text type="secondary" style={{ fontSize: 12 }}>
            编码：{recorder.mimeType}
          </Text>
        )}
      </Space>

      {submitting && <Text type="secondary">正在调用 Step ASR 转写…</Text>}

      {recorder.error && <Alert type="error" message={recorder.error} showIcon />}
      {submitError && <Alert type="error" message={submitError} showIcon closable />}

      {!isRecording && !isBusy && recorder.status === "idle" && (
        <Text type="secondary" style={{ fontSize: 12 }}>
          首次使用浏览器会请求麦克风权限。Safari 用户请在系统设置开启麦克风访问。
        </Text>
      )}
    </Space>
  );
}

export default AudioRecorder;
