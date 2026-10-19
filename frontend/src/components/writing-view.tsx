"use client";

import { useState } from "react";
import {
  ArrowsClockwiseIcon,
  CheckCircleIcon,
  ClockIcon,
  LightbulbIcon,
  PencilLineIcon,
  TextAaIcon,
} from "@phosphor-icons/react/ssr";
import { Alert, BandFigure, BandScale, Button, Eyebrow, PageHeader, Panel, SectionHeading } from "@/components/ui";
import { api, errorMessage, type EssayResult } from "@/lib/api";
import { bandTone, formatBand } from "@/lib/bands";

// Static for now: the SRS has no writing-prompt table yet.
const PROMPTS = [
  "Some people believe that university education should be free for all students. Discuss both views and give your opinion.",
  "Some people think children should start learning a foreign language at primary school. To what extent do you agree or disagree?",
  "Many cities now have more cars than ever. What problems does this cause, and what measures could be taken to solve them?",
  "Some people say that technology has made our lives more complicated. Do the advantages of technology outweigh the disadvantages?",
];

const MIN_CHARS = 50; // backend rule (EssayRequest.min_length)
const TARGET_WORDS = 250; // IELTS Task 2 minimum
const countWords = (t: string) => (t.trim() ? t.trim().split(/\s+/).length : 0);

const CRITERIA: { key: "task_response" | "coherence" | "vocabulary" | "grammar"; label: string; asks: string }[] = [
  { key: "task_response", label: "Task response", asks: "How fully you answer every part of the question." },
  { key: "coherence", label: "Coherence and cohesion", asks: "How logically your ideas are organised and linked." },
  { key: "vocabulary", label: "Lexical resource", asks: "The range and accuracy of your vocabulary." },
  { key: "grammar", label: "Grammatical range and accuracy", asks: "The variety and correctness of your sentences." },
];

export function WritingView() {
  const [promptIndex, setPromptIndex] = useState(0);
  const [essay, setEssay] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<EssayResult | null>(null);

  const words = countWords(essay);
  const tooShort = essay.trim().length < MIN_CHARS;
  const progress = Math.min(1, words / TARGET_WORDS);

  async function submit() {
    setError(null);
    setBusy(true);
    try {
      const res = await api<EssayResult>("/writing/evaluate", {
        method: "POST",
        body: { essay, task_type: "task2", prompt_text: PROMPTS[promptIndex] },
      });
      setResult(res);
      window.scrollTo({ top: 0 });
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusy(false);
    }
  }

  function reset() {
    setResult(null);
    setEssay("");
    setError(null);
  }

  if (result) return <ResultView result={result} prompt={PROMPTS[promptIndex]} onAgain={reset} />;

  return (
    <div className="grid gap-10">
      <PageHeader
        eyebrow="Writing · Task 2"
        title="Write your essay"
        description="Answer the question below as you would in the exam. You will get an estimated band for each criterion."
      />

      <div className="grid gap-8 lg:grid-cols-[minmax(0,20rem)_minmax(0,1fr)] lg:items-start">
        <aside className="grid gap-5 lg:sticky lg:top-8">
          <div>
            <Eyebrow>
              Question {promptIndex + 1} of {PROMPTS.length}
            </Eyebrow>
            <p className="mt-3 font-display text-xl leading-8 text-ink">{PROMPTS[promptIndex]}</p>
          </div>
          <ul className="grid gap-2 border-y border-rule py-4 text-sm text-ink-2">
            <li className="flex items-center gap-2.5">
              <ClockIcon aria-hidden size={18} className="text-ink-3" /> Spend about 40 minutes on this task.
            </li>
            <li className="flex items-center gap-2.5">
              <TextAaIcon aria-hidden size={18} className="text-ink-3" /> Write at least {TARGET_WORDS} words.
            </li>
          </ul>
          <Button
            variant="secondary"
            size="sm"
            disabled={busy}
            onClick={() => setPromptIndex((i) => (i + 1) % PROMPTS.length)}
            className="justify-self-start"
          >
            <ArrowsClockwiseIcon aria-hidden size={16} /> Try a different question
          </Button>
        </aside>

        <div className="grid min-w-0 gap-4">
          <Panel className="overflow-hidden focus-within:border-accent focus-within:ring-3 focus-within:ring-accent/25">
            <div className="flex items-center justify-between gap-4 border-b border-rule px-5 py-2.5">
              <label htmlFor="essay" className="font-mono text-xs font-medium tracking-[0.12em] text-ink-3 uppercase">
                Answer sheet
              </label>
              <span className="font-mono text-xs text-ink-3 tabular-nums" aria-hidden>
                {words} / {TARGET_WORDS} words
              </span>
            </div>
            <textarea
              id="essay"
              value={essay}
              onChange={(e) => setEssay(e.target.value)}
              readOnly={busy}
              rows={16}
              placeholder="Start writing here…"
              aria-describedby="essay-count"
              spellCheck={false}
              className="ruled block min-h-[32rem] w-full resize-y bg-surface px-5 py-8 text-[17px] text-ink placeholder:text-ink-3 focus:outline-none"
            />
          </Panel>

          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="grid min-w-48 flex-1 gap-1.5">
              <div className="h-1.5 max-w-xs overflow-hidden rounded-full bg-surface-2">
                <div
                  className={`h-full rounded-full transition-[width] duration-300 ${progress >= 1 ? "bg-success" : "bg-accent"}`}
                  style={{ width: `${progress * 100}%` }}
                />
              </div>
              <p id="essay-count" aria-live="polite" className="flex items-center gap-1.5 text-sm text-ink-2">
                {words >= TARGET_WORDS ? (
                  <>
                    <CheckCircleIcon aria-hidden size={16} weight="fill" className="text-success" />
                    {words} words. You have reached the minimum.
                  </>
                ) : (
                  <>{words} words, {TARGET_WORDS - words} to go.</>
                )}
              </p>
            </div>
            <Button onClick={submit} disabled={tooShort} loading={busy}>
              {busy ? "Scoring your essay…" : "Submit for scoring"}
            </Button>
          </div>
          {!busy && essay.length > 0 && tooShort && (
            <p className="text-sm text-ink-3">Write a few more sentences to enable scoring.</p>
          )}
          {error && <Alert>{error}</Alert>}
        </div>
      </div>
    </div>
  );
}

