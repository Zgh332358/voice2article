import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { App as AntdApp, ConfigProvider } from "antd";
import zhCN from "antd/locale/zh_CN";

import App from "./App";
import { setMessageApi } from "./services/notify";
import "./styles/global.css";

function Bootstrap() {
  const { message } = AntdApp.useApp();
  setMessageApi(message);
  return <App />;
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ConfigProvider locale={zhCN}>
      <AntdApp>
        <BrowserRouter>
          <Bootstrap />
        </BrowserRouter>
      </AntdApp>
    </ConfigProvider>
  </React.StrictMode>
);
