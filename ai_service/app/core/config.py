from pydantic_settings import BaseSettings
from typing import Optional


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
    TUTORING_LLM_MODEL: str = "gemini-2.5-pro"
    TUTORING_LLM_TEMPERATURE: float = 0.7
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create a global settings instance
settings = Settings()
