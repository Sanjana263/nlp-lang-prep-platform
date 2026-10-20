"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState, type FormEvent } from "react";
import { AuthCard } from "@/components/auth-card";
import { PasswordField } from "@/components/password-field";
import { Alert, Button, Field, TextLink } from "@/components/ui";
import { errorMessage } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export default function LoginPage() {
  const { login, status } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (status === "authenticated") router.replace("/dashboard");
  }, [status, router]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await login(email, password);
      router.replace("/dashboard");
    } catch (err) {
      setError(errorMessage(err));
      setBusy(false);
    }
  }

  return (
    <AuthCard title="Welcome back" subtitle="Log in to pick up where you left off.">
      <form onSubmit={onSubmit} className="grid gap-5">
        {error && <Alert>{error}</Alert>}
        <Field id="email" label="Email" type="email" autoComplete="email" required value={email}
          onChange={(e) => setEmail(e.target.value)} />
        <PasswordField id="password" label="Password" autoComplete="current-password" required value={password}
          onChange={(e) => setPassword(e.target.value)} />
        <Button type="submit" loading={busy} className="mt-1 w-full">
          {busy ? "Logging in…" : "Log in"}
        </Button>
      </form>
      <p className="mt-8 text-ink-2">
        New to Cadence? <TextLink href="/register">Create an account</TextLink>
      </p>
    </AuthCard>
  );
}
