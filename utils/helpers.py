"""Utility helpers for data processing and formatting."""

import pandas as pd


def get_dataframe_summary(df: pd.DataFrame) -> str:
    """Generate a concise summary of a DataFrame for LLM context.

    Includes column names, dtypes, shape, sample values, and basic stats
    so the LLM can write accurate Pandas code.
    """
    lines: list[str] = []
    lines.append(f"Shape: {df.shape[0]} rows × {df.shape[1]} columns")
    lines.append("")
    lines.append("Columns and dtypes:")
    for col in df.columns:
        dtype = df[col].dtype
        null_count = df[col].isna().sum()
        unique_count = df[col].nunique()
        sample_vals = df[col].dropna().head(3).tolist()
        sample_str = ", ".join(str(v) for v in sample_vals)
        lines.append(
            f"  - {col} ({dtype}) | nulls: {null_count}, "
            f"unique: {unique_count} | sample: [{sample_str}]"
        )
    lines.append("")

    # Basic stats for numeric columns
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    if numeric_cols:
        lines.append("Numeric column stats (min / mean / max):")
        for col in numeric_cols[:10]:  # Limit to avoid huge prompts
            lines.append(
                f"  - {col}: {df[col].min():.2f} / {df[col].mean():.2f} / {df[col].max():.2f}"
            )
    return "\n".join(lines)


def format_result_for_display(result: object) -> tuple[str, pd.DataFrame | None]:
    """Convert an execution result into a display string and optional DataFrame.

    Returns:
        (display_text, dataframe_or_none)
    """
    if isinstance(result, pd.DataFrame):
        return result.to_string(max_rows=50), result
    if isinstance(result, pd.Series):
        frame = result.reset_index()
        frame.columns = [str(c) for c in frame.columns]
        return frame.to_string(max_rows=50), frame
    if result is None:
        return "Query executed successfully (no output).", None
    # Scalar or other
    return str(result), None


def truncate_dataframe(df: pd.DataFrame, max_rows: int = 500) -> pd.DataFrame:
    """Truncate a DataFrame for safe display."""
    if len(df) > max_rows:
        return df.head(max_rows)
    return df


def convert_df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    """Convert a DataFrame to CSV bytes for download."""
    return df.to_csv(index=False).encode("utf-8")
