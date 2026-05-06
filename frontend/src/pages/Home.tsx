import { useEffect, useState } from "react";
import { Alert, Button, Card, Descriptions, Space, Typography } from "antd";

import { fetchHealth, type HealthResponse } from "@/services/api";

const { Title, Paragraph } = Typography;

function Home() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const check = async () => {
    setLoading(true);
    setError(null);
    try {
      setHealth(await fetchHealth());
    } catch (e) {
      const message = e instanceof Error ? e.message : "未知错误";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    check();
  }, []);

  return (
    <Space direction="vertical" size="large" style={{ width: "100%" }}>
      <div>
        <Title level={2}>欢迎使用语音对话公众号生成器</Title>
        <Paragraph type="secondary">
          MVP W1 — 当前为脚手架阶段，语音、生成、排版功能将在 W2-W4 陆续上线。
        </Paragraph>
      </div>

      <Card title="后端连通性检查" extra={<Button onClick={check} loading={loading}>重新检测</Button>}>
        {error && <Alert type="error" message={error} showIcon />}
        {health && (
          <Descriptions column={1} bordered size="small">
            <Descriptions.Item label="状态">{health.status}</Descriptions.Item>
            <Descriptions.Item label="服务名">{health.name}</Descriptions.Item>
            <Descriptions.Item label="版本">{health.version}</Descriptions.Item>
            <Descriptions.Item label="环境">{health.env}</Descriptions.Item>
          </Descriptions>
        )}
      </Card>
    </Space>
  );
}

export default Home;
