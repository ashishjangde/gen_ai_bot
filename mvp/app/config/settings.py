import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"
    debug: bool = False
    
    # Vector DB
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""
    
    # Cache
    valkey_url: str = "redis://localhost:6379"
    
    # LLM
    llm_api_key: str = ""  # Groq API key
    analyzer_model: str = "llama-3.1-8b-instant"     # Efficient routing (Low Cost)
    refiner_model: str = "llama-3.1-8b-instant"      # Fast prompt engineering (Low Cost)
    main_model: str = "llama-3.3-70b-versatile"    # Main chat model (High Quality)
    
    # External APIs
    tavily_api_key: str = ""
    mem0_api_key: str = ""
    
    # Object Storage (Supabase)
    supabase_access_key_id: str = ""
    supabase_access_key_secret: str = ""
    supabase_bucket_name: str = "test-bucket"
    supabase_endpoint: str = ""
    supabase_region: str = ""

    model_config = {
        "env_file": os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        "env_file_encoding": "utf-8",
        "env_prefix": "",
        "case_sensitive": False,
        "extra": "ignore",
    }

settings = Settings()