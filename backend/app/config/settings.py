from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:postgres@localhost:5432/postgres"
    debug: bool = False
    refresh_token_secret_key: str = (
        "your-super-secret-refresh-key-change-this-in-production"
    )
    access_token_secret_key: str = (
        "your-super-secret-access-key-change-this-in-production"
    )
    jwt_algorithms: str = "HS256"
    refresh_token_expire_minutes: int = 10080 
    access_token_expire_minutes: int = 30  
    resend_api_token: str = ""
    resend_from_email: str = "noreply@crypalgos.com"
    resend_from_name: str = "CrypAlgos Platform"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_prefix = ""
        case_sensitive = False
        
settings = Settings()