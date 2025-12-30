from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:postgres@localhost:5432/postgres"
    debug: bool = False
    qdrant_url: str = "http://localhost:6333"
    valkey_url: str = "redis://localhost:6379"
    llm_api_key: str = ""
    tavily_api_key: str = ""
    supabase_access_key_id : str = ""
    supabase_secret_key_secret : str = ""
    supabase_endpoint : str = ""
    supabase_region: str = ""

    
    
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_prefix = ""
        case_sensitive = False
        extra = "ignore"  # Allow extra env vars like POSTGRES_USER, etc.
        
settings = Settings()