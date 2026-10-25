import type { ReactNode } from "react";
import { useAuthStore } from "../../store/authStore";

export function PermissionGate({
  permission,
  children,
}: {
  permission: "write" | "admin";
  children: ReactNode;
}) {
  const role = useAuthStore((state) => state.user?.role);
  const allowed = permission === "admin" ? role === "admin" : role === "admin" || role === "dev";
  return allowed ? children : null;
}
