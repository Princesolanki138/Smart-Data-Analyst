"""LLM Service — handles all communication with the OpenAI-compatible API."""

from __future__ import annotations

import re
from openai import OpenAI

from config.settings import settings
from utils.prompt_templates import (
    CODE_GENERATION_SYSTEM,
    CODE_GENERATION_USER,
    ERROR_FIX_SYSTEM,
    ERROR_FIX_USER,
    INSIGHT_SYSTEM,
    INSIGHT_USER,
    VISUALIZATION_SYSTEM,
    VISUALIZATION_USER,
)


def _get_client() -> OpenAI:
    """Create an OpenAI-compatible client pointing at Ollama."""
    return OpenAI(
        api_key="ollama",  # Ollama ignores this but the client requires it
        base_url=settings.OLLAMA_BASE_URL,
    )


def _chat(system: str, user: str, temperature: float | None = None) -> str:
    """Send a chat completion request and return the assistant's reply."""
    client = _get_client()
    response = client.chat.completions.create(
        model=settings.OLLAMA_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature if temperature is not None else settings.TEMPERATURE,
        max_tokens=2048,
    )
    content = response.choices[0].message.content
    return (content or "").strip()


def _strip_markdown_fences(code: str) -> str:
    """Remove ```python ... ``` wrappers if the LLM ignores instructions."""
    code = code.strip()
    # Remove opening fence
    code = re.sub(r"^```(?:python)?\s*\n?", "", code)
    # Remove closing fence
    code = re.sub(r"\n?```\s*$", "", code)
    return code.strip()


def generate_code(
    schema: str,
    query: str,
    history: str = "",
) -> str:
    """Generate Pandas code from a natural-language query."""
    user_prompt = CODE_GENERATION_USER.format(
        schema=schema,
        query=query,
        history=history if history else "(No prior queries)",
    )
    raw = _chat(CODE_GENERATION_SYSTEM, user_prompt)
    return _strip_markdown_fences(raw)


def fix_code(
    schema: str,
    query: str,
    code: str,
    error: str,
) -> str:
    """Ask the LLM to fix code that raised an error."""
    user_prompt = ERROR_FIX_USER.format(
        schema=schema,
        query=query,
        code=code,
        error=error,
    )
    raw = _chat(ERROR_FIX_SYSTEM, user_prompt)
    return _strip_markdown_fences(raw)


def generate_insights(
    query: str,
    result_summary: str,
    result_data: str,
) -> str:
    """Generate human-readable business insights from query results."""
    user_prompt = INSIGHT_USER.format(
        query=query,
        result_summary=result_summary,
        result_data=result_data,
    )
    return _chat(INSIGHT_SYSTEM, user_prompt, temperature=0.4)


def recommend_chart_type(
    query: str,
    columns_info: str,
    num_rows: int,
) -> str:
    """Ask the LLM to recommend a chart type for the result."""
    user_prompt = VISUALIZATION_USER.format(
        query=query,
        columns_info=columns_info,
        num_rows=num_rows,
    )
    reply = _chat(VISUALIZATION_SYSTEM, user_prompt)
    # Normalise: take the first word, lowercase
    chart_type = reply.strip().split()[0].lower() if reply.strip() else "none"
    valid_types = {"bar", "line", "histogram", "scatter", "pie", "none"}
    return chart_type if chart_type in valid_types else "none"
