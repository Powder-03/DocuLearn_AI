from pydantic_settings import BaseSettings
from pydantic import field_validator, ValidationError
from typing import Optional
import sys


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
        return v


# Create a global settings instance
try:
    settings = Settings()
except ValidationError as e:
    print("❌ FATAL: Missing or invalid environment variables. Check your secrets in Google Cloud.", file=sys.stderr)
    print(e, file=sys.stderr)
    # Exit with a non-zero status code to make the crash obvious in logs
    sys.exit(1)
