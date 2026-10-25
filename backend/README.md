# Backend: FastAPI evaluation service

A FastAPI service for **evaluating agentic AI systems**: run an agent over a dataset of tasks, capture its full trajectory (final answer, tool calls, turns, tokens, latency), and score it with deterministic metrics and an LLM-as-judge.

## Features

- **Agents under test**: pluggable `BaseAgent` interface. Ships with an offline `echo` baseline and two tool-using agents with the same tools, `claude` (Anthropic) and `gemini` (Google), each driven by a manual loop so every tool call is recorded and the two can be compared on the same dataset.
- **Evaluators**:
  | Name | What it measures |
  |---|---|
  | `exact_match` | Normalized final answer equals the expected output |
  | `contains` | Expected answer appears in the final output |
  | `tool_sequence` | Trajectory: expected tools were called in order (score is F1 over tool names) |
  | `latency` | Run finished within budget (`metadata.max_latency_ms`, default 30s) |
  | `no_error` | No crash, refusal, or turn-limit hit |
  | `llm_judge` | Claude grades the answer and trajectory against a rubric (1–5, normalized) |
- **Two ways to evaluate**: `POST /run` executes an agent; `POST /score` grades traces you recorded elsewhere (LangGraph, CrewAI, your own agent, and so on).
- Run reports are saved as JSON in `results/`.

## Project structure

```
backend/
├── app/
│   ├── main.py                    # FastAPI app factory
│   ├── core/                      # settings (.env) and logging
│   ├── api/routes/                # /health, /api/v1/evaluations/*
│   ├── schemas/evaluation.py      # EvalCase, AgentTrace, MetricResult, RunSummary
│   ├── agents/                    # agents under test + their tools
│   ├── evaluators/                # metrics + LLM judge + registry
│   └── services/                  # Anthropic client, evaluation orchestration
├── datasets/                      # JSONL eval sets (one EvalCase per line)
├── scripts/run_eval.py            # CLI runner (no server needed)
├── results/                       # run reports (git-ignored)
├── notebooks/                     # analysis / exploration
├── tests/                         # pytest suite (no API key required)
├── Dockerfile
├── pyproject.toml, requirements*.txt
└── .env.example
```

## Getting started

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux

# 2. Install dependencies
pip install -r requirements-dev.txt

# 3. Configure secrets
copy .env.example .env          # Windows  (cp on macOS / Linux)
# then set ANTHROPIC_API_KEY in .env

# 4. Run the API
uvicorn app.main:app --reload
```

Open the interactive docs at http://localhost:8000/docs.

## Usage

**Run an agent over a dataset**

```bash
curl -X POST http://localhost:8000/api/v1/evaluations/run \
  -H "Content-Type: application/json" \
  -d '{"agent": "claude", "dataset": "sample_eval.jsonl",
       "evaluators": ["contains", "tool_sequence", "no_error", "llm_judge"]}'
```

**Score traces from an external agent**

```bash
curl -X POST http://localhost:8000/api/v1/evaluations/score \
  -H "Content-Type: application/json" \
  -d '{"items": [{"case": {"id": "x", "input": "2+2?", "expected_output": "4", "expected_tools": ["calculator"]},
                  "trace": {"output": "4", "tool_calls": [{"name": "calculator"}]}}],
       "evaluators": ["exact_match", "tool_sequence"]}'
```

**Other endpoints**: `GET /health`, `GET /api/v1/evaluations/catalog`, `GET /api/v1/evaluations/{run_id}`.

**From the command line**

```bash
python -m scripts.run_eval --agent echo
python -m scripts.run_eval --agent claude --evaluators contains tool_sequence llm_judge
```

## Dataset format

`datasets/*.jsonl`, one case per line:

```json
{"id": "math-001", "input": "What is (17 * 23) + 4?", "expected_output": "395",
 "expected_tools": ["calculator"], "rubric": "optional judge criteria", "metadata": {"max_latency_ms": 20000}}
```

All fields except `id` and `input` are optional; an evaluator skips a case when its required field is missing.

## Extending

- **New agent**: subclass `BaseAgent` in `app/agents/`, implement `async run(task) -> AgentTrace`, and register it in `app/agents/registry.py`.
- **New tool for the Claude agent**: add a schema to `TOOLS` and a function to `HANDLERS` in `app/agents/tools.py`.
- **New metric**: subclass `BaseEvaluator` in `app/evaluators/`, and register it in `app/evaluators/registry.py`.

## Development

```bash
pytest -q          # tests (no API key needed)
ruff check .       # lint
ruff format .      # format
pre-commit install # run lint on every commit
```

## Docker

```bash
docker build -t agentic-eval-backend . && docker run -p 8000:8000 --env-file .env agentic-eval-backend
```

## Configuration

See `.env.example`. Key settings:

- **Claude**: `ANTHROPIC_API_KEY`, `AGENT_MODEL` / `JUDGE_MODEL` (default `claude-opus-5-5`), `AGENT_EFFORT` / `JUDGE_EFFORT`, `ENABLE_FALLBACKS` (server-side retry on a fallback model if a request is refused).
- **Gemini**: `GEMINI_API_KEY` (from Google AI Studio), `GEMINI_AGENT_MODEL` / `GEMINI_JUDGE_MODEL` (default `gemini-3.5-flash-lite`).
- **Judge**: `JUDGE_PROVIDER` = `anthropic` or `gemini` picks who grades answers for `llm_judge`.
- **Run**: `AGENT_MAX_TURNS`, `MAX_CONCURRENCY` (questions at once; use `1` on a rate-limited free tier).

Gemini's free tier has small per-minute **and per-day** limits per model. A `429 RESOURCE_EXHAUSTED` error naming `GenerateRequestsPerDay...` means the day's allowance for that model is used up: switch `GEMINI_AGENT_MODEL` / `GEMINI_JUDGE_MODEL` to another model, wait for the daily reset, or enable billing in Google AI Studio.
