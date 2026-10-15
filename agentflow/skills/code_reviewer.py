"""Sample skill: review code-like input and return structured feedback."""

from __future__ import annotations

from skills.base import BaseSkill, LLMClient, SkillResult

SYSTEM_PROMPT = """You are a careful senior code reviewer.
Review the user's code (or code-like snippet) and respond with markdown that includes:
1. **Summary** — one short paragraph
2. **Strengths** — bullet list
3. **Issues** — bullet list of bugs, smells, or risks (severity + why)
4. **Suggestions** — concrete improvements
Be specific and concise. If the input is not code, say so and still offer useful feedback.
"""


class CodeReviewerSkill(BaseSkill):
    name = "code_reviewer"
    description = "Reviews code-ish input and returns structured feedback."

    def run(self, prompt: str, llm: LLMClient) -> SkillResult:
        logs = [
            f"[{self.name}] starting review",
            f"[{self.name}] prompt length={len(prompt)}",
        ]
        review_prompt = (
            "Please review the following code or snippet:\n\n"
            f"```\n{prompt}\n```"
        )
        output = llm.generate(review_prompt, system=SYSTEM_PROMPT)
        logs.append(f"[{self.name}] review complete ({len(output)} chars)")
        return SkillResult(
            skill=self.name,
            output=output,
            metadata={"mode": "code_review", "prompt_chars": len(prompt)},
            logs=logs,
        )
