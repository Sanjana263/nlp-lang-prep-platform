"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState, type FormEvent } from "react";
import { AuthCard } from "@/components/auth-card";
import { PasswordField } from "@/components/password-field";
import { Alert, Button, Field, TextLink } from "@/components/ui";
import { ExamPicker } from "@/components/exam-picker";
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
    <AuthCard title="Create your account" subtitle="Free to use. Pick the exam you are preparing for.">
      <form onSubmit={onSubmit} className="grid gap-5">
        {error && <Alert>{error}</Alert>}
        <Field id="name" label="Full name" autoComplete="name" required maxLength={100} value={fullName}
          onChange={(e) => setFullName(e.target.value)} />
        <Field id="email" label="Email" type="email" autoComplete="email" required value={email}
          onChange={(e) => setEmail(e.target.value)} />
        <PasswordField id="password" label="Password" hint="At least 8 characters." autoComplete="new-password"
          required minLength={8} maxLength={72} value={password} onChange={(e) => setPassword(e.target.value)} />
        <ExamPicker value={targetExam} onChange={setTargetExam} />
        <Button type="submit" loading={busy} className="mt-1 w-full">
          {busy ? "Creating account…" : "Create account"}
        </Button>
      </form>
      <p className="mt-8 text-ink-2">
        Already registered? <TextLink href="/login">Log in</TextLink>
      </p>
    </AuthCard>
  );
}
