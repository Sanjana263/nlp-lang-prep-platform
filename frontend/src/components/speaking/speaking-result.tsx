"use client";

import { useEffect, useState } from "react";
import { ArrowRightIcon, CheckCircleIcon, LightbulbIcon, MicrophoneIcon, WaveformIcon } from "@phosphor-icons/react/ssr";
import { Alert, Badge, BandFigure, BandScale, Button, Eyebrow, PageHeader, Panel, SectionHeading } from "@/components/ui";
import { apiBlob, type SpeakingSubmissionDetail, type SpeakingWord } from "@/lib/api";
import { bandTone, formatBand } from "@/lib/bands";

const CRITERIA = [
  { key: "fluency", label: "Fluency and coherence", asks: "How smoothly you speak and how well you link ideas.", source: "audio" },
  { key: "lexical", label: "Lexical resource", asks: "The range and precision of your vocabulary.", source: "text" },
  { key: "grammar", label: "Grammatical range and accuracy", asks: "The variety and correctness of your sentences.", source: "text" },
  { key: "pronunciation", label: "Pronunciation", asks: "How clearly each sound and word comes across.", source: "audio" },
] as const;

const isWeak = (w: SpeakingWord) => w.phones.some((p) => !p.ok);

export function SpeakingResult({ detail, onAgain }: { detail: SpeakingSubmissionDetail; onAgain: () => void }) {
  const a = detail.analysis_json!;
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [selected, setSelected] = useState<number | null>(null);

  useEffect(() => {
    let url: string | null = null;
    apiBlob(`/speaking/submissions/${detail.speaking_id}/audio`)
      .then((b) => setAudioUrl((url = URL.createObjectURL(b))))
      .catch(() => setAudioUrl(null));
    return () => {
      if (url) URL.revokeObjectURL(url);
    };
  }, [detail.speaking_id]);

  const f = a.fluency;
  const weakCount = a.words.filter(isWeak).length;
  const chosen = selected !== null ? a.words[selected] : null;

  return (
    <div className="grid gap-12">
      <PageHeader
        eyebrow={`Speaking · Part ${detail.part_number} · result`}
        title="Your estimated band"
        description="An automated estimate to guide your practice. It is not an official score."
        actions={
          <Button onClick={onAgain}>
            <MicrophoneIcon aria-hidden size={18} /> Answer another question
          </Button>
        }
      />

      {a.pronunciation.available === false && (
        <Alert tone="info">
          Your answer was transcribed and scored, but the pronunciation check wasn&apos;t available this time
          {a.pronunciation.error ? ` (${a.pronunciation.error})` : ""}. The overall band uses the other three criteria.
        </Alert>
      )}

      <Panel className="grid gap-8 p-6 sm:p-8 lg:grid-cols-[minmax(0,15rem)_minmax(0,1fr)]">
        <div className="grid content-start gap-5">
          <Eyebrow>Overall band</Eyebrow>
          <BandFigure score={a.bands.overall} size="xl" />
          <p className="border-t border-rule pt-4 text-sm text-ink-2">
            <span className="text-ink-3">Question: </span>
            {detail.prompt_text}
          </p>
        </div>
        <ul className="grid min-w-0 gap-6">
          {CRITERIA.map(({ key, label, asks, source }) => {
            const score = a.bands[key];
            return (
            <li key={key} className="grid gap-2">
              <div className="flex items-baseline justify-between gap-4">
                <div className="min-w-0">
                  <p className="flex flex-wrap items-center gap-2 font-semibold text-ink">
                    {label}
                    <span className="font-mono text-[11px] font-normal tracking-wide text-ink-3 uppercase">
                      {source === "audio" ? "from your voice" : a.examiner ? "examiner-checked" : "from your words"}
                    </span>
                  </p>
                  <p className="text-sm text-ink-3">{asks}</p>
                </div>
                <span className={`font-display text-3xl font-semibold tabular-nums ${score === null ? "text-ink-3" : bandTone(score)}`}>
                  {formatBand(score)}
                </span>
              </div>
              {score !== null && <BandScale score={score} size="sm" label={label} />}
            </li>
            );
          })}
        </ul>
      </Panel>

      <section aria-labelledby="transcript" className="grid gap-4">
        <SectionHeading>
          <span id="transcript">What we heard</span>
        </SectionHeading>
        {audioUrl && <audio controls src={audioUrl} className="w-full max-w-xl" />}
        <Panel className="grid gap-4 p-5 sm:p-6">
          <p className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-ink-3">
            <span className="flex items-center gap-1.5">
              <span aria-hidden className="rounded bg-red-soft px-1 font-mono text-xs text-red-pen">um</span> filler sound
            </span>
            {weakCount > 0 && (
              <span className="flex items-center gap-1.5">
                <span aria-hidden className="underline decoration-red-pen decoration-wavy decoration-2 underline-offset-4">word</span>
                unclear sound, select it for details
              </span>
            )}
          </p>
          <p className="font-display text-xl leading-9 text-ink">
            {a.words.map((w, i) => {
              if (w.filler)
                return (
                  <span key={i}>
                    <span className="rounded bg-red-soft px-1 font-mono text-sm text-red-pen">{w.text.replace(/[^\w]/g, "").toLowerCase()}</span>{" "}
                  </span>
                );
              if (isWeak(w))
                return (
                  <span key={i}>
                    <button
                      onClick={() => setSelected(selected === i ? null : i)}
                      aria-expanded={selected === i}
                      aria-controls="word-detail"
                      className="cursor-pointer rounded-sm underline decoration-red-pen decoration-wavy decoration-2 underline-offset-4 hover:bg-red-soft focus-visible:outline-2 focus-visible:outline-accent aria-expanded:bg-red-soft"
                    >
                      {w.text}
                    </button>{" "}
                  </span>
                );
              return <span key={i}>{w.text} </span>;
            })}
          </p>
          <div id="word-detail" aria-live="polite">
            {chosen && (
              <div className="grid gap-2 rounded-lg border border-rule bg-paper px-4 py-3">
                <p className="font-semibold text-ink">
                  “{chosen.text.replace(/[.,!?]/g, "")}”
                  <span className="ml-2 font-mono text-sm font-normal text-ink-3">
                    /{chosen.phones.map((p) => p.expected).join("")}/
                  </span>
                </p>
                <ul className="flex flex-wrap gap-2">
                  {chosen.phones.filter((p) => !p.ok).map((p, k) => (
                    <li key={k} className="text-sm text-ink-2">
                      Expected <span className="font-mono font-semibold text-ink">/{p.expected}/</span>, sounded like{" "}
                      <span className="font-mono font-semibold text-red-pen">/{p.heard}/</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </Panel>
      </section>

      <div className="grid gap-10 lg:grid-cols-[minmax(0,1fr)_minmax(0,18rem)]">
        <div className="grid content-start gap-10">
          <section aria-labelledby="feedback">
            <SectionHeading>
              <span id="feedback">What to work on</span>
            </SectionHeading>
            <ul className="grid gap-3">
              {a.feedback.map((tip) => (
                <li key={tip} className="flex gap-3 rounded-lg border border-rule bg-surface px-4 py-3.5 text-ink">
                  <LightbulbIcon aria-hidden size={20} className="mt-0.5 shrink-0 text-accent" />
                  <span>{tip}</span>
                </li>
              ))}
            </ul>
          </section>

          {a.corrections.length > 0 && (
            <section aria-labelledby="corrections">
              <SectionHeading>
                <span id="corrections">Corrections</span>
              </SectionHeading>
              <ul className="grid gap-3">
                {a.corrections.map((c) => (
                  <li key={c.original} className="grid gap-1 rounded-lg border border-rule bg-surface px-4 py-3.5">
                    <p className="text-ink-2 line-through decoration-red-pen">{c.original}</p>
                    <p className="flex items-start gap-2 font-semibold text-ink">
                      <ArrowRightIcon aria-hidden size={16} weight="bold" className="mt-1 shrink-0 text-success" />
                      {c.corrected}
                    </p>
                    <p className="text-sm text-ink-3">{c.explanation}</p>
                  </li>
                ))}
              </ul>
              {a.vocabulary_suggestions.length > 0 && (
                <p className="mt-4 text-sm text-ink-2">
                  <span className="font-semibold text-ink">Try instead: </span>
                  {a.vocabulary_suggestions.join(" · ")}
                </p>
              )}
            </section>
          )}

          {a.mistake_patterns.length > 0 && (
            <section aria-labelledby="patterns">
              <SectionHeading>
                <span id="patterns">Mistake patterns</span>
              </SectionHeading>
              <ul className="grid gap-2">
                {a.mistake_patterns.map((m, i) => (
                  <li key={i} className="flex flex-wrap items-baseline gap-x-3 gap-y-1 border-b border-rule py-2.5">
                    <Badge tone={m.type === "pronunciation" ? "danger" : "neutral"}>{m.type}</Badge>
                    <span className="font-semibold text-ink">{m.label}</span>
                    {m.examples.length > 0 && <span className="text-sm text-ink-3">{m.examples.join(", ")}</span>}
                  </li>
                ))}
              </ul>
            </section>
          )}
        </div>

        <section aria-labelledby="delivery">
          <SectionHeading>
            <span id="delivery">Delivery</span>
          </SectionHeading>
          <dl className="grid grid-cols-2 gap-x-6 gap-y-4 lg:grid-cols-1">
            <Stat label="Speech rate" value={`${Math.round(f.words_per_minute)} words/min`} hint="Fluent speakers: about 120–150" />
            <Stat label="Words between pauses" value={f.mean_length_of_run.toFixed(1)} hint="Higher is smoother" />
            <Stat label="Pauses per minute" value={f.pauses_per_minute.toFixed(1)} hint={`${f.long_pauses} longer than 1 second`} />
            <Stat label="Filler sounds" value={String(f.filler_count)} hint={`${f.fillers_per_100_words} per 100 words`} />
            <Stat
              label="Sounds said clearly"
              value={a.pronunciation.available === false ? "–" : `${Math.round(a.pronunciation.accuracy * 100)}%`}
              hint={a.pronunciation.available === false ? "Not checked this time" : "Checked sound by sound"}
            />
            <Stat label="Speaking time" value={`${Math.round(f.speaking_seconds)} s`} hint={`${f.word_count} words`} />
          </dl>
          <p className="mt-6 flex items-start gap-2 text-sm text-ink-3">
            {a.examiner ? (
              <CheckCircleIcon aria-hidden size={16} className="mt-0.5 shrink-0 text-success" />
            ) : (
              <WaveformIcon aria-hidden size={16} className="mt-0.5 shrink-0" />
            )}
            {a.examiner
              ? "Vocabulary and grammar were also reviewed by an AI examiner."
              : "Scored from your recording and transcript by our speech models."}
          </p>
        </section>
      </div>
    </div>
  );
}

function Stat({ label, value, hint }: { label: string; value: string; hint: string }) {
  return (
    <div className="border-t border-rule pt-2">
      <dt className="text-sm text-ink-3">{label}</dt>
      <dd className="font-mono text-lg font-semibold text-ink tabular-nums">{value}</dd>
      <dd className="text-xs text-ink-3">{hint}</dd>
    </div>
  );
}
