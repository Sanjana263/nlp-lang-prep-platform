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

export type BandTier = "strong" | "good" | "fair" | "weak";

export function bandTier(score: number): BandTier {
  if (score >= 7) return "strong";
  if (score >= 6) return "good";
  if (score >= 5) return "fair";
  return "weak";
}

/** Text colour class for a band score (tokens from globals.css). */
export function bandTone(score: number): string {
  return {
    strong: "text-band-strong",
    good: "text-band-good",
    fair: "text-band-fair",
    weak: "text-band-weak",
  }[bandTier(score)];
}

/** Fill colour class for bars and markers. */
export function bandFill(score: number): string {
  return {
    strong: "bg-band-strong",
    good: "bg-band-good",
    fair: "bg-band-fair",
    weak: "bg-band-weak",
  }[bandTier(score)];
}

/** Official IELTS band descriptor names, so a number always comes with words. */
const DESCRIPTORS = [
  "Did not attempt",
  "Non-user",
  "Intermittent user",
  "Extremely limited user",
  "Limited user",
  "Modest user",
  "Competent user",
  "Good user",
  "Very good user",
  "Expert user",
];

export function bandDescriptor(score: number): string {
  return DESCRIPTORS[Math.max(0, Math.min(9, Math.floor(score)))];
}
