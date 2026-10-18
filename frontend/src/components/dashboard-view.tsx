"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Card, ErrorAlert, Spinner } from "@/components/ui";
import { api, errorMessage, type WritingSubmissionSummary } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { bandTone, formatBand, writingOverall } from "@/lib/bands";

const OTHER_SKILLS = ["Reading", "Listening", "Speaking"];

export function DashboardView() {
  const { user } = useAuth();
  const [subs, setSubs] = useState<WritingSubmissionSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api<WritingSubmissionSummary[]>("/writing/submissions")
      .then(setSubs)
      .catch((e) => setError(errorMessage(e)));
  }, []);

  const completed = (subs ?? []).filter((s) => s.status === "completed");
  const overalls = completed.map(writingOverall).filter((v): v is number => v !== null);
  const average = overalls.length ? overalls.reduce((a, b) => a + b, 0) / overalls.length : null;
  const latest = overalls[0] ?? null;

  return (
    <div className="space-y-8">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-sm text-zinc-500">Welcome back,</p>
          <h1 className="text-3xl font-semibold tracking-tight">{user?.full_name}</h1>
          <p className="mt-1 text-sm text-zinc-500">Preparing for {user?.target_exam}</p>
        </div>
        <Link
          href="/writing"
          className="rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-indigo-500"
        >
          Start writing practice
        </Link>
      </header>

      {error && <ErrorAlert>{error}</ErrorAlert>}

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <p className="text-sm font-medium">Writing</p>
          <p className={`mt-2 text-3xl font-semibold ${average !== null ? bandTone(average) : "text-zinc-400"}`}>
            {average !== null ? formatBand(Math.round(average * 10) / 10) : "–"}
          </p>
          <p className="mt-1 text-xs text-zinc-500">
            {subs === null ? "Loading…" : `${completed.length} attempt${completed.length === 1 ? "" : "s"}`}
            {latest !== null && ` · latest ${formatBand(latest)}`}
          </p>
        </Card>
        {OTHER_SKILLS.map((name) => (
          <Card key={name} className="opacity-60">
            <p className="text-sm font-medium">{name}</p>
            <p className="mt-2 text-3xl font-semibold text-zinc-400">–</p>
            <p className="mt-1 text-xs text-zinc-500">Coming soon</p>
          </Card>
        ))}
      </section>

      <section>
        <h2 className="mb-3 text-lg font-semibold">Recent writing attempts</h2>
        {subs === null && !error && (
          <div className="py-6 text-zinc-500">
            <Spinner />
          </div>
        )}
        {subs !== null && subs.length === 0 && (
          <Card className="text-center text-sm text-zinc-500">
            No attempts yet.{" "}
            <Link href="/writing" className="font-medium text-indigo-600 hover:underline dark:text-indigo-400">
              Write your first essay
            </Link>
            .
          </Card>
        )}
        {subs !== null && subs.length > 0 && (
          <Card className="divide-y divide-zinc-200 p-0 dark:divide-zinc-800">
            {subs.slice(0, 10).map((s) => {
              const overall = writingOverall(s);
              return (
                <div key={s.writing_id} className="flex items-center justify-between gap-4 px-5 py-3.5">
                  <div>
                    <p className="text-sm font-medium">
                      Task {s.task_type.replace("task", "")} · {s.word_count} words
                    </p>
                    <p className="text-xs text-zinc-500">{new Date(s.submitted_at).toLocaleString()}</p>
                  </div>
                  {s.status === "completed" && overall !== null ? (
                    <span className={`text-xl font-semibold ${bandTone(overall)}`}>{formatBand(overall)}</span>
                  ) : (
                    <span className="rounded-full bg-zinc-100 px-2 py-0.5 text-xs text-zinc-500 dark:bg-zinc-800">
                      {s.status}
                    </span>
                  )}
                </div>
              );
            })}
          </Card>
        )}
      </section>
    </div>
  );
}
