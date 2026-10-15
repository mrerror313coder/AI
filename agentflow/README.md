# AgentFlow

Open-source AI agent orchestrator with a modular skill system.

- **Backend** — FastAPI service that lists skills and runs prompts
- **Frontend** — Streamlit dashboard
- **Skills** — pluggable agents (`code_reviewer`, `markdown_generator`)
- **LLM** — local [Ollama](https://ollama.com) when available; automatic mock fallback offline

## Setup

```bash
cd agentflow
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run the backend

From the `agentflow/` directory:

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

API docs: http://127.0.0.1:8000/docs

### Endpoints

| Method | Path        | Description                                      |
|--------|-------------|--------------------------------------------------|
| GET    | `/health`   | Liveness + loaded skill count + LLM backend      |
| GET    | `/skills`   | List registered skills                           |
| POST   | `/execute`  | Run `{ "skill": "...", "prompt": "..." }`        |

Optional Ollama env vars: `OLLAMA_BASE_URL` (default `http://127.0.0.1:11434`), `OLLAMA_MODEL` (default `llama3.2`).

## Run the Streamlit UI

In a second terminal (still inside `agentflow/` with the venv active):

```bash
streamlit run app.py
```

Override the API base URL in the sidebar, or set `AGENTFLOW_API_BASE`.

## Adding a skill

1. Create `skills/my_skill.py` with a `BaseSkill` subclass (`name`, `description`, `run`).
2. Restart the backend — skills are auto-discovered from the `skills/` package.
