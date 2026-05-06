import { Layout, Menu } from "antd";
import { Link, Route, Routes } from "react-router-dom";

import Home from "./pages/Home";

const { Header, Content, Footer } = Layout;

function App() {
  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Header>
        <div style={{ color: "#fff", fontSize: 18, float: "left", marginRight: 32 }}>
          🎙️ 语音公众号生成器
        </div>
        <Menu
          theme="dark"
          mode="horizontal"
          defaultSelectedKeys={["home"]}
          items={[
            { key: "home", label: <Link to="/">首页</Link> },
          ]}
        />
      </Header>

      <Content style={{ padding: "24px 48px" }}>
        <Routes>
          <Route path="/" element={<Home />} />
        </Routes>
      </Content>

      <Footer style={{ textAlign: "center" }}>
        Voice Article Generator · MVP W1
      </Footer>
    </Layout>
  );
}

export default App;
