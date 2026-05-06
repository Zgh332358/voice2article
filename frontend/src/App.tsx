import { Avatar, Button, Dropdown, Layout, Menu, Space } from "antd";
import { Link, Route, Routes, useNavigate } from "react-router-dom";

import ProtectedRoute from "@/components/ProtectedRoute";
import Home from "@/pages/Home";
import Login from "@/pages/Login";
import Register from "@/pages/Register";
import { useAuthStore } from "@/store/auth";

const { Header, Content, Footer } = Layout;

function App() {
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
  const clear = useAuthStore((s) => s.clear);

  const handleLogout = () => {
    clear();
    navigate("/login", { replace: true });
  };

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Header style={{ display: "flex", alignItems: "center" }}>
        <div style={{ color: "#fff", fontSize: 18, marginRight: 32 }}>🎙️ 语音公众号生成器</div>
        <Menu
          theme="dark"
          mode="horizontal"
          defaultSelectedKeys={["home"]}
          style={{ flex: 1, minWidth: 0 }}
          items={[{ key: "home", label: <Link to="/">首页</Link> }]}
        />
        <Space>
          {user ? (
            <Dropdown
              menu={{
                items: [{ key: "logout", label: "退出登录", onClick: handleLogout }],
              }}
            >
              <Space style={{ color: "#fff", cursor: "pointer" }}>
                <Avatar size="small">{(user.nickname || user.email)[0]?.toUpperCase()}</Avatar>
                <span>{user.nickname || user.email}</span>
              </Space>
            </Dropdown>
          ) : (
            <>
              <Button type="link" style={{ color: "#fff" }} onClick={() => navigate("/login")}>
                登录
              </Button>
              <Button type="primary" onClick={() => navigate("/register")}>
                注册
              </Button>
            </>
          )}
        </Space>
      </Header>

      <Content style={{ padding: "24px 48px" }}>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Home />
              </ProtectedRoute>
            }
          />
        </Routes>
      </Content>

      <Footer style={{ textAlign: "center" }}>Voice Article Generator · MVP W1 Day 3-4</Footer>
    </Layout>
  );
}

export default App;
