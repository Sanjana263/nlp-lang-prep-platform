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

export interface EssayResult {
  submission_id: number;
  metrics: EssayMetrics;
  bands: BandScores;
  feedback: string[];
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
