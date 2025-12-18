from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    DATABASE_URL: str
    MONGODB_URL: str
    GROQ_API_KEY: str
    
    # MongoDB database name
    MONGO_DB: Optional[str] = "learning_saas_chats"
    
    # LLM Model Configuration - Using Groq Llama 3.1 70B for both
    PLANNING_LLM_PROVIDER: str = "groq"
    PLANNING_LLM_MODEL: str = "llama-3.1-70b-versatile"
    PLANNING_LLM_TEMPERATURE: float = 0.7
    
    TUTORING_LLM_PROVIDER: str = "groq"
    TUTORING_LLM_MODEL: str = "llama-3.1-70b-versatile"
    TUTORING_LLM_TEMPERATURE: float = 0.7
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create a global settings instance
settings = Settings()
