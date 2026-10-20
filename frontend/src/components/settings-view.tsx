"use client";

import { useState, type FormEvent } from "react";
import { ExamPicker } from "@/components/exam-picker";
import { Alert, Button, Field, PageHeader, Panel } from "@/components/ui";
import { api, errorMessage, type TargetExam, type User } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export function SettingsView() {
  const { user, setUser } = useAuth();
  const [fullName, setFullName] = useState(user?.full_name ?? "");
  const [targetExam, setTargetExam] = useState<TargetExam>(user?.target_exam ?? "IELTS");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  const dirty = fullName !== user?.full_name || targetExam !== user?.target_exam;

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

  const memberSince = user
    ? new Date(user.created_at).toLocaleDateString(undefined, { day: "numeric", month: "long", year: "numeric" })
    : "";

  return (
    <div className="grid gap-10">
      <PageHeader eyebrow="Account" title="Profile" description={`Member since ${memberSince}.`} />

      <Panel className="max-w-xl p-6 sm:p-8">
        <form onSubmit={onSubmit} className="grid gap-5">
          {error && <Alert>{error}</Alert>}
          <Field id="name" label="Full name" autoComplete="name" required maxLength={100} value={fullName}
            onChange={(e) => { setFullName(e.target.value); setSaved(false); }} />
          <Field id="email" label="Email" value={user?.email ?? ""} readOnly disabled
            hint="Your email is your login, so it can't be changed here." />
          <ExamPicker value={targetExam} onChange={(v) => { setTargetExam(v); setSaved(false); }} />
          <div className="flex flex-wrap items-center gap-4 pt-1">
            <Button type="submit" loading={busy} disabled={!dirty}>
              {busy ? "Saving…" : "Save changes"}
            </Button>
            {saved && <Alert tone="success">Profile saved.</Alert>}
          </div>
        </form>
      </Panel>
    </div>
  );
}
