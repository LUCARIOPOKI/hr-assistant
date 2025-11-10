from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    # App
    app_name: str = "HR Assistant"
    app_version: str = "0.1.0"
    debug: bool = True
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: List[str] = ["*"]

    # Azure OpenAI / OpenAI
    azure_openai_endpoint: str | None = None
    azure_openai_api_key: str | None = None
    azure_openai_api_version: str | None = "2024-02-01"
    azure_openai_deployment_name: str | None = None
    azure_openai_embedding_deployment: str | None = None
    embedding_model: str = "text-embedding-ada-002"

    # Pinecone
    pinecone_api_key: str | None = None
    pinecone_environment: str | None = None
    pinecone_index_name: str = "hr-assistant-index"
    pinecone_dimension: int = 1536
    pinecone_metric: str = "cosine"

    # MongoDB/Database
    mongo_db_connection_string: str | None = None
    database_name: str = "company_information_chunks"
    collection_name: str = "chunks"
    log_database_name: str = "audit_trail"
    log_collection_name: str = "logs"

    model_config = SettingsConfigDict(env_file=(".env", "src/.env"), env_prefix="HR_", case_sensitive=False, extra="ignore")


@lru_cache()
def get_settings() -> Settings:
    return Settings()
