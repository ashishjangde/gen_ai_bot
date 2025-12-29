from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:postgres@localhost:5432/postgres"
    debug: bool = False
    env: str = "development"
    refresh_token_secret_key: str = (
        "sdfssdfhuwsdfsd"
    )
    access_token_secret_key: str = (
        "ashishfsd32yhjsd"
    )
    jwt_algorithms: str = "HS256"
    refresh_token_expire_minutes: int = 10080 
    access_token_expire_minutes: int = 30 
    
    # Qdrant
    qdrant_url: str = "http://qdrant:6333"
    
    # Valkey (Redis-compatible)
    valkey_url: str = "redis://valkey:6379/0"
    
    # LLM API
    llm_provider: str = "groq"  # groq, openai, anthropic
    llm_api_key: str = ""
    llm_model: str = "llama-3.3-70b-versatile"
    
    # Tavily Web Search
    tavily_api_key: str = ""
    
    # Mem0
    mem0_api_key: str = ""  # Leave empty for local storage
    
    # Oracle Cloud Object Storage
    oci_config_file: str = "~/.oci/config"
    oci_config_profile: str = "DEFAULT"
    oci_namespace: str = ""
    oci_bucket_name: str = ""
    oci_region: str = "ap-mumbai-1"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_prefix = ""
        case_sensitive = False
        extra = "ignore"  # Allow extra env vars like POSTGRES_USER, etc.
        
settings = Settings()