from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # API Settings
    api_title: str = "Casual Memory Agent API"
    api_version: str = "0.1.0"
    debug: bool = False

    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # DeepSeek API (OpenAI-compatible)
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"
    max_tokens: int = 4096

    # SiliconFlow API (for embeddings and reranking)
    siliconflow_api_key: str = ""
    siliconflow_base_url: str = "https://api.siliconflow.cn/v1"
    embedding_model: str = "BAAI/bge-m3"
    rerank_model: str = "BAAI/bge-reranker-v2-m3"
    embedding_dimensions: int = 1024

    # Database paths
    data_dir: Path = Path("data")

    @property
    def database_path(self) -> Path:
        return self.data_dir / "database" / "memory.db"

    @property
    def lancedb_path(self) -> Path:
        return self.data_dir / "database" / "lancedb"


@lru_cache
def get_settings() -> Settings:
    return Settings()
