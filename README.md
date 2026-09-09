# 📊 Smart Data Analyst

AI-powered data analysis application that lets you upload CSV files and query them using natural language. Built with Python, Streamlit, and **Ollama** — runs 100% locally, no API keys needed.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.36+-red)
![Ollama](https://img.shields.io/badge/Ollama-Local%20LLM-purple)
![License](https://img.shields.io/badge/License-MIT-green)

## ✨ Features

- **Natural Language Queries** — Ask questions like *"Top 5 products by revenue"* and get instant results
- **Auto Visualization** — Charts are generated automatically using Plotly (bar, line, histogram, scatter, pie)
- **AI Insights** — Get concise, business-focused takeaways from every query
- **Safe Execution** — Generated code runs in a sandboxed environment that blocks file/OS/network access
- **Error Auto-Fix** — If generated code fails, the LLM automatically retries with the error context (up to 2 retries)
- **Conversation Memory** — Follow-up queries maintain context (e.g., *"Now filter for 2023"*)
- **Download Results** — Export any result as CSV
- **Fully Local** — Powered by Ollama, your data never leaves your machine

---

## 🚀 Quick Start

### 1. Install Ollama

Download and install from [ollama.com](https://ollama.com), then pull a model:

```bash
ollama pull llama3.1
```

> You can use any model — see [Supported Models](#-supported-models) below.

### 2. Install Python Dependencies

```bash
# Navigate to project directory
cd "Smart Data Analyst application"

# Create a virtual environment (recommended)
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Run the App

Make sure Ollama is running, then launch:

```env
OPENAI_API_KEY=sk-your-actual-key-here
```

> **Using a different provider?** Set `OPENAI_BASE_URL` to point to any OpenAI-compatible API (e.g., Azure, local LLM, etc.)

### 3. Run the App

```bash
streamlit run app.py
```

The app will open at [http://localhost:8501](http://localhost:8501).

> **Note:** Ollama starts automatically on most systems. If you get a connection error, run `ollama serve` in a separate terminal.

---

## 📁 Project Structure

```
Smart Data Analyst application/
│
├── app.py                    # Main Streamlit application
├── services/
│   ├── llm_service.py        # Ollama API communication (OpenAI-compatible)
│   ├── code_executor.py      # Sandboxed code execution engine
│   ├── visualization.py      # Plotly chart generation
│   └── insights.py           # AI insight generation
│
├── utils/
│   ├── prompt_templates.py   # All LLM prompt templates
│   └── helpers.py            # Data processing utilities
│
├── config/
│   └── settings.py           # Environment-based configuration
│
├── .env                      # Local config (not committed to git)
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

---

## ⚙️ Configuration

All settings are controlled via environment variables (`.env` file):

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://localhost:11434/v1` | Ollama API endpoint |
| `OLLAMA_MODEL` | `llama3.1` | Model to use for code generation |
| `MAX_RETRIES` | `2` | Max auto-fix retries on code errors |
| `MAX_UPLOAD_SIZE_MB` | `200` | Maximum CSV file size in MB |
| `TEMPERATURE` | `0.0` | LLM temperature (0 = deterministic) |

---

## 🤖 Supported Models

Any Ollama model works. Recommended options:

| Model | Size | Best For |
|---|---|---|
| `llama3.1` | ~4.7 GB | General purpose (default) |
| `llama3.1:70b` | ~40 GB | Higher accuracy, needs more RAM |
| `qwen2.5-coder` | ~4.4 GB | Optimized for code generation |
| `codellama` | ~3.8 GB | Code-focused, lighter weight |
| `mistral` | ~4.1 GB | Good balance of speed and quality |

To switch models:

```bash
ollama pull qwen2.5-coder
```

Then update `.env`:

```env
OLLAMA_MODEL=qwen2.5-coder
```

---

## 🧪 Sample Queries

After uploading a dataset, try these:

| Query | What it does |
|---|---|
| `Top 5 products by sales` | Aggregates and ranks |
| `Monthly revenue trend` | Time-series grouping |
| `Average price by category` | Category-level statistics |
| `Show distribution of order values` | Histogram analysis |
| `What percentage of orders are from each region?` | Proportional breakdown |
| `Now filter for 2023` | Follow-up with context |

---

## 🔐 Security

The code execution engine enforces strict sandboxing:

- **Blocked**: `os`, `sys`, `subprocess`, `shutil`, `pathlib`, `socket`, `http`, `requests`
- **Blocked**: `exec()`, `eval()`, `open()`, `compile()`, `__import__()`, `getattr()`, `setattr()`
- **Blocked**: File write operations (`.to_csv()`, `.to_excel()`, `.to_parquet()`, etc.)
- **Allowed**: Only `pandas` and `numpy` operations within a restricted `exec()` namespace

---

## 🛠️ Troubleshooting

| Problem | Solution |
|---|---|
| `Cannot reach Ollama` | Run `ollama serve` or check if Ollama is installed |
| Slow responses | Try a smaller model like `codellama` or `mistral` |
| Bad code generation | Switch to `qwen2.5-coder` or `llama3.1:70b` for better accuracy |
| Import errors | Make sure you activated the venv and ran `pip install -r requirements.txt` |

---

## 📝 License

MIT
