"use client";

import { useState, type FormEvent } from "react";
import { Button, Card, ErrorAlert, Field, SelectField, Spinner } from "@/components/ui";
import { api, errorMessage, type TargetExam, type User } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export function SettingsView() {
  const { user, setUser } = useAuth();
  const [fullName, setFullName] = useState(user?.full_name ?? "");
  const [targetExam, setTargetExam] = useState<TargetExam>(user?.target_exam ?? "IELTS");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSaved(false);
    setBusy(true);
    try {
      const updated = await api<User>("/users/me", {
        method: "PUT",
        body: { full_name: fullName, target_exam: targetExam },
      });
      setUser(updated);
      setSaved(true);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold tracking-tight">Profile</h1>
      <Card className="max-w-lg">
        <form onSubmit={onSubmit} className="space-y-4">
          {error && <ErrorAlert>{error}</ErrorAlert>}
          {saved && (
            <p role="status" className="text-sm text-emerald-600 dark:text-emerald-400">
              Profile updated.
            </p>
          )}
          <Field id="name" label="Full name" required maxLength={100} value={fullName}
            onChange={(e) => { setFullName(e.target.value); setSaved(false); }} />
          <Field id="email" label="Email" value={user?.email ?? ""} disabled readOnly />
          <SelectField id="exam" label="Target exam" value={targetExam}
            onChange={(e) => { setTargetExam(e.target.value as TargetExam); setSaved(false); }}>
            <option value="IELTS">IELTS</option>
            <option value="TOEFL">TOEFL</option>
            <option value="PTE">PTE</option>
          </SelectField>
          <Button type="submit" disabled={busy} className="gap-2">
            {busy && <Spinner />} Save changes
          </Button>
        </form>
      </Card>
    </div>
  );
}
