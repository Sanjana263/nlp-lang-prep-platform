"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState, type FormEvent } from "react";
import { AuthCard } from "@/components/auth-card";
import { Button, ErrorAlert, Field, Spinner } from "@/components/ui";
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
    <AuthCard title="Welcome back" subtitle="Log in to continue your practice.">
      <form onSubmit={onSubmit} className="space-y-4">
        {error && <ErrorAlert>{error}</ErrorAlert>}
        <Field id="email" label="Email" type="email" autoComplete="email" required value={email}
          onChange={(e) => setEmail(e.target.value)} />
        <Field id="password" label="Password" type="password" autoComplete="current-password" required value={password}
          onChange={(e) => setPassword(e.target.value)} />
        <Button type="submit" className="w-full gap-2" disabled={busy}>
          {busy && <Spinner />} Log in
        </Button>
      </form>
      <p className="mt-6 text-center text-sm text-zinc-500">
        New here?{" "}
        <Link href="/register" className="font-medium text-indigo-600 hover:underline dark:text-indigo-400">
          Create an account
        </Link>
      </p>
    </AuthCard>
  );
}
