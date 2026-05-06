import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";

import { useAuthStore } from "@/store/auth";

interface ProtectedRouteProps {
  children: ReactNode;
}

function ProtectedRoute({ children }: ProtectedRouteProps) {
  const token = useAuthStore((s) => s.token);
  const location = useLocation();

  if (!token) {
    return <Navigate to="/login" state={{ from: location.pathname }} replace />;
  }
  return <>{children}</>;
}

export default ProtectedRoute;
