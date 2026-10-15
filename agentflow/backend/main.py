"""AgentFlow FastAPI backend: list skills and execute agent prompts."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Allow `uvicorn backend.main:app` from the agentflow/ directory.
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from backend.llm import get_llm_client  # noqa: E402
from skills import load_skills  # noqa: E402

app = FastAPI(
    title="AgentFlow",
    description="Open-source AI agent orchestrator with a modular skill system.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SKILLS = load_skills()


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class SkillInfo(BaseModel):
    name: str
    description: str


class SkillListResponse(BaseModel):
    skills: list[SkillInfo]
    count: int


class ExecuteRequest(BaseModel):
    skill: str = Field(..., description="Registered skill name to run")
    prompt: str = Field(..., min_length=1, description="User / agent prompt")
    prefer_ollama: bool = Field(
        default=True,
        description="If true, try local Ollama before falling back to mock LLM",
    )
    ollama_base_url: Optional[str] = Field(
        default=None,
        description="Override Ollama base URL (default http://127.0.0.1:11434)",
    )
    ollama_model: Optional[str] = Field(
        default=None,
        description="Override Ollama model name",
    )


class ExecuteResponse(BaseModel):
    skill: str
    prompt: str
    output: str
    backend: str
    logs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    status: str
    skills_loaded: int
    llm_backend: str


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    _, backend = get_llm_client(prefer_ollama=True)
    return HealthResponse(
        status="ok",
        skills_loaded=len(SKILLS),
        llm_backend=backend,
    )


@app.get("/skills", response_model=SkillListResponse)
def list_skills() -> SkillListResponse:
    items = [
        SkillInfo(name=s.name, description=s.description)
        for s in sorted(SKILLS.values(), key=lambda x: x.name)
    ]
    return SkillListResponse(skills=items, count=len(items))


@app.post("/execute", response_model=ExecuteResponse)
def execute_skill(body: ExecuteRequest) -> ExecuteResponse:
    skill = SKILLS.get(body.skill)
    if skill is None:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown skill '{body.skill}'. Available: {sorted(SKILLS)}",
        )

    llm, backend_name = get_llm_client(
        prefer_ollama=body.prefer_ollama,
        base_url=body.ollama_base_url,
        model=body.ollama_model,
    )

    logs = [f"[orchestrator] using LLM backend={backend_name}"]
    result = skill.execute(body.prompt, llm)
    logs.extend(result.logs)

    return ExecuteResponse(
        skill=result.skill,
        prompt=body.prompt,
        output=result.output,
        backend=backend_name,
        logs=logs,
        metadata=result.metadata,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
