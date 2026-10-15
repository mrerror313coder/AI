"""Base skill contract for AgentFlow agents."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Protocol

from pydantic import BaseModel, Field


class LLMClient(Protocol):
    """Minimal interface expected from an LLM backend (Ollama or mock)."""

    def generate(self, prompt: str, system: str | None = None) -> str:
        """Return model text for the given prompt."""
        ...


class SkillResult(BaseModel):
    """Structured result returned by every skill."""

    skill: str
    output: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    logs: list[str] = Field(default_factory=list)


class BaseSkill(ABC):
    """Abstract skill: name, description, and a run/execute entrypoint."""

    name: str = "base"
    description: str = "Abstract skill"

    @abstractmethod
    def run(self, prompt: str, llm: LLMClient) -> SkillResult:
        """Execute the skill against *prompt* using *llm*."""

    def execute(self, prompt: str, llm: LLMClient) -> SkillResult:
        """Alias for :meth:`run` so callers can use either verb."""
        return self.run(prompt, llm)
