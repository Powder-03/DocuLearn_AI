from pydantic_settings import BaseSettings
from pydantic import field_validator, ValidationError
from typing import Optional
import sys
import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

logger = logging.getLogger(__name__)


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
        # Replace 'postgres://' with 'postgresql://' for compatibility with newer SQLAlchemy versions
        if v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql://", 1)
        return v


# Create a global settings instance
try:
    settings = Settings()

    # --- MongoDB Connection Check ---
    logger.info("Attempting to connect to MongoDB...")
    try:
        # Set a timeout to avoid long waits on startup
        client = MongoClient(settings.MONGODB_URL, serverSelectionTimeoutMS=5000)
        # Get the specific database from the client
        db = client[settings.MONGO_DB]
        # Ping the specific database to verify connection and permissions.
        db.command('ping')
        logger.info(f"✅ MongoDB connection successful to database '{settings.MONGO_DB}'.")
    except ConnectionFailure as e:
        logger.critical(f"❌ FATAL: Could not connect to MongoDB database '{settings.MONGO_DB}'. Check your MONGODB_URL and network access.")
        logger.critical(e)
        sys.exit(1)

except ValidationError as e:
    # Use logger to output to stderr, which is standard for container logs
    logger.critical("❌ FATAL: Missing or invalid environment variables. Check your secrets in Google Cloud.")
    logger.critical(e)
    # Exit with a non-zero status code to make the crash obvious in logs
    sys.exit(1)
