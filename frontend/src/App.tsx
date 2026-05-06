import { Route, Routes } from "react-router-dom";

import ProtectedRoute from "@/components/ProtectedRoute";
import AuthLayout from "@/layouts/AuthLayout";
import MainLayout from "@/layouts/MainLayout";
import Home from "@/pages/Home";
import Login from "@/pages/Login";
import NotFound from "@/pages/NotFound";
import Register from "@/pages/Register";

function App() {
  return (
    <Routes>
      {/* 已认证：带侧边栏的主布局 */}
      <Route
        element={
          <ProtectedRoute>
            <MainLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/" element={<Home />} />
        {/* 未匹配路径：登录态下显示 404 页面 */}
        <Route path="*" element={<NotFound />} />
      </Route>

      {/* 未认证：登录注册页，独立布局 */}
      <Route element={<AuthLayout />}>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
      </Route>
    </Routes>
  );
}

export default App;
