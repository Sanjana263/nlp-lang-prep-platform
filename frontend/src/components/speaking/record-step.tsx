"use client";

import { useEffect, useState } from "react";
import { ArrowCounterClockwiseIcon, MicrophoneIcon, StopIcon } from "@phosphor-icons/react/ssr";
import { Alert, Button, Eyebrow, Panel } from "@/components/ui";
import type { SpeakingPrompt } from "@/lib/api";
import { useRecorder } from "./use-recorder";

const PREP_SECONDS = 60; // IELTS Part 2: one minute to prepare
const clock = (s: number) => `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;

export function RecordStep({
  prompt,
  busy,
  onSubmit,
  onCancel,
}: {
  prompt: SpeakingPrompt;
  busy: boolean;
  onSubmit: (audio: Blob) => void;
  onCancel: () => void;
}) {
  const maxSeconds = Math.min(180, prompt.speak_seconds + 30);
  const rec = useRecorder(maxSeconds);
  const [prep, setPrep] = useState(prompt.part === 2 ? PREP_SECONDS : 0);

  useEffect(() => {
    if (prep <= 0) return;
    const t = window.setTimeout(() => setPrep((p) => p - 1), 1000);
    return () => window.clearTimeout(t);
  }, [prep]);

  const preparing = prep > 0 && rec.state === "idle";
  const progress = Math.min(1, rec.elapsed / prompt.speak_seconds);

  return (
    <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_minmax(0,24rem)] lg:items-start">
      <Panel as="section" className="grid gap-4 p-6 sm:p-8">
        <Eyebrow>
          Part {prompt.part} · {prompt.topic}
        </Eyebrow>
        <p className="font-display text-2xl leading-snug text-ink sm:text-3xl">{prompt.question}</p>
        {prompt.points.length > 0 && (
          <div className="border-t border-rule pt-4">
            <p className="text-sm text-ink-3">You should say:</p>
            <ul className="mt-2 grid gap-1.5 text-ink">
              {prompt.points.map((p) => (
                <li key={p} className="flex gap-2.5">
                  <span aria-hidden className="mt-2.5 size-1.5 shrink-0 rounded-full bg-ink-3" />
                  {p}
                </li>
              ))}
            </ul>
          </div>
        )}
        <p className="border-t border-rule pt-4 text-sm text-ink-2">
          Speak for about {prompt.speak_seconds >= 60 ? `${Math.round(prompt.speak_seconds / 60)} minute${prompt.speak_seconds >= 120 ? "s" : ""}` : `${prompt.speak_seconds} seconds`}.
          Recording stops automatically at {clock(maxSeconds)}.
        </p>
      </Panel>

      <section aria-label="Recorder" className="grid gap-5 rounded-xl border border-rule bg-surface p-6 sm:p-8">
        {preparing && (
          <div className="grid gap-3 text-center">
            <Eyebrow>Preparation time</Eyebrow>
            <p className="font-mono text-5xl font-semibold text-ink tabular-nums" aria-live="off">{clock(prep)}</p>
            <p className="text-sm text-ink-2">Make notes on the points. Recording starts when you are ready.</p>
          </div>
        )}

        {(rec.state === "idle" || rec.state === "requesting" || rec.state === "error") && (
          <div className="grid justify-items-center gap-4 text-center">
            <button
              onClick={rec.start}
              disabled={rec.state === "requesting"}
              aria-label="Start recording"
              className="grid size-20 cursor-pointer place-items-center rounded-full bg-accent text-on-accent transition-colors duration-150 hover:bg-accent-hover focus-visible:outline-3 focus-visible:outline-offset-4 focus-visible:outline-accent disabled:cursor-wait disabled:opacity-60"
            >
              <MicrophoneIcon aria-hidden size={34} weight="fill" />
            </button>
            <p className="font-semibold text-ink">
              {rec.state === "requesting" ? "Waiting for microphone permission…" : preparing ? "Start speaking now" : "Start recording"}
            </p>
            {rec.error && <Alert>{rec.error}</Alert>}
          </div>
        )}

        {rec.state === "recording" && (
          <div className="grid gap-5">
            <div className="flex items-baseline justify-between">
              <span className="flex items-center gap-2 font-semibold text-red-pen">
                <span aria-hidden className="size-2.5 animate-pulse rounded-full bg-red-pen" /> Recording
              </span>
              <span className="font-mono text-2xl font-semibold text-ink tabular-nums">{clock(rec.elapsed)}</span>
            </div>
            <div aria-hidden className="grid gap-1.5">
              <span className="text-xs text-ink-3">Microphone level</span>
              <div className="h-2 overflow-hidden rounded-full bg-surface-2">
                <div className="h-full origin-left rounded-full bg-success transition-transform duration-75" style={{ transform: `scaleX(${rec.level})` }} />
              </div>
            </div>
            <div className="grid gap-1.5">
              <span className="text-xs text-ink-3">Suggested length {clock(prompt.speak_seconds)}</span>
              <div className="h-1.5 overflow-hidden rounded-full bg-surface-2">
                <div className={`h-full rounded-full transition-[width] duration-300 ${progress >= 1 ? "bg-success" : "bg-accent"}`} style={{ width: `${progress * 100}%` }} />
              </div>
            </div>
            <Button variant="secondary" onClick={rec.stop}>
              <StopIcon aria-hidden size={18} weight="fill" className="text-red-pen" /> Stop recording
            </Button>
          </div>
        )}

        {rec.state === "recorded" && rec.url && rec.blob && (
          <div className="grid gap-4">
            <p className="font-semibold text-ink">Listen back, then submit your answer</p>
            <audio controls src={rec.url} className="w-full" />
            <p className="font-mono text-sm text-ink-3">Length {clock(rec.elapsed)}</p>
            <div className="flex flex-wrap gap-3">
              <Button onClick={() => onSubmit(rec.blob!)} loading={busy}>
                {busy ? "Uploading…" : "Submit for scoring"}
              </Button>
              <Button variant="secondary" onClick={rec.reset} disabled={busy}>
                <ArrowCounterClockwiseIcon aria-hidden size={18} /> Record again
              </Button>
            </div>
          </div>
        )}

        <button
          onClick={onCancel}
          disabled={busy || rec.state === "recording"}
          className="justify-self-start rounded-sm text-sm font-semibold text-ink-2 underline-offset-4 hover:text-ink hover:underline focus-visible:outline-2 focus-visible:outline-accent disabled:opacity-45"
        >
          Choose a different question
        </button>
      </section>
    </div>
  );
}
