import { useState } from "react";
import { Alert, Button, Card, Form, Input, Typography } from "antd";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { login } from "@/services/auth";
import { useAuthStore } from "@/store/auth";

const { Title } = Typography;

interface LoginFormValues {
  email: string;
  password: string;
}

function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const setSession = useAuthStore((s) => s.setSession);

  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const from = (location.state as { from?: string } | null)?.from || "/";

  const onFinish = async (values: LoginFormValues) => {
    setError(null);
    setLoading(true);
    try {
      const { access_token, user } = await login(values);
      setSession(access_token, user);
      navigate(from, { replace: true });
    } catch (e) {
      setError(e instanceof Error ? e.message : "登录失败");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: "flex", justifyContent: "center", paddingTop: 80 }}>
      <Card style={{ width: 380 }}>
        <Title level={3} style={{ textAlign: "center", marginTop: 0 }}>
          登录
        </Title>

        {error && <Alert type="error" message={error} showIcon style={{ marginBottom: 16 }} />}

        <Form<LoginFormValues> layout="vertical" onFinish={onFinish} disabled={loading}>
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
            rules={[{ required: true, message: "请输入密码" }]}
          >
            <Input.Password autoComplete="current-password" placeholder="密码" />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0 }}>
            <Button type="primary" htmlType="submit" loading={loading} block>
              登录
            </Button>
          </Form.Item>
        </Form>

        <div style={{ textAlign: "center", marginTop: 16 }}>
          还没有账号？<Link to="/register">立即注册</Link>
        </div>
      </Card>
    </div>
  );
}

export default Login;
