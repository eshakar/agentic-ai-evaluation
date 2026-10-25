// Typed client for the FastAPI backend. Types mirror backend/app/schemas/evaluation.py.

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type ToolCall = {
  name: string;
  arguments: Record<string, unknown>;
  output: string | null;
};

export type AgentTrace = {
  output: string;
  tool_calls: ToolCall[];
  turns: number;
  latency_ms: number;
  input_tokens: number;
  output_tokens: number;
  error: string | null;
};

export type MetricResult = {
  name: string;
  score: number;
  passed: boolean;
  reason: string;
};

export type CaseResult = {
  case_id: string;
  trace: AgentTrace;
  metrics: MetricResult[];
};

export type RunSummary = {
  run_id: string;
  created_at: string;
  agent: string;
  evaluators: string[];
  num_cases: number;
  /** Cases at least one evaluator applied to; pass_rate is over these. */
  num_scored: number;
  pass_rate: number;
  mean_scores: Record<string, number>;
  mean_latency_ms: number;
  results: CaseResult[];
};

export type RunListItem = Pick<
  RunSummary,
  "run_id" | "created_at" | "agent" | "num_cases" | "pass_rate"
>;

export type Catalog = {
  agents: string[];
  tools: string[];
  evaluators: string[];
  datasets: string[];
};

export type EvalCase = {
  id: string;
  input: string;
  expected_output?: string | null;
  expected_tools?: string[] | null;
  rubric?: string | null;
  metadata?: Record<string, unknown>;
};

export type AskRequest = {
  agent: string;
  question: string;
  expected_output?: string;
  /** null/undefined = don't check tools; [] = the agent should use no tools. */
  expected_tools?: string[] | null;
  rubric?: string;
  use_judge?: boolean;
};

export type AskResponse = {
  agent: string;
  question: string;
  trace: AgentTrace;
  metrics: MetricResult[];
};

export type SaveCaseRequest = {
  dataset: string;
  question: string;
  expected_output?: string;
  expected_tools?: string[] | null;
  rubric?: string;
  category?: string;
};

export type SaveCaseResponse = {
  dataset: string;
  case: EvalCase;
  total_cases: number;
};

export type RunRequest = {
  agent: string;
  dataset: string;
  evaluators: string[];
};

/** FastAPI sends a string detail for our own errors and a list for validation errors. */
function errorDetail(body: unknown, fallback: string): string {
  const detail = (body as { detail?: unknown } | null)?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((d: { loc?: unknown[]; msg?: string }) => {
        const field = d.loc?.filter((x) => x !== "body").join(".");
        return field ? `${field}: ${d.msg}` : d.msg;
      })
      .join("; ");
  }
  return fallback;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...init?.headers },
    });
  } catch {
    throw new Error(`Cannot reach the backend at ${API_URL}. Is it running?`);
  }
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(`${res.status}: ${errorDetail(body, res.statusText)}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

const post = <T,>(path: string, body: unknown) =>
  request<T>(path, { method: "POST", body: JSON.stringify(body) });

export const api = {
  /** storage: "mongodb (<db>)", "files", or "files (MongoDB unreachable: ...)". */
  health: () => request<{ status: string; storage?: string }>("/health"),
  catalog: () => request<Catalog>("/api/v1/evaluations/catalog"),
  runs: (limit = 100) => request<RunListItem[]>(`/api/v1/evaluations/runs?limit=${limit}`),
  getRun: (runId: string) =>
    request<RunSummary>(`/api/v1/evaluations/${encodeURIComponent(runId)}`),
  deleteRun: (runId: string) =>
    request<void>(`/api/v1/evaluations/${encodeURIComponent(runId)}`, { method: "DELETE" }),
  ask: (body: AskRequest) => post<AskResponse>("/api/v1/agents/ask", body),
  saveCase: (body: SaveCaseRequest) => post<SaveCaseResponse>("/api/v1/datasets/cases", body),
  run: (body: RunRequest) => post<RunSummary>("/api/v1/evaluations/run", body),
};

/** Matches the backend: a case no evaluator applied to is "not scored", never a pass. */
export const isCaseScored = (r: CaseResult) => r.metrics.length > 0;
export const isCasePassed = (r: CaseResult) => isCaseScored(r) && r.metrics.every((m) => m.passed);

export const formatMs = (v: number) =>
  v >= 1000 ? `${(v / 1000).toFixed(1)}s` : `${Math.round(v)}ms`;
