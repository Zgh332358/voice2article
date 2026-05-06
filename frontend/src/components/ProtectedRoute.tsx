import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { jwtDecode } from "jwt-decode";

import { useAuthStore } from "@/store/auth";

interface ProtectedRouteProps {
  children: ReactNode;
}

interface JwtPayload {
  exp?: number;
  sub?: string;
}

/** 客户端校验 token 是否仍然有效。无效则返回 false 并清登录态。 */
function isTokenValid(token: string | null, clear: () => void): boolean {
  if (!token) return false;
  try {
    const { exp } = jwtDecode<JwtPayload>(token);
    if (typeof exp !== "number") {
      clear();
      return false;
    }
    // exp 是秒级 Unix 时间戳；提前 30 秒认定过期，避免临界请求
    const nowSec = Math.floor(Date.now() / 1000);
    if (exp - nowSec <= 30) {
      clear();
      return false;
    }
    return true;
  } catch {
    clear();
    return false;
  }
}

function ProtectedRoute({ children }: ProtectedRouteProps) {
  const token = useAuthStore((s) => s.token);
  const clear = useAuthStore((s) => s.clear);
  const location = useLocation();

  if (!isTokenValid(token, clear)) {
    return <Navigate to="/login" state={{ from: location.pathname }} replace />;
  }
  return <>{children}</>;
}

export default ProtectedRoute;
