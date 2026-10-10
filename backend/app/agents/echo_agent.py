import time

from app.agents.base import BaseAgent
from app.schemas.evaluation import AgentTrace


class EchoAgent(BaseAgent):
    """Offline baseline that echoes the input. Lets you test the pipeline without an API key."""

    name = "echo"

    async def run(self, task: str) -> AgentTrace:
        start = time.perf_counter()
        return AgentTrace(output=task, turns=1, latency_ms=(time.perf_counter() - start) * 1000)
