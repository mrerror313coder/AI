"""Sample skill: turn a free-form prompt into polished markdown."""

from __future__ import annotations

from skills.base import BaseSkill, LLMClient, SkillResult

SYSTEM_PROMPT = """You are a technical writing assistant.
Convert the user's request into clean, well-structured markdown.
Use headings, lists, and code fences where appropriate.
Do not wrap the entire response in an outer code fence unless asked.
"""


class MarkdownGeneratorSkill(BaseSkill):
    name = "markdown_generator"
    description = "Turns a prompt into well-structured markdown."

    def run(self, prompt: str, llm: LLMClient) -> SkillResult:
        logs = [
            f"[{self.name}] generating markdown",
            f"[{self.name}] prompt length={len(prompt)}",
        ]
        output = llm.generate(prompt, system=SYSTEM_PROMPT)
        logs.append(f"[{self.name}] generation complete ({len(output)} chars)")
        return SkillResult(
            skill=self.name,
            output=output,
            metadata={"mode": "markdown", "prompt_chars": len(prompt)},
            logs=logs,
        )
