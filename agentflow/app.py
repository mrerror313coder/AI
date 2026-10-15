"""AgentFlow Streamlit dashboard — select a skill, run a prompt, view logs."""

from __future__ import annotations

import os

import requests
import streamlit as st

DEFAULT_API_BASE = os.getenv("AGENTFLOW_API_BASE", "http://127.0.0.1:8000")


def api_get(base: str, path: str, timeout: float = 10.0) -> dict:
    resp = requests.get(f"{base.rstrip('/')}{path}", timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def api_post(base: str, path: str, payload: dict, timeout: float = 120.0) -> dict:
    resp = requests.post(
        f"{base.rstrip('/')}{path}",
        json=payload,
        timeout=timeout,
    )
    resp.raise_for_status()
    return resp.json()


st.set_page_config(
    page_title="AgentFlow",
    page_icon="AF",
    layout="wide",
)

st.title("AgentFlow")
st.caption("Modular AI agent orchestrator — pick a skill, send a prompt, inspect the run.")

with st.sidebar:
    st.header("Connection")
    api_base = st.text_input(
        "Backend URL",
        value=st.session_state.get("api_base", DEFAULT_API_BASE),
        help="FastAPI base URL (default http://127.0.0.1:8000)",
    ).rstrip("/")
    st.session_state["api_base"] = api_base
    prefer_ollama = st.checkbox("Prefer Ollama when available", value=True)

    if st.button("Check health", use_container_width=True):
        try:
            health = api_get(api_base, "/health")
            st.success(
                f"OK — {health.get('skills_loaded', '?')} skills · "
                f"LLM={health.get('llm_backend', '?')}"
            )
        except requests.RequestException as exc:
            st.error(f"Backend unreachable: {exc}")

# --- Load skills -----------------------------------------------------------

skills: list[dict] = []
skills_error: str | None = None
try:
    data = api_get(api_base, "/skills")
    skills = data.get("skills") or []
except requests.RequestException as exc:
    skills_error = str(exc)

if skills_error:
    st.warning(
        f"Could not load skills from `{api_base}`.\n\n"
        f"Start the backend first:\n"
        f"```bash\ncd agentflow && uvicorn backend.main:app --reload --port 8000\n```\n\n"
        f"Error: {skills_error}"
    )
    st.stop()

if not skills:
    st.info("No skills registered on the backend.")
    st.stop()

skill_names = [s["name"] for s in skills]
skill_labels = {
    s["name"]: f"{s['name']} — {s.get('description', '')}" for s in skills
}

col_left, col_right = st.columns([1, 1])

with col_left:
    selected = st.selectbox(
        "Skill",
        options=skill_names,
        format_func=lambda n: skill_labels.get(n, n),
    )
    prompt = st.text_area(
        "Prompt",
        height=220,
        placeholder=(
            "For code_reviewer: paste a function or snippet.\n"
            "For markdown_generator: describe the document you want."
        ),
    )
    run = st.button("Run agent", type="primary", use_container_width=True)

with col_right:
    st.subheader("Response")
    result_box = st.empty()
    st.subheader("Logs")
    log_box = st.empty()

if run:
    if not prompt.strip():
        st.error("Enter a prompt before running.")
    else:
        with st.spinner(f"Running `{selected}`…"):
            try:
                result = api_post(
                    api_base,
                    "/execute",
                    {
                        "skill": selected,
                        "prompt": prompt,
                        "prefer_ollama": prefer_ollama,
                    },
                )
            except requests.RequestException as exc:
                result_box.error(f"Execute failed: {exc}")
                st.stop()

        backend = result.get("backend", "?")
        result_box.markdown(
            f"*Backend: `{backend}` · skill: `{result.get('skill')}`*\n\n"
            f"{result.get('output', '')}"
        )
        logs = result.get("logs") or []
        if logs:
            log_box.code("\n".join(logs), language="text")
        else:
            log_box.info("No logs returned.")

        meta = result.get("metadata") or {}
        if meta:
            with st.expander("Metadata"):
                st.json(meta)
