from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App
    app_name: str = "Noel Whittaker Financial Chatbot"
    debug: bool = False

    # Groq (free LLM API)
    groq_api_key: str
    groq_model: str = "llama-3.1-8b-instant"

    # Qdrant
    qdrant_url: str = "https://2f62aaa8-2cef-4634-8ab5-4aacc1b9cd68.sa-east-1-0.aws.cloud.qdrant.io:6333"
    qdrant_api_key: str | None = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.DaODSsMZPd3vcsweeNSF8kcgokcWQLLgrlP5ONw4Ow4"
    qdrant_collection_name: str = "noel_whittaker_docs"

    # Supabase (optional - for conversation history)
    supabase_url: str | None = None
    supabase_key: str | None = None

    # Embeddings (local model, no API key needed)
    embedding_model: str = "all-MiniLM-L6-v2"

    # RAG settings
    chunk_size: int = 512
    chunk_overlap: int = 50
    top_k: int = 5

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
