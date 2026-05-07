import { useEffect, useState } from "react";
import { DeleteOutlined, PlusOutlined } from "@ant-design/icons";
import {
  Avatar,
  Button,
  Card,
  Empty,
  List,
  Popconfirm,
  Space,
  Spin,
  Tabs,
  Tag,
  Typography,
} from "antd";

import AudioFileUploader from "@/components/AudioFileUploader";
import AudioRecorder from "@/components/AudioRecorder";
import GenerationPanel from "@/components/GenerationPanel";
import { notify } from "@/services/notify";
import {
  type Conversation,
  type ConversationDetail,
  type Message,
  appendMessage,
  createConversation,
  deleteConversation,
  getConversation,
  listConversations,
} from "@/services/conversations";

const { Title, Paragraph, Text } = Typography;

function formatTitle(c: Conversation): string {
  if (c.title) return c.title;
  return `未命名会话 · ${new Date(c.created_at).toLocaleString()}`;
}

function MessageBubble({ msg }: { msg: Message }) {
  const isUser = msg.role === "user";
  return (
    <div
      style={{
        display: "flex",
        justifyContent: isUser ? "flex-end" : "flex-start",
        marginBottom: 12,
      }}
    >
      {!isUser && (
        <Avatar size="small" style={{ marginRight: 8, background: "#722ed1" }}>
          AI
        </Avatar>
      )}
      <div
        style={{
          maxWidth: "70%",
          padding: "8px 12px",
          borderRadius: 8,
          background: isUser ? "#1677ff" : "#f0f0f0",
          color: isUser ? "#fff" : "#1f1f1f",
          whiteSpace: "pre-wrap",
        }}
      >
        {msg.content}
      </div>
      {isUser && (
        <Avatar size="small" style={{ marginLeft: 8, background: "#1677ff" }}>
          我
        </Avatar>
      )}
    </div>
  );
}

function Conversations() {
  const [list, setList] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [detail, setDetail] = useState<ConversationDetail | null>(null);
  const [loadingList, setLoadingList] = useState(false);
  const [loadingDetail, setLoadingDetail] = useState(false);

  const refreshList = async (selectFirst = false) => {
    setLoadingList(true);
    try {
      const { items } = await listConversations();
      setList(items);
      if (selectFirst && items.length > 0 && activeId === null) {
        setActiveId(items[0].id);
      }
    } finally {
      setLoadingList(false);
    }
  };

  useEffect(() => {
    refreshList(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (activeId === null) {
      setDetail(null);
      return;
    }
    let cancelled = false;
    setLoadingDetail(true);
    getConversation(activeId)
      .then((d) => {
        if (!cancelled) setDetail(d);
      })
      .catch(() => {
        if (!cancelled) setDetail(null);
      })
      .finally(() => {
        if (!cancelled) setLoadingDetail(false);
      });
    return () => {
      cancelled = true;
    };
  }, [activeId]);

  const handleCreate = async () => {
    const conv = await createConversation();
    await refreshList();
    setActiveId(conv.id);
    notify.success("已创建新会话");
  };

  const handleDelete = async (id: string) => {
    await deleteConversation(id);
    notify.success("已删除");
    if (activeId === id) setActiveId(null);
    refreshList();
  };

  const handleTranscribed = async (text: string) => {
    let convId = activeId;
    if (!convId) {
      const conv = await createConversation({ title: text.slice(0, 30) });
      await refreshList();
      convId = conv.id;
      setActiveId(convId);
    }
    await appendMessage(convId, { role: "user", content: text });
    const updated = await getConversation(convId);
    setDetail(updated);
    notify.success(`已记录 ${text.length} 字`);
  };

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Title level={2} style={{ marginBottom: 4 }}>
          对话创作
        </Title>
        <Paragraph type="secondary" style={{ marginBottom: 0 }}>
          录音或上传音频后，转写文字会作为 user 消息存入当前会话。W3 起 AI 会在右侧给出文章草稿。
        </Paragraph>
      </div>

      <div style={{ display: "flex", gap: 16 }}>
        {/* 左：会话列表 */}
        <Card
          title="我的会话"
          style={{ width: 280, flexShrink: 0 }}
          extra={
            <Button type="primary" size="small" icon={<PlusOutlined />} onClick={handleCreate}>
              新建
            </Button>
          }
          styles={{ body: { padding: 0 } }}
        >
          {loadingList ? (
            <div style={{ padding: 24, textAlign: "center" }}>
              <Spin />
            </div>
          ) : list.length === 0 ? (
            <Empty description="还没有会话" style={{ padding: 24 }} />
          ) : (
            <List
              dataSource={list}
              renderItem={(c) => (
                <List.Item
                  style={{
                    padding: "12px 16px",
                    cursor: "pointer",
                    background: c.id === activeId ? "#e6f4ff" : undefined,
                  }}
                  onClick={() => setActiveId(c.id)}
                  actions={[
                    <Popconfirm
                      key="del"
                      title="确认删除该会话？"
                      onConfirm={(e) => {
                        e?.stopPropagation();
                        handleDelete(c.id);
                      }}
                      onCancel={(e) => e?.stopPropagation()}
                    >
                      <Button
                        type="text"
                        size="small"
                        icon={<DeleteOutlined />}
                        onClick={(e) => e.stopPropagation()}
                      />
                    </Popconfirm>,
                  ]}
                >
                  <List.Item.Meta
                    title={
                      <Text ellipsis style={{ maxWidth: 160 }}>
                        {formatTitle(c)}
                      </Text>
                    }
                    description={
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        {new Date(c.updated_at).toLocaleString()}
                      </Text>
                    }
                  />
                </List.Item>
              )}
            />
          )}
        </Card>

        {/* 右：当前会话内容 + 输入 */}
        <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 16 }}>
          <Card
            title={
              <Space>
                <span>{detail ? formatTitle(detail) : "选择或新建一个会话"}</span>
                {detail && <Tag color="blue">{detail.mode}</Tag>}
              </Space>
            }
            styles={{ body: { minHeight: 300, maxHeight: 480, overflowY: "auto" } }}
          >
            {loadingDetail ? (
              <div style={{ textAlign: "center", padding: 24 }}>
                <Spin />
              </div>
            ) : !detail ? (
              <Empty description="点左侧某个会话，或在下方录音直接开新会话" />
            ) : detail.messages.length === 0 ? (
              <Empty description="还没有消息。在下方录音/上传后会作为 user 消息追加" />
            ) : (
              detail.messages.map((m) => <MessageBubble key={m.id} msg={m} />)
            )}
          </Card>

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

          <GenerationPanel conversationId={activeId} />
        </div>
      </div>
    </div>
  );
}

export default Conversations;
