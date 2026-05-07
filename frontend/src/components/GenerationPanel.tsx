import { useRef, useState } from "react";
import { ThunderboltOutlined } from "@ant-design/icons";
import { Alert, Button, Card, Input, Select, Space, Tag, Typography } from "antd";

import { notify } from "@/services/notify";
import {
  type Generation,
  type Length,
  type Tone,
  createGenerationStream,
} from "@/services/generations";

const { Title, Paragraph, Text } = Typography;
const { TextArea } = Input;

interface GenerationPanelProps {
  conversationId: string | null;
  /** 父组件可以用来刷新历史列表 */
  onCompleted?: (event: { generation_id: string; title: string | null; word_count: number }) => void;
}

const TONES: Tone[] = ["亲切", "正式", "幽默", "理性"];
const LENGTHS: { value: Length; label: string }[] = [
  { value: "short", label: "短（≈800 字）" },
  { value: "medium", label: "中（≈1700 字）" },
  { value: "long", label: "长（≈3000 字）" },
];

function GenerationPanel({ conversationId, onCompleted }: GenerationPanelProps) {
  const [tone, setTone] = useState<Tone>("亲切");
  const [length, setLength] = useState<Length>("medium");
  const [extra, setExtra] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [streamed, setStreamed] = useState("");
  const [meta, setMeta] = useState<Pick<Generation, "id" | "title" | "word_count"> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const disabled = !conversationId || streaming;

  const handleGenerate = async () => {
    if (!conversationId) return;
    setError(null);
    setStreamed("");
    setMeta(null);
    setStreaming(true);

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      await createGenerationStream(
        {
          conversation_id: conversationId,
          mode: "dialogue",
          tone,
          length,
          extra_instructions: extra.trim() || undefined,
        },
        (event) => {
          if (event.type === "delta") {
            setStreamed((prev) => prev + event.content);
          } else if (event.type === "done") {
            setMeta({
              id: event.generation_id,
              title: event.title,
              word_count: event.word_count,
            });
            notify.success(`生成完成：${event.word_count} 字`);
            onCompleted?.({
              generation_id: event.generation_id,
              title: event.title,
              word_count: event.word_count,
            });
          } else if (event.type === "error") {
            setError(event.detail);
          }
        },
        controller.signal
      );
    } catch (e) {
      if ((e as DOMException)?.name === "AbortError") return;
      setError(e instanceof Error ? e.message : "生成失败");
    } finally {
      setStreaming(false);
      abortRef.current = null;
    }
  };

  const handleStop = () => {
    abortRef.current?.abort();
    setStreaming(false);
  };

  return (
    <Card
      title={
        <Space>
          <ThunderboltOutlined style={{ color: "#faad14" }} />
          <span>生成文章</span>
          {meta?.word_count != null && <Tag color="green">{meta.word_count} 字</Tag>}
        </Space>
      }
    >
      <Space direction="vertical" size="middle" style={{ width: "100%" }}>
        <Space wrap>
          <Space>
            <Text>风格</Text>
            <Select<Tone>
              value={tone}
              onChange={setTone}
              disabled={streaming}
              style={{ width: 100 }}
              options={TONES.map((t) => ({ value: t, label: t }))}
            />
          </Space>
          <Space>
            <Text>篇幅</Text>
            <Select<Length>
              value={length}
              onChange={setLength}
              disabled={streaming}
              style={{ width: 160 }}
              options={LENGTHS}
            />
          </Space>
        </Space>

        <TextArea
          value={extra}
          onChange={(e) => setExtra(e.target.value)}
          disabled={streaming}
          placeholder="额外要求（可选），如：避免使用专业术语、加入个人故事…"
          rows={2}
          maxLength={500}
          showCount
        />

        <Space>
          {!streaming ? (
            <Button
              type="primary"
              icon={<ThunderboltOutlined />}
              onClick={handleGenerate}
              disabled={disabled}
            >
              生成草稿
            </Button>
          ) : (
            <Button danger onClick={handleStop}>
              停止
            </Button>
          )}
          {!conversationId && (
            <Text type="secondary" style={{ fontSize: 12 }}>
              请先选择或新建一个会话
            </Text>
          )}
        </Space>

        {error && <Alert type="error" message={error} showIcon closable />}

        {(streaming || streamed) && (
          <Card
            type="inner"
            title={
              <Space>
                <span>生成结果</span>
                {streaming && <Tag color="processing">流式生成中…</Tag>}
                {meta?.title && <Text strong>{meta.title}</Text>}
              </Space>
            }
            extra={
              streamed && (
                <Button
                  size="small"
                  onClick={() => navigator.clipboard.writeText(streamed)}
                >
                  复制
                </Button>
              )
            }
          >
            {streamed ? (
              <Paragraph style={{ whiteSpace: "pre-wrap", marginBottom: 0 }}>
                {streamed}
                {streaming && <span style={{ color: "#faad14" }}>▍</span>}
              </Paragraph>
            ) : (
              <Title level={5} type="secondary">
                正在调 step-2-16k…
              </Title>
            )}
          </Card>
        )}
      </Space>
    </Card>
  );
}

export default GenerationPanel;
