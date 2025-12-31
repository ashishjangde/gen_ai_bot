import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:postgres@localhost:5432/postgres"
    debug: bool = False
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""
    valkey_url: str = "redis://localhost:6379"
    llm_api_key: str = ""
    tavily_api_key: str = ""
    supabase_access_key_id : str = ""
    supabase_access_key_secret : str = ""
    supabase_bucket_name: str = "test-bucket"
    supabase_endpoint : str = ""
    supabase_region: str = ""

    
    
    
    class Config:
        env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env")
        env_file_encoding = "utf-8"
        env_prefix = ""
        case_sensitive = False
        extra = "ignore"  # Allow extra env vars like POSTGRES_USER, etc.
        
settings = Settings()