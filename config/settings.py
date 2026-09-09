import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application configuration loaded from environment variables."""

    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.1")
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "2"))
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "200"))
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.0"))
    MAX_PREVIEW_ROWS: int = int(os.getenv("MAX_PREVIEW_ROWS", "5"))
    MAX_CONVERSATION_HISTORY: int = int(os.getenv("MAX_CONVERSATION_HISTORY", "10"))

    @classmethod
    def validate(cls) -> list[str]:
        """Return a list of configuration errors (empty if valid)."""
        errors: list[str] = []
        # Check if Ollama is reachable
        import urllib.request
        try:
            urllib.request.urlopen(
                cls.OLLAMA_BASE_URL.replace("/v1", ""), timeout=3
            )
        except Exception:
            errors.append(
                f"Cannot reach Ollama at {cls.OLLAMA_BASE_URL}. "
                "Make sure Ollama is running (`ollama serve`)."
            )
        return errors


settings = Settings()
