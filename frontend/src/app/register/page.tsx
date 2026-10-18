"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState, type FormEvent } from "react";
import { AuthCard } from "@/components/auth-card";
import { Button, ErrorAlert, Field, SelectField, Spinner } from "@/components/ui";
import { errorMessage, type TargetExam } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export default function RegisterPage() {
  const { register, status } = useAuth();
  const router = useRouter();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [targetExam, setTargetExam] = useState<TargetExam>("IELTS");
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
      await register({ full_name: fullName, email, password, target_exam: targetExam });
      router.replace("/dashboard");
    } catch (err) {
      setError(errorMessage(err));
      setBusy(false);
    }
  }

  return (
    <AuthCard title="Create your account" subtitle="Tell us which exam you are preparing for.">
      <form onSubmit={onSubmit} className="space-y-4">
        {error && <ErrorAlert>{error}</ErrorAlert>}
        <Field id="name" label="Full name" autoComplete="name" required maxLength={100} value={fullName}
          onChange={(e) => setFullName(e.target.value)} />
        <Field id="email" label="Email" type="email" autoComplete="email" required value={email}
          onChange={(e) => setEmail(e.target.value)} />
        <Field id="password" label="Password (at least 8 characters)" type="password" autoComplete="new-password"
          required minLength={8} maxLength={72} value={password} onChange={(e) => setPassword(e.target.value)} />
        <SelectField id="exam" label="Target exam" value={targetExam}
          onChange={(e) => setTargetExam(e.target.value as TargetExam)}>
          <option value="IELTS">IELTS</option>
          <option value="TOEFL">TOEFL</option>
          <option value="PTE">PTE</option>
        </SelectField>
        <Button type="submit" className="w-full gap-2" disabled={busy}>
          {busy && <Spinner />} Create account
        </Button>
      </form>
      <p className="mt-6 text-center text-sm text-zinc-500">
        Already registered?{" "}
        <Link href="/login" className="font-medium text-indigo-600 hover:underline dark:text-indigo-400">
          Log in
        </Link>
      </p>
    </AuthCard>
  );
}
