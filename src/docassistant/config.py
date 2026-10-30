"""Settings read from environment variables (.env in local development)."""
import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


def _require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing environment variable {name}, see .env.example")
    return value


@dataclass(frozen=True)
class Settings:
    # Azure AI Foundry / Azure OpenAI
    openai_endpoint: str = field(default_factory=lambda: _require("AZURE_OPENAI_ENDPOINT"))
    openai_api_key: str = field(default_factory=lambda: _require("AZURE_OPENAI_API_KEY"))
    openai_api_version: str = os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21")
    embedding_deployment: str = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "embedding")
    embedding_dimensions: int = 1536
    chat_deployment: str = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "chat")

    # Azure AI Search
    search_endpoint: str = field(default_factory=lambda: os.getenv("AZURE_SEARCH_ENDPOINT", ""))
    search_api_key: str = field(default_factory=lambda: os.getenv("AZURE_SEARCH_API_KEY", ""))
    search_index: str = os.getenv("AZURE_SEARCH_INDEX", "industrial-docs")


settings = Settings()
