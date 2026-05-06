import { useState } from "react";
import {
  AppstoreOutlined,
  BookOutlined,
  HomeOutlined,
  LogoutOutlined,
  MessageOutlined,
} from "@ant-design/icons";
import { Avatar, Dropdown, Layout, Menu, type MenuProps } from "antd";
import { Link, Outlet, useLocation, useNavigate } from "react-router-dom";

import { useAuthStore } from "@/store/auth";

const { Header, Sider, Content } = Layout;

const SIDER_WIDTH = 220;

const menuItems: MenuProps["items"] = [
  { key: "/", icon: <HomeOutlined />, label: <Link to="/">首页</Link> },
  {
    key: "/conversations",
    icon: <MessageOutlined />,
    label: <Link to="/conversations">对话创作</Link>,
  },
  {
    key: "documents",
    icon: <BookOutlined />,
    label: "文档库",
    disabled: true,
  },
  {
    key: "history",
    icon: <AppstoreOutlined />,
    label: "生成历史",
    disabled: true,
  },
];

function MainLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const user = useAuthStore((s) => s.user);
  const clear = useAuthStore((s) => s.clear);
  const [collapsed, setCollapsed] = useState(false);

  const handleLogout = () => {
    clear();
    navigate("/login", { replace: true });
  };

  const userMenuItems: MenuProps["items"] = [
    { key: "logout", icon: <LogoutOutlined />, label: "退出登录", onClick: handleLogout },
  ];

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Sider
        width={SIDER_WIDTH}
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        theme="dark"
      >
        <div
          style={{
            color: "#fff",
            fontSize: collapsed ? 18 : 16,
            textAlign: "center",
            padding: "16px 8px",
            whiteSpace: "nowrap",
            overflow: "hidden",
          }}
        >
          {collapsed ? "🎙️" : "🎙️ Voice2Article"}
        </div>
        <Menu theme="dark" mode="inline" selectedKeys={[location.pathname]} items={menuItems} />
      </Sider>

      <Layout>
        <Header
          style={{
            background: "#fff",
            padding: "0 24px",
            display: "flex",
            justifyContent: "flex-end",
            alignItems: "center",
            borderBottom: "1px solid #f0f0f0",
          }}
        >
          {user && (
            <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
              <div style={{ cursor: "pointer", display: "flex", alignItems: "center", gap: 8 }}>
                <Avatar size="small">{(user.nickname || user.email)[0]?.toUpperCase()}</Avatar>
                <span>{user.nickname || user.email}</span>
              </div>
            </Dropdown>
          )}
        </Header>

        <Content style={{ padding: 24, background: "#f5f5f5" }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}

export default MainLayout;
