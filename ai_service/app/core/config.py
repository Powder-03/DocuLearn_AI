from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Optional
import urllib.parse


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    DATABASE_URL: str
    MONGODB_URL: str
    GOOGLE_API_KEY: str
    
    # MongoDB database name
    MONGO_DB: Optional[str] = "learning_saas_chats"
    
    # LLM Model Configuration
    PLANNING_LLM_PROVIDER: str = "google"
    PLANNING_LLM_MODEL: str = "gemini-2.5-pro"
    PLANNING_LLM_TEMPERATURE: float = 0.7
    
    TUTORING_LLM_PROVIDER: str = "google"
    TUTORING_LLM_MODEL: str = "gemini-2.5-flash"
    TUTORING_LLM_TEMPERATURE: float = 0.7
    
    class Config:
        env_file = ".env"
        case_sensitive = True

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def clean_database_url(cls, v: str) -> str:
        """Clean database URL to remove unsupported parameters."""
        if not v:
            return v
        try:
            parsed = urllib.parse.urlparse(v)
            query = urllib.parse.parse_qs(parsed.query)
            # Remove parameters that cause issues with psycopg2 in some environments
            query.pop('channel_binding', None)
            query.pop('sslmode', None)
            new_query = urllib.parse.urlencode(query, doseq=True)
            return urllib.parse.urlunparse(parsed._replace(query=new_query))
        except Exception:
            return v


# Create a global settings instance
settings = Settings()
