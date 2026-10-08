import time
from typing import Any

from app.agents.base import BaseAgent
from app.agents.tools import HANDLERS, TOOLS
from app.core.config import get_settings
from app.schemas.evaluation import AgentTrace, ToolCall
from app.services.llm_client import create_message

SYSTEM_PROMPT = (
    "You are a helpful assistant with access to tools. Use a tool whenever it gives a more "
    "reliable answer than reasoning alone. Finish with a concise final answer."
)


class ClaudeToolAgent(BaseAgent):
    """Tool-using Claude agent driven by a manual agentic loop, so every step is traceable."""

    name = "claude"

    async def run(self, task: str) -> AgentTrace:
        settings = get_settings()
        start = time.perf_counter()
        messages: list[dict[str, Any]] = [{"role": "user", "content": task}]
        tool_calls: list[ToolCall] = []
        usage = {"input": 0, "output": 0}
        response: Any = None
        error: str | None = "max_turns_exceeded"
        turn = 0

        for turn in range(1, settings.agent_max_turns + 1):  # noqa: B007 (read after loop)
            response = await create_message(
                model=settings.agent_model,
                effort=settings.agent_effort,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=messages,
            )
            usage["input"] += response.usage.input_tokens
            usage["output"] += response.usage.output_tokens
            # Append the full content (not only text) so thinking and tool_use blocks are kept.
            messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason == "refusal":
                error = "refusal"
                break
            if response.stop_reason != "tool_use":
                error = None
                break

            results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                args = dict(block.input)
                try:
                    output, is_error = HANDLERS[block.name](**args), False
                except Exception as exc:  # surface tool errors to the model instead of crashing
                    output, is_error = f"Error: {exc}", True
                tool_calls.append(ToolCall(name=block.name, arguments=args, output=output))
                results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": output,
                        "is_error": is_error,
                    }
                )
            # All tool results for one turn go back in a single user message.
            messages.append({"role": "user", "content": results})

        output = ""
        if response is not None and error != "refusal":
            output = "".join(b.text for b in response.content if b.type == "text").strip()

        return AgentTrace(
            output=output,
            tool_calls=tool_calls,
            turns=turn,
            latency_ms=(time.perf_counter() - start) * 1000,
            input_tokens=usage["input"],
            output_tokens=usage["output"],
            error=error,
        )
