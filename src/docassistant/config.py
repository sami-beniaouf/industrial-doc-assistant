"""Settings read from environment variables (.env in local development)."""
import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing environment variable {name}, see .env.example")
    return value


@dataclass(frozen=True)
class Settings:
    openai_endpoint: str = _require("AZURE_OPENAI_ENDPOINT")
    openai_api_key: str = _require("AZURE_OPENAI_API_KEY")
    openai_api_version: str = os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21")
    embedding_deployment: str = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "embedding")
    chat_deployment: str = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "chat")


settings = Settings()
