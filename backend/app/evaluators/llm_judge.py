"""LLM-as-judge: Claude or Gemini (JUDGE_PROVIDER) grades an answer and trajectory by rubric."""

import json

from google.genai import types
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.evaluators.base import BaseEvaluator
from app.schemas.evaluation import AgentTrace, EvalCase, MetricResult
from app.services.gemini_client import get_gemini_client
from app.services.llm_client import create_message

JUDGE_SYSTEM = (
    "You are a strict, impartial evaluator of AI agent runs. Grade only against the rubric and "
    "reference answer provided. Judge the final answer for correctness and completeness, and the "
    "tool trajectory for whether the tools used were appropriate and efficient. Do not reward "
    "verbosity. Score from 1 (fails the rubric) to 5 (fully meets it)."
)

DEFAULT_RUBRIC = (
    "The final answer correctly and completely resolves the user's task, is consistent with the "
    "reference answer if one is given, and any tools used were appropriate for the task."
)


class JudgeVerdict(BaseModel):
    reasoning: str = Field(description="Brief justification citing the rubric.")
    score: int = Field(ge=1, le=5)


JUDGE_SCHEMA = {
    "type": "object",
    "properties": {
        "reasoning": {"type": "string"},
        "score": {"type": "integer", "enum": [1, 2, 3, 4, 5]},
    },
    "required": ["reasoning", "score"],
    "additionalProperties": False,
}


class LLMJudgeEvaluator(BaseEvaluator):
    name = "llm_judge"
    pass_threshold = 4

    async def evaluate(self, case: EvalCase, trace: AgentTrace) -> MetricResult | None:
        settings = get_settings()
        trajectory = [
            {"tool": c.name, "arguments": c.arguments, "output": c.output} for c in trace.tool_calls
        ]
        reference = case.expected_output or "(none provided)"
        prompt = (
            f"<task>\n{case.input}\n</task>\n\n"
            f"<reference_answer>\n{reference}\n</reference_answer>\n\n"
            f"<rubric>\n{case.rubric or DEFAULT_RUBRIC}\n</rubric>\n\n"
            f"<agent_trajectory>\n{json.dumps(trajectory, indent=2)}\n</agent_trajectory>\n\n"
            f"<agent_final_answer>\n{trace.output}\n</agent_final_answer>"
        )

        if settings.judge_provider == "gemini":
            text = await _judge_with_gemini(prompt)
        else:
            text = await _judge_with_claude(prompt)
        if text is None:
            return MetricResult(name=self.name, score=0.0, passed=False, reason="judge refused")

        verdict = JudgeVerdict.model_validate_json(text)
        return MetricResult(
            name=self.name,
            score=(verdict.score - 1) / 4,  # normalize 1..5 -> 0..1
            passed=verdict.score >= self.pass_threshold,
            reason=verdict.reasoning,
        )


async def _judge_with_claude(prompt: str) -> str | None:
    """Returns the verdict JSON, or None if the judge refused."""
    settings = get_settings()
    response = await create_message(
        model=settings.judge_model,
        effort=settings.judge_effort,
        system=JUDGE_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
        output_config={"format": {"type": "json_schema", "schema": JUDGE_SCHEMA}},
    )
    if response.stop_reason == "refusal":
        return None
    return "".join(b.text for b in response.content if b.type == "text")


async def _judge_with_gemini(prompt: str) -> str | None:
    """Returns the verdict JSON, or None if the judge's response was blocked."""
    settings = get_settings()
    response = await get_gemini_client().aio.models.generate_content(
        model=settings.gemini_judge_model,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=JUDGE_SYSTEM,
            response_mime_type="application/json",
            response_json_schema=JUDGE_SCHEMA,
        ),
    )
    if not response.candidates or not response.text:
        return None
    return response.text