function ResultView({ result, prompt, onAgain }: { result: EssayResult; prompt: string; onAgain: () => void }) {
  const { bands, feedback, metrics } = result;
  return (
    <div className="grid gap-12">
      <PageHeader
        eyebrow="Writing · Task 2 · result"
        title="Your estimated band"
        description="An automated estimate to guide your practice. It is not an official score."
        actions={
          <Button onClick={onAgain}>
            <PencilLineIcon aria-hidden size={18} /> Write another essay
          </Button>
        }
      />

      <Panel className="grid gap-8 p-6 sm:p-8 lg:grid-cols-[minmax(0,15rem)_minmax(0,1fr)]">
        <div className="grid content-start gap-5">
          <Eyebrow>Overall band</Eyebrow>
          <BandFigure score={bands.overall} size="xl" />
          <p className="border-t border-rule pt-4 text-sm text-ink-2">
            <span className="text-ink-3">Question: </span>
            {prompt}
          </p>
        </div>
        <ul className="grid min-w-0 gap-6">
          {CRITERIA.map(({ key, label, asks }) => (
            <li key={key} className="grid gap-2">
              <div className="flex items-baseline justify-between gap-4">
                <div className="min-w-0">
                  <p className="font-semibold text-ink">{label}</p>
                  <p className="text-sm text-ink-3">{asks}</p>
                </div>
                <span className={`font-display text-3xl font-semibold tabular-nums ${bandTone(bands[key])}`}>
                  {formatBand(bands[key])}
                </span>
              </div>
              <BandScale score={bands[key]} size="sm" label={label} />
            </li>
          ))}
        </ul>
      </Panel>

      <div className="grid gap-10 lg:grid-cols-[minmax(0,1fr)_minmax(0,18rem)]">
        <section aria-labelledby="feedback">
          <SectionHeading>
            <span id="feedback">What to work on</span>
          </SectionHeading>
          <ul className="grid gap-3">
            {feedback.map((tip) => (
              <li key={tip} className="flex gap-3 rounded-lg border border-rule bg-surface px-4 py-3.5 text-ink">
                <LightbulbIcon aria-hidden size={20} className="mt-0.5 shrink-0 text-accent" />
                <span>{tip}</span>
              </li>
            ))}
          </ul>
        </section>

        <section aria-labelledby="stats">
          <SectionHeading>
            <span id="stats">Essay statistics</span>
          </SectionHeading>
          <dl className="grid grid-cols-2 gap-x-6 gap-y-4 lg:grid-cols-1">
            <Stat label="Words" value={metrics.word_count} />
            <Stat label="Sentences" value={metrics.sentence_count} />
            <Stat label="Average sentence length" value={`${metrics.avg_sentence_length} words`} />
            <Stat label="Complex sentences" value={`${Math.round(metrics.complex_sentence_ratio * 100)}%`} />
            <Stat label="Different words used" value={`${Math.round(metrics.lexical_diversity * 100)}%`} />
          </dl>
        </section>
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="border-t border-rule pt-2">
      <dt className="text-sm text-ink-3">{label}</dt>
      <dd className="font-mono text-lg font-semibold text-ink tabular-nums">{value}</dd>
    </div>
  );
}
