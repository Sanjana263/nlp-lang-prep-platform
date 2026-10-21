"use client";

import { useCallback, useEffect, useState } from "react";
import { ArrowCounterClockwiseIcon } from "@phosphor-icons/react/ssr";
import { Alert, Button, PageHeader, Panel, Spinner } from "@/components/ui";
import {
  api,
  apiUpload,
  errorMessage,
  type SpeakingPrompt,
  type SpeakingSubmissionDetail,
  type SpeakingSubmissionSummary,
} from "@/lib/api";
import { QuestionPicker } from "./question-picker";
import { RecordStep } from "./record-step";
import { SpeakingResult } from "./speaking-result";

type Stage =
  | { kind: "pick" }
  | { kind: "record"; prompt: SpeakingPrompt }
  | { kind: "scoring"; id: number; attempt: number }
  | { kind: "result"; detail: SpeakingSubmissionDetail };

const POLL_MS = 2000;
const SLOW_AFTER_MS = 200_000; // the backend allows a retry once a recording has been unscored for 3 minutes

/** Appears if scoring is still running after SLOW_AFTER_MS, with a way out. */
function SlowNotice({ onRetry }: { onRetry: () => void }) {
  const [show, setShow] = useState(false);
  useEffect(() => {
    const t = window.setTimeout(() => setShow(true), SLOW_AFTER_MS);
    return () => window.clearTimeout(t);
  }, []);
  if (!show) return null;
  return (
    <div className="grid gap-3 border-t border-rule pt-4">
      <p className="text-ink-2">
        This is taking longer than usual. The server may have restarted or the pronunciation checker may be busy.
        Your recording is saved.
      </p>
      <div>
        <Button variant="secondary" onClick={onRetry}>
          <ArrowCounterClockwiseIcon aria-hidden size={18} /> Score it again
        </Button>
      </div>
    </div>
  );
}

export function SpeakingView() {
  const [stage, setStage] = useState<Stage>({ kind: "pick" });
  const [part, setPart] = useState<1 | 2 | 3>(1);
  const [prompts, setPrompts] = useState<SpeakingPrompt[] | null>(null);
  const [history, setHistory] = useState<SpeakingSubmissionSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const loadHistory = useCallback(() => {
    api<SpeakingSubmissionSummary[]>("/speaking/submissions").then(setHistory).catch(() => setHistory([]));
  }, []);

  useEffect(() => {
    api<SpeakingPrompt[]>("/speaking/prompts").then(setPrompts).catch((e) => setError(errorMessage(e)));
    loadHistory();
  }, [loadHistory]);

  // While scoring, poll the submission until it completes or fails.
  const scoringId = stage.kind === "scoring" ? stage.id : null;
  const attempt = stage.kind === "scoring" ? stage.attempt : 0;
  const [failed, setFailed] = useState<SpeakingSubmissionDetail | null>(null);
  useEffect(() => {
    if (scoringId === null) return;
    let stopped = false;
    const check = async () => {
      try {
        const d = await api<SpeakingSubmissionDetail>(`/speaking/submissions/${scoringId}`);
        if (stopped) return;
        if (d.status === "completed") {
          setStage({ kind: "result", detail: d });
          loadHistory();
          window.scrollTo({ top: 0 });
        } else if (d.status === "failed") setFailed(d);
        else timer = window.setTimeout(check, POLL_MS);
      } catch (e) {
        if (!stopped) setError(errorMessage(e));
      }
    };
    let timer = window.setTimeout(check, POLL_MS);
    return () => {
      stopped = true;
      window.clearTimeout(timer);
    };
  }, [scoringId, attempt, loadHistory]);

  async function submit(prompt: SpeakingPrompt, audio: Blob) {
    setError(null);
    setBusy(true);
    try {
      const form = new FormData();
      form.append("prompt_id", prompt.id);
      const ext = audio.type.includes("mp4") ? "m4a" : audio.type.includes("ogg") ? "ogg" : "webm";
      form.append("audio", new File([audio], `answer.${ext}`, { type: audio.type.split(";")[0] }));
      const sub = await apiUpload<SpeakingSubmissionSummary>("/speaking/submissions", form);
      setFailed(null);
      setStage({ kind: "scoring", id: sub.speaking_id, attempt: 0 });
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusy(false);
    }
  }

  async function open(id: number) {
    setError(null);
    try {
      const d = await api<SpeakingSubmissionDetail>(`/speaking/submissions/${id}`);
      setFailed(null);
      if (d.status === "completed") setStage({ kind: "result", detail: d });
      else if (d.status === "failed") {
        setStage({ kind: "scoring", id, attempt: 0 });
        setFailed(d);
      } else setStage({ kind: "scoring", id, attempt: 0 });
      window.scrollTo({ top: 0 });
    } catch (e) {
      setError(errorMessage(e));
    }
  }

  async function retry(id: number) {
    setError(null);
    try {
      await api(`/speaking/submissions/${id}/retry`, { method: "POST" });
      setFailed(null);
      setStage((s) => ({ kind: "scoring", id, attempt: s.kind === "scoring" ? s.attempt + 1 : 0 }));
    } catch (e) {
      setError(errorMessage(e));
    }
  }

  const backToPick = () => {
    setFailed(null);
    setStage({ kind: "pick" });
    loadHistory();
  };

  if (stage.kind === "result") return <SpeakingResult detail={stage.detail} onAgain={backToPick} />;

  return (
    <div className="grid gap-10">
      <PageHeader
        eyebrow="Speaking"
        title={stage.kind === "pick" ? "Practise speaking" : stage.kind === "record" ? "Record your answer" : "Scoring your answer"}
        description={
          stage.kind === "pick"
            ? "Record an answer to a real IELTS-style question. You get a band for each speaking criterion, your transcript, and the sounds to work on."
            : undefined
        }
      />

      {error && <Alert>{error}</Alert>}

      {stage.kind === "pick" && (
        <QuestionPicker
          prompts={prompts}
          part={part}
          onPart={setPart}
          onPick={(p) => setStage({ kind: "record", prompt: p })}
          history={history}
          onOpen={open}
        />
      )}

      {stage.kind === "record" && (
        <RecordStep
          key={stage.prompt.id}
          prompt={stage.prompt}
          busy={busy}
          onSubmit={(audio) => submit(stage.prompt, audio)}
          onCancel={backToPick}
        />
      )}

      {stage.kind === "scoring" && (
        <Panel className="grid max-w-xl gap-5 p-6 sm:p-8">
          {failed ? (
            <>
              <Alert>{failed.error_message ?? "This recording could not be scored."}</Alert>
              <div className="flex flex-wrap gap-3">
                <Button onClick={() => retry(failed.speaking_id)}>
                  <ArrowCounterClockwiseIcon aria-hidden size={18} /> Score it again
                </Button>
                <Button variant="secondary" onClick={backToPick}>Record a new answer</Button>
              </div>
            </>
          ) : (
            <div role="status" className="grid gap-3">
              <p className="flex items-center gap-3 font-semibold text-ink">
                <Spinner className="text-accent" /> Listening to your answer…
              </p>
              <p className="text-ink-2">
                We transcribe your recording, check each sound, and measure your pace and pauses. This usually takes
                under 30 seconds, but the first answer of the day can take a few minutes while the pronunciation
                checker starts up. You can leave this page; the result will be in your recent answers.
              </p>
              <SlowNotice key={`${stage.id}-${stage.attempt}`} onRetry={() => retry(stage.id)} />
            </div>
          )}
        </Panel>
      )}
    </div>
  );
}
