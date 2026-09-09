"""Smart Data Analyst — AI-powered data analysis with natural language.

Run with:  streamlit run app.py
"""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# Ensure project root is on the path so services/ and utils/ are importable.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config.settings import settings  # noqa: E402
from services.llm_service import generate_code, fix_code, recommend_chart_type  # noqa: E402
from services.code_executor import (  # noqa: E402
    execute_code,
    CodeSecurityError,
    CodeExecutionError,
)
from services.visualization import create_chart  # noqa: E402
from services.insights import generate as generate_insights  # noqa: E402
from utils.helpers import (  # noqa: E402
    get_dataframe_summary,
    format_result_for_display,
    truncate_dataframe,
    convert_df_to_csv_bytes,
)


# ── Page Configuration ─────────────────────────────────────────────────────
st.set_page_config(
    page_title="Smart Data Analyst",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* Global font & background */
    .main .block-container {
        max-width: 1100px;
        padding-top: 2rem;
    }
    /* Header styling */
    .app-header {
        text-align: center;
        padding: 1rem 0 0.5rem 0;
    }
    .app-header h1 {
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }
    .app-header p {
        color: #6B7280;
        font-size: 1.05rem;
        margin-top: 0;
    }
    /* Card-like containers */
    .stExpander {
        border: 1px solid #E5E7EB;
        border-radius: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── Session State Initialisation ───────────────────────────────────────────
def _init_state() -> None:
    defaults = {
        "df": None,
        "conversation": [],  # list[dict] for context
        "results_history": [],  # list[dict] for display
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


_init_state()


# ── Helpers ────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_csv(file_bytes: bytes, file_name: str) -> pd.DataFrame:
    """Load and cache a CSV file."""
    from io import BytesIO

    return pd.read_csv(BytesIO(file_bytes), low_memory=False)


def _conversation_history_text() -> str:
    """Build a textual summary of previous queries for LLM context."""
    if not st.session_state.conversation:
        return ""
    lines = []
    for turn in st.session_state.conversation[-settings.MAX_CONVERSATION_HISTORY :]:
        lines.append(f"Q: {turn['query']}")
        lines.append(f"Code: {turn['code']}")
    return "\n".join(lines)


def _process_query(query: str, df: pd.DataFrame) -> dict:
    """End-to-end pipeline: generate code → execute → visualize → insights."""
    schema = get_dataframe_summary(df)
    history = _conversation_history_text()

    # ── Step 1: Generate code ───────────────────────────────────────────
    code = generate_code(schema=schema, query=query, history=history)

    # ── Step 2: Execute with auto-retry ─────────────────────────────────
    result = None
    error_msg = None
    attempts = 0

    while attempts <= settings.MAX_RETRIES:
        try:
            result = execute_code(code, df)
            error_msg = None
            break
        except CodeSecurityError as e:
            error_msg = str(e)
            break  # Security errors are not retryable
        except CodeExecutionError as e:
            error_msg = str(e)
            attempts += 1
            if attempts <= settings.MAX_RETRIES:
                code = fix_code(
                    schema=schema,
                    query=query,
                    code=code,
                    error=error_msg,
                )
            else:
                break

    if error_msg:
        return {
            "query": query,
            "code": code,
            "error": error_msg,
            "result": None,
            "result_df": None,
            "chart": None,
            "insights": None,
        }

    # ── Step 3: Format result ───────────────────────────────────────────
    display_text, result_df = format_result_for_display(result)

    # ── Step 4: Visualization ───────────────────────────────────────────
    chart = None
    if result_df is not None and not result_df.empty and len(result_df) > 1:
        cols_info = "\n".join(
            f"  {c}: {result_df[c].dtype}" for c in result_df.columns
        )
        chart_type = recommend_chart_type(
            query=query,
            columns_info=cols_info,
            num_rows=len(result_df),
        )
        chart = create_chart(result_df, chart_type, query)

    # ── Step 5: Insights ────────────────────────────────────────────────
    insights = generate_insights(query=query, result=result)

    # ── Save to conversation memory ─────────────────────────────────────
    st.session_state.conversation.append({"query": query, "code": code})

    return {
        "query": query,
        "code": code,
        "error": None,
        "result": display_text,
        "result_df": result_df,
        "chart": chart,
        "insights": insights,
    }


# ── UI Layout ──────────────────────────────────────────────────────────────
st.markdown(
    '<div class="app-header">'
    "<h1>📊 Smart Data Analyst</h1>"
    "<p>Upload your data, ask questions in plain English, get instant analysis.</p>"
    "</div>",
    unsafe_allow_html=True,
)

# ── Configuration Check ───────────────────────────────────────────────────
config_errors = settings.validate()
if config_errors:
    for err in config_errors:
        st.error(f"⚙️ {err}")
    st.stop()

# ── File Upload ────────────────────────────────────────────────────────────
st.markdown("### 📁 Upload Dataset")

uploaded_file = st.file_uploader(
    "Drop a CSV file here",
    type=["csv"],
    help=f"Max file size: {settings.MAX_UPLOAD_SIZE_MB} MB",
)

if uploaded_file is not None:
    # Size check
    file_size_mb = uploaded_file.size / (1024 * 1024)
    if file_size_mb > settings.MAX_UPLOAD_SIZE_MB:
        st.error(
            f"File is {file_size_mb:.1f} MB — exceeds the "
            f"{settings.MAX_UPLOAD_SIZE_MB} MB limit."
        )
        st.stop()

    with st.spinner("Loading dataset…"):
        try:
            df = load_csv(uploaded_file.getvalue(), uploaded_file.name)
            st.session_state.df = df
        except Exception as e:
            st.error(f"Failed to load CSV: {e}")
            st.stop()

if st.session_state.df is not None:
    df = st.session_state.df

    # ── Data Preview ───────────────────────────────────────────────────
    st.markdown("---")
    col_info, col_preview = st.columns([1, 2])

    with col_info:
        st.markdown("#### 📋 Dataset Info")
        st.markdown(f"**Rows:** {df.shape[0]:,}  •  **Columns:** {df.shape[1]}")
        dtype_df = pd.DataFrame(
            {"Column": df.columns, "Type": [str(t) for t in df.dtypes]}
        )
        st.dataframe(dtype_df, use_container_width=True, hide_index=True, height=220)

    with col_preview:
        st.markdown("#### 👀 Preview")
        st.dataframe(
            df.head(settings.MAX_PREVIEW_ROWS),
            use_container_width=True,
            hide_index=True,
            height=220,
        )

    # ── Query Input ────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 💬 Ask Your Data")

    # Sample queries
    sample_queries = [
        "Top 5 products by sales",
        "Monthly revenue trend",
        "Average price by category",
    ]
    sample_cols = st.columns(len(sample_queries))
    for i, sq in enumerate(sample_queries):
        if sample_cols[i].button(f"💡 {sq}", key=f"sample_{i}", use_container_width=True):
            st.session_state["_pending_query"] = sq

    query = st.text_input(
        "Type your question…",
        value=st.session_state.get("_pending_query", ""),
        placeholder="e.g., What are the top 10 customers by total spending?",
        label_visibility="collapsed",
    )

    # Clear pending query after use
    if "_pending_query" in st.session_state:
        del st.session_state["_pending_query"]

    if st.button("🔍 Analyze", type="primary", use_container_width=True):
        if not query.strip():
            st.warning("Please enter a query.")
        else:
            with st.spinner("Analyzing your data…"):
                result = _process_query(query.strip(), df)
                st.session_state.results_history.insert(0, result)

    # ── Display Results ────────────────────────────────────────────────
    if st.session_state.results_history:
        latest = st.session_state.results_history[0]
        st.markdown("---")

        if latest["error"]:
            st.error(f"❌ **Error:** {latest['error']}")
            with st.expander("🔧 Generated Code"):
                st.code(latest["code"], language="python")
        else:
            # Generated Code (collapsible)
            with st.expander("🔧 Generated Code", expanded=False):
                st.code(latest["code"], language="python")

            # Result Table
            st.markdown("#### 📊 Result")
            if latest["result_df"] is not None:
                display_df = truncate_dataframe(latest["result_df"])
                st.dataframe(display_df, use_container_width=True, hide_index=True)

                # Download button
                csv_bytes = convert_df_to_csv_bytes(latest["result_df"])
                st.download_button(
                    "⬇️ Download as CSV",
                    data=csv_bytes,
                    file_name="query_result.csv",
                    mime="text/csv",
                )
            else:
                st.info(latest["result"])

            # Chart
            if latest["chart"] is not None:
                st.markdown("#### 📈 Visualization")
                st.plotly_chart(latest["chart"], use_container_width=True)

            # Insights
            if latest["insights"]:
                st.markdown("#### 💡 AI Insights")
                st.markdown(latest["insights"])

        # ── Previous Queries ───────────────────────────────────────────
        if len(st.session_state.results_history) > 1:
            st.markdown("---")
            with st.expander(
                f"📜 Previous Queries ({len(st.session_state.results_history) - 1})",
                expanded=False,
            ):
                for i, past in enumerate(st.session_state.results_history[1:], 1):
                    st.markdown(f"**{i}. {past['query']}**")
                    if past["error"]:
                        st.caption(f"❌ Error: {past['error']}")
                    else:
                        st.caption("✅ Completed")
                    st.markdown("")

else:
    # Empty state
    st.markdown("---")
    st.info(
        "👆 Upload a CSV file to get started. "
        "Then ask questions about your data in plain English!"
    )

# ── Footer ─────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("Built with ❤️ using Streamlit, Pandas, Plotly & Ollama")

