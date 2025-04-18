from pydantic_settings import BaseSettings
from typing import Set, List
import os
from pathlib import Path


class Settings(BaseSettings):
    # API Keys
    openai_api_key: str
    openai_model: str = "text-embedding-3-small"
    openai_rate_limit_rpm: int = 60
    openai_retry_attempts: int = 3
    
    # Supabase Settings
    supabase_url: str
    supabase_key: str
    supabase_service_key: str
    
    # JWT Settings
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # File Processing
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    chunk_size: int = 1000
    chunk_overlap: int = 200
    allowed_file_types: Set[str] = {"application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/plain"}
    
    # Vector Search
    embedding_dimension: int = 1536
    similarity_threshold: float = 0.75
    max_results: int = 5
    
    # Server Settings
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    log_level: str = "info"
    
    # Templates
    templates_dir: str = "/templates"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings() 