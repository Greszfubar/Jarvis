"""BaseAgent — all agents extend this."""
from abc import ABC, abstractmethod
from typing import Any


class BaseAgent(ABC):
    name: str = "base"

    @abstractmethod
    def tools(self) -> list[dict]:
        """Return Anthropic tool definitions for this agent."""
        ...

    @abstractmethod
    async def execute(self, method: str, params: dict) -> Any:
        """Execute a named method with params."""
        ...

    async def tick(self):
        """Called every N minutes by the scheduler for proactive work. Override as needed."""
        pass

    def _tool(self, method: str, description: str, properties: dict, required: list = None) -> dict:
        return {
            "name": f"{self.name}__{method}",
            "description": description,
            "input_schema": {
                "type": "object",
                "properties": properties,
                "required": required or [],
            },
        }
