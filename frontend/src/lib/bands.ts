/** IELTS-style rounding to the nearest 0.5 (mirrors backend round_band). */
export function roundBand(score: number): number {
  return Math.max(0, Math.min(9, Math.floor(score * 2 + 0.5) / 2));
}

export function formatBand(score: number | null | undefined): string {
  return score === null || score === undefined ? "–" : score.toFixed(1);
}

/** Average of the four writing criteria for a saved submission (null until scored). */
export function writingOverall(s: {
  task_response_score: number | null;
  grammar_score: number | null;
  coherence_score: number | null;
  vocabulary_score: number | null;
}): number | null {
  const parts = [s.task_response_score, s.grammar_score, s.coherence_score, s.vocabulary_score];
  if (parts.some((p) => p === null)) return null;
  return roundBand((parts as number[]).reduce((a, b) => a + b, 0) / 4);
}

export function bandTone(score: number): string {
  if (score >= 7) return "text-emerald-600 dark:text-emerald-400";
  if (score >= 6) return "text-indigo-600 dark:text-indigo-400";
  if (score >= 5) return "text-amber-600 dark:text-amber-400";
  return "text-rose-600 dark:text-rose-400";
}
