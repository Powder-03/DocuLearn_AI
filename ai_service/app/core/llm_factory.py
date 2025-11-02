import os
from functools import lru_cache
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_core.language_models import BaseChatModel
from app.core.config import settings


# Set environment variables for API keys
os.environ["GOOGLE_API_KEY"] = settings.GOOGLE_API_KEY
os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY


@lru_cache(maxsize=10)
def get_llm(model_provider: str, model_name: str, temperature: float = 0.7) -> BaseChatModel:
    """
    Factory function to get an LLM instance based on provider and model name.
    
    Args:
        model_provider: Either "google" or "openai"
        model_name: The specific model name (e.g., "gemini-2.5-flash", "gpt-4o")
        temperature: Temperature setting for the model (default 0.7)
    
    Returns:
        BaseChatModel: An instance of the requested LLM
    """
    if model_provider.lower() == "google":
        return ChatGoogleGenerativeAI(
            model=model_name,
            temperature=temperature
        )
    elif model_provider.lower() == "openai":
        return ChatOpenAI(
            model=model_name,
            temperature=temperature
        )
    else:
        raise ValueError(f"Unsupported model provider: {model_provider}")
