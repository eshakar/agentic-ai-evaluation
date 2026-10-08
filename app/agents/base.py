from abc import ABC, abstractmethod

from app.schemas.evaluation import AgentTrace


class BaseAgent(ABC):
    """An agent under test. Implement `run` to return the final answer and its trajectory."""

    name: str = "base"

    @abstractmethod
    async def run(self, task: str) -> AgentTrace: ...
