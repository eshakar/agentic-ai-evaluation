import time
from typing import Any

from google.genai import types

from app.agents.base import BaseAgent
from app.agents.claude_agent import SYSTEM_PROMPT
from app.agents.tools import HANDLERS, TOOLS
from app.core.config import get_settings
from app.schemas.evaluation import AgentTrace, ToolCall
from app.services.gemini_client import get_gemini_client

# Same tools as the Claude agent, so the two can be compared on the same dataset.
GEMINI_TOOLS = [
    types.Tool(
        function_declarations=[
            types.FunctionDeclaration(
                name=t["name"],
                description=t["description"],
                parameters_json_schema=t["input_schema"],
            )
            for t in TOOLS
        ]
    )
]

# Finish reasons that mean the answer is unusable rather than complete.
_ERROR_FINISH = {
    types.FinishReason.MAX_TOKENS: "max_tokens",
    types.FinishReason.SAFETY: "safety_block",
    types.FinishReason.PROHIBITED_CONTENT: "safety_block",
    types.FinishReason.BLOCKLIST: "safety_block",
    types.FinishReason.MALFORMED_FUNCTION_CALL: "malformed_function_call",
}


class GeminiToolAgent(BaseAgent):
    """Tool-using Gemini agent with a manual function-calling loop, so every step is traceable."""

    name = "gemini"

    async def run(self, task: str) -> AgentTrace:
        settings = get_settings()
        client = get_gemini_client()
        start = time.perf_counter()
        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            tools=GEMINI_TOOLS,
            # We run the tools ourselves so each call is recorded for scoring.
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        )
        contents: list[types.Content] = [
            types.Content(role="user", parts=[types.Part.from_text(text=task)])
        ]
        tool_calls: list[ToolCall] = []
        usage = {"input": 0, "output": 0}
        response: Any = None
        error: str | None = "max_turns_exceeded"
        turn = 0

        for turn in range(1, settings.agent_max_turns + 1):  # noqa: B007 (read after loop)
            response = await client.aio.models.generate_content(
                model=settings.gemini_agent_model, contents=contents, config=config
            )
            meta = response.usage_metadata
            if meta:
                usage["input"] += meta.prompt_token_count or 0
                usage["output"] += (meta.candidates_token_count or 0) + (
                    meta.thoughts_token_count or 0
                )

            if not response.candidates:
                error = "prompt_blocked"
                break
            candidate = response.candidates[0]
            if candidate.finish_reason in _ERROR_FINISH:
                error = _ERROR_FINISH[candidate.finish_reason]
                break
            # Append the model's turn unchanged: it carries thought signatures Gemini needs back.
            contents.append(candidate.content)

            calls = response.function_calls
            if not calls:
                error = None
                break

            parts = []
            for call in calls:
                args = dict(call.args or {})
                try:
                    output, payload = HANDLERS[call.name](**args), "result"
                except Exception as exc:  # surface tool errors to the model instead of crashing
                    output, payload = f"Error: {exc}", "error"
                tool_calls.append(ToolCall(name=call.name, arguments=args, output=output))
                parts.append(
                    types.Part(
                        function_response=types.FunctionResponse(
                            id=call.id, name=call.name, response={payload: output}
                        )
                    )
                )
            # All function results for one turn go back together.
            contents.append(types.Content(role="user", parts=parts))

        return AgentTrace(
            output=_final_text(response) if error is None or error == "max_turns_exceeded" else "",
            tool_calls=tool_calls,
            turns=turn,
            latency_ms=(time.perf_counter() - start) * 1000,
            input_tokens=usage["input"],
            output_tokens=usage["output"],
            error=error,
        )


def _final_text(response: Any) -> str:
    if response is None or not response.candidates or not response.candidates[0].content:
        return ""
    parts = response.candidates[0].content.parts or []
    return "".join(p.text for p in parts if p.text and not p.thought).strip()
