"use client";

import { useState } from "react";
import { Button, Card, ErrorAlert, Spinner } from "@/components/ui";
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
const countWords = (t: string) => (t.trim() ? t.trim().split(/\s+/).length : 0);

const CRITERIA: { key: "task_response" | "coherence" | "vocabulary" | "grammar"; label: string }[] = [
  { key: "task_response", label: "Task response" },
  { key: "coherence", label: "Coherence & cohesion" },
  { key: "vocabulary", label: "Lexical resource" },
  { key: "grammar", label: "Grammatical range" },
];

export function WritingView() {
  const [promptIndex, setPromptIndex] = useState(0);
  const [essay, setEssay] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<EssayResult | null>(null);

  const words = countWords(essay);
  const canSubmit = essay.trim().length >= MIN_CHARS && !busy;

  async function submit() {
    setError(null);
    setBusy(true);
    try {
      const res = await api<EssayResult>("/writing/evaluate", {
        method: "POST",
        body: { essay, task_type: "task2", prompt_text: PROMPTS[promptIndex] },
      });
      setResult(res);
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

  if (result) return <ResultView result={result} onAgain={reset} />;

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Writing test · Task 2</h1>
        <p className="mt-1 text-sm text-zinc-500">Aim for at least 250 words. You will get an estimated band and feedback.</p>
      </header>

      <Card>
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">Prompt</p>
            <p className="mt-2 leading-7">“{PROMPTS[promptIndex]}”</p>
          </div>
          <button
            type="button"
            disabled={busy}
            onClick={() => setPromptIndex((i) => (i + 1) % PROMPTS.length)}
            className="shrink-0 text-sm text-indigo-600 hover:underline disabled:opacity-50 dark:text-indigo-400"
          >
            Different prompt
          </button>
        </div>
      </Card>

      <div>
        <label htmlFor="essay" className="sr-only">
          Your essay
        </label>
        <textarea
          id="essay"
          value={essay}
          onChange={(e) => setEssay(e.target.value)}
          disabled={busy}
          rows={16}
          placeholder="Type your response here..."
          className="w-full resize-y rounded-2xl border border-zinc-300 bg-white p-4 leading-7 placeholder:text-zinc-400 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/30 dark:border-zinc-700 dark:bg-zinc-900"
        />
        <div className="mt-3 flex items-center justify-between gap-4">
          <p className={`text-sm ${words >= 250 ? "text-emerald-600 dark:text-emerald-400" : "text-zinc-500"}`}>
            Word count: {words}
          </p>
          <Button onClick={submit} disabled={!canSubmit} className="gap-2">
            {busy && <Spinner />} {busy ? "Evaluating…" : "Submit"}
          </Button>
        </div>
        {!busy && essay.length > 0 && essay.trim().length < MIN_CHARS && (
          <p className="mt-2 text-xs text-zinc-500">Write a little more to enable submission.</p>
        )}
      </div>

      {error && <ErrorAlert>{error}</ErrorAlert>}
    </div>
  );
}

function ResultView({ result, onAgain }: { result: EssayResult; onAgain: () => void }) {
  const { bands, feedback, metrics } = result;
  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Your result</h1>
          <p className="mt-1 text-sm text-zinc-500">
            An automated estimate for practice. It is not an official score.
          </p>
        </div>
        <Button onClick={onAgain}>Write another essay</Button>
      </header>

      <div className="grid gap-4 md:grid-cols-[220px_1fr]">
        <Card className="flex flex-col items-center justify-center text-center">
          <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">Overall band</p>
          <p className={`mt-2 text-6xl font-semibold ${bandTone(bands.overall)}`}>{formatBand(bands.overall)}</p>
        </Card>
        <Card className="space-y-4">
          {CRITERIA.map(({ key, label }) => (
            <div key={key}>
              <div className="mb-1.5 flex justify-between text-sm">
                <span>{label}</span>
                <span className={`font-semibold ${bandTone(bands[key])}`}>{formatBand(bands[key])}</span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-zinc-100 dark:bg-zinc-800">
                <div className="h-full rounded-full bg-indigo-500" style={{ width: `${(bands[key] / 9) * 100}%` }} />
              </div>
            </div>
          ))}
        </Card>
      </div>

      <Card>
        <h2 className="font-semibold">Feedback</h2>
        <ul className="mt-3 list-disc space-y-2 pl-5 text-sm leading-6">
          {feedback.map((tip) => (
            <li key={tip}>{tip}</li>
          ))}
        </ul>
      </Card>

      <Card>
        <h2 className="font-semibold">Essay statistics</h2>
        <dl className="mt-3 grid grid-cols-2 gap-4 text-sm sm:grid-cols-4">
          <Stat label="Words" value={metrics.word_count} />
          <Stat label="Sentences" value={metrics.sentence_count} />
          <Stat label="Avg. sentence length" value={metrics.avg_sentence_length} />
          <Stat label="Complex sentences" value={`${Math.round(metrics.complex_sentence_ratio * 100)}%`} />
        </dl>
      </Card>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div>
      <dt className="text-xs text-zinc-500">{label}</dt>
      <dd className="mt-0.5 text-lg font-semibold">{value}</dd>
    </div>
  );
}
