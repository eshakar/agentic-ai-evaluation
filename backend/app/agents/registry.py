from app.agents.base import BaseAgent
from app.agents.claude_agent import ClaudeToolAgent
from app.agents.echo_agent import EchoAgent
from app.agents.gemini_agent import GeminiToolAgent

_AGENTS: dict[str, type[BaseAgent]] = {
    EchoAgent.name: EchoAgent,
    ClaudeToolAgent.name: ClaudeToolAgent,
    GeminiToolAgent.name: GeminiToolAgent,
}


def list_agents() -> list[str]:
    return sorted(_AGENTS)


def get_agent(name: str) -> BaseAgent:
    try:
        return _AGENTS[name]()
    except KeyError as exc:
        raise ValueError(f"Unknown agent '{name}'. Available: {list_agents()}") from exc
