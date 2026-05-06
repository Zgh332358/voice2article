import { useState } from "react";
import { InboxOutlined } from "@ant-design/icons";
import { Alert, Space, Typography, Upload } from "antd";
import type { UploadProps } from "antd";
import type { RcFile } from "antd/es/upload";

import { transcribe } from "@/services/stt";

const { Text } = Typography;
const { Dragger } = Upload;

interface AudioFileUploaderProps {
  onTranscribed: (text: string, source: { kind: "upload"; filename: string; size: number }) => void;
}

const ACCEPTED = ".wav,.mp3,.m4a,.mp4,.aiff,.aif,.ogg,.webm,.flac";
const MAX_BYTES = 25 * 1024 * 1024;

function AudioFileUploader({ onTranscribed }: AudioFileUploaderProps) {
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleBeforeUpload = async (file: RcFile): Promise<boolean> => {
    setError(null);

    if (file.size > MAX_BYTES) {
      setError(`文件超过 ${MAX_BYTES / 1024 / 1024}MB 限制`);
      return false;
    }

    setSubmitting(true);
    try {
      const result = await transcribe(file, file.name, { silent: true });
      onTranscribed(result.text, { kind: "upload", filename: file.name, size: file.size });
    } catch (e) {
      setError(e instanceof Error ? e.message : "转写失败");
    } finally {
      setSubmitting(false);
    }

    // 始终返回 false 阻断 antd 默认上传 —— 转写在 beforeUpload 里已经完成
    return false;
  };

  const draggerProps: UploadProps = {
    name: "file",
    accept: ACCEPTED,
    multiple: false,
    showUploadList: false,
    disabled: submitting,
    beforeUpload: handleBeforeUpload,
  };

  return (
    <Space direction="vertical" size="middle" style={{ width: "100%" }}>
      <Dragger {...draggerProps}>
        <p className="ant-upload-drag-icon">
          <InboxOutlined />
        </p>
        <p className="ant-upload-text">{submitting ? "正在转写…" : "点击或拖拽音频到此处"}</p>
        <p className="ant-upload-hint" style={{ fontSize: 12 }}>
          支持 wav / mp3 / m4a / mp4 / aiff / ogg / webm / flac，单个文件 ≤ 25MB
        </p>
      </Dragger>

      {error && <Alert type="error" message={error} showIcon closable />}

      {!submitting && !error && (
        <Text type="secondary" style={{ fontSize: 12 }}>
          上传后立刻调 /stt/transcribe，不会存到服务器（W2 Day 12-13 才接对话存储）。
        </Text>
      )}
    </Space>
  );
}

export default AudioFileUploader;
