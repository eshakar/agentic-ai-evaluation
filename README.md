# agentic-ai-evaluation

An "exam system" for AI agents: give an agent a set of questions, record how it answers (final answer, tools it called, time, tokens), score the answers, and view the report card in a web dashboard.

```
agentic-ai-evaluation/
├── backend/    FastAPI service: agents, evaluators, datasets, tests  → see backend/README.md
├── frontend/   Next.js + shadcn/ui dashboard                         → see frontend/README.md
├── .github/workflows/ci.yml   lint, tests and build for both on every push / PR
└── docker-compose.yml         runs the backend in Docker
```

## Run it locally

You need **Python 3.11+** and **Node.js 20+**. Use two terminals.

**Terminal 1: backend** (http://localhost:8000, API docs at `/docs`)

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
copy .env.example .env            # then add your ANTHROPIC_API_KEY
uvicorn app.main:app --reload --port 8000
```

**Terminal 2: frontend** (http://localhost:3000)

```powershell
cd frontend
npm install
npm run dev
```

Open http://localhost:3000, pick an agent, a dataset and evaluators, and click **Run evaluation**.
The `echo` agent and the non-LLM evaluators work without an API key; `claude` and `llm_judge` need `ANTHROPIC_API_KEY` in `backend/.env`.

## How the two parts talk

The frontend calls the backend's REST API at `NEXT_PUBLIC_API_URL` (default `http://localhost:8000`; override it in `frontend/.env.local`). The backend allows requests from `http://localhost:3000` (CORS); change `CORS_ORIGINS` in `backend/.env` if the frontend runs elsewhere.

| Endpoint | Used for |
|---|---|
| `GET  /api/v1/evaluations/catalog` | agents, evaluators and datasets for the form |
| `POST /api/v1/evaluations/run` | run an agent over a dataset and score it |
| `GET  /api/v1/evaluations/runs` | past runs list |
| `GET  /api/v1/evaluations/{run_id}` | one run's full report |
| `POST /api/v1/evaluations/score` | score traces recorded by an external agent |
