"""LLM client: prefer local Ollama; fall back to a deterministic mock."""

from __future__ import annotations

import os
from typing import Optional

import httpx

DEFAULT_OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")


class OllamaClient:
    """Thin HTTP wrapper around Ollama's ``/api/generate`` endpoint."""

    def __init__(
        self,
        base_url: str = DEFAULT_OLLAMA_URL,
        model: str = DEFAULT_MODEL,
        timeout: float = 60.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def available(self) -> bool:
        try:
            with httpx.Client(timeout=2.0) as client:
                resp = client.get(f"{self.base_url}/api/tags")
                return resp.status_code == 200
        except Exception:
            return False

    def generate(self, prompt: str, system: str | None = None) -> str:
        payload: dict = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }
        if system:
            payload["system"] = system
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(f"{self.base_url}/api/generate", json=payload)
            resp.raise_for_status()
            data = resp.json()
            return (data.get("response") or "").strip()


class MockLLMClient:
    """Offline fallback so AgentFlow works without Ollama installed."""

    def generate(self, prompt: str, system: str | None = None) -> str:
        mode = "general"
        if system:
            lowered = system.lower()
            if "code reviewer" in lowered:
                mode = "code_review"
            elif "markdown" in lowered or "technical writing" in lowered:
                mode = "markdown"

        snippet = prompt.strip()
        if len(snippet) > 400:
            snippet = snippet[:400] + "…"

        if mode == "code_review":
            return (
                "## Summary\n"
                "Mock review (Ollama unavailable). The snippet was inspected for "
                "common structure and readability issues.\n\n"
                "## Strengths\n"
                "- Input was received and parsed successfully\n"
                "- Intent looks clear enough for a first-pass review\n\n"
                "## Issues\n"
                "- Unable to run a live model — feedback is heuristic only\n"
                "- Edge cases and runtime behavior were not executed\n\n"
                "## Suggestions\n"
                "- Start Ollama locally for richer, model-backed reviews\n"
                "- Add tests around the hottest paths in the snippet\n\n"
                f"### Reviewed excerpt\n```\n{snippet}\n```"
            )

        if mode == "markdown":
            return (
                f"# Generated Markdown (mock)\n\n"
                f"> Ollama was not reachable, so this is a structured stub.\n\n"
                f"## Request\n\n{snippet}\n\n"
                f"## Outline\n\n"
                f"1. Context\n"
                f"2. Key points\n"
                f"3. Next steps\n\n"
                f"## Draft body\n\n"
                f"Expand each section above based on the request. "
                f"Replace this stub by pointing AgentFlow at a running Ollama instance."
            )

        return (
            f"**Mock LLM response**\n\n"
            f"Ollama is offline. Echoing your prompt:\n\n{snippet}"
        )


def get_llm_client(
    prefer_ollama: bool = True,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
) -> tuple[object, str]:
    """
    Return ``(client, backend_name)``.

    Tries Ollama first when *prefer_ollama* is true; otherwise uses the mock.
    """
    if prefer_ollama:
        client = OllamaClient(
            base_url=base_url or DEFAULT_OLLAMA_URL,
            model=model or DEFAULT_MODEL,
        )
        if client.available():
            return client, "ollama"
    return MockLLMClient(), "mock"
