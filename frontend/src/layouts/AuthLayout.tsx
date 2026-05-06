import { Layout } from "antd";
import { Outlet } from "react-router-dom";

const { Content } = Layout;

function AuthLayout() {
  return (
    <Layout style={{ minHeight: "100vh", background: "#f5f5f5" }}>
      <Content>
        <Outlet />
      </Content>
    </Layout>
  );
}

export default AuthLayout;
