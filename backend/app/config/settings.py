from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"
    debug: bool = False
    env : str = "development"
    qdrant_url: str = "http://localhost:6333"
    
    valkey_url: str = "redis://localhost:6379"
    llm_api_key: str = ""
    analyzer_model: str = "llama-3.1-8b-instant"     
    main_model: str = "llama-3.3-70b-versatile"
    
    tavily_api_key: str = ""
    
    supabase_access_key_id: str = ""
    supabase_access_key_secret: str = ""
    supabase_endpoint: str = ""
    supabase_region: str = ""

    refresh_token_secret_key: str = ""
    access_token_secret_key: str = ""
    jwt_algorithms: str = "HS256"
    refresh_token_expire_minutes: int = 60 * 24 * 7
    access_token_expire_minutes: int = 60 * 24

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"

settings = Settings()