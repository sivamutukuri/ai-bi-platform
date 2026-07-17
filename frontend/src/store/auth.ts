"use client";

import { create } from "zustand";

import { api, clearTokens, setTokens } from "@/lib/api";
import { User } from "@/lib/types";

interface AuthState {
  user: User | null;
  loading: boolean;
  initialized: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string) => Promise<void>;
  fetchMe: () => Promise<void>;
  logout: () => void;
}

export const useAuth = create<AuthState>((set) => ({
  user: null,
  loading: false,
  initialized: false,

  login: async (email, password) => {
    set({ loading: true });
    try {
      const form = new URLSearchParams();
      form.append("username", email);
      form.append("password", password);
      const { data } = await api.post("/auth/login", form, {
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      });
      setTokens(data.access_token, data.refresh_token);
      const me = await api.get("/auth/me");
      set({ user: me.data });
    } finally {
      set({ loading: false });
    }
  },

  register: async (email, password, fullName) => {
    set({ loading: true });
    try {
      await api.post("/auth/register", {
        email,
        password,
        full_name: fullName || null,
      });
    } finally {
      set({ loading: false });
    }
  },

  fetchMe: async () => {
    try {
      const me = await api.get("/auth/me");
      set({ user: me.data, initialized: true });
    } catch {
      set({ user: null, initialized: true });
    }
  },

  logout: () => {
    clearTokens();
    set({ user: null });
    if (typeof window !== "undefined") window.location.href = "/login";
  },
}));
