import { useState } from "react";
import { Card, Empty, Input, Space, Tabs, Tag, Typography } from "antd";

import AudioFileUploader from "@/components/AudioFileUploader";
import AudioRecorder from "@/components/AudioRecorder";
import { notify } from "@/services/notify";

const { Title, Paragraph, Text } = Typography;
const { TextArea } = Input;

type TranscriptSource =
  | { kind: "recording"; duration: number }
  | { kind: "upload"; filename: string; size: number };

function describeSource(source: TranscriptSource): string {
  if (source.kind === "recording") {
    const m = Math.floor(source.duration / 60);
    const s = source.duration % 60;
    return `录音 ${m}:${s.toString().padStart(2, "0")}`;
  }
  return `上传 ${source.filename} · ${(source.size / 1024).toFixed(1)} KB`;
}

function Conversations() {
  const [transcript, setTranscript] = useState<string>("");
  const [source, setSource] = useState<TranscriptSource | null>(null);

  const handleTranscribed = (text: string, src: TranscriptSource) => {
    setTranscript((prev) => (prev ? `${prev}\n\n${text}` : text));
    setSource(src);
    notify.success(`转写完成：${text.length} 字`);
  };

  return (
    <Space direction="vertical" size="large" style={{ width: "100%" }}>
      <div>
        <Title level={2} style={{ marginBottom: 4 }}>
          对话创作
        </Title>
        <Paragraph type="secondary" style={{ marginBottom: 0 }}>
          通过录音或上传音频，把你的想法转成文字。W3 起这段文字会送到 LLM 生成文章草稿。
        </Paragraph>
      </div>

      <Card title="语音输入">
        <Tabs
          items={[
            {
              key: "record",
              label: "实时录音",
              children: <AudioRecorder onTranscribed={handleTranscribed} />,
            },
            {
              key: "upload",
              label: "上传文件",
              children: <AudioFileUploader onTranscribed={handleTranscribed} />,
            },
          ]}
        />
      </Card>

      <Card
        title={
          <Space>
            <span>转写文本</span>
            {source && <Tag color="blue">{describeSource(source)}</Tag>}
          </Space>
        }
        extra={
          transcript && (
            <Text type="secondary" style={{ fontSize: 12 }}>
              {transcript.length} 字符
            </Text>
          )
        }
      >
        {transcript ? (
          <TextArea
            value={transcript}
            onChange={(e) => setTranscript(e.target.value)}
            autoSize={{ minRows: 6, maxRows: 20 }}
            placeholder="转写内容会出现在这里，可以手动修正"
          />
        ) : (
          <Empty description="还没有转写内容。先在上面录音或上传一段音频。" />
        )}
      </Card>
    </Space>
  );
}

export default Conversations;
