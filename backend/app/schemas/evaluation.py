from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ToolCall(BaseModel):
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    output: str | None = None


class AgentTrace(BaseModel):
    """Everything the agent produced for one task: final answer plus its trajectory."""

    output: str
    tool_calls: list[ToolCall] = Field(default_factory=list)
    turns: int = 0
    latency_ms: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    error: str | None = None


class EvalCase(BaseModel):
    id: str
    input: str
    expected_output: str | None = None
    expected_tools: list[str] | None = Field(
        default=None, description="Tool names the agent is expected to call, in order."
    )
    rubric: str | None = Field(default=None, description="Grading criteria for the LLM judge.")
    metadata: dict[str, Any] = Field(default_factory=dict)


class MetricResult(BaseModel):
    name: str
    score: float = Field(ge=0.0, le=1.0)
    passed: bool
    reason: str = ""


class CaseResult(BaseModel):
    case_id: str
    trace: AgentTrace
    metrics: list[MetricResult]

    @property
    def scored(self) -> bool:
        """False when none of the chosen evaluators applied to this case."""
        return bool(self.metrics)

    @property
    def passed(self) -> bool:
        return self.scored and all(m.passed for m in self.metrics)


class RunSummary(BaseModel):
    run_id: str
    created_at: datetime
    agent: str
    evaluators: list[str]
    num_cases: int
    num_scored: int = Field(
        default=0, description="Cases at least one evaluator applied to; pass_rate is over these."
    )
    pass_rate: float
    mean_scores: dict[str, float]
    mean_latency_ms: float
    results: list[CaseResult]


class RunListItem(BaseModel):
    """Lightweight run info for listing past runs."""

    run_id: str
    created_at: datetime
    agent: str
    num_cases: int
    pass_rate: float


class RunRequest(BaseModel):
    """Run an agent over a dataset (or inline cases) and score it."""

    agent: str = "echo"
    dataset: str | None = Field(
        default=None, description="File name in datasets/, e.g. sample_eval.jsonl"
    )
    cases: list[EvalCase] | None = None
    evaluators: list[str] = Field(
        default_factory=lambda: ["exact_match", "tool_sequence", "latency"]
    )


class AskRequest(BaseModel):
    """One free-form question for a quick manual check of an agent."""

    agent: str = "echo"
    question: str = Field(min_length=1, max_length=4000)
    expected_output: str | None = Field(
        default=None, max_length=1000, description="Optional: the answer you expect."
    )
    expected_tools: list[str] | None = Field(
        default=None, description="Optional: tools the agent should call, in order."
    )
    rubric: str | None = Field(
        default=None, max_length=2000, description="Optional: grading rules for the AI judge."
    )
    use_judge: bool = Field(default=False, description="Also grade the answer with llm_judge.")


class AskResponse(BaseModel):
    agent: str
    question: str
    trace: AgentTrace
    metrics: list[MetricResult]


DATASET_NAME_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}\.jsonl$"


class SaveCaseRequest(BaseModel):
    """Add one question to a dataset file (created if it does not exist)."""

    dataset: str = Field(default="my_questions.jsonl", pattern=DATASET_NAME_PATTERN)
    question: str = Field(min_length=1, max_length=4000)
    expected_output: str | None = Field(default=None, max_length=1000)
    expected_tools: list[str] | None = None
    rubric: str | None = Field(default=None, max_length=2000)
    category: str | None = Field(default=None, max_length=50)


class SaveCaseResponse(BaseModel):
    dataset: str
    case: EvalCase
    total_cases: int


class ScoreItem(BaseModel):
    case: EvalCase
    trace: AgentTrace


class ScoreRequest(BaseModel):
    """Score pre-recorded traces from an external agent (no agent execution)."""

    agent: str = "external"
    items: list[ScoreItem]
    evaluators: list[str] = Field(default_factory=lambda: ["exact_match", "tool_sequence"])
