// Thin wrapper around fetch for the Cadence FastAPI backend.

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const TOKEN_KEY = "cadence_token";

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

// localStorage can throw (private mode, SSR), so every access is guarded.
export const tokenStore = {
  get(): string | null {
    try {
      return typeof window === "undefined" ? null : localStorage.getItem(TOKEN_KEY);
    } catch {
      return null;
    }
  },
  set(token: string) {
    try {
      localStorage.setItem(TOKEN_KEY, token);
    } catch {}
  },
  clear() {
    try {
      localStorage.removeItem(TOKEN_KEY);
    } catch {}
  },
};

export const UNAUTHORIZED_EVENT = "cadence:unauthorized";

type Options = { method?: string; body?: unknown; auth?: boolean };

export async function api<T>(path: string, { method = "GET", body, auth = true }: Options = {}): Promise<T> {
  const headers: Record<string, string> = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  const token = auth ? tokenStore.get() : null;
  if (token) headers["Authorization"] = `Bearer ${token}`;

  let res: Response;
  try {
    res = await fetch(`${BASE}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new ApiError("Cannot reach the server. Check your connection and try again.", 0);
  }

  if (res.status === 401 && auth) {
    // Session expired or token invalid: tell the AuthProvider to log out.
    window.dispatchEvent(new Event(UNAUTHORIZED_EVENT));
  }
  if (!res.ok) {
    throw new ApiError(await readError(res), res.status);
  }
  return (await res.json()) as T;
}

/** Multipart upload (e.g. an audio recording). */
export async function apiUpload<T>(path: string, form: FormData): Promise<T> {
  const headers: Record<string, string> = {};
  const token = tokenStore.get();
  if (token) headers["Authorization"] = `Bearer ${token}`;
  let res: Response;
  try {
    res = await fetch(`${BASE}${path}`, { method: "POST", headers, body: form });
  } catch {
    throw new ApiError("Cannot reach the server. Check your connection and try again.", 0);
  }
  if (res.status === 401) window.dispatchEvent(new Event(UNAUTHORIZED_EVENT));
  if (!res.ok) throw new ApiError(await readError(res), res.status);
  return (await res.json()) as T;
}

/** Authenticated binary download (an <audio> element can't send the auth header itself). */
export async function apiBlob(path: string): Promise<Blob> {
  const token = tokenStore.get();
  const res = await fetch(`${BASE}${path}`, { headers: token ? { Authorization: `Bearer ${token}` } : {} });
  if (!res.ok) throw new ApiError(await readError(res), res.status);
  return res.blob();
}

// FastAPI errors: {detail: "text"} or, for validation, {detail: [{loc, msg}, ...]}
async function readError(res: Response): Promise<string> {
  try {
    const data = await res.json();
    if (typeof data.detail === "string") return data.detail;
    if (Array.isArray(data.detail) && data.detail.length) {
      const first = data.detail[0];
      const field = Array.isArray(first.loc) ? first.loc[first.loc.length - 1] : "";
      return field ? `${field}: ${first.msg}` : first.msg;
    }
  } catch {}
  return `Request failed (${res.status})`;
}

export function errorMessage(e: unknown): string {
  return e instanceof Error ? e.message : "Something went wrong.";
}

// ---- Types mirroring backend/app/**/schemas.py ----
export type TargetExam = "IELTS" | "TOEFL" | "PTE";

export interface User {
  user_id: number;
  full_name: string;
  email: string;
  target_exam: TargetExam;
  role: "student" | "admin";
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface EssayMetrics {
  word_count: number;
  sentence_count: number;
  avg_sentence_length: number;
  avg_parse_depth: number;
  complex_sentence_ratio: number;
  lexical_diversity: number;
}

export interface BandScores {
  task_response: number;
  coherence: number;
  vocabulary: number;
  grammar: number;
  overall: number;
}

export interface WritingIssue {
  type: string; // repeated_word, capitalization, confused_word, punctuation
  line: number;
  text: string;
  message: string;
}

export interface WordSuggestion {
  word: string;
  count: number;
  line: number;
  alternatives: { word: string; meaning: string; example: string }[];
}

export interface EssayResult {
  submission_id: number;
  writing_type: "essay" | "letter" | "report" | "graph_description";
  min_words: number;
  metrics: EssayMetrics;
  bands: BandScores;
  issues: WritingIssue[];
  word_suggestions: WordSuggestion[];
  improved_text: string;
  changes: string[];
  feedback: string[];
}

export interface WritingPrompt {
  prompt_id: number;
  writing_type: "essay" | "letter" | "report" | "graph_description";
  topic: string;
  question_type: string;
  prompt_text: string;
}

export interface WritingSubmissionSummary {
  writing_id: number;
  task_type: string;
  word_count: number;
  task_response_score: number | null;
  grammar_score: number | null;
  coherence_score: number | null;
  vocabulary_score: number | null;
  status: "pending" | "completed" | "failed";
  submitted_at: string;
}

export interface SpeakingPrompt {
  id: string;
  part: 1 | 2 | 3;
  topic: string;
  question: string;
  points: string[];
  speak_seconds: number;
}

export interface SpeakingBands {
  fluency: number;
  lexical: number;
  grammar: number;
  pronunciation: number | null; // null when the pronunciation checker was unavailable
  overall: number;
}

export interface SpeakingWord {
  text: string;
  start: number;
  end: number;
  filler: boolean;
  accuracy: number | null;
  phones: { expected: string; heard: string; ok: boolean }[];
}

export interface MistakePattern {
  type: "pronunciation" | "fluency" | "grammar";
  label: string;
  count: number;
  examples: string[];
}

export interface SpeakingAnalysis {
  transcript: string;
  bands: SpeakingBands;
  fluency: {
    speaking_seconds: number;
    word_count: number;
    words_per_minute: number;
    articulation_rate: number;
    mean_length_of_run: number;
    pauses_per_minute: number;
    long_pauses: number;
    filler_count: number;
    fillers_per_100_words: number;
    repetitions: number;
  };
  text: { mattr: number; rare_word_ratio: number; rare_words: string[]; complex_sentence_ratio: number; discourse_markers: string[] };
  pronunciation: { accuracy: number; substitutions: Record<string, string[]>; available?: boolean; error?: string | null };
  words: SpeakingWord[];
  feedback: string[];
  corrections: { original: string; corrected: string; explanation: string }[];
  vocabulary_suggestions: string[];
  mistake_patterns: MistakePattern[];
  examiner: boolean;
}

export interface SpeakingSubmissionSummary {
  speaking_id: number;
  part_number: number;
  prompt_id: string | null;
  prompt_text: string | null;
  duration_seconds: number | null;
  fluency_score: number | null;
  lexical_score: number | null;
  grammar_score: number | null;
  pronunciation_score: number | null;
  overall_band: number | null;
  pace_score: number | null;
  filler_word_count: number | null;
  status: "pending" | "processing" | "completed" | "failed";
  error_message: string | null;
  submitted_at: string;
}

export interface SpeakingSubmissionDetail extends SpeakingSubmissionSummary {
  transcribed_text: string | null;
  mistake_patterns_json: MistakePattern[] | null;
  analysis_json: SpeakingAnalysis | null;
}
