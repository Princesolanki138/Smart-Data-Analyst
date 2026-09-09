"""Visualization service — generates Plotly charts from query results."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def create_chart(
    df: pd.DataFrame,
    chart_type: str,
    query: str = "",
) -> go.Figure | None:
    """Create a Plotly figure based on the recommended chart type.

    Returns None if chart_type is 'none' or the data cannot be charted.
    """
    if chart_type == "none" or df is None or df.empty:
        return None

    # Limit rows for chart performance
    plot_df = df.head(50).copy()

    # Identify column types
    numeric_cols = plot_df.select_dtypes(include="number").columns.tolist()
    non_numeric_cols = plot_df.select_dtypes(exclude="number").columns.tolist()

    try:
        if chart_type == "bar":
            return _bar_chart(plot_df, numeric_cols, non_numeric_cols, query)
        elif chart_type == "line":
            return _line_chart(plot_df, numeric_cols, non_numeric_cols, query)
        elif chart_type == "histogram":
            return _histogram(plot_df, numeric_cols, query)
        elif chart_type == "scatter":
            return _scatter_chart(plot_df, numeric_cols, query)
        elif chart_type == "pie":
            return _pie_chart(plot_df, numeric_cols, non_numeric_cols, query)
        else:
            return None
    except Exception:
        return None


def _apply_theme(fig: go.Figure, title: str) -> go.Figure:
    """Apply a consistent professional theme to charts."""
    fig.update_layout(
        template="plotly_white",
        title=dict(text=title, font=dict(size=16)),
        margin=dict(l=40, r=40, t=60, b=40),
        font=dict(family="Inter, sans-serif", size=12),
        height=420,
    )
    return fig


def _bar_chart(
    df: pd.DataFrame,
    numeric_cols: list[str],
    non_numeric_cols: list[str],
    query: str,
) -> go.Figure:
    x_col = non_numeric_cols[0] if non_numeric_cols else df.columns[0]
    y_col = numeric_cols[0] if numeric_cols else df.columns[-1]
    fig = px.bar(df, x=x_col, y=y_col, color_discrete_sequence=["#4F46E5"])
    return _apply_theme(fig, query or f"{y_col} by {x_col}")


def _line_chart(
    df: pd.DataFrame,
    numeric_cols: list[str],
    non_numeric_cols: list[str],
    query: str,
) -> go.Figure:
    x_col = non_numeric_cols[0] if non_numeric_cols else df.columns[0]
    y_col = numeric_cols[0] if numeric_cols else df.columns[-1]
    fig = px.line(df, x=x_col, y=y_col, markers=True, color_discrete_sequence=["#4F46E5"])
    return _apply_theme(fig, query or f"{y_col} over {x_col}")


def _histogram(
    df: pd.DataFrame,
    numeric_cols: list[str],
    query: str,
) -> go.Figure:
    col = numeric_cols[0] if numeric_cols else df.columns[0]
    fig = px.histogram(df, x=col, color_discrete_sequence=["#4F46E5"])
    return _apply_theme(fig, query or f"Distribution of {col}")


def _scatter_chart(
    df: pd.DataFrame,
    numeric_cols: list[str],
    query: str,
) -> go.Figure:
    x_col = numeric_cols[0] if len(numeric_cols) >= 1 else df.columns[0]
    y_col = numeric_cols[1] if len(numeric_cols) >= 2 else df.columns[-1]
    fig = px.scatter(df, x=x_col, y=y_col, color_discrete_sequence=["#4F46E5"])
    return _apply_theme(fig, query or f"{y_col} vs {x_col}")


def _pie_chart(
    df: pd.DataFrame,
    numeric_cols: list[str],
    non_numeric_cols: list[str],
    query: str,
) -> go.Figure:
    names_col = non_numeric_cols[0] if non_numeric_cols else df.columns[0]
    values_col = numeric_cols[0] if numeric_cols else df.columns[-1]
    fig = px.pie(df, names=names_col, values=values_col)
    return _apply_theme(fig, query or f"{values_col} share by {names_col}")
