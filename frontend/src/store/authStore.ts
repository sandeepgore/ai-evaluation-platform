import { create } from "zustand";
import { persist } from "zustand/middleware";

export type AppRole = "admin" | "dev" | "user";
export interface AuthUser { id: string; email: string; full_name: string | null; role: AppRole; is_active?: boolean; created_at?: string | null }
interface AuthState {
  token: string | null;
  user: AuthUser | null;
  setSession: (token: string, user: AuthUser) => void;
  clearSession: () => void;
}

export const useAuthStore = create<AuthState>()(persist((set) => ({
  token: null,
  user: null,
  setSession: (token, user) => set({ token, user }),
  clearSession: () => set({ token: null, user: null }),
}), { name: "ai-evaluation-auth" }));
