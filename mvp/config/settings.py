from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    db_name: str = "postgres"
    db_user: str = "postgres"
    db_password: str = "postgres"
    db_host: str = "localhost"
    db_port: str = "5432"

    # LLM
    groq_api_key: str = ""
    openai_api_key: str = ""

    # Supabase / S3
    supabase_url: str = "https://zkkwcrciazcivtiaodiy.supabase.co"
    supabase_key: str = ""
    supabase_bucket_name: str = "test-bucket"
    supabase_access_key_id: str = ""
    supabase_secret_key_secret: str = ""
    supabase_endpoint: str = ""
    supabase_region: str = "ap-south-1"

    # Vector DB
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
