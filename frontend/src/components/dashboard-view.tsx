"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  ArrowRightIcon,
  BookOpenTextIcon,
  HeadphonesIcon,
  MicrophoneIcon,
  PencilLineIcon,
} from "@phosphor-icons/react/ssr";
import { BandTrend } from "@/components/band-trend";
import {
  Alert,
  Badge,
  BandFigure,
  BandScale,
  EmptyState,
  Eyebrow,
  LinkButton,
  PageHeader,
  Panel,
  SectionHeading,
  Skeleton,
} from "@/components/ui";
import { api, errorMessage, type SpeakingSubmissionSummary, type WritingSubmissionSummary } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { bandDescriptor, bandTone, formatBand, roundBand, writingOverall } from "@/lib/bands";

const IN_DEVELOPMENT = [
  { name: "Reading", Icon: BookOpenTextIcon },
  { name: "Listening", Icon: HeadphonesIcon },
];

const shortDate = (iso: string) => new Date(iso).toLocaleDateString(undefined, { day: "numeric", month: "short" });

export function DashboardView() {
  const { user } = useAuth();
  const [subs, setSubs] = useState<WritingSubmissionSummary[] | null>(null);
  const [speaking, setSpeaking] = useState<SpeakingSubmissionSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api<WritingSubmissionSummary[]>("/writing/submissions")
      .then(setSubs)
      .catch((e) => setError(errorMessage(e)));
    api<SpeakingSubmissionSummary[]>("/speaking/submissions")
      .then(setSpeaking)
      .catch(() => setSpeaking([]));
  }, []);

  const spoken = (speaking ?? []).filter((s) => s.status === "completed" && s.overall_band !== null);
  const speakingAverage = spoken.length ? roundBand(spoken.reduce((a, s) => a + s.overall_band!, 0) / spoken.length) : null;

  const scored = (subs ?? [])
    .map((s) => ({ s, band: writingOverall(s) }))
    .filter((x): x is { s: WritingSubmissionSummary; band: number } => x.s.status === "completed" && x.band !== null);
  const average = scored.length ? roundBand(scored.reduce((a, x) => a + x.band, 0) / scored.length) : null;
  const best = scored.length ? Math.max(...scored.map((x) => x.band)) : null;
  const trend = scored
    .slice(0, 12)
    .reverse()
    .map((x) => ({ band: x.band, date: shortDate(x.s.submitted_at) }));
  const firstName = user?.full_name.split(/\s+/)[0];

  return (
    <div className="grid gap-12">
      <PageHeader
        eyebrow={`${user?.target_exam} preparation`}
        title={`Welcome back, ${firstName}`}
        description="Your scores so far, and what to practise next."
        actions={
          <LinkButton href="/writing">
            Start writing practice <ArrowRightIcon aria-hidden size={16} weight="bold" />
          </LinkButton>
        }
      />

      {error && <Alert>{error} Refresh the page to try again.</Alert>}

      <section aria-labelledby="writing-summary">
        <Panel className="grid gap-8 p-6 sm:p-8 lg:grid-cols-[minmax(0,15rem)_minmax(0,1fr)]">
          <div className="grid content-start gap-5">
            <div className="flex items-center gap-2 text-ink-2">
              <PencilLineIcon aria-hidden size={20} />
              <h2 id="writing-summary" className="font-semibold">Writing · average band</h2>
            </div>
            {subs === null && !error ? (
              <Skeleton className="h-20 w-32" />
            ) : (
              <BandFigure score={average} size="xl" />
            )}
            <dl className="grid grid-cols-3 gap-4 border-t border-rule pt-4">
              <Stat label="Essays" value={subs === null ? "…" : String(scored.length)} />
              <Stat label="Latest" value={formatBand(scored[0]?.band)} />
              <Stat label="Best" value={formatBand(best)} />
            </dl>
          </div>

          <div className="grid min-w-0 content-start gap-6">
            <BandScale score={average} label="Average writing band" />
            {subs === null && !error && <Skeleton className="h-36 w-full" />}
            {trend.length >= 2 && <BandTrend points={trend} />}
            {subs !== null && trend.length < 2 && (
              <p className="text-ink-2">
                {scored.length === 0
                  ? "Submit your first essay to see where you sit on the band scale."
                  : "Submit one more essay to start seeing your trend."}
              </p>
            )}
          </div>
        </Panel>
      </section>

      <section aria-labelledby="other-skills">
        <h2 id="other-skills" className="sr-only">Other skills</h2>
        <ul className="grid gap-3 sm:grid-cols-3">
          <li>
            <Link
              href="/speaking"
              className="flex h-full items-center gap-3 rounded-xl border border-rule bg-surface px-4 py-4 transition-colors duration-150 hover:border-accent focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
            >
              <MicrophoneIcon aria-hidden size={22} className="text-accent" />
              <span className="min-w-0">
                <span className="block font-semibold text-ink">Speaking</span>
                <span className="block text-sm text-ink-3">
                  {speaking === null ? "Loading…" : spoken.length === 0 ? "Record your first answer" : `${spoken.length} answer${spoken.length === 1 ? "" : "s"} · average band`}
                </span>
              </span>
              <span className={`ml-auto font-display text-3xl font-semibold tabular-nums ${speakingAverage !== null ? bandTone(speakingAverage) : "text-ink-3"}`}>
                {formatBand(speakingAverage)}
              </span>
            </Link>
          </li>
          {IN_DEVELOPMENT.map(({ name, Icon }) => (
            <li key={name} className="flex items-center gap-3 rounded-xl border border-dashed border-rule-strong px-4 py-4">
              <Icon aria-hidden size={22} className="text-ink-3" />
              <span className="font-semibold text-ink-2">{name}</span>
              <span className="ml-auto">
                <Badge>In development</Badge>
              </span>
            </li>
          ))}
        </ul>
      </section>

      <section aria-labelledby="recent">
        <SectionHeading>
          <span id="recent">Recent essays</span>
        </SectionHeading>

        {subs === null && !error && (
          <div className="grid gap-2">
            {[0, 1, 2].map((i) => <Skeleton key={i} className="h-16 w-full" />)}
          </div>
        )}

        {subs !== null && subs.length === 0 && (
          <EmptyState
            icon={<PencilLineIcon aria-hidden size={32} />}
            title="No essays yet"
            action={<LinkButton href="/writing" variant="secondary">Write your first essay</LinkButton>}
          >
            Each essay you submit appears here with its band and the date you wrote it.
          </EmptyState>
        )}

        {subs !== null && subs.length > 0 && (
          <Panel className="overflow-hidden">
            <div aria-hidden className="hidden grid-cols-[7rem_minmax(0,1fr)_6rem_9rem] gap-4 border-b border-rule bg-paper px-5 py-2.5 sm:grid">
              <Eyebrow>Date</Eyebrow>
              <Eyebrow>Task</Eyebrow>
              <Eyebrow className="text-right">Words</Eyebrow>
              <Eyebrow className="text-right">Band</Eyebrow>
            </div>
            <ul className="divide-y divide-rule">
              {subs.slice(0, 10).map((s) => {
                const band = writingOverall(s);
                return (
                  <li
                    key={s.writing_id}
                    className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-x-4 gap-y-0.5 px-5 py-3.5 sm:grid-cols-[7rem_minmax(0,1fr)_6rem_9rem]"
                  >
                    <span className="font-mono text-sm text-ink-2 tabular-nums">{shortDate(s.submitted_at)}</span>
                    <span className="row-start-2 text-ink sm:row-start-auto">
                      Task {s.task_type.replace("task", "")} essay
                      <span className="text-ink-3 sm:hidden"> · {s.word_count} words</span>
                    </span>
                    <span className="hidden text-right font-mono text-sm text-ink-2 tabular-nums sm:block">{s.word_count}</span>
                    <span className="col-start-2 row-span-2 row-start-1 text-right sm:col-start-auto sm:row-span-1 sm:row-start-auto">
                      {s.status === "completed" && band !== null ? (
                        <span className="inline-flex items-baseline gap-2">
                          <span className="hidden text-sm text-ink-3 lg:inline">{bandDescriptor(band).replace(" user", "")}</span>
                          <span className={`font-display text-2xl font-semibold tabular-nums ${bandTone(band)}`}>{formatBand(band)}</span>
                        </span>
                      ) : (
                        <Badge tone={s.status === "failed" ? "danger" : "neutral"}>
                          {s.status === "failed" ? "Not scored" : "Scoring"}
                        </Badge>
                      )}
                    </span>
                  </li>
                );
              })}
            </ul>
          </Panel>
        )}
      </section>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-sm text-ink-3">{label}</dt>
      <dd className="font-mono text-lg font-semibold text-ink tabular-nums">{value}</dd>
    </div>
  );
}
