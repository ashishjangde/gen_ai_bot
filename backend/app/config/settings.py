from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"
    debug: bool = False
    
    qdrant_url: str = "http://localhost:6333"
    
    valkey_url: str = "redis://localhost:6379"
    
    llm_api_key: str = ""
    analyzer_model: str = "llama-3.1-8b-instant"
    refiner_model: str = "llama-3.1-8b-instant"      
    main_model: str = "llama-3.3-70b-versatile"
    
    tavily_api_key: str = ""
    mem0_api_key: str = ""
    
    supabase_access_key_id: str = ""
    supabase_access_key_secret: str = ""
    supabase_endpoint: str = ""
    supabase_region: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"

settings = Settings()