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
  evaluators: string[];
  datasets: string[];
};

export type RunRequest = {
  agent: string;
  dataset: string;
  evaluators: string[];
};

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
    const detail = typeof body?.detail === "string" ? body.detail : res.statusText;
    throw new Error(`${res.status}: ${detail}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  catalog: () => request<Catalog>("/api/v1/evaluations/catalog"),
  runs: () => request<RunListItem[]>("/api/v1/evaluations/runs"),
  getRun: (runId: string) => request<RunSummary>(`/api/v1/evaluations/${runId}`),
  run: (body: RunRequest) =>
    request<RunSummary>("/api/v1/evaluations/run", {
      method: "POST",
      body: JSON.stringify(body),
    }),
};

/** Matches the backend: a case no evaluator applied to is "not scored", never a pass. */
export const isCaseScored = (r: CaseResult) => r.metrics.length > 0;
export const isCasePassed = (r: CaseResult) => isCaseScored(r) && r.metrics.every((m) => m.passed);
