import { useEffect, useState } from "react";
import { CopyOutlined, FormatPainterOutlined } from "@ant-design/icons";
import {
  Button,
  Card,
  Empty,
  List,
  Modal,
  Space,
  Spin,
  Tag,
  Typography,
} from "antd";

import FormatModal from "@/components/FormatModal";
import { notify } from "@/services/notify";
import {
  type Generation,
  getGeneration,
  listGenerations,
} from "@/services/generations";

const { Title, Paragraph, Text } = Typography;

function previewOf(g: Generation): string {
  if (!g.generated_content) return "";
  const flat = g.generated_content.replace(/\n+/g, " ").trim();
  return flat.length > 80 ? `${flat.slice(0, 80)}…` : flat;
}

function HistoryPage() {
  const [items, setItems] = useState<Generation[]>([]);
  const [loading, setLoading] = useState(false);
  const [openId, setOpenId] = useState<string | null>(null);
  const [openDetail, setOpenDetail] = useState<Generation | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [formatOpen, setFormatOpen] = useState(false);

  const refresh = async () => {
    setLoading(true);
    try {
      const { items: rows } = await listGenerations();
      setItems(rows);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
  }, []);

  useEffect(() => {
    if (openId === null) {
      setOpenDetail(null);
      return;
    }
    let cancelled = false;
    setLoadingDetail(true);
    getGeneration(openId)
      .then((d) => {
        if (!cancelled) setOpenDetail(d);
      })
      .catch(() => {
        if (!cancelled) setOpenDetail(null);
      })
      .finally(() => {
        if (!cancelled) setLoadingDetail(false);
      });
    return () => {
      cancelled = true;
    };
  }, [openId]);

  return (
    <Space direction="vertical" size="large" style={{ width: "100%" }}>
      <div>
        <Title level={2} style={{ marginBottom: 4 }}>
          生成历史
        </Title>
        <Paragraph type="secondary" style={{ marginBottom: 0 }}>
          展示所有用 step-2-16k 生成过的草稿。点开可查看完整正文。
        </Paragraph>
      </div>

      <Card>
        {loading ? (
          <div style={{ textAlign: "center", padding: 32 }}>
            <Spin />
          </div>
        ) : items.length === 0 ? (
          <Empty description="还没有生成记录，去对话创作页生成一篇试试" />
        ) : (
          <List
            dataSource={items}
            renderItem={(g) => (
              <List.Item
                style={{ cursor: "pointer" }}
                onClick={() => setOpenId(g.id)}
                actions={[
                  <Tag key="words" color="blue">
                    {g.word_count ?? 0} 字
                  </Tag>,
                  <Tag key="status" color={g.status === "draft" ? "default" : "green"}>
                    {g.status}
                  </Tag>,
                ]}
              >
                <List.Item.Meta
                  title={
                    <Text strong>
                      {g.title || "未命名草稿"}
                    </Text>
                  }
                  description={
                    <Space direction="vertical" size={0} style={{ width: "100%" }}>
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        {new Date(g.created_at).toLocaleString()}
                      </Text>
                      <Text style={{ fontSize: 13 }}>{previewOf(g)}</Text>
                    </Space>
                  }
                />
              </List.Item>
            )}
          />
        )}
      </Card>

      <Modal
        open={openId !== null}
        title={openDetail?.title || "生成详情"}
        onCancel={() => setOpenId(null)}
        width={760}
        footer={null}
      >
        {loadingDetail ? (
          <div style={{ textAlign: "center", padding: 32 }}>
            <Spin />
          </div>
        ) : openDetail ? (
          <Space direction="vertical" size="middle" style={{ width: "100%" }}>
            <Space>
              <Tag color="blue">{openDetail.word_count ?? 0} 字</Tag>
              <Tag>{openDetail.status}</Tag>
              <Text type="secondary" style={{ fontSize: 12 }}>
                {new Date(openDetail.created_at).toLocaleString()}
              </Text>
              <Button
                size="small"
                icon={<CopyOutlined />}
                onClick={() => {
                  navigator.clipboard.writeText(openDetail.generated_content || "");
                  notify.success("已复制到剪贴板");
                }}
              >
                复制全文
              </Button>
              <Button
                size="small"
                type="primary"
                icon={<FormatPainterOutlined />}
                onClick={() => setFormatOpen(true)}
              >
                一键排版
              </Button>
            </Space>
            <Paragraph
              style={{
                whiteSpace: "pre-wrap",
                maxHeight: 480,
                overflowY: "auto",
                background: "#fafafa",
                padding: 16,
                borderRadius: 4,
              }}
            >
              {openDetail.generated_content || "（无内容）"}
            </Paragraph>
          </Space>
        ) : (
          <Empty description="加载失败" />
        )}
      </Modal>

      {openDetail && (
        <FormatModal
          open={formatOpen}
          onClose={() => setFormatOpen(false)}
          content={openDetail.generated_content || ""}
          title={openDetail.title}
        />
      )}
    </Space>
  );
}

export default HistoryPage;
