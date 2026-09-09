"""Insight generation service.

Uses the LLM to produce concise, business-focused takeaways from query results.
"""

from __future__ import annotations

import pandas as pd

from services.llm_service import generate_insights as _llm_insights


def generate(query: str, result: object) -> str:
    """Generate human-readable insights from a query result.

    Args:
        query: The original natural-language query.
        result: The execution result (DataFrame, Series, scalar, etc.).

    Returns:
        A short markdown-formatted insights string.
    """
    result_summary, result_data = _prepare_result(result)
    try:
        return _llm_insights(
            query=query,
            result_summary=result_summary,
            result_data=result_data,
        )
    except Exception as exc:
        return f"_Could not generate insights: {exc}_"


def _prepare_result(result: object) -> tuple[str, str]:
    """Convert result into summary text and data text for the LLM prompt."""
    if isinstance(result, pd.DataFrame):
        summary = (
            f"DataFrame with {len(result)} rows and {len(result.columns)} columns.\n"
            f"Columns: {', '.join(result.columns.tolist())}"
        )
        data = result.head(20).to_string(index=False)
        return summary, data

    if isinstance(result, pd.Series):
        summary = f"Series with {len(result)} entries."
        data = result.head(20).to_string()
        return summary, data

    # Scalar or other
    text = str(result)
    return text, text
