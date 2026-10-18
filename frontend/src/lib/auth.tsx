"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { api, tokenStore, UNAUTHORIZED_EVENT, type TargetExam, type TokenResponse, type User } from "@/lib/api";

type Status = "loading" | "authenticated" | "anonymous";

interface AuthValue {
  user: User | null;
  status: Status;
  login: (email: string, password: string) => Promise<void>;
  register: (input: { full_name: string; email: string; password: string; target_exam: TargetExam }) => Promise<void>;
  logout: () => void;
  setUser: (u: User) => void;
}

const AuthContext = createContext<AuthValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [status, setStatus] = useState<Status>("loading");

  const logout = useCallback(() => {
    tokenStore.clear();
    setUser(null);
    setStatus("anonymous");
  }, []);

  // On first load: if a token is stored, ask the backend who it belongs to.
  useEffect(() => {
    let cancelled = false;
    if (!tokenStore.get()) {
      Promise.resolve().then(() => !cancelled && setStatus("anonymous"));
      return;
    }
    api<User>("/users/me")
      .then((u) => {
        if (cancelled) return;
        setUser(u);
        setStatus("authenticated");
      })
      .catch(() => {
        if (cancelled) return;
        tokenStore.clear();
        setStatus("anonymous");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  // Any API call that gets a 401 (e.g. expired token) logs the user out.
  useEffect(() => {
    window.addEventListener(UNAUTHORIZED_EVENT, logout);
    return () => window.removeEventListener(UNAUTHORIZED_EVENT, logout);
  }, [logout]);

  const accept = useCallback((res: TokenResponse) => {
    tokenStore.set(res.access_token);
    setUser(res.user);
    setStatus("authenticated");
  }, []);

  const login = useCallback(
    async (email: string, password: string) => {
      accept(await api<TokenResponse>("/auth/login", { method: "POST", auth: false, body: { email, password } }));
    },
    [accept],
  );

  const register = useCallback(
    async (input: { full_name: string; email: string; password: string; target_exam: TargetExam }) => {
      accept(await api<TokenResponse>("/auth/register", { method: "POST", auth: false, body: input }));
    },
    [accept],
  );

  const value = useMemo(
    () => ({ user, status, login, register, logout, setUser }),
    [user, status, login, register, logout],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}
