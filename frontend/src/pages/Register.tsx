import { useState } from "react";
import { Alert, Button, Card, Form, Input, Typography } from "antd";
import { Link, useNavigate } from "react-router-dom";

import { register } from "@/services/auth";
import { useAuthStore } from "@/store/auth";

const { Title } = Typography;

interface RegisterFormValues {
  email: string;
  password: string;
  nickname?: string;
}

function Register() {
  const navigate = useNavigate();
  const setSession = useAuthStore((s) => s.setSession);

  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const onFinish = async (values: RegisterFormValues) => {
    setError(null);
    setLoading(true);
    try {
      const { access_token, user } = await register(values);
      setSession(access_token, user);
      navigate("/", { replace: true });
    } catch (e) {
      setError(e instanceof Error ? e.message : "注册失败");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: "flex", justifyContent: "center", paddingTop: 80 }}>
      <Card style={{ width: 380 }}>
        <Title level={3} style={{ textAlign: "center", marginTop: 0 }}>
          注册
        </Title>

        {error && <Alert type="error" message={error} showIcon style={{ marginBottom: 16 }} />}

        <Form<RegisterFormValues> layout="vertical" onFinish={onFinish} disabled={loading}>
          <Form.Item
            label="邮箱"
            name="email"
            rules={[
              { required: true, message: "请输入邮箱" },
              { type: "email", message: "邮箱格式不正确" },
            ]}
          >
            <Input autoComplete="email" placeholder="you@example.com" />
          </Form.Item>

          <Form.Item
            label="密码"
            name="password"
            rules={[
              { required: true, message: "请输入密码" },
              { min: 8, max: 128, message: "密码长度需要在 8-128 字符之间" },
            ]}
          >
            <Input.Password autoComplete="new-password" placeholder="至少 8 位" />
          </Form.Item>

          <Form.Item
            label="昵称（可选）"
            name="nickname"
            rules={[{ max: 50, message: "昵称最长 50 字符" }]}
          >
            <Input placeholder="如何称呼你？" />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0 }}>
            <Button type="primary" htmlType="submit" loading={loading} block>
              注册
            </Button>
          </Form.Item>
        </Form>

        <div style={{ textAlign: "center", marginTop: 16 }}>
          已有账号？<Link to="/login">直接登录</Link>
        </div>
      </Card>
    </div>
  );
}

export default Register;
