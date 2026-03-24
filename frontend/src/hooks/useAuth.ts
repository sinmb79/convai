"use client";
import { create } from "zustand";
import { persist } from "zustand/middleware";
import api from "@/lib/api";
import type { User, TokenResponse } from "@/lib/types";

interface AuthState {
  user: User | null;
  accessToken: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  setUser: (user: User) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      login: async (email, password) => {
        const formData = new FormData();
        formData.append("username", email);
        formData.append("password", password);
        const resp = await api.post<TokenResponse>("/auth/login", formData, {
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
        });
        const { access_token, refresh_token, user } = resp.data;
        localStorage.setItem("access_token", access_token);
        localStorage.setItem("refresh_token", refresh_token);
        set({ user, accessToken: access_token });
      },
      logout: () => {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        set({ user: null, accessToken: null });
      },
      setUser: (user) => set({ user }),
    }),
    { name: "conai-auth", partialize: (state) => ({ user: state.user }) }
  )
);

export function useAuth() {
  return useAuthStore();
}
