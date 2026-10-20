"use client";

import { ArrowRightIcon, ClockIcon } from "@phosphor-icons/react/ssr";
import { Badge, Eyebrow, Skeleton } from "@/components/ui";
import type { SpeakingPrompt, SpeakingSubmissionSummary } from "@/lib/api";
import { bandTone, formatBand } from "@/lib/bands";

const PARTS: { part: 1 | 2 | 3; name: string; about: string }[] = [
  { part: 1, name: "Part 1", about: "Short answers about familiar topics" },
  { part: 2, name: "Part 2", about: "A long turn from a cue card: 1 minute to prepare, up to 2 to speak" },
  { part: 3, name: "Part 3", about: "Discussion of wider, more abstract issues" },
];

const minutes = (s: number) => (s >= 60 ? `${Math.round(s / 60)} min` : `${s} s`);

export function QuestionPicker({
  prompts,
  part,
  onPart,
  onPick,
  history,
  onOpen,
}: {
  prompts: SpeakingPrompt[] | null;
  part: 1 | 2 | 3;
  onPart: (p: 1 | 2 | 3) => void;
  onPick: (p: SpeakingPrompt) => void;
  history: SpeakingSubmissionSummary[] | null;
  onOpen: (id: number) => void;
}) {
  const current = PARTS.find((p) => p.part === part)!;
  return (
    <div className="grid gap-10 lg:grid-cols-[minmax(0,1fr)_minmax(0,18rem)]">
      <section aria-labelledby="choose" className="grid min-w-0 grid-cols-1 content-start gap-5">
        <div role="group" aria-label="Test part" className="grid grid-cols-3 gap-1 rounded-xl bg-surface-2 p-1">
          {PARTS.map((p) => (
            <button
              key={p.part}
              aria-pressed={part === p.part}
              onClick={() => onPart(p.part)}
              className="min-h-11 cursor-pointer rounded-lg px-3 font-semibold text-ink-2 transition-colors duration-150 hover:text-ink focus-visible:outline-2 focus-visible:outline-accent aria-pressed:bg-surface aria-pressed:text-ink aria-pressed:shadow-[0_1px_2px_rgb(18_26_43/0.08)]"
            >
              {p.name}
            </button>
          ))}
        </div>
        <p id="choose" className="text-ink-2">{current.about}. Choose a question to answer.</p>

        <ul className="grid gap-3">
          {prompts === null &&
            [0, 1, 2].map((i) => (
              <li key={i}>
                <Skeleton className="h-24 w-full" />
              </li>
            ))}
          {prompts
            ?.filter((p) => p.part === part)
            .map((p) => (
              <li key={p.id}>
                <button
                  onClick={() => onPick(p)}
                  className="group grid w-full cursor-pointer gap-2 rounded-xl border border-rule bg-surface px-5 py-4 text-left transition-colors duration-150 hover:border-accent focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
                >
                  <span className="flex items-center justify-between gap-3">
                    <Eyebrow>{p.topic}</Eyebrow>
                    <span className="flex items-center gap-1.5 font-mono text-xs text-ink-3">
                      <ClockIcon aria-hidden size={14} /> {minutes(p.speak_seconds)}
                    </span>
                  </span>
                  <span className="font-display text-xl leading-snug text-ink">{p.question}</span>
                  <span className="flex items-center gap-1.5 text-sm font-semibold text-accent">
                    Answer this question
                    <ArrowRightIcon aria-hidden size={14} weight="bold" className="transition-transform duration-150 group-hover:translate-x-0.5" />
                  </span>
                </button>
              </li>
            ))}
        </ul>
      </section>

      <aside aria-labelledby="recent-speaking" className="grid min-w-0 grid-cols-1 content-start gap-3">
        <h2 id="recent-speaking" className="font-display text-2xl font-semibold text-ink">Your recent answers</h2>
        {history === null && <Skeleton className="h-40 w-full" />}
        {history !== null && history.length === 0 && (
          <p className="text-sm text-ink-2">Answers you record appear here with their band.</p>
        )}
        {history !== null && history.length > 0 && (
          <ul className="divide-y divide-rule rounded-xl border border-rule bg-surface">
            {history.slice(0, 6).map((h) => (
              <li key={h.speaking_id}>
                <button
                  onClick={() => onOpen(h.speaking_id)}
                  className="flex w-full cursor-pointer items-center justify-between gap-3 px-4 py-3 text-left hover:bg-surface-2 focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-accent"
                >
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-sm text-ink" title={h.prompt_text ?? undefined}>{h.prompt_text}</span>
                    <span className="font-mono text-xs text-ink-3">
                      Part {h.part_number} · {new Date(h.submitted_at).toLocaleDateString(undefined, { day: "numeric", month: "short" })}
                    </span>
                  </span>
                  {h.status === "completed" && h.overall_band !== null ? (
                    <span className={`font-display text-2xl font-semibold tabular-nums ${bandTone(h.overall_band)}`}>
                      {formatBand(h.overall_band)}
                    </span>
                  ) : (
                    <Badge tone={h.status === "failed" ? "danger" : "neutral"}>{h.status === "failed" ? "Not scored" : "Scoring"}</Badge>
                  )}
                </button>
              </li>
            ))}
          </ul>
        )}
      </aside>
    </div>
  );
}
