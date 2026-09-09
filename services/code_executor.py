"""Sandboxed code execution engine.

Executes LLM-generated Pandas code in a restricted environment
that blocks file-system, network, and OS access.
"""

from __future__ import annotations

import re
from typing import Any

import pandas as pd
import numpy as np

# ---------------------------------------------------------------------------
# Blocklist — patterns that MUST NOT appear in generated code
# ---------------------------------------------------------------------------
_BLOCKED_PATTERNS: list[tuple[str, str]] = [
    (r"\bimport\s+(os|sys|subprocess|shutil|pathlib|socket|http|requests|urllib)",
     "Importing forbidden module"),
    (r"\bfrom\s+(os|sys|subprocess|shutil|pathlib|socket|http|requests|urllib)\b",
     "Importing from forbidden module"),
    (r"\b__import__\s*\(", "Use of __import__"),
    (r"\bexec\s*\(", "Use of exec()"),
    (r"\beval\s*\(", "Use of eval()"),
    (r"\bcompile\s*\(", "Use of compile()"),
    (r"\bglobals\s*\(", "Use of globals()"),
    (r"\blocals\s*\(", "Use of locals()"),
    (r"\bopen\s*\(", "Use of open()"),
    (r"\bgetattr\s*\(", "Use of getattr()"),
    (r"\bsetattr\s*\(", "Use of setattr()"),
    (r"\bdelattr\s*\(", "Use of delattr()"),
    (r"\.to_csv\s*\(", "Writing to CSV"),
    (r"\.to_excel\s*\(", "Writing to Excel"),
    (r"\.to_parquet\s*\(", "Writing to Parquet"),
    (r"\.to_json\s*\(", "Writing to JSON file"),
    (r"\.to_sql\s*\(", "Writing to SQL"),
    (r"\.to_pickle\s*\(", "Writing to pickle"),
    (r"subprocess", "Reference to subprocess"),
    (r"\bos\.\b", "Reference to os module"),
]


class CodeSecurityError(Exception):
    """Raised when generated code contains blocked patterns."""


class CodeExecutionError(Exception):
    """Raised when code execution fails at runtime."""


def validate_code(code: str) -> None:
    """Scan code for blocked patterns. Raises CodeSecurityError if found."""
    for pattern, description in _BLOCKED_PATTERNS:
        if re.search(pattern, code):
            raise CodeSecurityError(
                f"Security violation: {description}. "
                f"The generated code contains a blocked operation."
            )


def _build_restricted_globals(df: pd.DataFrame) -> dict[str, Any]:
    """Build a restricted global namespace for exec()."""
    restricted: dict[str, Any] = {"__builtins__": {}}

    # Allow safe builtins
    import builtins
    safe_builtins = [
        "abs", "all", "any", "bool", "dict", "enumerate", "filter",
        "float", "format", "frozenset", "int", "isinstance", "issubclass",
        "len", "list", "map", "max", "min", "next", "print", "range",
        "reversed", "round", "set", "slice", "sorted", "str", "sum",
        "tuple", "type", "zip", "True", "False", "None",
        "ValueError", "TypeError", "KeyError", "IndexError",
        "Exception", "StopIteration",
    ]
    for name in safe_builtins:
        if hasattr(builtins, name):
            restricted["__builtins__"][name] = getattr(builtins, name)

    # Inject safe libraries
    restricted["pd"] = pd
    restricted["np"] = np
    restricted["df"] = df.copy()  # Always work on a copy

    return restricted


def execute_code(code: str, df: pd.DataFrame) -> Any:
    """Validate and execute code in a sandboxed environment.

    Returns the value of the `result` variable after execution.

    Raises:
        CodeSecurityError: If code contains blocked patterns.
        CodeExecutionError: If code fails at runtime.
    """
    validate_code(code)

    restricted_globals = _build_restricted_globals(df)
    local_ns: dict[str, Any] = {}

    try:
        exec(code, restricted_globals, local_ns)  # noqa: S102
    except Exception as exc:
        raise CodeExecutionError(str(exc)) from exc

    if "result" not in local_ns:
        raise CodeExecutionError(
            "Generated code did not assign a value to `result`. "
            "The code must contain: result = ..."
        )

    return local_ns["result"]
